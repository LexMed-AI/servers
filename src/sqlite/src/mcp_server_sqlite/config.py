# --- SVP (Specific Vocational Preparation) ---
# Source: Guide Section I (Descriptions), APIJobData.SVPNum (Key)
# Target: JobData.svp.description
svp_map = {
    1: "Short demonstration only",
    2: "Anything beyond short demonstration up to 1 month",
    3: "Over 1 month up to 3 months",
    4: "Over 3 months up to 6 months",
    5: "Over 6 months up to 1 year",
    6: "Over 1 year up to 2 years",
    7: "Over 2 years up to 4 years",
    8: "Over 4 years up to 10 years",
    9: "Over 10 years"
}

# --- SVP to Skill Level Mapping ---
# Maps SVP values to SSA skill level classifications
svp_to_skill_level = {
    1: "Unskilled",
    2: "Unskilled",
    3: "Semi-skilled",
    4: "Semi-skilled",
    5: "Skilled",
    6: "Skilled",
    7: "Skilled",
    8: "Skilled",
    9: "Skilled"
}

# --- Strength ---
# Source: Guide Section IV (Codes/Descriptions), APIJobData.Strength (Key 'S'-'V')
# Target: JobData.strength.level (Name 'Sedentary'-'Very Heavy'), JobData.strength.description
strength_map = {
    'S': "Exerting up to 10 pounds of force occasionally (up to 1/3 of the time) and/or a negligible amount of force frequently.",
    'L': "Exerting up to 20 pounds of force occasionally, and/or up to 10 pounds of force frequently.",
    'M': "Exerting 20 to 50 pounds of force occasionally, and/or 10 to 25 pounds of force frequently.",
    'H': "Exerting 50 to 100 pounds of force occasionally, and/or 25 to 50 pounds of force frequently.",
    'V': "Exerting in excess of 100 pounds of force occasionally, and/or in excess of 50 pounds of force frequently."
}

# --- Strength Code to Name Mapping ---
strength_code_to_name = {
    'S': 'Sedentary',
    'L': 'Light',
    'M': 'Medium',
    'H': 'Heavy',
    'V': 'Very Heavy'
}

# --- Strength Description Map ---
strength_description_map = {
    'S': "Exerting up to 10 pounds of force occasionally (up to 1/3 of the time) and/or a negligible amount of force frequently.",
    'L': "Exerting up to 20 pounds of force occasionally, and/or up to 10 pounds of force frequently.",
    'M': "Exerting 20 to 50 pounds of force occasionally, and/or 10 to 25 pounds of force frequently.",
    'H': "Exerting 50 to 100 pounds of force occasionally, and/or 25 to 50 pounds of force frequently.",
    'V': "Exerting in excess of 100 pounds of force occasionally, and/or in excess of 50 pounds of force frequently."
}

# --- Strength Number to Code Mapping ---
# Based on Revised Handbook for Analyzing Jobs (RHAJ) / DOT Appendix C definitions
# Used because schema only provides StrengthNum (INTEGER)
strength_num_to_code = {
    1: 'S', # Sedentary
    2: 'L', # Light
    3: 'M', # Medium
    4: 'H', # Heavy
    5: 'V', # Very Heavy
}

# --- RFC to Strength Level Mapping ---
# Maps RFC levels to compatible strength levels (for transferable skills analysis)
rfc_to_strength_levels = {
    "SEDENTARY": ["S"],
    "LIGHT": ["S", "L"],
    "MEDIUM": ["S", "L", "M"],
    "HEAVY": ["S", "L", "M", "H"],
    "VERY HEAVY": ["S", "L", "M", "H", "V"]
}

# --- Frequency Levels ---
# Source: Guide Section "Frequency Levels Definitions", APIJobData.<*>Num (Key 1-4)
# Target: JobData.characteristics.<*> (Name 'Not Present'-'Constantly' via FrequencyLevel type)
# Note: Guide uses 'Never', TS uses 'Not Present'. Prioritizing TS for target structure.
freq_map = {
    1: "N - Not Present",
    2: "O - Occasionally (up to 1/3 of the time)",
    3: "F - Frequently (1/3 to 2/3 of the time)",
    4: "C - Constantly (more than 2/3 of the time)"
}

