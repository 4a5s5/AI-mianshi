from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class QuestionBase(BaseModel):
    content: str
    category: str = "自定义"
    analysis: Optional[str] = None
    reference_answer: Optional[str] = None
    image_url: Optional[str] = None
    tags: Optional[str] = None
    source: Optional[str] = None


class QuestionCreate(QuestionBase):
    pass


class QuestionUpdate(BaseModel):
    category: Optional[str] = None
    content: Optional[str] = None
    analysis: Optional[str] = None
    reference_answer: Optional[str] = None
    image_url: Optional[str] = None
    tags: Optional[str] = None


class QuestionResponse(QuestionBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class QuestionListResponse(BaseModel):
    items: list[QuestionResponse]
    total: int
    page: int
    page_size: int


class BatchDeleteRequest(BaseModel):
    ids: list[int]


class BatchDeleteResponse(BaseModel):
    deleted_count: int
    message: str = "删除成功"
