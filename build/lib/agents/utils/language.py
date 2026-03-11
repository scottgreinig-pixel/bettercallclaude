"""
Language detection and multilingual support utilities for Swiss legal context.

Provides language detection with confidence scoring, legal terminology
mapping, and user confirmation workflow for CAUTIOUS mode.
"""

import re
from dataclasses import dataclass

from src.agents.models.shared import Language

# =============================================================================
# Language Detection Markers
# =============================================================================

# Common words and patterns that strongly indicate each language
LANGUAGE_MARKERS: dict[Language, dict[str, list[str]]] = {
    Language.DE: {
        "articles": ["der", "die", "das", "dem", "den", "ein", "eine", "einer"],
        "conjunctions": ["und", "oder", "aber", "sondern", "denn", "weil"],
        "prepositions": ["in", "auf", "mit", "bei", "nach", "von", "zu", "aus"],
        "legal_terms": [
            "gemäss",
            "gemass",
            "betreffend",
            "Kläger",
            "Klager",
            "Beklagter",
            "Gericht",
            "Urteil",
            "Entscheid",
            "Vertrag",
            "Haftung",
            "Schadenersatz",
            "Bundesgericht",
        ],
        "legal_refs": ["Art.", "Abs.", "Ziff.", "OR", "ZGB", "StGB", "BGE"],
    },
    Language.FR: {
        "articles": ["le", "la", "les", "un", "une", "des", "du", "au", "aux"],
        "conjunctions": ["et", "ou", "mais", "donc", "car", "parce"],
        "prepositions": ["de", "à", "dans", "sur", "avec", "pour", "par", "en"],
        "legal_terms": [
            "selon",
            "conformément",
            "demandeur",
            "défendeur",
            "defendeur",
            "tribunal",
            "arrêt",
            "arret",
            "jugement",
            "contrat",
            "responsabilité",
            "responsabilite",
            "dommages-intérêts",
        ],
        "legal_refs": ["art.", "al.", "ch.", "CO", "CC", "CP", "ATF"],
    },
    Language.IT: {
        "articles": ["il", "lo", "la", "i", "gli", "le", "un", "uno", "una"],
        "conjunctions": ["e", "o", "ma", "però", "pero", "perché", "perche"],
        "prepositions": ["di", "a", "da", "in", "con", "su", "per", "tra", "fra"],
        "legal_terms": [
            "secondo",
            "conformemente",
            "attore",
            "convenuto",
            "tribunale",
            "sentenza",
            "decisione",
            "contratto",
            "responsabilità",
            "responsabilita",
            "risarcimento",
        ],
        "legal_refs": ["art.", "cpv.", "n.", "CO", "CC", "CP", "DTF"],
    },
    Language.EN: {
        "articles": ["the", "a", "an"],
        "conjunctions": ["and", "or", "but", "because", "however", "therefore"],
        "prepositions": ["in", "on", "at", "with", "for", "to", "from", "by"],
        "legal_terms": [
            "pursuant",
            "plaintiff",
            "defendant",
            "court",
            "judgment",
            "ruling",
            "contract",
            "liability",
            "damages",
            "breach",
        ],
        "legal_refs": ["Art.", "para.", "sec.", "BGE", "ATF", "DTF"],
    },
}

# Weights for different marker types
MARKER_WEIGHTS = {
    "articles": 1.0,
    "conjunctions": 1.5,
    "prepositions": 1.0,
    "legal_terms": 3.0,  # Legal terms are strong indicators
    "legal_refs": 4.0,  # Legal references are very strong indicators
}


# =============================================================================
# Language Detection Results
# =============================================================================


@dataclass
class LanguageDetectionResult:
    """Result of language detection."""

    detected_language: Language
    confidence: float
    scores: dict[Language, float]
    markers_found: dict[Language, list[str]]
    needs_confirmation: bool

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "detected_language": self.detected_language.value,
            "confidence": self.confidence,
            "scores": {lang.value: score for lang, score in self.scores.items()},
            "markers_found": {lang.value: markers for lang, markers in self.markers_found.items()},
            "needs_confirmation": self.needs_confirmation,
        }


# =============================================================================
# Detection Functions
# =============================================================================


def detect_language(text: str) -> Language:
    """
    Detect language from input text.

    Uses simple heuristics optimized for Swiss legal context:
    - German markers: der, die, das, und, gemäss, Art.
    - French markers: le, la, les, et, selon, art.
    - Italian markers: il, la, le, e, secondo, art.
    - English markers: the, and, pursuant, Art.

    Args:
        text: Input text to analyze

    Returns:
        Detected Language enum value
    """
    result = detect_language_confidence(text)
    return result.detected_language


