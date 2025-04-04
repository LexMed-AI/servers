from typing import Dict, List, Optional, Union, Any
from config import (
    svp_map,
    worker_functions_map,
    ged_map,
    strength_map,
    freq_map,
    noise_map,
    aptitude_level_map,
    temperament_map
)

SECTION_SEPARATOR = "-" * 80
TABLE_PADDING = 2
MIN_COLUMN_WIDTH = 10
MAX_SVP_LEVEL = 9

def validate_job_data(job_data: Dict[str, Any]) -> bool:
    """Validate required fields in job data.
    
    Returns:
        bool: True if data is valid, False otherwise
    """
    required_fields = ['jobTitle', 'NCode', 'industryDesignation']
    return all(job_data.get(field) for field in required_fields)

def format_job_report(job_data: Dict[str, Any]) -> str:
    """Format job data into a markdown report."""
    
    # Start building the markdown report
    report = [
        f"# {job_data.get('jobTitle', 'N/A')}",
        f"## {job_data.get('dotCode', 'N/A')}",
        "\n---\n",
        "| Detail                 | Value                                                                 |",
        "| :--------------------- | :-------------------------------------------------------------------- |",
        f"| **Industry Designation** | `{job_data.get('industryDesignation', 'N/A')}` |",
        f"| **GOE Code**           | `{job_data.get('goeCode', 'N/A')}` |",
        "| **GOE Titles**         | " + f"`- {job_data.get('goe_title', 'N/A')}`<br>`- {job_data.get('GOE2', 'N/A')}`<br>`- {job_data.get('GOE3', 'N/A')}`" + " |",
        f"| **Alternate Titles**   | `{job_data.get('alternateTitles', 'N/A')}` |",
        f"| **SVP**                | **Level `{job_data.get('SVPNum', 'N/A')}`:** `{svp_map.get(job_data.get('SVPNum'), 'N/A')}` |",
        f"| **Strength**           | **`{job_data.get('Strength', 'S')}`:** `{strength_map.get(job_data.get('Strength', 'S'), 'N/A')}` |",
        "\n---\n",
        "## Definition\n",
        f"`{job_data.get('definition', 'N/A')}`\n",
        "\n---\n",
        "## Characteristics\n",
        "| Category        | Activity / Condition   | Frequency / Level                       |",
        "| :-------------- | :--------------------- | :-------------------------------------- |",
        "| **Postural**    | Climbing               | `" + format_frequency_level(job_data.get('ClimbingNum')) + "` |",
        "|                 | Balancing              | `" + format_frequency_level(job_data.get('BalancingNum')) + "` |",
        "|                 | Stooping               | `" + format_frequency_level(job_data.get('StoopingNum')) + "` |",
        "|                 | Kneeling               | `" + format_frequency_level(job_data.get('KneelingNum')) + "` |",
        "|                 | Crouching              | `" + format_frequency_level(job_data.get('CrouchingNum')) + "` |",
        "|                 | Crawling               | `" + format_frequency_level(job_data.get('CrawlingNum')) + "` |",
        "| **Manipulative**| Reaching               | `" + format_frequency_level(job_data.get('ReachingNum')) + "` |",
        "|                 | Handling               | `" + format_frequency_level(job_data.get('HandlingNum')) + "` |",
        "|                 | Fingering              | `" + format_frequency_level(job_data.get('FingeringNum')) + "` |",
        "| **Sensory**     | Feeling                | `" + format_frequency_level(job_data.get('FeelingNum')) + "` |",
        "|                 | Talking                | `" + format_frequency_level(job_data.get('TalkingNum')) + "` |",
        "|                 | Hearing                | `" + format_frequency_level(job_data.get('HearingNum')) + "` |",
        "|                 | Taste/Smell            | `" + format_frequency_level(job_data.get('TastingNum')) + "` |",
        "| **Visual**      | Near Acuity            | `" + format_frequency_level(job_data.get('NearAcuityNum')) + "` |",
        "|                 | Far Acuity             | `" + format_frequency_level(job_data.get('FarAcuityNum')) + "` |",
        "|                 | Depth Perc.            | `" + format_frequency_level(job_data.get('DepthNum')) + "` |",
        "|                 | Accom.                 | `" + format_frequency_level(job_data.get('AccommodationNum')) + "` |",
        "|                 | Color Vis.             | `" + format_frequency_level(job_data.get('ColorVisionNum')) + "` |",
        "|                 | Field of Vis.          | `" + format_frequency_level(job_data.get('FieldVisionNum')) + "` |",
        "| **Environmental** | Weather              | `" + format_frequency_level(job_data.get('WeatherNum')) + "` |",
        "|                 | Extreme Cold           | `" + format_frequency_level(job_data.get('ColdNum')) + "` |",
        "|                 | Extreme Heat           | `" + format_frequency_level(job_data.get('HeatNum')) + "` |",
        "|                 | Wet                    | `" + format_frequency_level(job_data.get('WetNum')) + "` |",
        f"|                 | Noise                  | `{job_data.get('NoiseNum', 1)}` - `{noise_map.get(job_data.get('NoiseNum', 1), 'N/A')}` |",
        "|                 | Vibration              | `" + format_frequency_level(job_data.get('VibrationNum')) + "` |",
        "|                 | Atmos. Cond.           | `" + format_frequency_level(job_data.get('AtmosphereNum')) + "` |",
        "|                 | Moving Mech.           | `" + format_frequency_level(job_data.get('MovingNum')) + "` |",
        "|                 | Elec. Shock            | `" + format_frequency_level(job_data.get('ElectricityNum')) + "` |",
        "|                 | Height                 | `" + format_frequency_level(job_data.get('HeightNum')) + "` |",
        "|                 | Radiation              | `" + format_frequency_level(job_data.get('RadiationNum')) + "` |",
        "|                 | Explosion              | `" + format_frequency_level(job_data.get('ExplosionNum')) + "` |",
        "|                 | Toxic Chem.            | `" + format_frequency_level(job_data.get('ToxicNum')) + "` |",
        "|                 | Other                  | `" + format_frequency_level(job_data.get('OtherNum')) + "` |",
        "\n---\n",
        "## General Educational Development",
        "*(Range: Lowest (1) to Highest (6))*\n",
        "| Area       | Level | Description                                     |",
        "| :--------- | :---- | :---------------------------------------------- |",
        f"| Reasoning  | `{job_data.get('GEDR', 'N/A')}` | `{format_ged_reasoning(job_data.get('GEDR'))}` |",
        f"| Math       | `{job_data.get('GEDM', 'N/A')}` | `{format_ged_math(job_data.get('GEDM'))}` |",
        f"| Language   | `{job_data.get('GEDL', 'N/A')}` | `{format_ged_language(job_data.get('GEDL'))}` |",
        "\n---\n",
        "## Worker Functions",
        "*(Range: Lowest (6-8) to Highest (0))*\n",
        "| Function | Level / Significance        | Description                                     |",
        "| :------- | :-------------------------- | :---------------------------------------------- |",
        f"| Data     | `{job_data.get('WFData', 'N/A')}` | `{format_worker_function_data(job_data.get('WFData'))}` |",
        f"| People   | `{job_data.get('WFPeople', 'N/A')}` | `{format_worker_function_people(job_data.get('WFPeople'))}` |",
        f"| Things   | `{job_data.get('WFThings', 'N/A')}` | `{format_worker_function_things(job_data.get('WFThings'))}` |",
        "\n---\n",
        "## Work Fields\n",
        "| Code | Description                            |",
        "| :--- | :------------------------------------- |",
        format_work_fields_description(job_data),
        "\n---\n",
        "## MPSMS Code\n",
        "| Code | Description                                     |",
        "| :--- | :---------------------------------------------- |",
        format_mpsms_description(job_data),
        "\n---\n",
        "## Aptitudes\n",
        "| Aptitude                      | Level | Description                                     |",
        "| :---------------------------- | :---- | :---------------------------------------------- |",
        format_aptitudes_table(job_data),
        "\n---\n",
        "## Temperaments\n",
        "| Code / Title                                     | Description                                     |",
        "| :----------------------------------------------- | :---------------------------------------------- |",
        format_temperaments_table(job_data),
        "\n---\n",
        "## Legend\n",
        "**Frequency:**",
        "- **Not Present:** Activity or condition does not exist.",
        "- **Occasionally:** Activity or condition exists up to 1/3 of the time.",
        "- **Frequently:** Activity or condition exists from 1/3 to 2/3 of the time.",
        "- **Constantly:** Activity or condition exists 2/3 or more of the time. *(Note: The OCR'd legend incorrectly says \"Not Present\" for Constant)*\n",
        "**Noise:**",
        "- **1:** Very Quiet",
        "- **2:** Quiet",
        "- **3:** Moderate",
        "- **4:** Loud",
        "- **5:** Very Loud"
    ]
    
    return "\n".join(report)

