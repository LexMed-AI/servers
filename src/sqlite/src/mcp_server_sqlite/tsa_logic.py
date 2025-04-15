# tsa_logic.py

"""
Contains the logic for performing Transferable Skills Analysis (TSA).
This module implements the step-by-step process based on vocational
expert standards and SSA guidelines.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List

# Local imports
from .db_handler import DatabaseHandler
from . import config
# from . import analysis_utils # Not currently used, commented out
from .ve_logic import get_job_analysis # Import necessary function from ve_logic

# Constants from ve_logic needed here (or defined centrally)
UNKNOWN_STRING = "Unknown"

logger = logging.getLogger(__name__)

# --- Load Grid Rules Data --- #
GRID_RULES_DATA: Optional[Dict[str, Any]] = None
GRID_RULES_PATH = Path(__file__).parent / "reference" / "medical_vocational_guidelines.json"

try:
    with open(GRID_RULES_PATH, 'r') as f:
        GRID_RULES_DATA = json.load(f)
        logger.info(f"Successfully loaded Grid Rules data from {GRID_RULES_PATH}")
except FileNotFoundError:
    logger.error(f"Grid Rules JSON file not found at {GRID_RULES_PATH}. Grid rule application will not work.")
except json.JSONDecodeError:
    logger.error(f"Error decoding JSON from {GRID_RULES_PATH}. Grid rule application will not work.")
except Exception as e:
    logger.error(f"An unexpected error occurred loading {GRID_RULES_PATH}: {e}")
# --- End Load Grid Rules Data --- #

# --- Helper Functions for Grid Rule Application --- #

def _map_rfc_to_table_key(rfc_strength: str) -> Optional[str]:
    """Maps RFC strength string to the key used for tables in GRID_RULES_DATA."""
    rfc_lower = rfc_strength.lower()
    if rfc_lower == "sedentary":
        return "201.00" # Corresponds to Table 1 section key
    elif rfc_lower == "light":
        return "202.00" # Corresponds to Table 2 section key
    elif rfc_lower == "medium":
        return "203.00" # Corresponds to Table 3 section key
    # Heavy/Very Heavy are handled by 204.00 text, not a table in the same format
    elif rfc_lower in ["heavy", "very heavy"]:
        return "204.00"
    else:
        logger.warning(f"Unsupported RFC strength for Grid Rule table mapping: {rfc_strength}")
        return None

def _map_age_category(age_input: str) -> str:
    """Maps rough age category input to the specific strings used in Grid Rules."""
    # This requires a predefined mapping based on SSA definitions
    # Example mapping (Needs refinement based on exact SSA definitions expected as input)
    age_lower = age_input.lower().replace("_", " ") # Allow underscores
    if "advanced age" in age_lower or age_lower == "advanced": # Matches "Advanced age"
        return "Advanced age"
    elif "closely approaching advanced" in age_lower: # Matches "Closely approaching advanced age"
        return "Closely approaching advanced age"
    elif "younger" in age_lower and "45-49" in age_lower: # Matches "Younger individual age 45-49"
        return "Younger individual age 45-49"
    elif "younger" in age_lower: # Matches "Younger individual age 18-44" or just "Younger individual"
        # Need to distinguish between 18-44 and 45-49 based on input if possible
        # Defaulting to the broader category if only 'Younger' is given, but rules differ.
        # Assume 18-44 if not specified 45-49 for now.
        return "Younger individual age 18-44" # Or map to just "Younger individual" if tables use that
    elif "closely approaching retirement" in age_lower: # Matches "Closely approaching retirement age" (Table 3)
        return "Closely approaching retirement age"
    else:
        logger.warning(f"Could not map age category: '{age_input}'")
        return age_input # Return original if no mapping found

def _map_education_level(education_input: str) -> str:
    """Maps rough education level input to the specific strings used in Grid Rules."""
    # This requires a predefined mapping based on SSA definitions
    # Example mapping (Needs refinement based on exact SSA definitions expected as input)
    edu_lower = education_input.lower().replace("_", " ")
    if edu_lower == "illiterate":
        return "Illiterate"
    elif edu_lower in ["limited or less", "limited", "marginal or less", "marginal"]:
        # Need careful handling based on rule specificity (e.g., Table 1 uses "Limited or less")
        # Table 2 differentiates "Illiterate" vs "Limited or Marginal, but not Illiterate"
        # Table 3 differentiates "Marginal or Illiterate" vs "Limited"
        # For simplicity now, map common ones; may need RFC context for precise mapping.
        if "marginal" in edu_lower and "illiterate" in edu_lower: # Table 3 specific
             return "Marginal or Illiterate"
        elif "marginal" in edu_lower and "not illiterate" in edu_lower: # Table 2 specific
             return "Limited or Marginal, but not Illiterate"
        elif "limited or less" in edu_lower: # Table 1 & 2
            return "Limited or less"
        elif "limited" in edu_lower: # Table 3 uses just "Limited"
            return "Limited"
        else: # Fallback
            return "Limited or less" # Default assumption, needs review
    elif "high school" in edu_lower:
        # Rules differentiate based on direct entry into skilled work
        # This info isn't in the education level alone. Assume non-direct entry for now.
        if "does not provide for direct entry" in edu_lower:
             return "High school graduate or more—does not provide for direct entry into skilled work"
        elif "provides for direct entry" in edu_lower:
             return "High school graduate or more—provides for direct entry into skilled work"
        else:
             # Default assumption if not specified
             return "High school graduate or more—does not provide for direct entry into skilled work"
    elif "graduate or more" in edu_lower: # Generic HS grad+
         return "High school graduate or more—does not provide for direct entry into skilled work"
    else:
        logger.warning(f"Could not map education level: '{education_input}'")
        return education_input

def _format_previous_work_experience(skill_category: str, transferable: bool) -> str:
    """Formats the 'previous_work_experience' string based on skill and transferability."""
    # Map skill category from analysis_utils/config to Grid Rule terms
    # Assuming config.svp_to_skill_level maps SVP to "Skilled", "Semiskilled", "Unskilled"
    skill_lower = skill_category.lower()

    if skill_lower == "unskilled":
        return "Unskilled or none" # Grid rules often combine these
    elif skill_lower in ["skilled", "semiskilled", "semi-skilled"]:
        if transferable:
            return "Skilled or semiskilled—skills transferable"
        else:
            return "Skilled or semiskilled—skills not transferable"
    elif skill_lower == "none": # Handle explicit 'none'
        return "Unskilled or none"
    else:
        logger.warning(f"Unknown skill category for formatting: {skill_category}")
        return "Unknown" # Should not happen with proper source analysis

def apply_grid_rule(rfc_strength: str, age_category: str, education_level: str, prw_skill_category: str, skills_transferable: bool) -> Dict[str, Optional[str]]:
    """
    Applies the Medical-Vocational Guidelines (Grid Rules) based on inputs.

    Args:
        rfc_strength: Claimant's RFC (e.g., "SEDENTARY", "LIGHT").
        age_category: Claimant's age category (using terms like "Advanced age", etc.).
        education_level: Claimant's education level (using terms like "Limited or less", etc.).
        prw_skill_category: Skill level of PRW ("Skilled", "Semiskilled", "Unskilled").
        skills_transferable: Boolean indicating if skills are transferable (relevant if PRW is skilled/semiskilled).

    Returns:
        A dictionary with 'rule_id' and 'decision' if a rule applies, otherwise indicates no rule matched.
    """
    if GRID_RULES_DATA is None:
        return {"rule_id": None, "decision": "Error: Grid Rules data not loaded.", "reason": "GRID_RULES_DATA is None"}

    table_key = _map_rfc_to_table_key(rfc_strength)
    if not table_key:
        return {"rule_id": None, "decision": "Not Applicable", "reason": f"RFC '{rfc_strength}' does not map to a standard Grid table."}

    # Handle Heavy/Very Heavy separately based on 204.00 text
    if table_key == "204.00":
         logger.info("RFC is Heavy or Very Heavy; applying principle from 204.00.")
         # Section 204.00 generally directs a finding of 'Not disabled'
         return {"rule_id": "204.00 (Principle)", "decision": "Not disabled", "reason": "RFC allows Heavy or Very Heavy work (per 204.00 principle)."}

    # Find the relevant section/table in the loaded data
    table_section = next((section for section in GRID_RULES_DATA.get("sections", []) if section.get("section_number") == table_key), None)
    if not table_section or "table" not in table_section:
        logger.error(f"Could not find table data for section {table_key} in GRID_RULES_DATA.")
        return {"rule_id": None, "decision": "Error: Grid Rules data structure unexpected.", "reason": f"Missing table for section {table_key}"}

    rules = table_section["table"].get("rules", [])

    # Map inputs to the specific strings used in the JSON
    mapped_age = _map_age_category(age_category)
    mapped_education = _map_education_level(education_level)
    # Determine transferability status needed for formatting
    # If PRW is unskilled, transferability is irrelevant for the rule string
    transferable_status = skills_transferable if prw_skill_category.lower() not in ["unskilled", "none"] else False
    formatted_prw = _format_previous_work_experience(prw_skill_category, transferable_status)

    logger.debug(f"Attempting Grid Rule match for: RFC Table={table_key}, Age='{mapped_age}', Edu='{mapped_education}', PRW='{formatted_prw}'")

    # Find the matching rule
    for rule in rules:
        # Normalize PWE string from JSON (remove footnote markers if present)
        rule_pwe = rule.get("previous_work_experience", "").split("—")[0].strip()
        pwe_match_string = formatted_prw.split("—")[0].strip()

        # Adjust check for PRW - handle slight variations like 'semiskilled' vs 'semi-skilled'
        # A more robust approach might involve canonical mapping
        pwe_matches = (pwe_match_string.replace("-","") == rule_pwe.replace("-",""))
        
        # Handle education variations - some rules are less specific
        # Example: Rule 203.02 'Limited or less' vs input 'Limited'
        # This basic check assumes exact match after mapping, might need refinement
        education_matches = (mapped_education == rule.get("education"))
        # A simple fallback for less specific rules might be needed:
        # if not education_matches and "Limited or less" in rule.get("education","") and mapped_education == "Limited":
        #     education_matches = True 
        # elif not education_matches and "Limited or Marginal, but not Illiterate" in rule.get("education","") and mapped_education in ["Limited", "Marginal"]:
             # Requires more complex logic based on table structure

        if (rule.get("age") == mapped_age and
            education_matches and 
            pwe_matches):
            # Check transferability part if PWE requires it
            if "transferable" in rule.get("previous_work_experience", ""):
                 rule_is_transferable = "skills transferable" in rule.get("previous_work_experience", "")
                 if rule_is_transferable == skills_transferable:
                     logger.info(f"Matched Grid Rule: {rule.get('rule_id')}")
                     return {"rule_id": rule.get("rule_id"), "decision": rule.get("decision")}
            else: # Rule PWE is 'Unskilled or none', transferability doesn't matter
                 logger.info(f"Matched Grid Rule: {rule.get('rule_id')}")
                 return {"rule_id": rule.get("rule_id"), "decision": rule.get("decision")}

    logger.warning("No exact Grid Rule match found.")
    return {"rule_id": None, "decision": "Rule Not Applicable", "reason": "No exact match found for the provided vocational profile."}

# --- End Helper Functions --- #

# --- Skill Identification & Transferability Helpers ---

def _extract_potential_skills(analysis_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extracts key vocational factors relevant to skill identification from job analysis data.

    Args:
        analysis_data: The dictionary returned by get_job_analysis.

    Returns:
        A dictionary containing SVP, Worker Functions, Work Fields, and MPSMS.
        Returns empty dict if analysis data is missing expected keys.
    """
    skills = {}
    try:
        skills['svp'] = analysis_data.get('skill_level', {}).get('svp')
        # Worker Functions - handle potential None or missing keys gracefully
        wf_data = analysis_data.get('worker_functions', {})
        skills['worker_functions'] = {
            'data': wf_data.get('data'),
            'people': wf_data.get('people'),
            'things': wf_data.get('things')
        }
        # Work Fields - store as a list of codes
        skills['work_fields'] = [wf.get('code') for wf in analysis_data.get('work_fields', []) if wf.get('code')]
        # MPSMS - store as a list of codes
        skills['mpsms'] = [m.get('code') for m in analysis_data.get('mpsms', []) if m.get('code')]
        
        # Validate extracted data (e.g., ensure SVP is a number)
        if not isinstance(skills.get('svp'), (int, float)):
             logger.warning(f"Invalid or missing SVP in analysis data: {analysis_data.get('job_title')}")
             skills['svp'] = None # Mark as None if invalid
             
    except Exception as e:
        logger.error(f"Error extracting skills from analysis data: {e}", exc_info=True)
        return {} # Return empty on error
        
    # Return None for WF ratings if they weren't found
    for key in ['data', 'people', 'things']:
        if skills['worker_functions'][key] is None:
           logger.warning(f"Missing Worker Function '{key}' rating in analysis data for {analysis_data.get('job_title')}")
           # Keep as None to indicate missing data during comparison
           
    # Filter out None values from lists just in case
    skills['work_fields'] = [code for code in skills['work_fields'] if code is not None]
    skills['mpsms'] = [code for code in skills['mpsms'] if code is not None]

    return skills

