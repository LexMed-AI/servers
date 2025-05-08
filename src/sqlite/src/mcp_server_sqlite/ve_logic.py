# ve_logic.py

"""
Core Vocational Expert (VE) analysis logic, formatting, and orchestration.

This module uses database access functions (via db_handler), low-level
utility functions (from analysis_utils), and configuration data (from config)
to perform VE-specific tasks like TSA, obsolescence assessment, report formatting,
and consistency checks.
"""

import logging
from typing import Dict, Any, Optional, List

# Import utility functions, configuration data and the DatabaseHandler class definition
from . import analysis_utils
from . import config

# from .db_handler import DatabaseHandler # Removed to break circular import
from .job_obsolescence import check_job_obsolescence  # Import directly

logger = logging.getLogger(__name__)

# --- Constants ---
UNKNOWN_STRING = "Unknown"
DEFAULT_RFC_LEVEL = "SEDENTARY"  # Default RFC if not provided to TSA
DEFAULT_AGE_CATEGORY = (
    "CLOSELY APPROACHING ADVANCED AGE"  # Default Age if not provided to TSA
)
DEFAULT_EDUCATION = "UNKNOWN"  # Default Education if not provided to TSA

# --- Core Analysis Functions ---


def get_job_analysis(
    job_data: Dict[str, Any], hearing_date_str: Optional[str] = None
) -> Dict[str, Any]:
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
        applicable_ssr_result = analysis_utils.determine_applicable_ssr(
            hearing_date_str
        )
        if applicable_ssr_result:
            applicable_ssr = applicable_ssr_result
        else:
            logger.warning(
                f"Invalid hearing_date format '{hearing_date_str}', cannot determine SSR."
            )
            applicable_ssr = "Error: Invalid Date Format"
    else:
        # Default based on current date (requires current time context)
        # Or simply default to the latest known SSR if no date provided
        # For simplicity, let's assume default is latest if no date given
        # This might need refinement based on desired behavior for missing dates
        applicable_ssr = "24-3p"  # Adjust this default as needed
        logger.debug("No hearing date provided, defaulting applicable SSR.")

    # Extract basic info using .get() for safety
    dot_code = job_data.get("dotCodeReal", UNKNOWN_STRING)  # From report_query alias
    n_code = job_data.get("NCode", UNKNOWN_STRING)
    strength_num = job_data.get("StrengthNum", None)  # Get the number from DB data
    svp_num = job_data.get("SVPNum", None)
    gedr_num = job_data.get("GEDR", None)
    gedm_num = job_data.get("GEDM", None)
    gedl_num = job_data.get("GEDL", None)
    wf_data = job_data.get("WFData", None)
    wf_people = job_data.get("WFPeople", None)
    wf_things = job_data.get("WFThings", None)

    # Derive strength code ('S','L',..) using the map from config and StrengthNum
    strength_code_derived = config.strength_num_to_code.get(
        strength_num
    )  # Returns None if num invalid/missing

    analysis = {
        "job_title": job_data.get(
            "jobTitle", UNKNOWN_STRING
        ),  # From report_query alias
        "dot_code_real": dot_code,  # Store the original REAL value if needed
        "n_code": n_code,
        "formatted_dot_code": job_data.get(
            "dotCode", UNKNOWN_STRING
        ),  # Store original formatted code if available
        "applicable_ssr": applicable_ssr,
        "definition": job_data.get("definition", "N/A"),
        "exertional_level": {
            "num": strength_num,  # Keep the original number
            "code": strength_code_derived,  # Use the derived code ('S','L', None)
            "name": config.strength_code_to_name.get(strength_code_derived)
            if strength_code_derived
            else UNKNOWN_STRING,
            "description": config.strength_description_map.get(strength_code_derived)
            if strength_code_derived
            else UNKNOWN_STRING,
        },
        "skill_level": {
            "svp": svp_num,
            "svp_description": config.svp_map.get(svp_num, UNKNOWN_STRING),
            "category": analysis_utils.get_svp_category(
                svp_num
            ),  # Util handles None/invalid SVP
        },
        "ged_levels": {
            "reasoning": {
                "level": gedr_num,
                "description": config.ged_map.get(gedr_num, {}).get(
                    "reasoning", UNKNOWN_STRING
                ),
            },
            "math": {
                "level": gedm_num,
                "description": config.ged_map.get(gedm_num, {}).get(
                    "math", UNKNOWN_STRING
                ),
            },
            "language": {
                "level": gedl_num,
                "description": config.ged_map.get(gedl_num, {}).get(
                    "language", UNKNOWN_STRING
                ),
            },
        },
        "worker_functions": {
            "data": {
                "level": wf_data,
                "description": config.worker_functions_map.get("data", {}).get(
                    wf_data, UNKNOWN_STRING
                ),
            },
            "people": {
                "level": wf_people,
                "description": config.worker_functions_map.get("people", {}).get(
                    wf_people, UNKNOWN_STRING
                ),
            },
            "things": {
                "level": wf_things,
                "description": config.worker_functions_map.get("things", {}).get(
                    wf_things, UNKNOWN_STRING
                ),
            },
        },
        "physical_demands": {},  # Populated below
        "environmental_conditions": {},  # Populated below
        "aptitudes": {},  # Populated below
        "temperaments": [],  # Populated below
        "work_fields": [],  # Populated below
        "mpsms": [],  # Populated below
        # Extended analysis using utility functions
        "obsolescence_analysis": check_job_obsolescence(job_data.get("dotCode", "")),
    }

    # Process physical demands using utils
    for api_key, label in config.physical_demand_api_keys_to_labels.items():
        if api_key in job_data:
            demand_value = job_data.get(api_key)  # Get numeric value from DB data
            formatted_demand = analysis_utils.format_physical_demand(
                label, demand_value
            )
            if formatted_demand:  # Only add if valid frequency value was processed
                analysis["physical_demands"][label] = formatted_demand

    # Process environmental conditions using utils & config
    for api_key, label in config.environmental_condition_api_keys_to_labels.items():
        if api_key in job_data and api_key != "NoiseNum":  # Handle noise separately
            env_value = job_data.get(api_key)  # Get numeric value
            freq_details = analysis_utils.get_frequency_details(env_value)
            if freq_details:  # Only add if valid frequency value processed
                description = config.environmental_conditions_descriptions.get(
                    label, f"No description found for '{label}'"
                )
                analysis["environmental_conditions"][label] = {
                    "name": label,
                    "frequency": freq_details,  # Store the detailed dict from util
                    "description": description,
                }

    # Handle noise specially using config map
    noise_value = job_data.get("NoiseNum")
    noise_details = config.noise_level_descriptions.get(noise_value)
    if noise_details:
        analysis["environmental_conditions"]["Noise"] = {
            "name": "Noise",
            "level": noise_value,
            "description": f"{noise_details.get('name', '')} - {noise_details.get('description', '')}",
            "examples": noise_details.get("examples", []),
        }

    # Add temperaments using config map
    for i in range(1, 6):  # Assuming Temp1 to Temp5 keys exist in job_data
        temp_code = job_data.get(
            f"Temp{i}"
        )  # Assume DB stores string codes like 'P', 'S'
        if (
            isinstance(temp_code, str)
            and temp_code in config.temperament_rfc_considerations
        ):
            # Directly use the string code if the config map uses string keys
            analysis["temperaments"].append(
                config.temperament_rfc_considerations[temp_code]
            )
        elif temp_code is not None:
            logger.debug(
                f"Temperament code {temp_code} from Temp{i} not found in config map or is not a string."
            )

    # Add aptitudes using config maps
    # Map aptitude level numbers (1-5) to codes ('G', 'V', 'N', etc.) if needed for config keys
    # This depends on how aptitude_code_to_details_map keys are defined in config.py
    # Assuming aptitude_code_to_details_map uses CHARACTER codes ('G', 'V', 'N'...) as keys
    # NOTE: This mapping was previously used but is now kept for reference
    # level_to_apt_code = {
    #     v["level"]: k for k, v in config.aptitude_code_to_details_map.items()
    # }  # Reverse map: {1: 'G', 2: 'V', ...}

    for (
        api_key_base,
        details,
    ) in config.aptitude_code_to_details_map.items():  # Iterate through config first
        api_key = (
            f"Apt{details['api_suffix']}"  # Construct DB column name like AptGenLearn
        )
        apt_name = details.get("name", UNKNOWN_STRING)

        if api_key in job_data:
            level_val = job_data.get(api_key)  # Get numeric level (1-5) from DB
            if level_val is not None:
                try:
                    level_num = int(level_val)  # Ensure it's an integer level
                    if 1 <= level_num <= 5:
                        # Get level details using the integer level number
                        level_details = config.aptitude_level_percentiles.get(level_num)
                        if level_details:
                            analysis["aptitudes"][apt_name] = {
                                "level": level_num,
                                "description": level_details.get(
                                    "description", UNKNOWN_STRING
                                ),
                                "percentile": level_details.get(
                                    "percentile_range", UNKNOWN_STRING
                                ),
                                "rfc_compatibility": level_details.get(
                                    "rfc_compatibility", UNKNOWN_STRING
                                ),
                            }
                        else:
                            logger.warning(
                                f"Aptitude level details not found for level {level_num} in config."
                            )
                    else:
                        logger.warning(
                            f"Invalid aptitude level value {level_num} for {api_key}."
                        )
                except ValueError:
                    logger.warning(
                        f"Invalid non-integer aptitude level '{level_val}' for {api_key}. Skipping."
                    )
            # else: logger.debug(f"Aptitude {api_key} is None in job_data. Skipping.") # Implicitly skipped
        # else: logger.debug(f"Aptitude column {api_key} not in job_data.") # Implicitly skipped

    # Process Work Fields (WFLD)
    for i in range(1, 4):  # Assuming WField1Short to WField3Short
        wfld_code = job_data.get(f"WField{i}Short")
        if wfld_code:  # Add if not None or empty string
            # TODO: Consider mapping code to description from config if available
            analysis["work_fields"].append(
                {"code": wfld_code, "description": "(Description N/A)"}
            )

    # Process MPSMS
    for i in range(1, 4):  # Assuming MPSMS1Short to MPSMS3Short
        mpsms_code = job_data.get(f"MPSMS{i}Short")
        if mpsms_code:
            # TODO: Consider mapping code to description from config if available
            analysis["mpsms"].append(
                {"code": mpsms_code, "description": "(Description N/A)"}
            )

    return analysis