# Enhanced frequency map with detailed descriptions
freq_map_detailed = {
    1: {
        "code": "N",
        "short": "Not Present",
        "full": "Activity or condition does not exist",
        "percentage": "0% of time",
        "hours_per_day": "0 hours"
    },
    2: {
        "code": "O",
        "short": "Occasionally",
        "full": "Activity or condition exists up to 1/3 of the time",
        "percentage": "Up to 33% of time",
        "hours_per_day": "Up to 2.5 hours in 8-hour day"
    },
    3: {
        "code": "F",
        "short": "Frequently",
        "full": "Activity or condition exists from 1/3 to 2/3 of the time",
        "percentage": "34-66% of time",
        "hours_per_day": "2.5 to 5.5 hours in 8-hour day"
    },
    4: {
        "code": "C",
        "short": "Constantly",
        "full": "Activity or condition exists 2/3 or more of the time",
        "percentage": "67-100% of time",
        "hours_per_day": "5.5 to 8 hours in 8-hour day"
    }
}

# --- Physical Demands & Environmental Conditions Labels ---
# Maps APIJobData field names (or suffixes) to display labels used in reports.
# Source: APIJobData keys, Guide Section V/VI codes, UI/DB mapping table labels.
# Target: Keys/Labels used in format_report.py or other display logic.
# NOTE: This assumes the Python code iterates through these or similar keys.
physical_demand_api_keys_to_labels = {
    # Postural
    'ClimbingNum': 'Climbing',
    'BalancingNum': 'Balancing',
    'StoopingNum': 'Stooping',
    'KneelingNum': 'Kneeling',
    'CrouchingNum': 'Crouching',
    'CrawlingNum': 'Crawling',
    # 'StandingNum': 'Standing', # Add if StandingNum exists in APIJobData

    # Manipulative
    'ReachingNum': 'Reaching',
    'HandlingNum': 'Handling',
    'FingeringNum': 'Fingering',
    'FeelingNum': 'Feeling',

    # Sensory
    'TalkingNum': 'Talking',
    'HearingNum': 'Hearing',
    'TastingNum': 'Taste/Smell', # Combined label based on TS/UI

    # Visual
    'NearAcuityNum': 'Near Acuity',
    'FarAcuityNum': 'Far Acuity',
    'DepthNum': 'Depth Perception',
    'AccommodationNum': 'Accommodation',
    'ColorVisionNum': 'Color Vision',
    'FieldVisionNum': 'Field of Vision'
}

# Enhanced physical demands with detailed descriptions
physical_demands_descriptions = {
    'Climbing': "Ascending or descending ladders, stairs, scaffolding, ramps, poles and the like, using feet and legs and/or hands and arms",
    'Balancing': "Maintaining body equilibrium to prevent falling and walking, standing or crouching on narrow, slippery, or moving surfaces",
    'Stooping': "Bending body downward and forward by bending spine at the waist",
    'Kneeling': "Bending legs at knee to come to a rest on knee or knees",
    'Crouching': "Bending the body downward and forward by bending leg and spine",
    'Crawling': "Moving about on hands and knees or hands and feet",
    'Reaching': "Extending hand(s) and arm(s) in any direction",
    'Handling': "Seizing, holding, grasping, turning, or otherwise working with hand or hands",
    'Fingering': "Picking, pinching, typing or otherwise working primarily with fingers rather than with the whole hand as in handling",
    'Feeling': "Perceiving attributes of objects, such as size, shape, temperature or texture by touching with skin",
    'Talking': "Expressing or exchanging ideas by means of the spoken word",
    'Hearing': "Perceiving the nature of sounds at normal speaking levels with or without correction",
    'Taste/Smell': "Distinguishing, with the aid of tongue and/or nose, the qualities of chemicals by taste or odor",
    'Near Acuity': "Clarity of vision at 20 inches or less",
    'Far Acuity': "Clarity of vision at 20 feet or more",
    'Depth Perception': "Three-dimensional vision; ability to judge distances and spatial relationships",
    'Accommodation': "Adjustment of eye to bring an object into sharp focus",
    'Color Vision': "Ability to identify and distinguish colors",
    'Field of Vision': "Observing an area that can be seen up and down or right to left while eyes are fixed on a given point"
}

