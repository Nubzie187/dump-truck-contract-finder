"""Ingestion orchestrator that runs all ingest modules."""
from typing import List, Dict
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime

from ..ingest.kytc import ingest_kytc, normalize_kytc
from ..ingest.indot import ingest_indot, normalize_indot
from ..models import ContractAward
from ..scoring import score_contract


def run_ingestion(db: Session) -> Dict:
    """
    Run all ingestion modules, normalize, score, and upsert into database.
    
    Args:
        db: Database session
        
    Returns:
        Dictionary with counts of processed and upserted contracts
    """
    kytc_count = 0
    indot_count = 0
    total_upserted = 0
    
    # Ingest KYTC
    kytc_raw = ingest_kytc()
    kytc_normalized = normalize_kytc(kytc_raw)
    kytc_count = len(kytc_normalized)
    
    # Ingest INDOT
    indot_raw = ingest_indot()
    indot_normalized = normalize_indot(indot_raw)
    indot_count = len(indot_normalized)
    
    # Combine all contracts
    all_contracts = kytc_normalized + indot_normalized
    
    # Process each contract: score and upsert
    for contract_data in all_contracts:
        # Score the contract
        scoring_result = score_contract(
            description=contract_data.get("description", ""),
            contract_id=contract_data.get("contract_id", ""),
            awarded_to=contract_data.get("awarded_to", "")
        )
        
        # Check if contract already exists (by state + contract_id)
        existing = db.query(ContractAward).filter(
            and_(
                ContractAward.state == contract_data["state"],
                ContractAward.contract_id == contract_data["contract_id"]
            )
        ).first()
        
        if existing:
            # Update existing contract
            existing.letting_date = contract_data["letting_date"]
            existing.awarded_to = contract_data["awarded_to"]
            existing.description = contract_data["description"]
            existing.amount = contract_data.get("amount")
            existing.source_url = contract_data["source_url"]
            existing.score = scoring_result["score"]
            existing.score_reasons = scoring_result["score_reasons"]
            # Don't update status if it's been manually changed from NEW
            if existing.status.value == "new":
                pass  # Keep as new
        else:
            # Create new contract
            new_contract = ContractAward(
                state=contract_data["state"],
                letting_date=contract_data["letting_date"],
                contract_id=contract_data["contract_id"],
                awarded_to=contract_data["awarded_to"],
                description=contract_data["description"],
                amount=contract_data.get("amount"),
                source_url=contract_data["source_url"],
                score=scoring_result["score"],
                score_reasons=scoring_result["score_reasons"]
            )
            db.add(new_contract)
        
        total_upserted += 1
    
    # Commit all changes
    db.commit()
    
    return {
        "kytc_count": kytc_count,
        "indot_count": indot_count,
        "total_processed": len(all_contracts),
        "total_upserted": total_upserted
    }