def _check_specific_exertional_conflict(
    hypo_limits: Dict[str, Any], job_exert_level_code: Optional[str]
) -> List[Dict[str, str]]:
    """Helper function to check specific exertional limits against job requirements."""
    exertional_conflicts: List[Dict[str, str]] = []
    if not job_exert_level_code:
        return exertional_conflicts  # Cannot check if job level unknown

    # Define standard requirements based on 20 CFR 404.1567 / 416.967
    # (Lift Occ / Lift Freq / StandWalk Hrs / Sit Hrs)
    # Using approximate hours for stand/walk/sit based on typical definitions
    job_reqs = {
        "S": {"lift_occ": 10, "lift_freq": 0, "sw_hrs": 2, "sit_hrs": 6},  # Sedentary
        "L": {"lift_occ": 20, "lift_freq": 10, "sw_hrs": 6, "sit_hrs": 2},  # Light
        "M": {"lift_occ": 50, "lift_freq": 25, "sw_hrs": 6, "sit_hrs": 2},  # Medium
        "H": {"lift_occ": 100, "lift_freq": 50, "sw_hrs": 6, "sit_hrs": 2},  # Heavy
        "V": {
            "lift_occ": 101,
            "lift_freq": 51,
            "sw_hrs": 6,
            "sit_hrs": 2,
        },  # Very Heavy (using > limits)
    }

    reqs = job_reqs.get(job_exert_level_code)
    if not reqs:
        logger.warning(
            f"Unknown job exertional level code '{job_exert_level_code}' for detailed check."
        )
        return exertional_conflicts

    job_level_name = config.strength_code_to_name.get(
        job_exert_level_code, job_exert_level_code
    )

    # Check Lifting/Carrying Occasionally
    hypo_lift_occ = hypo_limits.get("lift_carry_occ")
    if hypo_lift_occ is not None and hypo_lift_occ < reqs["lift_occ"]:
        job_req_lift_occ = reqs["lift_occ"]
        exertional_conflicts.append(
            {
                "area": "Exertional (Lift/Carry Occasional)",
                "hypothetical_limit": f"<= {hypo_lift_occ} lbs",
                "job_requirement": f"{job_level_name} requires lifting up to {job_req_lift_occ} lbs",
                "conflict_description": f"Hypothetical allows lifting only {hypo_lift_occ} lbs occasionally, but {job_level_name} work requires lifting up to {job_req_lift_occ} lbs.",
            }
        )

    # Check Lifting/Carrying Frequently
    hypo_lift_freq = hypo_limits.get("lift_carry_freq")
    if hypo_lift_freq is not None and hypo_lift_freq < reqs["lift_freq"]:
        job_req_lift_freq = reqs["lift_freq"]
        exertional_conflicts.append(
            {
                "area": "Exertional (Lift/Carry Frequent)",
                "hypothetical_limit": f"<= {hypo_lift_freq} lbs",
                "job_requirement": f"{job_level_name} requires lifting up to {job_req_lift_freq} lbs frequently",
                "conflict_description": f"Hypothetical allows lifting only {hypo_lift_freq} lbs frequently, but {job_level_name} work requires lifting up to {job_req_lift_freq} lbs frequently.",
            }
        )

    # Check Stand/Walk Hours
    hypo_sw_hours = hypo_limits.get("stand_walk_hours")
    job_req_sw_hrs = reqs["sw_hrs"]
    if (
        hypo_sw_hours is not None
        and job_exert_level_code in ["L", "M", "H", "V"]
        and hypo_sw_hours < job_req_sw_hrs
    ):
        exertional_conflicts.append(
            {
                "area": "Exertional (Stand/Walk)",
                "hypothetical_limit": f"<= {hypo_sw_hours} hours",
                "job_requirement": f"{job_level_name} requires standing/walking about {job_req_sw_hrs} hours",
                "conflict_description": f"Hypothetical limits standing/walking to {hypo_sw_hours} hours, but {job_level_name} work requires about {job_req_sw_hrs} hours.",
            }
        )
    elif (
        hypo_sw_hours is not None
        and job_exert_level_code == "S"
        and hypo_sw_hours < job_req_sw_hrs
    ):
        exertional_conflicts.append(
            {
                "area": "Exertional (Stand/Walk)",
                "hypothetical_limit": f"<= {hypo_sw_hours} hours",
                "job_requirement": f"{job_level_name} requires standing/walking about {job_req_sw_hrs} hours",
                "conflict_description": f"Hypothetical limits standing/walking to {hypo_sw_hours} hours, but {job_level_name} work requires about {job_req_sw_hrs} hours.",
            }
        )

    # Check Sit Hours
    hypo_sit_hours = hypo_limits.get("sit_hours")
    job_req_sit_hrs = reqs["sit_hrs"]
    if (
        hypo_sit_hours is not None
        and job_exert_level_code == "S"
        and hypo_sit_hours < job_req_sit_hrs
    ):
        exertional_conflicts.append(
            {
                "area": "Exertional (Sit)",
                "hypothetical_limit": f"<= {hypo_sit_hours} hours",
                "job_requirement": f"{job_level_name} requires sitting about {job_req_sit_hrs} hours",
                "conflict_description": f"Hypothetical limits sitting to {hypo_sit_hours} hours, but {job_level_name} work requires about {job_req_sit_hrs} hours.",
            }
        )

    # Check Sit/Stand Option Need
    hypo_sit_stand_need = hypo_limits.get("sit_stand_option", False)
    if hypo_sit_stand_need:
        if job_exert_level_code == "S":
            job_req_sit_hrs = reqs["sit_hrs"]
            exertional_conflicts.append(
                {
                    "area": "Exertional (Sit/Stand Option)",
                    "hypothetical_limit": "Needs sit/stand option at will",
                    "job_requirement": f"{job_level_name} requires prolonged sitting (~{job_req_sit_hrs} hours)",
                    "conflict_description": "Hypothetical requires sit/stand option at will, conflicting with prolonged sitting needed for Sedentary work unless job specifically allows alternation.",
                }
            )
        elif job_exert_level_code in ["L", "M", "H", "V"]:
            job_req_sw_hrs = reqs["sw_hrs"]
            exertional_conflicts.append(
                {
                    "area": "Exertional (Sit/Stand Option)",
                    "hypothetical_limit": "Needs sit/stand option at will",
                    "job_requirement": f"{job_level_name} requires prolonged standing/walking (~{job_req_sw_hrs} hours)",
                    "conflict_description": "Hypothetical requires sit/stand option at will, conflicting with prolonged standing/walking needed for {job_level_name} work unless job specifically allows alternation.",
                }
            )

    return exertional_conflicts


