import csv
from typing import Dict, List, Optional, Union

# Value mappings
svp_map = {
    1: "Short demonstration only (short demonstration - 30 days)",
    2: "Anything beyond short demonstration up to and including 30 days (30 days - 3 months)",
    3: "Over 30 days up to and including 3 months (3-6 months)",
    4: "Over 3 months up to and including 6 months (6 months - 1 year)",
    5: "Over 6 months up to and including 1 year (1-2 years)",
    6: "Over 1 year up to and including 2 years (2-4 years)",
    7: "Over 2 years up to and including 4 years (4-10 years)",
    8: "Over 4 years up to and including 10 years (over 10 years)",
    9: "Over 10 years"
}

worker_functions_map = {
    "Data": {
        0: "Synthesizing",
        1: "Coordinating",
        2: "Analyzing",
        3: "Compiling",
        4: "Computing",
        5: "Copying",
        6: "Comparing",
        7: "Serving",
        8: "Taking Instructions-Helping"
    },
    "People": {
        0: "Mentoring",
        1: "Negotiating",
        2: "Instructing",
        3: "Supervising",
        4: "Diverting",
        5: "Persuading",
        6: "Speaking-Signaling",
        7: "Serving",
        8: "Taking Instructions-Helping"
    },
    "Things": {
        0: "Setting Up",
        1: "Precision Working",
        2: "Operating-Controlling",
        3: "Driving-Operating",
        4: "Manipulating",
        5: "Tending",
        6: "Feeding-Offbearing",
        7: "Handling",
        8: "No significant relationship"
    }
}

ged_map = {
    "Reasoning": {
        1: "Apply commonsense understanding to carry out simple one- or two-step instructions",
        2: "Apply commonsense understanding to carry out detailed but uninvolved written or oral instructions",
        3: "Apply commonsense understanding to carry out instructions furnished in written, oral, or diagrammatic form",
        4: "Apply principles of rational systems to solve practical problems",
        5: "Apply principles of logical or scientific thinking to define problems, collect data, establish facts, and draw valid conclusions",
        6: "Apply principles of logical or scientific thinking to a wide range of intellectual and practical problems"
    },
    "Math": {
        1: "Add and subtract two digit numbers",
        2: "Add, subtract, multiply and divide all units of measure",
        3: "Compute discount, interest, profit and loss; commission, markup and selling price",
        4: "Perform ordinary arithmetic, algebraic and geometric procedures in standard, practical applications",
        5: "Deal with system of real numbers; linear, quadratic, rational, exponential; logarithmic, angle and circular functions",
        6: "Work with exponents and logarithms, linear equations, quadratic equations, mathematical induction and binomial theorem"
    },
    "Language": {
        1: "Recognize meaning of 2,500 (two- or three-syllable) words",
        2: "Passive vocabulary of 5,000-6,000 words",
        3: "Read novels, magazines, manuals, encyclopedias, and safety rules",
        4: "Write compound and complex sentences, using proper punctuation",
        5: "Write business letters, summaries, and reports, using prescribed format and conforming to rules of punctuation",
        6: "Write novels, plays, editorials, journals, speeches, manuals, critiques, poetry, and songs"
    }
}

strength_map = {
    "S": "Sedentary Work - Exerting up to 10 pounds of force occasionally",
    "L": "Light Work - Exerting up to 20 pounds of force occasionally",
    "M": "Medium Work - Exerting 20 to 50 pounds of force occasionally",
    "H": "Heavy Work - Exerting 50 to 100 pounds of force occasionally",
    "V": "Very Heavy Work - Exerting over 100 pounds of force occasionally"
}

aptitude_map = {
    "G": "General Learning Ability",
    "V": "Verbal Aptitude",
    "N": "Numerical Aptitude",
    "S": "Spatial Aptitude",
    "P": "Form Perception",
    "Q": "Clerical Perception",
    "K": "Motor Coordination",
    "F": "Finger Dexterity",
    "M": "Manual Dexterity",
    "E": "Eye-Hand-Foot Coordination",
    "C": "Color Discrimination"
}

aptitude_level_map = {
    1: "The top 10% of the population (Superior)",
    2: "The highest third exclusive of the top 10% (Above Average)",
    3: "The middle third of the population (Average)",
    4: "The lowest third exclusive of the bottom 10% (Below Average)",
    5: "The lowest 10% of the population (Low)"
}

frequency_map = {
    1: "Not Present",
    2: "Occasionally",
    3: "Frequently",
    4: "Constantly"
}

def get_frequency_text(value: Optional[Union[int, str]]) -> str:
    if value is None:
        return "Unknown"
    try:
        freq = int(value)
        return frequency_map.get(freq, f"Unknown (Value: {freq})")
    except (ValueError, TypeError):
        return f"Unknown (Value: {value})"