def format_frequency_level(value: Optional[int]) -> str:
    """Convert numeric frequency to descriptive text."""
    if value is None:
        return "N (Not Present)"
    return freq_map.get(value, "Unknown")

def format_frequency_description(num: int) -> str:
    """Format frequency level with description."""
    return freq_map.get(num, "Unknown frequency")

def format_ged_level(value: Optional[int]) -> Dict[str, str]:
    """Format GED level with description."""
    if value is None:
        return {"level": "1", "description": "Not specified"}
    level = str(min(max(value, 1), 6))
    return {
        "level": level,
        "description": ged_map[int(level)]["reasoning"]  # Using reasoning as default description
    }

def format_worker_functions(job_data: Dict[str, Any]) -> Dict[str, Dict[str, str]]:
    """Format worker functions with levels and descriptions."""
    return {
        "data": {
            "level": str(job_data.get("WFData", 8)),
            "description": worker_functions_map["data"].get(job_data.get("WFData", 8), "Unknown")
        },
        "people": {
            "level": str(job_data.get("WFPeople", 8)),
            "description": worker_functions_map["people"].get(job_data.get("WFPeople", 8), "Unknown")
        },
        "things": {
            "level": str(job_data.get("WFThings", 7)),
            "description": worker_functions_map["things"].get(job_data.get("WFThings", 7), "Unknown")
        }
    }

