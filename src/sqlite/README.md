# SQLite MCP Server

## Overview
A Model Context Protocol (MCP) server implementation for advanced job data analysis, vocational evaluation, and business intelligence using SQLite and BLS Excel data. This server enables running SQL queries, generating job reports, checking job obsolescence, analyzing transferable skills, and integrating SSA Medical-Vocational Guidelines for VE/SSA use cases.

## Features
- **Direct SQL Querying:** Run safe, read-only SELECT queries on the DOT SQLite database.
- **Job Report Generation:** Generate detailed, formatted reports for DOT jobs, including exertion, SVP, GED, physical/environmental demands, etc.
- **Job Obsolescence Checking:** Check if a DOT job is potentially obsolete using SSA/EM guidance and reference data from `reference_json/obsolete_out_dated.json`.
- **Transferable Skills Analysis (TSA):** Perform preliminary analysis of transferable skills and apply SSA Medical-Vocational Guidelines (Grids) for claimants (using data from `reference_json/medical_vocational_guidelines.json` and `reference_json/ssr_82-41.json`).
- **BLS Excel Data Integration:** Query BLS OEWS data by SOC code or occupation title for wage and employment statistics (using data from `DOTSOCBLS_Excel/bls_all_data_M_2024.xlsx`).
- **Schema Introspection:** List tables and describe table schemas in the DOT database.
- **Robust Error Handling:** All tools and handlers provide structured error messages and logging.

## Components

### Prompts
The server provides one primary prompt intended for VE transcript analysis:
- **`ve-transcript-audit`**
  - **Description:** Instructs AI to act as VE Auditor and analyze a hearing transcript using the `ve_audit_MCP_rag.py` template.
  - **Required Arguments:**
    - `hearing_date` (string): Date of the hearing (YYYY-MM-DD).
    - `transcript` (string): Full text of the hearing transcript.
  - **Optional Argument:**
    - `claimant_name` (string): Claimant identifier (defaults to "Claimant").

### Tools
The server offers the following tools:

#### Core VE Analysis Tools
- **`generate_job_report`**
  - **Description:** Generate a comprehensive formatted text report of job requirements (Exertion, SVP, GED, Physical Demands, Environment, etc.) for a specific DOT code or job title.
  - **Input:**
    - `search_term` (string): DOT code (format: XXX.XXX-XXX) or job title to search for.
  - **Returns:** Formatted text report.

- **`check_job_obsolescence`**
  - **Description:** Check if a specific DOT job is potentially obsolete based on available indicators and SSA guidance (e.g., EM-24027 REV).
  - **Input:**
    - `dot_code` (string): DOT code (format: XXX.XXX-XXX) to analyze.
  - **Returns:** JSON string with analysis results.

- **`analyze_transferable_skills`**
  - **Description:** Performs a preliminary Transferable Skills Analysis (TSA) based on PRW, RFC, age, and education per SSA guidelines. **Note:** Placeholder implementation requiring full SSA rules review for production use.
  - **Input:**
    - `source_dot` (string): DOT code (format: XXX.XXX-XXX) of the Past Relevant Work (PRW).
    - `residual_capacity` (string): Claimant's RFC level (e.g., SEDENTARY, LIGHT).
    - `age` (string): Claimant's age category (e.g., ADVANCED AGE).
    - `education` (string): Claimant's education category (e.g., HIGH SCHOOL).
    - `target_dots` (array, optional): Specific target DOT codes (format: XXX.XXX-XXX) suggested by VE.
  - **Returns:** JSON string with preliminary TSA results.

#### Database Utility Tools
- **`read_query`**
  - **Description:** Execute a read-only SELECT query directly on the DOT SQLite database.
  - **Input:**
    - `query` (string): The SELECT SQL query to execute.
  - **Returns:** JSON string of query results.

- **`list_tables`**
  - **Description:** List all tables available in the DOT SQLite database.
  - **Input:** None.
  - **Returns:** JSON string containing an array of table names.

