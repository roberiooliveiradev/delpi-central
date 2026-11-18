"""Política de ativação do recebimento físico para OTD (#852).

Contrato de ativação puro, compartilhado por cache e consultas. Default OFF.
"""
from __future__ import annotations

import os


def physical_receipts_enabled() -> bool:
    return os.getenv("OTD_PHYSICAL_RECEIPTS_ENABLED", "false").strip().lower() in {
        "1", "true", "yes", "on",
    }