def detect_language_confidence(
    text: str,
    confirmation_threshold: float = 0.7,
) -> LanguageDetectionResult:
    """
    Detect language with confidence scoring.

    Args:
        text: Input text to analyze
        confirmation_threshold: Confidence below this triggers confirmation need

    Returns:
        LanguageDetectionResult with detailed scores
    """
    if not text or not text.strip():
        return LanguageDetectionResult(
            detected_language=Language.DE,  # Default to German
            confidence=0.0,
            scores=dict.fromkeys(Language, 0.0),
            markers_found={lang: [] for lang in Language},
            needs_confirmation=True,
        )

    # Normalize text for matching
    text_lower = text.lower()
    words = re.findall(r"\b\w+\b", text_lower)
    word_set = set(words)

    # Also check original case for legal references
    original_words = re.findall(r"\b[\w.]+\b", text)

    scores: dict[Language, float] = {}
    markers_found: dict[Language, list[str]] = {}

    for lang, marker_groups in LANGUAGE_MARKERS.items():
        lang_score = 0.0
        found_markers: list[str] = []

        for marker_type, markers in marker_groups.items():
            weight = MARKER_WEIGHTS.get(marker_type, 1.0)

            for marker in markers:
                marker_lower = marker.lower()

                # Check in word set (for most markers)
                if marker_lower in word_set:
                    # Count occurrences
                    count = words.count(marker_lower)
                    lang_score += weight * min(count, 5)  # Cap at 5 occurrences
                    found_markers.append(marker)

                # Check original case for legal refs (Art., BGE, etc.)
                elif marker in original_words:
                    count = original_words.count(marker)
                    lang_score += weight * min(count, 5)
                    found_markers.append(marker)

        scores[lang] = lang_score
        markers_found[lang] = found_markers

    # Normalize scores
    total_score = sum(scores.values())
    if total_score > 0:
        for lang in scores:
            scores[lang] = scores[lang] / total_score

    # Find best match
    best_lang = max(scores, key=lambda x: scores[x])
    confidence = scores[best_lang]

    # Check if confirmation needed
    needs_confirmation = confidence < confirmation_threshold

    # If very low confidence, check for any strong indicators
    if confidence < 0.4:
        # Check for explicit language markers
        if any(ref in text for ref in ["BGE", "Bundesgericht"]):
            best_lang = Language.DE
            confidence = 0.6
        elif any(ref in text for ref in ["ATF", "Tribunal fédéral"]):
            best_lang = Language.FR
            confidence = 0.6
        elif any(ref in text for ref in ["DTF", "Tribunale federale"]):
            best_lang = Language.IT
            confidence = 0.6

    return LanguageDetectionResult(
        detected_language=best_lang,
        confidence=confidence,
        scores=scores,
        markers_found=markers_found,
        needs_confirmation=needs_confirmation,
    )


def confirm_language_with_user(
    detected: LanguageDetectionResult,
) -> tuple[Language, bool]:
    """
    Generate confirmation prompt for CAUTIOUS mode.

    In an actual implementation, this would interact with the user.
    Here it returns the detected language and a flag indicating
    confirmation was requested.

    Args:
        detected: Detection result to confirm

    Returns:
        Tuple of (language, was_confirmed)
    """
    # In practice, this would be handled by the agent's checkpoint system
    return detected.detected_language, False


# =============================================================================
# Legal Terminology
# =============================================================================

