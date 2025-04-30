import logging
from pathlib import Path
import json # For structured JSON output from tools where appropriate
import sqlite3

# MCP SDK Imports
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
import mcp.server.stdio

# Pydantic and Typing
from pydantic import AnyUrl # Although not used if memo resource removed
from typing import Any, Dict, List, Optional, Union

# Local module imports for refactored logic
from .db_handler import DatabaseHandler # Import the handler class
from . import ve_logic, tsa_logic # Import the modules with core logic/formatting
# Import the specific prompt module needed
from .prompt_library import ve_audit_MCP_rag # Changed import
from .excel_handler import BLSExcelHandler # Import the Excel handler
from .job_obsolescence import check_job_obsolescence # Import the new function

# Setup logger for this module
logger = logging.getLogger(__name__)
# Note: Logging level is configured in __init__.py/run()

# Define tool configurations (place this perhaps before the server initialization)
TOOL_DEFINITIONS = [
    # Core VE Analysis Tools
    {
        "name": "generate_job_report",
        "description": "Generate a comprehensive formatted text report of job requirements (Exertion, SVP, GED, Physical Demands, Environment, etc.) for a specific DOT code or job title.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "search_term": {
                    "type": "string",
                    "description": "DOT code (format: XXX.XXX-XXX, e.g., '209.587-034') or job title (e.g., 'Marker') to search for."
                }
            },
            "required": ["search_term"],
        },
    },
    {
        "name": "check_job_obsolescence",
        "description": "Check if a specific DOT job is potentially obsolete based on available indicators and SSA guidance (e.g., EM-24027 REV). Returns JSON.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "dot_code": {
                    "type": "string",
                    "description": "DOT code (format: XXX.XXX-XXX, e.g., '209.587-034') to analyze."
                }
            },
            "required": ["dot_code"],
        },
    },
    {
        "name": "analyze_transferable_skills",
        "description": "Performs a preliminary Transferable Skills Analysis (TSA) based on PRW, RFC, age, and education per SSA guidelines. Returns JSON. **Note:** Placeholder implementation requiring full SSA rules.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "source_dot": {"type": "string", "description": "DOT code (format: XXX.XXX-XXX) of the Past Relevant Work (PRW)."},
                "residual_capacity": {"type": "string", "description": "Claimant's RFC level (e.g., SEDENTARY, LIGHT)."},
                "age": {"type": "string", "description": "Claimant's age category (e.g., ADVANCED AGE)."},
                "education": {"type": "string", "description": "Claimant's education category (e.g., HIGH SCHOOL)."},
                "target_dots": {"type": "array", "items": {"type": "string"}, "description": "Optional: Specific target DOT codes (format: XXX.XXX-XXX) suggested by VE."},
            },
            "required": ["source_dot", "residual_capacity", "age", "education"],
        },
    },
    # Database Utility Tools
    {
        "name": "read_query",
        "description": "Execute a read-only SELECT query directly on the DOT SQLite database. Returns JSON.",
        "inputSchema": {"type": "object", "properties": {"query": {"type": "string", "description": "SELECT SQL query."}}, "required": ["query"]},
    },
    {
        "name": "list_tables",
        "description": "List all tables available in the DOT SQLite database. Returns JSON.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "describe_table",
        "description": "Get the column schema for a specific table in the DOT database. Returns JSON.",
        "inputSchema": {"type": "object", "properties": {"table_name": {"type": "string", "description": "Name of the table (e.g., 'DOT')."}}, "required": ["table_name"]},
    },
    # BLS Excel Tools
    {
        "name": "analyze_bls_excel",
        "description": "Check the status of the loaded BLS Excel data handler and show basic info (e.g., first few rows).",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "query_bls_by_soc",
        "description": "Query BLS occupation data by SOC (Standard Occupational Classification) code. Returns wage and employment data.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "soc_code": {"type": "string", "description": "SOC code to search for (e.g., '15-1252')"}
            },
            "required": ["soc_code"],
        },
    },
    {
        "name": "query_bls_by_title",
        "description": "Search BLS occupation data by job title (partial match). Returns wage and employment data for matching occupations.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Occupation title to search for (e.g., 'Software')"}
            },
            "required": ["title"],
        },
    },
    # File writing tool
    {
        "name": "write_file",
        "description": "Write provided content to a specified file within the allowed project directory structure. Creates directories if needed.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Directory path relative to the project root where the file should be saved (e.g., 'audits/completed'). Slashes will be normalized."
                },
                "filename": {
                    "type": "string",
                    "description": "Name of the file to create (e.g., '2024-01-15_audit_smith.md')."
                },
                "content": {
                    "type": "string",
                    "description": "The text content to write into the file."
                }
            },
            "required": ["path", "filename", "content"],
        },
    },
    # Removed tools are implicitly handled by not being in this list
]


