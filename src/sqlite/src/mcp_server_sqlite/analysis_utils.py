# analysis_utils.py

"""
Low-level utility functions for processing configuration data and performing
simple transformations related to VE analysis.

These functions typically take specific data points and configuration maps
as input and return derived values or formatted strings/dictionaries.
"""

from datetime import date
import json
import os
import logging  # Added logging
from typing import Dict, Any, Optional, List, Tuple, Union, TypedDict
import re

# Import necessary data structures from config.py
# Assuming config.py is in the same directory (adjust path if needed)
from . import config
from .models.dot_code import DotCode  # Import the new DotCode class

logger = logging.getLogger(__name__)  # Added logger

# --- TypedDict Definitions --- #


class ValidationResultDict(TypedDict):
    valid: bool
    original: str
    formatted: Optional[str]
    ncode: Optional[int]
    errors: List[str]


class TSAFindingsDict(TypedDict):
    identified_skills: List[str]  # Assuming simple list for now
    tools_and_equipment: List[str]
    work_processes: List[str]
    analysis_complete: bool
    error: Optional[str]


class TSACompletedStepDict(TypedDict):
    step: int
    title: str
    findings: Union[TSAFindingsDict, ValidationResultDict]  # Depending on the step


class TSARequirementsResultDict(TypedDict):
    completed_steps: List[TSACompletedStepDict]
    findings: Dict[str, Any]  # Keep findings generic for now
    potential_skills: List[str]
    transferable_occupations: List[Dict[str, Any]]  # Keep generic for now


class PhysicalDemandDetailDict(TypedDict):
    name: str
    frequency: Dict[str, Any]  # Freq details from get_frequency_details
    description: str


class EvaluateTransferabilityResultDict(TypedDict):
    is_transferable: bool
    matching_skills: List[str]
    skill_gaps: List[str]
    physical_demands_compatible: bool
    environmental_conditions_compatible: bool
    analysis_details: Dict[str, Any]
    svp_analysis: Dict[str, Any]


class DocumentedOccupationDict(TypedDict):
    dot_code: Optional[str]
    title: Optional[str]
    skill_match: List[str]
    justification: str


class TSADocumentationDict(TypedDict):
    summary: str
    steps_completed: List[TSACompletedStepDict]  # Reuse
    occupations_cited: List[DocumentedOccupationDict]
    skill_transfer_analysis: str
    conclusion: str


# --- Data Loading ---

# NOTE: Obsolescence data loading and checking is now handled by the dedicated
# job_obsolescence.py module and is removed from here to avoid redundancy.