def _check_mental_ged_conflict(
    hypo_mental_limits: Dict[str, Any], job_ged_levels: Dict[str, Any]
) -> List[Dict[str, str]]:
    """Helper to check GED-related limits against job GED requirements."""
    mental_conflicts = []

    # --- GED Level Checks ---
    # Direct GED level comparisons
    for key in ["reasoning", "math", "language"]:
        hypo_limit = hypo_mental_limits.get(key)
        actual_level = job_ged_levels.get(key, {}).get("level")

        if (
            hypo_limit is not None
            and actual_level is not None
            and actual_level > hypo_limit
        ):
            mental_conflicts.append(
                {
                    "area": f"Mental (GED {key.title()})",
                    "hypothetical_limit": f"<= GED {key.title()} {hypo_limit}",
                    "job_requirement": f"GED {key.title()} Level {actual_level}",
                    "conflict_description": f"Job requires GED {key.title()} Level {actual_level}, exceeding hypothetical limit of {hypo_limit}.",
                }
            )

    # --- Instruction Complexity Check ---
    # Map Simple -> GED-R 1/2, Detailed -> GED-R 3, Complex -> GED-R 4+
    # This provides an *approximate* check against the job's reasoning level.
    instruction_map = {
        "Simple": 2,
        "Detailed": 3,
        "Complex": 6,
    }  # Max GED-R level typically associated
    hypo_instructions_val = hypo_mental_limits.get(
        "instructions"
    )  # e.g., 'Simple', 'Detailed'

    hypo_max_gedr: Optional[int] = None
    if isinstance(hypo_instructions_val, str):
        hypo_max_gedr = instruction_map.get(hypo_instructions_val)
    elif hypo_instructions_val is not None:
        logger.warning(
            f"Hypothetical instructions limit is not a string: {hypo_instructions_val}. Cannot map to GED-R."
        )

    actual_gedr = job_ged_levels.get("reasoning", {}).get("level")

    if (
        hypo_max_gedr is not None
        and actual_gedr is not None
        and actual_gedr > hypo_max_gedr
    ):
        # Retrieve compatibility notes from config for additional context
        if hypo_max_gedr is not None:  # Extra safety check for mypy
            compatibility_info = config.ged_reasoning_to_rfc_mental.get(
                hypo_max_gedr, {}
            )
            compatibility_note = ""
            incompatible_tasks = compatibility_info.get(
                "potentially_incompatible_with", []
            )
            if incompatible_tasks:
                compatibility_note = f" (Note: Level {hypo_max_gedr} reasoning is potentially incompatible with: {', '.join(incompatible_tasks)} based on config mapping)."

            mental_conflicts.append(
                {
                    "area": "Mental (Instruction Complexity)",
                    "hypothetical_limit": f"{hypo_instructions_val} instructions (Approx GED-R <= {hypo_max_gedr})",
                    "job_requirement": f"Job GED-R Level {actual_gedr}",
                    "conflict_description": f"Job requires GED Reasoning Level {actual_gedr}, potentially conflicting with hypothetical limit to {hypo_instructions_val} instructions.{compatibility_note}",
                }
            )

    return mental_conflicts


