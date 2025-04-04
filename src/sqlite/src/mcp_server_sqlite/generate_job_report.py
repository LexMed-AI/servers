import sys
from typing import Dict, Any, Optional, Tuple
from pathlib import Path
from ve_logic import generate_formatted_job_report
from db_handler import DatabaseHandler

def convert_dot_code(code: str) -> str:
    """
    Converts between DOT code formats.
    If given ###.###-### format, converts to ######### format.
    If given ######### format, converts to ###.###-### format.
    
    Args:
        code: The DOT code to convert
        
    Returns:
        The converted DOT code, or the original if not a valid format
    """
    # Remove any non-numeric characters
    numeric_only = ''.join(c for c in code if c.isdigit())
    
    if len(numeric_only) == 9:
        # Convert ######### to ###.###-###
        if '.' not in code and '-' not in code:
            return f"{numeric_only[:3]}.{numeric_only[3:6]}-{numeric_only[6:]}"
        # Convert ###.###-### to #########
        else:
            return numeric_only
    return code

def clean_dot_code(dot_code: str) -> Tuple[Optional[int], Optional[str]]:
    """
    Cleans and converts a DOT code into both Ncode (INTEGER) and Code (TEXT) formats.
    
    Args:
        dot_code: A DOT code in either ######### or ###.###-### format
        
    Returns:
        A tuple of (Ncode, Code) where:
        - Ncode is an INTEGER (e.g., 1001061010 for 001.061-010)
        - Code is TEXT (e.g., "001.061-010")
    """
    try:
        # Remove any whitespace
        dot_code = dot_code.strip()
        
        if '.' in dot_code and '-' in dot_code:
            # Format is ###.###-###
            parts = dot_code.replace('-', '.').split('.')
            if len(parts) != 3:
                return None, None
                
            group = int(parts[0])
            subgroup = int(parts[1])
            suffix = int(parts[2])
            
            # Convert to Ncode (9-digit integer)
            ncode = int(f"1{group:03d}{subgroup:03d}{suffix:03d}")
            
            # Format Code as TEXT (###.###-###)
            code_text = f"{group:03d}.{subgroup:03d}-{suffix:03d}"
            
            return ncode, code_text
            
        elif dot_code.isdigit() and len(dot_code) == 9:
            # Format is #########
            ncode = int(f"1{dot_code}")  # Add leading 1 for Ncode
            
            # Extract parts
            group = int(dot_code[:3])
            subgroup = int(dot_code[3:6])
            suffix = int(dot_code[6:])
            
            # Format Code as TEXT (###.###-###)
            code_text = f"{group:03d}.{subgroup:03d}-{suffix:03d}"
            
            return ncode, code_text
            
        return None, None
    except (ValueError, IndexError):
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
    try:
        # First try to find by exact code match if it looks like a DOT code
        ncode, code_text = clean_dot_code(search_term)
        if ncode is not None:
            # Try Code match first (since that's what we see in the data)
            results = db._execute_query("SELECT * FROM DOT WHERE Code = ? LIMIT 1;", [code_text])
            if not results:
                # Try Ncode match as fallback
                results = db._execute_query("SELECT * FROM DOT WHERE Ncode = ? LIMIT 1;", [ncode])
            
            if results:
                # Map the database fields to the expected keys
                job_data = results[0]
                job_data['dotCode'] = job_data['Code']  # Already in ###.###-### format
                job_data['jobTitle'] = job_data['Title']
                job_data['definition'] = job_data.get('Definitions', 'N/A')
                return job_data
        
        # If no results or not a DOT code, try finding by job title
        results = db.find_job_data(search_term)
        if results:
            # Map the database fields to the expected keys
            job_data = results[0]
            job_data['dotCode'] = job_data['Code']  # Already in ###.###-### format
            job_data['jobTitle'] = job_data['Title']
            job_data['definition'] = job_data.get('Definitions', 'N/A')
            return job_data
        
        print(f"No job data found for search term: {search_term}")
        return None
    except Exception as e:
        print(f"Error retrieving job data: {e}")
        return None

def main():
    """
    Main function that processes command line arguments and generates a job report.
    """
    if len(sys.argv) != 2:
        print("Usage: python generate_job_report.py <search_term>")
        print("  search_term can be:")
        print("  - A DOT code (e.g., 001.061-010 or 001061010)")
        print("  - A job title (e.g., 'Architect')")
        sys.exit(1)

    search_term = sys.argv[1]
    db = DatabaseHandler("DOT.db")
    
    job_data = get_job_data(db, search_term)
    if job_data:
        report = generate_formatted_job_report(job_data)
        print(report)

if __name__ == "__main__":
    main() 