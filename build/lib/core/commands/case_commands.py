"""
Case Management Commands for BetterCallClaude

Implements the /case:* command family for case lifecycle management:
- /case:create - Create a new case
- /case:open - Load an existing case
- /case:close - Close a case
- /case:list - List all cases
- /case:summary - Generate case summary
- /case:export - Export case data
"""

import logging
from datetime import datetime
from typing import Any

from ..case.manager import (
    CaseManager,
    CaseStatus,
    CaseType,
    Deadline,
    Party,
)
from .base import BaseCommand, CommandCategory, CommandMetadata

logger = logging.getLogger(__name__)

# Singleton case manager instance
_case_manager: CaseManager | None = None


def get_case_manager() -> CaseManager:
    """Get or create the singleton CaseManager instance."""
    global _case_manager
    if _case_manager is None:
        _case_manager = CaseManager()
    return _case_manager


class CaseCreateCommand(BaseCommand):
    """
    Create a new case with the specified details.

    Usage:
        /case:create "Müller vs. ABC AG" --type litigation --canton ZH
        /case:create "Contract Review" --type contract --federal
    """

    def __init__(self) -> None:
        metadata = CommandMetadata(
            name="case:create",
            category=CommandCategory.CASE_STRATEGY,
            description="Create a new legal case",
            help_text='Usage: /case:create "<title>" [--type] [--canton] [--federal] [--lang]',
            auto_personas=[],
            mcp_servers=[],
        )
        super().__init__(metadata)

        self.add_argument("title", str, required=True, help_text="Case title")
        self.add_argument(
            "type",
            str,
            required=False,
            default="other",
            help_text="Case type: litigation, corporate, contract, regulatory, other",
        )
        self.add_argument(
            "canton",
            str,
            required=False,
            help_text="Canton jurisdiction (e.g., ZH, BE, GE)",
        )
        self.add_argument(
            "federal",
            bool,
            required=False,
            default=True,
            help_text="Whether federal jurisdiction applies",
        )
        self.add_argument(
            "lang",
            str,
            required=False,
            default="DE",
            help_text="Working language (DE, FR, IT, EN)",
        )
        self.add_argument(
            "client",
            str,
            required=False,
            help_text="Client name",
        )

    async def execute(self, args: dict[str, Any]) -> dict[str, Any]:
        """Execute case creation."""
        manager = get_case_manager()

        # Parse case type
        type_str = args.get("type", "other").lower()
        try:
            case_type = CaseType(type_str)
        except ValueError:
            case_type = CaseType.OTHER

        # Build parties list
        parties: list[Party] = []
        if args.get("client"):
            parties.append(Party(name=args["client"], role="client"))

        # Build canton list
        cantons: list[str] = []
        if args.get("canton"):
            cantons = [c.strip().upper() for c in args["canton"].split(",")]

        # Build languages list
        languages = [args.get("lang", "DE").upper()]

        # Create the case
        case = await manager.create_case(
            title=args["title"],
            case_type=case_type,
            jurisdiction_federal=args.get("federal", True),
            jurisdiction_cantons=cantons,
            languages=languages,
            parties=parties,
            user_id=args.get("user_id", "anonymous"),
            firm_id=args.get("firm_id"),
        )

        return {
            "success": True,
            "case_id": case.case_id,
            "title": case.title,
            "case_type": case.case_type.value,
            "message": f"Created case: {case.case_id} - {case.title}",
        }


class CaseOpenCommand(BaseCommand):
    """
    Open an existing case by ID.

    Usage:
        /case:open MUL-2025-001
    """

    def __init__(self) -> None:
        metadata = CommandMetadata(
            name="case:open",
            category=CommandCategory.CASE_STRATEGY,
            description="Open an existing case",
            help_text="Usage: /case:open <case_id>",
            auto_personas=[],
            mcp_servers=[],
        )
        super().__init__(metadata)

        self.add_argument("case_id", str, required=True, help_text="Case identifier")

    async def execute(self, args: dict[str, Any]) -> dict[str, Any]:
        """Execute case opening."""
        manager = get_case_manager()
        case_id = args["case_id"]

        case = await manager.open_case(case_id)

        if case is None:
            return {
                "success": False,
                "error": f"Case not found: {case_id}",
            }

        return {
            "success": True,
            "case_id": case.case_id,
            "title": case.title,
            "case_type": (
                case.case_type.value if isinstance(case.case_type, CaseType) else case.case_type
            ),
            "status": case.status.value if isinstance(case.status, CaseStatus) else case.status,
            "parties_count": len(case.parties),
            "facts_count": len(case.facts),
            "message": f"Opened case: {case.case_id} - {case.title}",
        }


