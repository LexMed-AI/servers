
import logging
from pathlib import Path
import json # For structured JSON output from tools where appropriate

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
from . import ve_logic # Import the module with core logic/formatting
# Assumes prompt templates are moved to a separate file
from . import prompt_templates

# Setup logger for this module
logger = logging.getLogger(__name__)
# Note: Logging level is configured in __init__.py/run()


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

    # Create the MCP Server instance
    server = Server("ve-audit-dot-server") # Specific server name

    # --- Register MCP Handlers ---
    logger.debug("Registering MCP handlers...")

    # --- Resource Handlers ---
    # (Removed - No dynamic resources exposed in this version)

    # --- Prompt Handlers ---
    @server.list_prompts()
    async def handle_list_prompts() -> list[types.Prompt]:
        """Lists the available prompts."""
        logger.debug("Handling list_prompts request")
        # Return definitions matching the actual prompts available
        return [
            types.Prompt(
                name="ve-audit-demo",
                description="Demo: Interactively analyze DOT job data using VE tools.",
                arguments=[
                    types.PromptArgument(
                        name="job_title",
                        description="DOT code or job title to analyze in the demo.",
                        required=True,
                    )
                ],
            ),
            types.Prompt(
                name="ve-transcript-audit",
                description="Instructs AI to act as VE Auditor and analyze a hearing transcript.",
                arguments=[
                    types.PromptArgument( name="hearing_date", description="Date of the hearing (YYYY-MM-DD).", required=True ),
                    types.PromptArgument( name="transcript", description="Full text of the hearing transcript.", required=True ),
                    types.PromptArgument( name="claimant_name", description="Claimant identifier (optional).", required=False, default="Claimant" ),
                ],
            )
        ]

    @server.get_prompt()
    async def handle_get_prompt(name: str, arguments: dict[str, str] | None) -> types.GetPromptResult:
        """Gets the content for a specific prompt using templates."""
        logger.debug(f"Handling get_prompt request for '{name}' with args: {arguments}")
        args = arguments or {}

        if name == "ve-audit-demo":
            if "job_title" not in args:
                logger.error("Missing required argument for ve-audit-demo: job_title")
                raise ValueError("Missing required argument: job_title")
            job_title = args["job_title"]
            # Load template from the dedicated module
            try:
                prompt_text = prompt_templates.PROMPT_TEMPLATE.format(job_title=job_title)
            except AttributeError:
                 logger.error("prompt_templates.PROMPT_TEMPLATE not found or inaccessible.")
                 raise ImportError("Could not load prompt template.")
            except KeyError:
                logger.error("Error formatting PROMPT_TEMPLATE - 'job_title' key missing?")
                raise ValueError("Error formatting demo prompt template.")


            logger.debug(f"Generated prompt 've-audit-demo' for job title: {job_title}")
            return types.GetPromptResult(
                description=f"VE audit demo for {job_title}",
                messages=[types.PromptMessage(role="user", content=types.TextContent(type="text", text=prompt_text.strip()))],
            )

        elif name == "ve-transcript-audit":
            required_args = ["hearing_date", "transcript"]
            missing = [arg for arg in required_args if arg not in args]
            if missing:
                logger.error(f"Missing required arguments for ve-transcript-audit: {missing}")
                raise ValueError(f"Missing required arguments: {missing}")

            # Load template from the dedicated module
            try:
                prompt_text = prompt_templates.VE_AUDITOR_PROMPT.format(
                    hearing_date=args["hearing_date"],
                    # Let the LLM determine applicable SSR based on date within the prompt's instructions
                    applicable_ssr="To be determined based on hearing date",
                    claimant_name=args.get("claimant_name", "Claimant"),
                    transcript=args["transcript"]
                )
            except AttributeError:
                 logger.error("prompt_templates.VE_AUDITOR_PROMPT not found or inaccessible.")
                 raise ImportError("Could not load prompt template.")
            except KeyError as e:
                logger.error(f"Error formatting VE_AUDITOR_PROMPT - missing key? {e}")
                raise ValueError("Error formatting transcript audit prompt template.")

            logger.debug(f"Generated prompt 've-transcript-audit' for claimant: {args.get('claimant_name', 'Claimant')}")
            return types.GetPromptResult(
                description=f"VE transcript audit for {args.get('claimant_name', 'Claimant')}",
                messages=[types.PromptMessage(role="user", content=types.TextContent(type="text", text=prompt_text.strip()))],
            )

        else:
            logger.error(f"Unknown prompt requested: {name}")
            raise ValueError(f"Unknown prompt: {name}")

    # --- Tool Handlers ---
    @server.list_tools()
    async def handle_list_tools() -> list[types.Tool]:
        """Lists the available tools relevant to VE analysis."""
        logger.debug("Handling list_tools request")
        return [
            # Core VE Analysis Tools
            types.Tool(
                name="generate_job_report",
                description="Generate a comprehensive formatted text report of job requirements (Exertion, SVP, GED, Physical Demands, Environment, etc.) for a specific DOT code or job title.",
                inputSchema={ "type": "object", "properties": { "search_term": {"type": "string", "description": "DOT code (e.g., '209.587-034') or job title (e.g., 'Marker') to search for."}}, "required": ["search_term"]},
            ),
            types.Tool(
                name="check_job_obsolescence",
                description="Check if a specific DOT job is potentially obsolete based on available indicators and SSA guidance (e.g., EM-24027 REV). Returns JSON.",
                inputSchema={ "type": "object", "properties": { "dot_code": {"type": "string", "description": "DOT code (e.g., '209.587-034') to analyze."}},"required": ["dot_code"]},
            ),
            types.Tool(
                name="analyze_transferable_skills",
                description="Performs a preliminary Transferable Skills Analysis (TSA) based on PRW, RFC, age, and education per SSA guidelines. Returns JSON. **Note:** Placeholder implementation requiring full SSA rules.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "source_dot": {"type": "string", "description": "DOT code of the Past Relevant Work (PRW)."},
                        "residual_capacity": {"type": "string", "description": "Claimant's RFC level (e.g., SEDENTARY, LIGHT)."},
                        "age": {"type": "string", "description": "Claimant's age category (e.g., ADVANCED AGE)."},
                        "education": {"type": "string", "description": "Claimant's education category (e.g., HIGH SCHOOL)."},
                        "target_dots": {"type": "array", "items": {"type": "string"}, "description": "Optional: Specific target DOT codes suggested by VE."},
                    },
                    "required": ["source_dot", "residual_capacity", "age", "education"]
                }
            ),
            # Database Utility Tools
            types.Tool(
                name="read_query",
                description="Execute a read-only SELECT query directly on the DOT SQLite database. Returns JSON.",
                inputSchema={"type": "object", "properties": {"query": {"type": "string", "description": "SELECT SQL query."}},"required": ["query"]},
            ),
            types.Tool(
                name="list_tables",
                description="List all tables available in the DOT SQLite database. Returns JSON.",
                inputSchema={"type": "object", "properties": {}},
            ),
            types.Tool(
                name="describe_table",
                description="Get the column schema for a specific table in the DOT database. Returns JSON.",
                inputSchema={"type": "object", "properties": {"table_name": {"type": "string", "description": "Name of the table (e.g., 'DOT')."}},"required": ["table_name"]},
            ),
            # Removed: append_analysis, write_query, create_table
        ]

    @server.call_tool()
    async def handle_call_tool(
        name: str, arguments: dict[str, Any] | None
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        """
        Handle tool execution requests by dispatching to appropriate modules.
        """
        logger.info(f"Tool call received: {name} with args: {arguments}")
        args = arguments or {} # Ensure args is a dict, even if None

        try:
            # --- Dispatch based on tool name ---
            # Note: Using synchronous calls for db_handler/ve_logic for now.
            # If they become async internally (e.g., using aiosqlite), add 'await'.
            # The perform_tsa_analysis is marked async just in case.

            if name == "list_tables":
                results = db.list_all_tables() # Call db_handler method
                return [types.TextContent(type="text", text=json.dumps(results, indent=2))]

            elif name == "describe_table":
                if "table_name" not in args: raise ValueError("Missing required argument: table_name")
                results = db.describe_table_schema(args['table_name']) # Call db_handler method
                return [types.TextContent(type="text", text=json.dumps(results, indent=2))]

            elif name == "read_query":
                 if "query" not in args: raise ValueError("Missing required argument: query")
                 # Safety check already in db_handler.execute_select_query, but good practice here too
                 query_text = args['query'].strip()
                 if not query_text.upper().startswith("SELECT"):
                     raise ValueError("Only SELECT queries are allowed for read_query")
                 results = db.execute_select_query(query_text) # Call db_handler method
                 return [types.TextContent(type="text", text=json.dumps(results, indent=2))]

            elif name == "check_job_obsolescence":
                if "dot_code" not in args: raise ValueError("Missing required argument: dot_code")
                # Call ve_logic function
                results_dict = ve_logic.assess_job_obsolescence_detailed(args["dot_code"])
                return [types.TextContent(type="text", text=json.dumps(results_dict, indent=2))]

            elif name == "analyze_transferable_skills":
                 required_tsa_args = ["source_dot", "residual_capacity", "age", "education"]
                 missing = [arg for arg in required_tsa_args if arg not in args]
                 if missing: raise ValueError(f"Missing required arguments for TSA: {missing}")
                 # Call ve_logic async function, passing db instance
                 results_dict = await ve_logic.perform_tsa_analysis(
                     db_handler=db,
                     source_dot_code=args["source_dot"],
                     rfc_strength=args["residual_capacity"],
                     age_category=args["age"],
                     education_level=args["education"],
                     target_dot_codes=args.get("target_dots")
                 )
                 return [types.TextContent(type="text", text=json.dumps(results_dict, indent=2))]

            elif name == "generate_job_report":
                if "search_term" not in args: raise ValueError("Missing required argument: search_term")
                search_term = args['search_term'].strip()
                # 1. Get raw data using db_handler (returns list, expect 0 or 1 item)
                job_data_list = db.find_job_data(search_term)
                if not job_data_list:
                    # Return text content indicating not found
                    return [types.TextContent(type="text", text=f"No matching jobs found for search term: '{search_term}'.")]
                # 2. Format data using ve_logic function (returns formatted string)
                report_text = ve_logic.generate_formatted_job_report(job_data_list[0]) # Pass the job data dict
                return [types.TextContent(type="text", text=report_text)]

            else:
                logger.error(f"Unknown tool called: {name}")
                raise ValueError(f"Unknown tool: {name}")

        # --- Error Handling ---
        except ValueError as e: # Catch argument validation or other specific value errors
             logger.error(f"ValueError calling tool '{name}': {e}", exc_info=True)
             return [types.TextContent(type="text", text=f"Tool Error ({name}): Invalid input or value. {str(e)}")]
        except FileNotFoundError as e: # Catch errors like missing DB or SQL file
             logger.critical(f"FileNotFoundError calling tool '{name}': {e}", exc_info=True)
             return [types.TextContent(type="text", text=f"Server Configuration Error: Required file not found. {str(e)}")]
        # Catch database errors raised from db_handler
        # Note: Catching the base sqlite3.Error might require importing sqlite3 again,
        # or rely on db_handler wrapping errors in a custom exception, or catch general Exception.
        # For now, catch general Exception for DB errors propagating up.
        except Exception as e:
            # Catch-all for unexpected errors in db_handler or ve_logic
            logger.exception(f"Unexpected error calling tool '{name}'") # Log full traceback
            # Return generic error message consistent with schema (TextContent)
            return [types.TextContent(type="text", text=f"Unexpected server error processing tool '{name}'. Check server logs for details.")]


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