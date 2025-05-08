"""
Models package for DOT job and analysis data structures.
Provides standardized data models to prevent circular dependencies.
"""

from .dot_job import DotJob
from .analysis import JobAnalysis
from .dot_code import DotCode

__all__ = ["DotJob", "JobAnalysis", "DotCode"]