def format_aptitude_level(level: int) -> str:
    """Format aptitude level with description."""
    return aptitude_level_map.get(level, "Unknown aptitude level")

def format_aptitudes(job_data: Dict[str, Any]) -> str:
    """Format aptitudes with proper descriptions."""
    aptitudes = [
        ("General Learning Ability", job_data.get('AptGenLearn', 3)),
        ("Verbal Aptitude", job_data.get('AptVerbal', 3)),
        ("Numerical Aptitude", job_data.get('AptNumerical', 3)),
        ("Spatial Aptitude", job_data.get('AptSpacial', 3)),
        ("Form Perception", job_data.get('AptFormPer', 3)),
        ("Clerical Perception", job_data.get('AptClericalPer', 3)),
        ("Motor Coordination", job_data.get('AptMotor', 3)),
        ("Finger Dexterity", job_data.get('AptFingerDext', 3)),
        ("Manual Dexterity", job_data.get('AptManualDext', 3)),
        ("Eye-Hand-Foot Coordination", job_data.get('AptEyeHandCoord', 3)),
        ("Color Discrimination", job_data.get('AptColorDisc', 3))
    ]
    
    formatted = []
    for name, level in aptitudes:
        desc = format_aptitude_level(level)
        formatted.append(f"{name} (Level {level}): {desc}")
    
    return "\n".join(formatted)