environmental_condition_api_keys_to_labels = {
    'WeatherNum': 'Weather',
    'ColdNum': 'Extreme Cold',
    'HeatNum': 'Extreme Heat',
    'WetNum': 'Wet/Humid', # Label based on previous format_report
    'NoiseNum': 'Noise', # Noise level handled separately
    'VibrationNum': 'Vibration',
    'AtmosphereNum': 'Atmospheric Conditions',
    'MovingNum': 'Moving Mechanical Parts', # Label based on previous format_report
    'ElectricityNum': 'Electric Shock',
    'HeightNum': 'High Places', # Label based on previous format_report
    'RadiationNum': 'Radiation',
    'ExplosionNum': 'Explosives', # Label based on previous format_report
    'ToxicNum': 'Toxic/Caustic Chemicals', # Label based on previous format_report
    'OtherNum': 'Other Conditions' # Label based on previous format_report
}

# Enhanced environmental conditions with detailed descriptions
environmental_conditions_descriptions = {
    'Weather': "Exposure to outside atmospheric conditions",
    'Extreme Cold': "Exposure to non-weather-related cold temperatures",
    'Extreme Heat': "Exposure to non-weather-related hot temperatures",
    'Wet/Humid': "Contact with water or other liquids or exposure to non-weather-related humid conditions",
    'Noise': "Exposure to sounds and noise levels that may be distracting or uncomfortable",
    'Vibration': "Exposure to oscillating movements of the extremities or whole body",
    'Atmospheric Conditions': "Exposure to conditions such as fumes, noxious odors, dusts, mists, gases, and poor ventilation",
    'Moving Mechanical Parts': "Exposure to possible bodily injury from moving mechanical parts of equipment, tools, or machinery",
    'Electric Shock': "Exposure to possible bodily injury from electrical shock",
    'High Places': "Exposure to possible bodily injury from falling",
    'Radiation': "Exposure to possible bodily injury from radiation",
    'Explosives': "Exposure to possible injury from explosions",
    'Toxic/Caustic Chemicals': "Exposure to possible bodily injury from toxic or caustic chemicals",
    'Other Conditions': "Exposure to conditions other than those listed"
}

# --- Noise ---
# Source: Guide Section "Noise Levels", APIJobData.NoiseNum (Key 1-5)
# Target: JobData.characteristics.environmental.noise (String Name)
noise_map = {
    1: "Very Quiet",
    2: "Quiet",
    3: "Moderate",
    4: "Loud",
    5: "Very Loud"
}

# Enhanced noise level descriptions
noise_level_descriptions = {
    1: {
        "name": "Very Quiet",
        "description": "Very quiet environment such as a private office with no machinery, isolation booth for hearing tests",
        "examples": ["Private office", "Recording studio", "Isolation booth"]
    },
    2: {
        "name": "Quiet",
        "description": "Quiet environment such as a library, many private offices, funeral reception area, light traffic",
        "examples": ["Library", "Many private offices", "Funeral home reception"]
    },
    3: {
        "name": "Moderate",
        "description": "Moderate noise such as business office with typewriters/computers, light traffic, department store",
        "examples": ["Business office", "Department store", "Fast food restaurant"]
    },
    4: {
        "name": "Loud",
        "description": "Loud noise such as heavy traffic, factory areas with noisy machines",
        "examples": ["Factory with noisy machines", "Heavy traffic", "Many pieces of large office equipment"]
    },
    5: {
        "name": "Very Loud",
        "description": "Very loud noise such as in a boiler room, near a jackhammer or jet engine",
        "examples": ["Boiler room", "Near jackhammer", "Near jet engine"]
    }
}

