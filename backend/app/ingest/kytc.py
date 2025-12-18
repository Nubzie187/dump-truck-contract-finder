"""KYTC (Kentucky Transportation Cabinet) ingestion module."""
from typing import List, Dict
from datetime import date, datetime
import httpx
from bs4 import BeautifulSoup
import re
from urllib.parse import unquote


def ingest_kytc() -> List[Dict]:
    """
    Fetch KYTC contract awards from HTML pages.
    
    Returns:
        List of raw contract dictionaries with keys:
        - letting_date (date or ISO string)
        - contract_id
        - awarded_to
        - description
        - amount (None if not present)
        - source_url
    """
    contracts = []
    
    # Temporarily bypass lettings list discovery - use hardcoded date for testing
    letting_dates = ["11/20/2025"]
    
    letting_contracts_base = "https://transportation.ky.gov/Construction-Procurement/Pages/Letting-Contracts.aspx"
    
    # Headers with polite User-Agent
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        with httpx.Client(headers=headers, timeout=30.0) as client:
            # For each letting date, fetch the contracts page
            for date_str in letting_dates:
                try:
                    # Construct the full URL
                    letting_url = f"{letting_contracts_base}?letting={date_str.replace('/', '%2F')}"
                    
                    # Fetch the letting contracts page
                    contracts_response = client.get(letting_url)
                    contracts_response.raise_for_status()
                    
                    contracts_soup = BeautifulSoup(contracts_response.text, 'html.parser')
                    
                    # Parse contract data from table/div
                    table = contracts_soup.find('table')
                    if not table:
                        # Try alternative selectors
                        table = contracts_soup.find('div', class_=re.compile(r'table|contract', re.I))
                    
                    if table:
                        # Extract all text cells into a flat list
                        flat_text = table.get_text(" | ", strip=True)
                        items = flat_text.split(" | ")
                        
                        # Expected header: ["Call","Status","Awarded To","Contract ID","District","County","Project Description"]
                        expected_header = ["Call", "Status", "Awarded To", "Contract ID", "District", "County", "Project Description"]
                        
                        # Find the index where the header starts
                        header_start_idx = None
                        for i in range(len(items) - len(expected_header) + 1):
                            # Check if the next N items match the header (case-insensitive, allowing for variations)
                            potential_header = [item.strip() for item in items[i:i+len(expected_header)]]
                            # Check if all expected header terms are present in order
                            matches = 0
                            for j, expected in enumerate(expected_header):
                                if expected.lower() in potential_header[j].lower():
                                    matches += 1
                            if matches >= len(expected_header) - 1:  # Allow one mismatch
                                header_start_idx = i
                                break
                        
                        if header_start_idx is None:
                            print("rows found: 0 (header not found)")
                        else:
                            # Remove the header tokens
                            data_items = items[header_start_idx + len(expected_header):]
                            
                            # Known status values
                            known_statuses = ["Awarded", "Withdrawn", "Rejected"]
                            
                            # Streaming parser: iterate through tokens
                            i = 0
                            while i < len(data_items):
                                token = data_items[i].strip()
                                
                                # Check if token looks like a call number (numeric string)
                                if token and token.isdigit() and i + 1 < len(data_items):
                                    next_token = data_items[i + 1].strip()
                                    
                                    # Check if next token is a known status
                                    if next_token in known_statuses:
                                        call = token
                                        status = next_token
                                        i += 2  # Move past call and status
                                        
                                        # If status is "Awarded", collect fields until next call/status pair
                                        if status == "Awarded":
                                            awarded_to = ""
                                            contract_id = ""
                                            description_parts = []
                                            field_state = "awarded_to"
                                            
                                            # Collect fields until we hit the next call/status pair
                                            while i < len(data_items):
                                                current_token = data_items[i].strip()
                                                
                                                # Check if we've hit the next call/status pair
                                                if current_token.isdigit() and i + 1 < len(data_items):
                                                    next_check = data_items[i + 1].strip()
                                                    if next_check in known_statuses:
                                                        break  # Found next record, stop collecting
                                                
                                                if not current_token:
                                                    i += 1
                                                    continue
                                                
                                                # Collect fields in order: awarded_to, contract_id, county (skip), description
                                                if field_state == "awarded_to":
                                                    # First token is awarded_to
                                                    awarded_to = current_token
                                                    field_state = "contract_id"
                                                elif field_state == "contract_id":
                                                    # Next token that is all digits is contract_id
                                                    if current_token.isdigit():
                                                        contract_id = current_token
                                                        field_state = "county"
                                                    # If not digits, might be continuation, but per pattern should be digits
                                                elif field_state == "county":
                                                    # Skip county token (ignore it)
                                                    field_state = "description"
                                                    # Don't increment i here, let description handle it
                                                    i += 1
                                                    continue
                                                else:  # field_state == "description"
                                                    # All remaining tokens go to description
                                                    description_parts.append(current_token)
                                                
                                                i += 1
                                            
                                            # Only emit if we have required fields
                                            if awarded_to and contract_id:
                                                # Parse the letting date
                                                try:
                                                    # Date format is typically MM/DD/YYYY
                                                    date_parts = date_str.split('/')
                                                    if len(date_parts) == 3:
                                                        letting_date = date(
                                                            int(date_parts[2]),
                                                            int(date_parts[0]),
                                                            int(date_parts[1])
                                                        )
                                                    else:
                                                        # Try ISO format or other formats
                                                        letting_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                                                except (ValueError, IndexError):
                                                    # If parsing fails, use the string as-is
                                                    letting_date = date_str
                                                
                                                contract_data = {
                                                    "letting_date": letting_date,
                                                    "contract_id": contract_id,
                                                    "awarded_to": awarded_to,
                                                    "description": " ".join(description_parts) if description_parts else "",
                                                    "amount": None,
                                                    "source_url": letting_url
                                                }
                                                
                                                contracts.append(contract_data)
                                        else:
                                            # For non-Awarded status, skip until next call/status pair
                                            while i < len(data_items):
                                                current_token = data_items[i].strip()
                                                if current_token.isdigit() and i + 1 < len(data_items):
                                                    next_check = data_items[i + 1].strip()
                                                    if next_check in known_statuses:
                                                        break  # Found next record
                                                i += 1
                                    else:
                                        i += 1
                                else:
                                    i += 1
                    
                except httpx.HTTPError as e:
                    # Skip this letting date if there's an error
                    continue
                except Exception as e:
                    # Skip this letting date on any other error
                    continue
        
    
    except httpx.HTTPError as e:
        # Return empty list if main page fails
        return []
    except Exception as e:
        # Return empty list on any other error
        return []
    
    return contracts


def normalize_kytc(raw_contracts: List[Dict]) -> List[Dict]:
    """
    Normalize KYTC contract data to standard format.
    
    Args:
        raw_contracts: List of raw contract dictionaries from KYTC
        
    Returns:
        List of normalized contract dictionaries
    """
    normalized = []
    for contract in raw_contracts:
        normalized.append({
            "state": "KY",
            "letting_date": contract.get("letting_date"),
            "contract_id": contract.get("contract_id", ""),
            "awarded_to": contract.get("awarded_to", ""),
            "description": contract.get("description", ""),
            "amount": contract.get("amount"),
            "source_url": contract.get("source_url", ""),
        })
    return normalized

