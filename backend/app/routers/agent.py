from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
)
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.dependencies import (
    CurrentAuth,
    get_current_auth,
)
from app.schemas import (
    AgentSource,
    ChatRequest,
    ChatResponse,
    VoiceResponse,
)
from app.services.agent_service import (
    run_agent,
)
from app.services.conversation_service import (
    create_conversation,
    get_owned_conversation,
    recent_history,
    save_image_attachment,
    save_message,
)
from app.services.farmer_service import (
    farmer_context,
    get_farmer,
)
from app.services.language_service import (
    normalize_language,
)
from app.services.rate_limit import (
    rate_limit,
)
from app.services.vision_service import (
    analyze_image,
)
from app.services.voice_service import (
    normalize_language as normalize_voice_language,
    transcribe,
)


router = APIRouter(
    prefix="/agent",
    tags=["Farming Agent"],
)


def _source_models(
    items: list[dict],
) -> list[AgentSource]:
    return [
        AgentSource(
            **{
                key: item.get(key)
                for key in [
                    "title",
                    "source",
                    "url",
                    "type",
                ]
            }
        )
        for item in items
    ]


def _conversation(
    db: Session,
    auth: CurrentAuth,
    conversation_id: str | None,
    language: str,
    location: str = "",
):
    if conversation_id:
        conversation = get_owned_conversation(
            db,
            conversation_id,
            auth.farmer_id,
        )

        if not conversation:
            raise HTTPException(
                status_code=404,
                detail="Conversation not found",
            )

        return conversation

    return create_conversation(
        db,
        auth.farmer_id,
        language,
        location,
    )


@router.post(
    "/chat",
    response_model=ChatResponse,
)
async def chat(
    request: Request,
    payload: ChatRequest,
    auth: CurrentAuth = Depends(
        get_current_auth
    ),
    db: Session = Depends(get_db),
    _=Depends(
        rate_limit(30, 60)
    ),
):
    farmer = get_farmer(
        db,
        auth.farmer_id,
    )

    if not farmer:
        raise HTTPException(
            status_code=404,
            detail="Farmer profile not found",
        )

    # Saved profile language is the source of truth.
    language = normalize_language(
        farmer.language
    )

    location = ", ".join(
        value
        for value in [
            farmer.village,
            farmer.district,
            farmer.state,
        ]
        if value
    )

    conversation = _conversation(
        db,
        auth,
        payload.conversation_id,
        language,
        location,
    )

    history = recent_history(
        db,
        conversation.id,
    )

    answer, sources, tools = run_agent(
        payload.message.strip(),
        language=language,
        history=history,
        farmer_context=farmer_context(
            farmer
        ),
    )

    save_message(
        db,
        conversation.id,
        "user",
        payload.message.strip(),
        "text",
    )

    save_message(
        db,
        conversation.id,
        "assistant",
        answer,
        "text",
        sources,
    )

    conversation.language = language
    conversation.location = (
        location
        or conversation.location
    )

    db.commit()

    return ChatResponse(
        answer=answer,
        conversation_id=conversation.id,
        language=language,
        sources=_source_models(
            sources
        ),
        used_tools=tools,
    )


@router.post(
    "/image-chat",
    response_model=ChatResponse,
)
async def image_chat(
    request: Request,
    question: str = Form(
        "Please check this crop image."
    ),
    conversation_id: str | None = Form(
        None
    ),
    image: UploadFile = File(...),
    auth: CurrentAuth = Depends(
        get_current_auth
    ),
    db: Session = Depends(get_db),
    _=Depends(
        rate_limit(30, 60)
    ),
):
    farmer = get_farmer(
        db,
        auth.farmer_id,
    )

    if not farmer:
        raise HTTPException(
            status_code=404,
            detail="Farmer profile not found",
        )

    language = normalize_language(
        farmer.language
    )

    location = ", ".join(
        value
        for value in [
            farmer.village,
            farmer.district,
            farmer.state,
        ]
        if value
    )

    # Keep a bounded copy of the uploaded file
    # so we can persist the same validated bytes.
    image_bytes = await image.read(
        settings.image_max_size_mb
        * 1024
        * 1024
        + 1
    )

    if len(image_bytes) > (
        settings.image_max_size_mb
        * 1024
        * 1024
    ):
        raise HTTPException(
            status_code=413,
            detail="Image is too large",
        )

    # Reset the UploadFile because the vision
    # service will read it again.
    await image.seek(0)

    conversation = _conversation(
        db,
        auth,
        conversation_id,
        language,
        location,
    )

    # This performs actual image validation
    # and sends the image to the vision model.
    observations = await analyze_image(
        image
    )

    history = recent_history(
        db,
        conversation.id,
    )

    answer, sources, tools = run_agent(
        question.strip(),
        language=language,
        history=history,
        farmer_context=farmer_context(
            farmer
        ),
        visual_observations=observations,
    )

    # Only persist after successful image validation
    # and successful AI analysis.
    try:
        attachment = save_image_attachment(
            image_bytes,
            image.filename,
            image.content_type,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail="Unable to persist the uploaded image",
        ) from exc

    save_message(
        db,
        conversation.id,
        "user",
        question.strip(),
        "image",
        attachment=attachment,
    )

    save_message(
        db,
        conversation.id,
        "assistant",
        answer,
        "image",
        sources,
    )

    conversation.language = language
    conversation.location = (
        location
        or conversation.location
    )

    db.commit()

    return ChatResponse(
        answer=answer,
        conversation_id=conversation.id,
        language=language,
        sources=_source_models(
            sources
        ),
        used_tools=tools,
    )


@router.post(
    "/voice-chat",
    response_model=VoiceResponse,
)
async def voice_chat(
    request: Request,
    audio: UploadFile = File(...),
    conversation_id: str | None = Form(
        None
    ),
    voice_language: str = Form(
        "auto"
    ),
    auth: CurrentAuth = Depends(
        get_current_auth
    ),
    db: Session = Depends(get_db),
    _=Depends(
        rate_limit(30, 60)
    ),
):
    farmer = get_farmer(
        db,
        auth.farmer_id,
    )

    if not farmer:
        raise HTTPException(
            status_code=404,
            detail="Farmer profile not found",
        )

    preferred_language = normalize_language(
        farmer.language
    )

    requested_language = None

    if (
        str(voice_language or "")
        .strip()
        .lower()
        != "auto"
    ):
        requested_language = (
            normalize_voice_language(
                voice_language
            )
        )

    transcript, detected_language = (
        await transcribe(
            audio,
            preferred_language=preferred_language,
            language_hint=requested_language,
        )
    )

    answer_language = (
        preferred_language
    )

    location = ", ".join(
        value
        for value in [
            farmer.village,
            farmer.district,
            farmer.state,
        ]
        if value
    )

    conversation = _conversation(
        db,
        auth,
        conversation_id,
        answer_language,
        location,
    )

    history = recent_history(
        db,
        conversation.id,
    )

    answer, sources, tools = run_agent(
        transcript,
        language=answer_language,
        history=history,
        farmer_context=farmer_context(
            farmer
        ),
    )

    save_message(
        db,
        conversation.id,
        "user",
        transcript,
        "voice",
    )

    save_message(
        db,
        conversation.id,
        "assistant",
        answer,
        "voice",
        sources,
    )

    conversation.language = (
        answer_language
    )

    conversation.location = (
        location
        or conversation.location
    )

    db.commit()

    return VoiceResponse(
        answer=answer,
        conversation_id=conversation.id,
        language=answer_language,
        sources=_source_models(
            sources
        ),
        used_tools=tools,
        transcript=transcript,
        detected_language=detected_language,
    )