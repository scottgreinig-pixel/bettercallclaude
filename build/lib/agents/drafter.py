"""
BetterCallClaude Drafter Agent

Legal document generation agent for Swiss law.
Generates properly structured legal documents including court submissions,
legal opinions, and contracts with multi-lingual support.

Workflow:
1. UNDERSTAND - Parse requirements and context
2. STRUCTURE - Create document outline
3. DRAFT - Generate content section by section
4. CITE - Add proper legal citations
5. FORMAT - Apply Swiss legal formatting
6. REVIEW - Final review with checkpoints
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .base import (
    ActionType,
    AgentBase,
    AgentOutcome,
    AgentResult,
    AutonomyMode,
)
from .models.drafter import (
    Citation,
    DocumentMetadata,
    DocumentSection,
    DocumentType,
    LegalDocument,
)
from .models.shared import (
    CaseFacts,
    Jurisdiction,
    Language,
    LegalParty,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Document Templates
# =============================================================================


DOCUMENT_STRUCTURES = {
    DocumentType.KLAGESCHRIFT: {
        Language.DE: [
            ("rubrum", "Rubrum", True),
            ("rechtsbegehren", "Rechtsbegehren", True),
            ("sachverhalt", "Sachverhalt", True),
            ("rechtliches", "Rechtliches", True),
            ("beweis", "Beweismittel", True),
            ("schluss", "Schlussantrag", False),
        ],
        Language.FR: [
            ("rubrum", "En-tête", True),
            ("conclusions", "Conclusions", True),
            ("faits", "En fait", True),
            ("droit", "En droit", True),
            ("preuves", "Offres de preuves", True),
        ],
        Language.IT: [
            ("rubrum", "Rubrica", True),
            ("petitum", "Petitum", True),
            ("fatti", "Fatti", True),
            ("diritto", "In diritto", True),
            ("prove", "Prove", True),
        ],
    },
    DocumentType.KLAGEANTWORT: {
        Language.DE: [
            ("rubrum", "Rubrum", True),
            ("rechtsbegehren", "Rechtsbegehren", True),
            ("sachverhalt", "Stellungnahme zum Sachverhalt", True),
            ("rechtliches", "Rechtliche Würdigung", True),
            ("beweis", "Beweismittel", True),
        ],
        Language.FR: [
            ("rubrum", "En-tête", True),
            ("conclusions", "Conclusions", True),
            ("faits", "Observations sur les faits", True),
            ("droit", "En droit", True),
            ("preuves", "Offres de preuves", True),
        ],
    },
    DocumentType.RECHTSGUTACHTEN: {
        Language.DE: [
            ("einleitung", "Einleitung", True),
            ("sachverhalt", "Sachverhalt", True),
            ("fragestellung", "Fragestellung", True),
            ("rechtliche_analyse", "Rechtliche Analyse", True),
            ("ergebnis", "Ergebnis", True),
        ],
        Language.FR: [
            ("introduction", "Introduction", True),
            ("faits", "Faits", True),
            ("questions", "Questions juridiques", True),
            ("analyse", "Analyse juridique", True),
            ("conclusion", "Conclusion", True),
        ],
    },
    DocumentType.MEMORANDUM: {
        Language.DE: [
            ("zusammenfassung", "Zusammenfassung", True),
            ("sachverhalt", "Sachverhalt", True),
            ("rechtsfragen", "Rechtsfragen", True),
            ("analyse", "Analyse", True),
            ("empfehlung", "Empfehlung", True),
        ],
        Language.EN: [
            ("summary", "Executive Summary", True),
            ("facts", "Statement of Facts", True),
            ("issues", "Legal Issues", True),
            ("analysis", "Analysis", True),
            ("conclusion", "Conclusion and Recommendations", True),
        ],
    },
    DocumentType.VERTRAG: {
        Language.DE: [
            ("praeambel", "Präambel", False),
            ("definitionen", "Definitionen", False),
            ("hauptleistung", "Hauptleistungspflichten", True),
            ("nebenleistung", "Nebenleistungspflichten", False),
            ("verguetung", "Vergütung", True),
            ("haftung", "Haftung", True),
            ("kuendigung", "Kündigung", True),
            ("schlussbestimmungen", "Schlussbestimmungen", True),
        ],
    },
}


# =============================================================================
# Checkpoint Configuration
# =============================================================================


DRAFTER_CHECKPOINTS = {
    "section_complete": {
        "trigger": "section_count > 3",
        "message_de": "📄 Abschnitt abgeschlossen. Überprüfung vor Fortsetzung.",
        "message_fr": "📄 Section terminée. Vérification avant de continuer.",
        "message_it": "📄 Sezione completata. Verifica prima di continuare.",
        "message_en": "📄 Section completed. Review before continuing.",
        "requires_confirmation": False,
    },
    "document_long": {
        "trigger": "word_count > 5000",
        "message_de": "📚 Dokument überschreitet 5000 Wörter. Struktur überprüfen.",
        "message_fr": "📚 Document dépasse 5000 mots. Vérifier la structure.",
        "message_it": "📚 Documento supera 5000 parole. Verificare la struttura.",
        "message_en": "📚 Document exceeds 5000 words. Review structure.",
        "requires_confirmation": True,
    },
    "citations_pending": {
        "trigger": "unverified_citations > 0",
        "message_de": "📖 Unbestätigte Zitate erkannt. Vor Abschluss validieren.",
        "message_fr": "📖 Citations non vérifiées détectées. Valider avant finalisation.",
        "message_it": "📖 Citazioni non verificate rilevate. Validare prima della finalizzazione.",
        "message_en": "📖 Unverified citations detected. Validate before finalizing.",
        "requires_confirmation": True,
    },
}


# =============================================================================
# Drafter-Specific Data Classes
# =============================================================================


@dataclass
class DraftingParameters:
    """Parameters for document generation."""

    document_type: DocumentType
    language: Language
    jurisdiction: Jurisdiction
    parties: list[LegalParty]
    case_facts: CaseFacts | None = None
    strategy_input: dict[str, Any] | None = None
    style_formal: bool = True
    include_citations: bool = True


@dataclass
class DrafterDeliverable:
    """Complete deliverable from DrafterAgent."""

    document: LegalDocument
    drafting_notes: list[str]
    citation_report: dict[str, Any]
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Serialize deliverable to dictionary."""
        return {
            "document": self.document.to_dict(),
            "drafting_notes": self.drafting_notes,
            "citation_report": self.citation_report,
            "metadata": self.metadata,
        }


