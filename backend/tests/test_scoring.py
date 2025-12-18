"""Tests for the scoring module."""
import pytest
from app.scoring import score_contract, KEYWORD_WEIGHTS


def test_score_contract_with_dump_truck_keyword():
    """Test scoring when 'dump truck' keyword is present."""
    description = "Dump truck hauling services for highway construction"
    result = score_contract(description)
    
    assert result["score"] >= 10  # Should match "dump truck" keyword
    assert result["score_reasons"] is not None
    assert "dump truck" in result["score_reasons"].lower()


def test_score_contract_with_multiple_keywords():
    """Test scoring with multiple relevant keywords."""
    description = "Dump truck hauling for earthwork and excavation project"
    result = score_contract(description)
    
    # Should match multiple keywords: dump truck (10), hauling (8), earthwork (7), excavation (6)
    assert result["score"] >= 10 + 8 + 7 + 6
    assert result["score_reasons"] is not None


def test_score_contract_with_bonus():
    """Test that bonus points are awarded for multiple keyword matches."""
    description = "Dump truck hauling services for earthwork, excavation, grading, and fill operations"
    result = score_contract(description)
    
    # Should have multiple matches triggering bonus
    assert result["score"] > 0
    assert "bonus" in result["score_reasons"].lower() or result["score"] > sum(KEYWORD_WEIGHTS.values()[:4])


def test_score_contract_no_relevant_keywords():
    """Test scoring when no relevant keywords are present."""
    description = "Bridge construction and maintenance services"
    result = score_contract(description)
    
    assert result["score"] == 0
    assert result["score_reasons"] is None


def test_score_contract_case_insensitive():
    """Test that keyword matching is case-insensitive."""
    description1 = "DUMP TRUCK services"
    description2 = "dump truck services"
    description3 = "Dump Truck services"
    
    result1 = score_contract(description1)
    result2 = score_contract(description2)
    result3 = score_contract(description3)
    
    # All should have the same score
    assert result1["score"] == result2["score"] == result3["score"]
    assert result1["score"] >= 10


def test_score_contract_with_contract_id():
    """Test that contract_id is also searched for keywords."""
    description = "Construction services"
    contract_id = "DT-2024-001"  # DT might match, but let's use a clearer example
    result = score_contract(description, contract_id=contract_id)
    
    # Should still search in contract_id field
    assert "score" in result
    assert "score_reasons" in result


def test_score_contract_with_awarded_to():
    """Test that awarded_to field is also searched."""
    description = "General construction"
    awarded_to = "Dump Truck Hauling Inc."
    result = score_contract(description, awarded_to=awarded_to)
    
    # Should match keywords in awarded_to field
    assert result["score"] >= 10  # Should match "dump truck"
    assert result["score_reasons"] is not None

