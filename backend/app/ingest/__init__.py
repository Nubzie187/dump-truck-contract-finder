"""Ingestion modules for contract data."""
from .kytc import ingest_kytc
from .indot import ingest_indot

__all__ = ["ingest_kytc", "ingest_indot"]