class CaseCloseCommand(BaseCommand):
    """
    Close a case (archive with closure date).

    Usage:
        /case:close [case_id] [--reason "Case settled"]
    """

    def __init__(self) -> None:
        metadata = CommandMetadata(
            name="case:close",
            category=CommandCategory.CASE_STRATEGY,
            description="Close a case",
            help_text="Usage: /case:close [case_id] [--reason <reason>]",
            auto_personas=[],
            mcp_servers=[],
        )
        super().__init__(metadata)

        self.add_argument(
            "case_id",
            str,
            required=False,
            help_text="Case identifier (defaults to current case)",
        )
        self.add_argument(
            "reason",
            str,
            required=False,
            help_text="Reason for closure",
        )

    async def execute(self, args: dict[str, Any]) -> dict[str, Any]:
        """Execute case closure."""
        manager = get_case_manager()

        case_id = args.get("case_id")
        reason = args.get("reason", "")

        # Determine case to close
        if case_id is None and manager.current_case:
            case_id = manager.current_case.case_id

        if case_id is None:
            return {
                "success": False,
                "error": "No case specified and no current case active",
            }

        success = await manager.close_case(case_id, reason)

        if not success:
            return {
                "success": False,
                "error": f"Failed to close case: {case_id}",
            }

        return {
            "success": True,
            "case_id": case_id,
            "status": "closed",
            "message": f"Case closed: {case_id}",
        }


class CaseListCommand(BaseCommand):
    """
    List all cases with optional filtering.

    Usage:
        /case:list
        /case:list --status active
        /case:list --limit 20
    """

    def __init__(self) -> None:
        metadata = CommandMetadata(
            name="case:list",
            category=CommandCategory.CASE_STRATEGY,
            description="List all cases",
            help_text="Usage: /case:list [--status <status>] [--limit <n>]",
            auto_personas=[],
            mcp_servers=[],
        )
        super().__init__(metadata)

        self.add_argument(
            "status",
            str,
            required=False,
            help_text="Filter by status: active, archived, closed",
        )
        self.add_argument(
            "limit",
            int,
            required=False,
            default=100,
            help_text="Maximum number of results",
        )
        self.add_argument(
            "offset",
            int,
            required=False,
            default=0,
            help_text="Pagination offset",
        )

    async def execute(self, args: dict[str, Any]) -> dict[str, Any]:
        """Execute case listing."""
        manager = get_case_manager()

        # Parse status filter
        status = None
        if args.get("status"):
            try:
                status = CaseStatus(args["status"].lower())
            except ValueError:
                pass

        cases = await manager.list_cases(
            firm_id=args.get("firm_id"),
            status=status,
            limit=args.get("limit", 100),
            offset=args.get("offset", 0),
        )

        # Mark current case
        current_id = manager.current_case.case_id if manager.current_case else None

        return {
            "success": True,
            "cases": cases,
            "total": len(cases),
            "current_case_id": current_id,
        }


class CaseSummaryCommand(BaseCommand):
    """
    Generate a case status overview.

    Usage:
        /case:summary [case_id]
    """

    def __init__(self) -> None:
        metadata = CommandMetadata(
            name="case:summary",
            category=CommandCategory.CASE_STRATEGY,
            description="Generate case status overview",
            help_text="Usage: /case:summary [case_id]",
            auto_personas=[],
            mcp_servers=[],
        )
        super().__init__(metadata)

        self.add_argument(
            "case_id",
            str,
            required=False,
            help_text="Case identifier (defaults to current case)",
        )

    async def execute(self, args: dict[str, Any]) -> dict[str, Any]:
        """Execute case summary generation."""
        manager = get_case_manager()

        summary = await manager.generate_summary(args.get("case_id"))

        if "error" in summary:
            return {
                "success": False,
                "error": summary["error"],
            }

        return {
            "success": True,
            "summary": summary,
        }


class CaseExportCommand(BaseCommand):
    """
    Export case data for external use.

    Usage:
        /case:export [case_id] [--format json|markdown]
    """

    def __init__(self) -> None:
        metadata = CommandMetadata(
            name="case:export",
            category=CommandCategory.CASE_STRATEGY,
            description="Export case data",
            help_text="Usage: /case:export [case_id] [--format json|markdown]",
            auto_personas=[],
            mcp_servers=[],
        )
        super().__init__(metadata)

        self.add_argument(
            "case_id",
            str,
            required=False,
            help_text="Case identifier (defaults to current case)",
        )
        self.add_argument(
            "format",
            str,
            required=False,
            default="json",
            help_text="Export format: json, markdown",
        )

    async def execute(self, args: dict[str, Any]) -> dict[str, Any]:
        """Execute case export."""
        manager = get_case_manager()

        export_data = await manager.export_case(
            case_id=args.get("case_id"),
            format=args.get("format", "json"),
        )

        if "error" in export_data:
            return {
                "success": False,
                "error": export_data,
            }

        return {
            "success": True,
            "format": args.get("format", "json"),
            "data": export_data,
        }


