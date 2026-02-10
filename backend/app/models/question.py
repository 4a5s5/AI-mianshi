from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from ..core.database import Base


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    category = Column(String(50), nullable=False)  # 题型
    content = Column(Text, nullable=False)  # 题干
    analysis = Column(Text, nullable=True)  # 解析
    reference_answer = Column(Text, nullable=True)  # 参考答案
    image_url = Column(String(500), nullable=True)  # 思维导图
    tags = Column(String(200), nullable=True)  # 标签
    source = Column(String(50), nullable=True)  # 来源
    is_deleted = Column(Boolean, default=False, nullable=False)  # 软删除标记
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联
    answers = relationship("Answer", back_populates="question")
    paper_items = relationship("PaperItem", back_populates="question")
