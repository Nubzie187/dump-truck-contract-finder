"""Pydantic schemas for request/response validation."""
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List
from datetime import date, datetime
from enum import Enum


class ContractStatusEnum(str, Enum):
    """Contract status enumeration for API."""
    NEW = "new"
    CONTACTED = "contacted"
    IGNORED = "ignored"
    CONVERTED = "converted"


class ContractAwardBase(BaseModel):
    """Base contract award schema."""
    state: str = Field(..., description="State code (KY or IN)", max_length=2)
    letting_date: date = Field(..., description="Letting date")
    contract_id: str = Field(..., description="Contract identifier")
    awarded_to: str = Field(..., description="Awarded to company name")
    description: str = Field(..., description="Contract description")
    amount: Optional[str] = Field(None, description="Contract amount")
    source_url: str = Field(..., description="Source URL")
    score: int = Field(0, description="Score")
    score_reasons: Optional[str] = Field(None, description="JSON string of score reasons")
    status: ContractStatusEnum = Field(ContractStatusEnum.NEW, description="Status")


class ContractAwardCreate(ContractAwardBase):
    """Schema for creating a contract award."""
    pass


class ContractAwardResponse(ContractAwardBase):
    """Schema for contract award response."""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class IngestResponse(BaseModel):
    """Response schema for ingest operation."""
    kytc_count: int = Field(..., description="Number of contracts from KYTC")
    indot_count: int = Field(..., description="Number of contracts from INDOT")
    total_processed: int = Field(..., description="Total contracts processed")
    total_upserted: int = Field(..., description="Total contracts upserted")


class LeadFilterParams(BaseModel):
    """Query parameters for filtering leads."""
    state: Optional[str] = Field(None, description="Filter by state (KY or IN)")
    status: Optional[ContractStatusEnum] = Field(None, description="Filter by status")
    min_score: Optional[int] = Field(None, description="Minimum score threshold")


class StatusUpdate(BaseModel):
    """Schema for updating contract status."""
    status: ContractStatusEnum = Field(..., description="New status")


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "healthy"
    database: str = "connected"

