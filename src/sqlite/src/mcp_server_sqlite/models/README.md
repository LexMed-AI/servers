# Models Package

This package contains domain models for the MCP server's DOT job analysis functionality. The models provide standardized data structures that help prevent circular imports and improve code organization.

## Key Components

### DotJob Class (`dot_job.py`)

A dataclass representing a DOT job with standardized field names:

- `ncode`: Numeric representation of the DOT code
- `dot_code`: Formatted DOT code (XXX.XXX-XXX)
- `title`: Job title
- `definition`: Job definition
- `svp`: Specific Vocational Preparation level
- `strength_num`: Strength requirement numeric value
- `ged_reasoning`, `ged_math`, `ged_language`: GED component values

Key methods:
- `from_db_row()`: Create a DotJob instance from a database row dictionary
- `to_dict()`: Convert the DotJob instance to a dictionary

### JobAnalysis Class (`analysis.py`)

A dataclass representing a complete job analysis:

- Core job information (title, DOT code, definition)
- Analysis components (exertional level, skill level, GED levels, etc.)
- Physical demands and environmental conditions
- Obsolescence analysis

Key methods:
- `from_dict()`: Create a JobAnalysis instance from a dictionary
- `to_dict()`: Convert the JobAnalysis instance to a dictionary

### DotCode Class (`dot_code.py`)

A utility class for DOT code processing:

- `clean()`: Convert a DOT code between numeric and formatted representations
- `format()`: Format a numeric code as a standard DOT code string
- `validate()`: Validate a DOT code string for proper format
- `to_dict()`: Convert a DOT code to a dictionary with all its representations

## Usage

The models are designed to be imported and used throughout the application:

```python
from mcp_server_sqlite.models import DotJob, JobAnalysis, DotCode

# Convert a DOT code
ncode, formatted = DotCode.clean("209.587-034")

# Create a job model from database results
job = DotJob.from_db_row(db_result)

# Use a standardized job analysis
analysis = JobAnalysis(
    job_title=job.title,
    dot_code=job.dot_code,
    formatted_dot_code=job.dot_code,
    definition=job.definition,
    # ... other fields ...
)
```

## Benefits

- **Prevents Circular Imports**: The model classes are free of references to other modules
- **Standardizes Field Names**: Consistent field naming across the application
- **Type Safety**: Proper typing with dataclasses
- **Centralized Validation**: Built-in validation and data conversion
