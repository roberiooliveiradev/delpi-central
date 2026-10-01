"""Identidade canônica do operador resolvida pelo diretório do Portal RH (C2).

external_id é o epi_collaborator.id do Portal RH — nunca a matrícula.
registration é texto puro: "001" != "1" e jamais vira inteiro.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class OperatorIdentity:
    external_id: int
    registration: str
    full_name: str
    branch_code: str
    active: bool
