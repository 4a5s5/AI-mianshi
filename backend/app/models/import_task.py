from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime
from ..core.database import Base


class ImportTask(Base):
    __tablename__ = "imports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    file_name = Column(String(200), nullable=False)
    file_type = Column(String(10), nullable=False)  # txt/pdf
    import_type = Column(String(20), nullable=False)  # single/paper
    status = Column(String(20), nullable=False)  # pending/running/success/failed
    raw_text = Column(Text, nullable=True)
    result_summary = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
