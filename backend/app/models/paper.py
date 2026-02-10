from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from ..core.database import Base


class Paper(Base):
    __tablename__ = "papers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    time_limit_seconds = Column(Integer, nullable=True)  # 作答时限
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联
    items = relationship("PaperItem", back_populates="paper", cascade="all, delete-orphan")
    answers = relationship("Answer", back_populates="paper")


class PaperItem(Base):
    __tablename__ = "paper_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    paper_id = Column(Integer, ForeignKey("papers.id", ondelete="CASCADE"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id", ondelete="RESTRICT"), nullable=False)
    sort_order = Column(Integer, nullable=False)

    # 关联
    paper = relationship("Paper", back_populates="items")
    question = relationship("Question", back_populates="paper_items")