- **`describe_table`**
  - **Description:** Get the column schema for a specific table in the DOT database.
  - **Input:**
    - `table_name` (string): Name of the table (e.g., 'DOT').
  - **Returns:** JSON string with column schema information.

#### BLS Excel Tools
- **`analyze_bls_excel`**
  - **Description:** Check the status of the loaded BLS Excel data handler and show basic info (e.g., first few rows).
  - **Input:** None.
  - **Returns:** JSON string with handler status and data summary.

- **`query_bls_by_soc`**
  - **Description:** Query BLS occupation data by SOC (Standard Occupational Classification) code. Returns wage and employment data.
  - **Input:**
    - `soc_code` (string): SOC code to search for (e.g., '15-1252').
  - **Returns:** JSON string with matching BLS data or message if not found.

- **`query_bls_by_title`**
  - **Description:** Search BLS occupation data by job title (partial match). Returns wage and employment data for matching occupations.
  - **Input:**
    - `title` (string): Occupation title to search for (e.g., 'Software').
  - **Returns:** JSON string with matching BLS data results.

## Medical-Vocational Guidelines (Grids)
- The server loads SSA Medical-Vocational Guidelines from `src/sqlite/src/mcp_server_sqlite/reference_json/medical_vocational_guidelines.json` and applies them in TSA analysis.

## DOT SQLite Database
- This repository includes a comprehensive **SQLite database** (`src/sqlite/src/mcp_server_sqlite/DOT.db`) containing Dictionary of Occupational Titles (DOT) jobs and requirements.
- It's the primary data source for `generate_job_report`, `analyze_transferable_skills`, `check_job_obsolescence`, and `read_query`.
- The server loads this database at startup (path provided via `--db-path`).
- You can explore the schema with `list_tables` and `describe_table`.
- You may replace or update the database file, ensuring the schema matches.

### Database Schema (`DOT` Table)

```sql
CREATE TABLE "DOT" (
"Ncode" INTEGER PRIMARY KEY,
"DocumentNumber" TEXT,
"Code" REAL,
"DLU" INTEGER,
"WFData" INTEGER,
"WFDataSig" TEXT,
"WFPeople" INTEGER,
"WFPeopleSig" TEXT,
"WFThings" INTEGER,
"WFThingsSig" TEXT,
"GEDR" INTEGER,
"GEDM" INTEGER,
"GEDL" INTEGER,
"SVPNum" INTEGER,
"AptGenLearn" INTEGER,
"AptVerbal" INTEGER,
"AptNumerical" INTEGER,
"AptSpacial" INTEGER,
"AptFormPer" INTEGER,
"AptClericalPer" INTEGER,
"AptMotor" INTEGER,
"AptFingerDext" INTEGER,
"AptManualDext" INTEGER,
"AptEyeHandCoord" INTEGER,
"AptColorDisc" INTEGER,
"WField1" TEXT,
"WField2" TEXT,
"WField3" TEXT,
"MPSMS1" TEXT,
"MPSMS2" TEXT,
"MPSMS3" TEXT,
"Temp1" TEXT,
"Temp2" TEXT,
"Temp3" TEXT,
"Temp4" TEXT,
"Temp5" TEXT,
"GOE" REAL,
"GOENum" INTEGER,
"Strength" TEXT,
"StrengthNum" INTEGER,
"ClimbingNum" INTEGER,
"BalancingNum" INTEGER,
"StoopingNum" INTEGER,
"KneelingNum" INTEGER,
"CrouchingNum" INTEGER,
"CrawlingNum" INTEGER,
"ReachingNum" INTEGER,
"HandlingNum" INTEGER,
"FingeringNum" INTEGER,
"FeelingNum" INTEGER,
"TalkingNum" INTEGER,
"HearingNum" INTEGER,
"TastingNum" INTEGER,
"NearAcuityNum" INTEGER,
"FarAcuityNum" INTEGER,
"DepthNum" INTEGER,
"AccommodationNum" INTEGER,
"ColorVisionNum" INTEGER,
"FieldVisionNum" INTEGER,
"WeatherNum" INTEGER,
"ColdNum" INTEGER,
"HeatNum" INTEGER,
"WetNum" INTEGER,
"NoiseNum" INTEGER,
"VibrationNum" INTEGER,
"AtmosphereNum" INTEGER,
"MovingNum" INTEGER,
"ElectricityNum" INTEGER,
"HeightNum" INTEGER,
"RadiationNum" INTEGER,
"ExplosionNum" INTEGER,
"ToxicNum" INTEGER,
"OtherNum" INTEGER,
"Title" TEXT,
"AltTitles" TEXT,
"CompleteTitle" TEXT,
"Industry" TEXT,
"Definitions" TEXT,
"GOE1" TEXT,
"GOE2" TEXT,
"GOE3" TEXT,
"WField1Short" TEXT,
"WField2Short" TEXT,
"WField3Short" TEXT,
"MPSMS1Short" TEXT,
"MPSMS2Short" TEXT,
"MPSMS3Short" TEXT,
"OccGroup" TEXT
);

CREATE INDEX idx_dot_title ON DOT (Title);
CREATE INDEX idx_dot_completetitle ON DOT (CompleteTitle);
CREATE INDEX idx_dot_code_text ON DOT (CAST(Code AS TEXT));
```

