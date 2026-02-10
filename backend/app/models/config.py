from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from datetime import datetime
from ..core.database import Base


class ModelConfig(Base):
    __tablename__ = "model_configs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    base_url = Column(String(500), nullable=False)
    api_key = Column(String(500), nullable=False)
    model_name = Column(String(100), nullable=False)
    role = Column(String(20), nullable=False)  # "analyze" | "import"
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def api_key_masked(self) -> str | None:
        if not self.api_key:
            return None
        key = self.api_key
        if len(key) < 8:
            return "***"
        return f"{key[:3]}...{key[-4:]}"


class Prompt(Base):
    __tablename__ = "prompts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    prompt_type = Column(String(50), unique=True, nullable=False)
    title = Column(String(100), nullable=False)
    content = Column(Text, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SpeechConfig(Base):
    __tablename__ = "speech_configs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    provider = Column(String(20), nullable=False)  # "web_speech" | "whisper"
    whisper_api_url = Column(String(500), nullable=True)
    whisper_api_key = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
