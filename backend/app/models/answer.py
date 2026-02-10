from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from ..core.database import Base


class Answer(Base):
    __tablename__ = "answers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    mode = Column(String(20), nullable=False)  # "single" | "paper"
    question_id = Column(Integer, ForeignKey("questions.id", ondelete="RESTRICT"), nullable=False)
    paper_id = Column(Integer, ForeignKey("papers.id", ondelete="SET NULL"), nullable=True)
    paper_session_id = Column(String(50), nullable=True)  # 套卷练习会话ID
    transcript = Column(Text, nullable=True)  # 转写文本
    audio_url = Column(String(500), nullable=True)  # 音频地址
    duration_seconds = Column(Integer, nullable=True)  # 作答时长
    started_at = Column(DateTime, nullable=False)
    finished_at = Column(DateTime, nullable=True)
    practice_date = Column(String(10), nullable=False)  # YYYY-MM-DD
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关联
    question = relationship("Question", back_populates="answers")
    paper = relationship("Paper", back_populates="answers")
    analysis = relationship("AnalysisResult", back_populates="answer", uselist=False)
