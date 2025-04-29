# analysis_utils.py

"""
Low-level utility functions for processing configuration data and performing
simple transformations related to VE analysis.

These functions typically take specific data points and configuration maps
as input and return derived values or formatted strings/dictionaries.
"""

from datetime import date, datetime
import json
import os
import logging # Added logging
from pathlib import Path # Added pathlib
from typing import Dict, Any, Optional, Union, List, Tuple
import re

# Import necessary data structures from config.py
# Assuming config.py is in the same directory (adjust path if needed)
from . import config

logger = logging.getLogger(__name__) # Added logger

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
        tsa_file_path = os.path.join(os.path.dirname(__file__), 'reference_json', 'tsa_analysis.json')
        with open(tsa_file_path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Error loading TSA analysis data: {e}", exc_info=True) # Use logger
        return {"steps": []}  # Return empty steps if file not found or invalid

# Load TSA data at module level
TSA_DATA = load_tsa_analysis()

# --- DOT Code/Ncode Conversion Utilities ---
def dot_to_ncode(dot_code: str) -> str:
    """
    Convert a human-readable DOT code (e.g., '211.462-010') to a 9-digit Ncode (e.g., '211462010').
    """
    if not dot_code:
        return ""
    return re.sub(r'[^0-9]', '', dot_code)

def ncode_to_dot(ncode: str) -> str:
    """
    Convert a 9-digit Ncode (e.g., '211462010') to a human-readable DOT code (e.g., '211.462-010').
    """
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
        # Compare with date objects from config
        # Ensure dates in config.ssr_application_date are also date objects
        if hearing_date <= config.ssr_application_date['ssr_00_4p_end_date']:
            return '00-4p'
        else:
            # Check if it's before the start date if necessary, though <= end date covers it
            return '24-3p'
    except (ValueError, TypeError):
        # Handle invalid date format or None input
        logger.warning(f"Invalid hearing date format '{hearing_date_str}' received.", exc_info=False) # Log warning
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

def analyze_tsa_requirements(prw_description: str, dot_code: str, rfc: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze TSA requirements based on PRW description and DOT code.

    Args:
        prw_description: Description of past relevant work
        dot_code: DOT code for the occupation
        rfc: Dictionary containing RFC limitations

    Returns:
        Dictionary with TSA analysis results including completed steps and findings
    """
    results = {
        'completed_steps': [],
        'findings': {},
        'potential_skills': [],
        'transferable_occupations': []
    }
    
    # Step 1: Review Job Description
    job_review = analyze_job_description(prw_description)
    results['completed_steps'].append({
        'step': 1,
        'title': 'Job Description Review',
        'findings': job_review
    })
    
    # Step 2: DOT Code Validation
    dot_validation = validate_dot_code(dot_code)
    results['completed_steps'].append({
        'step': 2,
        'title': 'DOT Code Validation',
        'findings': dot_validation
    })
    
    # Add potential skills from job description analysis
    results['potential_skills'] = job_review.get('identified_skills', [])
    
    return results

def analyze_job_description(description: str) -> Dict[str, Any]:
    """
    Analyze job description for potential skills and work activities.

    Args:
        description: Detailed job description from claimant

    Returns:
        Dictionary containing analysis results including identified skills
    """
    # Initialize results
    results = {
        'identified_skills': [],
        'tools_and_equipment': [],
        'work_processes': [],
        'analysis_complete': True
    }
    
    # Basic validation
    if not description or len(description.strip()) < 10:
        results['analysis_complete'] = False
        results['error'] = 'Job description too brief for meaningful analysis'
        return results
    
    # TODO: Implement more sophisticated skill extraction logic
    # This is a placeholder for more complex analysis
    
    return results

def validate_dot_code(dot_code: str) -> Dict[str, Any]:
    """
    Validate DOT code format (XXX.XXX-XXX).
    Note: This only checks format, not existence in the database.

    Args:
        dot_code: DOT code string to validate.

    Returns:
        Dictionary containing validation results.
    """
    # Placeholder - Basic format check is ok, but needs DB lookup for existence
    logger.warning("validate_dot_code placeholder only checks format, not existence.")
    results = {
        'is_valid_format': False,
        'occupation_details': None, # Keep this key, but it won't be populated here
        'validation_messages': []
    }
    if not dot_code:
        results['validation_messages'].append('No DOT code provided')
        return results
    # Check DOT code format (XXX.XXX-XXX)
    if isinstance(dot_code, str) and len(dot_code) == 11 and dot_code[3] == '.' and dot_code[7] == '-':
        results['is_valid_format'] = True
        # Remove message about existence check, as it's documented in the docstring
        # results['validation_messages'].append('Format valid. Existence not checked.')
    else:
        results['validation_messages'].append('Invalid DOT code format (Expected XXX.XXX-XXX)')
    return results

def get_tsa_step_requirements(step_number: int) -> Dict[str, Any]:
    """
    Get requirements and guidance for a specific TSA step.

    Args:
        step_number: The TSA step number (1-8)

    Returns:
        Dictionary containing step requirements and guidance
    """
    if not TSA_DATA or 'steps' not in TSA_DATA:
        return {'error': 'TSA data not available'}
        
    step = next((s for s in TSA_DATA['steps'] if s['step'] == step_number), None)
    if not step:
        return {'error': f'Step {step_number} not found'}
        
    return step

def evaluate_skill_transferability(source_occupation: Dict[str, Any], 
                                target_occupation: Dict[str, Any],
                                rfc: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluate skill transferability between source and target occupations.

    Args:
        source_occupation: Dictionary containing source occupation details
        target_occupation: Dictionary containing target occupation details
        rfc: Dictionary containing RFC limitations

    Returns:
        Dictionary containing transferability analysis results
    """
    results = {
        'is_transferable': False,
        'matching_skills': [],
        'skill_gaps': [],
        'physical_demands_compatible': False,
        'environmental_conditions_compatible': False,
        'analysis_details': {}
    }
    
    # Compare SVP levels
    source_svp = source_occupation.get('svp', 0)
    target_svp = target_occupation.get('svp', 0)
    results['svp_analysis'] = {
        'source_svp': source_svp,
        'target_svp': target_svp,
        'is_compatible': target_svp <= source_svp
    }
    
    # Compare physical demands
    results['physical_demands_compatible'] = compare_physical_demands(
        source_occupation.get('physical_demands', {}),
        target_occupation.get('physical_demands', {}),
        rfc
    )
    
    # Overall transferability determination
    results['is_transferable'] = (
        results['svp_analysis']['is_compatible'] and
        results['physical_demands_compatible'] and
        len(results['matching_skills']) > 0
    )
    
    return results

def compare_physical_demands(source_demands: Dict[str, Any],
                           target_demands: Dict[str, Any],
                           rfc: Dict[str, Any]) -> bool:
    """
    Compare physical demands between occupations considering RFC limitations.

    Args:
        source_demands: Physical demands of source occupation
        target_demands: Physical demands of target occupation
        rfc: RFC limitations

    Returns:
        Boolean indicating if physical demands are compatible
    """
    # Check if target demands are within RFC limitations
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
    # Define demand level hierarchy (from lowest to highest)
    demand_hierarchy = {
        'sedentary': 1,
        'light': 2,
        'medium': 3,
        'heavy': 4,
        'very heavy': 5
    }
    
    try:
        demand_value = demand_hierarchy[demand_level.lower()]
        limit_value = demand_hierarchy[rfc_limit.lower()]
        return demand_value <= limit_value
    except KeyError:
        # If levels aren't in our hierarchy, return False to be safe
        return False

def find_related_occupations(dot_code: str, 
                           skills: List[str],
                           rfc: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Find occupations related to the given DOT code and compatible with skills/RFC.

    Args:
        dot_code: DOT code of the source occupation
        skills: List of identified skills
        rfc: Dictionary containing RFC limitations

    Returns:
        List of dictionaries containing related occupation details
    """
    results = []
    
    # TODO: Implement occupation search logic
    # This would typically involve:
    # 1. Finding occupations with similar first 3 DOT digits
    # 2. Checking occupations with similar worker functions
    # 3. Filtering based on RFC compatibility
    # 4. Ranking by skill match
    
    return results

def document_tsa_decision(analysis_results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate documentation for TSA decision.

    Args:
        analysis_results: Dictionary containing all TSA analysis results

    Returns:
        Dictionary containing formatted documentation and citations
    """
    documentation = {
        'summary': '',
        'steps_completed': [],
        'occupations_cited': [],
        'skill_transfer_analysis': '',
        'conclusion': ''
    }
    
    # Format step completion information
    for step in analysis_results.get('completed_steps', []):
        documentation['steps_completed'].append({
            'step_number': step['step'],
            'title': step['title'],
            'findings': step['findings']
        })
    
    # Add transferable occupations
    documentation['occupations_cited'] = [
        {
            'dot_code': occ.get('dot_code'),
            'title': occ.get('title'),
            'skill_match': occ.get('matching_skills', []),
            'justification': occ.get('transfer_justification', '')
        }
        for occ in analysis_results.get('transferable_occupations', [])
    ]
    
    return documentation

# --- Functions below this line were incorrectly placed here and should be in ve_logic.py ---
# def analyze_transferable_skills_compatibility(...)
# def format_ve_testimony_report(...)
# def get_job_analysis(...)
# def analyze_ve_testimony(...)
# --- Remove them from this file ---