# Load TSA analysis data
def load_tsa_analysis() -> Dict[str, Any]:
    """
    Load TSA analysis data from JSON file.

    Returns:
        Dictionary containing TSA analysis steps and requirements.
    """
    try:
        tsa_file_path = os.path.join(
            os.path.dirname(__file__), "reference_json", "tsa_analysis.json"
        )
        with open(tsa_file_path, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(
            f"Error loading TSA analysis data: {e}", exc_info=True
        )  # Use logger
        return {"steps": []}  # Return empty steps if file not found or invalid


# Load TSA data at module level
TSA_DATA = load_tsa_analysis()


# --- DOT Code/Ncode Conversion Utilities ---
# DEPRECATED: Use DotCode class methods instead
def dot_to_ncode(dot_code: str) -> str:
    """
    DEPRECATED: Use DotCode.clean() instead.
    Convert a human-readable DOT code (e.g., '211.462-010') to a 9-digit Ncode (e.g., '211462010').
    """
    logger.warning(
        "Using deprecated dot_to_ncode function. Use DotCode.clean() instead."
    )
    if not dot_code:
        return ""
    return re.sub(r"[^0-9]", "", dot_code)


# DEPRECATED: Use DotCode class methods instead
def ncode_to_dot(ncode: str) -> str:
    """
    DEPRECATED: Use DotCode.format() instead.
    Convert a 9-digit Ncode (e.g., '211462010') to a human-readable DOT code (e.g., '211.462-010').
    """
    logger.warning(
        "Using deprecated ncode_to_dot function. Use DotCode.format() instead."
    )
    if not ncode or len(ncode) != 9 or not ncode.isdigit():
        return ncode or ""
    return f"{ncode[:3]}.{ncode[3:6]}-{ncode[6:]}"


# --- Functions ---


def determine_applicable_ssr(hearing_date_str: str) -> Optional[str]:
    """
    Determine which SSR applies based on hearing date string.

    Args:
        hearing_date_str: Date of hearing in 'YYYY-MM-DD' format.

    Returns:
        String '00-4p' or '24-3p', or None if date format is invalid.
    """
    try:
        # Parse input string to date object
        hearing_date = date.fromisoformat(hearing_date_str)

        # Get end date from config and ensure it's a date object
        end_date_value = config.ssr_application_date.get("ssr_00_4p_end_date")
        if isinstance(end_date_value, str):
            end_date = date.fromisoformat(end_date_value)
        elif isinstance(end_date_value, date):
            end_date = end_date_value
        else:
            logger.error(f"Invalid date format in config: {end_date_value}")
            return None

        # Compare with properly typed date object
        if hearing_date <= end_date:
            return "00-4p"
        else:
            # Check if it's before the start date if necessary, though <= end date covers it
            return "24-3p"
    except (ValueError, TypeError):
        # Handle invalid date format or None input
        logger.warning(
            f"Invalid hearing date format '{hearing_date_str}' received.",
            exc_info=False,
        )  # Log warning
        return None


# If using Enums in config.py, the return type hint would change, e.g. -> Optional[SkillLevel]
def get_svp_category(svp_num: Optional[int]) -> str:
    """
    Get SVP category (Unskilled, Semi-skilled, Skilled) from SVP number.

    Args:
        svp_num: SVP value (1-9) or None.

    Returns:
        String with skill category ("Unskilled", "Semi-skilled", "Skilled", or "Unknown").
    """
    if svp_num is None or not (1 <= svp_num <= 9):
        return "Unknown"
    # Use .get for safety, though keys should exist if validation passes
    # Adjust return type if using SkillLevel Enum, e.g., return svp_to_skill_level.get(svp_num, SkillLevel.UNKNOWN)
    return config.svp_to_skill_level.get(svp_num, "Unknown")


# The return type hint Dict[str, Any] assumes the structure in freq_map_detailed
def get_frequency_details(freq_num: Optional[int]) -> Optional[Dict[str, Any]]:
    """
    Get detailed frequency information (code, short/full description, percentages)
    from frequency number (1-4).

    Args:
        freq_num: Frequency value (1-4) or None.

    Returns:
        Dictionary with detailed frequency information, or None for invalid input.
    """
    # Adjusted validation: Check if freq_num is within the valid keys of the map
    # Assuming keys are 1, 2, 3, 4 in freq_map_detailed
    if freq_num is None or freq_num not in config.freq_map_detailed:
        # Return None for invalid input instead of defaulting to level 1
        return None
    # Use .get for safety, though keys should exist if validation passes
    return config.freq_map_detailed.get(freq_num)


def get_dot_to_soc_mapping(dot_code: Optional[str]) -> Optional[Dict[str, Any]]:
    """
    Get SOC mapping information for a DOT code from the crosswalk.

    Args:
        dot_code: DOT code string to map, or None.

    Returns:
        Dictionary with SOC mapping information, or None if not found or input is None.
    """
    if not dot_code:
        return None

    # Fix attribute error: config may not have dot_to_soc_crosswalk
    crosswalk_map = getattr(config, "dot_to_soc_crosswalk", {})
    if not crosswalk_map:
        logger.warning("dot_to_soc_crosswalk not found in config")
        return None

    return crosswalk_map.get(dot_code)  # .get handles missing keys


def format_physical_demand(
    demand_name: str, value: Optional[int]
) -> Optional[PhysicalDemandDetailDict]:
    """
    Formats a physical demand with its frequency and description.

    Args:
        demand_name: Name of the physical demand (e.g., 'Climbing', 'Reaching').
        value: Frequency value (1-4) or None.

    Returns:
        Dictionary conforming to PhysicalDemandDetailDict, or None if frequency value is invalid.
    """
    freq_details = get_frequency_details(value)
    if freq_details is None:
        return None  # Return None if frequency value is invalid

    description = config.physical_demands_descriptions.get(
        demand_name, f"No description found for '{demand_name}'"
    )

    # Return the TypedDict explicitly
    return PhysicalDemandDetailDict(
        name=demand_name,
        frequency=freq_details,  # Use the detailed frequency dict
        description=description,
    )


def analyze_tsa_requirements(
    prw_description: str, dot_code: str, rfc: Dict[str, Any]
) -> TSARequirementsResultDict:
    """
    Analyze TSA requirements based on PRW description and DOT code.

    Args:
        prw_description: Description of past relevant work
        dot_code: DOT code for the occupation
        rfc: Dictionary containing RFC limitations

    Returns:
        Dictionary conforming to TSARequirementsResultDict.
    """
    results: TSARequirementsResultDict = {
        "completed_steps": [],
        "findings": {},
        "potential_skills": [],
        "transferable_occupations": [],
    }

    # Step 1: Review Job Description
    job_review = analyze_job_description(prw_description)
    # Explicitly create a TSACompletedStepDict
    step1: TSACompletedStepDict = {
        "step": 1,
        "title": "Job Description Review",
        "findings": job_review,
    }
    results["completed_steps"].append(step1)

    # Step 2: DOT Code Validation
    dot_validation = validate_dot_code(dot_code)
    # Explicitly create a TSACompletedStepDict
    step2: TSACompletedStepDict = {
        "step": 2,
        "title": "DOT Code Validation",
        "findings": dot_validation,
    }
    results["completed_steps"].append(step2)

    # Add potential skills from job description analysis
    potential_skills = job_review.get("identified_skills")
    if isinstance(potential_skills, list):
        results["potential_skills"] = potential_skills
    else:
        results["potential_skills"] = []

    return results


def analyze_job_description(description: str) -> TSAFindingsDict:
    """
    Analyze job description for potential skills and work activities.

    Args:
        description: Detailed job description from claimant

    Returns:
        Dictionary conforming to TSAFindingsDict.
    """
    results: TSAFindingsDict = {
        "identified_skills": [],
        "tools_and_equipment": [],
        "work_processes": [],
        "analysis_complete": True,
        "error": None,
    }

    if not description or len(description.strip()) < 10:
        results["analysis_complete"] = False
        results["error"] = "Job description too brief for meaningful analysis"
        return results

    # TODO: Implement more sophisticated skill extraction logic
    return results


def validate_dot_code(dot_code: str) -> ValidationResultDict:
    """
    Validate DOT code format (XXX.XXX-XXX).
    Note: This only checks format, not existence in the database.

    Args:
        dot_code: DOT code string to validate.

    Returns:
        Dictionary conforming to ValidationResultDict.
    """
    validation_data = DotCode.validate(dot_code)
    return ValidationResultDict(
        valid=validation_data.get("valid", False),
        original=validation_data.get("original", dot_code),
        formatted=validation_data.get("formatted"),
        ncode=validation_data.get("ncode"),
        errors=validation_data.get("errors", []),
    )


def get_tsa_step_requirements(step_number: int) -> Dict[str, Any]:
    """
    Get requirements and guidance for a specific TSA step.

    Args:
        step_number: The TSA step number (1-8)

    Returns:
        Dictionary containing step requirements and guidance
    """
    if not TSA_DATA or "steps" not in TSA_DATA:
        return {"error": "TSA data not available"}

    step = next((s for s in TSA_DATA["steps"] if s["step"] == step_number), None)
    if not step:
        return {"error": f"Step {step_number} not found"}

    return step


def evaluate_skill_transferability(
    source_occupation: Dict[str, Any],
    target_occupation: Dict[str, Any],
    rfc: Dict[str, Any],
) -> EvaluateTransferabilityResultDict:
    """
    Evaluate skill transferability between source and target occupations.

    Args:
        source_occupation: Dictionary containing source occupation details
        target_occupation: Dictionary containing target occupation details
        rfc: Dictionary containing RFC limitations

    Returns:
        Dictionary conforming to EvaluateTransferabilityResultDict.
    """
    results: EvaluateTransferabilityResultDict = {
        "is_transferable": False,
        "matching_skills": [],
        "skill_gaps": [],
        "physical_demands_compatible": False,
        "environmental_conditions_compatible": False,
        "analysis_details": {},
        "svp_analysis": {},
    }

    source_svp = int(source_occupation.get("svp", 0))
    target_svp = int(target_occupation.get("svp", 0))
    is_svp_compatible = target_svp <= source_svp
    results["svp_analysis"] = {
        "source_svp": source_svp,
        "target_svp": target_svp,
        "is_compatible": is_svp_compatible,
    }

    results["physical_demands_compatible"] = compare_physical_demands(
        source_occupation.get("physical_demands", {}),
        target_occupation.get("physical_demands", {}),
        rfc,
    )

    results["is_transferable"] = (
        results["svp_analysis"].get("is_compatible", False)
        and results["physical_demands_compatible"]
        and len(results.get("matching_skills", [])) > 0
    )

    return results


def compare_physical_demands(
    source_demands: Dict[str, Any], target_demands: Dict[str, Any], rfc: Dict[str, Any]
) -> bool:
    """
    Compare physical demands between occupations considering RFC limitations.

    Args:
        source_demands: Physical demands of source occupation
        target_demands: Physical demands of target occupation
        rfc: RFC limitations

    Returns:
        Boolean indicating if physical demands are compatible
    """
    for demand, level in target_demands.items():
        if demand in rfc:
            rfc_limit = rfc[demand]
            if not is_demand_within_limits(level, rfc_limit):
                return False

    return True


def is_demand_within_limits(demand_level: str, rfc_limit: str) -> bool:
    """
    Check if a physical demand level is within RFC limits.

    Args:
        demand_level: Physical demand level from occupation
        rfc_limit: RFC limitation level

    Returns:
        Boolean indicating if demand is within limits
    """
    demand_hierarchy = {
        "sedentary": 1,
        "light": 2,
        "medium": 3,
        "heavy": 4,
        "very heavy": 5,
    }

    try:
        demand_value = demand_hierarchy[demand_level.lower()]
        limit_value = demand_hierarchy[rfc_limit.lower()]
        return demand_value <= limit_value
    except KeyError:
        return False


def find_related_occupations(
    dot_code: str, skills: List[str], rfc: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Find occupations related to the given DOT code and compatible with skills/RFC.

    Args:
        dot_code: DOT code of the source occupation
        skills: List of identified skills
        rfc: Dictionary containing RFC limitations

    Returns:
        List of dictionaries containing related occupation details
    """
    results: List[Dict[str, Any]] = []

    # TODO: Implement occupation search logic
    # This would typically involve:
    # 1. Finding occupations with similar first 3 DOT digits
    # 2. Checking occupations with similar worker functions
    # 3. Filtering based on RFC compatibility
    # 4. Ranking by skill match

    return results


def document_tsa_decision(analysis_results: Dict[str, Any]) -> TSADocumentationDict:
    """
    Generate documentation for TSA decision.

    Args:
        analysis_results: Dictionary containing all TSA analysis results

    Returns:
        Dictionary conforming to TSADocumentationDict.
    """
    documentation: TSADocumentationDict = {
        "summary": "",
        "steps_completed": [],
        "occupations_cited": [],
        "skill_transfer_analysis": "",
        "conclusion": "",
    }

    # Ensure steps_completed is a list before appending
    raw_steps = analysis_results.get("completed_steps", [])
    if isinstance(raw_steps, list):
        step_list: List[TSACompletedStepDict] = []
        for item in raw_steps:
            if isinstance(item, dict):
                step_list.append(item)
        documentation["steps_completed"] = step_list
    else:
        documentation["steps_completed"] = []

    # Process transferable occupations
    raw_transferable = analysis_results.get("transferable_occupations", [])
    occupations_cited_list: List[DocumentedOccupationDict] = []
    if isinstance(raw_transferable, list):
        for occ in raw_transferable:
            if isinstance(occ, dict):
                # Safely extract skill_match ensuring it's a list
                skill_match = occ.get("matching_skills", [])
                # Ensure skill_match is a list
                if not isinstance(skill_match, list):
                    skill_match = []

                cited_occ = DocumentedOccupationDict(
                    dot_code=occ.get("dot_code"),
                    title=occ.get("title"),
                    skill_match=skill_match,
                    justification=occ.get("transfer_justification", ""),
                )
                occupations_cited_list.append(cited_occ)
    documentation["occupations_cited"] = occupations_cited_list

    documentation["summary"] = analysis_results.get("summary", "Summary not available.")
    documentation["skill_transfer_analysis"] = analysis_results.get(
        "skill_transfer_analysis", "Analysis not available."
    )
    documentation["conclusion"] = analysis_results.get(
        "conclusion", "Conclusion not available."
    )

    return documentation


# --- DOT Code Cleaning Utility (Forwarding to DotCode class) ---


def clean_dot_code(dot_code: str) -> Tuple[Optional[int], Optional[str]]:
    """
    DEPRECATED: Use DotCode.clean() directly instead.
    Forwards to DotCode.clean() for backward compatibility.

    Cleans and converts a DOT code into both Ncode (INTEGER) and Code (TEXT) formats.

    Args:
        dot_code: A DOT code in various possible formats

    Returns:
        A tuple of (Ncode, Code) where:
        - Ncode is an INTEGER (e.g., 1061010 for 001.061-010)
        - Code is TEXT (e.g., "001.061-010")
        Returns (None, None) if the format is unrecognized or invalid.
    """
    logger.debug(f"Using clean_dot_code compatibility function for: {dot_code}")
    return DotCode.clean(dot_code)


# Remember to add 'Tuple' to the imports at the top of analysis_utils.py if not already present:
# from typing import ..., Tuple, ...
