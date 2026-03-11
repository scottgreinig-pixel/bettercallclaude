"""
Drafter Agent Data Models

This module provides data models specific to the DrafterAgent for
legal document generation with Swiss law compliance.

Supports court submissions, legal opinions, contracts, and correspondence
in DE, FR, IT, EN with proper Swiss legal formatting.

Dokumentmodelle / Modèles de documents / Modelli di documenti
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from src.agents.models.shared import Jurisdiction, Language, LegalParty


class DocumentType(Enum):
    """
    Swiss legal document types.

    Dokumenttypen / Types de documents / Tipi di documenti

    Categories:
        Submissions (Eingaben / Écritures / Atti processuali)
        Legal opinions (Gutachten / Avis juridiques / Pareri legali)
        Contracts (Verträge / Contrats / Contratti)
        Correspondence (Korrespondenz / Correspondance / Corrispondenza)
    """

    # Court Submissions
    KLAGESCHRIFT = "klageschrift"  # Statement of claim / Demande / Petizione
    KLAGEANTWORT = "klageantwort"  # Statement of defense / Réponse / Risposta
    REPLIK = "replik"  # Reply / Réplique / Replica
    DUPLIK = "duplik"  # Rejoinder / Duplique / Duplica
    BERUFUNG = "berufung"  # Appeal / Appel / Appello
    BESCHWERDE = "beschwerde"  # Complaint/Appeal / Recours / Ricorso
    STELLUNGNAHME = "stellungnahme"  # Statement / Détermination / Osservazioni

    # Legal Opinions
    RECHTSGUTACHTEN = "rechtsgutachten"  # Legal opinion / Avis de droit / Parere legale
    MEMORANDUM = "memorandum"  # Legal memo / Mémorandum / Memorandum
    KURZGUTACHTEN = "kurzgutachten"  # Brief opinion / Avis succinct / Parere breve

    # Contracts
    VERTRAG = "vertrag"  # Contract / Contrat / Contratto
    VEREINBARUNG = "vereinbarung"  # Agreement / Convention / Convenzione
    KAUFVERTRAG = "kaufvertrag"  # Sales contract / Contrat de vente / Contratto di vendita
    MIETVERTRAG = "mietvertrag"  # Lease / Bail / Contratto di locazione
    ARBEITSVERTRAG = (
        "arbeitsvertrag"  # Employment contract / Contrat de travail / Contratto di lavoro
    )

    # Correspondence
    MAHNUNG = "mahnung"  # Formal notice / Mise en demeure / Diffida
    KUENDIGUNG = "kuendigung"  # Termination notice / Résiliation / Disdetta
    MANDATSBESTAETIGUNG = (
        "mandatsbestaetigung"  # Engagement letter / Confirmation de mandat / Conferma mandato
    )

    @property
    def display_name(self) -> dict[str, str]:
        """Return document type name in multiple languages."""
        names = {
            DocumentType.KLAGESCHRIFT: {
                "de": "Klageschrift",
                "fr": "Demande",
                "it": "Petizione",
                "en": "Statement of Claim",
            },
            DocumentType.KLAGEANTWORT: {
                "de": "Klageantwort",
                "fr": "Réponse",
                "it": "Risposta",
                "en": "Statement of Defense",
            },
            DocumentType.REPLIK: {
                "de": "Replik",
                "fr": "Réplique",
                "it": "Replica",
                "en": "Reply",
            },
            DocumentType.DUPLIK: {
                "de": "Duplik",
                "fr": "Duplique",
                "it": "Duplica",
                "en": "Rejoinder",
            },
            DocumentType.BERUFUNG: {
                "de": "Berufung",
                "fr": "Appel",
                "it": "Appello",
                "en": "Appeal",
            },
            DocumentType.BESCHWERDE: {
                "de": "Beschwerde",
                "fr": "Recours",
                "it": "Ricorso",
                "en": "Complaint",
            },
            DocumentType.STELLUNGNAHME: {
                "de": "Stellungnahme",
                "fr": "Détermination",
                "it": "Osservazioni",
                "en": "Statement",
            },
            DocumentType.RECHTSGUTACHTEN: {
                "de": "Rechtsgutachten",
                "fr": "Avis de droit",
                "it": "Parere legale",
                "en": "Legal Opinion",
            },
            DocumentType.MEMORANDUM: {
                "de": "Memorandum",
                "fr": "Mémorandum",
                "it": "Memorandum",
                "en": "Legal Memorandum",
            },
            DocumentType.KURZGUTACHTEN: {
                "de": "Kurzgutachten",
                "fr": "Avis succinct",
                "it": "Parere breve",
                "en": "Brief Opinion",
            },
            DocumentType.VERTRAG: {
                "de": "Vertrag",
                "fr": "Contrat",
                "it": "Contratto",
                "en": "Contract",
            },
            DocumentType.VEREINBARUNG: {
                "de": "Vereinbarung",
                "fr": "Convention",
                "it": "Convenzione",
                "en": "Agreement",
            },
            DocumentType.KAUFVERTRAG: {
                "de": "Kaufvertrag",
                "fr": "Contrat de vente",
                "it": "Contratto di vendita",
                "en": "Sales Contract",
            },
            DocumentType.MIETVERTRAG: {
                "de": "Mietvertrag",
                "fr": "Bail",
                "it": "Contratto di locazione",
                "en": "Lease Agreement",
            },
            DocumentType.ARBEITSVERTRAG: {
                "de": "Arbeitsvertrag",
                "fr": "Contrat de travail",
                "it": "Contratto di lavoro",
                "en": "Employment Contract",
            },
            DocumentType.MAHNUNG: {
                "de": "Mahnung",
                "fr": "Mise en demeure",
                "it": "Diffida",
                "en": "Formal Notice",
            },
            DocumentType.KUENDIGUNG: {
                "de": "Kündigung",
                "fr": "Résiliation",
                "it": "Disdetta",
                "en": "Termination Notice",
            },
            DocumentType.MANDATSBESTAETIGUNG: {
                "de": "Mandatsbestätigung",
                "fr": "Confirmation de mandat",
                "it": "Conferma mandato",
                "en": "Engagement Letter",
            },
        }
        return names[self]

    @property
    def category(self) -> str:
        """Return document category."""
        submissions = {
            DocumentType.KLAGESCHRIFT,
            DocumentType.KLAGEANTWORT,
            DocumentType.REPLIK,
            DocumentType.DUPLIK,
            DocumentType.BERUFUNG,
            DocumentType.BESCHWERDE,
            DocumentType.STELLUNGNAHME,
        }
        opinions = {
            DocumentType.RECHTSGUTACHTEN,
            DocumentType.MEMORANDUM,
            DocumentType.KURZGUTACHTEN,
        }
        contracts = {
            DocumentType.VERTRAG,
            DocumentType.VEREINBARUNG,
            DocumentType.KAUFVERTRAG,
            DocumentType.MIETVERTRAG,
            DocumentType.ARBEITSVERTRAG,
        }

        if self in submissions:
            return "submission"
        elif self in opinions:
            return "opinion"
        elif self in contracts:
            return "contract"
        else:
            return "correspondence"

    @property
    def requires_court(self) -> bool:
        """Determine if document type requires court information."""
        return self.category == "submission"


class DocumentSectionType(Enum):
    """
    Standard document sections for Swiss legal documents.

    Abschnitte / Sections / Sezioni

    Used to structure documents according to Swiss practice.
    """

    # Court submissions
    RUBRUM = "rubrum"  # Header with parties
    RECHTSBEGEHREN = "rechtsbegehren"  # Legal requests/prayers for relief
    SACHVERHALT = "sachverhalt"  # Statement of facts
    RECHTLICHES = "rechtliches"  # Legal arguments
    BEWEISMITTEL = "beweismittel"  # Evidence/Exhibits
    SCHLUSSFOLGERUNG = "schlussfolgerung"  # Conclusion

    # Legal opinions
    FRAGESTELLUNG = "fragestellung"  # Legal question
    ZUSAMMENFASSUNG = "zusammenfassung"  # Executive summary
    ANALYSE = "analyse"  # Analysis
    EMPFEHLUNG = "empfehlung"  # Recommendation

    # Contracts
    PRAEAMBEL = "praeambel"  # Preamble
    DEFINITIONEN = "definitionen"  # Definitions
    HAUPTTEIL = "hauptteil"  # Main body
    SCHLUSSBESTIMMUNGEN = "schlussbestimmungen"  # Final provisions
    UNTERSCHRIFTEN = "unterschriften"  # Signatures

    @property
    def display_name(self) -> dict[str, str]:
        """Return section name in multiple languages."""
        names = {
            DocumentSectionType.RUBRUM: {
                "de": "Rubrum",
                "fr": "Rubrique",
                "it": "Rubrica",
                "en": "Header",
            },
            DocumentSectionType.RECHTSBEGEHREN: {
                "de": "Rechtsbegehren",
                "fr": "Conclusions",
                "it": "Conclusioni",
                "en": "Prayers for Relief",
            },
            DocumentSectionType.SACHVERHALT: {
                "de": "Sachverhalt",
                "fr": "État de fait",
                "it": "Fatti",
                "en": "Statement of Facts",
            },
            DocumentSectionType.RECHTLICHES: {
                "de": "Rechtliches",
                "fr": "En droit",
                "it": "In diritto",
                "en": "Legal Arguments",
            },
            DocumentSectionType.BEWEISMITTEL: {
                "de": "Beweismittel",
                "fr": "Moyens de preuve",
                "it": "Mezzi di prova",
                "en": "Evidence",
            },
            DocumentSectionType.SCHLUSSFOLGERUNG: {
                "de": "Schlussfolgerung",
                "fr": "Conclusion",
                "it": "Conclusione",
                "en": "Conclusion",
            },
            DocumentSectionType.FRAGESTELLUNG: {
                "de": "Fragestellung",
                "fr": "Question juridique",
                "it": "Quesito",
                "en": "Legal Question",
            },
            DocumentSectionType.ZUSAMMENFASSUNG: {
                "de": "Zusammenfassung",
                "fr": "Résumé",
                "it": "Sintesi",
                "en": "Executive Summary",
            },
            DocumentSectionType.ANALYSE: {
                "de": "Analyse",
                "fr": "Analyse",
                "it": "Analisi",
                "en": "Analysis",
            },
            DocumentSectionType.EMPFEHLUNG: {
                "de": "Empfehlung",
                "fr": "Recommandation",
                "it": "Raccomandazione",
                "en": "Recommendation",
            },
            DocumentSectionType.PRAEAMBEL: {
                "de": "Präambel",
                "fr": "Préambule",
                "it": "Preambolo",
                "en": "Preamble",
            },
            DocumentSectionType.DEFINITIONEN: {
                "de": "Definitionen",
                "fr": "Définitions",
                "it": "Definizioni",
                "en": "Definitions",
            },
            DocumentSectionType.HAUPTTEIL: {
                "de": "Hauptteil",
                "fr": "Corps du contrat",
                "it": "Parte principale",
                "en": "Main Body",
            },
            DocumentSectionType.SCHLUSSBESTIMMUNGEN: {
                "de": "Schlussbestimmungen",
                "fr": "Dispositions finales",
                "it": "Disposizioni finali",
                "en": "Final Provisions",
            },
            DocumentSectionType.UNTERSCHRIFTEN: {
                "de": "Unterschriften",
                "fr": "Signatures",
                "it": "Firme",
                "en": "Signatures",
            },
        }
        return names[self]


@dataclass
class DocumentMetadata:
    """
    Metadata for a legal document.

    Dokumentmetadaten / Métadonnées du document / Metadati del documento

    Attributes:
        document_type: Type of legal document
        language: Document language
        jurisdiction: Applicable jurisdiction
        case_reference: Court case reference number
        court: Target court name
        date_created: Document creation date
        author: Document author
        client_reference: Internal client reference
        version: Document version
    """

    document_type: DocumentType
    language: Language
    jurisdiction: Jurisdiction
    case_reference: str | None = None
    court: str | None = None
    date_created: str | None = None
    author: str | None = None
    client_reference: str | None = None
    version: str = "1.0"

    def __post_init__(self) -> None:
        """Set default court name if not provided."""
        if self.court is None and self.document_type.requires_court:
            self.court = self.jurisdiction.court_name.get(self.language.value, "")

    def to_dict(self) -> dict[str, Any]:
        """Serialize metadata to dictionary."""
        return {
            "document_type": self.document_type.value,
            "language": self.language.value,
            "jurisdiction": self.jurisdiction.value,
            "case_reference": self.case_reference,
            "court": self.court,
            "date_created": self.date_created,
            "author": self.author,
            "client_reference": self.client_reference,
            "version": self.version,
        }


@dataclass
class Citation:
    """
    Legal citation reference.

    Zitat / Citation / Citazione

    Attributes:
        citation_text: Full citation text (e.g., "BGE 123 III 456")
        source_type: Type of source (bge, cantonal, doctrine, legislation)
        is_verified: Whether citation has been verified
        url: URL to source if available
        relevance: Relevance description
    """

    citation_text: str
    source_type: str = "unknown"  # bge, cantonal, doctrine, legislation
    is_verified: bool = False
    url: str | None = None
    relevance: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize citation to dictionary."""
        return {
            "citation_text": self.citation_text,
            "source_type": self.source_type,
            "is_verified": self.is_verified,
            "url": self.url,
            "relevance": self.relevance,
        }


