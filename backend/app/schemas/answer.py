from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class AnswerCreate(BaseModel):
    mode: str  # "single" | "paper"
    question_id: int
    paper_id: Optional[int] = None
    paper_session_id: Optional[str] = None
    transcript: Optional[str] = None
    audio_url: Optional[str] = None
    duration_seconds: Optional[int] = None
    started_at: datetime
    finished_at: Optional[datetime] = None


class AnswerResponse(BaseModel):
    id: int
    mode: str
    question_id: int
    paper_id: Optional[int] = None
    paper_session_id: Optional[str] = None
    transcript: Optional[str] = None
    duration_seconds: Optional[int] = None
    started_at: datetime
    finished_at: Optional[datetime] = None
    practice_date: str
    created_at: datetime

    class Config:
        from_attributes = True


class AnalysisResultResponse(BaseModel):
    id: int
    answer_id: int
    analysis_type: str
    score: Optional[float] = None
    score_details: Optional[str] = None
    feedback: Optional[str] = None
    model_answer: Optional[str] = None
    model_name: str
    created_at: datetime

    class Config:
        from_attributes = True


class AnswerWithAnalysis(AnswerResponse):
    analysis: Optional[AnalysisResultResponse] = None
    question_content: Optional[str] = None


class HistoryAnalyzeRequest(BaseModel):
    answer_ids: list[int]
    analysis_type: str  # "history_single" | "history_paper"


class PaperAnalyzeRequest(BaseModel):
    paper_session_id: str
