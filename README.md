# 🧬 GeneXA — Gene Expression Search Assistant Chatbot

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35-red?logo=streamlit)](https://streamlit.io)
[![MySQL](https://img.shields.io/badge/MySQL-8.0-orange?logo=mysql)](https://mysql.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-green)](LICENSE)

> A production-grade biotech SaaS platform for natural-language gene expression analysis.  
> Ask questions in plain English — get database-backed expression data, visualizations, and AI insights instantly.

---

## 🚀 Demo Queries

```
"What's the expression of TP53 in lung under infected condition?"
"Show top 10 upregulated genes in breast cancer"
"Compare BRCA1 and BRCA2 across all tissues"
"Heatmap of MYC, EGFR, KRAS under cancer vs normal"
```

---

## 🏗 Architecture

```
genexa/
├── app/
│   ├── main.py              # Streamlit UI — chat, explore, compare, heatmap, export
│   ├── nlp/
│   │   └── parser.py        # Multi-layer NLP: spaCy NER + gazetteer + heuristics
│   ├── db/
│   │   ├── connection.py    # SQLAlchemy pooled connection manager
│   │   └── queries.py       # Parameterized query engine (SQL injection-safe)
│   ├── components/
│   │   ├── charts.py        # Plotly chart components
│   │   └── cards.py         # Gene summary cards
│   └── utils/
│       ├── logger.py        # Structured JSON logger
│       └── export.py        # CSV / Excel export helpers
├── config/
│   ├── settings.py          # Environment-based config
│   └── schema.sql           # MySQL schema with production indexes
├── tests/
│   └── test_parser.py       # NLP parser unit tests
├── requirements.txt
└── README.md
```

---

## ⚡ Quick Start

```bash
# 1. Clone & install
git clone https://github.com/yourusername/genexa
cd genexa
pip install -r requirements.txt
python -m spacy download en_core_web_sm

# 2. Configure database (optional — demo mode works without DB)
cp .env.example .env
# Edit .env with your MySQL credentials

# 3. Load schema
mysql -u root -p < config/schema.sql

# 4. Launch
streamlit run app/main.py
```

---

## 🧠 NLP Pipeline

```
User query
    │
    ▼
Layer 1: spaCy NER          ← identifies GENE, PROTEIN entities
    │
    ▼
Layer 2: Gazetteer matching  ← 50+ known genes, tissues, conditions
    │
    ▼
Layer 3: Heuristic fallback  ← uppercase 2-6 char token patterns
    │
    ▼
Structured ParsedQuery dict → SQL query engine
```

---

## 🗄 Database Design (MySQL)

| Feature | Implementation |
|---|---|
| Injection-safe queries | SQLAlchemy parameterized `text()` |
| Connection pooling | QueuePool, size=5, max_overflow=10 |
| Auto-reconnect | `pool_pre_ping=True` |
| Query speed | Composite index: `(gene_name, tissue_type, condition)` |
| TOP-N queries | Index on `expression_level` |

---

## 📊 Features

| Feature | Status |
|---|---|
| Natural language query parsing | ✅ |
| Gene expression lookup | ✅ |
| Comparative analysis (multi-gene) | ✅ |
| Expression heatmaps | ✅ |
| CSV / Excel export | ✅ |
| Search history | ✅ |
| Favorite queries | ✅ |
| Dark-mode UI | ✅ |
| DB connection pooling | ✅ |
| Structured logging | ✅ |
| Demo mode (no DB needed) | ✅ |
| spaCy NER integration | ✅ |
| NCBI / UniProt API | 🔄 In progress |
| Auth (OAuth2) | 🔄 Planned |
| Docker / deployment | 🔄 Planned |

---

## 🏢 Industry Alignment

| Company | Expectation | How GeneXA addresses it |
|---|---|---|
| **Google / DeepMind** | Scalable NLP, clean architecture, testable code | Layered NLP parser, SQLAlchemy ORM, modular structure |
| **Microsoft / Azure** | Cloud-deployable, REST-ready, CI/CD-friendly | Env-based config, requirements pinned, schema versioned |
| **Illumina / BGI** | Bioinformatics domain correctness, HGNC symbols, GEO integration | KNOWN_GENES gazetteer, GEO dataset fields in schema, NCBI API hooks |
| **Broad Institute** | Reproducible, open, publication-worthy | MIT license, schema SQL, demo data from real GSE accessions |

---

## 🧪 Tests

```bash
pytest tests/ -v --cov=app
```

---

## 📄 License

MIT — free to use, modify, and deploy.