def _check_mental_pace_stress_conflict(
    hypo_mental_limits: Dict[str, Any], job_temperaments: List[Dict[str, Any]]
) -> List[Dict[str, str]]:
    """Helper to check pace and stress limits against job temperaments."""
    mental_conflicts = []
    hypo_pace = hypo_mental_limits.get(
        "pace", ""
    ).lower()  # e.g., 'slow', 'no fast pace'
    hypo_stress = hypo_mental_limits.get(
        "stress", ""
    ).lower()  # e.g., 'low', 'no high stress'

    temperament_codes = {
        temp.get("description", "").split(":")[0] for temp in job_temperaments
    }  # Get codes like 'S', 'R', 'V'

    # Check Pace vs. Temperaments R (Repetitive), V (Variety)
    if "no fast pace" in hypo_pace or "slow" in hypo_pace:
        # Variety (V) might imply more pace/change than allowed
        if "V" in temperament_codes:
            mental_conflicts.append(
                {
                    "area": "Mental (Pace/Variety)",
                    "hypothetical_limit": f"Pace: {hypo_pace}",
                    "job_requirement": "Temperament: V (Variety)",
                    "conflict_description": "Hypothetical limitation on pace/change potentially conflicts with job temperament requiring variety.",
                }
            )
    # Conversely, if hypo *requires* fast pace and job is 'R' (Repetitive)? Less common hypo.

    # Check Stress vs. Temperament S (Stress)
    if (
        "low" in hypo_stress
        or "no high stress" in hypo_stress
        or "no stress" in hypo_stress
    ):
        if "S" in temperament_codes:
            mental_conflicts.append(
                {
                    "area": "Mental (Stress)",
                    "hypothetical_limit": f"Stress: {hypo_stress}",
                    "job_requirement": "Temperament: S (Stress)",
                    "conflict_description": "Hypothetical limitation on stress tolerance conflicts with job temperament requiring performance under stress.",
                }
            )

    # Check Concentration/Precision vs Temperament T (Tolerances)
    # Assumes hypo might have 'concentration_persistence' limit (e.g., '2 hour segments', 'no tasks requiring high precision')
    hypo_conc = hypo_mental_limits.get("concentration_persistence", "").lower()
    if "no high precision" in hypo_conc or "limited precision" in hypo_conc:
        if "T" in temperament_codes:
            mental_conflicts.append(
                {
                    "area": "Mental (Concentration/Precision)",
                    "hypothetical_limit": f"Concentration/Precision: {hypo_conc}",
                    "job_requirement": "Temperament: T (Tolerances)",
                    "conflict_description": "Hypothetical limitation on precision potentially conflicts with job temperament requiring attaining precise tolerances.",
                }
            )

    return mental_conflicts


