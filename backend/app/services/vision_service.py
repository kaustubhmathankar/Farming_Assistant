import base64
from io import BytesIO

from fastapi import HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError
from groq import Groq

from app.config import settings


async def analyze_image(upload: UploadFile) -> str:
    data = await upload.read(settings.image_max_size_mb * 1024 * 1024 + 1)
    if len(data) > settings.image_max_size_mb * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Image is too large")
    try:
        image = Image.open(BytesIO(data))
        image.verify()
        image = Image.open(BytesIO(data))
        fmt = (image.format or "").upper()
        if fmt not in {"JPEG", "PNG", "WEBP"}:
            raise ValueError("Unsupported image format")
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise HTTPException(status_code=400, detail="Upload a valid JPEG, PNG, or WEBP image") from exc

    encoded = base64.b64encode(data).decode("utf-8")
    client = Groq(api_key=settings.groq_api_key)
    response = client.chat.completions.create(
        model=settings.vision_model,
        temperature=0,
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": "Observe this crop/leaf image. Describe visible symptoms, affected plant parts, and plausible categories of stress or disease. Do not claim certainty, do not invent details, and do not give pesticide dosage. Return concise observations for another farming assistant to reason over."},
                {"type": "image_url", "image_url": {"url": f"data:{upload.content_type or 'image/jpeg'};base64,{encoded}"}},
            ],
        }],
    )  
    return response.choices[0].message.content or "No reliable visual observations were returned."
