"""
Unit tests for NLPParser.
Run: pytest tests/test_parser.py -v
"""

import sys
sys.path.insert(0, "../app")

import pytest
from nlp.parser import NLPParser


@pytest.fixture
def parser():
    return NLPParser()


class TestGeneExtraction:
    def test_known_gene_uppercase(self, parser):
        r = parser.parse("What is the expression of TP53 in lung?")
        assert r["gene"] == "TP53"

    def test_known_gene_lowercase_query(self, parser):
        r = parser.parse("show me tp53 expression in liver cancer")
        assert r["gene"] == "TP53"

    def test_multi_gene(self, parser):
        r = parser.parse("Compare BRCA1 and BRCA2 in breast tissue")
        assert "BRCA1" in r["genes"]
        assert "BRCA2" in r["genes"]

    def test_no_gene(self, parser):
        r = parser.parse("show all genes in lung")
        # no crash, gene may be None
        assert isinstance(r, dict)


class TestTissueExtraction:
    def test_lung(self, parser):
        r = parser.parse("TP53 expression in lung")
        assert r["tissue"] == "Lung"

    def test_brain(self, parser):
        r = parser.parse("What's the expression of MYC in brain?")
        assert r["tissue"] == "Brain"

    def test_no_tissue(self, parser):
        r = parser.parse("TP53 expression under infection")
        assert r["tissue"] is None


class TestConditionExtraction:
    def test_infected(self, parser):
        r = parser.parse("TP53 in lung under infected condition")
        assert r["condition"] == "Infected"

    def test_cancer(self, parser):
        r = parser.parse("BRCA1 in breast cancer")
        assert r["condition"] == "Cancer"

    def test_tumor_maps_to_cancer(self, parser):
        r = parser.parse("EGFR in tumor tissue")
        assert r["condition"] == "Cancer"

    def test_normal(self, parser):
        r = parser.parse("show TP53 under normal condition")
        assert r["condition"] == "Normal"


class TestIntentDetection:
    def test_single_lookup(self, parser):
        r = parser.parse("What is the expression of TP53 in lung?")
        assert r["intent"] == "single_lookup"

    def test_top_n(self, parser):
        r = parser.parse("Show top 10 genes in lung cancer")
        assert r["intent"] == "top_n"
        assert r["top_n"] == 10

    def test_compare(self, parser):
        r = parser.parse("Compare BRCA1 vs BRCA2")
        assert r["intent"] == "compare"

    def test_upregulated(self, parser):
        r = parser.parse("Show upregulated genes in liver under infection")
        assert r["regulation"] == "up"
