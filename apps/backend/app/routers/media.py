from io import BytesIO
from uuid import uuid4
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from PIL import Image
from sqlalchemy.orm import Session
from app.config import settings
from app.database import get_db
from app.deps import current_user, membership
from app.models import Media, User

router = APIRouter(prefix="/api/v1/media", tags=["media"])
ALLOWED = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp", "image/gif": "gif"}


@router.post("")
def upload(file: UploadFile = File(...), user: User = Depends(current_user), db: Session = Depends(get_db)):
    kind = file.content_type or ""
    if kind not in ALLOWED: raise HTTPException(400, "仅支持 JPG、PNG、WebP、GIF 图片")
    data = file.file.read(8 * 1024 * 1024 + 1)
    if len(data) > 8 * 1024 * 1024: raise HTTPException(400, "图片不能超过 8MB")
    m = membership(user, db); folder = settings.uploads / m.space_id; folder.mkdir(parents=True, exist_ok=True)
    name = f"{uuid4().hex}.{ALLOWED[kind]}"; (folder / name).write_bytes(data)
    thumb_name = f"{uuid4().hex}_thumb.jpg"; thumb_url = None
    try:
        image = Image.open(BytesIO(data)).convert("RGB"); image.thumbnail((480, 480)); image.save(folder / thumb_name, "JPEG", quality=82)
        thumb_url = f"{settings.public_base_url}/uploads/{m.space_id}/{thumb_name}"
    except Exception: pass
    row = Media(space_id=m.space_id, uploader_id=user.id, url=f"{settings.public_base_url}/uploads/{m.space_id}/{name}", thumb_url=thumb_url, content_type=kind)
    db.add(row); db.commit(); db.refresh(row)
    return {"id": row.id, "url": row.url, "thumb_url": row.thumb_url, "content_type": row.content_type}

