from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from ..core.database import Base


class AnalysisResult(Base):
    __tablename__ = "analysis_results"
    __table_args__ = (
        UniqueConstraint('answer_id', name='uq_analysis_answer_id'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    answer_id = Column(Integer, ForeignKey("answers.id", ondelete="CASCADE"), nullable=False)
    paper_session_id = Column(String(50), nullable=True)  # 套卷整体分析
    analysis_type = Column(String(30), nullable=False)  # single/paper/history_single/history_paper
    score = Column(Float, nullable=True)  # 总分
    score_details = Column(Text, nullable=True)  # JSON：各维度得分
    feedback = Column(Text, nullable=True)  # AI反馈
    model_answer = Column(Text, nullable=True)  # 模范作答
    model_name = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关联
    answer = relationship("Answer", back_populates="analysis")
