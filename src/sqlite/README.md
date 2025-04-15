# SQLite MCP Server

## Overview
A Model Context Protocol (MCP) server implementation for advanced job data analysis, vocational evaluation, and business intelligence using SQLite and BLS Excel data. This server enables running SQL queries, generating job reports, analyzing transferable skills, and integrating SSA Medical-Vocational Guidelines for VE/SSA use cases.

## Features
- **Direct SQL Querying:** Run safe, read-only SELECT queries on the DOT SQLite database.
- **Job Report Generation:** Generate detailed, formatted reports for DOT jobs, including exertion, SVP, GED, and more.
- **Job Obsolescence Checking:** Check if a DOT job is potentially obsolete using SSA/EM guidance and reference data.
- **Transferable Skills Analysis (TSA):** Analyze transferable skills and apply SSA Medical-Vocational Guidelines (Grids) for claimants.
- **BLS Excel Data Integration:** Query BLS OEWS data by SOC code or occupation title for wage and employment statistics.
- **Schema Introspection:** List tables and describe table schemas in the DOT database.
- **Robust Error Handling:** All tools and handlers provide structured error messages and logging.

## Components

### Resources
The server exposes a single dynamic resource:
- `memo://insights`: A continuously updated business insights memo that aggregates discovered insights during analysis
  - Auto-updates as new insights are discovered via the append-insight tool

### Prompts
The server provides a demonstration prompt:
- `mcp-demo`: Interactive prompt that guides users through database operations
  - Required argument: `topic` - The business domain to analyze
  - Generates appropriate database schemas and sample data
  - Guides users through analysis and insight generation
  - Integrates with the business insights memo

### Tools
The server offers six core tools:

#### Query Tools
- `read_query`
   - Execute SELECT queries to read data from the database
   - Input:
     - `query` (string): The SELECT SQL query to execute
   - Returns: Query results as array of objects

- `write_query`
   - Execute INSERT, UPDATE, or DELETE queries
   - Input:
     - `query` (string): The SQL modification query
   - Returns: `{ affected_rows: number }`

- `create_table`
   - Create new tables in the database
   - Input:
     - `query` (string): CREATE TABLE SQL statement
   - Returns: Confirmation of table creation

#### Schema Tools
- `list_tables`
   - Get a list of all tables in the database
   - No input required
   - Returns: Array of table names

- `describe-table`
   - View schema information for a specific table
   - Input:
     - `table_name` (string): Name of table to describe
   - Returns: Array of column definitions with names and types

#### Analysis Tools
- `append_insight`
   - Add new business insights to the memo resource
   - Input:
     - `insight` (string): Business insight discovered from data analysis
   - Returns: Confirmation of insight addition
   - Triggers update of memo://insights resource

### Medical-Vocational Guidelines (Grids)
- The server loads SSA Medical-Vocational Guidelines from a structured JSON file and applies them in TSA analysis (see `reference/medical_vocational_guidelines.json`).

## DOT SQLite Database

This repository includes a comprehensive **SQLite database** containing all Dictionary of Occupational Titles (DOT) jobs and their associated job requirements. The database is used as the primary data source for:

- **Job report generation**
- **Transferable Skills Analysis (TSA)**
- **Job obsolescence checks**
- **Direct SQL queries and schema introspection**

### What's Included
- **DOT Jobs Table:** Contains every DOT code, job title, and detailed requirements (exertion, SVP, GED, physical/environmental demands, etc.).
- **Schema:** The database schema is designed for efficient querying and integration with MCP tools.
- **Reference Data:** Used by the server's logic modules for VE/SSA analysis and reporting.

### Usage
- The server loads the SQLite database at startup (path provided via `--db-path`).
- All core tools and handlers interact with this database for job lookups, reporting, and analysis.
- You can run safe, read-only SELECT queries using the `read_query` tool, or explore the schema with `list_tables` and `describe_table`.

### Customization
- You may replace or update the database file to use a different or updated DOT dataset, as long as the schema matches the expected structure.

## Usage with Claude Desktop

### uv

```bash
# Add the server to your claude_desktop_config.json
"mcpServers": {
  "sqlite": {
    "command": "uv",
    "args": [
      "--directory",
      "parent_of_servers_repo/servers/src/sqlite",
      "run",
      "mcp-server-sqlite",
      "--db-path",
      "~/test.db"
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
      "mcp-test:/mcp",
      "mcp/sqlite",
      "--db-path",
      "/mcp/test.db"
    ]
  }
}
```

## Building

Docker:

```bash
docker build -t mcp/sqlite .
```

## BLS Excel Integration
- The server loads BLS OEWS Excel data at startup (see `reference/bls_all_data_M_2024.xlsx`).
- Query by SOC code or occupation title for wage and employment statistics.
- If the Excel file is missing or fails to load, BLS tools will return a structured error message and log the issue.

## Error Handling and Logging
- All tool calls and handlers use structured error handling and logging (see logs for details).
- Errors are returned as JSON or formatted text, with user-friendly messages and references where possible.
- Critical errors (e.g., missing database or Excel file) are logged and may disable some tools.

## Extensibility and Code Structure
- Modular handler classes for database, Excel, TSA, and job obsolescence logic.
- Configuration and prompt templates are separated for maintainability.
- Easy to add new tools or extend existing logic (see `src/mcp_server_sqlite/`).
- Singleton pattern for BLS Excel handler with reload/reset capability.
- All code is type-annotated and uses modern Python best practices.

## Code Quality, Testing, and Contribution
- All modules use docstrings, type hints, and logging.
- Input validation and error handling are enforced throughout.
- Unit tests are recommended for all handlers and logic modules.
- Contributions are welcome! Please follow code style and add/expand tests for new features.

## License

This MCP server is licensed under the MIT License. This means you are free to use, modify, and distribute the software, subject to the terms and conditions of the MIT License. For more details, please see the LICENSE file in the project repository.
