import sys
import logging
from typing import Dict, Any, Optional, Callable, List
from pathlib import Path
from functools import lru_cache  # Import for caching

# Import the original formatting function name from ve_logic
from .ve_logic import generate_formatted_job_report
# Removed DatabaseHandler import to break circular dependency
# from .db_handler import DatabaseHandler
# Import the moved clean_dot_code utility

# Import from models package
from .models import DotJob, DotCode

# Setup logger for this module
logger = logging.getLogger(__name__)

# Create a QueryFunction type alias for better type hinting
QueryFunction = Callable[[int, str], Optional[Dict[str, Any]]]


# LRU cache with statistics for monitoring performance
class CacheStats:
    """Class to track cache statistics."""

    hits = 0
    misses = 0
    calls = 0

    @classmethod
    def reset(cls):
        """Reset all statistics."""
        cls.hits = 0
        cls.misses = 0
        cls.calls = 0

    @classmethod
    def get_stats(cls) -> Dict[str, Any]:
        """Get current cache statistics."""
        hit_rate = 0 if cls.calls == 0 else (cls.hits / cls.calls) * 100
        return {
            "hits": cls.hits,
            "misses": cls.misses,
            "calls": cls.calls,
            "hit_rate": f"{hit_rate:.2f}%",
        }


def get_job_data(db: Any, search_term: str) -> Optional[Dict[str, Any]]:
    """
    Retrieves job data from the database based on a search term.
    The search term can be:
    - A DOT code in ######### format
    - A DOT code in ###.###-### format
    - A job title or partial title

    Args:
        db: The database handler instance
        search_term: The search term to use (DOT code or job title)

    Returns:
        A dictionary containing the job data if found, None otherwise
    """
    if not search_term or not search_term.strip():
        logger.error("Empty search term provided")
        return None

    try:
        # First try to find by exact code match if it looks like a DOT code
        ncode, code_text = DotCode.clean(search_term)
        if ncode is not None:
            logger.debug(f"Searching DOT code: ncode={ncode}, code_text={code_text}")

            # Create a query function to pass to the cache function
            def query_function(ncode: int, code_text: str) -> Optional[Dict[str, Any]]:
                results = db._execute_query(
                    "SELECT * FROM DOT WHERE Ncode = ? OR CAST(Code AS TEXT) = ? LIMIT 1;",
                    [ncode, code_text],
                )
                return results[0] if results else None

            # Use the cached lookup with the query function
            job_data = cached_get_job_by_code(ncode, code_text, query_function)

            # Log cache statistics periodically
            if CacheStats.calls % 50 == 0:
                logger.info(f"DOT cache stats: {CacheStats.get_stats()}")

            if job_data:
                # job_data is now confirmed Dict[str, Any]
                dot_job_instance = DotJob.from_db_row(
                    job_data
                )  # Expects Dict, returns DotJob
                if dot_job_instance:
                    dot_job_dict = (
                        dot_job_instance.to_dict()
                    )  # Expects DotJob, returns Dict
                    if dot_job_dict is not None:
                        standardized_data = {**job_data, **dot_job_dict}
                        logger.debug(f"Found job data for DOT code {code_text}")
                        return standardized_data
                    else:
                        logger.warning(
                            f"dot_job.to_dict() returned None for {code_text}. Returning raw DB data."
                        )
                        return job_data  # Fallback to job_data if to_dict is None
                else:
                    logger.warning(
                        f"DotJob.from_db_row() returned None for {code_text}. Returning raw DB data."
                    )
                    return job_data  # Fallback if DotJob instance is None

        # If no results or not a DOT code, try finding by job title using find_job_data
        logger.debug(f"Searching by job title: {search_term}")
        results = db.find_job_data(search_term)
        if results:
            # Map the database fields to the expected keys using DotJob model
            job_data_from_list = results[0]
            # job_data_from_list is Dict[str, Any]
            dot_job_instance_title = DotJob.from_db_row(job_data_from_list)
            if dot_job_instance_title:
                dot_job_dict_title = dot_job_instance_title.to_dict()
                if dot_job_dict_title is not None:
                    standardized_data = {**job_data_from_list, **dot_job_dict_title}
                    logger.debug(
                        f"Found job data by title search: {dot_job_instance_title.title}"
                    )
                    return standardized_data
                else:
                    logger.warning(
                        f"dot_job.to_dict() returned None for title search {search_term}. Returning raw DB data."
                    )
                    return job_data_from_list
            else:
                logger.warning(
                    f"DotJob.from_db_row() returned None for title search {search_term}. Returning raw DB data."
                )
                return job_data_from_list

        logger.info(f"No job data found for search term: {search_term}")
        return None
    except Exception as e:
        logger.error(f"Error retrieving job data: {e}", exc_info=True)
        return None


