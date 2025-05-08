"""Data models for DOT job information."""

from dataclasses import dataclass
from typing import Dict, Optional, Any


@dataclass
class DotJob:
    """Represents a DOT job with standardized field names."""

    ncode: Optional[int] = None
    dot_code: Optional[str] = None
    title: Optional[str] = None
    definition: Optional[str] = None
    svp: Optional[int] = None
    strength_num: Optional[int] = None
    ged_reasoning: Optional[int] = None
    ged_math: Optional[int] = None
    ged_language: Optional[int] = None

    @classmethod
    def from_db_row(cls, row_dict: Dict[str, Any]) -> "DotJob":
        """Create a DotJob instance from a database row dictionary."""
        if not row_dict:
            return cls()

        return cls(
            ncode=cls._safe_int(
                row_dict.get(
                    "NCode", row_dict.get("Ncode", row_dict.get("n_code", None))
                )
            ),
            dot_code=row_dict.get(
                "dotCode", row_dict.get("Code", row_dict.get("dotCodeFormatted", None))
            ),
            title=row_dict.get("jobTitle", row_dict.get("Title", None)),
            definition=row_dict.get("definition", row_dict.get("Definitions", None)),
            svp=cls._safe_int(row_dict.get("svp", row_dict.get("SVPNum", None))),
            strength_num=cls._safe_int(
                row_dict.get("strengthNum", row_dict.get("StrengthNum", None))
            ),
            ged_reasoning=cls._safe_int(
                row_dict.get("GEDR", row_dict.get("GEDReasoning", None))
            ),
            ged_math=cls._safe_int(row_dict.get("GEDM", row_dict.get("GEDMath", None))),
            ged_language=cls._safe_int(
                row_dict.get("GEDL", row_dict.get("GEDLanguage", None))
            ),
        )

    @staticmethod
    def _safe_int(value: Any) -> Optional[int]:
        """Safely convert a value to int, returning None if conversion fails."""
        if value is None:
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert the DotJob instance to a dictionary."""
        return {
            "ncode": self.ncode,
            "dot_code": self.dot_code,
            "title": self.title,
            "definition": self.definition,
            "svp": self.svp,
            "strength_num": self.strength_num,
            "ged_reasoning": self.ged_reasoning,
            "ged_math": self.ged_math,
            "ged_language": self.ged_language,
        }