# --- GED (General Educational Development) ---
# Source: Guide Section III (Descriptions), APIJobData.GEDR/M/L (Key 1-6)
# Target: JobData.generalEducationalDevelopment.<*>.description
# Using the guide's summary descriptions as before.
ged_map = {
    1: {
        "reasoning": "Apply commonsense understanding to carry out simple one- or two-step instructions",
        "math": "Add and subtract two-digit numbers; multiply and divide 10's and 100's; perform basic arithmetic with coins and units",
        "language": "Recognize meaning of 2,500 words; print simple sentences; speak simple sentences"
    },
    2: {
        "reasoning": "Apply commonsense understanding to carry out detailed but uninvolved instructions",
        "math": "Perform arithmetic operations with fractions, decimals, percentages; draw and interpret bar graphs",
        "language": "Read at a rate of 190-215 words/minute, write compound sentences, speak clearly"
    },
    3: {
        "reasoning": "Apply commonsense understanding to carry out instructions in written, oral, or diagrammatic form",
        "math": "Compute discount, interest; Algebra; Geometry",
        "language": "Read a variety of novels, write reports, speak confidently"
    },
    4: {
        "reasoning": "Apply principles of rational systems to solve practical problems",
        "math": "Algebra, Geometry, Shop Math",
        "language": "Read novels, prepare business letters, participate in discussions"
    },
    5: {
        "reasoning": "Apply principles of logical or scientific thinking to define problems, collect data, establish facts, and draw valid conclusions",
        "math": "Algebra, Calculus, Statistics",
        "language": "Read literature, write novels, conversant in effective speaking"
    },
    6: {
        "reasoning": "Apply principles of logical or scientific thinking to a wide range of problems; handle nonverbal symbolism in its most difficult forms",
        "math": "Advanced calculus, Modern Algebra, Statistics",
        "language": "Same as Level 5"
    }
}

# Enhanced GED to RFC mental limitation mapping
ged_reasoning_to_rfc_mental = {
    1: {
        "compatible_with": ["simple 1-2 step instructions", "simple, routine, repetitive tasks"],
        "potentially_incompatible_with": ["detailed instructions", "complex tasks", "independent judgment"]
    },
    2: {
        "compatible_with": ["detailed but uninvolved instructions", "routine work with some variation"],
        "potentially_incompatible_with": ["complex instructions", "abstract concepts", "independent judgment"]
    },
    3: {
        "compatible_with": ["instructions in various forms", "semi-complex tasks", "some independent judgment"],
        "potentially_incompatible_with": ["highly complex tasks", "significant abstract reasoning"]
    },
    4: {
        "compatible_with": ["complex tasks", "abstract concepts", "independent judgment"],
        "potentially_incompatible_with": ["severe concentration deficits", "significant memory impairments"]
    },
    5: {
        "compatible_with": ["advanced reasoning", "complex problem-solving", "high-level abstract thinking"],
        "potentially_incompatible_with": ["most mental RFC limitations"]
    },
    6: {
        "compatible_with": ["highest level reasoning", "scientific thinking", "advanced symbolism"],
        "potentially_incompatible_with": ["most mental RFC limitations"]
    }
}