def format_temperaments(job_data: Dict[str, Any]) -> str:
    """Format temperaments with proper descriptions."""
    temps = []
    for i in range(1, 6):  # Check Temp1 through Temp5
        temp = job_data.get(f'Temp{i}')
        if temp and temp in temperament_map:
            temps.append(f"{temp}: {temperament_map[temp]}")
    
    return "\n".join(temps) if temps else "No specific temperaments listed"

def format_physical_demands(job_data: Dict[str, Any]) -> str:
    demands = {
        'Climbing': format_frequency_level(job_data.get('ClimbingNum')),
        'Balancing': format_frequency_level(job_data.get('BalancingNum')),
        'Stooping': format_frequency_level(job_data.get('StoopingNum')),
        'Kneeling': format_frequency_level(job_data.get('KneelingNum')),
        'Crouching': format_frequency_level(job_data.get('CrouchingNum')),
        'Crawling': format_frequency_level(job_data.get('CrawlingNum'))
    }
    return "\n".join(f"{activity:<15}{level}" for activity, level in demands.items())

def format_manipulative_demands(job_data: Dict[str, Any]) -> str:
    demands = {
        'Reaching': format_frequency_level(job_data.get('ReachingNum')),
        'Handling': format_frequency_level(job_data.get('HandlingNum')),
        'Fingering': format_frequency_level(job_data.get('FingeringNum'))
    }
    return "\n".join(f"{activity:<15}{level}" for activity, level in demands.items())

def format_sensory_demands(job_data: Dict[str, Any]) -> str:
    demands = {
        'Feeling': format_frequency_level(job_data.get('FeelingNum')),
        'Talking': format_frequency_level(job_data.get('TalkingNum')),
        'Hearing': format_frequency_level(job_data.get('HearingNum')),
        'Taste/Smell': format_frequency_level(job_data.get('TastingNum'))
    }
    return "\n".join(f"{activity:<15}{level}" for activity, level in demands.items())

def format_visual_demands(job_data: Dict[str, Any]) -> str:
    demands = {
        'Near Acuity': format_frequency_level(job_data.get('NearAcuityNum')),
        'Far Acuity': format_frequency_level(job_data.get('FarAcuityNum')),
        'Depth Perc.': format_frequency_level(job_data.get('DepthNum')),
        'Accom.': format_frequency_level(job_data.get('AccommodationNum')),
        'Color Vis.': format_frequency_level(job_data.get('ColorVisionNum')),
        'Field of Vis.': format_frequency_level(job_data.get('FieldVisionNum'))
    }
    return "\n".join(f"{activity:<15}{level}" for activity, level in demands.items())

def format_environmental_conditions(job_data: Dict[str, Any]) -> str:
    """Format environmental conditions."""
    conditions = [
        ("Weather", job_data.get('WeatherNum', 1)),
        ("Cold", job_data.get('ColdNum', 1)),
        ("Heat", job_data.get('HeatNum', 1)),
        ("Wet/Humid", job_data.get('WetNum', 1)),
        ("Noise", job_data.get('NoiseNum', 1)),
        ("Vibration", job_data.get('VibrationNum', 1)),
        ("Atmospheric Conditions", job_data.get('AtmosphereNum', 1)),
        ("Moving Mechanical Parts", job_data.get('MovingNum', 1)),
        ("Electric Shock", job_data.get('ElectricityNum', 1)),
        ("High Places", job_data.get('HeightNum', 1)),
        ("Radiation", job_data.get('RadiationNum', 1)),
        ("Explosives", job_data.get('ExplosionNum', 1)),
        ("Toxic/Caustic Chemicals", job_data.get('ToxicNum', 1)),
        ("Other Environmental Conditions", job_data.get('OtherNum', 1))
    ]
    
    formatted = []
    for condition, level in conditions:
        freq = format_frequency_level(level)
        formatted.append(f"{condition}: {freq}")
    
    return "\n".join(formatted)

def format_ged_reasoning(level: Optional[int]) -> str:
    """Format GED reasoning level with description."""
    if level is None:
        return "Reasoning level not specified"
    return ged_map.get(level, {}).get("reasoning", f"Unknown reasoning level: {level}")

