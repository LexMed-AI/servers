import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

# Setup logger
logger = logging.getLogger(__name__)

# Define the path to the JSON file relative to this script
JSON_FILE_PATH = Path(__file__).parent / "reference_json" / "obsolete_out_dated.json"

# Load the obsolescence data once when the module is imported
OBSOLETE_JOBS_DATA: Optional[List[Dict[str, Any]]] = None
OBSOLETE_JOBS_DICT: Dict[str, Dict[str, Any]] = {}

try:
    with open(JSON_FILE_PATH, "r") as f:
        OBSOLETE_JOBS_DATA = json.load(f)
        # Create a dictionary for faster lookups by DOT code
        if OBSOLETE_JOBS_DATA is not None:  # Check if data was loaded
            for job in OBSOLETE_JOBS_DATA:
                if "DOT Code" in job and isinstance(job, dict):
                    OBSOLETE_JOBS_DICT[job["DOT Code"]] = job
        else:
            logger.warning(
                f"JSON data from {JSON_FILE_PATH} was loaded as None. Obsolescence dictionary will be empty."
            )
    logger.info(f"Successfully loaded obsolescence data from {JSON_FILE_PATH}")
except FileNotFoundError:
    logger.error(
        f"Obsolescence JSON file not found at {JSON_FILE_PATH}. Obsolescence check will not work."
    )
    OBSOLETE_JOBS_DATA = None  # Ensure it's None if loading fails
except json.JSONDecodeError:
    logger.error(
        f"Error decoding JSON from {JSON_FILE_PATH}. Obsolescence check will not work."
    )
    OBSOLETE_JOBS_DATA = None
except Exception as e:
    logger.error(f"An unexpected error occurred loading {JSON_FILE_PATH}: {e}")
    OBSOLETE_JOBS_DATA = None


def check_job_obsolescence(dot_code: str) -> Dict[str, Any]:
    """
    Retrieves obsolescence reference data for a given DOT code if available.

    This function does NOT determine whether a job is actually obsolete - it only
    provides reference information about whether the DOT code appears in SSA
    obsolescence documentation for further analysis.

    Args:
        dot_code: The DOT code (format: XXX.XXX-XXX) to check.

    Returns:
        A dictionary containing reference data if the DOT is in the obsolescence list,
        or a message indicating it wasn't found in reference data.
    """
    logger.debug(f"Checking obsolescence references for DOT code: {dot_code}")

    if OBSOLETE_JOBS_DATA is None:
        return {
            "dot_code": dot_code,
            "reference_status": "Error",
            "message": "Obsolescence reference data failed to load. Check server logs.",
        }

    # Normalize the input dot_code format just in case (e.g., remove whitespace)
    # A more robust function could handle variations if needed.
    normalized_dot_code = dot_code.strip()

    obsolete_info = OBSOLETE_JOBS_DICT.get(normalized_dot_code)

    if obsolete_info:
        logger.info(
            f"DOT code {normalized_dot_code} found in obsolescence reference data ({obsolete_info.get('EM')})."
        )
        return {
            "dot_code": normalized_dot_code,
            "reference_status": "Found in Reference",
            "data_source": obsolete_info.get("EM", "N/A"),
            "reference_comment": obsolete_info.get("Comment", "N/A"),
            "raw_reference_data": obsolete_info,  # Include all details from the JSON
            "note": "This DOT appears in reference data that identifies potentially obsolete/outdated occupations. Further analysis required.",
        }
    else:
        logger.debug(
            f"DOT code {normalized_dot_code} not found in obsolescence reference data."
        )
        return {
            "dot_code": normalized_dot_code,
            "reference_status": "Not Found",
            "message": "This DOT code does not appear in the reference data identifying potentially obsolete/outdated occupations (EM-24026, EM-24027).",
            "note": "Not appearing in reference data does not guarantee the occupation is current. Consider conducting additional research.",
        }
