from typing import Dict, List, Optional
import logging
from datetime import datetime
import sqlite3
from contextlib import closing
from pathlib import Path

logger = logging.getLogger('mcp_ve_audit')

VE_AUDIT_PROMPT_TEMPLATE = """
Welcome to the Vocational Expert Audit tool! I see you've selected the job title/DOT code: {job_title}. Let's begin our analysis! 📊

<vocational_assessment>
1. Job Information:
   - DOT Code: {dot_code}
   - Title: {job_title}
   - Industry: {industry}

2. Physical Demands Profile:
   - Strength Level: {strength}
   - Key Physical Activities: {physical_demands}
   - Environmental Conditions: {environmental}

3. Skill Requirements:
   - SVP Level: {svp}
   - GED Levels:
     * Reasoning: {ged_r}
     * Math: {ged_m}
     * Language: {ged_l}

4. Worker Functions:
   - Data: {wf_data}
   - People: {wf_people}
   - Things: {wf_things}

5. Vocational Considerations:
   - Transferable Skills Analysis
   - Job Obsolescence Check
   - Alternative Occupations
</vocational_assessment>

Please select an area for detailed analysis:
1. Physical Demands Analysis
2. Skills and Aptitudes Assessment
3. Job Classification Analysis
4. Environmental Conditions Impact
"""

def format_ve_report(job_data: Dict) -> str:
    """Format job data into a VE-friendly report format"""
    physical_demands = []
    if job_data.get('ClimbingNum') > 1: physical_demands.append("Climbing")
    if job_data.get('BalancingNum') > 1: physical_demands.append("Balancing")
    if job_data.get('StoopingNum') > 1: physical_demands.append("Stooping")
    if job_data.get('KneelingNum') > 1: physical_demands.append("Kneeling")
    if job_data.get('CrouchingNum') > 1: physical_demands.append("Crouching")
    if job_data.get('CrawlingNum') > 1: physical_demands.append("Crawling")
    if job_data.get('ReachingNum') > 1: physical_demands.append("Reaching")
    if job_data.get('HandlingNum') > 1: physical_demands.append("Handling")
    if job_data.get('FingeringNum') > 1: physical_demands.append("Fingering")
    if job_data.get('FeelingNum') > 1: physical_demands.append("Feeling")
    if job_data.get('TalkingNum') > 1: physical_demands.append("Talking")
    if job_data.get('HearingNum') > 1: physical_demands.append("Hearing")
    if job_data.get('TastingNum') > 1: physical_demands.append("Tasting")
    if job_data.get('NearAcuityNum') > 1: physical_demands.append("Near Visual Acuity")
    if job_data.get('FarAcuityNum') > 1: physical_demands.append("Far Visual Acuity")
    if job_data.get('DepthNum') > 1: physical_demands.append("Depth Perception")
    if job_data.get('AccommodationNum') > 1: physical_demands.append("Visual Accommodation")
    if job_data.get('ColorVisionNum') > 1: physical_demands.append("Color Vision")
    if job_data.get('FieldVisionNum') > 1: physical_demands.append("Field of Vision")

    # Environmental Conditions
    environmental_conditions = []
    if job_data.get('WeatherNum') > 1: environmental_conditions.append("Weather")
    if job_data.get('ColdNum') > 1: environmental_conditions.append("Cold")
    if job_data.get('HeatNum') > 1: environmental_conditions.append("Heat")
    if job_data.get('WetNum') > 1: environmental_conditions.append("Wet")
    if job_data.get('NoiseNum') > 1: environmental_conditions.append("Noise")
    if job_data.get('VibrationNum') > 1: environmental_conditions.append("Vibration")
    if job_data.get('AtmosphereNum') > 1: environmental_conditions.append("Atmospheric Conditions")
    if job_data.get('MovingNum') > 1: environmental_conditions.append("Moving Mechanical Parts")
    if job_data.get('ElectricityNum') > 1: environmental_conditions.append("Electrical Shock")
    if job_data.get('HeightNum') > 1: environmental_conditions.append("High Places")
    if job_data.get('RadiationNum') > 1: environmental_conditions.append("Radiation")
    if job_data.get('ExplosionNum') > 1: environmental_conditions.append("Explosives")
    if job_data.get('ToxicNum') > 1: environmental_conditions.append("Toxic/Caustic Chemicals")

    # Skill Requirements
    skill_requirements = []
    if job_data.get('SVPNum') > 1: skill_requirements.append("SVP")
    if job_data.get('GEDR') > 1: skill_requirements.append("Reasoning")
    if job_data.get('GEDM') > 1: skill_requirements.append("Math")
    if job_data.get('GEDL') > 1: skill_requirements.append("Language")

    # Worker Functions
    worker_functions = []
    if job_data.get('WFData') > 1: worker_functions.append("Data")
    if job_data.get('WFPeople') > 1: worker_functions.append("People")
    if job_data.get('WFThings') > 1: worker_functions.append("Things")

    # Vocational Considerations
    vocational_considerations = []
    if job_data.get('TransferableSkills') > 1: vocational_considerations.append("Transferable Skills")
    if job_data.get('JobObsolescence') > 1: vocational_considerations.append("Job Obsolescence")
    if job_data.get('AlternativeOccupations') > 1: vocational_considerations.append("Alternative Occupations")
    


    return VE_AUDIT_PROMPT_TEMPLATE.format(
        job_title=job_data.get('Title', 'Unknown'),
        dot_code=job_data.get('Code', 'Unknown'),
        industry=job_data.get('Industry', 'Unknown'),
        strength=job_data.get('Strength', 'Unknown'),
        physical_demands=", ".join(physical_demands),
        environmental=", ".join(environmental_conditions),
        svp=job_data.get('SVPNum', 'Unknown'),
        ged_r=job_data.get('GEDR', 'Unknown'),
        ged_m=job_data.get('GEDM', 'Unknown'),
        ged_l=job_data.get('GEDL', 'Unknown'),
        wf_data=job_data.get('WFData', 'Unknown'),
        wf_people=job_data.get('WFPeople', 'Unknown'),
        wf_things=job_data.get('WFThings', 'Unknown')
    )