def format_ged_math(level: Optional[int]) -> str:
    """Format GED math level with description."""
    if level is None:
        return "Math level not specified"
    return ged_map.get(level, {}).get("math", f"Unknown math level: {level}")

def format_ged_language(level: Optional[int]) -> str:
    """Format GED language level with description."""
    if level is None:
        return "Language level not specified"
    return ged_map.get(level, {}).get("language", f"Unknown language level: {level}")

def format_worker_function_data(level: Optional[int]) -> str:
    """Format worker function data level with description."""
    if level is None:
        return "Data function level not specified"
    return worker_functions_map.get("data", {}).get(level, f"Unknown data function level: {level}")

def format_worker_function_people(level: Optional[int]) -> str:
    """Format worker function people level with description."""
    if level is None:
        return "People function level not specified"
    return worker_functions_map.get("people", {}).get(level, f"Unknown people function level: {level}")

def format_worker_function_things(level: Optional[int]) -> str:
    """Format worker function things level with description."""
    if level is None:
        return "Things function level not specified"
    return worker_functions_map.get("things", {}).get(level, f"Unknown things function level: {level}")

def format_work_fields_description(job_data: Dict[str, Any]) -> str:
    """Format work fields with descriptions."""
    fields = []
    
    # Primary work field
    if 'WField1' in job_data and job_data['WField1']:
        fields.append(f"Primary: {job_data['WField1']}")
        if 'WField1Short' in job_data and job_data['WField1Short']:
            fields.append(f"Description: {job_data['WField1Short']}")
    
    # Secondary work field
    if 'WField2' in job_data and job_data['WField2']:
        fields.append(f"\nSecondary: {job_data['WField2']}")
        if 'WField2Short' in job_data and job_data['WField2Short']:
            fields.append(f"Description: {job_data['WField2Short']}")
    
    # Tertiary work field
    if 'WField3' in job_data and job_data['WField3']:
        fields.append(f"\nTertiary: {job_data['WField3']}")
        if 'WField3Short' in job_data and job_data['WField3Short']:
            fields.append(f"Description: {job_data['WField3Short']}")
    
    return "\n".join(fields) if fields else "No work fields specified"

def format_strength(job_data: Dict[str, Any]) -> str:
    """Format strength requirement with proper description."""
    strength = job_data.get('Strength', 'S')
    return strength_map.get(strength, "Unknown strength requirement")

def format_climbing_balancing(job_data: Dict[str, Any]) -> str:
    """Format climbing and balancing requirements."""
    climbing = format_frequency_level(job_data.get('ClimbingNum', 1))
    balancing = format_frequency_level(job_data.get('BalancingNum', 1))
    return f"Climbing: {climbing}\nBalancing: {balancing}"

def format_stooping_kneeling(job_data: Dict[str, Any]) -> str:
    """Format stooping, kneeling, crouching, and crawling requirements."""
    stooping = format_frequency_level(job_data.get('StoopingNum', 1))
    kneeling = format_frequency_level(job_data.get('KneelingNum', 1))
    crouching = format_frequency_level(job_data.get('CrouchingNum', 1))
    crawling = format_frequency_level(job_data.get('CrawlingNum', 1))
    return f"Stooping: {stooping}\nKneeling: {kneeling}\nCrouching: {crouching}\nCrawling: {crawling}"

def format_reaching_handling(job_data: Dict[str, Any]) -> str:
    """Format reaching, handling, fingering, and feeling requirements."""
    reaching = format_frequency_level(job_data.get('ReachingNum', 1))
    handling = format_frequency_level(job_data.get('HandlingNum', 1))
    fingering = format_frequency_level(job_data.get('FingeringNum', 1))
    feeling = format_frequency_level(job_data.get('FeelingNum', 1))
    return f"Reaching: {reaching}\nHandling: {handling}\nFingering: {fingering}\nFeeling: {feeling}"