# --- Worker Functions ---
# Source: APIJobData.WFData/People/Things (Key 0-8)
# Target: JobData.workerFunctions.<*>.description
worker_functions_map = {
    "data": {
        0: "*Synthesizing*: Integrating analyses of data to discover facts and/or develop knowledge concepts or interpretations",
        1: "*Coordinating*: Determining time, place, and sequence of operations or action to be taken on the basis of analysis of data",
        2: "*Analyzing*: Examining and evaluating data. Presenting alternative actions in relation to the evaluation",
        3: "*Compiling*: Gathering, collating, or classifying information about data, people, or things",
        4: "*Computing*: Performing arithmetic operations and reporting on and/or carrying out prescribed actions",
        5: "*Copying*: Transcribing, entering, or posting data",
        6: "*Comparing*: Judging the readily observable functional, structural, or compositional characteristics",
        7: "*No significant relationship*: The worker has no significant relationship with data",
        8: "*Taking Instructions-Helping*: Helping applies to 'non-learning' helpers"
    },
    "people": {
        0: "*Mentoring*: Dealing with individuals in terms of their total personality to advise, counsel, and/or guide them",
        1: "*Negotiating*: Exchanging ideas, information, and opinions with others to formulate policies and programs",
        2: "*Instructing*: Teaching subject matter to others, or training others through explanation and demonstration",
        3: "*Supervising*: Determining or interpreting work procedures for a group of workers",
        4: "*Diverting*: Amusing others, usually through the medium of stage, screen, television, or radio",
        5: "*Persuading*: Influencing others in favor of a product, service, or point of view",
        6: "*Speaking-Signaling*: Talking with and/or signaling people to convey or exchange information",
        7: "*Serving*: Attending to the needs or requests of people or animals",
        8: "*No significant relationship*: The worker has no significant relationship with people"
    },
    "things": {
        0: "*Setting Up*: Adjusting machines or equipment by replacing or altering tools, jigs, fixtures, and attachments",
        1: "*Precision Working*: Using body members and/or tools or work aids to work, move, guide, or place objects or materials",
        2: "*Operating-Controlling*: Starting, stopping, controlling, and adjusting the progress of machines or equipment",
        3: "*Driving-Operating*: Starting, stopping, and controlling the actions of machines or equipment for which a course must be steered",
        4: "*Manipulating*: Using body members, tools, or special devices to work, move, guide, or place objects or materials",
        5: "*Tending*: Starting, stopping, and observing the functioning of machines and equipment",
        6: "*Feeding-Offbearing*: Inserting, throwing, dumping, or placing materials in or removing them from machines",
        7: "*Handling*: Using body members, handtools, and/or special devices to work, move, or carry objects or materials",
        8: "*No significant relationship*: The worker has no significant relationship with things"
    }
}

# Enhanced worker functions with RFC compatibility notes
worker_functions_rfc_notes = {
    "data": {
        0: {
            "mental_limitations": "May be incompatible with limitations on complex tasks, problem-solving, abstract thinking",
            "physical_limitations": "Generally no direct physical limitations"
        },
        1: {
            "mental_limitations": "May be incompatible with limitations on planning, organizing, decision-making",
            "physical_limitations": "Generally no direct physical limitations"
        },
        2: {
            "mental_limitations": "May be incompatible with limitations on analysis, evaluation, judgment",
            "physical_limitations": "Generally no direct physical limitations"
        },
        3: {
            "mental_limitations": "May be incompatible with significant memory or concentration limitations",
            "physical_limitations": "Generally no direct physical limitations"
        },
        4: {
            "mental_limitations": "May be incompatible with significant mathematical limitations",
            "physical_limitations": "Generally no direct physical limitations"
        },
        5: {
            "mental_limitations": "Often compatible with limitations to simple, routine tasks",
            "physical_limitations": "May be incompatible with manipulative limitations affecting writing/typing"
        },
        6: {
            "mental_limitations": "Often compatible with limitations to simple, routine tasks",
            "physical_limitations": "Generally no significant mental limitations"
        },
        7: {
            "mental_limitations": "Compatible with most mental limitations",
            "physical_limitations": "Compatible with most mental limitations"
        }
    },
    "people": {
        # Similar structure for people function levels 0-8
        6: {
            "mental_limitations": "May be incompatible with significant communication limitations",
            "physical_limitations": "May be incompatible with speech impairments"
        },
        # Add other levels as needed
    },
    "things": {
        # Similar structure for things function levels 0-8
        7: {
            "mental_limitations": "Generally compatible with most mental limitations",
            "physical_limitations": "May be incompatible with manipulative or lifting/carrying limitations"
        },
        # Add other levels as needed
    }
}