def analyze_transferable_skills(db_path: str, source_dot: str, target_dots: list[str] = None, 
                               residual_capacity: str = "SEDENTARY", age: str = "ADVANCED AGE") -> dict:
    """
    Analyzes transferable skills between DOT occupations following SSA guidelines and SkillTRAN methodology.
    
    Args:
        db_path: Path to SQLite database
        source_dot: Source DOT code for the claimant's past relevant work
        target_dots: Optional list of specific DOT codes to evaluate for transferability
                     If None, will search for potential transferable occupations
        residual_capacity: Residual functional capacity (RFC) - default "SEDENTARY"
        age: Age category per SSA guidelines - default "ADVANCED AGE"
    
    Returns:
        Dictionary containing transferability analysis
    """
    # Define SVP thresholds based on SSA policy
    svp_thresholds = {
        "UNSKILLED": [1, 2],  # Not transferable by definition
        "SEMI_SKILLED": [3, 4],
        "SKILLED": [5, 6, 7, 8, 9]
    }
    
    # Define mapping for RFC levels to strength ratings
    rfc_to_strength = {
        "SEDENTARY": ["Sedentary"],
        "LIGHT": ["Sedentary", "Light"],
        "MEDIUM": ["Sedentary", "Light", "Medium"],
        "HEAVY": ["Sedentary", "Light", "Medium", "Heavy"],
        "VERY HEAVY": ["Sedentary", "Light", "Medium", "Heavy", "Very Heavy"]
    }
    
    # Age-related transferability rules per SSA
    age_rules = {
        "YOUNGER": {"requires_little_adjustment": False},  # Under 50
        "CLOSELY APPROACHING ADVANCED AGE": {"requires_little_adjustment": True},  # 50-54
        "ADVANCED AGE": {"requires_little_adjustment": True},  # 55+
        "CLOSELY APPROACHING RETIREMENT AGE": {"requires_little_adjustment": True}  # 60+
    }
    
    analysis = {
        "source_job": None,
        "skill_level": None,
        "key_work_fields": [],
        "key_mpsms_codes": [],
        "transferable_occupations": [],
        "transferability_factors": {
            "age_category": age,
            "requires_little_adjustment": age_rules.get(age, {}).get("requires_little_adjustment", False),
            "rfc": residual_capacity
        },
        "analysis_summary": ""
    }
    
    try:
        with closing(sqlite3.connect(db_path)) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Clean the DOT code format
            source_dot_clean = source_dot.replace(".", "").replace("-", "")
            
            # Get source job data
            cursor.execute("""
                SELECT 
                    Title, CompleteTitle, NCode, Code, SVPNum, Strength, 
                    WField1, WField2, WField3, MPSMS1, MPSMS2, MPSMS3,
                    WFData, WFPeople, WFThings, GEDR, GEDM, GEDL,
                    AptGenLearn, AptVerbal, AptNumerical, AptSpacial, AptFormPer, 
                    AptClericalPer, AptMotor, AptFingerDext, AptManualDext
                FROM DOT
                WHERE Code = ? OR NCode = ?
            """, (source_dot_clean, source_dot_clean))
            
            source_job = cursor.fetchone()
            
            if not source_job:
                return {"error": f"Source job with DOT code {source_dot} not found"}
            
            source_job_dict = dict(source_job)
            analysis["source_job"] = {
                "title": source_job_dict["Title"],
                "dot_code": source_job_dict["Code"],
                "svp": source_job_dict["SVPNum"],
                "strength": source_job_dict["Strength"],
                "ged_reasoning": source_job_dict["GEDR"],
                "ged_math": source_job_dict["GEDM"],
                "ged_language": source_job_dict["GEDL"]
            }
            
            # Determine skill level
            svp = source_job_dict["SVPNum"]
            if svp in svp_thresholds["UNSKILLED"]:
                analysis["skill_level"] = "UNSKILLED"
                analysis["analysis_summary"] = "The source occupation is UNSKILLED (SVP 1-2). Per SSA guidelines, unskilled occupations do not have transferable skills."
                return analysis
            elif svp in svp_thresholds["SEMI_SKILLED"]:
                analysis["skill_level"] = "SEMI-SKILLED"
            else:
                analysis["skill_level"] = "SKILLED"
            
            # Extract Work Fields and MPSMS codes
            work_fields = [source_job_dict[f"WField{i}"] for i in range(1, 4) if source_job_dict.get(f"WField{i}")]
            mpsms_codes = [source_job_dict[f"MPSMS{i}"] for i in range(1, 4) if source_job_dict.get(f"MPSMS{i}")]
            
            analysis["key_work_fields"] = work_fields
            analysis["key_mpsms_codes"] = mpsms_codes
            
            # Get Work Field and MPSMS descriptions for report
            work_field_desc = []
            for wf in work_fields:
                cursor.execute("SELECT Description FROM WorkFields WHERE Code = ?", (wf,))
                result = cursor.fetchone()
                if result:
                    work_field_desc.append({"code": wf, "description": result["Description"]})
            
            mpsms_desc = []
            for mp in mpsms_codes:
                cursor.execute("SELECT Description FROM MPSMS WHERE Code = ?", (mp,))
                result = cursor.fetchone()
                if result:
                    mpsms_desc.append({"code": mp, "description": result["Description"]})
            
            analysis["work_field_descriptions"] = work_field_desc
            analysis["mpsms_descriptions"] = mpsms_desc
            
            # Define search criteria for transferable occupations
            allowed_strength_levels = rfc_to_strength[residual_capacity]
            
            # If specific target DOTs were provided, analyze just those
            if target_dots and len(target_dots) > 0:
                target_dot_list = "','".join([d.replace(".", "").replace("-", "") for d in target_dots])
                target_query = f"""
                    SELECT 
                        Title, CompleteTitle, NCode, Code, SVPNum, Strength, 
                        WField1, WField2, WField3, MPSMS1, MPSMS2, MPSMS3,
                        WFData, WFPeople, WFThings, GEDR, GEDM, GEDL
                    FROM DOT
                    WHERE (Code IN ('{target_dot_list}') OR NCode IN ('{target_dot_list}'))
                    AND SVPNum >= 3
                    AND Strength IN ('{"','".join(allowed_strength_levels)}')
                """
            else:
                # Search for potential transferable occupations
                # First priority: match at least one Work Field and one MPSMS
                work_fields_list = "','".join(work_fields)
                mpsms_list = "','".join(mpsms_codes)
                
                target_query = f"""
                    SELECT 
                        Title, CompleteTitle, NCode, Code, SVPNum, Strength, 
                        WField1, WField2, WField3, MPSMS1, MPSMS2, MPSMS3,
                        WFData, WFPeople, WFThings, GEDR, GEDM, GEDL
                    FROM DOT
                    WHERE (
                        (WField1 IN ('{work_fields_list}') OR WField2 IN ('{work_fields_list}') OR WField3 IN ('{work_fields_list}'))
                        AND 
                        (MPSMS1 IN ('{mpsms_list}') OR MPSMS2 IN ('{mpsms_list}') OR MPSMS3 IN ('{mpsms_list}'))
                    )
                    AND SVPNum >= 3
                    AND SVPNum <= {svp + 1}
                    AND GEDR <= {source_job_dict["GEDR"]}
                    AND GEDM <= {source_job_dict["GEDM"]}
                    AND GEDL <= {source_job_dict["GEDL"]}
                    AND Strength IN ('{"','".join(allowed_strength_levels)}')
                    LIMIT 50
                """
            
            cursor.execute(target_query)
            potential_transfers = cursor.fetchall()
            
            # Analyze each potential transfer
            for job in potential_transfers:
                job_dict = dict(job)
                
                # Skip the source job itself
                if job_dict["Code"] == source_job_dict["Code"]:
                    continue
                
                # Matching Work Fields
                job_work_fields = [job_dict[f"WField{i}"] for i in range(1, 4) if job_dict.get(f"WField{i}")]
                job_mpsms = [job_dict[f"MPSMS{i}"] for i in range(1, 4) if job_dict.get(f"MPSMS{i}")]
                
                matching_work_fields = [wf for wf in job_work_fields if wf in work_fields]
                matching_mpsms = [mp for mp in job_mpsms if mp in mpsms_codes]
                
                # Calculate skill transferability score (0-100)
                # Weight factors per SkillTRAN method
                wf_match_score = len(matching_work_fields) / max(len(work_fields), 1) * 60
                mpsms_match_score = len(matching_mpsms) / max(len(mpsms_codes), 1) * 40
                transfer_score = wf_match_score + mpsms_match_score
                
                # For advanced age, transferability requires little adjustment
                requires_adjustment = not (
                    # Same work fields or closely related
                    len(matching_work_fields) > 0 and
                    # Similar tools and machines (implied by matching work fields)
                    # Similar or same raw materials/products/processes (MPSMS)
                    len(matching_mpsms) > 0 and
                    # Semi-skilled or skilled
                    job_dict["SVPNum"] >= 3 and
                    # No higher skill level required (based on SVP)
                    job_dict["SVPNum"] <= svp
                )
                
                # For older workers, requires little adjustment rule applies
                if age_rules.get(age, {}).get("requires_little_adjustment", False):
                    if requires_adjustment:
                        continue  # Skip this job if it requires significant adjustment
                
                transferable_job = {
                    "title": job_dict["Title"],
                    "dot_code": job_dict["Code"],
                    "svp": job_dict["SVPNum"],
                    "strength": job_dict["Strength"],
                    "ged_reasoning": job_dict["GEDR"],
                    "ged_math": job_dict["GEDM"],
                    "ged_language": job_dict["GEDL"],
                    "matching_work_fields": matching_work_fields,
                    "matching_mpsms": matching_mpsms,
                    "transfer_score": round(transfer_score, 2),
                    "requires_adjustment": requires_adjustment
                }
                
                analysis["transferable_occupations"].append(transferable_job)
            
            # Sort by transfer score descending
            analysis["transferable_occupations"].sort(key=lambda x: x["transfer_score"], reverse=True)
            
            # Generate analysis summary
            skill_level = analysis["skill_level"]
            toc = len(analysis["transferable_occupations"])
            
            if toc == 0:
                analysis["analysis_summary"] = f"No transferable occupations found for this {skill_level.lower()} occupation at a {residual_capacity.lower()} RFC level for a person of {age.lower()}."
            else:
                analysis["analysis_summary"] = f"Found {toc} transferable occupations for this {skill_level.lower()} occupation at a {residual_capacity.lower()} RFC level for a person of {age.lower()}."
                
            # Add SSA regulatory citations
            if age in ["ADVANCED AGE", "CLOSELY APPROACHING RETIREMENT AGE"]:
                analysis["regulatory_citations"] = ["Medical-Vocational Guidelines (Grid Rules)", "SSR 82-41", "20 CFR 404.1568", "20 CFR 416.968"]
            
        return analysis
    
    except sqlite3.Error as e:
        logger.error(f"Database error in transferable skills analysis: {e}")
        return {"error": f"Database error: {str(e)}"}
    except Exception as e:
        logger.error(f"Error in transferable skills analysis: {e}")
        return {"error": f"Error: {str(e)}"}

def check_obsolescence(job_data: Dict) -> Dict:
    """Check if a job might be obsolete based on various factors"""
    factors = []
    
    # Check last update
    if job_data.get('LastUpdate', '1991') < '1991':
        factors.append("Position not updated since 1991 DOT revision")
    
    # Check technology-related terms
    tech_terms = ['computer', 'technology', 'digital', 'automated']
    if any(term in job_data.get('Title', '').lower() for term in tech_terms):
        factors.append("Technology-dependent position may be outdated")
    
    return {
        'is_obsolete': len(factors) > 0,
        'factors': factors
    } 