@dataclass
class DocumentSection:
    """
    Individual section within a legal document.

    Dokumentabschnitt / Section du document / Sezione del documento

    Attributes:
        section_type: Type of section
        title: Section title
        content: Section content
        citations: Legal citations in this section
        footnotes: Footnotes for this section
        subsections: Nested subsections
        order: Order within document
    """

    section_type: str
    title: str
    content: str
    citations: list[Citation] = field(default_factory=list)
    footnotes: list[str] = field(default_factory=list)
    subsections: list["DocumentSection"] = field(default_factory=list)
    order: int = 0

    @property
    def word_count(self) -> int:
        """Calculate word count for this section."""
        count = len(self.content.split())
        for subsection in self.subsections:
            count += subsection.word_count
        return count

    @property
    def citation_count(self) -> int:
        """Count citations in this section and subsections."""
        count = len(self.citations)
        for subsection in self.subsections:
            count += subsection.citation_count
        return count

    def to_dict(self) -> dict[str, Any]:
        """Serialize section to dictionary."""
        return {
            "section_type": self.section_type,
            "title": self.title,
            "content": self.content,
            "citations": [c.to_dict() for c in self.citations],
            "footnotes": self.footnotes,
            "subsections": [s.to_dict() for s in self.subsections],
            "order": self.order,
            "word_count": self.word_count,
            "citation_count": self.citation_count,
        }