def _is_exertion_within_rfc(target_exertion: Optional[str], rfc_strength: str) -> bool:
    """Checks if the target job's exertion level is within the claimant's RFC."""
    if not target_exertion:
        logger.warning("Target job exertion level is missing or unknown.")
        return False # Cannot confirm transferability if target exertion is unknown
       
    # Define exertion hierarchy (lower number is lighter)
    exertion_levels = {
        "sedentary": 1,
        "light": 2,
        "medium": 3,
        "heavy": 4,
        "very heavy": 5
    }
    
    target_level = exertion_levels.get(target_exertion.lower())
    rfc_level = exertion_levels.get(rfc_strength.lower())
    
    if target_level is None:
        logger.warning(f"Unknown target exertion level encountered: {target_exertion}")
        return False
    if rfc_level is None:
        logger.warning(f"Unknown RFC strength encountered: {rfc_strength}")
        # If RFC is unknown, we cannot definitively say if exertion is met
        return False 
       
    return target_level <= rfc_level

def _evaluate_transferability(source_skills: Dict[str, Any], target_analysis: Dict[str, Any], rfc_strength: str) -> Dict[str, Any]:
    """Evaluates skill transferability from source to target based on POMS DI 25015.017 principles.

    Args:
        source_skills: Dictionary from _extract_potential_skills for the PRW.
        target_analysis: Dictionary from get_job_analysis for the potential target job.
        rfc_strength: Claimant's RFC strength level.

    Returns:
        Dictionary with 'transferable' (bool), 'reason' (str), and detailed 'checks_passed' (dict).
    """
    checks_passed = {
        "exertion_met": False,
        "svp_compatible": False,
        "worker_functions_match": False,
        "wfld_mpsms_overlap": False
    }
    reasons = []

    # --- Pre-checks: Ensure necessary data exists --- #
    target_skills = _extract_potential_skills(target_analysis)
    if not target_skills or not source_skills:
        return {"transferable": False, "reason": "Missing necessary skill data in source or target analysis.", "checks_passed": checks_passed}

    source_svp = source_skills.get('svp')
    target_svp = target_skills.get('svp')
    source_wf = source_skills.get('worker_functions')
    target_wf = target_skills.get('worker_functions')

    if source_svp is None or target_svp is None:
        reasons.append("SVP missing in source or target.")
        # Cannot proceed with SVP check, implicitly fail
    if not source_wf or not target_wf or None in source_wf.values() or None in target_wf.values():
        reasons.append("Worker Function ratings missing or incomplete in source or target.")
        # Cannot proceed with WF check, implicitly fail
       
    # If essential data missing, return early
    if reasons:
         return {"transferable": False, "reason": "Essential data missing for comparison: " + "; ".join(reasons), "checks_passed": checks_passed}

    # --- 1. Check Exertion Level --- #
    target_exertion = target_analysis.get('physical_demands', {}).get('exertion_level')
    checks_passed["exertion_met"] = _is_exertion_within_rfc(target_exertion, rfc_strength)
    if not checks_passed["exertion_met"]:
        reasons.append(f"Target exertion ({target_exertion}) exceeds RFC ({rfc_strength}).")
    else:
        reasons.append(f"Target exertion ({target_exertion}) within RFC ({rfc_strength}).")

    # --- 2. Check SVP Level --- #
    # Per POMS DI 25015.017 B.3.c - target SVP must be <= source SVP, max 2 level reduction
    if isinstance(source_svp, (int, float)) and isinstance(target_svp, (int, float)):
        if target_svp <= source_svp and (source_svp - target_svp <= 2):
            checks_passed["svp_compatible"] = True
            reasons.append(f"Target SVP ({target_svp}) compatible with Source SVP ({source_svp}).")
        else:
            reasons.append(f"Target SVP ({target_svp}) not compatible with Source SVP ({source_svp}) (max 2 level reduction rule).")
    else:
        reasons.append("Invalid SVP values for comparison.") # Should have been caught earlier, but double-check

    # --- 3. Check Worker Functions --- #
    # Requires identical ratings for DPT per typical TSA practice
    if (source_wf and target_wf and 
        source_wf.get('data') == target_wf.get('data') and
        source_wf.get('people') == target_wf.get('people') and
        source_wf.get('things') == target_wf.get('things')):
        # Ensure none were None implicitly
        if None not in [source_wf.get('data'), source_wf.get('people'), source_wf.get('things')]:
             checks_passed["worker_functions_match"] = True
             reasons.append("Worker Functions (DPT) match.")
        else:
             reasons.append("Worker Functions comparison failed due to missing ratings.")
    else:
        reasons.append("Worker Functions (DPT) do not match.")
       
    # --- 4. Check Work Field / MPSMS Overlap --- #
    # Requires at least one match in *either* category
    source_wfld = set(source_skills.get('work_fields', []))
    target_wfld = set(target_skills.get('work_fields', []))
    source_mpsms = set(source_skills.get('mpsms', []))
    target_mpsms = set(target_skills.get('mpsms', []))

    wfld_overlap = len(source_wfld.intersection(target_wfld)) > 0
    mpsms_overlap = len(source_mpsms.intersection(target_mpsms)) > 0

    if wfld_overlap or mpsms_overlap:
        checks_passed["wfld_mpsms_overlap"] = True
        reason_overlap = []
        if wfld_overlap:
            reason_overlap.append(f"Work Field overlap found ({source_wfld.intersection(target_wfld)}).")
        if mpsms_overlap:
            reason_overlap.append(f"MPSMS overlap found ({source_mpsms.intersection(target_mpsms)}).")
        reasons.append(" ".join(reason_overlap))
    else:
        reasons.append("No overlap found in Work Fields or MPSMS.")

    # --- Final Determination --- #
    is_transferable = all(checks_passed.values())
    final_reason = "Skills transferable based on criteria." if is_transferable else "Skills not transferable to this specific job: " + "; ".join([r for passed, r in zip(checks_passed.values(), reasons[-4:]) if not passed]) # Get last 4 reasons corresponding to checks

    return {
        "transferable": is_transferable,
        "reason": final_reason,
        "checks_passed": checks_passed,
        "details": {
            "source_svp": source_svp,
            "target_svp": target_svp,
            "source_wf": source_wf,
            "target_wf": target_wf,
            "wfld_overlap": list(source_wfld.intersection(target_wfld)),
            "mpsms_overlap": list(source_mpsms.intersection(target_mpsms))
        }
    }