def _check_mental_social_conflict(
    hypo_mental_limits: Dict[str, Any],
    job_temperaments: List[Dict[str, Any]],
    job_worker_functions: Dict[str, Any],
) -> List[Dict[str, str]]:
    """Helper to check social interaction limits against temperaments and worker functions."""
    mental_conflicts = []
    # Freq codes: N=1, O=2, F=3, C=4
    freq_order = {"N": 1, "O": 2, "F": 3, "C": 4, None: 0}

    temperament_codes = {
        temp.get("description", "").split(":")[0] for temp in job_temperaments
    }
    people_wf_level = job_worker_functions.get("people", {}).get(
        "level"
    )  # Worker function level 0-8

    # Public Contact
    hypo_public = hypo_mental_limits.get("contact_public")  # Expect 'N', 'O', 'F', 'C'
    # Conflict if hypo limits public contact (N/O) AND job involves dealing with People (P) or high People WF level
    if freq_order.get(hypo_public, 5) <= 2:  # Hypo limits to None or Occasional
        if "P" in temperament_codes or (
            people_wf_level is not None and people_wf_level < 8
        ):  # Job involves People temperament or has significant People WF
            mental_conflicts.append(
                {
                    "area": "Mental (Social - Public)",
                    "hypothetical_limit": f"Public Contact: {hypo_public}",
                    "job_requirement": f"Temperament P or People WF Level {people_wf_level}",
                    "conflict_description": "Hypothetical limitation on public contact potentially conflicts with job requirements involving dealing with people.",
                }
            )

    # Coworker Contact (Harder to map directly - often assumed unless job is Temperament A: Alone)
    hypo_coworker = hypo_mental_limits.get("contact_coworkers")
    if freq_order.get(hypo_coworker, 5) <= 2:  # Hypo limits coworker contact
        if "A" not in temperament_codes:  # Job is NOT explicitly 'Alone'
            mental_conflicts.append(
                {
                    "area": "Mental (Social - Coworkers)",
                    "hypothetical_limit": f"Coworker Contact: {hypo_coworker}",
                    "job_requirement": "Job not performed in isolation (Temperament A not present)",
                    "conflict_description": "Hypothetical limitation on coworker contact potentially conflicts with typical workplace interaction unless job is performed in isolation.",
                }
            )

    # Supervisor Contact (Difficult - most jobs involve supervision. Conflict if hypo is very restrictive e.g., 'superficial only')
    hypo_supervisor = hypo_mental_limits.get("contact_supervisors", "").lower()
    if (
        "superficial" in hypo_supervisor
        or "none" in hypo_supervisor
        or "brief" in hypo_supervisor
    ):
        # Assume most jobs require more than superficial supervisor contact unless specified otherwise
        mental_conflicts.append(
            {
                "area": "Mental (Social - Supervisors)",
                "hypothetical_limit": f"Supervisor Contact: {hypo_supervisor}",
                "job_requirement": "Typical Supervision",
                "conflict_description": "Hypothetical limitation on supervisor contact likely conflicts with standard work requirements.",
            }
        )

    return mental_conflicts