def format_talking_hearing(job_data: Dict[str, Any]) -> str:
    """Format talking, hearing, and tasting/smelling requirements."""
    talking = format_frequency_level(job_data.get('TalkingNum', 1))
    hearing = format_frequency_level(job_data.get('HearingNum', 1))
    tasting = format_frequency_level(job_data.get('TastingNum', 1))
    return f"Talking: {talking}\nHearing: {hearing}\nTasting/Smelling: {tasting}"

def format_seeing(job_data: Dict[str, Any]) -> str:
    """Format seeing requirements."""
    near_acuity = format_frequency_level(job_data.get('NearAcuityNum', 1))
    far_acuity = format_frequency_level(job_data.get('FarAcuityNum', 1))
    depth = format_frequency_level(job_data.get('DepthNum', 1))
    accommodation = format_frequency_level(job_data.get('AccommodationNum', 1))
    color_vision = format_frequency_level(job_data.get('ColorVisionNum', 1))
    field_vision = format_frequency_level(job_data.get('FieldVisionNum', 1))
    return (f"Near Acuity: {near_acuity}\nFar Acuity: {far_acuity}\n"
            f"Depth Perception: {depth}\nAccommodation: {accommodation}\n"
            f"Color Vision: {color_vision}\nField of Vision: {field_vision}")

def format_mpsms_description(job_data: Dict[str, Any]) -> str:
    """Format MPSMS codes with descriptions."""
    codes = []
    
    # Primary MPSMS code
    if 'MPSMS1' in job_data and job_data['MPSMS1']:
        codes.append(f"Primary: {job_data['MPSMS1']}")
        if 'MPSMS1Short' in job_data and job_data['MPSMS1Short']:
            codes.append(f"Description: {job_data['MPSMS1Short']}")
    
    # Secondary MPSMS code
    if 'MPSMS2' in job_data and job_data['MPSMS2']:
        codes.append(f"\nSecondary: {job_data['MPSMS2']}")
        if 'MPSMS2Short' in job_data and job_data['MPSMS2Short']:
            codes.append(f"Description: {job_data['MPSMS2Short']}")
    
    # Tertiary MPSMS code
    if 'MPSMS3' in job_data and job_data['MPSMS3']:
        codes.append(f"\nTertiary: {job_data['MPSMS3']}")
        if 'MPSMS3Short' in job_data and job_data['MPSMS3Short']:
            codes.append(f"Description: {job_data['MPSMS3Short']}")
    
    return "\n".join(codes) if codes else "No MPSMS codes specified"

def format_aptitudes_table(job_data: Dict[str, Any]) -> str:
    """Format aptitudes in table format."""
    aptitudes = [
        ("General Learning Ability", 'AptGenLearn'),
        ("Verbal Aptitude", 'AptVerbal'),
        ("Numerical Aptitude", 'AptNumerical'),
        ("Spatial Aptitude", 'AptSpacial'),
        ("Form Perception", 'AptFormPer'),
        ("Clerical Perception", 'AptClericalPer'),
        ("Motor Coordination", 'AptMotor'),
        ("Finger Dexterity", 'AptFingerDext'),
        ("Manual Dexterity", 'AptManualDext'),
        ("Eye-Hand-Foot Coordination", 'AptEyeHandCoord'),
        ("Color Discrimination", 'AptColorDisc')
    ]
    
    rows = []
    for name, key in aptitudes:
        level = job_data.get(key, 3)
        desc = format_aptitude_level(level)
        rows.append(f"| {name:<28} | `{level}` | `{desc}` |")
    
    return "\n".join(rows)

def format_temperaments_table(job_data: Dict[str, Any]) -> str:
    """Format temperaments in table format."""
    rows = []
    for i in range(1, 6):
        temp_code = job_data.get(f'Temp{i}')
        if temp_code and temp_code in temperament_map:
            desc = temperament_map[temp_code]
            rows.append(f"| **`{temp_code}`** | `{desc}` |")
    
    return "\n".join(rows) if rows else "| N/A | No specific temperaments listed |" 