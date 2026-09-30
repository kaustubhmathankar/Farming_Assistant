from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import (
    Session,
    selectinload,
)

from app.database import get_db
from app.dependencies import (
    CurrentAuth,
    get_current_auth,
)
from app.models import (
    Conversation,
    Message,
)
from app.services.conversation_service import (
    attachment_path,
    delete_message_attachment,
    get_image_attachment,
    serialize_conversation,
    serialize_conversation_summary,
)


router = APIRouter(
    prefix="/conversations",
    tags=["Conversations"],
)


@router.get("")
def list_conversations(
    auth: CurrentAuth = Depends(
        get_current_auth
    ),
    db: Session = Depends(get_db),
):
    conversations = db.scalars(
        select(Conversation)
        .where(
            Conversation.farmer_id
            == auth.farmer_id
        )
        .options(
            selectinload(
                Conversation.messages
            )
        )
        .order_by(
            Conversation.updated_at.desc()
        )
    ).all()

    return {
        "items": [
            serialize_conversation_summary(
                item
            )
            for item in conversations
        ],
        "total": len(
            conversations
        ),
    }


@router.get(
    "/{conversation_id}"
)
def get_conversation(
    conversation_id: str,
    auth: CurrentAuth = Depends(
        get_current_auth
    ),
    db: Session = Depends(get_db),
):
    conversation = db.scalar(
        select(Conversation)
        .where(
            Conversation.id
            == conversation_id,
            Conversation.farmer_id
            == auth.farmer_id,
        )
        .options(
            selectinload(
                Conversation.messages
            )
        )
    )

    if not conversation:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found",
        )

    return serialize_conversation(
        conversation
    )


@router.get(
    "/{conversation_id}/messages/{message_id}/image"
)
def get_message_image(
    conversation_id: str,
    message_id: int,
    auth: CurrentAuth = Depends(
        get_current_auth
    ),
    db: Session = Depends(get_db),
):
    """
    Return a persisted crop image only if
    it belongs to the currently authenticated farmer.
    """

    message = db.scalar(
        select(Message)
        .join(
            Conversation,
            Message.conversation_id
            == Conversation.id,
        )
        .where(
            Message.id == message_id,
            Message.conversation_id
            == conversation_id,
            Message.role == "user",
            Conversation.farmer_id
            == auth.farmer_id,
        )
    )

    if not message:
        raise HTTPException(
            status_code=404,
            detail="Image message not found",
        )

    attachment = (
        get_image_attachment(
            message
        )
    )

    if not attachment:
        raise HTTPException(
            status_code=404,
            detail="No image attachment found",
        )

    storage_name = str(
        attachment.get(
            "storage_name",
            "",
        )
    ).strip()

    if not storage_name:
        raise HTTPException(
            status_code=404,
            detail="Image file is unavailable",
        )

    try:
        path = attachment_path(
            storage_name
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail="Image file is unavailable",
        ) from exc

    if not path.is_file():
        raise HTTPException(
            status_code=404,
            detail="Image file is unavailable",
        )

    return FileResponse(
        path,
        media_type=attachment.get(
            "content_type"
        )
        or "application/octet-stream",
        filename=attachment.get(
            "original_name"
        )
        or "crop-image",
        headers={
            "Cache-Control": (
                "private, max-age=3600"
            )
        },
    )


@router.delete(
    "/{conversation_id}"
)
def delete_conversation(
    conversation_id: str,
    auth: CurrentAuth = Depends(
        get_current_auth
    ),
    db: Session = Depends(get_db),
):
    conversation = db.scalar(
        select(Conversation)
        .where(
            Conversation.id
            == conversation_id,
            Conversation.farmer_id
            == auth.farmer_id,
        )
        .options(
            selectinload(
                Conversation.messages
            )
        )
    )

    if not conversation:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found",
        )

    # Also delete saved image files.
    for message in conversation.messages:
        delete_message_attachment(
            message
        )

    db.delete(conversation)
    db.commit()

    return {
        "message": "Conversation deleted"
    }