def perform_consistency_check(
    hypothetical_limits: Dict[str, Any], job_analysis: Dict[str, Any]
) -> List[Dict[str, str]]:
    """
    Compares ALJ hypothetical limitations against the actual job requirements analysis.
    Uses standard definitions and checks multiple functional areas based on available job data
    and configuration mappings.

    Args:
        hypothetical_limits: A structured dictionary representing the limitations.
                             Example Structure:
                             {
                                 'exertional': {
                                     'lift_carry_occ': 10, 'lift_carry_freq': 5,
                                     'stand_walk_hours': 2, 'sit_hours': 6,
                                     'push_pull': 'O', 'level': 'Sedentary',
                                     'sit_stand_option': True
                                 },
                                 'postural': {'Climbing': 'N', 'Balancing': 'O', 'Stooping': 'F', ...},
                                 'manipulative': {'Reaching': 'O', 'Handling': 'F', 'Fingering': 'O', ...},
                                 'environmental': {'Fumes': 'N', 'Noise': 3, 'Heights': 'N', ...},
                                 'mental': {
                                     'svp': 2, 'reasoning': 1, 'math': 1, 'language': 2,
                                     'instructions': 'Simple', 'pace': 'Slow', 'stress': 'Low',
                                     'contact_public': 'N', 'contact_coworkers': 'O', 'contact_supervisors': 'Superficial',
                                     'concentration_persistence': '2 hour segments'
                                 }
                             }
                             Frequency codes used: N=Not Present(1), O=Occasionally(2), F=Frequently(3), C=Constantly(4)
                             Noise: Level 1-5
                             GED/SVP: Level number
        job_analysis: The structured job analysis dictionary from get_job_analysis().

    Returns:
        A list of dictionaries, where each dictionary represents an identified conflict.
    """
    conflicts = []
    if not hypothetical_limits or not job_analysis or "error" in job_analysis:
        logger.warning("perform_consistency_check received invalid input.")
        return [{"error": "Invalid input for consistency check"}]

    logger.debug(
        f"Performing consistency check for DOT {job_analysis.get('formatted_dot_code')}"
    )

    freq_order = {"N": 1, "O": 2, "F": 3, "C": 4, None: 0}

    # --- Exertional Check (Detailed) ---
    hypo_exert_limits = hypothetical_limits.get("exertional", {})
    job_exert_code = job_analysis.get("exertional_level", {}).get("code")
    conflicts.extend(
        _check_specific_exertional_conflict(hypo_exert_limits, job_exert_code)
    )
    # Note: Push/Pull check requires specific push/pull force/frequency data in job_analysis,
    # which is not standard in base DOT data derived solely from StrengthNum. Check skipped.

    # --- Mental Checks (Refined) ---
    # Compares GED levels, instruction complexity, pace, stress, and social interaction.
    # Uses mappings in config.py but does not parse full policy text from SSRs/POMs.
    hypo_mental_limits = hypothetical_limits.get("mental", {})

    # --- Skill Level (SVP) Check ---
    # Compares max SVP allowed by hypo against the job's actual SVP.
    hypo_svp_limit = hypo_mental_limits.get(
        "svp"
    )  # Access directly since hypo_mental_limits is already the 'mental' sub-dict
    actual_svp = job_analysis.get("skill_level", {}).get("svp")
    if (
        hypo_svp_limit is not None
        and actual_svp is not None
        and actual_svp > hypo_svp_limit
    ):
        conflicts.append(
            {
                "area": "Skill (SVP)",
                "hypothetical_limit": f"<= SVP {hypo_svp_limit}",
                "job_requirement": f"SVP {actual_svp}",
                "conflict_description": f"Job requires SVP {actual_svp}, but hypothetical limits to SVP {hypo_svp_limit} or less.",
            }
        )

    job_ged_levels = job_analysis.get("ged_levels", {})
    job_temperaments = job_analysis.get("temperaments", [])
    job_worker_functions = job_analysis.get("worker_functions", {})

    conflicts.extend(_check_mental_ged_conflict(hypo_mental_limits, job_ged_levels))
    conflicts.extend(
        _check_mental_pace_stress_conflict(hypo_mental_limits, job_temperaments)
    )
    conflicts.extend(
        _check_mental_social_conflict(
            hypo_mental_limits, job_temperaments, job_worker_functions
        )
    )

    # --- Physical Demands Check (Postural, Manipulative, Visual, Sensory) ---
    # Compares frequency requirements based on N/O/F/C codes.
    hypo_physical_limits = {
        **hypothetical_limits.get("postural", {}),
        **hypothetical_limits.get("manipulative", {}),
        **hypothetical_limits.get("visual", {}),
        **hypothetical_limits.get("sensory", {}),
    }
    actual_physical_demands = job_analysis.get("physical_demands", {})

    for demand_label, hypo_freq_code in hypo_physical_limits.items():
        if hypo_freq_code not in freq_order:
            logger.warning(
                f"Skipping check for '{demand_label}' due to invalid hypo limit: {hypo_freq_code}"
            )
            continue

        actual_demand_info = actual_physical_demands.get(demand_label)
        if actual_demand_info:
            actual_freq_code = actual_demand_info.get("frequency", {}).get("code")
            hypo_order = freq_order.get(hypo_freq_code, 0)
            actual_order = freq_order.get(actual_freq_code, 0)

            if actual_order > hypo_order:
                conflicts.append(
                    {
                        "area": f"Physical ({demand_label})",
                        "hypothetical_limit": f"{hypo_freq_code} ({config.freq_map_detailed.get(hypo_order, {}).get('short', '?')})",
                        "job_requirement": f"{actual_freq_code} ({actual_demand_info.get('frequency', {}).get('short')})",
                        "conflict_description": f"Job requires {demand_label} {actual_freq_code} ({actual_demand_info.get('frequency', {}).get('short')}), but hypothetical limits to {hypo_freq_code} ({config.freq_map_detailed.get(hypo_order, {}).get('short', '?')}).",
                    }
                )
        elif hypo_order < 2:  # Hypo avoids (N) a demand the job doesn't list
            pass
        elif hypo_freq_code is not None:
            logger.debug(
                f"Hypothetical limit specified for '{demand_label}', but this demand not found in job analysis data (implies Not Present)."
            )

    # --- Environmental Check ---
    # Compares frequency or level requirements (e.g., Noise).
    hypo_env_limits = hypothetical_limits.get("environmental", {})
    actual_env_conditions = job_analysis.get("environmental_conditions", {})

    for condition_label, hypo_limit_value in hypo_env_limits.items():
        actual_condition_info = actual_env_conditions.get(condition_label)
        if actual_condition_info:
            if condition_label == "Noise":
                try:
                    hypo_noise_level_limit = int(hypo_limit_value)
                    actual_noise_level = actual_condition_info.get("level")

                    if (
                        actual_noise_level is not None
                        and actual_noise_level > hypo_noise_level_limit
                    ):
                        hypo_noise_name = config.noise_map.get(
                            hypo_noise_level_limit, "?"
                        )
                        actual_noise_name = config.noise_map.get(
                            actual_noise_level, "?"
                        )
                        conflicts.append(
                            {
                                "area": "Environmental (Noise Level)",
                                "hypothetical_limit": f"<= Level {hypo_noise_level_limit} ({hypo_noise_name})",
                                "job_requirement": f"Level {actual_noise_level} ({actual_noise_name})",
                                "conflict_description": f"Job requires Noise Level {actual_noise_level} ({actual_noise_name}), but hypothetical limits to Level {hypo_noise_level_limit} ({hypo_noise_name}) or less.",
                            }
                        )
                except (ValueError, TypeError):
                    logger.warning(
                        f"Invalid hypothetical noise level limit: {hypo_limit_value}. Skipping noise check."
                    )
            else:  # Handle frequency-based environmental factors
                hypo_freq_code = hypo_limit_value
                if hypo_freq_code not in freq_order:
                    logger.warning(
                        f"Skipping check for '{condition_label}' due to invalid hypo limit: {hypo_freq_code}"
                    )
                    continue

                actual_freq_code = actual_condition_info.get("frequency", {}).get(
                    "code"
                )
                hypo_order = freq_order.get(hypo_freq_code, 0)
                actual_order = freq_order.get(actual_freq_code, 0)

                if actual_order > hypo_order:
                    conflicts.append(
                        {
                            "area": f"Environmental ({condition_label})",
                            "hypothetical_limit": f"{hypo_freq_code} ({config.freq_map_detailed.get(hypo_order, {}).get('short', '?')})",
                            "job_requirement": f"{actual_freq_code} ({actual_condition_info.get('frequency', {}).get('short')})",
                            "conflict_description": f"Job requires exposure to {condition_label} {actual_freq_code} ({actual_condition_info.get('frequency', {}).get('short')}), but hypothetical limits to {hypo_freq_code} ({config.freq_map_detailed.get(hypo_order, {}).get('short', '?')}).",
                        }
                    )
        elif hypo_limit_value == "N" or freq_order.get(hypo_limit_value, 5) < 2:
            pass
        elif hypo_limit_value is not None:
            logger.debug(
                f"Hypothetical limit specified for env condition '{condition_label}', but this condition not found in job analysis data (implies Not Present)."
            )

    if not conflicts:
        logger.debug("Consistency check found no conflicts.")
    else:
        logger.info(f"Consistency check found {len(conflicts)} potential conflict(s).")

    return conflicts