@dataclass
class LegalDocument:
    """
    Complete legal document output from DrafterAgent.

    Rechtsdokument / Document juridique / Documento legale

    Attributes:
        metadata: Document metadata
        sections: Document sections
        full_text: Complete rendered document text
        word_count: Total word count
        page_estimate: Estimated page count
        citations_used: All citations used in document
        checkpoints_requested: Checkpoints triggered during generation
        parties: Parties involved (for submissions)
        bilingual_version: Document in alternate language (if generated)
    """

    metadata: DocumentMetadata
    sections: list[DocumentSection] = field(default_factory=list)
    full_text: str = ""
    word_count: int = 0
    page_estimate: int = 0
    citations_used: list[Citation] = field(default_factory=list)
    checkpoints_requested: list[str] = field(default_factory=list)
    parties: list[LegalParty] = field(default_factory=list)
    bilingual_version: Optional["LegalDocument"] = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self) -> None:
        """Calculate word count and page estimate if not set."""
        if self.word_count == 0 and self.sections:
            self.word_count = sum(s.word_count for s in self.sections)
        if self.page_estimate == 0 and self.word_count > 0:
            # Estimate ~300 words per page for legal documents
            self.page_estimate = max(1, self.word_count // 300)

    @property
    def requires_checkpoint(self) -> bool:
        """Determine if document requires checkpoint (>5000 words)."""
        return self.word_count > 5000

    @property
    def unverified_citations(self) -> list[Citation]:
        """Return list of unverified citations."""
        return [c for c in self.citations_used if not c.is_verified]

    @property
    def has_unverified_citations(self) -> bool:
        """Check if document has unverified citations."""
        return len(self.unverified_citations) > 0

    def get_section(self, section_type: str) -> DocumentSection | None:
        """Get section by type."""
        for section in self.sections:
            if section.section_type == section_type:
                return section
        return None

    def add_section(self, section: DocumentSection) -> None:
        """Add a section to the document."""
        section.order = len(self.sections)
        self.sections.append(section)
        self.word_count += section.word_count
        self.page_estimate = max(1, self.word_count // 300)

    def render_full_text(self) -> str:
        """Render complete document text from sections."""
        parts = []
        for section in sorted(self.sections, key=lambda s: s.order):
            if section.title:
                parts.append(f"\n## {section.title}\n")
            parts.append(section.content)
            if section.footnotes:
                parts.append("\n---\n")
                for i, footnote in enumerate(section.footnotes, 1):
                    parts.append(f"[{i}] {footnote}\n")
        self.full_text = "\n".join(parts)
        return self.full_text

    def to_dict(self) -> dict[str, Any]:
        """Serialize document to dictionary."""
        return {
            "metadata": self.metadata.to_dict(),
            "sections": [s.to_dict() for s in self.sections],
            "full_text": self.full_text,
            "word_count": self.word_count,
            "page_estimate": self.page_estimate,
            "citations_used": [c.to_dict() for c in self.citations_used],
            "checkpoints_requested": self.checkpoints_requested,
            "parties": [
                {
                    "name": p.name,
                    "role": p.role,
                    "representation": p.representation,
                }
                for p in self.parties
            ],
            "has_bilingual": self.bilingual_version is not None,
            "created_at": self.created_at.isoformat(),
            "requires_checkpoint": self.requires_checkpoint,
            "has_unverified_citations": self.has_unverified_citations,
        }

    def get_summary(self, language: Language = Language.DE) -> str:
        """Generate document summary in specified language."""
        templates = {
            Language.DE: """
Dokument: {doc_type}
Sprache: {lang}
Gerichtsbarkeit: {jurisdiction}
Seitenanzahl: ca. {pages}
Wortanzahl: {words}
Zitationen: {citations}
            """,
            Language.FR: """
Document: {doc_type}
Langue: {lang}
Juridiction: {jurisdiction}
Nombre de pages: env. {pages}
Nombre de mots: {words}
Citations: {citations}
            """,
            Language.IT: """
Documento: {doc_type}
Lingua: {lang}
Giurisdizione: {jurisdiction}
Numero di pagine: ca. {pages}
Numero di parole: {words}
Citazioni: {citations}
            """,
            Language.EN: """
Document: {doc_type}
Language: {lang}
Jurisdiction: {jurisdiction}
Page Count: approx. {pages}
Word Count: {words}
Citations: {citations}
            """,
        }

        return (
            templates[language]
            .format(
                doc_type=self.metadata.document_type.display_name[language.value],
                lang=self.metadata.language.display_name,
                jurisdiction=self.metadata.jurisdiction.value,
                pages=self.page_estimate,
                words=self.word_count,
                citations=len(self.citations_used),
            )
            .strip()
        )
