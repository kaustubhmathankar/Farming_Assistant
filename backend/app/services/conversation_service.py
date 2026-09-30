import json
import uuid
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Conversation, Message, utcnow_naive


ATTACHMENT_MARKER = "__chat_attachment__"

ATTACHMENT_DIR = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "uploads"
    / "chat"
)


def _ensure_attachment_dir() -> Path:
    ATTACHMENT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )
    return ATTACHMENT_DIR


def save_image_attachment(
    data: bytes,
    original_name: str | None,
    content_type: str | None,
) -> dict:
    """
    Save a validated crop image using a random server-side filename.

    The original filename is stored only as metadata.
    """

    from io import BytesIO

    from PIL import Image

    if not data:
        raise ValueError(
            "Image data is empty"
        )

    try:
        image = Image.open(
            BytesIO(data)
        )

        image.verify()

        image = Image.open(
            BytesIO(data)
        )

        image_format = (
            image.format or ""
        ).upper()

    except Exception as exc:
        raise ValueError(
            "Invalid image data"
        ) from exc

    formats = {
        "JPEG": (
            "jpg",
            "image/jpeg",
        ),
        "PNG": (
            "png",
            "image/png",
        ),
        "WEBP": (
            "webp",
            "image/webp",
        ),
    }

    if image_format not in formats:
        raise ValueError(
            "Unsupported image format"
        )

    extension, normalized_type = formats[
        image_format
    ]

    storage_name = (
        f"{uuid.uuid4().hex}.{extension}"
    )

    target = (
        _ensure_attachment_dir()
        / storage_name
    )

    target.write_bytes(data)

    return {
        "type": ATTACHMENT_MARKER,
        "storage_name": storage_name,
        "original_name": (
            original_name
            or f"crop-image.{extension}"
        )[:255],
        "content_type": normalized_type,
        "size": len(data),
    }


def get_image_attachment(
    message: Message,
) -> dict | None:
    try:
        items = json.loads(
            message.sources_json or "[]"
        )
    except (
        TypeError,
        ValueError,
        json.JSONDecodeError,
    ):
        return None

    for item in items:
        if (
            isinstance(item, dict)
            and item.get("type")
            == ATTACHMENT_MARKER
        ):
            return item

    return None


def attachment_path(
    storage_name: str,
) -> Path:
    """
    Resolve an attachment path safely inside the upload folder.
    """

    safe_name = Path(
        storage_name
    ).name

    directory = (
        _ensure_attachment_dir()
    )

    target = directory / safe_name
    root = directory.resolve()

    if target.resolve().parent != root:
        raise ValueError(
            "Invalid attachment path"
        )

    return target


def delete_message_attachment(
    message: Message,
) -> None:
    attachment = get_image_attachment(
        message
    )

    if not attachment:
        return

    storage_name = str(
        attachment.get(
            "storage_name",
            "",
        )
    ).strip()

    if not storage_name:
        return

    try:
        path = attachment_path(
            storage_name
        )

        if path.exists():
            path.unlink()

    except (
        OSError,
        ValueError,
    ):
        pass


def create_conversation(
    db: Session,
    farmer_id: str,
    language: str,
    location: str = "",
    crop: str = "",
) -> Conversation:
    conversation = Conversation(
        id=str(uuid.uuid4()),
        farmer_id=farmer_id,
        language=language,
        location=location or "",
        crop=crop or "",
    )

    db.add(conversation)
    db.flush()

    return conversation


def get_owned_conversation(
    db: Session,
    conversation_id: str,
    farmer_id: str,
) -> Conversation | None:
    return db.scalar(
        select(Conversation).where(
            Conversation.id
            == conversation_id,
            Conversation.farmer_id
            == farmer_id,
        )
    )


def save_message(
    db: Session,
    conversation_id: str,
    role: str,
    content: str,
    input_type: str = "text",
    sources: list | None = None,
    attachment: dict | None = None,
) -> Message:

    metadata = list(
        sources or []
    )

    if attachment:
        metadata.append(
            attachment
        )

    message = Message(
        conversation_id=conversation_id,
        role=role,
        content=content,
        input_type=input_type,
        sources_json=json.dumps(
            metadata,
            ensure_ascii=False,
        ),
    )

    db.add(message)
    db.flush()

    conversation = db.get(
        Conversation,
        conversation_id,
    )

    if conversation:
        conversation.updated_at = (
            utcnow_naive()
        )

    return message


def recent_history(
    db: Session,
    conversation_id: str,
) -> list[dict]:

    rows = db.scalars(
        select(Message)
        .where(
            Message.conversation_id
            == conversation_id,
            Message.role.in_(
                [
                    "user",
                    "assistant",
                ]
            ),
        )
        .order_by(
            Message.id.desc()
        )
        .limit(
            settings.memory_message_limit
        )
    ).all()

    rows.reverse()

    return [
        {
            "role": row.role,
            "content": row.content,
        }
        for row in rows
    ]


def conversation_title(
    conversation: Conversation,
) -> str:

    first_user = next(
        (
            row
            for row in sorted(
                conversation.messages,
                key=lambda item: item.id,
            )
            if row.role == "user"
        ),
        None,
    )

    if not first_user:
        if conversation.crop:
            return conversation.crop

        return "New farming chat"

    title = " ".join(
        (
            first_user.content
            or ""
        ).split()
    )

    if len(title) > 46:
        title = (
            title[:46].rstrip()
            + "…"
        )

    return (
        title
        or "New farming chat"
    )


def serialize_conversation_summary(
    conversation: Conversation,
) -> dict:

    return {
        "id": conversation.id,
        "title": conversation_title(
            conversation
        ),
        "language": conversation.language,
        "location": conversation.location,
        "crop": conversation.crop,
        "message_count": sum(
            1
            for row in conversation.messages
            if row.role
            in {
                "user",
                "assistant",
            }
        ),
        "created_at": (
            conversation.created_at.isoformat()
        ),
        "updated_at": (
            conversation.updated_at.isoformat()
        ),
    }


def serialize_conversation(
    conversation: Conversation,
) -> dict:

    serialized_messages = []

    for row in sorted(
        conversation.messages,
        key=lambda item: item.id,
    ):
        if row.role not in {
            "user",
            "assistant",
        }:
            continue

        try:
            metadata = json.loads(
                row.sources_json or "[]"
            )

        except (
            TypeError,
            ValueError,
            json.JSONDecodeError,
        ):
            metadata = []

        sources = [
            item
            for item in metadata
            if isinstance(item, dict)
            and item.get("type")
            != ATTACHMENT_MARKER
        ]

        payload = {
            "id": row.id,
            "role": row.role,
            "content": row.content,
            "input_type": row.input_type,
            "sources": sources,
            "created_at": (
                row.created_at.isoformat()
            ),
        }

        attachment = get_image_attachment(
            row
        )

        if (
            attachment
            and attachment.get(
                "storage_name"
            )
        ):
            payload["image_url"] = (
                f"/conversations/"
                f"{conversation.id}/messages/"
                f"{row.id}/image"
            )

            payload["image_name"] = (
                attachment.get(
                    "original_name"
                )
            )

        serialized_messages.append(
            payload
        )

    return {
        "id": conversation.id,
        "title": conversation_title(
            conversation
        ),
        "language": conversation.language,
        "location": conversation.location,
        "crop": conversation.crop,
        "messages": serialized_messages,
    }