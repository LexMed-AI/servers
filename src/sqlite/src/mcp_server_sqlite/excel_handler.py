import logging
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional, Union

# Setup logger for this module
logger = logging.getLogger(__name__)


class BLSExcelHandlerError(Exception):
    """
    Custom exception for all BLSExcelHandler errors.
    Includes a message and optionally the original exception.
    """

    def __init__(self, message: str, original_exception: Optional[Exception] = None):
        super().__init__(message)
        self.original_exception = original_exception


class BLSExcelData:
    """Represents structured BLS data from the Excel file."""

    def __init__(
        self,
        occ_code: str,
        occ_title: str,
        tot_emp: float,
        a_mean: float,
        a_median: float,
        a_pct10: float,
        a_pct25: float,
        a_pct75: float,
        a_pct90: float,
    ):
        """Initialize BLS data structure with actual column names from the data."""
        self.occ_code = occ_code
        self.occ_title = occ_title
        self.tot_emp = tot_emp
        self.a_mean = a_mean
        self.a_median = a_median
        self.percentiles = {
            "a_pct10": a_pct10,
            "a_pct25": a_pct25,
            "a_pct75": a_pct75,
            "a_pct90": a_pct90,
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert data to dictionary for JSON serialization."""
        return {
            "occCode": self.occ_code,
            "occupationTitle": self.occ_title,
            "employmentTotal": self.tot_emp,
            "meanWage": self.a_mean,
            "medianWage": self.a_median,
            "percentiles": self.percentiles,
        }


class BLSExcelHandler:
    """Singleton handler for BLS Excel data operations."""

    _instance = None  # Singleton instance

    # Field descriptions for BLS OEWS data
    FIELD_DESCRIPTIONS = {
        "AREA": "U.S. (99), state FIPS code, Metropolitan Statistical Area (MSA) code, or OEWS-specific nonmetropolitan area code",
        "AREA_TITLE": "Area name",
        "AREA_TYPE": "Area type: 1= U.S.; 2= State; 3= U.S. Territory; 4= Metropolitan Statistical Area (MSA); 6= Nonmetropolitan Area",
        "PRIM_STATE": "The primary state for the given area. 'US' is used for the national estimates.",
        "NAICS": "North American Industry Classification System (NAICS) code for the given industry",
        "NAICS_TITLE": "North American Industry Classification System (NAICS) title for the given industry",
        "I_GROUP": "Industry level: Indicates cross-industry or NAICS sector, 3-digit, 4-digit, 5-digit, or 6-digit industry.",
        "OWN_CODE": "Ownership type: 1= Federal Government; 2= State Government; 3= Local Government; 123= Federal, State, and Local Government; 235=Private, State, and Local Government; 3= Private and Local Government; 5= Private; 57=Private, Local Government Gambling Establishments (Sector 71), and Local Government Casino Hotels (Sector 72); 58= Private plus State and Local Government Hospitals; 59= Private and Postal Service; 123S= Federal, State, and Local Government and Private Sector",
        "OCC_CODE": "The 6-digit Standard Occupational Classification (SOC) code or OEWS-specific code for the occupation",
        "OCC_TITLE": "SOC title or OEWS-specific title for the occupation",
        "O_GROUP": "SOC occupation level: For most occupations, this field indicates the standard SOC major, minor, broad, and detailed levels, in addition to all-occupations totals.",
        "TOT_EMP": "Estimated total employment rounded to the nearest 10 (excludes self-employed).",
        "EMP_PRSE": "Percent relative standard error (PRSE) for the employment estimate.",
        "JOBS_1000": "The number of jobs (employment) in the given occupation per 1,000 jobs in the given area.",
        "LOC_QUOTIENT": "The location quotient represents the ratio of an occupation's share of employment in a given area to that occupation's share of employment in the U.S. as a whole.",
        "PCT_TOTAL": "Percent of industry employment in the given occupation.",
        "PCT_RPT": "Percent of establishments reporting the given occupation for the cell.",
        "H_MEAN": "Mean hourly wage",
        "A_MEAN": "Annual mean wage",
        "MEAN_PRSE": "Percent relative standard error (PRSE) for the mean wage estimate.",
        "H_PCT10": "Hourly 10th percentile wage",
        "H_PCT25": "Hourly 25th percentile wage",
        "H_MEDIAN": "Hourly median wage (or the 50th percentile)",
        "H_PCT75": "Hourly 75th percentile wage",
        "H_PCT90": "Hourly 90th percentile wage",
        "A_PCT10": "Annual 10th percentile wage",
        "A_PCT25": "Annual 25th percentile wage",
        "A_MEDIAN": "Annual median wage (or the 50th percentile)",
        "A_PCT75": "Annual 75th percentile wage",
        "A_PCT90": "Annual 90th percentile wage",
        "ANNUAL": "Contains 'TRUE' if only annual wages are released. The OEWS program releases only annual wages for some occupations that typically work fewer than 2,080 hours per year but are paid on an annual basis, such as teachers, pilots, and athletes.",
        "HOURLY": "Contains 'TRUE' if only hourly wages are released. The OEWS program releases only hourly wages for some occupations that typically work fewer than 2,080 hours per year and are paid on an hourly basis, such as actors, dancers, and musicians and singers.",
    }

    def __init__(self, file_path: Union[str, Path]):
        """
        Initialize the BLS Excel handler.

        Args:
            file_path: Path to the BLS Excel file
        Raises:
            BLSExcelHandlerError: If the file cannot be loaded.
        """
        self.file_path = Path(file_path)
        self.dataframe = None
        try:
            self.load_workbook()
            logger.info(f"BLSExcelHandler initialized with file: {self.file_path}")
        except Exception as e:
            logger.error(f"Error initializing BLSExcelHandler: {e}", exc_info=True)
            raise BLSExcelHandlerError(f"Failed to initialize BLSExcelHandler: {e}", e)

    @classmethod
    def get_instance(cls, file_path: Union[str, Path]) -> "BLSExcelHandler":
        """
        Get singleton instance of BLSExcelHandler.

        Args:
            file_path: Path to the BLS Excel file

        Returns:
            BLSExcelHandler instance
        Raises:
            BLSExcelHandlerError: If initialization fails.
        """
        if cls._instance is None:
            cls._instance = cls(file_path)
        return cls._instance

    @classmethod
    def reset_instance(cls):
        """
        Reset the singleton instance (for reload/testing flexibility).
        """
        cls._instance = None

    def load_workbook(self) -> None:
        """
        Load the Excel workbook into a pandas DataFrame.
        Raises:
            BLSExcelHandlerError: If the file cannot be loaded.
        """
        if not self.file_path.exists():
            logger.error(f"Excel file not found at path: {self.file_path}")
            raise BLSExcelHandlerError(
                f"Excel file not found at path: {self.file_path}"
            )

        try:
            # Read the Excel file
            self.dataframe = pd.read_excel(self.file_path)

            # Log column info to help with debugging
            if self.dataframe is not None:
                logger.info(f"Loaded BLS Excel data with {len(self.dataframe)} rows")
                logger.info(f"Available columns: {list(self.dataframe.columns)}")
            else:
                # This case should ideally be caught by pd.read_excel raising an error,
                # but as a safeguard:
                logger.error(
                    f"DataFrame is None after attempting to load {self.file_path}"
                )
                raise BLSExcelHandlerError(
                    f"Failed to load data into DataFrame from {self.file_path}"
                )

        except Exception as e:
            logger.error(f"Error loading Excel file: {e}", exc_info=True)
            raise BLSExcelHandlerError(f"Error loading Excel file: {e}", e)

    def query_by_soc_code(self, soc_code: str) -> List[Dict[str, Any]]:
        """
        Query BLS data by SOC code (OCC_CODE in the Excel).

        Args:
            soc_code: SOC code to search for (non-empty string)

        Returns:
            List of dictionaries with BLS data (empty if not found)
        Raises:
            BLSExcelHandlerError: If the workbook is not loaded or input is invalid.
        """
        if not isinstance(soc_code, str) or not soc_code.strip():
            logger.error("query_by_soc_code called with invalid or empty soc_code.")
            raise BLSExcelHandlerError("SOC code must be a non-empty string.")
        if self.dataframe is None:
            logger.error("Workbook not loaded in query_by_soc_code.")
            raise BLSExcelHandlerError("Workbook not loaded.")

        try:
            # Filter for the specific SOC code in OCC_CODE column
            filtered = self.dataframe[self.dataframe["OCC_CODE"] == soc_code]

            if filtered.empty:
                return []

            # Convert the first matching row to our data structure
            row = filtered.iloc[0]
            return [
                BLSExcelData(
                    occ_code=row.get("OCC_CODE", ""),
                    occ_title=row.get("OCC_TITLE", ""),
                    tot_emp=float(row.get("TOT_EMP", 0)),
                    a_mean=float(row.get("A_MEAN", 0)),
                    a_median=float(row.get("A_MEDIAN", 0)),
                    a_pct10=float(row.get("A_PCT10", 0)),
                    a_pct25=float(row.get("A_PCT25", 0)),
                    a_pct75=float(row.get("A_PCT75", 0)),
                    a_pct90=float(row.get("A_PCT90", 0)),
                ).to_dict()
            ]
        except Exception as e:
            logger.error(f"Error querying by SOC code: {e}", exc_info=True)
            raise BLSExcelHandlerError(f"Error querying by SOC code: {e}", e)

    def query_by_occupation_title(self, title: str) -> List[Dict[str, Any]]:
        """
        Query BLS data by occupation title (OCC_TITLE in the Excel, partial match).

        Args:
            title: Occupation title or part of title to search for (non-empty string)

        Returns:
            List of dictionaries with matching BLS data (empty if not found)
        Raises:
            BLSExcelHandlerError: If the workbook is not loaded or input is invalid.
        """
        if not isinstance(title, str) or not title.strip():
            logger.error(
                "query_by_occupation_title called with invalid or empty title."
            )
            raise BLSExcelHandlerError("Title must be a non-empty string.")
        if self.dataframe is None:
            logger.error("Workbook not loaded in query_by_occupation_title.")
            raise BLSExcelHandlerError("Workbook not loaded.")

        try:
            # Filter for occupation titles containing the search term (case insensitive)
            filtered = self.dataframe[
                self.dataframe["OCC_TITLE"].str.lower().str.contains(title.lower())
            ]

            # Convert matching rows to our data structure
            results = []
            for _, row in filtered.iterrows():
                results.append(
                    BLSExcelData(
                        occ_code=row.get("OCC_CODE", ""),
                        occ_title=row.get("OCC_TITLE", ""),
                        tot_emp=float(row.get("TOT_EMP", 0)),
                        a_mean=float(row.get("A_MEAN", 0)),
                        a_median=float(row.get("A_MEDIAN", 0)),
                        a_pct10=float(row.get("A_PCT10", 0)),
                        a_pct25=float(row.get("A_PCT25", 0)),
                        a_pct75=float(row.get("A_PCT75", 0)),
                        a_pct90=float(row.get("A_PCT90", 0)),
                    ).to_dict()
                )

            return results
        except Exception as e:
            logger.error(f"Error querying by occupation title: {e}", exc_info=True)
            raise BLSExcelHandlerError(f"Error querying by occupation title: {e}", e)

    def get_field_description(self, field_name: str) -> str:
        """
        Get the description for a specific field/column.

        Args:
            field_name: Name of the field/column

        Returns:
            Description of the field or 'Unknown field' if not found
        """
        return self.FIELD_DESCRIPTIONS.get(field_name.upper(), "Unknown field")

    def get_all_field_descriptions(self) -> Dict[str, str]:
        """
        Get descriptions for all fields.

        Returns:
            Dictionary mapping field names to their descriptions
        """
        return self.FIELD_DESCRIPTIONS.copy()
