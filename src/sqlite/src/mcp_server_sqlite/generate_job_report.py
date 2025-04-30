import sys
from typing import Dict, Any, Optional, Tuple
from pathlib import Path
from functools import lru_cache  # Import for caching
# Import the original formatting function name from ve_logic
from .ve_logic import generate_formatted_job_report
from .db_handler import DatabaseHandler
import re # Import re for clean_dot_code if needed

def clean_dot_code(dot_code: str) -> Tuple[Optional[int], Optional[str]]:
    """
    Cleans and converts a DOT code into both Ncode (INTEGER) and Code (TEXT) formats.
    Handles multiple input formats:
    - ###.###-### (standard format with periods and hyphen)
    - ######### (9-digit numeric format)
    - #.##.## (shortened format with missing zeros)
    - ###-###-### (alternative format with hyphens)
    
    Args:
        dot_code: A DOT code in various possible formats
        
    Returns:
        A tuple of (Ncode, Code) where:
        - Ncode is an INTEGER (e.g., 1061010 for 001.061-010)
        - Code is TEXT (e.g., "001.061-010")
    """
    if not dot_code or not isinstance(dot_code, str):
        return None, None
        
    try:
        # Remove any whitespace
        dot_code = dot_code.strip()
        
        # Case 1: Standard format ###.###-###
        if '.' in dot_code and '-' in dot_code:
            parts = dot_code.replace('-', '.').split('.')
            if len(parts) != 3:
                return None, None
                
            # Parse each part, handling potential non-numeric values
            try:
                group = int(parts[0])
                subgroup = int(parts[1])
                suffix = int(parts[2])
            except ValueError:
                return None, None
                
            # Format as Ncode (9-digit integer)
            ncode_str = f"{group:03d}{subgroup:03d}{suffix:03d}"
            ncode = int(ncode_str)
            
            # Format as standard DOT code text
            code_text = f"{group:03d}.{subgroup:03d}-{suffix:03d}"
            
            return ncode, code_text
            
        # Case 2: Pure numeric format (9 digits)
        elif dot_code.isdigit():
            if len(dot_code) == 9:
                # Format is #########
                ncode = int(dot_code)
                
                # Extract parts
                group = int(dot_code[:3])
                subgroup = int(dot_code[3:6])
                suffix = int(dot_code[6:])
                
                # Format Code as TEXT
                code_text = f"{group:03d}.{subgroup:03d}-{suffix:03d}"
                
                return ncode, code_text
            # Handle shorter numeric formats by padding with zeros
            elif len(dot_code) < 9:
                # Pad to 9 digits
                padded = dot_code.zfill(9)
                ncode = int(padded)
                
                # Extract parts
                group = int(padded[:3])
                subgroup = int(padded[3:6])
                suffix = int(padded[6:])
                
                # Format Code as TEXT
                code_text = f"{group:03d}.{subgroup:03d}-{suffix:03d}"
                
                return ncode, code_text
        
        # Case 3: Alternative formats with hyphens only (###-###-###)
        elif '-' in dot_code and '.' not in dot_code:
            parts = dot_code.split('-')
            if len(parts) != 3:
                return None, None
                
            try:
                group = int(parts[0])
                subgroup = int(parts[1])
                suffix = int(parts[2])
            except ValueError:
                return None, None
                
            # Format as Ncode (9-digit integer)
            ncode_str = f"{group:03d}{subgroup:03d}{suffix:03d}"
            ncode = int(ncode_str)
            
            # Format as standard DOT code text
            code_text = f"{group:03d}.{subgroup:03d}-{suffix:03d}"
            
            return ncode, code_text
            
        # No recognized format
        return None, None
    except (ValueError, IndexError) as e:
        print(f"Error parsing DOT code '{dot_code}': {e}")
        return None, None

def get_job_data(db: DatabaseHandler, search_term: str) -> Optional[Dict[str, Any]]:
    """
    Retrieves job data from the database based on a search term.
    The search term can be:
    - A DOT code in ######### format
    - A DOT code in ###.###-### format
    - A job title or partial title

    Args:
        db: The database handler instance
        search_term: The search term to use (DOT code or job title)

    Returns:
        A dictionary containing the job data if found, None otherwise
    """
    if not search_term or not search_term.strip():
        print("Error: Empty search term provided")
        return None
        
    try:
        # First try to find by exact code match if it looks like a DOT code
        ncode, code_text = clean_dot_code(search_term)
        if ncode is not None:
            # Use the cached lookup to improve performance
            db_path_str = str(db.db_path)
            job_data = cached_get_job_by_code(ncode, code_text, db_path_str)
            
            if job_data:
                # Ensure keys expected by generate_formatted_job_report are present
                return _ensure_required_fields(job_data)
        
        # If no results or not a DOT code, try finding by job title using find_job_data
        results = db.find_job_data(search_term)
        if results:
            # Map the database fields to the expected keys
            job_data = results[0]
            return _ensure_required_fields(job_data)
        
        print(f"No job data found for search term: {search_term}")
        return None
    except Exception as e:
        print(f"Error retrieving job data: {e}")
        return None