# --- Aptitudes ---
# Source: Guide Section "Aptitude Codes", "Test Score Conversion Guide", APIJobData.Apt<*> (Key 1-5)
# Target: JobData.aptitudes.<*>.aptitude (Name), JobData.aptitudes.<*>.description (Interpretation)

# Maps standard Aptitude codes ('G', 'V', ...) to APIJobData field suffix and full name/description
# Needed to link API data field to the aptitude it represents
aptitude_code_to_details_map = {
    "G": {"api_suffix": "GenLearn", "name": "General Learning Ability: Learn, reason, make judgments"},
    "V": {"api_suffix": "Verbal", "name": "Verbal: Understand and use words effectively"},
    "N": {"api_suffix": "Numerical", "name": "Numerical: Perform mathematical functions"},
    "S": {"api_suffix": "Spacial", "name": "Spatial: Visualize 3D objects from 2D"}, # Note API uses 'Spacial'
    "P": {"api_suffix": "FormPer", "name": "Form Perception: Perceive and distinguish graphic detail"},
    "Q": {"api_suffix": "ClericalPer", "name": "Clerical Perception: Distinguish verbal detail"},
    "K": {"api_suffix": "Motor", "name": "Motor Coordination: Coordinate eyes, hands, fingers"},
    "F": {"api_suffix": "FingerDext", "name": "Finger Dexterity: Manipulate small objects"},
    "M": {"api_suffix": "ManualDext", "name": "Manual Dexterity: Handle placing and turning motions"},
    "E": {"api_suffix": "EyeHandCoord", "name": "Eye/Hand/Foot Coordination: Respond to visual stimuli"}, # Note API may shorten suffix
    "C": {"api_suffix": "ColorDisc", "name": "Color Discrimination: Match/discriminate colors"}
}

# Maps aptitude level number (1-5) to the interpretation description
# Source: Guide Section "Test Score Conversion Guide", Interpretation column
aptitude_level_map = {
    1: "Superior",
    2: "Above Average",
    3: "Average",
    4: "Below Average",
    5: "Minimal Ability/Unable to Perform"
}

# Enhanced aptitude descriptions with percentile ranges
aptitude_level_percentiles = {
    1: {
        "description": "Superior",
        "percentile_range": "Top 10% (90th percentile and above)",
        "rfc_compatibility": "Even high mental/physical limitations may not preclude performance"
    },
    2: {
        "description": "Above Average",
        "percentile_range": "Top third excluding the top 10% (67th to 89th percentile)",
        "rfc_compatibility": "Some significant mental/physical limitations may be compatible"
    },
    3: {
        "description": "Average",
        "percentile_range": "Middle third (34th to 66th percentile)",
        "rfc_compatibility": "Moderate mental/physical limitations may affect performance"
    },
    4: {
        "description": "Below Average",
        "percentile_range": "Lowest third excluding bottom 10% (11th to 33rd percentile)",
        "rfc_compatibility": "Even mild to moderate limitations may significantly affect performance"
    },
    5: {
        "description": "Minimal Ability/Unable to Perform",
        "percentile_range": "Lowest 10% (10th percentile and below)",
        "rfc_compatibility": "Most limitations in this area would preclude performance"
    }
}

# --- Temperaments ---
# Source: Guide Section VII (Codes/Descriptions), APIJobData.Temp1-5 (Values 'D'-'J')
# Target: JobData.temperaments.description
temperament_map = {
    'D': "Directing: Controlling or planning activities",
    'R': "Repetitive: Performing repetitive or short cycle work",
    'I': "Influencing: Influencing people's opinions, attitudes, judgments",
    'V': "Variety: Performing a variety of work",
    'E': "Expressing: Expressing personal feelings",
    'A': "Alone: Working alone or apart in physical isolation",
    'S': "Stress: Performing under stress",
    'T': "Tolerances: Attaining precise set limits, tolerances, standards",
    'U': "Instructions: Working under specific instructions",
    'P': "People: Dealing with people",
    'J': "Judgments: Making judgments and decisions"
}

