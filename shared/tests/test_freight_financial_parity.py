"""Impedir que Suprimentos use regras/metas diferentes do Portal Financeiro.

A fonte em financial-api permanece intacta (sem efeito no portal homologado).
Este teste falha caso uma das cópias mude sem atualizar a outra.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_allocations_use_exact_same_source_as_financial_api():
    financial = ROOT / "financial-api/financial_app/domain/services/freight_allocation_service.py"
    shared = ROOT / "shared/delpi_freight/freight_allocation_service.py"
    assert financial.read_bytes() == shared.read_bytes(), (
        "Regra financeira de rateio mudou: atualizar e revalidar paridade de Suprimentos."
    )


def test_branch_limits_and_reasons_match_financial_configuration():
    financial = ROOT / "financial-api/financial_app/content/freight.json"
    shared = ROOT / "shared/delpi_freight/freight.json"
    assert financial.read_bytes() == shared.read_bytes(), (
        "Meta ou regra fiscal do Financeiro mudou: atualizar o espelho de Suprimentos."
    )