LEGAL_TERMINOLOGY: dict[str, dict[Language, str]] = {
    # Parties
    "plaintiff": {
        Language.DE: "Kläger",
        Language.FR: "Demandeur",
        Language.IT: "Attore",
        Language.EN: "Plaintiff",
    },
    "defendant": {
        Language.DE: "Beklagter",
        Language.FR: "Défendeur",
        Language.IT: "Convenuto",
        Language.EN: "Defendant",
    },
    "appellant": {
        Language.DE: "Berufungskläger",
        Language.FR: "Appelant",
        Language.IT: "Appellante",
        Language.EN: "Appellant",
    },
    # Documents
    "statement_of_claim": {
        Language.DE: "Klageschrift",
        Language.FR: "Demande",
        Language.IT: "Petizione",
        Language.EN: "Statement of Claim",
    },
    "answer": {
        Language.DE: "Klageantwort",
        Language.FR: "Réponse",
        Language.IT: "Risposta",
        Language.EN: "Answer",
    },
    "legal_opinion": {
        Language.DE: "Rechtsgutachten",
        Language.FR: "Avis de droit",
        Language.IT: "Parere legale",
        Language.EN: "Legal Opinion",
    },
    # Sections
    "facts": {
        Language.DE: "Sachverhalt",
        Language.FR: "État de fait",
        Language.IT: "Fatti",
        Language.EN: "Statement of Facts",
    },
    "legal_analysis": {
        Language.DE: "Rechtliches",
        Language.FR: "En droit",
        Language.IT: "In diritto",
        Language.EN: "Legal Analysis",
    },
    "conclusion": {
        Language.DE: "Ergebnis",
        Language.FR: "Conclusion",
        Language.IT: "Conclusione",
        Language.EN: "Conclusion",
    },
    # Legal concepts
    "breach_of_contract": {
        Language.DE: "Vertragsverletzung",
        Language.FR: "Violation du contrat",
        Language.IT: "Violazione del contratto",
        Language.EN: "Breach of Contract",
    },
    "damages": {
        Language.DE: "Schadenersatz",
        Language.FR: "Dommages-intérêts",
        Language.IT: "Risarcimento",
        Language.EN: "Damages",
    },
    "liability": {
        Language.DE: "Haftung",
        Language.FR: "Responsabilité",
        Language.IT: "Responsabilità",
        Language.EN: "Liability",
    },
    "good_faith": {
        Language.DE: "Treu und Glauben",
        Language.FR: "Bonne foi",
        Language.IT: "Buona fede",
        Language.EN: "Good Faith",
    },
    # Law references
    "article": {
        Language.DE: "Art.",
        Language.FR: "art.",
        Language.IT: "art.",
        Language.EN: "Art.",
    },
    "paragraph": {
        Language.DE: "Abs.",
        Language.FR: "al.",
        Language.IT: "cpv.",
        Language.EN: "para.",
    },
    "code_of_obligations": {
        Language.DE: "OR",
        Language.FR: "CO",
        Language.IT: "CO",
        Language.EN: "CO",
    },
    "civil_code": {
        Language.DE: "ZGB",
        Language.FR: "CC",
        Language.IT: "CC",
        Language.EN: "CC",
    },
}


def get_legal_terminology(
    term: str,
    language: Language,
    fallback: str | None = None,
) -> str:
    """
    Get legal term in specified language.

    Args:
        term: English term key
        language: Target language
        fallback: Value to return if term not found

    Returns:
        Translated term or fallback
    """
    term_lower = term.lower().replace(" ", "_")

    if term_lower in LEGAL_TERMINOLOGY:
        return LEGAL_TERMINOLOGY[term_lower].get(
            language,
            fallback or term,
        )

    return fallback or term


def translate_legal_phrase(
    phrase: str,
    from_lang: Language,
    to_lang: Language,
) -> str:
    """
    Attempt to translate a legal phrase between languages.

    This is a simple lookup-based translation for known terms.
    For complex phrases, returns the original.

    Args:
        phrase: Phrase to translate
        from_lang: Source language
        to_lang: Target language

    Returns:
        Translated phrase if found, original otherwise
    """
    # Try to find the phrase in terminology
    for _term_key, translations in LEGAL_TERMINOLOGY.items():
        if translations.get(from_lang, "").lower() == phrase.lower():
            return translations.get(to_lang, phrase)

    return phrase


# =============================================================================
# Utility Functions
# =============================================================================


def get_language_code(language: Language) -> str:
    """Get ISO 639-1 language code."""
    return language.value


def get_language_name(language: Language, in_language: Language | None = None) -> str:
    """
    Get language name in specified language.

    Args:
        language: Language to name
        in_language: Language to use for the name (default: same language)

    Returns:
        Language name
    """
    names = {
        Language.DE: {
            Language.DE: "Deutsch",
            Language.FR: "Allemand",
            Language.IT: "Tedesco",
            Language.EN: "German",
        },
        Language.FR: {
            Language.DE: "Französisch",
            Language.FR: "Français",
            Language.IT: "Francese",
            Language.EN: "French",
        },
        Language.IT: {
            Language.DE: "Italienisch",
            Language.FR: "Italien",
            Language.IT: "Italiano",
            Language.EN: "Italian",
        },
        Language.EN: {
            Language.DE: "Englisch",
            Language.FR: "Anglais",
            Language.IT: "Inglese",
            Language.EN: "English",
        },
    }

    target = in_language or language
    return names.get(language, {}).get(target, language.display_name)


def is_swiss_national_language(language: Language) -> bool:
    """Check if language is a Swiss national language."""
    return language in [Language.DE, Language.FR, Language.IT]