# Enhanced temperaments with RFC considerations
temperament_rfc_considerations = {
    'D': {
        "description": "Directing: Controlling or planning activities",
        "mental_rfc_considerations": "May be incompatible with limitations on decision-making, planning, organizing",
        "examples": ["Supervisor", "Manager", "Team Leader"]
    },
    'R': {
        "description": "Repetitive: Performing repetitive or short cycle work",
        "mental_rfc_considerations": "Often compatible with limitations to simple, routine tasks",
        "examples": ["Assembly Line Worker", "Data Entry Clerk", "Machine Operator"]
    },
    'I': {
        "description": "Influencing: Influencing people's opinions, attitudes, judgments",
        "mental_rfc_considerations": "May be incompatible with social interaction limitations",
        "examples": ["Sales Representative", "Teacher", "Public Relations Specialist"]
    },
    'V': {
        "description": "Variety: Performing a variety of work",
        "mental_rfc_considerations": "May be incompatible with limitations to simple, routine tasks",
        "examples": ["General Office Clerk", "Maintenance Worker", "Small Business Owner"]
    },
    'E': {
        "description": "Expressing: Expressing personal feelings",
        "mental_rfc_considerations": "May be incompatible with social interaction limitations",
        "examples": ["Actor", "Counselor", "Artist"]
    },
    'A': {
        "description": "Alone: Working alone or apart in physical isolation",
        "mental_rfc_considerations": "May be compatible with social interaction limitations",
        "examples": ["Fire Lookout", "Night Security Guard", "Remote Data Analyst"]
    },
    'S': {
        "description": "Stress: Performing under stress",
        "mental_rfc_considerations": "Often incompatible with stress limitations",
        "examples": ["Air Traffic Controller", "Emergency Room Nurse", "Police Officer"]
    },
    'T': {
        "description": "Tolerances: Attaining precise set limits, tolerances, standards",
        "mental_rfc_considerations": "May be incompatible with concentration limitations",
        "examples": ["Quality Control Inspector", "Surgeon", "Jeweler"]
    },
    'U': {
        "description": "Instructions: Working under specific instructions",
        "mental_rfc_considerations": "Often compatible with limitations to simple, routine tasks",
        "examples": ["Production Worker", "Clerical Worker", "Food Service Worker"]
    },
    'P': {
        "description": "People: Dealing with people",
        "mental_rfc_considerations": "May be incompatible with social interaction limitations",
        "examples": ["Receptionist", "Customer Service Representative", "Retail Sales Clerk"]
    },
    'J': {
        "description": "Judgments: Making judgments and decisions",
        "mental_rfc_considerations": "May be incompatible with limitations on decision-making",
        "examples": ["Judge", "Physician", "Financial Analyst"]
    }
}

# --- GOE (Guide for Occupational Exploration) ---
# Source: Guide Section IX
# Target: Potentially used if processing GOE code/titles further
goe_interest_area_map = {
    '01': "Artistic",
    '02': "Scientific",
    '03': "Plants-Animals",
    '04': "Protective",
    '05': "Mechanical",
    '06': "Industrial",
    '07': "Business Detail",
    '08': "Selling",
    '09': "Accommodating",
    '10': "Humanitarian",
    '11': "Leading-Influencing",
    '12': "Physical Performing"
}

# --- SSR Application Date Cutoff (NEW) ---
# Defines the cutoff date for SSR 00-4p vs SSR 24-3p application
ssr_application_date = {
    'ssr_00_4p_end_date': '2025-01-05',  # Last day SSR 00-4p applies
    'ssr_24_3p_start_date': '2025-01-06'  # First day SSR 24-3p applies
}