async def main(db_path: Path):
    """
    Main asynchronous function to initialize and run the MCP server.

    Args:
        db_path: A pathlib.Path object pointing to the validated SQLite database file.
    """
    logger.info(f"Initializing MCP Server with DB path: {db_path}")

    try:
        # Instantiate the database handler (ensure it's ready)
        db = DatabaseHandler(db_path)
        logger.info("DatabaseHandler initialized successfully.")
    except FileNotFoundError as e:
         logger.critical(f"Database file not found during DatabaseHandler init: {e}", exc_info=True)
         return # Stop if DB cannot be initialized
    except Exception as e:
        logger.critical(f"Failed to initialize DatabaseHandler: {e}", exc_info=True)
        # Cannot proceed without the database handler
        return

    # --- Initialize BLS Excel Handler ---
    # Use absolute path for robustness when launched externally
    # excel_file_path = Path('/Users/COLEMAN/Documents/GitHub/servers/src/sqlite/src/mcp_server_sqlite/reference_json/bls_all_data_M_2024.xlsx') # Old absolute path
    # Construct path relative to this server.py file
    excel_file_path = Path(__file__).parent / "DOTSOCBLS_Excel" / "bls_all_data_M_2024.xlsx"
    try:
        bls_handler = BLSExcelHandler.get_instance(excel_file_path) # Use get_instance for singleton
        logger.info("BLSExcelHandler initialized successfully.")
    except FileNotFoundError as e:
        logger.warning(f"BLS Excel file not found: {e}. BLS tools will be unavailable.")
        bls_handler = None  # Server will still run, but BLS tools won't work
    except Exception as e:
        logger.error(f"Error initializing BLSExcelHandler: {e}. BLS tools will be unavailable.")
        bls_handler = None  # Server will still run, but BLS tools won't work

    # Create the MCP Server instance
    server = Server("ve-audit-dot-server") # Specific server name

    # --- Register MCP Handlers ---
    logger.debug("Registering MCP handlers...")

    # --- Resource Handlers ---
    # (Removed - No dynamic resources exposed in this version)

    # --- Prompt Handlers --- (Restored for Claude Desktop compatibility)
    @server.list_prompts()
    async def handle_list_prompts() -> list[types.Prompt]:
        """Lists the available prompts."""
        logger.debug("Handling list_prompts request")
        # Only list the single prompt we support
        return [
            types.Prompt(
                name="ve-transcript-audit", # The only supported prompt
                description="Instructs AI to act as VE Auditor and analyze a hearing transcript using the ve_audit_MCP_rag template.",
                arguments=[
                    types.PromptArgument( name="hearing_date", description="Date of the hearing (YYYY-MM-DD).", required=True ),
                    types.PromptArgument( name="transcript", description="Full text of the hearing transcript.", required=True ),
                    types.PromptArgument( name="claimant_name", description="Claimant identifier (optional).", required=False, default="Claimant" ),
                ],
            )
        ]

    @server.get_prompt()
    async def handle_get_prompt(name: str, arguments: dict[str, str] | None) -> types.GetPromptResult:
        """Gets the content for the ve-transcript-audit prompt."""
        logger.debug(f"Handling get_prompt request for '{name}' with args: {arguments}")
        args = arguments or {}

        # Only handle the one supported prompt
        if name == "ve-transcript-audit":
            required_args = ["hearing_date", "transcript"]
            missing = [arg for arg in required_args if arg not in args]
            if missing:
                logger.error(f"Missing required arguments for ve-transcript-audit: {missing}")
                raise ValueError(f"Missing required arguments: {missing}")

            # Load template from the specific imported module
            try:
                prompt_text = ve_audit_MCP_rag.PROMPT_TEMPLATE.format(
                    hearing_date=args["hearing_date"],
                    # Assuming the template handles this logic internally or via LLM instruction
                    applicable_ssr="To be determined based on hearing date",
                    claimant_name=args.get("claimant_name", "Claimant"),
                    transcript=args["transcript"]
                )
            except AttributeError:
                 # This would mean PROMPT_TEMPLATE isn't defined in ve_audit_MCP_rag.py
                 logger.error("ve_audit_MCP_rag.PROMPT_TEMPLATE not found or inaccessible.")
                 raise ImportError("Could not load the specified prompt template.")
            except KeyError as e:
                logger.error(f"Error formatting ve_audit_MCP_rag.PROMPT_TEMPLATE - missing key? {e}")
                raise ValueError("Error formatting transcript audit prompt template.")

            logger.debug(f"Generated prompt 've-transcript-audit' for claimant: {args.get('claimant_name', 'Claimant')}")
            return types.GetPromptResult(
                description=f"VE transcript audit for {args.get('claimant_name', 'Claimant')}",
                messages=[types.PromptMessage(role="user", content=types.TextContent(type="text", text=prompt_text.strip()))],
            )

        else:
            # Reject requests for any other prompt name
            logger.error(f"Unknown or unsupported prompt requested: {name}")
            raise ValueError(f"Unknown or unsupported prompt: {name}")

    # --- Tool Handlers ---
    @server.list_tools()
    async def handle_list_tools() -> list[types.Tool]:
        """Lists the available tools relevant to VE analysis."""
        logger.debug("Handling list_tools request")
        # Generate Tool objects dynamically from the configuration list
        return [
            types.Tool(
                name=tool_def["name"],
                description=tool_def["description"],
                inputSchema=tool_def["inputSchema"]
            )
            for tool_def in TOOL_DEFINITIONS
        ]

    # --- Tool Dispatch Handlers ---
    async def tool_list_tables(args, db, **kwargs):
        results = db.list_all_tables()
        return [types.TextContent(type="text", text=json.dumps(results, indent=2))]

    async def tool_describe_table(args, db, **kwargs):
        if "table_name" not in args: raise ValueError("Missing required argument: table_name")
        results = db.describe_table_schema(args['table_name'])
        return [types.TextContent(type="text", text=json.dumps(results, indent=2))]

    async def tool_read_query(args, db, **kwargs):
        if "query" not in args: raise ValueError("Missing required argument: query")
        query_text = args['query'].strip()
        if not query_text.upper().startswith("SELECT"):
            raise ValueError("Only SELECT queries are allowed for read_query")
        results = db.execute_select_query(query_text)
        return [types.TextContent(type="text", text=json.dumps(results, indent=2))]

    async def tool_check_job_obsolescence(args, **kwargs):
        if "dot_code" not in args: raise ValueError("Missing required argument: dot_code")
        results_dict = check_job_obsolescence(args["dot_code"])
        return [types.TextContent(type="text", text=json.dumps(results_dict, indent=2))]

    async def tool_analyze_transferable_skills(args, db, **kwargs):
        required_tsa_args = ["source_dot", "residual_capacity", "age", "education"]
        missing = [arg for arg in required_tsa_args if arg not in args]
        if missing: raise ValueError(f"Missing required arguments for TSA: {missing}")
        results_dict = await tsa_logic.perform_tsa_analysis(
            db_handler=db,
            source_dot_code=args["source_dot"],
            rfc_strength=args["residual_capacity"],
            age_category=args["age"],
            education_level=args["education"],
            target_dot_codes=args.get("target_dots")
        )
        return [types.TextContent(type="text", text=json.dumps(results_dict, indent=2))]

    async def tool_generate_job_report(args, db, **kwargs):
        if "search_term" not in args: raise ValueError("Missing required argument: search_term")
        search_term = args['search_term'].strip()
        
        logger.debug(f"generate_job_report searching for: '{search_term}'")
        
        # First try to find by code - prioritize Ncode search for numerical codes
        job_data = None
        
        # Try using clean_dot_code if it appears to be a DOT code
        from .generate_job_report import clean_dot_code, get_job_data
        
        try:
            # Use the more robust get_job_data function from generate_job_report.py
            job_data = get_job_data(db, search_term)
            
            if job_data:
                logger.debug(f"Found job data for '{search_term}' using get_job_data function")
                try:
                    report_text = ve_logic.generate_formatted_job_report(job_data)
                    return [types.TextContent(type="text", text=report_text)]
                except Exception as format_err:
                    logger.error(f"Error formatting job report for '{search_term}': {format_err}", exc_info=True)
                    return [types.TextContent(type="text", text=f"Found job data for '{search_term}' but encountered an error formatting the report: {str(format_err)}")]
            
            # If get_job_data fails, fall back to the original method
            job_data_list = db.find_job_data(search_term)
            if job_data_list:
                logger.debug(f"Found job data for '{search_term}' using find_job_data function")
                try:
                    report_text = ve_logic.generate_formatted_job_report(job_data_list[0])
                    return [types.TextContent(type="text", text=report_text)]
                except Exception as format_err:
                    logger.error(f"Error formatting job report for '{search_term}' using find_job_data results: {format_err}", exc_info=True)
                    return [types.TextContent(type="text", text=f"Found job data for '{search_term}' but encountered an error formatting the report: {str(format_err)}")]
                
            # No results found through any method
            logger.info(f"No job data found for search term: '{search_term}'")
            return [types.TextContent(type="text", text=f"No matching jobs found for search term: '{search_term}'.")]
        except Exception as e:
            # Provide more detailed error message and include error type
            error_type = type(e).__name__
            error_msg = str(e)
            
            logger.error(f"Error in generate_job_report for '{search_term}': {error_type} - {error_msg}", exc_info=True)
            return [types.TextContent(type="text", text=f"Error generating job report for '{search_term}': {error_type} - {error_msg}")]

    async def tool_analyze_bls_excel(args, bls_handler, **kwargs):
        if bls_handler is None:
            return [types.TextContent(type="text", text=json.dumps({
                "status": "Error",
                "message": "BLS Excel handler failed to initialize. Check server logs."
            }, indent=2))]
        try:
            if bls_handler.dataframe is not None:
                head_rows = bls_handler.dataframe.head(5).to_dict(orient='records')
                column_info = {col: bls_handler.get_field_description(col) for col in bls_handler.dataframe.columns}
                result = {
                    "status": "Success",
                    "total_rows": len(bls_handler.dataframe),
                    "columns": list(bls_handler.dataframe.columns),
                    "field_descriptions": column_info,
                    "sample_rows": head_rows
                }
                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
            else:
                return [types.TextContent(type="text", text=json.dumps({
                    "status": "Error",
                    "message": "BLS DataFrame is not loaded within the handler."
                }, indent=2))]
        except Exception as e:
            logger.error(f"Error accessing BLS handler info: {e}", exc_info=True)
            return [types.TextContent(type="text", text=json.dumps({
                "status": "Error",
                "message": f"Failed to retrieve info from BLS handler: {str(e)}"
            }, indent=2))]

    async def tool_query_bls_by_soc(args, bls_handler, **kwargs):
        if bls_handler is None:
            return [types.TextContent(type="text", text=json.dumps({
                "error": "BLS Excel handler is not available. Check server logs."
            }, indent=2))]
        if "soc_code" not in args: raise ValueError("Missing required argument: soc_code")
        soc_code = args["soc_code"]
        try:
            result = bls_handler.query_by_soc_code(soc_code)
            if result is None:
                return [types.TextContent(type="text", text=json.dumps({
                    "message": f"No BLS data found for SOC code: {soc_code}"
                }, indent=2))]
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
        except Exception as e:
            logger.error(f"Error querying BLS data by SOC code '{soc_code}': {e}", exc_info=True)
            return [types.TextContent(type="text", text=json.dumps({
                "error": f"Failed to query BLS data by SOC: {str(e)}"
            }, indent=2))]

    async def tool_query_bls_by_title(args, bls_handler, **kwargs):
        if bls_handler is None:
            return [types.TextContent(type="text", text=json.dumps({
                "error": "BLS Excel handler is not available. Check server logs."
            }, indent=2))]
        if "title" not in args: raise ValueError("Missing required argument: title")
        title = args["title"]
        try:
            results = bls_handler.query_by_occupation_title(title)
            return [types.TextContent(type="text", text=json.dumps({
                "query": title,
                "count": len(results),
                "results": results
            }, indent=2))]
        except Exception as e:
            logger.error(f"Error querying BLS data by title '{title}': {e}", exc_info=True)
            return [types.TextContent(type="text", text=json.dumps({
                "error": f"Failed to query BLS data by title: {str(e)}"
            }, indent=2))]

    async def tool_write_file(args, **kwargs):
        """Handles writing content to a file within the project."""
        required_args = ["path", "filename", "content"]
        missing = [arg for arg in required_args if arg not in args]
        if missing:
            raise ValueError(f"Missing required arguments for write_file: {missing}")

        relative_path_str = args["path"]
        filename = args["filename"]
        content = args["content"]

        # Basic sanitization/validation (can be enhanced)
        if ".." in relative_path_str or ".." in filename:
            logger.error("Attempted file write with invalid path traversal ('..').")
            raise ValueError("Invalid path or filename containing '..'.")
        if not filename:
             raise ValueError("Filename cannot be empty.")

        try:
            # Assume workspace_root is the directory containing the 'src' folder
            # For this project structure, it seems to be /Users/COLEMAN/Documents/GitHub/servers
            # A more robust solution might get this from an environment variable or config
            workspace_root = Path(__file__).parent.parent.parent # Go up three levels from server.py
            
            # Resolve the target path relative to the workspace root
            target_dir = workspace_root / Path(relative_path_str)
            target_file = target_dir / filename

            # Security Check (Example): Ensure we are writing within the workspace
            # This prevents writing to arbitrary locations like /etc/passwd
            # You might want more specific allowed directories.
            if not target_file.resolve().is_relative_to(workspace_root.resolve()):
                 logger.error(f"Attempted to write file outside workspace: {target_file}")
                 raise ValueError("Target path is outside the allowed workspace.")

            # Create parent directories if they don't exist
            target_dir.mkdir(parents=True, exist_ok=True)

            # Write the file
            target_file.write_text(content, encoding='utf-8')
            logger.info(f"Successfully wrote file: {target_file}")
            
            return [types.TextContent(type="text", text=json.dumps({
                "status": "Success",
                "message": f"File written successfully to {target_file.relative_to(workspace_root)}"
            }, indent=2))]
        
        except OSError as e:
            logger.error(f"OS error writing file {target_file}: {e}", exc_info=True)
            raise ValueError(f"Failed to write file due to OS error: {e.strerror}")
        except Exception as e:
            logger.error(f"Unexpected error writing file {target_file}: {e}", exc_info=True)
            raise ValueError(f"An unexpected error occurred while writing the file: {str(e)}")

    TOOL_DISPATCH = {
        "list_tables": tool_list_tables,
        "describe_table": tool_describe_table,
        "read_query": tool_read_query,
        "check_job_obsolescence": tool_check_job_obsolescence,
        "analyze_transferable_skills": tool_analyze_transferable_skills,
        "generate_job_report": tool_generate_job_report,
        "analyze_bls_excel": tool_analyze_bls_excel,
        "query_bls_by_soc": tool_query_bls_by_soc,
        "query_bls_by_title": tool_query_bls_by_title,
        "write_file": tool_write_file,
    }

    @server.call_tool()
    async def handle_call_tool(
        name: str, arguments: dict[str, Any] | None
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        """
        Handle tool execution requests by dispatching to appropriate modules.
        """
        logger.info(f"Tool call received: {name} with args: {arguments}")
        args = arguments or {}
        try:
            handler = TOOL_DISPATCH.get(name)
            if not handler:
                logger.error(f"Unknown tool called: {name}")
                raise ValueError(f"Unknown tool: {name}")
            # Pass only the handlers that are needed
            handler_kwargs = {}
            if 'db' in handler.__code__.co_varnames:
                handler_kwargs['db'] = db
            if 'bls_handler' in handler.__code__.co_varnames:
                handler_kwargs['bls_handler'] = bls_handler
            return await handler(args, **handler_kwargs)
        except ValueError as e:
            logger.error(f"ValueError calling tool '{name}': {e}", exc_info=True)
            return [types.TextContent(type="text", text=f"Tool Error ({name}): Invalid input or value. {str(e)}")]
        except FileNotFoundError as e:
            logger.critical(f"FileNotFoundError calling tool '{name}': {e}", exc_info=True)
            return [types.TextContent(type="text", text=f"Server Configuration Error: Required file not found. {str(e)}")]
        except sqlite3.Error as e:
            logger.error(f"Database error calling tool '{name}': {e}", exc_info=True)
            return [types.TextContent(type="text", text=f"Database Error ({name}): {str(e)}")]
        except AttributeError as e:
            logger.error(f"AttributeError calling tool '{name}': {e}", exc_info=True)
            return [types.TextContent(type="text", text=f"Server Logic Error ({name}): Missing attribute or method. {str(e)}")]
        except Exception as e:
            # Get detailed traceback information
            import traceback
            tb_str = traceback.format_exc()
            logger.exception(f"Unexpected error calling tool '{name}':\n{tb_str}")
            
            # Provide a more informative error message
            error_type = type(e).__name__
            error_message = str(e) if str(e) else "No error message available"
            return [types.TextContent(type="text", text=f"Error in {name}: {error_type} - {error_message}\n\nCheck server logs for detailed traceback.")]


    # --- Run the Server using Stdio ---
    logger.info("Attempting to start server with stdio transport...")
    try:
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            logger.info("stdio transport acquired, running server run loop...")
            await server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="ve-audit-dot-server", # Specific name
                    server_version="0.2.0", # Updated version
                    capabilities=server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )
        logger.info("Server run loop finished normally.")
    except Exception as e:
         # Catch errors during server startup/run itself
         logger.critical(f"Failed to start or run stdio server: {e}", exc_info=True)


# No `if __name__ == "__main__":` block needed here.