## Usage (Standalone / External Client)

To run the server locally (e.g., for development or use with an external client like Claude Desktop):

1.  Ensure you have Python 3.10+ installed.
2.  Install dependencies (likely managed via `uv` or `pip`).
3.  Navigate to the root of the `servers` repository in your terminal.
4.  Run the server module, providing the path to the database:

```bash
python -m src.sqlite.src.mcp_server_sqlite --db-path src/sqlite/src/mcp_server_sqlite/DOT.db
```

The server will start and listen for MCP requests via stdio.

## Usage with Claude Desktop (Example Configurations)

### uv

```json
# Add the server to your claude_desktop_config.json
"mcpServers": {
  "sqlite": {
    "command": "uv",
    "args": [
      "--directory",
      "parent_of_servers_repo/servers/src/sqlite", # Adjust path as needed
      "run",
      "mcp-server-sqlite", # Assumes package name or script alias
      "--db-path",
      "src/sqlite/src/mcp_server_sqlite/DOT.db" # Relative path within project
    ]
  }
}
```

### Docker

```json
# Add the server to your claude_desktop_config.json
"mcpServers": {
  "sqlite": {
    "command": "docker",
    "args": [
      "run",
      "--rm",
      "-i",
      "-v",
      "./src/sqlite:/app/src/sqlite", # Mount project sub-directory
      "mcp/sqlite", # Assumes docker image name
      "--db-path",
      "/app/src/sqlite/src/mcp_server_sqlite/DOT.db" # Path inside container
    ]
  }
}
```

## Building (Docker Example)

```bash
docker build -t mcp/sqlite . # Run from src/sqlite directory, adjust Dockerfile context if needed
```

## BLS Excel Integration
- The server attempts to load BLS OEWS Excel data from `src/sqlite/src/mcp_server_sqlite/DOTSOCBLS_Excel/bls_all_data_M_2024.xlsx` at startup.
- If the file is missing or fails to load, BLS tools (`analyze_bls_excel`, `query_bls_by_soc`, `query_bls_by_title`) will return a structured error message, and a warning will be logged. Other tools will remain available.

## Error Handling and Logging
- All tool calls and handlers use structured error handling and logging. Check server console output for detailed logs.
- Errors are returned as JSON or formatted text via MCP.
- Critical errors during initialization (e.g., missing database) will prevent the server from starting fully or disable relevant tools.

## Extensibility and Code Structure
- Modular handler classes for database, Excel, TSA, and job obsolescence logic.
- Configuration (`config.py`) and prompt templates (`prompt_library/`) are separated.
- See `src/sqlite/src/mcp_server_sqlite/` for module details.

## Code Quality, Testing, and Contribution
- All modules use docstrings, type hints, and logging.
- Input validation and error handling are enforced.
- Unit tests are recommended.
- Contributions are welcome!

## License

This MCP server is licensed under the MIT License. See the LICENSE file for details.
