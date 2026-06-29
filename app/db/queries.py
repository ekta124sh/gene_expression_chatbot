"""
Gene Query Engine
-----------------
All SQL is parameterized (no f-string injection risk).
Results are cached with st.cache_data where possible.
"""

import logging
from typing import Optional, List

import pandas as pd

logger = logging.getLogger(__name__)

# Try sqlalchemy text helper
try:
    from sqlalchemy import text
    _HAS_SA = True
except ImportError:
    _HAS_SA = False

# Fallback to demo data when no DB is connected
_DEMO_DATA = pd.DataFrame([
    {"gene_name": "TP53", "tissue_type": "Lung", "condition": "Infected",  "expression_level": 8.32, "sample_count": 42},
    {"gene_name": "TP53", "tissue_type": "Lung", "condition": "Normal",    "expression_level": 3.11, "sample_count": 38},
    {"gene_name": "TP53", "tissue_type": "Liver","condition": "Cancer",    "expression_level": 9.74, "sample_count": 55},
    {"gene_name": "BRCA1","tissue_type": "Breast","condition": "Cancer",   "expression_level": 7.88, "sample_count": 61},
    {"gene_name": "BRCA1","tissue_type": "Breast","condition": "Normal",   "expression_level": 4.12, "sample_count": 44},
    {"gene_name": "BRCA2","tissue_type": "Breast","condition": "Cancer",   "expression_level": 6.55, "sample_count": 50},
    {"gene_name": "EGFR", "tissue_type": "Lung", "condition": "Cancer",    "expression_level": 10.1, "sample_count": 70},
    {"gene_name": "EGFR", "tissue_type": "Brain","condition": "Hypoxia",   "expression_level": 6.44, "sample_count": 30},
    {"gene_name": "MYC",  "tissue_type": "Blood","condition": "Cancer",    "expression_level": 11.2, "sample_count": 85},
    {"gene_name": "KRAS", "tissue_type": "Colon","condition": "Cancer",    "expression_level": 9.01, "sample_count": 66},
    {"gene_name": "KRAS", "tissue_type": "Colon","condition": "Normal",    "expression_level": 2.88, "sample_count": 40},
    {"gene_name": "PTEN", "tissue_type": "Brain","condition": "Normal",    "expression_level": 5.50, "sample_count": 28},
    {"gene_name": "PTEN", "tissue_type": "Brain","condition": "Stress",    "expression_level": 3.22, "sample_count": 22},
    {"gene_name": "HIF1A","tissue_type": "Heart","condition": "Hypoxia",   "expression_level": 12.4, "sample_count": 34},
    {"gene_name": "IL6",  "tissue_type": "Blood","condition": "Infected",  "expression_level": 14.5, "sample_count": 90},
])


