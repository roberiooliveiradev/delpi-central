"""Compatibilidade — preferir app.interface.http.kpi_field_labels."""

from app.interface.http.kpi_field_labels import (
    FINANCIAL_ROL_FIELD_LABELS,
    kpi_fields,
)

ROL_FIELD_LABELS = kpi_fields(FINANCIAL_ROL_FIELD_LABELS)
