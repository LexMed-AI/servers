"""Data models for job analysis results."""

from dataclasses import dataclass, field
from typing import Dict, List, Any


@dataclass
class JobAnalysis:
    """Represents a complete job analysis."""

    job_title: str
    dot_code: str
    formatted_dot_code: str
    definition: str
    exertional_level: Dict[str, Any] = field(default_factory=dict)
    skill_level: Dict[str, Any] = field(default_factory=dict)
    ged_levels: Dict[str, Any] = field(default_factory=dict)
    worker_functions: Dict[str, Any] = field(default_factory=dict)
    physical_demands: Dict[str, Any] = field(default_factory=dict)
    environmental_conditions: Dict[str, Any] = field(default_factory=dict)
    aptitudes: Dict[str, Any] = field(default_factory=dict)
    temperaments: List[Dict[str, Any]] = field(default_factory=list)
    obsolescence_analysis: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the JobAnalysis instance to a dictionary."""
        return {
            "job_title": self.job_title,
            "dot_code": self.dot_code,
            "formatted_dot_code": self.formatted_dot_code,
            "definition": self.definition,
            "exertional_level": self.exertional_level,
            "skill_level": self.skill_level,
            "ged_levels": self.ged_levels,
            "worker_functions": self.worker_functions,
            "physical_demands": self.physical_demands,
            "environmental_conditions": self.environmental_conditions,
            "aptitudes": self.aptitudes,
            "temperaments": self.temperaments,
            "obsolescence_analysis": self.obsolescence_analysis,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "JobAnalysis":
        """Create a JobAnalysis instance from a dictionary."""
        return cls(
            job_title=data.get("job_title", ""),
            dot_code=data.get("dot_code", ""),
            formatted_dot_code=data.get("formatted_dot_code", ""),
            definition=data.get("definition", ""),
            exertional_level=data.get("exertional_level", {}),
            skill_level=data.get("skill_level", {}),
            ged_levels=data.get("ged_levels", {}),
            worker_functions=data.get("worker_functions", {}),
            physical_demands=data.get("physical_demands", {}),
            environmental_conditions=data.get("environmental_conditions", {}),
            aptitudes=data.get("aptitudes", {}),
            temperaments=data.get("temperaments", []),
            obsolescence_analysis=data.get("obsolescence_analysis", {}),
        )
