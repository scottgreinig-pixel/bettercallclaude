"""
Shared Data Models for BetterCallClaude Agent Framework

This module provides foundational enums and dataclasses shared across all agents.
Designed for Swiss legal context with support for DE, FR, IT, EN languages.

Terminology Reference:
    DE: Deutsch (German) - Primary language for Bundesgericht
    FR: Français (French) - Primary language for Tribunal fédéral
    IT: Italiano (Italian) - Primary language for Tribunale federale
    EN: English - International clients and documentation
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class Language(Enum):
    """
    Supported languages for Swiss legal intelligence.

    Switzerland's four national languages plus English for international clients.
    Default is German (DE) as the most common language in Swiss legal practice.

    Sprachen / Langues / Lingue:
        DE: Deutsch / Allemand / Tedesco
        FR: Français / Français / Francese
        IT: Italiano / Italien / Italiano
        EN: English (international)
    """

    DE = "de"  # Deutsch / German
    FR = "fr"  # Français / French
    IT = "it"  # Italiano / Italian
    EN = "en"  # English

    @property
    def display_name(self) -> str:
        """Return the display name in the respective language."""
        names = {
            Language.DE: "Deutsch",
            Language.FR: "Français",
            Language.IT: "Italiano",
            Language.EN: "English",
        }
        return names[self]

    @classmethod
    def from_string(cls, value: str) -> "Language":
        """Parse language from string, case-insensitive."""
        normalized = value.lower().strip()
        for lang in cls:
            if lang.value == normalized or lang.display_name.lower() == normalized:
                return lang
        raise ValueError(f"Unknown language: {value}")


class RiskLevel(Enum):
    """
    Risk assessment levels for legal strategy evaluation.

    Used by StrategistAgent for litigation, cost, and reputation risk assessment.

    Risikostufen / Niveaux de risque / Livelli di rischio:
        VERY_LOW: Sehr gering / Très faible / Molto basso
        LOW: Gering / Faible / Basso
        MEDIUM: Mittel / Moyen / Medio
        HIGH: Hoch / Élevé / Alto
        VERY_HIGH: Sehr hoch / Très élevé / Molto alto
    """

    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"

    @property
    def numeric_score(self) -> float:
        """Return numeric score (0.0 to 1.0) for calculations."""
        scores = {
            RiskLevel.VERY_LOW: 0.1,
            RiskLevel.LOW: 0.3,
            RiskLevel.MEDIUM: 0.5,
            RiskLevel.HIGH: 0.7,
            RiskLevel.VERY_HIGH: 0.9,
        }
        return scores[self]

    @property
    def requires_checkpoint(self) -> bool:
        """Determine if this risk level requires a checkpoint in BALANCED mode."""
        return self in (RiskLevel.HIGH, RiskLevel.VERY_HIGH)


class Jurisdiction(Enum):
    """
    Swiss jurisdictions for legal document formatting and court procedures.

    All 26 Swiss cantons plus federal level (Bund/Confédération/Confederazione).

    Gerichtsbarkeiten / Juridictions / Giurisdizioni:
        FEDERAL: Bundesgericht / Tribunal fédéral / Tribunale federale

    German-speaking cantons (Deutschschweiz):
        ZH: Zürich / Zurich / Zurigo
        BE: Bern / Berne / Berna (bilingual DE/FR)
        LU: Luzern / Lucerne / Lucerna
        UR: Uri / Uri / Uri
        SZ: Schwyz / Schwytz / Svitto
        OW: Obwalden / Obwald / Obvaldo
        NW: Nidwalden / Nidwald / Nidvaldo
        GL: Glarus / Glaris / Glarona
        ZG: Zug / Zoug / Zugo
        SO: Solothurn / Soleure / Soletta
        BS: Basel-Stadt / Bâle-Ville / Basilea Città
        BL: Basel-Landschaft / Bâle-Campagne / Basilea Campagna
        SH: Schaffhausen / Schaffhouse / Sciaffusa
        AR: Appenzell Ausserrhoden / Appenzell Rhodes-Extérieures / Appenzello Esterno
        AI: Appenzell Innerrhoden / Appenzell Rhodes-Intérieures / Appenzello Interno
        SG: St. Gallen / Saint-Gall / San Gallo
        GR: Graubünden / Grisons / Grigioni (trilingual DE/IT/RM)
        AG: Aargau / Argovie / Argovia
        TG: Thurgau / Thurgovie / Turgovia

    French-speaking cantons (Romandie):
        FR: Freiburg / Fribourg / Friburgo (bilingual DE/FR)
        VD: Waadt / Vaud / Vaud
        VS: Wallis / Valais / Vallese (bilingual DE/FR)
        NE: Neuenburg / Neuchâtel / Neuchâtel
        GE: Genf / Genève / Ginevra
        JU: Jura / Jura / Giura

    Italian-speaking cantons (Svizzera italiana):
        TI: Tessin / Tessin / Ticino
    """

    # Federal
    FEDERAL = "federal"

    # German-speaking cantons
    ZH = "zurich"
    BE = "bern"
    LU = "lucerne"
    UR = "uri"
    SZ = "schwyz"
    OW = "obwalden"
    NW = "nidwalden"
    GL = "glarus"
    ZG = "zug"
    SO = "solothurn"
    BS = "basel_stadt"
    BL = "basel_land"
    SH = "schaffhausen"
    AR = "appenzell_ar"
    AI = "appenzell_ir"
    SG = "st_gallen"
    GR = "graubuenden"
    AG = "aargau"
    TG = "thurgau"

    # French-speaking cantons
    FR = "fribourg"
    VD = "vaud"
    VS = "valais"
    NE = "neuchatel"
    GE = "geneva"
    JU = "jura"

    # Italian-speaking cantons
    TI = "ticino"

    @property
    def primary_language(self) -> Language:
        """Return the primary language for this jurisdiction."""
        # French-speaking cantons
        french_cantons = {
            Jurisdiction.GE,
            Jurisdiction.VD,
            Jurisdiction.NE,
            Jurisdiction.JU,
        }
        # Italian-speaking cantons
        italian_cantons = {Jurisdiction.TI}
        # Note: Bilingual cantons (BE, FR, VS) are handled explicitly below

        if self in french_cantons:
            return Language.FR
        elif self == Jurisdiction.FR:
            return Language.FR  # Fribourg officially bilingual, but FR majority
        elif self == Jurisdiction.VS:
            return Language.FR  # Valais officially bilingual, but FR majority
        elif self in italian_cantons:
            return Language.IT
        else:
            return Language.DE  # All other cantons including BE, GR (trilingual)

    @property
    def is_bilingual(self) -> bool:
        """Check if the canton is officially bilingual or trilingual."""
        multilingual = {
            Jurisdiction.BE,  # DE/FR
            Jurisdiction.FR,  # DE/FR
            Jurisdiction.VS,  # DE/FR
            Jurisdiction.GR,  # DE/IT/RM (Romansh)
        }
        return self in multilingual

    @property
    def official_languages(self) -> list[Language]:
        """Return all official languages for this jurisdiction."""
        lang_map = {
            Jurisdiction.FEDERAL: [Language.DE, Language.FR, Language.IT],
            Jurisdiction.BE: [Language.DE, Language.FR],
            Jurisdiction.FR: [Language.DE, Language.FR],
            Jurisdiction.VS: [Language.DE, Language.FR],
            Jurisdiction.GR: [Language.DE, Language.IT],  # Romansh not in enum
            Jurisdiction.GE: [Language.FR],
            Jurisdiction.VD: [Language.FR],
            Jurisdiction.NE: [Language.FR],
            Jurisdiction.JU: [Language.FR],
            Jurisdiction.TI: [Language.IT],
        }
        # Default to German for all other cantons
        return lang_map.get(self, [Language.DE])

    @property
    def court_name(self) -> dict[str, str]:
        """Return highest cantonal court names in multiple languages."""
        names = {
            Jurisdiction.FEDERAL: {
                "de": "Bundesgericht",
                "fr": "Tribunal fédéral",
                "it": "Tribunale federale",
                "en": "Federal Supreme Court",
            },
            Jurisdiction.ZH: {
                "de": "Obergericht des Kantons Zürich",
                "fr": "Tribunal supérieur du canton de Zurich",
                "it": "Tribunale superiore del Canton Zurigo",
                "en": "High Court of the Canton of Zurich",
            },
            Jurisdiction.BE: {
                "de": "Obergericht des Kantons Bern",
                "fr": "Cour suprême du canton de Berne",
                "it": "Tribunale superiore del Canton Berna",
                "en": "High Court of the Canton of Bern",
            },
            Jurisdiction.LU: {
                "de": "Kantonsgericht Luzern",
                "fr": "Tribunal cantonal de Lucerne",
                "it": "Tribunale cantonale di Lucerna",
                "en": "Cantonal Court of Lucerne",
            },
            Jurisdiction.UR: {
                "de": "Obergericht des Kantons Uri",
                "fr": "Tribunal supérieur du canton d'Uri",
                "it": "Tribunale superiore del Canton Uri",
                "en": "High Court of the Canton of Uri",
            },
            Jurisdiction.SZ: {
                "de": "Kantonsgericht Schwyz",
                "fr": "Tribunal cantonal de Schwytz",
                "it": "Tribunale cantonale di Svitto",
                "en": "Cantonal Court of Schwyz",
            },
            Jurisdiction.OW: {
                "de": "Obergericht des Kantons Obwalden",
                "fr": "Tribunal supérieur du canton d'Obwald",
                "it": "Tribunale superiore del Canton Obvaldo",
                "en": "High Court of the Canton of Obwalden",
            },
            Jurisdiction.NW: {
                "de": "Obergericht des Kantons Nidwalden",
                "fr": "Tribunal supérieur du canton de Nidwald",
                "it": "Tribunale superiore del Canton Nidvaldo",
                "en": "High Court of the Canton of Nidwalden",
            },
            Jurisdiction.GL: {
                "de": "Obergericht des Kantons Glarus",
                "fr": "Tribunal supérieur du canton de Glaris",
                "it": "Tribunale superiore del Canton Glarona",
                "en": "High Court of the Canton of Glarus",
            },
            Jurisdiction.ZG: {
                "de": "Obergericht des Kantons Zug",
                "fr": "Tribunal supérieur du canton de Zoug",
                "it": "Tribunale superiore del Canton Zugo",
                "en": "High Court of the Canton of Zug",
            },
            Jurisdiction.SO: {
                "de": "Obergericht des Kantons Solothurn",
                "fr": "Tribunal supérieur du canton de Soleure",
                "it": "Tribunale superiore del Canton Soletta",
                "en": "High Court of the Canton of Solothurn",
            },
            Jurisdiction.BS: {
                "de": "Appellationsgericht Basel-Stadt",
                "fr": "Cour d'appel de Bâle-Ville",
                "it": "Corte d'appello di Basilea Città",
                "en": "Court of Appeal of Basel-City",
            },
            Jurisdiction.BL: {
                "de": "Kantonsgericht Basel-Landschaft",
                "fr": "Tribunal cantonal de Bâle-Campagne",
                "it": "Tribunale cantonale di Basilea Campagna",
                "en": "Cantonal Court of Basel-Landschaft",
            },
            Jurisdiction.SH: {
                "de": "Obergericht des Kantons Schaffhausen",
                "fr": "Tribunal supérieur du canton de Schaffhouse",
                "it": "Tribunale superiore del Canton Sciaffusa",
                "en": "High Court of the Canton of Schaffhausen",
            },
            Jurisdiction.AR: {
                "de": "Obergericht Appenzell Ausserrhoden",
                "fr": "Tribunal supérieur d'Appenzell Rhodes-Extérieures",
                "it": "Tribunale superiore di Appenzello Esterno",
                "en": "High Court of Appenzell Ausserrhoden",
            },
            Jurisdiction.AI: {
                "de": "Kantonsgericht Appenzell Innerrhoden",
                "fr": "Tribunal cantonal d'Appenzell Rhodes-Intérieures",
                "it": "Tribunale cantonale di Appenzello Interno",
                "en": "Cantonal Court of Appenzell Innerrhoden",
            },
            Jurisdiction.SG: {
                "de": "Kantonsgericht St. Gallen",
                "fr": "Tribunal cantonal de Saint-Gall",
                "it": "Tribunale cantonale di San Gallo",
                "en": "Cantonal Court of St. Gallen",
            },
            Jurisdiction.GR: {
                "de": "Kantonsgericht Graubünden",
                "fr": "Tribunal cantonal des Grisons",
                "it": "Tribunale cantonale dei Grigioni",
                "en": "Cantonal Court of Graubünden",
            },
            Jurisdiction.AG: {
                "de": "Obergericht des Kantons Aargau",
                "fr": "Tribunal supérieur du canton d'Argovie",
                "it": "Tribunale superiore del Canton Argovia",
                "en": "High Court of the Canton of Aargau",
            },
            Jurisdiction.TG: {
                "de": "Obergericht des Kantons Thurgau",
                "fr": "Tribunal supérieur du canton de Thurgovie",
                "it": "Tribunale superiore del Canton Turgovia",
                "en": "High Court of the Canton of Thurgau",
            },
            Jurisdiction.FR: {
                "de": "Kantonsgericht Freiburg",
                "fr": "Tribunal cantonal de Fribourg",
                "it": "Tribunale cantonale di Friburgo",
                "en": "Cantonal Court of Fribourg",
            },
            Jurisdiction.VD: {
                "de": "Kantonsgericht Waadt",
                "fr": "Tribunal cantonal vaudois",
                "it": "Tribunale cantonale vodese",
                "en": "Cantonal Court of Vaud",
            },
            Jurisdiction.VS: {
                "de": "Kantonsgericht Wallis",
                "fr": "Tribunal cantonal du Valais",
                "it": "Tribunale cantonale del Vallese",
                "en": "Cantonal Court of Valais",
            },
            Jurisdiction.NE: {
                "de": "Kantonsgericht Neuenburg",
                "fr": "Tribunal cantonal de Neuchâtel",
                "it": "Tribunale cantonale di Neuchâtel",
                "en": "Cantonal Court of Neuchâtel",
            },
            Jurisdiction.GE: {
                "de": "Kantonsgericht Genf",
                "fr": "Cour de justice de Genève",
                "it": "Corte di giustizia di Ginevra",
                "en": "Court of Justice of Geneva",
            },
            Jurisdiction.JU: {
                "de": "Kantonsgericht Jura",
                "fr": "Tribunal cantonal du Jura",
                "it": "Tribunale cantonale del Giura",
                "en": "Cantonal Court of Jura",
            },
            Jurisdiction.TI: {
                "de": "Kantonsgericht Tessin",
                "fr": "Tribunal cantonal du Tessin",
                "it": "Tribunale d'appello del Cantone Ticino",
                "en": "Court of Appeal of Ticino",
            },
        }
        return names[self]

    @property
    def canton_name(self) -> dict[str, str]:
        """Return canton names in multiple languages."""
        names = {
            Jurisdiction.FEDERAL: {
                "de": "Bund",
                "fr": "Confédération",
                "it": "Confederazione",
                "en": "Federal",
            },
            Jurisdiction.ZH: {
                "de": "Zürich",
                "fr": "Zurich",
                "it": "Zurigo",
                "en": "Zurich",
            },
            Jurisdiction.BE: {
                "de": "Bern",
                "fr": "Berne",
                "it": "Berna",
                "en": "Bern",
            },
            Jurisdiction.LU: {
                "de": "Luzern",
                "fr": "Lucerne",
                "it": "Lucerna",
                "en": "Lucerne",
            },
            Jurisdiction.UR: {
                "de": "Uri",
                "fr": "Uri",
                "it": "Uri",
                "en": "Uri",
            },
            Jurisdiction.SZ: {
                "de": "Schwyz",
                "fr": "Schwytz",
                "it": "Svitto",
                "en": "Schwyz",
            },
            Jurisdiction.OW: {
                "de": "Obwalden",
                "fr": "Obwald",
                "it": "Obvaldo",
                "en": "Obwalden",
            },
            Jurisdiction.NW: {
                "de": "Nidwalden",
                "fr": "Nidwald",
                "it": "Nidvaldo",
                "en": "Nidwalden",
            },
            Jurisdiction.GL: {
                "de": "Glarus",
                "fr": "Glaris",
                "it": "Glarona",
                "en": "Glarus",
            },
            Jurisdiction.ZG: {
                "de": "Zug",
                "fr": "Zoug",
                "it": "Zugo",
                "en": "Zug",
            },
            Jurisdiction.SO: {
                "de": "Solothurn",
                "fr": "Soleure",
                "it": "Soletta",
                "en": "Solothurn",
            },
            Jurisdiction.BS: {
                "de": "Basel-Stadt",
                "fr": "Bâle-Ville",
                "it": "Basilea Città",
                "en": "Basel-City",
            },
            Jurisdiction.BL: {
                "de": "Basel-Landschaft",
                "fr": "Bâle-Campagne",
                "it": "Basilea Campagna",
                "en": "Basel-Landschaft",
            },
            Jurisdiction.SH: {
                "de": "Schaffhausen",
                "fr": "Schaffhouse",
                "it": "Sciaffusa",
                "en": "Schaffhausen",
            },
            Jurisdiction.AR: {
                "de": "Appenzell Ausserrhoden",
                "fr": "Appenzell Rhodes-Extérieures",
                "it": "Appenzello Esterno",
                "en": "Appenzell Ausserrhoden",
            },
            Jurisdiction.AI: {
                "de": "Appenzell Innerrhoden",
                "fr": "Appenzell Rhodes-Intérieures",
                "it": "Appenzello Interno",
                "en": "Appenzell Innerrhoden",
            },
            Jurisdiction.SG: {
                "de": "St. Gallen",
                "fr": "Saint-Gall",
                "it": "San Gallo",
                "en": "St. Gallen",
            },
            Jurisdiction.GR: {
                "de": "Graubünden",
                "fr": "Grisons",
                "it": "Grigioni",
                "en": "Graubünden",
            },
            Jurisdiction.AG: {
                "de": "Aargau",
                "fr": "Argovie",
                "it": "Argovia",
                "en": "Aargau",
            },
            Jurisdiction.TG: {
                "de": "Thurgau",
                "fr": "Thurgovie",
                "it": "Turgovia",
                "en": "Thurgau",
            },
            Jurisdiction.FR: {
                "de": "Freiburg",
                "fr": "Fribourg",
                "it": "Friburgo",
                "en": "Fribourg",
            },
            Jurisdiction.VD: {
                "de": "Waadt",
                "fr": "Vaud",
                "it": "Vaud",
                "en": "Vaud",
            },
            Jurisdiction.VS: {
                "de": "Wallis",
                "fr": "Valais",
                "it": "Vallese",
                "en": "Valais",
            },
            Jurisdiction.NE: {
                "de": "Neuenburg",
                "fr": "Neuchâtel",
                "it": "Neuchâtel",
                "en": "Neuchâtel",
            },
            Jurisdiction.GE: {
                "de": "Genf",
                "fr": "Genève",
                "it": "Ginevra",
                "en": "Geneva",
            },
            Jurisdiction.JU: {
                "de": "Jura",
                "fr": "Jura",
                "it": "Giura",
                "en": "Jura",
            },
            Jurisdiction.TI: {
                "de": "Tessin",
                "fr": "Tessin",
                "it": "Ticino",
                "en": "Ticino",
            },
        }
        return names[self]

    @classmethod
    def from_string(cls, value: str) -> "Jurisdiction":
        """Parse jurisdiction from string (canton code or name)."""
        normalized = value.upper().strip()
        original = value.strip()
        # Try direct enum name match
        for jurisdiction in cls:
            if jurisdiction.name == normalized:
                return jurisdiction
        # Try value match
        for jurisdiction in cls:
            if jurisdiction.value.upper() == normalized:
                return jurisdiction
        # Try canton name match (in any language)
        for jurisdiction in cls:
            names = jurisdiction.canton_name
            for lang_name in names.values():
                if lang_name.lower() == original.lower():
                    return jurisdiction
        raise ValueError(f"Unknown jurisdiction: {value}")


@dataclass
class LegalParty:
    """
    Represents a party in legal proceedings.

    Partei / Partie / Parte in legal proceedings with role designation.

    Attributes:
        name: Full legal name of the party
        role: Legal role (plaintiff, defendant, appellant, respondent, etc.)
        representation: Legal representative (lawyer/firm)
        language_preference: Preferred language for communications
        address: Contact address (optional)
        metadata: Additional party information
    """

    name: str
    role: str  # plaintiff, defendant, appellant, respondent, intervenor
    representation: str | None = None
    language_preference: Language = Language.DE
    address: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def role_translated(self) -> dict[str, str]:
        """Return role in multiple languages."""
        role_translations = {
            "plaintiff": {
                "de": "Kläger",
                "fr": "Demandeur",
                "it": "Attore",
                "en": "Plaintiff",
            },
            "defendant": {
                "de": "Beklagter",
                "fr": "Défendeur",
                "it": "Convenuto",
                "en": "Defendant",
            },
            "appellant": {
                "de": "Berufungskläger",
                "fr": "Appelant",
                "it": "Appellante",
                "en": "Appellant",
            },
            "respondent": {
                "de": "Berufungsbeklagter",
                "fr": "Intimé",
                "it": "Appellato",
                "en": "Respondent",
            },
            "intervenor": {
                "de": "Nebenintervenient",
                "fr": "Intervenant",
                "it": "Interveniente",
                "en": "Intervenor",
            },
        }
        return role_translations.get(
            self.role.lower(),
            {"de": self.role, "fr": self.role, "it": self.role, "en": self.role},
        )


@dataclass
class CaseFacts:
    """
    Structured representation of case facts for analysis.

    Sachverhalt / État de fait / Fatti for legal analysis and strategy development.

    Attributes:
        summary: Brief summary of the case (1-3 sentences)
        key_events: Chronological list of key events with dates
        disputed_facts: Facts contested by parties
        undisputed_facts: Facts agreed upon by all parties
        evidence_available: List of available evidence items
        legal_questions: Legal questions to be addressed
        value_in_dispute: Amount in dispute (CHF)
        created_at: Timestamp of fact compilation
    """

    summary: str
    key_events: list[dict[str, Any]] = field(default_factory=list)
    disputed_facts: list[str] = field(default_factory=list)
    undisputed_facts: list[str] = field(default_factory=list)
    evidence_available: list[str] = field(default_factory=list)
    legal_questions: list[str] = field(default_factory=list)
    value_in_dispute: float | None = None  # CHF
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        """Serialize case facts to dictionary."""
        return {
            "summary": self.summary,
            "key_events": self.key_events,
            "disputed_facts": self.disputed_facts,
            "undisputed_facts": self.undisputed_facts,
            "evidence_available": self.evidence_available,
            "legal_questions": self.legal_questions,
            "value_in_dispute": self.value_in_dispute,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CaseFacts":
        """Create CaseFacts from dictionary."""
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        elif created_at is None:
            created_at = datetime.utcnow()

        return cls(
            summary=data.get("summary", ""),
            key_events=data.get("key_events", []),
            disputed_facts=data.get("disputed_facts", []),
            undisputed_facts=data.get("undisputed_facts", []),
            evidence_available=data.get("evidence_available", []),
            legal_questions=data.get("legal_questions", []),
            value_in_dispute=data.get("value_in_dispute"),
            created_at=created_at,
        )

    @property
    def fact_count(self) -> int:
        """Return total count of disputed and undisputed facts."""
        return len(self.disputed_facts) + len(self.undisputed_facts)

    @property
    def has_sufficient_evidence(self) -> bool:
        """Check if evidence appears sufficient for the claims."""
        # Heuristic: at least one evidence item per disputed fact
        return len(self.evidence_available) >= len(self.disputed_facts)
