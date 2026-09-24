from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BACKEND_DIR / ".env", extra="ignore")
    secret_key: str = "development-secret-key-change-me-32"
    database_url: str = f"sqlite:///{(BACKEND_DIR / 'var' / 'love_diary.db').as_posix()}"
    wechat_appid: str = ""
    wechat_secret: str = ""
    public_base_url: str = "http://127.0.0.1:8000"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    upload_dir: str = str(BACKEND_DIR / "uploads")

    @property
    def uploads(self) -> Path:
        return Path(self.upload_dir).resolve()


settings = Settings()
