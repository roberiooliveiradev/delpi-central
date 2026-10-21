"""Supplier cadastral enrichment domain — pure comparison, no I/O.

Framework-free domain package for SUPPLIES-ENRICHMENT-01 S1. It compares a
canonical SA2 supplier snapshot (read via api-delpi) against an external
company-registry snapshot and classifies each mapped field. It never talks
HTTP, SQL, Flask or providers, and never writes to Protheus.
"""

from app.domain.supplier_enrichment.comparison import (
    compare_supplier_snapshots,
)
from app.domain.supplier_enrichment.field_mapping import (
    CNPJ_SA2_MAPPING_V1,
    FieldMappingPolicy,
    FieldSpec,
)
from app.domain.supplier_enrichment.models import (
    CanonicalSupplierSnapshot,
    ComparisonState,
    EligibilityState,
    ExternalRegistrySnapshot,
    FieldDecisionState,
    SupplierEnrichmentComparison,
    SupplierEnrichmentReview,
    SupplierFieldProposal,
    SupplierRef,
)

__all__ = [
    "CNPJ_SA2_MAPPING_V1",
    "CanonicalSupplierSnapshot",
    "ComparisonState",
    "EligibilityState",
    "ExternalRegistrySnapshot",
    "FieldDecisionState",
    "FieldMappingPolicy",
    "FieldSpec",
    "SupplierEnrichmentComparison",
    "SupplierEnrichmentReview",
    "SupplierFieldProposal",
    "SupplierRef",
    "compare_supplier_snapshots",
]
