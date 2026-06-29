"""
NLP Parser Module
-----------------
Replaces fragile regex with a layered NLP approach:
  Layer 1 – spaCy NER (if available)
  Layer 2 – Rule-based gazetteer matching (always runs)
  Layer 3 – Fallback heuristics

Returns a structured dict ready for the query engine.
"""

import re
import logging
from typing import Optional
from dataclasses import dataclass, field, asdict

logger = logging.getLogger(__name__)

# ─── Known entity gazetteers ─────────────────────────────────────────────────
KNOWN_GENES = {
    "TP53", "BRCA1", "BRCA2", "EGFR", "MYC", "KRAS", "PTEN", "RB1",
    "APC", "VHL", "MLH1", "MSH2", "CDKN2A", "HER2", "ERBB2", "PIK3CA",
    "ALK", "RET", "MET", "BRAF", "NRAS", "IDH1", "IDH2", "DNMT3A",
    "FLT3", "NPM1", "RUNX1", "WT1", "JAK2", "STAT3", "STAT5",
    "BCL2", "BCL6", "MYD88", "NOTCH1", "FBXW7", "SF3B1", "ATM",
    "CHEK2", "PALB2", "RAD51", "FANCA", "FANCD2", "BRIP1",
    "IL6", "TNF", "VEGFA", "VEGFB", "HIF1A", "MAPK1", "MAPK3",
    "AKT1", "AKT2", "MTOR", "RPS6", "EIF4E", "MDM2", "MDM4",
}

KNOWN_TISSUES = {
    "lung", "liver", "brain", "heart", "kidney", "blood", "breast",
    "colon", "pancreas", "ovary", "prostate", "thyroid", "skin",
    "muscle", "bone", "stomach", "spleen", "intestine", "lymph node",
    "adrenal", "cervix", "uterus", "testis", "bladder", "esophagus",
}

KNOWN_CONDITIONS = {
    "normal", "infected", "infection", "cancer", "tumor", "tumour",
    "hypoxia", "stress", "treated", "untreated", "disease", "healthy",
    "inflamed", "inflammation", "oxidative", "apoptosis", "necrosis",
    "metastatic", "metastasis", "control", "wild-type", "knockout",
}

CONDITION_MAP = {
    "infection": "infected",
    "tumor": "cancer",
    "tumour": "cancer",
    "disease": "cancer",
    "inflamed": "inflammation",
    "healthy": "normal",
    "control": "normal",
    "wild-type": "normal",
}

INTENT_PATTERNS = {
    "single_lookup": [r"\bwhat\b.*\bexpression\b", r"\bshow\b.*\bexpression\b", r"\bget\b.*\bexpression\b"],
    "top_n": [r"\btop\s*(\d+)\b", r"\bhighest\b", r"\bmost\s+expressed\b"],
    "compare": [r"\bcompar\b", r"\bvs\b", r"\bversus\b", r"\bbetween\b"],
    "upregulated": [r"\bupregulat\b", r"\boverexpress\b"],
    "downregulated": [r"\bdownregulat\b", r"\bunderexpress\b"],
    "list_all": [r"\ball\s+genes\b", r"\blist\b.*\bgenes\b"],
}


@dataclass
class ParsedQuery:
    raw: str
    intent: str = "single_lookup"
    gene: Optional[str] = None
    genes: list = field(default_factory=list)   # for multi-gene compare
    tissue: Optional[str] = None
    condition: Optional[str] = None
    top_n: int = 50
    regulation: Optional[str] = None            # "up" | "down" | None
    confidence: float = 1.0

    def to_dict(self) -> dict:
        return asdict(self)


class NLPParser:
    """
    Multi-layer NLP parser for gene expression queries.

    Usage:
        parser = NLPParser()
        result = parser.parse("What's the expression of TP53 in lung under infected condition?")
        # → ParsedQuery(gene='TP53', tissue='lung', condition='infected', ...)
    """

    def __init__(self):
        self._nlp = None
        self._try_load_spacy()

    def _try_load_spacy(self):
        try:
            import spacy
            self._nlp = spacy.load("en_core_web_sm")
            logger.info("spaCy model loaded — NER active")
        except Exception:
            logger.warning("spaCy unavailable — using rule-based parser only")

    # ── Public API ────────────────────────────────────────────────────────────
    def parse(self, raw_query: str) -> dict:
        """Parse a natural-language query and return a plain dict."""
        pq = ParsedQuery(raw=raw_query)
        text = raw_query.strip()
        lower = text.lower()

        pq.intent = self._detect_intent(lower)
        pq.top_n = self._extract_top_n(lower)
        pq.regulation = self._detect_regulation(lower)

        # Gene extraction: spaCy first, then gazetteer
        pq.gene, pq.genes = self._extract_genes(text)
        pq.tissue = self._extract_tissue(lower)
        pq.condition = self._extract_condition(lower)

        # Confidence scoring
        extracted = sum([
            pq.gene is not None,
            pq.tissue is not None,
            pq.condition is not None,
        ])
        pq.confidence = round(extracted / 3, 2)

        logger.debug("Parsed query: %s", pq.to_dict())
        return pq.to_dict()

    # ── Private helpers ───────────────────────────────────────────────────────
    def _detect_intent(self, lower: str) -> str:
        for intent, patterns in INTENT_PATTERNS.items():
            if any(re.search(p, lower) for p in patterns):
                return intent
        return "single_lookup"

    def _extract_top_n(self, lower: str) -> int:
        m = re.search(r"\btop\s*(\d+)\b", lower)
        return int(m.group(1)) if m else 50

    def _detect_regulation(self, lower: str) -> Optional[str]:
        if re.search(r"\bupregulat|overexpress\b", lower):
            return "up"
        if re.search(r"\bdownregulat|underexpress\b", lower):
            return "down"
        return None

    def _extract_genes(self, text: str):
        """Returns (primary_gene, list_of_genes)."""
        found = []

        # spaCy NER pass
        if self._nlp:
            doc = self._nlp(text)
            for ent in doc.ents:
                if ent.label_ in {"GENE", "PROTEIN", "ORG"}:
                    candidate = ent.text.upper()
                    if candidate in KNOWN_GENES:
                        found.append(candidate)

        # Gazetteer pass (always)
        upper_text = text.upper()
        for gene in KNOWN_GENES:
            pattern = r'\b' + re.escape(gene) + r'\b'
            if re.search(pattern, upper_text) and gene not in found:
                found.append(gene)

        # Heuristic: token that looks like a gene symbol (2-6 uppercase letters)
        if not found:
            tokens = re.findall(r'\b[A-Z][A-Z0-9]{1,5}\b', text)
            for tok in tokens:
                if tok not in {"IN", "OF", "THE", "AND", "OR", "FOR", "ON",
                               "AT", "BY", "IS", "TO", "A", "AN", "SHOW",
                               "WHAT", "GET", "MY", "ALL", "TOP", "VS"}:
                    found.append(tok)

        primary = found[0] if found else None
        return primary, found

    def _extract_tissue(self, lower: str) -> Optional[str]:
        for tissue in KNOWN_TISSUES:
            if re.search(r'\b' + re.escape(tissue) + r'\b', lower):
                return tissue.capitalize()
        return None

    def _extract_condition(self, lower: str) -> Optional[str]:
        for cond in KNOWN_CONDITIONS:
            if re.search(r'\b' + re.escape(cond) + r'\b', lower):
                mapped = CONDITION_MAP.get(cond, cond)
                return mapped.capitalize()
        return None
