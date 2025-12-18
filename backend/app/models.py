"""SQLAlchemy database models."""
from sqlalchemy import Column, Integer, String, Date, Enum, Text, JSON, DateTime
from sqlalchemy.dialects.sqlite import JSON as SQLiteJSON
from sqlalchemy.sql import func
import enum
import uuid
from .database import Base


class ContractStatus(str, enum.Enum):
    """Contract status enumeration."""
    NEW = "new"
    CONTACTED = "contacted"
    IGNORED = "ignored"
    CONVERTED = "converted"


class ContractAward(Base):
    """Contract award model."""
    __tablename__ = "contract_awards"

    id = Column(Integer, primary_key=True, index=True)
    state = Column(String(2), nullable=False, index=True)  # "KY" or "IN"
    letting_date = Column(Date, nullable=False, index=True)
    contract_id = Column(String, nullable=False, index=True)
    awarded_to = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    amount = Column(String, nullable=True)  # Stored as string to handle various formats
    source_url = Column(String, nullable=False)
    score = Column(Integer, default=0, index=True)
    score_reasons = Column(Text, nullable=True)  # JSON stored as text
    status = Column(Enum(ContractStatus), default=ContractStatus.NEW, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<ContractAward(id={self.id}, contract_id={self.contract_id}, state={self.state}, score={self.score})>"

