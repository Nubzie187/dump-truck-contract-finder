"""API route handlers."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional

from ..database import get_db
from ..models import ContractAward, ContractStatus
from ..schemas import (
    ContractAwardResponse,
    IngestResponse,
    StatusUpdate,
    HealthResponse,
    LeadFilterParams
)
from ..ingest.runner import run_ingestion

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint."""
    try:
        # Test database connection
        db.execute(text("SELECT 1"))
        return HealthResponse(status="healthy", database="connected")
    except Exception as e:
        return HealthResponse(status="unhealthy", database=f"error: {str(e)}")


@router.post("/ingest/run", response_model=IngestResponse)
async def run_ingest(db: Session = Depends(get_db)):
    """
    Run ingestion for all sources (KYTC and INDOT).
    Normalizes, scores, and upserts contracts into database.
    """
    try:
        result = run_ingestion(db)
        return IngestResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


@router.get("/leads", response_model=List[ContractAwardResponse])
async def get_leads(
    state: Optional[str] = Query(None, description="Filter by state (KY or IN)"),
    status: Optional[str] = Query(None, description="Filter by status (new/contacted/ignored/converted)"),
    min_score: Optional[int] = Query(None, description="Minimum score threshold"),
    db: Session = Depends(get_db)
):
    """
    Get leads (contract awards) sorted by score descending.
    Supports filtering by state, status, and minimum score.
    """
    query = db.query(ContractAward)
    
    # Apply filters
    if state:
        query = query.filter(ContractAward.state == state.upper())
    
    if status:
        try:
            status_enum = ContractStatus(status.lower())
            query = query.filter(ContractAward.status == status_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
    
    if min_score is not None:
        query = query.filter(ContractAward.score >= min_score)
    
    # Sort by score descending
    contracts = query.order_by(ContractAward.score.desc()).all()
    
    return contracts


@router.post("/leads/{lead_id}/status", response_model=ContractAwardResponse)
async def update_lead_status(
    lead_id: int,
    status_update: StatusUpdate,
    db: Session = Depends(get_db)
):
    """
    Update the status of a lead (contract award).
    """
    contract = db.query(ContractAward).filter(ContractAward.id == lead_id).first()
    
    if not contract:
        raise HTTPException(status_code=404, detail=f"Lead with id {lead_id} not found")
    
    # Update status
    try:
        contract.status = ContractStatus(status_update.status.value)
        db.commit()
        db.refresh(contract)
        return contract
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid status: {status_update.status}")

