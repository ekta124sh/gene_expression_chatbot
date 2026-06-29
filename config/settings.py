"""
GeneXA Configuration
--------------------
All settings come from environment variables.

"""

import os
from dataclasses import dataclass


@dataclass
class Config:
    # Database
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", 3306))
    DB_USER: str = os.getenv("DB_USER", "root")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "12345")
    DB_NAME: str = os.getenv("DB_NAME", "gene_expression_db")

    # App
    APP_ENV: str = os.getenv("APP_ENV", "development")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    DEMO_MODE: bool = os.getenv("DEMO_MODE", "true").lower() == "true"

    # External APIs (optional)
    NCBI_API_KEY: str = os.getenv("NCBI_API_KEY", "")
    UNIPROT_BASE_URL: str = "https://rest.uniprot.org/uniprotkb"
    GEO_BASE_URL: str = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


config = Config()
