from datetime import timezone
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import extract, or_
from sqlalchemy.orm import Session, joinedload
from app.database import get_db
from app.deps import current_user, membership
from app.models import Entry, Media, User
from app.schemas import EntryIn, EntryPatch

router = APIRouter(prefix="/api/v1/entries", tags=["entries"])


def serialize(e: Entry):
    return {"id": e.id, "space_id": e.space_id, "author_id": e.author_id, "author_nickname": e.author.nickname, "title": e.title, "body": e.body, "mood": e.mood, "happened_on": e.happened_on, "visibility": e.visibility, "created_at": e.created_at, "updated_at": e.updated_at, "media": [{"id": m.id, "url": m.url, "thumb_url": m.thumb_url, "content_type": m.content_type} for m in e.media]}


def query(db: Session, user: User):
    m = membership(user, db)
    return db.query(Entry).options(joinedload(Entry.author), joinedload(Entry.media)).filter(Entry.space_id == m.space_id, or_(Entry.visibility == "shared", Entry.author_id == user.id))


@router.get("")
def listing(year: int | None = None, month: int | None = None, user: User = Depends(current_user), db: Session = Depends(get_db)):
    q = query(db, user)
    if year: q = q.filter(extract("year", Entry.happened_on) == year)
    if month: q = q.filter(extract("month", Entry.happened_on) == month)
    return [serialize(e) for e in q.order_by(Entry.happened_on.desc()).all()]


@router.get("/calendar")
def calendar(year: int, month: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    rows = listing(year, month, user, db); grouped = {}
    for e in rows:
        key = str(e["happened_on"]); grouped.setdefault(key, {"date": key, "count": 0, "moods": []}); grouped[key]["count"] += 1
        if e["mood"]: grouped[key]["moods"].append(e["mood"])
    return list(grouped.values())


@router.get("/{entry_id}")
def detail(entry_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    e = query(db, user).filter(Entry.id == entry_id).first()
    if not e: raise HTTPException(404, "日记不存在")
    return serialize(e)


def attach(db: Session, e: Entry, media_ids: list[str], user: User):
    m = membership(user, db)
    db.query(Media).filter(Media.id.in_(media_ids), Media.space_id == m.space_id, Media.entry_id.is_(None)).update({Media.entry_id: e.id}, synchronize_session=False) if media_ids else None


@router.post("")
def create(data: EntryIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    m = membership(user, db); e = Entry(space_id=m.space_id, author_id=user.id, **data.model_dump(exclude={"media_ids"}))
    db.add(e); db.flush(); attach(db, e, data.media_ids, user); db.commit(); db.refresh(e)
    return detail(e.id, user, db)


@router.patch("/{entry_id}")
def update(entry_id: str, data: EntryPatch, user: User = Depends(current_user), db: Session = Depends(get_db)):
    e = db.get(Entry, entry_id)
    if not e or e.author_id != user.id: raise HTTPException(403, "只能编辑自己的日记")
    server_time = e.updated_at.replace(tzinfo=timezone.utc) if e.updated_at.tzinfo is None else e.updated_at
    client_time = data.updated_at.replace(tzinfo=timezone.utc) if data.updated_at.tzinfo is None else data.updated_at
    if abs((server_time - client_time).total_seconds()) > .001: raise HTTPException(409, "内容已在另一端更新，请刷新")
    for key, value in data.model_dump(exclude={"updated_at", "media_ids"}).items(): setattr(e, key, value)
    db.query(Media).filter_by(entry_id=e.id).update({Media.entry_id: None}); attach(db, e, data.media_ids, user); db.commit(); db.refresh(e)
    return detail(e.id, user, db)


@router.delete("/{entry_id}", status_code=204)
def delete(entry_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    e = db.get(Entry, entry_id)
    if not e or e.author_id != user.id: raise HTTPException(403, "只能删除自己的日记")
    db.delete(e); db.commit(); return Response(status_code=204)

