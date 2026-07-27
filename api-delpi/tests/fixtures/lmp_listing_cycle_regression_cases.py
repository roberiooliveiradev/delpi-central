"""Casos de regressão — ciclos LMP maio/Q2 2026 (investigação Protheus)."""
from __future__ import annotations

from app.domain.services.lmp_listing_cycle_semantics_service import LmpHomologCycleRow

MIN_RESIDENCE = 30

# Bruto: múltiplas revisões Protheus no mesmo homolog_date (dedupe → 1 ciclo)
MAY_2026_RAW_CYCLES: list[LmpHomologCycleRow] = [
    LmpHomologCycleRow("02", "000087", "08", "08", "20260504", 109, "LMP"),
    LmpHomologCycleRow("02", "000102", "04", "03", "20260518", 0, "OUTRO"),
    LmpHomologCycleRow("02", "000102", "03", "03", "20260518", 1644, "LMP"),
    LmpHomologCycleRow("01", "003561", "05", "05", "20260505", 0, "OUTRO"),
    LmpHomologCycleRow("01", "002871", "06", "06", "20260527", 1, "OUTRO"),
    LmpHomologCycleRow("02", "000061", "12", "12", "20260527", 1055, "LMP"),
    LmpHomologCycleRow("02", "000090", "04", "04", "20260506", 3167, "LMP"),
    LmpHomologCycleRow("02", "000090", "07", "07", "20260515", 5496, "LMP"),
]

MAY_2026_EXPECTED_AFTER_DEDUPE: dict[str, tuple[str, int, str]] = {
    "000087": ("08", 109, "LMP"),
    "000102": ("03", 1644, "LMP"),
    "003561": ("05", 0, "OUTRO"),
    "002871": ("06", 1, "OUTRO"),
    "000061": ("12", 1055, "LMP"),
    "000090": ("04", 3167, "LMP"),  # primeiro ciclo; segundo ciclo separado abaixo
}

Q2_061_CYCLES: list[LmpHomologCycleRow] = [
    LmpHomologCycleRow("02", "000061", "04", "04", "20260417", 0, "OUTRO"),
    LmpHomologCycleRow("02", "000061", "08", "08", "20260421", 2801, "LMP"),
    LmpHomologCycleRow("02", "000061", "12", "12", "20260527", 1055, "LMP"),
]

# 087: homolog maio — não deve entrar em abril com política homolog_in_period
APR_2026_087_FIRST_ENG_ONLY = {
    "branch": "02",
    "sale_number": "000087",
    "first_eng": "20260421",
    "homolog_date": "20260504",
    "homolog_in_april": False,
    "homolog_in_may": True,
}

KIND_REGRESSION = [
    {
        "id": "561_zero_min_finalized",
        "anchor_kind": "LMP",
        "has_sample": True,
        "sample_minutes": 0,
        "total_minutes": 0,
        "has_lmp_finalized": True,
        "strict": True,
        "has_engineering_stage": True,
        "expected_kind": "OUTRO",
        "passes_residence": True,
    },
    {
        "id": "561_outro_sem_engenharia",
        "anchor_kind": "LMP",
        "has_sample": True,
        "sample_minutes": 0,
        "total_minutes": 0,
        "has_lmp_finalized": True,
        "strict": True,
        "has_engineering_stage": False,
        "expected_kind": "OUTRO",
        "passes_residence": False,
    },
    {
        "id": "2871_one_min_finalized",
        "anchor_kind": "LMP",
        "has_sample": True,
        "sample_minutes": 0,
        "total_minutes": 1,
        "has_lmp_finalized": True,
        "strict": True,
        "has_engineering_stage": True,
        "expected_kind": "OUTRO",
        "passes_residence": True,
    },
    {
        "id": "087_valid_lmp",
        "anchor_kind": "LMP",
        "has_sample": True,
        "sample_minutes": 0,
        "total_minutes": 109,
        "has_lmp_finalized": True,
        "strict": True,
        "has_engineering_stage": True,
        "expected_kind": "LMP",
        "passes_residence": True,
    },
    {
        "id": "102_cross_rev_measurement",
        "anchor_kind": "LMP",
        "has_sample": False,
        "sample_minutes": 0,
        "total_minutes": 1644,
        "has_lmp_finalized": True,
        "strict": True,
        "has_engineering_stage": True,
        "expected_kind": "LMP",
        "passes_residence": True,
    },
    {
        "id": "amostra_pontual_com_engenharia",
        "anchor_kind": "AMOSTRA",
        "has_sample": True,
        "sample_minutes": 0,
        "total_minutes": 0,
        "has_lmp_finalized": False,
        "strict": False,
        "has_engineering_stage": True,
        "expected_kind": "AMOSTRA",
        "passes_residence": True,
    },
    {
        "id": "amostra_sem_estagio_engenharia",
        "anchor_kind": "AMOSTRA",
        "has_sample": True,
        "sample_minutes": 0,
        "total_minutes": 0,
        "has_lmp_finalized": False,
        "strict": False,
        "has_engineering_stage": False,
        "expected_kind": "AMOSTRA",
        "passes_residence": False,
    },
]