# --- Formatting Functions ---


def _format_dict_section(
    title: str, data: Dict[str, Any], indent: int = 0
) -> List[str]:
    """Helper to format a dictionary section for the text report. Returns list of strings."""
    prefix = " " * indent
    report_lines = [f"{prefix}{title}:"]
    if not data or all(
        v is None for v in data.values()
    ):  # Check if dict is empty or all values are None
        report_lines.append(f"{prefix}  N/A")
        return report_lines

    for key, value in data.items():
        # Skip None values for cleaner report, unless it's the only value (handled above)
        if value is None:
            continue

        key_str = str(key).replace("_", " ").title()  # Format key nicely
        if isinstance(value, dict):
            # Simple nested dict formatting - filter out None values within sub-dict
            value_str = ", ".join(
                f"{k}: {v}" for k, v in value.items() if v is not None
            )
            if value_str:  # Only append if sub-dict wasn't all None
                report_lines.append(f"{prefix}  {key_str}: {value_str}")
        elif isinstance(value, list):
            # Format lists, especially the temperaments list which contains dicts
            if not value:
                continue  # Skip empty lists
            report_lines.append(f"{prefix}  {key_str}:")
            for item in value:
                if isinstance(item, dict):
                    # Format dict items within list (like temperaments)
                    item_desc = item.get("description", "N/A")
                    report_lines.append(f"{prefix}    - {item_desc}")
                    # Optionally add other fields from the item dict
                    # considerations = item.get('mental_rfc_considerations')
                    # if considerations: report_lines.append(f"{prefix}      ({considerations})")
                else:
                    report_lines.append(f"{prefix}    - {item}")  # Simple list item
        else:
            # Simple key-value pair
            report_lines.append(f"{prefix}  {key_str}: {value}")
    return report_lines


