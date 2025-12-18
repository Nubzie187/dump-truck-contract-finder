"""Rule-based scoring system for contract awards."""
from typing import Dict, List
import json


# Keyword weights for scoring
KEYWORD_WEIGHTS = {
    "dump truck": 10,
    "dumptruck": 10,
    "dump-truck": 10,
    "hauling": 8,
    "haul": 8,
    "earthwork": 7,
    "excavation": 6,
    "grading": 6,
    "fill": 5,
    "aggregate": 5,
    "gravel": 5,
    "stone": 4,
    "sand": 4,
    "material hauling": 9,
    "trucking": 7,
    "transport": 6,
}


def score_contract(description: str, contract_id: str = "", awarded_to: str = "") -> Dict:
    """
    Score a contract based on keyword matching in description and other fields.
    
    Args:
        description: Contract description text
        contract_id: Contract identifier (optional)
        awarded_to: Awarded company name (optional)
        
    Returns:
        Dictionary with 'score' (int) and 'score_reasons' (list of strings)
    """
    score = 0
    reasons = []
    
    # Normalize text for case-insensitive matching
    text_to_search = f"{description} {contract_id} {awarded_to}".lower()
    
    # Check each keyword
    for keyword, weight in KEYWORD_WEIGHTS.items():
        if keyword.lower() in text_to_search:
            score += weight
            reasons.append(f"Matched keyword '{keyword}' (+{weight} points)")
    
    # Bonus for multiple relevant keywords
    matches = sum(1 for kw in KEYWORD_WEIGHTS.keys() if kw.lower() in text_to_search)
    if matches > 3:
        bonus = (matches - 3) * 2
        score += bonus
        reasons.append(f"Multiple relevant keywords bonus (+{bonus} points)")
    
    return {
        "score": score,
        "score_reasons": json.dumps(reasons) if reasons else None
    }

