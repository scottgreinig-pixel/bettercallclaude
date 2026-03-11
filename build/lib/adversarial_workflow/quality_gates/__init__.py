"""
Quality gates for input validation and report verification.

Gates:
- InputValidation: Validates UserQueryPackage completeness and format
- ReportValidation: Validates agent reports for citation accuracy and structure
- ObjectivityValidation: Validates Judicial synthesis for balance and objectivity
"""

__all__ = [
    "InputValidation",
    "ReportValidation",
    "ObjectivityValidation",
]