def generate_formatted_job_report(analysis_data: Dict[str, Any]) -> str:
    """
    Formats the structured job analysis dictionary into a human-readable text report string
    suitable for the 'generate_job_report' MCP tool output.

    Assumes the input dictionary is the result of get_job_analysis().

    Args:
        analysis_data: A dictionary containing the structured job analysis.
                       Expected keys include 'n_code', 'formatted_dot_code', 'job_title',
                       'definition', 'exertional_level', 'skill_level', 'ged_levels',
                       'worker_functions', 'physical_demands', 'environmental_conditions',
                       'aptitudes', 'temperaments', 'applicable_ssr', 'obsolescence_analysis', etc.

    Returns:
        A formatted string representing the job report.
    """
    logger.debug(
        f"Generating formatted report for job analysis keys: {list(analysis_data.keys())}"
    )
    if "error" in analysis_data:
        logger.error(
            f"Error within analysis data provided for report generation: {analysis_data['error']}"
        )
        return f"Error generating report: {analysis_data['error']}"
    if not analysis_data:
        logger.error("generate_formatted_job_report received empty analysis_data.")
        return "Error generating report: No analysis data provided."

    report_sections = []

    # --- Header ---
    header = [
        "--- Job Analysis Report ---",
        f"DOT Code (NCode): {analysis_data.get('n_code', UNKNOWN_STRING)}",
        f"DOT Code (Formatted): {analysis_data.get('formatted_dot_code', UNKNOWN_STRING)}",
        f"Title: {analysis_data.get('job_title', UNKNOWN_STRING)}\n",
        "Definition:",
        f"  {analysis_data.get('definition', 'N/A')}",
    ]
    report_sections.append("\n".join(header))

    # --- Core Characteristics ---
    core_lines = []
    core_lines.extend(
        _format_dict_section(
            "Exertional Level", analysis_data.get("exertional_level", {})
        )
    )
    core_lines.extend(
        _format_dict_section("Skill Level (SVP)", analysis_data.get("skill_level", {}))
    )
    core_lines.extend(
        _format_dict_section(
            "General Educational Development (GED)", analysis_data.get("ged_levels", {})
        )
    )
    core_lines.extend(
        _format_dict_section(
            "Worker Functions", analysis_data.get("worker_functions", {})
        )
    )
    report_sections.append("\n".join(core_lines))

    # --- Physical Demands ---
    pd_report = ["Physical Demands:"]
    pd_data = analysis_data.get("physical_demands", {})
    if pd_data:
        for label, details in sorted(pd_data.items()):  # Sort for consistent order
            freq_info = details.get("frequency", {})
            freq_str = f"{freq_info.get('code', '?')} ({freq_info.get('short', '?')})"
            pd_report.append(f"  {label}: {freq_str}")
    else:
        pd_report.append("  N/A")
    report_sections.append("\n".join(pd_report))

    # --- Environmental Conditions ---
    ec_report = ["Environmental Conditions:"]
    ec_data = analysis_data.get("environmental_conditions", {})
    if ec_data:
        for label, details in sorted(ec_data.items()):  # Sort for consistent order
            if label == "Noise":
                ec_report.append(
                    f"  {label}: Level {details.get('level', '?')} ({details.get('description', '?')})"
                )
            else:
                freq_info = details.get("frequency", {})
                freq_str = (
                    f"{freq_info.get('code', '?')} ({freq_info.get('short', '?')})"
                )
                ec_report.append(f"  {label}: {freq_str}")
    else:
        ec_report.append("  N/A")
    report_sections.append("\n".join(ec_report))

    # --- Aptitudes ---
    apt_report = ["Aptitudes Required:"]
    apt_data = analysis_data.get("aptitudes", {})
    if apt_data:
        for name, details in sorted(apt_data.items()):  # Sort for consistent order
            apt_report.append(
                f"  {name}: Level {details.get('level', '?')} ({details.get('description', '?')})"
            )  # Removed percentile for brevity
    else:
        apt_report.append("  N/A")
    report_sections.append("\n".join(apt_report))

    # --- Temperaments ---
    temp_report = ["Temperaments:"]
    temp_data = analysis_data.get("temperaments", [])
    if temp_data:
        for details in temp_data:
            temp_report.append(f"  - {details.get('description', 'N/A')}")
    else:
        temp_report.append("  N/A")
    report_sections.append("\n".join(temp_report))

    # --- Regulatory Context ---
    reg_report = ["Regulatory Context:"]
    reg_report.append(
        f"  Applicable VE SSR (Contextual): {analysis_data.get('applicable_ssr', UNKNOWN_STRING)}"
    )

    obs = analysis_data.get("obsolescence_analysis", {})
    reg_report.append("  Obsolescence Check:")
    reg_report.append(
        f"    Potentially Obsolete: {obs.get('is_potentially_obsolete', '?')}"
    )
    if obs.get("risk_level", UNKNOWN_STRING) != "Undetermined":
        reg_report.append(f"    Risk Level: {obs.get('risk_level', UNKNOWN_STRING)}")
    if obs.get("factors"):
        reg_report.append("    Factors:")
        for factor in obs["factors"]:
            reg_report.append(f"      - {factor}")
    if obs.get("modern_equivalents"):
        reg_report.append(
            f"    Modern Equivalents: {', '.join(obs['modern_equivalents'])}"
        )
    if obs.get("message"):
        reg_report.append(f"    Note: {obs.get('message')}")

    report_sections.append("\n".join(reg_report))

    # Join sections with double newlines for separation
    return "\n\n".join(report_sections)


# --- Tool-Specific Logic Wrappers/Implementations ---

# Removed the unused assess_job_obsolescence_detailed function as requested.
# The call within get_job_analysis remains as it's used by generate_formatted_job_report.