def create_table(headers: List[str], rows: List[List[str]]) -> str:
    if not rows:
        return ""
    
    # Calculate column widths
    col_widths = [max(len(str(x)) for x in col) for col in zip(headers, *rows)]
    
    # Create the header
    header = " | ".join(f"{h:<{w}}" for h, w in zip(headers, col_widths))
    separator = "-" * len(header)
    
    # Create the rows
    table_rows = [
        " | ".join(f"{cell:<{w}}" for cell, w in zip(row, col_widths))
        for row in rows
    ]
    
    return f"{header}\n{separator}\n" + "\n".join(table_rows)

def format_job_report(job_data: Dict) -> str:
    sections = []
    
    # Overview Section
    dot_code = job_data.get('Code', 'Unknown')
    if dot_code != 'Unknown':
        try:
            # Format as XXX.XXX-XXX if not already formatted
            if '.' not in dot_code and '-' not in dot_code:
                dot_code = f"{dot_code[:3]}.{dot_code[3:6]}-{dot_code[6:]}"
        except:
            pass
    
    sections.append("Overview")
    sections.append("-" * len("Overview"))
    sections.append(f"DOT Code: {dot_code}")
    sections.append(f"Industry: {job_data.get('Industry', 'Unknown')}")
    sections.append(f"Title: {job_data.get('Title', 'Unknown')}")
    
    alt_titles = job_data.get('AltTitles', '')
    if alt_titles:
        sections.append("\nAlternate Titles:")
        for title in alt_titles.split(';'):
            sections.append(f"- {title.strip()}")
    
    # Definition Section
    if job_data.get('Definitions'):
        sections.append("\nDefinition")
        sections.append("-" * len("Definition"))
        sections.append(job_data.get('Definitions', 'Unknown'))
    
    # Physical Demands
    sections.append("\nPhysical Demands")
    sections.append("-" * len("Physical Demands"))
    sections.append(f"Strength: {strength_map.get(job_data.get('Strength'), 'Unknown')}")
    
    # Postural Activities
    postural = []
    for activity in ['Climbing', 'Balancing', 'Stooping', 'Kneeling', 'Crouching', 'Crawling']:
        value = job_data.get(f"{activity}Num")
        if value:
            freq = get_frequency_text(value)
            postural.append([activity, freq])
    
    if postural:
        sections.append("\nPostural Activities")
        sections.append(create_table(["Activity", "Frequency"], postural))
    
    # Manipulative Activities
    manipulative = []
    for activity in ['Reaching', 'Handling', 'Fingering', 'Feeling']:
        value = job_data.get(f"{activity}Num")
        if value:
            freq = get_frequency_text(value)
            manipulative.append([activity, freq])
    
    if manipulative:
        sections.append("\nManipulative Activities")
        sections.append(create_table(["Activity", "Frequency"], manipulative))
    
    # Sensory Activities
    sensory = []
    for activity in ['Talking', 'Hearing', 'Tasting']:
        value = job_data.get(f"{activity}Num")
        if value:
            freq = get_frequency_text(value)
            sensory.append([activity, freq])
    
    if sensory:
        sections.append("\nSensory Activities")
        sections.append(create_table(["Activity", "Frequency"], sensory))
    
    # Visual Activities
    visual = []
    for activity, name in [
        ('NearAcuity', 'Near Acuity'),
        ('FarAcuity', 'Far Acuity'),
        ('Depth', 'Depth Perception'),
        ('Accommodation', 'Accommodation'),
        ('ColorVision', 'Color Vision'),
        ('FieldVision', 'Field of Vision')
    ]:
        value = job_data.get(f"{activity}Num")
        if value:
            freq = get_frequency_text(value)
            visual.append([name, freq])
    
    if visual:
        sections.append("\nVisual Activities")
        sections.append(create_table(["Activity", "Frequency"], visual))
    
    # Environmental Conditions
    environmental = []
    for condition, name in [
        ('Weather', 'Weather'),
        ('Cold', 'Extreme Cold'),
        ('Heat', 'Extreme Heat'),
        ('Wet', 'Wet and/or Humid'),
        ('Noise', 'Noise'),
        ('Vibration', 'Vibration'),
        ('Atmosphere', 'Atmospheric Conditions'),
        ('Moving', 'Moving Mechanical Parts'),
        ('Electricity', 'Electric Shock'),
        ('Height', 'High Places'),
        ('Radiation', 'Radiation'),
        ('Explosion', 'Explosives'),
        ('Toxic', 'Toxic/Caustic Chemicals'),
        ('Other', 'Other Environmental Conditions')
    ]:
        value = job_data.get(f"{condition}Num")
        if value:
            freq = get_frequency_text(value)
            environmental.append([name, freq])
    
    if environmental:
        sections.append("\nEnvironmental Conditions")
        sections.append(create_table(["Condition", "Frequency"], environmental))
    
    # Worker Functions
    data_value = job_data.get('WFData')
    people_value = job_data.get('WFPeople')
    things_value = job_data.get('WFThings')
    
    if any(x is not None for x in [data_value, people_value, things_value]):
        sections.append("\nWorker Functions")
        sections.append("-" * len("Worker Functions"))
        
        try:
            if data_value is not None:
                data_level = int(data_value)
                if 0 <= data_level <= 8:
                    sections.append(f"Data: {worker_functions_map['Data'].get(data_level, 'Unknown')}")
        except (ValueError, TypeError):
            sections.append(f"Data: Unknown (Value: {data_value})")
            
        try:
            if people_value is not None:
                people_level = int(people_value)
                if 0 <= people_level <= 8:
                    sections.append(f"People: {worker_functions_map['People'].get(people_level, 'Unknown')}")
        except (ValueError, TypeError):
            sections.append(f"People: Unknown (Value: {people_value})")
            
        try:
            if things_value is not None:
                things_level = int(things_value)
                if 0 <= things_level <= 8:
                    sections.append(f"Things: {worker_functions_map['Things'].get(things_level, 'Unknown')}")
        except (ValueError, TypeError):
            sections.append(f"Things: Unknown (Value: {things_value})")
    
    # SVP Section
    svp_value = job_data.get('SVPNum')
    if svp_value:
        try:
            svp_num = int(svp_value)
            if 1 <= svp_num <= 9:
                sections.append("\nSpecific Vocational Preparation (SVP)")
                sections.append("-" * len("Specific Vocational Preparation (SVP)"))
                sections.append(f"Level {svp_num}: {svp_map.get(svp_num, 'Unknown')}")
        except (ValueError, TypeError):
            pass
    
    # GED Section
    ged_r = job_data.get('GEDR')
    ged_m = job_data.get('GEDM')
    ged_l = job_data.get('GEDL')
    
    if any(x is not None for x in [ged_r, ged_m, ged_l]):
        sections.append("\nGeneral Educational Development (GED)")
        sections.append("-" * len("General Educational Development (GED)"))
        
        for ged_type, value in [("Reasoning", ged_r), ("Math", ged_m), ("Language", ged_l)]:
            try:
                if value is not None:
                    level = int(value)
                    if 1 <= level <= 6:
                        sections.append(f"\n{ged_type}:")
                        sections.append(ged_map[ged_type].get(level, f"Unknown (Level: {level})"))
            except (ValueError, TypeError):
                sections.append(f"\n{ged_type}:")
                sections.append(f"Unknown (Value: {value})")
    
    # Aptitudes
    aptitudes = []
    aptitude_fields = {
        'G': 'AptGenLearn',
        'V': 'AptVerbal',
        'N': 'AptNumerical',
        'S': 'AptSpacial',
        'P': 'AptFormPer',
        'Q': 'AptClericalPer',
        'K': 'AptMotor',
        'F': 'AptFingerDext',
        'M': 'AptManualDext',
        'E': 'AptEyeHandCoord',
        'C': 'AptColorDisc'
    }
    
    for code, field in aptitude_fields.items():
        value = job_data.get(field)
        if value:
            try:
                level = int(value)
                if 1 <= level <= 5:
                    aptitudes.append([
                        f"{aptitude_map[code]} ({code})",
                        f"Level {level}",
                        aptitude_level_map.get(level, "Unknown")
                    ])
            except (ValueError, TypeError):
                aptitudes.append([
                    f"{aptitude_map[code]} ({code})",
                    "Unknown",
                    f"Invalid value: {value}"
                ])
    
    if aptitudes:
        sections.append("\nAptitudes")
        sections.append("-" * len("Aptitudes"))
        sections.append(create_table(
            ["Aptitude", "Level", "Description"],
            aptitudes
        ))
    
    # GOE Information
    if any(job_data.get(f'GOE{i}') for i in range(1, 4)):
        sections.append("\nGuide for Occupational Exploration (GOE)")
        sections.append("-" * len("Guide for Occupational Exploration (GOE)"))
        sections.append(f"Code: {job_data.get('GOE', 'Unknown')}")
        for i in range(1, 4):
            value = job_data.get(f'GOE{i}')
            if value:
                sections.append(f"Level {i}: {value}")
    
    return "\n".join(sections)

# Read the test data
with open("test_data_clean.csv", "r") as f:
    reader = csv.DictReader(f)
    job_data = next(reader)
    print(format_job_report(job_data))