# --- End Skill Identification & Transferability Helpers ---


# --- Tool-Specific Logic Wrappers/Implementations ---

async def perform_tsa_analysis(db_handler: DatabaseHandler,
                         source_dot_code: str,
                         rfc_strength: str,
                         age_category: str,
                         education_level: str,
                         target_dot_codes: Optional[List[str]] = None
                         ) -> Dict[str, Any]:
    """
    Performs Transferable Skills Analysis (TSA).
    **Partially Implemented** - Grid Rule application added, but skill identification
    and transferability evaluation remain placeholders.

    Args:
        db_handler: Instance of DatabaseHandler to query job data.
        source_dot_code: DOT code of the Past Relevant Work (PRW).
        rfc_strength: Claimant's RFC strength level ('SEDENTARY', 'LIGHT', etc.).
        age_category: Claimant's age category based on SSA rules (e.g., "ADVANCED AGE").
        education_level: Claimant's education level based on SSA rules (e.g., "LIMITED", "HIGH SCHOOL").
        target_dot_codes: Optional list of specific target DOT codes to evaluate against.

    Returns:
        Dictionary containing the preliminary TSA results.
    """
    logger.info(f"Performing TSA: PRW={source_dot_code}, RFC={rfc_strength}, Age={age_category}, Edu={education_level}")

    # 1. Get Source Job Data & Analysis
    source_job_data = db_handler.get_job_by_code(source_dot_code) # Assuming synchronous for now
    if not source_job_data:
        logger.error(f"TSA failed: Could not retrieve data for source DOT {source_dot_code}")
        return {"error": f"Could not retrieve data for source DOT {source_dot_code}"}

    # Perform analysis on the source job data
    # Note: get_job_analysis is imported from ve_logic
    source_analysis = get_job_analysis(source_job_data)
    if 'error' in source_analysis:
         logger.error(f"TSA failed: Error analyzing source DOT {source_dot_code}: {source_analysis['error']}")
         return {"error": f"Error analyzing source DOT {source_dot_code}: {source_analysis['error']}"}

    source_svp = source_analysis.get('skill_level', {}).get('svp', 0)
    source_skill_category = source_analysis.get('skill_level', {}).get('category', UNKNOWN_STRING)

    # 2. Check if PRW is skilled/semi-skilled
    # Compare against string value, or Enum value if config uses Enums
    # Ensure comparison is case-insensitive and handles variations if necessary
    is_prw_unskilled = source_skill_category.lower() == config.svp_to_skill_level.get(1, "unskilled").lower()
    if is_prw_unskilled:
         logger.info("TSA Not Applicable: PRW is Unskilled.")
         return {
             "result": "TSA Not Applicable",
             "reason": f"PRW ({source_dot_code}) is Unskilled (SVP {source_svp}). No skills to transfer.",
             "prw_details": source_analysis.get('skill_level')
         }

    # 3. **Placeholder:** Determine Skill Transferability
    # Extract skills from PRW
    source_skills = _extract_potential_skills(source_analysis)
    if not source_skills:
         # Error already logged in _extract_potential_skills
         return {"error": f"Could not extract potential skills from source DOT {source_dot_code}"}

    # Initialize transferability status and results
    skills_are_transferable = False # Overall status, True if *any* target is transferable
    transferability_reason = "No specific target DOTs provided for evaluation."
    target_job_evaluation_results = []

    # 4. Apply Grid Rules (Using the new function)
    # Note: Grid Rule application depends on the *overall* transferability status,
    # determined after checking specific targets (if any).
    # We will call this *after* the target evaluation loop.

    # 5. Evaluate transferability to potential target jobs (if provided)
    if target_dot_codes:
        logger.info(f"Evaluating transferability to specific targets: {target_dot_codes}")
        for target_code in target_dot_codes:
            target_job_data = db_handler.get_job_by_code(target_code)
            if not target_job_data:
                logger.warning(f"Could not find data for target DOT {target_code}. Skipping evaluation.")
                target_job_evaluation_results.append({
                    "target_dot": target_code,
                    "status": "Error",
                    "message": "Target DOT data not found."
                })
                continue

            target_analysis = get_job_analysis(target_job_data)
            if 'error' in target_analysis:
                logger.warning(f"Could not analyze target DOT {target_code}: {target_analysis['error']}. Skipping evaluation.")
                target_job_evaluation_results.append({
                    "target_dot": target_code,
                    "status": "Error",
                    "message": f"Target DOT analysis failed: {target_analysis['error']}"
                })
                continue

            # Evaluate transferability to this specific target
            evaluation_result = _evaluate_transferability(source_skills, target_analysis, rfc_strength)
            target_job_evaluation_results.append({
                "target_dot": target_code,
                "target_title": target_analysis.get('job_title', UNKNOWN_STRING),
                "evaluation": evaluation_result
            })

            # Update overall transferability status if this target is transferable
            if evaluation_result.get("transferable"):
                skills_are_transferable = True
                # Update overall reason (first success is enough for now)
                if transferability_reason == "No specific target DOTs provided for evaluation.":
                     transferability_reason = f"Skills potentially transferable to at least one target ({target_code})."

        # Refine overall reason if no targets were transferable after evaluation
        if not skills_are_transferable and target_dot_codes:
            transferability_reason = "Skills not transferable to any of the specified target DOTs based on criteria."

    else:
         logger.info("No specific target DOTs provided. General transferability assessment not implemented.")
         transferability_reason = "General transferability assessment requires further implementation (e.g., searching for potential jobs within RFC)."
         # skills_are_transferable remains False by default

    # --- Now apply Grid Rules using the determined transferability status --- #
    grid_result = apply_grid_rule(
        rfc_strength=rfc_strength,
        age_category=age_category,
        education_level=education_level,
        prw_skill_category=source_skill_category,
        skills_transferable=skills_are_transferable # Use determined value
    )
    grid_rule_id = grid_result.get("rule_id")
    grid_decision = grid_result.get("decision")
    grid_reason = grid_result.get("reason")

    # 6. Formulate Conclusion based on Grids and Transferability Assessment
    # If Grid Rules apply directly, the grid_decision is primary.
    # If not, the conclusion depends on the (placeholder) transferability assessment.
    if grid_decision not in ["Error", "Not Applicable", "Rule Not Applicable", None]:
        tsa_conclusion = f"Grid Rule {grid_rule_id} directs a finding of '{grid_decision}' based on the provided factors and determined skill transferability status ({skills_are_transferable})."
    else:
        # If grids don't apply, the decision hinges on whether skills transfer to *other work*
        if skills_are_transferable:
             tsa_conclusion = f"Grid Rules do not directly apply ({grid_reason}), but skills were found transferable to other occupations within RFC limits (e.g., {target_job_evaluation_results[0]['target_dot'] if target_job_evaluation_results and target_job_evaluation_results[0].get('evaluation',{}).get('transferable') else 'details in target analysis'}). Finding would likely be 'Not Disabled'."
        else:
             tsa_conclusion = f"Grid Rules do not directly apply ({grid_reason}), and skills were not found transferable to the specified target occupations (or no targets provided). Finding would likely be 'Disabled'."

    return {
        "status": "Analysis Complete (Based on Implemented Logic)",
        "grid_rule_application": {
            "matched_rule_id": grid_rule_id,
            "directed_decision": grid_decision,
            "reasoning": grid_reason or ("Rule applied successfully." if grid_rule_id else "No rule applied.")
        },
        "prw_details": {
            # Include extracted skills here for clarity
            "extracted_skills": source_skills,
             "dot": source_dot_code,
             "title": source_analysis.get('job_title'),
             **source_analysis.get('skill_level', {}) # Include SVP, category etc.
        },
        "claimant_factors": {"age": age_category, "rfc": rfc_strength, "education": education_level},
        "skill_transferability_analysis": {
            "overall_transferable_status": skills_are_transferable,
            "overall_reasoning": transferability_reason,
            "target_evaluations": target_job_evaluation_results
        },
        "overall_conclusion": tsa_conclusion,
        "notes": "Analysis based on implemented logic comparing exertion, SVP (max 2 level drop), exact Worker Function match, and WFld/MPSMS overlap. General transferability search (when no targets specified) is not implemented."
    }
# --- Add any other TSA-specific helper functions below --- 