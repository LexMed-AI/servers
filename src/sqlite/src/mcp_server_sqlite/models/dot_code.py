"""
DOT code utilities for consistent handling of codes across the application.
"""

import re
import logging
from typing import Dict, Optional, Tuple, Union, Any

logger = logging.getLogger(__name__)


class DotCode:
    """
    DOT code processing utility class with standardized methods for
    formatting, validation, and conversion between formats.
    """

    # Regular expression for validating DOT code format XXX.XXX-XXX
    DOT_CODE_PATTERN = re.compile(r"^(\d{3})\.(\d{3})-(\d{3})$")

    # Regular expression for validating DOT code in numeric format (9 digits)
    NCODE_PATTERN = re.compile(r"^\d{9}$")

    @classmethod
    def clean(cls, dot_code: str) -> Tuple[Optional[int], Optional[str]]:
        """
        Cleans and converts a DOT code into both Ncode (INTEGER) and Code (TEXT) formats.
        Handles multiple input formats.

        Args:
            dot_code: A DOT code in various possible formats

        Returns:
            A tuple of (Ncode, Code) where:
            - Ncode is an INTEGER (e.g., 1061010 for 001.061-010)
            - Code is TEXT (e.g., "001.061-010")
            Returns (None, None) if the format is unrecognized or invalid.
        """
        if not dot_code or not isinstance(dot_code, str):
            logger.debug(f"Invalid DOT code: {dot_code}")
            return None, None

        dot_code = dot_code.strip()

        # Case 1: Already in standard format (XXX.XXX-XXX)
        if cls.DOT_CODE_PATTERN.match(dot_code):
            # Convert to numeric format by removing dots and dashes
            numeric_code = dot_code.replace(".", "").replace("-", "")
            if len(numeric_code) == 9:
                try:
                    return int(numeric_code), dot_code
                except ValueError:
                    logger.warning(f"Failed to convert DOT code to integer: {dot_code}")
                    return None, None

        # Case 2: In numeric format with proper length (9 digits)
        if cls.NCODE_PATTERN.match(dot_code):
            try:
                ncode = int(dot_code)
                formatted_code = cls.format(ncode)
                return ncode, formatted_code
            except (ValueError, TypeError):
                logger.warning(f"Failed to process numeric DOT code: {dot_code}")
                return None, None

        # Case 3: In numeric format but without leading zeros
        if dot_code.isdigit():
            # Pad with leading zeros if needed
            padded_code = dot_code.zfill(9)
            try:
                ncode = int(padded_code)
                formatted_code = cls.format(ncode)
                return ncode, formatted_code
            except (ValueError, TypeError):
                logger.warning(
                    f"Failed to process and pad numeric DOT code: {dot_code}"
                )
                return None, None

        # If we reach here, the format is unrecognized
        logger.warning(f"Unrecognized DOT code format: {dot_code}")
        return None, None

    @classmethod
    def format(cls, ncode: Union[int, str]) -> str:
        """
        Formats a numeric DOT code (Ncode) as a standard DOT code string (XXX.XXX-XXX).

        Args:
            ncode: Integer or string representation of DOT code

        Returns:
            Formatted DOT code string
        """
        try:
            # Ensure ncode is a string
            ncode_str = str(ncode).zfill(9)

            if len(ncode_str) != 9:
                logger.warning(f"Invalid ncode length: {ncode_str}")
                return ""

            # Format as XXX.XXX-XXX
            return f"{ncode_str[0:3]}.{ncode_str[3:6]}-{ncode_str[6:9]}"
        except (ValueError, TypeError) as e:
            logger.warning(f"Error formatting DOT code {ncode}: {e}")
            return ""

    @classmethod
    def validate(cls, dot_code: str) -> Dict[str, Any]:
        """
        Validates a DOT code string for proper format.

        Args:
            dot_code: DOT code string to validate

        Returns:
            Dictionary with validation results
        """
        result: Dict[str, Any] = {
            "valid": False,
            "original": dot_code,
            "formatted": None,
            "ncode": None,
            "errors": [],  # Initialize as a list
        }

        if not dot_code or not isinstance(dot_code, str):
            result["errors"].append("DOT code must be a non-empty string")
            return result

        dot_code = dot_code.strip()

        # Check if it's in standard format
        if cls.DOT_CODE_PATTERN.match(dot_code):
            ncode, formatted = cls.clean(dot_code)
            if ncode is not None:
                result["valid"] = True
                result["ncode"] = ncode
                result["formatted"] = formatted
                return result
            result["errors"].append("Failed to convert to numeric format")

        # Check if it's in numeric format
        elif dot_code.isdigit():
            ncode, formatted = cls.clean(dot_code)
            if ncode is not None:
                result["valid"] = True
                result["ncode"] = ncode
                result["formatted"] = formatted
                return result
            result["errors"].append("Failed to convert to standard format")

        else:
            result["errors"].append(
                "DOT code must be in XXX.XXX-XXX format or all digits"
            )

        return result

    @classmethod
    def to_dict(cls, dot_code: str) -> Dict[str, Any]:
        """
        Converts a DOT code to a dictionary with all its representations.

        Args:
            dot_code: DOT code in any valid format

        Returns:
            Dictionary with different representations of the DOT code
        """
        ncode, formatted = cls.clean(dot_code)

        return {
            "original": dot_code,
            "ncode": ncode,
            "formatted": formatted,
            "valid": ncode is not None,
        }
