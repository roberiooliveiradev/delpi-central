"""Camada de domínio da Engineering API (G3 — owner das regras LMP).

Regras de negócio puras, sem dependência de framework, HTTP, banco ou
clients de integração. Implementadas conforme a spec canônica
`api-delpi/contracts/lmp/lmp_semantics.v1.yaml` — a paridade entre esta
implementação e a spec é verificada por teste dedicado.
"""