# =============================================================================
# Drafter Agent
# =============================================================================


class DrafterAgent(AgentBase):
    """
    Legal document generation agent for Swiss law.

    Generates Swiss legal documents with proper structure, citations,
    and formatting for court submissions and legal opinions.

    Supports: Klageschrift, Rechtsgutachten, Verträge, and more.
    Multi-lingual: DE/FR/IT/EN
    """

    WORKFLOW_STEPS = [
        "UNDERSTAND",  # Parse requirements and context
        "STRUCTURE",  # Create document outline
        "DRAFT",  # Generate content section by section
        "CITE",  # Add proper legal citations
        "FORMAT",  # Apply Swiss legal formatting
        "REVIEW",  # Final review with checkpoints
    ]

    # Swiss German legal phrases
    LEGAL_PHRASES_DE = {
        "therefore": "Daher",
        "consequently": "Folglich",
        "in accordance with": "gemäss",
        "pursuant to": "gestützt auf",
        "as set forth in": "wie in ... dargelegt",
        "notwithstanding": "ungeachtet",
        "hereby": "hiermit",
        "whereas": "in Anbetracht dessen, dass",
    }

    # Swiss French legal phrases
    LEGAL_PHRASES_FR = {
        "therefore": "Par conséquent",
        "consequently": "En conséquence",
        "in accordance with": "conformément à",
        "pursuant to": "en vertu de",
        "as set forth in": "tel que prévu dans",
        "notwithstanding": "nonobstant",
        "hereby": "par la présente",
        "whereas": "attendu que",
    }

    # Swiss Italian legal phrases
    LEGAL_PHRASES_IT = {
        "therefore": "Pertanto",
        "consequently": "Di conseguenza",
        "in accordance with": "conformemente a",
        "pursuant to": "in virtù di",
        "as set forth in": "come previsto in",
        "notwithstanding": "nonostante",
        "hereby": "con la presente",
        "whereas": "considerato che",
    }

    @property
    def agent_id(self) -> str:
        return "drafter"

    @property
    def agent_version(self) -> str:
        return "1.0.0"

    async def execute(
        self,
        task: str,
        document_type: DocumentType = DocumentType.MEMORANDUM,
        language: Language = Language.DE,
        jurisdiction: Jurisdiction = Jurisdiction.FEDERAL,
        case_context: dict[str, Any] | None = None,
        case_facts: CaseFacts | None = None,
        parties: list[LegalParty] | None = None,
        strategy_input: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> AgentResult[DrafterDeliverable]:
        """
        Execute document generation workflow.

        Args:
            task: Document generation request
            document_type: Type of legal document
            language: Document language
            jurisdiction: Target jurisdiction
            case_context: Case facts and context
            case_facts: Structured case facts
            parties: Legal parties involved
            strategy_input: Optional strategy from StrategistAgent

        Returns:
            AgentResult containing DrafterDeliverable
        """
        self._start_time = datetime.utcnow()
        logger.info(f"DrafterAgent starting: {task}")

        try:
            # Create initial checkpoint
            self.create_checkpoint("auto", "Document drafting started")

            # Initialize metadata
            metadata = DocumentMetadata(
                document_type=document_type,
                language=language,
                jurisdiction=jurisdiction,
                date_created=datetime.utcnow().strftime("%Y-%m-%d"),
            )

            # Step 1: UNDERSTAND requirements
            self.update_state("step", "UNDERSTAND")
            # Store parameters for potential future use
            _params = DraftingParameters(
                document_type=document_type,
                language=language,
                jurisdiction=jurisdiction,
                parties=parties or [],
                case_facts=case_facts,
                strategy_input=strategy_input,
            )
            del _params  # Parameters captured in method args, not needed here
            self._record_action(
                ActionType.ANALYZE,
                "Requirements parsed",
                inputs={"task": task, "document_type": document_type.value},
                outputs={"language": language.value, "jurisdiction": jurisdiction.value},
                duration_ms=50,
            )

            # Step 2: STRUCTURE - Create document outline
            self.update_state("step", "STRUCTURE")
            sections = await self.generate_structure(document_type, language)
            self._record_action(
                ActionType.GENERATE,
                "Document structure created",
                inputs={"document_type": document_type.value},
                outputs={"section_count": len(sections)},
                duration_ms=100,
            )

            # Step 3: DRAFT - Generate content section by section
            self.update_state("step", "DRAFT")
            drafted_sections = []
            total_word_count = 0

            for i, (section_type, title, _required) in enumerate(sections):
                section = await self.draft_section(
                    section_type=section_type,
                    title=title,
                    content_input={
                        "task": task,
                        "case_facts": case_facts,
                        "strategy_input": strategy_input,
                        "parties": parties,
                        "jurisdiction": jurisdiction,
                    },
                    language=language,
                    order=i,
                )
                drafted_sections.append(section)
                total_word_count += section.word_count

                # Section completion checkpoint (every 3 sections)
                if (i + 1) % 3 == 0 and self.autonomy_mode == AutonomyMode.CAUTIOUS:
                    checkpoint_msg = str(
                        DRAFTER_CHECKPOINTS["section_complete"][f"message_{language.value}"]
                    )
                    self.create_checkpoint("auto", checkpoint_msg)

            self._record_action(
                ActionType.GENERATE,
                "Content drafted",
                inputs={"section_count": len(drafted_sections)},
                outputs={"total_word_count": total_word_count},
                duration_ms=500,
            )

            # Check for long document checkpoint
            if total_word_count > 5000:
                checkpoint_msg = str(
                    DRAFTER_CHECKPOINTS["document_long"][f"message_{language.value}"]
                )
                if self.autonomy_mode != AutonomyMode.AUTONOMOUS:
                    self.create_checkpoint("user", checkpoint_msg)
                    await self.request_user_confirmation(checkpoint_msg)

            # Step 4: CITE - Add legal citations
            self.update_state("step", "CITE")
            document = LegalDocument(
                metadata=metadata,
                sections=drafted_sections,
                parties=parties or [],
            )

            # Extract and add citations
            citations = self._extract_citations_from_content(drafted_sections, language)
            if citations:
                document = await self.add_citations(document, citations)

            # Checkpoint for unverified citations
            if document.has_unverified_citations:
                checkpoint_msg = str(
                    DRAFTER_CHECKPOINTS["citations_pending"][f"message_{language.value}"]
                )
                if self.autonomy_mode == AutonomyMode.CAUTIOUS:
                    self.create_checkpoint("user", checkpoint_msg)
                    await self.request_user_confirmation(checkpoint_msg)

            self._record_action(
                ActionType.GENERATE,
                "Citations added",
                inputs={"citation_count": len(citations)},
                outputs={
                    "verified_count": len([c for c in document.citations_used if c.is_verified])
                },
                duration_ms=100,
            )

            # Step 5: FORMAT - Apply jurisdiction-specific formatting
            self.update_state("step", "FORMAT")
            document = await self.format_document(document, jurisdiction)
            self._record_action(
                ActionType.GENERATE,
                "Document formatted",
                inputs={"jurisdiction": jurisdiction.value},
                outputs={"page_estimate": document.page_estimate},
                duration_ms=100,
            )

            # Step 6: REVIEW - Final review
            self.update_state("step", "REVIEW")
            drafting_notes = self._generate_drafting_notes(document, language)
            citation_report = self._generate_citation_report(document)

            # Render full text
            document.render_full_text()

            deliverable = DrafterDeliverable(
                document=document,
                drafting_notes=drafting_notes,
                citation_report=citation_report,
                metadata={
                    "generated_at": datetime.utcnow().isoformat(),
                    "workflow_steps": self.WORKFLOW_STEPS,
                    "language": language.value,
                    "jurisdiction": jurisdiction.value,
                },
            )

            # Final checkpoint
            self.create_checkpoint("auto", "Document drafting completed")

            execution_time_ms = int((datetime.utcnow() - self._start_time).total_seconds() * 1000)

            return AgentResult(
                success=True,
                outcome=AgentOutcome.SUCCESS,
                deliverable=deliverable,
                partial_results=None,
                error_message=None,
                audit_log=self._create_audit_log(
                    AgentOutcome.SUCCESS,
                    ["legal_document", "citation_report"],
                ),
                execution_time_ms=execution_time_ms,
            )

        except Exception as e:
            self._handle_error(e, recoverable=False)
            execution_time_ms = int((datetime.utcnow() - self._start_time).total_seconds() * 1000)
            return AgentResult(
                success=False,
                outcome=AgentOutcome.FAILED,
                deliverable=None,
                partial_results=None,  # Type requires T | None, not dict
                error_message=str(e),
                audit_log=self._create_audit_log(AgentOutcome.FAILED, []),
                execution_time_ms=execution_time_ms,
            )

    # =========================================================================
    # HIGH PRIORITY METHODS
    # =========================================================================

    async def generate_structure(
        self,
        doc_type: DocumentType,
        language: Language,
    ) -> list[tuple[str, str, bool]]:
        """
        Generate document structure for document type.

        Returns list of (section_type, title, required) tuples.

        Args:
            doc_type: Type of legal document
            language: Document language

        Returns:
            List of section definitions
        """
        logger.info(f"Generating structure for {doc_type.value} in {language.value}")

        # Get structure for document type and language
        doc_structures = DOCUMENT_STRUCTURES.get(doc_type, {})
        structure = doc_structures.get(language)

        # Fallback to German structure if language not available
        if not structure:
            structure = doc_structures.get(Language.DE, [])
            logger.warning(f"No {language.value} structure for {doc_type.value}, using DE fallback")

        # If still no structure, use generic
        if not structure:
            structure = [
                ("einleitung", self._translate_section_title("introduction", language), True),
                ("hauptteil", self._translate_section_title("main_content", language), True),
                ("schluss", self._translate_section_title("conclusion", language), True),
            ]

        return structure

    async def draft_section(
        self,
        section_type: str,
        title: str,
        content_input: dict[str, Any],
        language: Language,
        order: int = 0,
    ) -> DocumentSection:
        """
        Draft individual document section.

        Args:
            section_type: Type of section (e.g., 'sachverhalt', 'rechtliches')
            title: Section title
            content_input: Input data for content generation
            language: Document language
            order: Section order in document

        Returns:
            DocumentSection with drafted content
        """
        logger.info(f"Drafting section: {title}")

        content = self._generate_section_content(
            section_type=section_type,
            content_input=content_input,
            language=language,
        )

        return DocumentSection(
            section_type=section_type,
            title=title,
            content=content,
            citations=[],
            footnotes=[],
            order=order,
            subsections=[],
        )

    async def add_citations(
        self,
        document: LegalDocument,
        citations: list[str],
    ) -> LegalDocument:
        """
        Add and format legal citations.

        Args:
            document: Document to add citations to
            citations: List of citation strings

        Returns:
            Updated LegalDocument
        """
        logger.info(f"Adding {len(citations)} citations")

        for citation_text in citations:
            citation = self._parse_citation(citation_text)
            if citation not in document.citations_used:
                document.citations_used.append(citation)

        return document

    async def format_document(
        self,
        document: LegalDocument,
        jurisdiction: Jurisdiction,
    ) -> LegalDocument:
        """
        Apply jurisdiction-specific formatting.

        Args:
            document: Document to format
            jurisdiction: Target jurisdiction

        Returns:
            Formatted LegalDocument
        """
        logger.info(f"Formatting document for {jurisdiction.value}")

        # Recalculate word count and page estimate
        total_words = sum(section.word_count for section in document.sections)
        document.word_count = total_words
        document.page_estimate = max(1, total_words // 300)

        # Set court name if submission type
        if document.metadata.document_type.requires_court:
            court_names = jurisdiction.court_name
            lang_key = document.metadata.language.value
            document.metadata.court = court_names.get(lang_key, court_names.get("de", ""))

        return document

    # =========================================================================
    # MEDIUM PRIORITY METHODS
    # =========================================================================

    async def generate_bilingual(
        self,
        document: LegalDocument,
        target_language: Language,
    ) -> LegalDocument:
        """
        Generate bilingual version of document.

        Args:
            document: Original document
            target_language: Target language for translation

        Returns:
            New LegalDocument in target language
        """
        logger.info(f"Generating bilingual version in {target_language.value}")

        # Create new metadata for target language
        new_metadata = DocumentMetadata(
            document_type=document.metadata.document_type,
            language=target_language,
            jurisdiction=document.metadata.jurisdiction,
            case_reference=document.metadata.case_reference,
            date_created=document.metadata.date_created,
            author=document.metadata.author,
            client_reference=document.metadata.client_reference,
        )

        # Get structure for target language
        structure = await self.generate_structure(
            document.metadata.document_type,
            target_language,
        )

        # Draft sections in target language
        new_sections = []
        for i, (section_type, title, _required) in enumerate(structure):
            # Find corresponding original section
            original_section = document.get_section(section_type)
            content_input = {
                "original_content": original_section.content if original_section else "",
                "translation_mode": True,
            }

            section = await self.draft_section(
                section_type=section_type,
                title=title,
                content_input=content_input,
                language=target_language,
                order=i,
            )
            new_sections.append(section)

        return LegalDocument(
            metadata=new_metadata,
            sections=new_sections,
            parties=document.parties,
            citations_used=document.citations_used,
        )

    async def validate_citations(
        self,
        citations: list[str],
    ) -> list[dict[str, Any]]:
        """
        Validate citation format and existence.

        Args:
            citations: List of citation strings

        Returns:
            Validation results for each citation
        """
        logger.info(f"Validating {len(citations)} citations")

        results = []
        for citation_text in citations:
            parsed = self._parse_citation(citation_text)
            validation = {
                "citation": citation_text,
                "parsed_type": parsed.source_type,
                "format_valid": self._validate_citation_format(citation_text),
                "is_verified": parsed.is_verified,
                "issues": (
                    []
                    if self._validate_citation_format(citation_text)
                    else ["Invalid citation format"]
                ),
            }

            results.append(validation)

        return results

    # =========================================================================
    # HELPER METHODS
    # =========================================================================

    def _generate_section_content(
        self,
        section_type: str,
        content_input: dict[str, Any],
        language: Language,
    ) -> str:
        """Generate content for a document section."""
        task = content_input.get("task", "")
        case_facts = content_input.get("case_facts")
        parties = content_input.get("parties", [])
        jurisdiction = content_input.get("jurisdiction", Jurisdiction.FEDERAL)
        strategy_input = content_input.get("strategy_input", {})

        # Rubrum section
        if section_type == "rubrum":
            return self._generate_rubrum(parties, jurisdiction, language)

        # Rechtsbegehren/Conclusions/Petitum
        if section_type in ["rechtsbegehren", "conclusions", "petitum"]:
            return self._generate_rechtsbegehren(task, language)

        # Sachverhalt/Faits/Fatti
        if section_type in ["sachverhalt", "faits", "fatti", "facts"]:
            return self._generate_sachverhalt(case_facts, language)

        # Rechtliches/Droit/Diritto
        if section_type in ["rechtliches", "rechtliche_analyse", "droit", "diritto", "analysis"]:
            return self._generate_rechtliches(case_facts, strategy_input, language)

        # Zusammenfassung/Summary
        if section_type in ["zusammenfassung", "summary", "einleitung", "introduction"]:
            return self._generate_summary(task, case_facts, language)

        # Empfehlung/Conclusion
        if section_type in ["empfehlung", "ergebnis", "conclusion", "schluss"]:
            return self._generate_conclusion(strategy_input, language)

        # Default placeholder content
        return self._generate_placeholder(section_type, language)

    def _generate_rubrum(
        self,
        parties: list[LegalParty],
        jurisdiction: Jurisdiction,
        language: Language,
    ) -> str:
        """Generate rubrum/header section."""
        court_name = jurisdiction.court_name.get(
            language.value, jurisdiction.court_name.get("de", "Gericht")
        )

        if language == Language.DE:
            lines = [f"An das {court_name}", "", "In Sachen", ""]
        elif language == Language.FR:
            lines = [f"Au {court_name}", "", "Dans la cause", ""]
        elif language == Language.IT:
            lines = [f"Al {court_name}", "", "Nella causa", ""]
        else:
            lines = [f"To the {court_name}", "", "In the matter of", ""]

        for party in parties:
            role_display = party.role_translated.get(language.value, party.role)
            lines.append(party.name)
            lines.append(role_display)
            if party.representation:
                rep_label = {
                    "de": "vertreten durch",
                    "fr": "représenté par",
                    "it": "rappresentato da",
                    "en": "represented by",
                }
                lines.append(
                    f"{rep_label.get(language.value, 'represented by')} {party.representation}"
                )
            lines.append("")

        return "\n".join(lines)

    def _generate_rechtsbegehren(self, task: str, language: Language) -> str:
        """Generate rechtsbegehren/conclusions section."""
        if language == Language.DE:
            return f"""1. [Hauptantrag basierend auf: {task[:100]}...]

2. Unter Kosten- und Entschädigungsfolgen zulasten der Gegenpartei.

3. Unter Vorbehalt der Ergänzung und Anpassung."""
        elif language == Language.FR:
            return f"""1. [Conclusion principale basée sur: {task[:100]}...]

2. Avec suite de frais et dépens à la charge de la partie adverse.

3. Sous réserve de compléments et modifications."""
        elif language == Language.IT:
            return f"""1. [Conclusione principale basata su: {task[:100]}...]

2. Con spese e ripetibili a carico della controparte.

3. Con riserva di complementi e modifiche."""
        else:
            return f"""1. [Main request based on: {task[:100]}...]

2. With costs and compensation to be borne by the opposing party.

3. Subject to amendments and supplements."""

    def _generate_sachverhalt(
        self,
        case_facts: CaseFacts | None,
        language: Language,
    ) -> str:
        """Generate sachverhalt/facts section."""
        if not case_facts:
            return self._generate_placeholder("sachverhalt", language)

        sections = []

        # Summary
        if language == Language.DE:
            sections.append(f"A. Übersicht\n\n{case_facts.summary}")
        elif language == Language.FR:
            sections.append(f"A. Aperçu\n\n{case_facts.summary}")
        elif language == Language.IT:
            sections.append(f"A. Panoramica\n\n{case_facts.summary}")
        else:
            sections.append(f"A. Overview\n\n{case_facts.summary}")

        # Key events
        if case_facts.key_events:
            if language == Language.DE:
                sections.append("\nB. Chronologie der Ereignisse\n")
            elif language == Language.FR:
                sections.append("\nB. Chronologie des événements\n")
            elif language == Language.IT:
                sections.append("\nB. Cronologia degli eventi\n")
            else:
                sections.append("\nB. Timeline of Events\n")

            for i, event in enumerate(case_facts.key_events[:10], 1):
                date = event.get("date", "")
                description = event.get("event", str(event))
                sections.append(f"{i}. {date}: {description}")

        # Disputed facts
        if case_facts.disputed_facts:
            if language == Language.DE:
                sections.append("\n\nC. Streitige Tatsachen\n")
            elif language == Language.FR:
                sections.append("\n\nC. Faits contestés\n")
            elif language == Language.IT:
                sections.append("\n\nC. Fatti contestati\n")
            else:
                sections.append("\n\nC. Disputed Facts\n")

            for _idx, fact in enumerate(case_facts.disputed_facts, 1):
                sections.append(f"- {fact}")

        return "\n".join(sections)

    def _generate_rechtliches(
        self,
        case_facts: CaseFacts | None,
        strategy_input: dict[str, Any] | None,
        language: Language,
    ) -> str:
        """Generate rechtliches/legal analysis section."""
        sections = []

        if language == Language.DE:
            sections.append("A. Anwendbares Recht\n")
            sections.append("Die vorliegende Streitigkeit untersteht schweizerischem Recht.\n")
            sections.append("\nB. Rechtliche Würdigung\n")
        elif language == Language.FR:
            sections.append("A. Droit applicable\n")
            sections.append("Le présent litige est soumis au droit suisse.\n")
            sections.append("\nB. Appréciation juridique\n")
        elif language == Language.IT:
            sections.append("A. Diritto applicabile\n")
            sections.append("La presente controversia è soggetta al diritto svizzero.\n")
            sections.append("\nB. Valutazione giuridica\n")
        else:
            sections.append("A. Applicable Law\n")
            sections.append("The present dispute is governed by Swiss law.\n")
            sections.append("\nB. Legal Assessment\n")

        # Add legal questions if available
        if case_facts and case_facts.legal_questions:
            for i, question in enumerate(case_facts.legal_questions, 1):
                sections.append(f"\n{i}. {question}\n")
                sections.append(
                    "[Rechtliche Analyse hier einfügen / Legal analysis to be inserted]\n"
                )

        return "\n".join(sections)

    def _generate_summary(
        self,
        task: str,
        case_facts: CaseFacts | None,
        language: Language,
    ) -> str:
        """Generate summary/introduction section."""
        if language == Language.DE:
            intro = f"Das vorliegende Dokument behandelt: {task}"
            if case_facts:
                intro += (
                    f"\n\nStreitwert: CHF {case_facts.value_in_dispute:,.0f}"
                    if case_facts.value_in_dispute
                    else ""
                )
        elif language == Language.FR:
            intro = f"Le présent document traite de: {task}"
            if case_facts:
                intro += (
                    f"\n\nValeur litigieuse: CHF {case_facts.value_in_dispute:,.0f}"
                    if case_facts.value_in_dispute
                    else ""
                )
        elif language == Language.IT:
            intro = f"Il presente documento tratta: {task}"
            if case_facts:
                intro += (
                    f"\n\nValore litigioso: CHF {case_facts.value_in_dispute:,.0f}"
                    if case_facts.value_in_dispute
                    else ""
                )
        else:
            intro = f"This document addresses: {task}"
            if case_facts:
                intro += (
                    f"\n\nAmount in dispute: CHF {case_facts.value_in_dispute:,.0f}"
                    if case_facts.value_in_dispute
                    else ""
                )

        return intro

    def _generate_conclusion(
        self,
        strategy_input: dict[str, Any] | None,
        language: Language,
    ) -> str:
        """Generate conclusion/recommendation section."""
        if language == Language.DE:
            return """Zusammenfassend ist festzuhalten:

1. [Hauptergebnis]
2. [Empfehlung]
3. [Nächste Schritte]"""
        elif language == Language.FR:
            return """En résumé:

1. [Résultat principal]
2. [Recommandation]
3. [Prochaines étapes]"""
        elif language == Language.IT:
            return """In sintesi:

1. [Risultato principale]
2. [Raccomandazione]
3. [Prossimi passi]"""
        else:
            return """In summary:

1. [Main finding]
2. [Recommendation]
3. [Next steps]"""

    def _generate_placeholder(self, section_type: str, language: Language) -> str:
        """Generate placeholder content for unknown sections."""
        placeholders = {
            Language.DE: f"[Inhalt für {section_type} hier einfügen]",
            Language.FR: f"[Insérer le contenu pour {section_type} ici]",
            Language.IT: f"[Inserire il contenuto per {section_type} qui]",
            Language.EN: f"[Insert content for {section_type} here]",
        }
        return placeholders.get(language, placeholders[Language.EN])

    def _translate_section_title(self, key: str, language: Language) -> str:
        """Translate section title to target language."""
        titles = {
            "introduction": {
                Language.DE: "Einleitung",
                Language.FR: "Introduction",
                Language.IT: "Introduzione",
                Language.EN: "Introduction",
            },
            "main_content": {
                Language.DE: "Hauptteil",
                Language.FR: "Corps du texte",
                Language.IT: "Corpo principale",
                Language.EN: "Main Content",
            },
            "conclusion": {
                Language.DE: "Schluss",
                Language.FR: "Conclusion",
                Language.IT: "Conclusione",
                Language.EN: "Conclusion",
            },
        }
        return titles.get(key, {}).get(language, key)

    def _extract_citations_from_content(
        self,
        sections: list[DocumentSection],
        language: Language,
    ) -> list[str]:
        """Extract citation references from section content."""
        citations = []
        import re

        # BGE pattern: BGE 123 III 456
        bge_pattern = r"BGE\s+\d{1,3}\s+[IVX]+\s+\d+"

        # Article pattern: Art. 97 OR, art. 97 CO
        article_pattern = (
            r"[Aa]rt\.?\s+\d+(?:\s+(?:Abs|al|cpv)\.?\s*\d+)?(?:\s+(?:OR|ZGB|StGB|ZPO|CO|CC|CPC))?"
        )

        for section in sections:
            content = section.content

            # Find BGE citations
            bge_matches = re.findall(bge_pattern, content)
            citations.extend(bge_matches)

            # Find article citations
            article_matches = re.findall(article_pattern, content)
            citations.extend(article_matches)

        # Remove duplicates while preserving order
        seen = set()
        unique_citations = []
        for c in citations:
            if c not in seen:
                seen.add(c)
                unique_citations.append(c)

        return unique_citations

    def _parse_citation(self, citation_text: str) -> Citation:
        """Parse citation text into Citation object."""
        # Determine source type
        source_type = "unknown"
        if citation_text.startswith("BGE"):
            source_type = "bge"
        elif "Art" in citation_text or "art" in citation_text:
            source_type = "statute"
        elif "/" in citation_text and "_" in citation_text:
            source_type = "federal_court"

        return Citation(
            citation_text=citation_text,
            source_type=source_type,
            is_verified=False,  # Would need MCP server verification
            url=None,
            relevance="",
        )

    def _validate_citation_format(self, citation_text: str) -> bool:
        """Validate citation format."""
        import re

        # BGE format
        if citation_text.startswith("BGE"):
            return bool(re.match(r"BGE\s+\d{1,3}\s+[IVX]+\s+\d+", citation_text))

        # Article format
        if "Art" in citation_text or "art" in citation_text:
            return bool(re.match(r"[Aa]rt\.?\s+\d+", citation_text))

        return True  # Accept other formats

    def _generate_drafting_notes(
        self,
        document: LegalDocument,
        language: Language,
    ) -> list[str]:
        """Generate drafting notes for review."""
        notes = []

        if language == Language.DE:
            word_info = f"Dokument enthält {document.word_count} Wörter"
            page_info = f"auf ca. {document.page_estimate} Seiten"
            notes.append(f"{word_info} {page_info}")
            if document.has_unverified_citations:
                cite_count = len(document.unverified_citations)
                notes.append(f"⚠️ {cite_count} unbestätigte Zitate erfordern Überprüfung")
        elif language == Language.FR:
            word_info = f"Document contient {document.word_count} mots"
            page_info = f"sur environ {document.page_estimate} pages"
            notes.append(f"{word_info} {page_info}")
            if document.has_unverified_citations:
                cite_count = len(document.unverified_citations)
                notes.append(f"⚠️ {cite_count} citations non vérifiées nécessitent vérification")
        else:
            word_info = f"Document contains {document.word_count} words"
            page_info = f"on approximately {document.page_estimate} pages"
            notes.append(f"{word_info} {page_info}")
            if document.has_unverified_citations:
                cite_count = len(document.unverified_citations)
                notes.append(f"⚠️ {cite_count} unverified citations require review")

        return notes

    def _generate_citation_report(self, document: LegalDocument) -> dict[str, Any]:
        """Generate citation verification report."""
        return {
            "total_citations": len(document.citations_used),
            "verified_count": len([c for c in document.citations_used if c.is_verified]),
            "unverified_count": len(document.unverified_citations),
            "by_type": self._group_citations_by_type(document.citations_used),
        }

    def _group_citations_by_type(self, citations: list[Citation]) -> dict[str, int]:
        """Group citations by source type."""
        groups: dict[str, int] = {}
        for citation in citations:
            groups[citation.source_type] = groups.get(citation.source_type, 0) + 1
        return groups
