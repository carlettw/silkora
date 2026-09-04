import uuid
from pathlib import Path

import requests
from fastapi import HTTPException, UploadFile

from app.core.config import settings

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp", "image/heic"}
MAX_FILE_SIZE_MB = 8


async def save_upload_image(file: UploadFile, subfolder: str) -> str:
    """
    Rasmni Supabase Storage'ga yuklaydi va to'liq (absolute) public URL qaytaradi.

    Render kabi platformalarda lokal disk vaqtinchalik (ephemeral) bo'lgani uchun
    fayllarni serverning o'z diskiga saqlash xavfli - har qayta deploy/restart'da
    o'chib ketadi. Shuning uchun fayllar Supabase Storage'da saqlanadi (doimiy).
    """
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail="Faqat JPEG, PNG, WEBP yoki HEIC rasm yuklash mumkin")

    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"Fayl hajmi {MAX_FILE_SIZE_MB}MB dan oshmasligi kerak")

    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
        raise HTTPException(
            status_code=500,
            detail="SUPABASE_URL yoki SUPABASE_SERVICE_ROLE_KEY sozlanmagan (.env / Render Environment tekshiring)",
        )

    ext = Path(file.filename or "").suffix.lower() or ".jpg"
    filename = f"{uuid.uuid4().hex}{ext}"
    storage_path = f"{subfolder}/{filename}"

    upload_url = (
        f"{settings.SUPABASE_URL}/storage/v1/object/"
        f"{settings.SUPABASE_STORAGE_BUCKET}/{storage_path}"
    )

    response = requests.post(
        upload_url,
        headers={
            "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
            "apikey": settings.SUPABASE_SERVICE_ROLE_KEY,
            "Content-Type": file.content_type,
            "x-upsert": "true",
        },
        data=contents,
        timeout=30,
    )

    if response.status_code not in (200, 201):
        raise HTTPException(
            status_code=502,
            detail=f"Rasmni Supabase Storage'ga yuklashda xato: {response.status_code} {response.text}",
        )

    public_url = (
        f"{settings.SUPABASE_URL}/storage/v1/object/public/"
        f"{settings.SUPABASE_STORAGE_BUCKET}/{storage_path}"
    )
    return public_url
