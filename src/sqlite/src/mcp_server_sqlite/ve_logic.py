# ve_logic.py

"""
Core Vocational Expert (VE) analysis logic, formatting, and orchestration.

This module uses database access functions (via db_handler), low-level
utility functions (from analysis_utils), and configuration data (from config)
to perform VE-specific tasks like TSA, obsolescence assessment, report formatting,
and consistency checks.
"""

import logging
from typing import Dict, Any, Optional, List, Union
from datetime import date, datetime # Import date if used elsewhere

# Import utility functions, configuration data and the DatabaseHandler class definition
from . import analysis_utils
from . import config
from .db_handler import DatabaseHandler

logger = logging.getLogger(__name__)

# --- Constants ---
UNKNOWN_STRING = "Unknown"
DEFAULT_RFC_LEVEL = "SEDENTARY" # Default RFC if not provided to TSA
DEFAULT_AGE_CATEGORY = "ADVANCED AGE" # Default Age if not provided to TSA
DEFAULT_EDUCATION = "UNKNOWN" # Default Education if not provided to TSA

# --- Core Analysis Functions ---

def get_job_analysis(job_data: Dict[str, Any], hearing_date_str: Optional[str] = None) -> Dict[str, Any]:
    """
    Orchestrates the generation of a comprehensive analysis dictionary for a job,
    drawing data from the raw DB dictionary and interpreting it using config/utils.

    Args:
        job_data: Raw job data dictionary (presumably from db_handler.find_job_data).
        hearing_date_str: Optional hearing date string ('YYYY-MM-DD') to determine applicable SSR.

    Returns:
        A dictionary containing structured analysis of the job's characteristics.
        Returns {'error': '...'} if input job_data is invalid.
    """
    if not job_data:
        logger.warning("get_job_analysis called with invalid job_data.")
        return {"error": "No job data provided to analyze"}

    # Determine applicable SSR using the utility function
    # Handle potential None return from determine_applicable_ssr if date format invalid
    applicable_ssr = UNKNOWN_STRING
    if hearing_date_str:
        applicable_ssr_result = analysis_utils.determine_applicable_ssr(hearing_date_str)
        if applicable_ssr_result:
            applicable_ssr = applicable_ssr_result
        else:
            logger.warning(f"Invalid hearing_date format '{hearing_date_str}', cannot determine SSR.")
            applicable_ssr = "Error: Invalid Date Format"
    else:
        # Default based on current date (requires current time context)
        # Or simply default to the latest known SSR if no date provided
        # For simplicity, let's assume default is latest if no date given
        # This might need refinement based on desired behavior for missing dates
        applicable_ssr = '24-3p' # Adjust this default as needed
        logger.debug("No hearing date provided, defaulting applicable SSR.")


    # Extract basic info using .get() for safety
    dot_code = job_data.get('dotCodeReal', UNKNOWN_STRING) # From report_query alias
    n_code = job_data.get('NCode', UNKNOWN_STRING)
    strength_num = job_data.get('StrengthNum', None) # Get the number from DB data
    svp_num = job_data.get('SVPNum', None)
    gedr_num = job_data.get('GEDR', None)
    gedm_num = job_data.get('GEDM', None)
    gedl_num = job_data.get('GEDL', None)
    wf_data = job_data.get('WFData', None)
    wf_people = job_data.get('WFPeople', None)
    wf_things = job_data.get('WFThings', None)

    # Derive strength code ('S','L',..) using the map from config and StrengthNum
    strength_code_derived = config.strength_num_to_code.get(strength_num) # Returns None if num invalid/missing

    analysis = {
        'job_title': job_data.get('jobTitle', UNKNOWN_STRING), # From report_query alias
        'dot_code_real': dot_code, # Store the original REAL value if needed
        'n_code': n_code,
        'formatted_dot_code': job_data.get('dotCode', UNKNOWN_STRING), # Store original formatted code if available
        'applicable_ssr': applicable_ssr,
        'definition': job_data.get('definition', 'N/A'),

        'exertional_level': {
            'num': strength_num, # Keep the original number
            'code': strength_code_derived, # Use the derived code ('S','L', None)
            'name': config.strength_code_to_name.get(strength_code_derived) if strength_code_derived else UNKNOWN_STRING,
            'description': config.strength_description_map.get(strength_code_derived) if strength_code_derived else UNKNOWN_STRING
        },

        'skill_level': {
            'svp': svp_num,
            'svp_description': config.svp_map.get(svp_num, UNKNOWN_STRING),
            'category': analysis_utils.get_svp_category(svp_num) # Util handles None/invalid SVP
        },

        'ged_levels': {
            'reasoning': {
                'level': gedr_num,
                'description': config.ged_map.get(gedr_num, {}).get('reasoning', UNKNOWN_STRING)
            },
            'math': {
                'level': gedm_num,
                'description': config.ged_map.get(gedm_num, {}).get('math', UNKNOWN_STRING)
            },
            'language': {
                'level': gedl_num,
                'description': config.ged_map.get(gedl_num, {}).get('language', UNKNOWN_STRING)
            }
        },

        'worker_functions': {
            'data': { 'level': wf_data, 'description': config.worker_functions_map.get('data', {}).get(wf_data, UNKNOWN_STRING) },
            'people': { 'level': wf_people, 'description': config.worker_functions_map.get('people', {}).get(wf_people, UNKNOWN_STRING) },
            'things': { 'level': wf_things, 'description': config.worker_functions_map.get('things', {}).get(wf_things, UNKNOWN_STRING) }
        },

        'physical_demands': {}, # Populated below
        'environmental_conditions': {}, # Populated below
        'aptitudes': {}, # Populated below
        'temperaments': [], # Populated below

        # Extended analysis using utility functions
        'soc_crosswalk': analysis_utils.get_dot_to_soc_mapping(job_data.get('dotCode')), # Pass formatted code if available and expected by util
        'obsolescence_analysis': analysis_utils.check_job_obsolescence(job_data.get('dotCode'))
    }

    # Process physical demands using utils
    for api_key, label in config.physical_demand_api_keys_to_labels.items():
        if api_key in job_data:
            demand_value = job_data.get(api_key) # Get numeric value from DB data
            formatted_demand = analysis_utils.format_physical_demand(label, demand_value)
            if formatted_demand: # Only add if valid frequency value was processed
                 analysis['physical_demands'][label] = formatted_demand

    # Process environmental conditions using utils & config
    for api_key, label in config.environmental_condition_api_keys_to_labels.items():
        if api_key in job_data and api_key != 'NoiseNum': # Handle noise separately
            env_value = job_data.get(api_key) # Get numeric value
            freq_details = analysis_utils.get_frequency_details(env_value)
            if freq_details: # Only add if valid frequency value processed
                description = config.environmental_conditions_descriptions.get(label, f"No description found for '{label}'")
                analysis['environmental_conditions'][label] = {
                    'name': label,
                    'frequency': freq_details, # Store the detailed dict from util
                    'description': description
                }

    # Handle noise specially using config map
    noise_value = job_data.get('NoiseNum')
    noise_details = config.noise_level_descriptions.get(noise_value)
    if noise_details:
        analysis['environmental_conditions']['Noise'] = {
            'name': 'Noise',
            'level': noise_value,
            'description': f"{noise_details.get('name', '')} - {noise_details.get('description', '')}",
            'examples': noise_details.get('examples', [])
        }

    # Add temperaments using config map
    for i in range(1, 6): # Assuming Temp1 to Temp5 keys exist in job_data
        temp_code = job_data.get(f'Temp{i}')
        if temp_code and temp_code in config.temperament_rfc_considerations:
            analysis['temperaments'].append(config.temperament_rfc_considerations[temp_code])

    # Add aptitudes using config maps
    for code, details in config.aptitude_code_to_details_map.items():
        api_key = f'Apt{details["api_suffix"]}' # Construct DB column name
        if api_key in job_data:
            level = job_data.get(api_key) # Get numeric level (1-5)
            level_details = config.aptitude_level_percentiles.get(level)
            apt_name = details.get("name", UNKNOWN_STRING) # Get readable name
            if level_details:
                analysis['aptitudes'][apt_name] = {
                    'level': level,
                    'description': level_details.get('description', UNKNOWN_STRING),
                    'percentile': level_details.get('percentile_range', UNKNOWN_STRING),
                    'rfc_compatibility': level_details.get('rfc_compatibility', UNKNOWN_STRING)
                }

    return analysis