class GeneQueryEngine:
    """
    Executes structured gene expression queries against MySQL.
    Falls back to demo data when database is unavailable.
    """

    def __init__(self):
        self._use_demo = False
        try:
            from db.connection import get_db_connection
            self._get_conn = get_db_connection
        except Exception:
            self._use_demo = True

    # ── Public methods ────────────────────────────────────────────────────────

    def execute(self, parsed: dict) -> pd.DataFrame:
        """Route a parsed query dict to the right SQL handler."""
        intent = parsed.get("intent", "single_lookup")

        if intent == "compare":
            return self.compare_genes(
                genes=parsed.get("genes", []),
                tissue=parsed.get("tissue"),
                condition=parsed.get("condition"),
            )
        if intent == "top_n":
            return self._top_n_query(parsed)
        return self._single_lookup(parsed)

    def explore(
        self,
        gene: Optional[str] = None,
        tissue: Optional[str] = None,
        condition: Optional[str] = None,
        limit: int = 100,
    ) -> pd.DataFrame:
        """Free-form explorer query with optional filters."""
        if self._use_demo:
            return self._filter_demo(gene, tissue, condition).head(limit)

        clauses, params = [], {}
        if gene:
            clauses.append("gene_name = :gene")
            params["gene"] = gene.upper()
        if tissue:
            clauses.append("tissue_type = :tissue")
            params["tissue"] = tissue
        if condition:
            clauses.append("condition = :condition")
            params["condition"] = condition

        where = "WHERE " + " AND ".join(clauses) if clauses else ""
        sql = f"""
            SELECT gene_name, tissue_type, condition,
                   expression_level, sample_count, updated_at
            FROM gene_expression
            {where}
            ORDER BY expression_level DESC
            LIMIT :limit
        """
        params["limit"] = limit
        return self._run(sql, params)

    def compare_genes(
        self,
        genes: List[str],
        tissue: Optional[str] = None,
        condition: Optional[str] = None,
    ) -> pd.DataFrame:
        """Return expression data for multiple genes side-by-side."""
        if not genes:
            return pd.DataFrame()

        if self._use_demo:
            df = self._filter_demo(tissue=tissue, condition=condition)
            return df[df["gene_name"].isin([g.upper() for g in genes])]

        placeholders = ", ".join([f":g{i}" for i in range(len(genes))])
        params = {f"g{i}": g.upper() for i, g in enumerate(genes)}
        clauses = [f"gene_name IN ({placeholders})"]
        if tissue:
            clauses.append("tissue_type = :tissue")
            params["tissue"] = tissue
        if condition:
            clauses.append("condition = :condition")
            params["condition"] = condition

        sql = f"""
            SELECT gene_name, tissue_type, condition,
                   AVG(expression_level) AS expression_level,
                   COUNT(*) AS sample_count
            FROM gene_expression
            WHERE {" AND ".join(clauses)}
            GROUP BY gene_name, tissue_type, condition
            ORDER BY gene_name, tissue_type
        """
        return self._run(sql, params)

    def heatmap_data(
        self,
        genes: List[str],
        conditions: List[str],
    ) -> pd.DataFrame:
        """Pull pivot-ready data for the heatmap tab."""
        if self._use_demo:
            df = _DEMO_DATA.copy()
            df = df[df["gene_name"].isin([g.upper() for g in genes])]
            df = df[df["condition"].isin(conditions)]
            return df

        g_ph = ", ".join([f":g{i}" for i in range(len(genes))])
        c_ph = ", ".join([f":c{i}" for i in range(len(conditions))])
        params = {f"g{i}": g.upper() for i, g in enumerate(genes)}
        params.update({f"c{i}": c for i, c in enumerate(conditions)})

        sql = f"""
            SELECT gene_name, condition,
                   AVG(expression_level) AS expression_level
            FROM gene_expression
            WHERE gene_name IN ({g_ph}) AND condition IN ({c_ph})
            GROUP BY gene_name, condition
        """
        return self._run(sql, params)

    # ── Private helpers ───────────────────────────────────────────────────────

    def _single_lookup(self, parsed: dict) -> pd.DataFrame:
        gene = parsed.get("gene")
        tissue = parsed.get("tissue")
        condition = parsed.get("condition")

        if self._use_demo:
            return self._filter_demo(gene, tissue, condition)

        clauses, params = [], {}
        if gene:
            clauses.append("gene_name = :gene")
            params["gene"] = gene.upper()
        if tissue:
            clauses.append("tissue_type = :tissue")
            params["tissue"] = tissue
        if condition:
            clauses.append("condition = :condition")
            params["condition"] = condition

        where = "WHERE " + " AND ".join(clauses) if clauses else ""
        sql = f"""
            SELECT gene_name, tissue_type, condition,
                   expression_level, sample_count
            FROM gene_expression
            {where}
            ORDER BY expression_level DESC
            LIMIT 200
        """
        return self._run(sql, params)

    def _top_n_query(self, parsed: dict) -> pd.DataFrame:
        n = parsed.get("top_n", 10)
        tissue = parsed.get("tissue")
        condition = parsed.get("condition")

        if self._use_demo:
            df = self._filter_demo(tissue=tissue, condition=condition)
            return df.nlargest(n, "expression_level")

        clauses, params = [], {"n": n}
        if tissue:
            clauses.append("tissue_type = :tissue")
            params["tissue"] = tissue
        if condition:
            clauses.append("condition = :condition")
            params["condition"] = condition

        where = "WHERE " + " AND ".join(clauses) if clauses else ""
        sql = f"""
            SELECT gene_name, tissue_type, condition,
                   expression_level, sample_count
            FROM gene_expression
            {where}
            ORDER BY expression_level DESC
            LIMIT :n
        """
        return self._run(sql, params)

    def _run(self, sql: str, params: dict) -> pd.DataFrame:
        """Execute parameterized SQL and return a DataFrame."""
        try:
            from db.connection import get_db_connection
            with get_db_connection() as conn:
                return pd.read_sql(text(sql), conn, params=params)
        except Exception as e:
            logger.error("Query execution error: %s | SQL: %s", e, sql)
            raise

    def _filter_demo(
        self,
        gene: Optional[str] = None,
        tissue: Optional[str] = None,
        condition: Optional[str] = None,
    ) -> pd.DataFrame:
        df = _DEMO_DATA.copy()
        if gene:
            df = df[df["gene_name"].str.upper() == gene.upper()]
        if tissue:
            df = df[df["tissue_type"].str.lower() == tissue.lower()]
        if condition:
            df = df[df["condition"].str.lower() == condition.lower()]
        return df.reset_index(drop=True)