def _ensure_required_fields(job_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ensures the job data dictionary has all fields required by generate_formatted_job_report.
    Maps fields between different naming conventions that might be used and validates data integrity.
    
    Args:
        job_data: Raw job data dictionary from database query
        
    Returns:
        Dictionary with all required fields properly mapped and validated
    """
    if not job_data:
        print("Warning: Empty job data received by _ensure_required_fields")
        return {}
        
    # Make a copy to avoid modifying the original
    job_data = dict(job_data)
    
    # Map expected field names for ve_logic.generate_formatted_job_report
    field_mappings = {
        'Code': 'dotCode',                  # Mapped to dotCode for formatted reporting
        'Title': 'jobTitle',                # Mapped to jobTitle for consistent naming
        'Definitions': 'definition',        # Mapped to definition (singular)
        'dotCodeFormatted': 'dotCode',      # For results from find_job_data
        'dotCodeNumeric': 'dotCodeReal',    # For results from find_job_data
        'NCode': 'n_code',                  # Map database NCode to expected n_code field
        'SVPNum': 'svp',                    # Map SVPNum to svp
        'StrengthNum': 'strengthNum',       # Map StrengthNum to strengthNum
    }
    
    # Apply field mappings only if source field exists and target doesn't
    for source_field, target_field in field_mappings.items():
        if source_field in job_data and target_field not in job_data:
            job_data[target_field] = job_data[source_field]
    
    # Ensure required fields exist with fallback values
    required_fields_with_defaults = {
        'dotCode': job_data.get('dotCodeFormatted', job_data.get('Code', 'N/A')),
        'jobTitle': job_data.get('Title', 'Unknown Job'),
        'definition': job_data.get('Definitions', 'N/A'),
        'n_code': job_data.get('NCode', job_data.get('Ncode', 0)),
        'svp': job_data.get('SVPNum', 0),
        'strengthNum': job_data.get('StrengthNum', 0)
    }
    
    for field, default_value in required_fields_with_defaults.items():
        if field not in job_data or job_data[field] is None:
            job_data[field] = default_value
            
    # Validate field data types
    type_validations = {
        'n_code': (lambda x: int(x) if isinstance(x, (int, str)) and str(x).isdigit() else 0),
        'svp': (lambda x: int(x) if isinstance(x, (int, str)) and str(x).isdigit() else 0),
        'strengthNum': (lambda x: int(x) if isinstance(x, (int, str)) and str(x).isdigit() else 0)
    }
    
    # Apply type validations
    for field, validator in type_validations.items():
        if field in job_data:
            try:
                job_data[field] = validator(job_data[field])
            except (ValueError, TypeError):
                # If validation fails, use default
                job_data[field] = required_fields_with_defaults.get(field, 0)
            
    return job_data

# LRU cache decorator for job data lookups
# This improves performance significantly for repeated queries
@lru_cache(maxsize=100)
def cached_get_job_by_code(ncode: int, code_text: str, db_path: str) -> Optional[Dict[str, Any]]:
    """
    Cached version of job lookup by DOT code.
    Uses an LRU cache to avoid repeated database queries for the same codes.
    
    Args:
        ncode: Numeric code integer
        code_text: Formatted DOT code text
        db_path: String representation of database path for cache key
        
    Returns:
        Job data dictionary if found, None otherwise
    """
    # Create a database handler with the path
    # This is inefficient but necessary since we can't pickle the DB handler for cache
    db = DatabaseHandler(Path(db_path))
    
    # Execute the query
    results = db._execute_query(
        "SELECT * FROM DOT WHERE Ncode = ? OR CAST(Code AS TEXT) = ? LIMIT 1;", 
        [ncode, code_text]
    )
    
    if results:
        return results[0]
    return None

def main():
    """
    Main function that processes command line arguments and generates a job report.
    """
    if len(sys.argv) != 2:
        print("Usage: python -m src.sqlite.src.mcp_server_sqlite.generate_job_report <search_term>")
        print("  search_term can be:")
        print("  - A DOT code (e.g., 001.061-010 or 001061010)")
        print("  - A job title (e.g., 'Architect')")
        sys.exit(1)

    search_term = sys.argv[1]
    
    # Assumes DOT.db is in the same directory as this script
    db_file_path = Path(__file__).parent / "DOT.db"
    
    if not db_file_path.exists():
        print(f"Error: Database file not found at {db_file_path}")
        print("Please ensure the DOT.db file is in the correct location.")
        sys.exit(1)
    
    try:
        db = DatabaseHandler(db_file_path)
        print(f"Connected to database: {db_file_path}")
        
        # Use the local get_job_data function
        job_data = get_job_data(db, search_term)
        
        if job_data:
            # Pass the potentially re-mapped job_data to the formatting function
            try:
                report = generate_formatted_job_report(job_data)
                print(report)
            except Exception as e:
                print(f"Error formatting job report: {e}")
                print("Job data found but could not format the report.")
                sys.exit(1)
        else:
            print(f"No job data found for search term: {search_term}")
            sys.exit(1)
    except FileNotFoundError:
        print(f"Error: Database file not found at {db_file_path}")
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 