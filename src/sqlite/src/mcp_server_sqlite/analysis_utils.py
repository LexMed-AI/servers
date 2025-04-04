# analysis_utils.py

"""
Low-level utility functions for processing configuration data and performing
simple transformations related to VE analysis.

These functions typically take specific data points and configuration maps
as input and return derived values or formatted strings/dictionaries.
"""

from datetime import date, datetime
from typing import Dict, Any, Optional, Union, List # Added Optional, Union, List, Dict

# Import necessary data structures from config.py
# Assuming config.py is in the same directory (adjust path if needed)
from . import config

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
        # Compare with date objects from config
        # Ensure dates in config.ssr_application_date are also date objects
        if hearing_date <= config.ssr_application_date['ssr_00_4p_end_date']:
            return '00-4p'
        else:
            # Check if it's before the start date if necessary, though <= end date covers it
            return '24-3p'
    except (ValueError, TypeError):
        # Handle invalid date format or None input
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

def check_job_obsolescence(dot_code: Optional[str]) -> Dict[str, Any]:
    """
    Check if a job is potentially obsolete based on pre-defined indicators.

    Args:
        dot_code: DOT code string to analyze, or None.

    Returns:
        Dictionary with obsolescence analysis results.
    """
    if not dot_code:
        return {
            'is_potentially_obsolete': False,
            'message': 'No DOT code provided for analysis'
        }

    # Use .get() for safer lookup in the indicators dictionary
    obsolescence_info = config.job_obsolescence_indicators.get(dot_code)

    if obsolescence_info:
        risk_level = obsolescence_info.get('risk_level', 'Unknown')
        return {
            'dot_code': dot_code, # Include dot_code in result for clarity
            'is_potentially_obsolete': risk_level in ['High', 'Medium'],
            'risk_level': risk_level,
            'factors': obsolescence_info.get('factors', []),
            'em_references': obsolescence_info.get('em_references', []),
            'modern_equivalents': obsolescence_info.get('modern_equivalents', [])
        }
    else:
        # Basic obsolescence check for DOT codes not specifically listed
        return {
            'dot_code': dot_code,
            'is_potentially_obsolete': False, # Default assumption if not listed
            'message': 'DOT code not in known obsolescence risk list. Consider potential obsolescence as DOT was last fully updated in 1991.',
            'risk_level': 'Undetermined',
            'factors': ['Not specifically listed in obsolescence indicators'],
        }

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
    return config.dot_to_soc_crosswalk.get(dot_code) # .get handles missing keys

def format_physical_demand(demand_name: str, value: Optional[int]) -> Optional[Dict[str, Any]]:
    """
    Formats a physical demand with its frequency and description.

    Args:
        demand_name: Name of the physical demand (e.g., 'Climbing', 'Reaching').
        value: Frequency value (1-4) or None.

    Returns:
        Dictionary with formatted physical demand information, or None if frequency value is invalid.
    """
    freq_details = get_frequency_details(value)
    if freq_details is None:
        return None # Return None if frequency value is invalid

    # Use .get() for safer lookup of description
    description = config.physical_demands_descriptions.get(demand_name, f"No description found for '{demand_name}'")

    return {
        'name': demand_name,
        'frequency': freq_details, # Use the detailed frequency dict
        'description': description
    }

# --- Functions below this line were incorrectly placed here and should be in ve_logic.py ---
# def analyze_transferable_skills_compatibility(...)
# def format_ve_testimony_report(...)
# def get_job_analysis(...)
# def analyze_ve_testimony(...)
# --- Remove them from this file ---