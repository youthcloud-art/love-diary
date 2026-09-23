from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.config import settings
from app.database import Base, engine
from app.routers import auth, entries, media, spaces

settings.uploads.mkdir(parents=True, exist_ok=True)
Base.metadata.create_all(engine)
app = FastAPI(title="恋爱日记 API", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=[x.strip() for x in settings.cors_origins.split(",")], allow_methods=["*"], allow_headers=["*"])
app.include_router(auth.router); app.include_router(spaces.router); app.include_router(entries.router); app.include_router(media.router)
app.mount("/uploads", StaticFiles(directory=settings.uploads), name="uploads")


@app.get("/api/v1/health")
def health(): return {"status": "ok"}

