"""
Proper financial data preprocessing utilities.
Handles numerical suffixes (M/B), currency symbols, and percentages correctly.
"""
import re
from typing import Union, Tuple


def normalize_financial_value(value: str) -> Tuple[float, str]:
    """
    Properly normalize financial values with suffixes and symbols.
    
    Args:
        value: Raw financial value string (e.g., "$1.5M", "25.3%", "$2.1B")
        
    Returns:
        Tuple of (normalized_float, unit)
        
    Examples:
        "$1.5M" -> (1500000.0, "USD")
        "25.3%" -> (0.253, "%")
        "$2.1B" -> (2100000000.0, "USD")
        "1.25" -> (1.25, "")
    """
    if not isinstance(value, str):
        return float(value), ""
    
    # Remove whitespace and convert to uppercase for consistent processing
    clean_value = value.strip().upper()
    
    # Extract unit information
    unit = ""
    if "$" in clean_value:
        unit = "USD"
    elif "%" in clean_value:
        unit = "%"
    
    # Remove currency symbols and percentage signs
    numeric_part = re.sub(r'[$%,]', '', clean_value)
    
    # Handle suffixes (M = millions, B = billions, K = thousands)
    multiplier = 1.0
    if numeric_part.endswith('B'):
        multiplier = 1e9
        numeric_part = numeric_part[:-1]
    elif numeric_part.endswith('M'):
        multiplier = 1e6
        numeric_part = numeric_part[:-1]
    elif numeric_part.endswith('K'):
        multiplier = 1e3
        numeric_part = numeric_part[:-1]
    
    try:
        # Convert to float and apply multiplier
        base_value = float(numeric_part)
        normalized_value = base_value * multiplier
        
        # For percentages, convert to decimal (25% -> 0.25)
        if unit == "%":
            normalized_value = normalized_value / 100.0
            
        return normalized_value, unit
    except ValueError:
        # If conversion fails, return original string and empty unit
        return value, ""


def extract_and_normalize_table_values(table_data: list) -> list:
    """
    Extract and normalize all numerical values from a table structure.
    
    Args:
        table_data: List of rows, where each row is a list of cell values
        
    Returns:
        List of normalized table data with proper numerical values
    """
    if not table_data:
        return table_data
    
    normalized_table = []
    
    for row in table_data:
        normalized_row = []
        for cell in row:
            if isinstance(cell, str) and re.search(r'[\d.,]+[MBK%$]?', cell):
                # This looks like a financial value, try to normalize it
                try:
                    normalized_value, unit = normalize_financial_value(cell)
                    # Keep the original format but store metadata about the normalized value
                    normalized_row.append({
                        "original": cell,
                        "normalized_value": normalized_value,
                        "unit": unit
                    })
                except:
                    # If normalization fails, keep original
                    normalized_row.append(cell)
            else:
                normalized_row.append(cell)
        normalized_table.append(normalized_row)
    
    return normalized_table


def is_financial_value(text: str) -> bool:
    """
    Check if a string contains a financial value that needs normalization.
    
    Args:
        text: String to check
        
    Returns:
        True if the string contains financial values, False otherwise
    """
    if not isinstance(text, str):
        return False
    
    # Pattern to match financial values: numbers with optional suffixes and symbols
    financial_pattern = r'[$]?\d+(?:,\d{3})*(?:\.\d+)?[MBK%]?'
    return bool(re.search(financial_pattern, text))


# Example usage and tests
if __name__ == "__main__":
    # Test cases
    test_values = [
        "$1.5M",     # Should become (1500000.0, "USD")
        "25.3%",     # Should become (0.253, "%")
        "$2.1B",     # Should become (2100000000.0, "USD")
        "1,234.56",  # Should become (1234.56, "")
        "500K",      # Should become (500000.0, "")
        "invalid",   # Should remain ("invalid", "")
    ]
    
    print("Testing financial value normalization:")
    for value in test_values:
        normalized, unit = normalize_financial_value(value)
        print(f"{value:>10} -> {normalized:>12} ({unit})")