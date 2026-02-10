from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class PaperItemBase(BaseModel):
    question_id: int
    sort_order: int


class PaperBase(BaseModel):
    title: str
    description: Optional[str] = None
    time_limit_seconds: Optional[int] = None


class PaperCreate(PaperBase):
    question_ids: Optional[list[int]] = None


class PaperUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    time_limit_seconds: Optional[int] = None


class PaperItemResponse(BaseModel):
    id: int
    question_id: int
    sort_order: int

    class Config:
        from_attributes = True


class PaperResponse(PaperBase):
    id: int
    items: list[PaperItemResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PaperListResponse(BaseModel):
    items: list[PaperResponse]
    total: int