def perform_consistency_check(hypothetical_limits: Dict[str, Any], job_analysis: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    Compares ALJ hypothetical limitations against the actual job requirements analysis.
    **Note:** The structure of `hypothetical_limits` needs to be standardized based
    on the output expected from the Megaprompt's Hypothetical parsing phase (Phase 4).

    Args:
        hypothetical_limits: A structured dictionary representing the limitations.
                             Example Structure (needs confirmation):
                             {
                                 'exertional': {'lift_carry': 10, 'stand_walk': 2, 'sit': 6, 'level': 'Sedentary'},
                                 'postural': {'Climbing': 'N', 'Balancing': 'O', 'Stooping': 'F', ...},
                                 'manipulative': {'Reaching': 'O', 'Handling': 'F', ...},
                                 'visual': {'Near Acuity': 'C', ...},
                                 'environmental': {'Fumes': 'N', 'Heights': 'N', ...},
                                 'mental': {'svp': 2, 'reasoning': 1, 'instructions': 'Simple', 'contact_public': 'N', ...}
                             }
                             Frequency codes assumed: N=Not Present, O=Occasionally, F=Frequently, C=Constantly
        job_analysis: The structured job analysis dictionary from get_job_analysis().

    Returns:
        A list of dictionaries, where each dictionary represents an identified conflict.
    """
    conflicts = []
    if not hypothetical_limits or not job_analysis or 'error' in job_analysis:
        logger.warning("perform_consistency_check received invalid input.")
        return [{'error': 'Invalid input for consistency check'}]

    logger.debug(f"Performing consistency check for DOT {job_analysis.get('formatted_dot_code')}")

    # Define frequency order for comparison N < O < F < C
    freq_order = {'N': 1, 'O': 2, 'F': 3, 'C': 4, None: 0} # Treat None as less than N

    # --- Exertional Check ---
    # TODO: Implement more detailed check comparing lift/carry/stand/walk/sit limits
    # against the definitions associated with the actual job's exertional level ('S', 'L', 'M'...).
    # This requires mapping the definitions from config.strength_description_map.
    hypo_exert_level = hypothetical_limits.get('exertional', {}).get('level') # e.g., 'Sedentary'
    actual_exert_name = job_analysis.get('exertional_level', {}).get('name') # e.g., 'Light'
    # Basic level name comparison (needs refinement based on actual limits)
    # if hypo_exert_level and actual_exert_name and hypo_exert_level != actual_exert_name:
    #     conflicts.append({...})


    # --- Skill Level (SVP) Check ---
    hypo_svp_limit = hypothetical_limits.get('mental', {}).get('svp') # Max SVP allowed by hypo
    actual_svp = job_analysis.get('skill_level', {}).get('svp')
    if hypo_svp_limit is not None and actual_svp is not None and actual_svp > hypo_svp_limit:
        conflicts.append({
            'area': 'Skill (SVP)',
            'hypothetical_limit': f'<= SVP {hypo_svp_limit}',
            'job_requirement': f'SVP {actual_svp}',
            'conflict_description': f'Job requires SVP {actual_svp}, but hypothetical limits to SVP {hypo_svp_limit} or less.'
        })

    # --- Mental (GED Reasoning) Check ---
    hypo_reasoning_limit = hypothetical_limits.get('mental', {}).get('reasoning') # Max GED-R level allowed
    actual_reasoning_level = job_analysis.get('ged_levels', {}).get('reasoning', {}).get('level')
    if hypo_reasoning_limit is not None and actual_reasoning_level is not None and actual_reasoning_level > hypo_reasoning_limit:
         conflicts.append({
            'area': 'Reasoning (GED-R)',
            'hypothetical_limit': f'Level <= {hypo_reasoning_limit}',
            'job_requirement': f'Level {actual_reasoning_level}',
            'conflict_description': f'Job requires GED Reasoning Level {actual_reasoning_level}, but hypothetical limits to Level {hypo_reasoning_limit} or less.'
        })
    # TODO: Add checks for other mental aspects vs Temperaments, Worker Functions etc.

    # --- Physical Demands Check (Postural, Manipulative, Visual, Sensory) ---
    # Combine relevant hypothetical sections
    hypo_physical_limits = {
        **hypothetical_limits.get('postural', {}),
        **hypothetical_limits.get('manipulative', {}),
        **hypothetical_limits.get('visual', {}),
        **hypothetical_limits.get('sensory', {}),
    }
    actual_physical_demands = job_analysis.get('physical_demands', {})

    for demand_label, hypo_freq_code in hypo_physical_limits.items(): # Assumes hypo_freq_code is 'N', 'O', 'F', 'C'
        actual_demand_info = actual_physical_demands.get(demand_label)
        if actual_demand_info:
            actual_freq_code = actual_demand_info.get('frequency', {}).get('code')
            hypo_order = freq_order.get(hypo_freq_code, 0) # Default to 0 if code invalid
            actual_order = freq_order.get(actual_freq_code, 0) # Default to 0 if code invalid

            if actual_order > hypo_order: # Job requires more frequency than hypo allows
                 conflicts.append({
                    'area': f'Physical ({demand_label})',
                    'hypothetical_limit': f'{hypo_freq_code}',
                    'job_requirement': f'{actual_freq_code}',
                    'conflict_description': f'Job requires {demand_label} {actual_freq_code} ({actual_demand_info.get("frequency",{}).get("short")}), but hypothetical limits to {hypo_freq_code} ({config.freq_map_detailed.get(freq_order.get(hypo_freq_code, 1), {}).get("short", "?")}).'
                })
        else:
            # Optional: Log if a limitation is specified for a demand not listed in the job analysis
            logger.debug(f"Hypothetical limit specified for '{demand_label}', but this demand not found in job analysis data.")


    # --- Environmental Check ---
    hypo_env_limits = hypothetical_limits.get('environmental', {}) # Assumes {'Fumes': 'N', 'Heights': 'O', ...}
    actual_env_conditions = job_analysis.get('environmental_conditions', {})

    for condition_label, hypo_freq_code in hypo_env_limits.items():
        actual_condition_info = actual_env_conditions.get(condition_label)
        if actual_condition_info:
            if condition_label == "Noise": # Special handling for Noise level
                hypo_noise_level = hypo_freq_code # Assuming hypo might specify max level e.g., 3 (Moderate)
                actual_noise_level = actual_condition_info.get('level')
                # Check if actual level exceeds hypothetical limit (needs defined noise level order)
                # if actual_noise_level is not None and hypo_noise_level is not None and actual_noise_level > hypo_noise_level:
                #    conflicts.append({...}) # Add noise level conflict
            else: # Handle frequency-based environmental factors
                actual_freq_code = actual_condition_info.get('frequency', {}).get('code')
                hypo_order = freq_order.get(hypo_freq_code, 0)
                actual_order = freq_order.get(actual_freq_code, 0)

                if actual_order > hypo_order: # Job requires more exposure than hypo allows
                    conflicts.append({
                        'area': f'Environmental ({condition_label})',
                        'hypothetical_limit': f'{hypo_freq_code}',
                        'job_requirement': f'{actual_freq_code}',
                        'conflict_description': f'Job requires exposure to {condition_label} {actual_freq_code} ({actual_condition_info.get("frequency",{}).get("short")}), but hypothetical limits to {hypo_freq_code} ({config.freq_map_detailed.get(freq_order.get(hypo_freq_code, 1), {}).get("short", "?")}).'
                    })
        else:
            logger.debug(f"Hypothetical limit specified for env condition '{condition_label}', but this condition not found in job analysis data.")


    if not conflicts:
        logger.debug("Consistency check found no conflicts.")
    else:
         logger.info(f"Consistency check found {len(conflicts)} potential conflict(s).")

    return conflicts


# --- Formatting Functions ---

def _format_dict_section(title: str, data: Dict[str, Any], indent: int = 0) -> List[str]:
    """Helper to format a dictionary section for the text report. Returns list of strings."""
    prefix = " " * indent
    report_lines = [f"{prefix}{title}:"]
    if not data or all(v is None for v in data.values()): # Check if dict is empty or all values are None
        report_lines.append(f"{prefix}  N/A")
        return report_lines

    for key, value in data.items():
        # Skip None values for cleaner report, unless it's the only value (handled above)
        if value is None:
            continue

        key_str = str(key).replace('_', ' ').title() # Format key nicely
        if isinstance(value, dict):
            # Simple nested dict formatting - filter out None values within sub-dict
            value_str = ", ".join(f"{k}: {v}" for k, v in value.items() if v is not None)
            if value_str: # Only append if sub-dict wasn't all None
                report_lines.append(f"{prefix}  {key_str}: {value_str}")
        elif isinstance(value, list):
             # Format lists, especially the temperaments list which contains dicts
             if not value: continue # Skip empty lists
             report_lines.append(f"{prefix}  {key_str}:")
             for item in value:
                 if isinstance(item, dict):
                     # Format dict items within list (like temperaments)
                     item_desc = item.get('description', 'N/A')
                     report_lines.append(f"{prefix}    - {item_desc}")
                     # Optionally add other fields from the item dict
                     # considerations = item.get('mental_rfc_considerations')
                     # if considerations: report_lines.append(f"{prefix}      ({considerations})")
                 else:
                     report_lines.append(f"{prefix}    - {item}") # Simple list item
        else:
            # Simple key-value pair
            report_lines.append(f"{prefix}  {key_str}: {value}")
    return report_lines

def generate_formatted_job_report(job_data: Dict[str, Any]) -> str:
    """
    Formats the raw job data dictionary into a human-readable text report string
    suitable for the 'generate_job_report' MCP tool output.

    Args:
        job_data: Raw job data dictionary from db_handler.

    Returns:
        A formatted string representing the job report.
    """
    logger.debug(f"Generating formatted report for job data keys: {list(job_data.keys())}")
    analysis = get_job_analysis(job_data) # Get the structured analysis first
    if 'error' in analysis:
        logger.error(f"Error during analysis for report generation: {analysis['error']}")
        return f"Error generating report: {analysis['error']}"

    report_sections = []

    # --- Header ---
    header = [
        f"--- Job Analysis Report ---",
        f"DOT Code (NCode): {analysis.get('n_code', UNKNOWN_STRING)}",
        f"DOT Code (Formatted): {analysis.get('formatted_dot_code', UNKNOWN_STRING)}",
        f"Title: {analysis.get('job_title', UNKNOWN_STRING)}\n",
        f"Definition:",
        f"  {analysis.get('definition', 'N/A')}"
    ]
    report_sections.append("\n".join(header))

    # --- Core Characteristics ---
    core_lines = []
    core_lines.extend(_format_dict_section("Exertional Level", analysis.get('exertional_level', {})))
    core_lines.extend(_format_dict_section("Skill Level (SVP)", analysis.get('skill_level', {})))
    core_lines.extend(_format_dict_section("General Educational Development (GED)", analysis.get('ged_levels', {})))
    core_lines.extend(_format_dict_section("Worker Functions", analysis.get('worker_functions', {})))
    report_sections.append("\n".join(core_lines))

    # --- Physical Demands ---
    pd_report = ["Physical Demands:"]
    pd_data = analysis.get('physical_demands', {})
    if pd_data:
        for label, details in sorted(pd_data.items()): # Sort for consistent order
            freq_info = details.get('frequency', {})
            freq_str = f"{freq_info.get('code', '?')} ({freq_info.get('short', '?')})"
            pd_report.append(f"  {label}: {freq_str}")
    else:
        pd_report.append("  N/A")
    report_sections.append("\n".join(pd_report))

    # --- Environmental Conditions ---
    ec_report = ["Environmental Conditions:"]
    ec_data = analysis.get('environmental_conditions', {})
    if ec_data:
        for label, details in sorted(ec_data.items()): # Sort for consistent order
             if label == "Noise":
                 ec_report.append(f"  {label}: Level {details.get('level', '?')} ({details.get('description', '?')})")
             else:
                freq_info = details.get('frequency', {})
                freq_str = f"{freq_info.get('code', '?')} ({freq_info.get('short', '?')})"
                ec_report.append(f"  {label}: {freq_str}")
    else:
        ec_report.append("  N/A")
    report_sections.append("\n".join(ec_report))

    # --- Aptitudes ---
    apt_report = ["Aptitudes Required:"]
    apt_data = analysis.get('aptitudes', {})
    if apt_data:
        for name, details in sorted(apt_data.items()): # Sort for consistent order
            apt_report.append(f"  {name}: Level {details.get('level', '?')} ({details.get('description', '?')})") # Removed percentile for brevity
    else:
        apt_report.append("  N/A")
    report_sections.append("\n".join(apt_report))

    # --- Temperaments ---
    temp_report = ["Temperaments:"]
    temp_data = analysis.get('temperaments', [])
    if temp_data:
        for details in temp_data:
            temp_report.append(f"  - {details.get('description', 'N/A')}")
    else:
        temp_report.append("  N/A")
    report_sections.append("\n".join(temp_report))

    # --- Regulatory Context ---
    reg_report = ["Regulatory Context:"]
    reg_report.append(f"  Applicable VE SSR (Contextual): {analysis.get('applicable_ssr', UNKNOWN_STRING)}")

    soc = analysis.get('soc_crosswalk')
    if soc:
        reg_report.append(f"  SOC Crosswalk: {soc.get('soc_code', '?')} - {soc.get('soc_title', '?')}")
        if soc.get('crosswalk_notes'): reg_report.append(f"    Note: {soc['crosswalk_notes']}")
    else:
        reg_report.append("  SOC Crosswalk: Not Found")

    obs = analysis.get('obsolescence_analysis', {})
    reg_report.append(f"  Obsolescence Check:")
    reg_report.append(f"    Potentially Obsolete: {obs.get('is_potentially_obsolete', '?')}")
    if obs.get('risk_level', UNKNOWN_STRING) != 'Undetermined':
         reg_report.append(f"    Risk Level: {obs.get('risk_level', UNKNOWN_STRING)}")
    if obs.get('factors'):
         reg_report.append("    Factors:")
         for factor in obs['factors']: reg_report.append(f"      - {factor}")
    if obs.get('modern_equivalents'):
         reg_report.append(f"    Modern Equivalents: {', '.join(obs['modern_equivalents'])}")
    if obs.get('message'):
         reg_report.append(f"    Note: {obs.get('message')}")

    report_sections.append("\n".join(reg_report))

    # Join sections with double newlines for separation
    return "\n\n".join(report_sections)


# --- Tool-Specific Logic Wrappers/Implementations ---

# Removed the unused assess_job_obsolescence_detailed function as requested.
# The call within get_job_analysis remains as it's used by generate_formatted_job_report.