# LRU cache decorator for job data lookups
# This improves performance significantly for repeated queries
@lru_cache(maxsize=100)
def cached_get_job_by_code(
    ncode: int, code_text: str, query_function: QueryFunction
) -> Optional[Dict[str, Any]]:
    """
    Cached version of job lookup by DOT code.
    Uses an LRU cache to avoid repeated database queries for the same codes.

    Args:
        ncode: Numeric code integer
        code_text: Formatted DOT code text
        query_function: Function that accepts ncode and code_text and returns job data

    Returns:
        Job data dictionary if found, None otherwise
    """
    # Update call statistics
    CacheStats.calls += 1

    # Check if in cache (handled by lru_cache decorator)
    # We just need to execute the query and let lru_cache handle the caching
    result = query_function(ncode, code_text)

    # Update hit/miss statistics
    if result is None:
        CacheStats.misses += 1
        logger.debug(f"Cache MISS for DOT code {code_text}")
    else:
        CacheStats.hits += 1
        logger.debug(f"Cache HIT for DOT code {code_text}")

    return result


def warm_up_cache(db: Any, common_dot_codes: List[str]) -> None:
    """
    Pre-warm the cache with commonly accessed DOT codes.

    Args:
        db: Database handler instance
        common_dot_codes: List of common DOT codes to pre-cache
    """
    logger.info(f"Warming up cache with {len(common_dot_codes)} common DOT codes")

    for dot_code in common_dot_codes:
        try:
            get_job_data(db, dot_code)
        except Exception as e:
            logger.error(f"Error warming cache for DOT code {dot_code}: {e}")

    logger.info(f"Cache warm-up complete. Stats: {CacheStats.get_stats()}")


def main():
    """
    Main function that processes command line arguments and generates a job report.
    """
    if len(sys.argv) != 2:
        print(
            "Usage: python -m src.sqlite.src.mcp_server_sqlite.generate_job_report <search_term>"
        )
        print("  search_term can be:")
        print("  - A DOT code (e.g., 001.061-010 or 001061010)")
        print("  - A job title (e.g., 'Architect')")
        sys.exit(1)

    search_term = sys.argv[1]

    # Assumes DOT.db is in the same directory as this script
    db_file_path = Path(__file__).parent / "DOT.db"

    if not db_file_path.exists():
        print(f"Error: Database file not found at {db_file_path}")
        print("Please ensure the DOT.db file is in the correct location.")
        sys.exit(1)

    try:
        # Configure logging
        logging.basicConfig(level=logging.INFO)

        # Import DatabaseHandler here for standalone use
        from .db_handler import DatabaseHandler

        db = DatabaseHandler(db_file_path)
        print(f"Connected to database: {db_file_path}")

        # Use the local get_job_data function
        job_data = get_job_data(db, search_term)

        if job_data:
            # Pass the potentially re-mapped job_data to the formatting function
            try:
                report = generate_formatted_job_report(job_data)
                print(report)

                # Print cache stats
                print(f"\nCache Statistics: {CacheStats.get_stats()}")
            except Exception as e:
                print(f"Error formatting job report: {e}")
                print("Job data found but could not format the report.")
                sys.exit(1)
        else:
            print(f"No job data found for search term: {search_term}")
            sys.exit(1)
    except FileNotFoundError:
        print(f"Error: Database file not found at {db_file_path}")
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
