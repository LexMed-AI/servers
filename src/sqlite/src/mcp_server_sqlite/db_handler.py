import sqlite3
import logging
import time # For profiling
import functools # For wraps decorator if needed (using simple wrapper function here)
from contextlib import closing
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Callable # Added Callable

# Import analysis utils for validation
from . import analysis_utils

# Get a logger for this module
logger = logging.getLogger(__name__)

# Define the expected location relative to this file
_REPORT_QUERY_SQL_PATH = Path(__file__).parent / "report_query.sql"

class DatabaseHandler:
    """Manages connection and queries to the DOT SQLite database."""

    def __init__(self, db_path: Path):
        """
        Initializes the DatabaseHandler.

        Args:
            db_path: A pathlib.Path object pointing to the SQLite database file.
        """
        if not isinstance(db_path, Path):
            db_path = Path(db_path)

        self.db_path = db_path.resolve()
        self._query_stats: Dict[str, Dict[str, Union[int, float]]] = {} # For profiling stats
        self._valid_dot_columns: Optional[List[str]] = None # Cache for filter_jobs validation

        try:
            if not self.db_path.is_file():
                 raise FileNotFoundError(f"Database file not found on init: {self.db_path}")
            self._ensure_indices() # Attempt to ensure indices exist
            logger.info(f"DatabaseHandler initialized for database: {self.db_path}")
        except (FileNotFoundError, sqlite3.Error) as e:
             logger.critical(f"Failed to initialize DatabaseHandler for {self.db_path}: {e}", exc_info=True)
             raise

    def _ensure_indices(self):
        """
        Ensures necessary indices exist in the database for performance.
        Uses CREATE INDEX IF NOT EXISTS. Focuses on columns used in common WHERE clauses.
        Includes index on CAST(Code AS TEXT) to support text searches on the REAL Code column.
        """
        indices = {
            "idx_dot_title": "CREATE INDEX IF NOT EXISTS idx_dot_title ON DOT (Title);",
            "idx_dot_completetitle": "CREATE INDEX IF NOT EXISTS idx_dot_completetitle ON DOT (CompleteTitle);",
            "idx_dot_code_text": "CREATE INDEX IF NOT EXISTS idx_dot_code_text ON DOT (CAST(Code AS TEXT));"
        }
        logger.debug("Ensuring database indices exist...")
        try:
            with closing(sqlite3.connect(self.db_path, timeout=5)) as conn:
                with closing(conn.cursor()) as cursor:
                    cursor.execute("PRAGMA table_info(DOT);")
                    columns_info = cursor.fetchall()
                    is_ncode_pk = any(col[1] == 'Ncode' and col[5] == 1 for col in columns_info)

                    if not is_ncode_pk:
                        logger.warning("Ncode is not the Primary Key! Creating index.")
                        indices["idx_dot_ncode"] = "CREATE INDEX IF NOT EXISTS idx_dot_ncode ON DOT (Ncode);"
                    else:
                        logger.debug("Ncode appears to be Primary Key (already indexed).")

                    for idx_name, sql in indices.items():
                        logger.debug(f"Applying index check: {idx_name}")
                        cursor.execute(sql)
                conn.commit()
            logger.debug("Database indices check/application complete.")
        except sqlite3.OperationalError as oe:
             if "index on expression" in str(oe):
                 logger.warning(f"Could not create index on expression (CAST(Code AS TEXT)): {oe}. Text searches on 'Code' column may be slow. Consider updating SQLite.")
             else:
                 logger.error(f"Database OperationalError while ensuring indices: {oe}", exc_info=True)
        except sqlite3.Error as e:
            logger.error(f"Failed to ensure database indices: {e}", exc_info=True)

    def _execute_query(self, query: str, params: Union[Dict[str, Any], List[Any], None] = None) -> List[Dict[str, Any]]:
        """
        Internal helper to execute a SQL query and return results. Handles connection management.
        (Profiled via _profile_query wrapper if log level is DEBUG)
        """
        # Profiling is applied to the public methods calling this,
        # or could be applied directly here if desired. Let's keep it on public methods.
        logger.debug(f"Executing query (params: {params}): {query[:300]}...")
        if not self.db_path.is_file():
             logger.error(f"Database file check failed in _execute_query: {self.db_path}")
             raise FileNotFoundError(f"Database file not found: {self.db_path}")

        conn = None
        try:
            conn = sqlite3.connect(self.db_path, timeout=10)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            is_write_operation = query.strip().upper().startswith(
                ('INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER', 'REPLACE')
            )

            if is_write_operation:
                conn.commit()
                affected = cursor.rowcount
                results = [{"affected_rows": affected}]
            else:
                results = [dict(row) for row in cursor.fetchall()]

            cursor.close()
            conn.close()
            conn = None # Signal connection was closed successfully
            logger.debug(f"Query executed successfully, {len(results) if not is_write_operation else 'write op'} result(s).")
            return results

        except sqlite3.Error as db_err:
            logger.error(f"Database error: {db_err}\nQuery: {query}\nParams: {params}", exc_info=True)
            raise # Propagate specific DB error
        except Exception as e:
             logger.error(f"Unexpected error during query execution: {e}\nQuery: {query}", exc_info=True)
             raise # Propagate other errors
        finally:
             if conn: # If connection wasn't closed successfully due to error
                 try:
                     conn.close()
                     logger.warning("Database connection closed in finally block after error.")
                 except sqlite3.Error as close_err:
                     logger.error(f"Error closing connection potentially after another error: {close_err}")

    def _clean_dot_code(self, dot_code: str) -> str:
        """Removes non-numeric characters from DOT code string."""
        if not dot_code or not isinstance(dot_code, str):
            return ""
        return ''.join(c for c in dot_code if c.isdigit())

    def _format_dot_code_standard(self, cleaned_numeric_code: str) -> Optional[str]:
         """Formats a cleaned 9-digit numeric string into standard ###.###-### format."""
         if len(cleaned_numeric_code) == 9:
              return f"{cleaned_numeric_code[:3]}.{cleaned_numeric_code[3:6]}-{cleaned_numeric_code[6:9]}"
         return None

    # --- Profiling Helper ---
    def _profile_query(self, query_name: str, query_func: Callable, *args, **kwargs) -> Any:
        """Wraps a function call to profile its execution time."""
        start_time = time.monotonic()
        try:
            result = query_func(*args, **kwargs)
            return result
        except Exception as e:
            # Log error within profile wrapper? Or let it propagate from _execute_query?
            # Let it propagate for now.
            raise
        finally:
            # Always record time, even if error occurred
            duration = time.monotonic() - start_time
            logger.debug(f"Profiled query '{query_name}' completed in {duration:.4f} seconds")

            # Record query stats (simple implementation)
            if query_name not in self._query_stats:
                self._query_stats[query_name] = {
                    'count': 0, 'total_time': 0.0, 'min_time': float('inf'), 'max_time': 0.0, 'errors': 0
                }

            stats = self._query_stats[query_name]
            stats['count'] += 1
            stats['total_time'] += duration
            stats['min_time'] = min(stats['min_time'], duration)
            stats['max_time'] = max(stats['max_time'], duration)
            # Could add error count here if try/except caught Exception e above

    # --- Public Data Access Methods ---

    def list_all_tables(self) -> List[Dict[str, Any]]:
        """Lists all tables in the database. (Profiled if DEBUG)"""
        if logger.isEnabledFor(logging.DEBUG):
            return self._profile_query('list_all_tables', self._list_all_tables_impl)
        else:
            return self._list_all_tables_impl()
    def _list_all_tables_impl(self) -> List[Dict[str, Any]]:
        query = "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"
        return self._execute_query(query)

    def describe_table_schema(self, table_name: str) -> List[Dict[str, Any]]:
        """Gets the schema info for a table. (Profiled if DEBUG)"""
        if logger.isEnabledFor(logging.DEBUG):
            # Note: Need to pass args correctly to wrapper
            return self._profile_query('describe_table_schema', self._describe_table_schema_impl, table_name)
        else:
            return self._describe_table_schema_impl(table_name)
    def _describe_table_schema_impl(self, table_name: str) -> List[Dict[str, Any]]:
        if not table_name.isidentifier():
             raise ValueError(f"Invalid table name specified: {table_name}")
        query = f"PRAGMA table_info({table_name});"
        return self._execute_query(query)

    def get_job_by_code(self, dot_code: str) -> Optional[Dict[str, Any]]:
         """Gets job by DOT code (Ncode or CAST Text). (Profiled if DEBUG)"""
         if logger.isEnabledFor(logging.DEBUG):
              return self._profile_query('get_job_by_code', self._get_job_by_code_impl, dot_code)
         else:
              return self._get_job_by_code_impl(dot_code)
    def _get_job_by_code_impl(self, dot_code: str) -> Optional[Dict[str, Any]]:
         """Implementation for get_job_by_code. Prioritizes formatted code match."""
         if not dot_code: return None
         term = dot_code.strip()

         # 1. Check if the search term is a valid DOT code format
         validation_result = analysis_utils.validate_dot_code_format(term)
         is_valid_dot_format = validation_result.get('is_valid_format', False)

         try:
             # 2a. If valid format, try querying by the formatted string first
             if is_valid_dot_format:
                 logger.debug(f"get_job_by_code: Term '{term}' matches format. Querying by CAST TEXT.")
                 results = self._execute_query("SELECT * FROM DOT WHERE CAST(Code AS TEXT) = ? LIMIT 1;", [term])
                 if results:
                     return results[0]
                 else:
                      logger.debug(f"get_job_by_code: No match found for formatted code '{term}'.")
                      # Optionally fall through to Ncode check even if format matched but no record found?
                      # For now, let's fall through.

             # 2b. If not valid format OR formatted query failed, try cleaning to Ncode
             cleaned_numeric_code = self._clean_dot_code(term)
             if cleaned_numeric_code:
                 try:
                     ncode_value = int(cleaned_numeric_code)
                     logger.debug(f"get_job_by_code: Querying by Ncode {ncode_value}.")
                     results = self._execute_query("SELECT * FROM DOT WHERE Ncode = ? LIMIT 1;", [ncode_value])
                     if results:
                         return results[0]
                     else:
                         logger.debug(f"get_job_by_code: No match found for Ncode {ncode_value}.")
                 except ValueError:
                     logger.warning(f"get_job_by_code: Could not convert cleaned code '{cleaned_numeric_code}' to integer Ncode.")
                     pass # Not purely numeric after cleaning

             # If neither method found a result
             logger.debug(f"get_job_by_code: No match found for input '{dot_code}' using any method.")
             return None

         except sqlite3.Error as e:
            logger.error(f"DB error in _get_job_by_code_impl for '{dot_code}': {e}")
            return None # Return None on DB error

    def find_job_data(self, search_term: str) -> List[Dict[str, Any]]:
        """Finds best single job match. (Profiled if DEBUG)"""
        if logger.isEnabledFor(logging.DEBUG):
            return self._profile_query('find_job_data', self._find_job_data_impl, search_term)
        else:
            return self._find_job_data_impl(search_term)
    def _find_job_data_impl(self, search_term: str) -> List[Dict[str, Any]]:
        """Implementation for find_job_data: Prioritize DOT format match.

        Checks if search_term matches XXX.XXX-XXX format. If yes, searches
        by that exact code first. Otherwise, performs a broader title search.
        """
        term = search_term.strip()
        if not term: return []

        # 1. Check if the search term is a valid DOT code format
        validation_result = analysis_utils.validate_dot_code_format(term)
        is_valid_dot_format = validation_result.get('is_valid_format', False)

        if is_valid_dot_format:
            logger.debug(f"Search term '{term}' matches DOT format. Querying by exact code.")
            # 2a. Query specifically by the formatted DOT code
            dot_query = """
                SELECT
                    Ncode AS dotCodeNumeric,
                    CAST(Code AS TEXT) AS dotCodeFormatted,
                    Title AS jobTitle,
                    Definitions,
                    SVPNum,
                    StrengthNum,
                    -- Add other frequently needed fields explicitly if desired
                    *
                FROM DOT
                WHERE CAST(Code AS TEXT) = ?
                LIMIT 1;
            """
            # Ensure all fields needed by generate_formatted_job_report are selected
            # The '*' will select all, but explicit listing can be safer if schema changes.
            results = self._execute_query(dot_query, [term])
            if results: # Return immediately if exact DOT match found
                logger.debug(f"Found exact match for DOT code '{term}'.")
                return results
            else:
                 # Optional: Log if exact format matched but no DB entry found?
                 logger.debug(f"Search term '{term}' matched DOT format, but no exact DB entry found. Falling back to title search.")
                 # Fall through to title search if exact format yields no result

        # 2b. If not a valid DOT format OR exact format search yielded no results, perform title search
        logger.debug(f"Search term '{term}' does not match DOT format or no exact match found. Querying by title/Ncode.")
        title_query = """
        WITH SearchResults AS (
            SELECT
                *,
                CASE
                    -- Prioritize Ncode match if term happens to be numeric, less likely but possible
                    WHEN Ncode = CAST(REPLACE(REPLACE(?, '.', ''), '-', '') AS INTEGER) THEN 200
                    WHEN Title = ? COLLATE NOCASE THEN 100
                    WHEN CompleteTitle = ? COLLATE NOCASE THEN 90
                    WHEN Title LIKE ? COLLATE NOCASE THEN 70
                    WHEN CompleteTitle LIKE ? COLLATE NOCASE THEN 60
                    ELSE 0
                END as relevance_score
            FROM DOT
            WHERE
                Ncode = CAST(REPLACE(REPLACE(?, '.', ''), '-', '') AS INTEGER)
                OR Title = ? COLLATE NOCASE
                OR CompleteTitle = ? COLLATE NOCASE
                OR Title LIKE ? COLLATE NOCASE
                OR CompleteTitle LIKE ? COLLATE NOCASE
        )
        SELECT
            Ncode AS dotCodeNumeric,
            CAST(Code AS TEXT) AS dotCodeFormatted,
            Title AS jobTitle,
            Definitions,
            SVPNum,
            StrengthNum,
            -- Explicitly list other fields needed by generate_formatted_job_report if not using '*' from CTE
            *
        FROM SearchResults
        WHERE relevance_score > 0
        ORDER BY relevance_score DESC
        LIMIT 1;
        """

        like_pattern = f"%{term}%"
        # Prepare params: term repeated for Ncode (potential), exact titles, LIKE titles
        params = [term] * 5 + [term] * 5
        # Execute the broader title/Ncode search
        return self._execute_query(title_query, params)

    def execute_select_query(self, query: str, params: Optional[List[Any]] = None) -> List[Dict[str, Any]]:
        """Executes provided SELECT query safely. (Profiled if DEBUG)"""
        if logger.isEnabledFor(logging.DEBUG):
             return self._profile_query('execute_select_query', self._execute_select_query_impl, query, params)
        else:
             return self._execute_select_query_impl(query, params)
    def _execute_select_query_impl(self, query: str, params: Optional[List[Any]] = None) -> List[Dict[str, Any]]:
        if not query.strip().upper().startswith("SELECT"):
             raise ValueError("Only SELECT queries are allowed via this method.")
        return self._execute_query(query, params)

    # --- NEW Methods from Suggestions ---

    def get_database_stats(self) -> Dict[str, Any]:
        """Collect statistics about the database. (Profiled if DEBUG)"""
        if logger.isEnabledFor(logging.DEBUG):
             return self._profile_query('get_database_stats', self._get_database_stats_impl)
        else:
             return self._get_database_stats_impl()
    def _get_database_stats_impl(self) -> Dict[str, Any]:
        """Implementation for get_database_stats."""
        stats: Dict[str, Any] = {'error': None}
        start_time = time.monotonic()
        try:
            # Get table counts - handle potential missing tables gracefully
            tables_to_count = ['DOT', 'goedb'] # Add others if relevant
            stats['table_counts'] = {}
            for table in tables_to_count:
                 try:
                     count_res = self._execute_query(f"SELECT COUNT(*) as count FROM {table}")
                     stats['table_counts'][table] = count_res[0]['count'] if count_res else 0
                 except sqlite3.Error as e:
                      logger.warning(f"Could not get count for table '{table}': {e}")
                      stats['table_counts'][table] = 'Error'

            # Get SQLite version
            version_res = self._execute_query("SELECT sqlite_version() as version")
            stats['sqlite_version'] = version_res[0]['version'] if version_res else 'Unknown'

            # Get index information for DOT table
            indices_res = self._execute_query("SELECT name, sql FROM sqlite_master WHERE type='index' AND tbl_name='DOT'")
            stats['dot_indices'] = {row['name']: row['sql'] for row in indices_res} if indices_res else {}

            # Get database size
            try:
                 stats['db_size_bytes'] = self.db_path.stat().st_size
                 stats['db_size_mb'] = round(stats['db_size_bytes'] / (1024 * 1024), 2)
            except OSError as e:
                 logger.warning(f"Could not get database file size: {e}")
                 stats['db_size_bytes'] = 'Error'
                 stats['db_size_mb'] = 'Error'

            # Get query profiling stats if enabled/exist
            if self._query_stats:
                 stats['query_profiling_summary'] = {}
                 for name, data in self._query_stats.items():
                     stats['query_profiling_summary'][name] = {
                         'count': data['count'],
                         'avg_time_ms': round((data['total_time'] / data['count']) * 1000, 2) if data['count'] > 0 else 0,
                         'min_time_ms': round(data['min_time'] * 1000, 2) if data['count'] > 0 else 0,
                         'max_time_ms': round(data['max_time'] * 1000, 2) if data['count'] > 0 else 0
                     }

        except sqlite3.Error as e:
            logger.error(f"Error collecting database statistics: {e}", exc_info=True)
            stats['error'] = f"Database error: {str(e)}"
        except Exception as e:
            logger.error(f"Unexpected error collecting database statistics: {e}", exc_info=True)
            stats['error'] = f"Unexpected error: {str(e)}"

        stats['stats_collection_time_ms'] = round((time.monotonic() - start_time) * 1000, 2)
        return stats

    def _get_valid_dot_columns(self) -> List[str]:
        """Helper to get and cache valid column names for the DOT table."""
        if self._valid_dot_columns is None:
             try:
                 schema = self.describe_table_schema('DOT') # Use existing method
                 self._valid_dot_columns = [col['name'] for col in schema]
             except (ValueError, sqlite3.Error) as e:
                 logger.error(f"Could not retrieve DOT schema to validate columns: {e}")
                 self._valid_dot_columns = [] # Prevent repeated attempts on error
        return self._valid_dot_columns

    def filter_jobs(self, filters: Dict[str, Any], sort_by: str = 'Title',
                    sort_dir: str = 'ASC', limit: int = 100) -> List[Dict[str, Any]]:
        """Filters jobs by various criteria with sorting. (Profiled if DEBUG)"""
        if logger.isEnabledFor(logging.DEBUG):
             return self._profile_query('filter_jobs', self._filter_jobs_impl, filters, sort_by, sort_dir, limit)
        else:
             return self._filter_jobs_impl(filters, sort_by, sort_dir, limit)
    def _filter_jobs_impl(self, filters: Dict[str, Any], sort_by: str = 'Title',
                         sort_dir: str = 'ASC', limit: int = 100) -> List[Dict[str, Any]]:
        """Implementation for filter_jobs."""
        valid_columns = self._get_valid_dot_columns()
        if not valid_columns:
             # Handle case where we couldn't get schema - maybe raise error or return empty?
             logger.error("Cannot filter jobs: Failed to retrieve valid column names for DOT table.")
             raise ValueError("Could not validate columns for filtering.")

        # Validate sort direction
        sort_dir_upper = sort_dir.upper()
        if sort_dir_upper not in ('ASC', 'DESC'):
            logger.warning(f"Invalid sort direction '{sort_dir}', defaulting to ASC.")
            sort_dir_upper = 'ASC'

        # Validate sort column (prevent injection)
        if sort_by not in valid_columns:
            logger.warning(f"Invalid sort column '{sort_by}', defaulting to 'Title'.")
            sort_by_validated = 'Title' # Default safely
        else:
             sort_by_validated = sort_by # Use original if valid

        # Build WHERE clause dynamically and safely based on filters
        where_clauses = []
        params = []
        invalid_filters = []

        for key, value in filters.items():
            if key in valid_columns:
                # Use placeholder for value to prevent SQL injection
                where_clauses.append(f"\"{key}\" = ?") # Quote column name for safety if needed
                params.append(value)
            else:
                 invalid_filters.append(key)

        if invalid_filters:
             logger.warning(f"Ignoring invalid filter keys: {invalid_filters}")

        # Build the final query
        query = f"SELECT * FROM DOT" # Select all columns for now
        if where_clauses:
            query += f" WHERE {' AND '.join(where_clauses)}"

        # Add ORDER BY and LIMIT clauses - ensure validated column name and direction are used
        # Use placeholder for LIMIT value
        query += f" ORDER BY \"{sort_by_validated}\" COLLATE NOCASE {sort_dir_upper} LIMIT ?" # Add COLLATE NOCASE for text sort
        params.append(limit)

        # Execute the constructed query
        return self._execute_query(query, params)

    def batch_get_jobs_by_codes(self, dot_codes: List[str]) -> List[Dict[str, Any]]:
        """Get multiple jobs by their DOT codes (formatted XXX.XXX-XXX) in a single query."""
        if not dot_codes:
            return []

        # Filter out any potentially invalid/empty codes before creating placeholders
        valid_formatted_codes = [code for code in dot_codes if analysis_utils.validate_dot_code_format(code).get('is_valid_format')]

        if not valid_formatted_codes:
             logger.warning("batch_get_jobs_by_codes: No valid formatted DOT codes provided in the list.")
             return []

        placeholders = ','.join('?' * len(valid_formatted_codes))
        # Correctly compare against the text representation of the Code column
        query = f"SELECT * FROM DOT WHERE CAST(Code AS TEXT) IN ({placeholders})"
        logger.debug(f"Executing batch_get_jobs_by_codes with {len(valid_formatted_codes)} codes.")
        return self._execute_query(query, valid_formatted_codes)