class CaseAddPartyCommand(BaseCommand):
    """
    Add a party to a case.

    Usage:
        /case:add-party "Hans Müller" --role client
        /case:add-party "ABC AG" --role opposing --contact "info@abc.ch"
    """

    def __init__(self) -> None:
        metadata = CommandMetadata(
            name="case:add-party",
            category=CommandCategory.CASE_STRATEGY,
            description="Add a party to a case",
            help_text='Usage: /case:add-party "<name>" --role <role> [--contact <email>]',
            auto_personas=[],
            mcp_servers=[],
        )
        super().__init__(metadata)

        self.add_argument("name", str, required=True, help_text="Party name")
        self.add_argument(
            "role",
            str,
            required=True,
            help_text="Party role: client, plaintiff, defendant, opposing, related",
        )
        self.add_argument("contact", str, required=False, help_text="Contact email")
        self.add_argument(
            "case_id",
            str,
            required=False,
            help_text="Case identifier (defaults to current case)",
        )

    async def execute(self, args: dict[str, Any]) -> dict[str, Any]:
        """Execute adding a party."""
        manager = get_case_manager()

        party = Party(
            name=args["name"],
            role=args["role"],
            contact=args.get("contact"),
        )

        success = await manager.add_party(args.get("case_id"), party)

        if not success:
            return {
                "success": False,
                "error": "Failed to add party. No case specified or case not found.",
            }

        return {
            "success": True,
            "party": party.to_dict(),
            "message": f"Added party: {party.name} ({party.role})",
        }


class CaseAddFactCommand(BaseCommand):
    """
    Add a fact to a case.

    Usage:
        /case:add-fact "Contract signed on 2024-01-15"
    """

    def __init__(self) -> None:
        metadata = CommandMetadata(
            name="case:add-fact",
            category=CommandCategory.CASE_STRATEGY,
            description="Add a fact to a case",
            help_text='Usage: /case:add-fact "<fact>"',
            auto_personas=[],
            mcp_servers=[],
        )
        super().__init__(metadata)

        self.add_argument("fact", str, required=True, help_text="Fact description")
        self.add_argument(
            "case_id",
            str,
            required=False,
            help_text="Case identifier (defaults to current case)",
        )

    async def execute(self, args: dict[str, Any]) -> dict[str, Any]:
        """Execute adding a fact."""
        manager = get_case_manager()

        success = await manager.add_fact(args.get("case_id"), args["fact"])

        if not success:
            return {
                "success": False,
                "error": "Failed to add fact. No case specified or case not found.",
            }

        return {
            "success": True,
            "fact": args["fact"],
            "message": "Fact added to case",
        }


class CaseAddDeadlineCommand(BaseCommand):
    """
    Add a deadline to a case.

    Usage:
        /case:add-deadline "Response to complaint" --date 2025-02-15
    """

    def __init__(self) -> None:
        metadata = CommandMetadata(
            name="case:add-deadline",
            category=CommandCategory.CASE_STRATEGY,
            description="Add a deadline to a case",
            help_text='Usage: /case:add-deadline "<name>" --date YYYY-MM-DD [--description "<d>"]',
            auto_personas=[],
            mcp_servers=[],
        )
        super().__init__(metadata)

        self.add_argument("name", str, required=True, help_text="Deadline name")
        self.add_argument(
            "date",
            str,
            required=True,
            help_text="Due date (YYYY-MM-DD)",
        )
        self.add_argument("description", str, required=False, help_text="Description")
        self.add_argument(
            "case_id",
            str,
            required=False,
            help_text="Case identifier (defaults to current case)",
        )

    async def execute(self, args: dict[str, Any]) -> dict[str, Any]:
        """Execute adding a deadline."""
        manager = get_case_manager()

        try:
            due_date = datetime.fromisoformat(args["date"])
        except ValueError:
            return {
                "success": False,
                "error": f"Invalid date format: {args['date']}. Use YYYY-MM-DD.",
            }

        deadline = Deadline(
            name=args["name"],
            due_date=due_date,
            description=args.get("description", ""),
        )

        success = await manager.add_deadline(args.get("case_id"), deadline)

        if not success:
            return {
                "success": False,
                "error": "Failed to add deadline. No case specified or case not found.",
            }

        return {
            "success": True,
            "deadline": deadline.to_dict(),
            "message": f"Added: {deadline.name} ({deadline.due_date.strftime('%Y-%m-%d')})",
        }


# Export all command classes for registration
CASE_COMMANDS = [
    CaseCreateCommand,
    CaseOpenCommand,
    CaseCloseCommand,
    CaseListCommand,
    CaseSummaryCommand,
    CaseExportCommand,
    CaseAddPartyCommand,
    CaseAddFactCommand,
    CaseAddDeadlineCommand,
]
