"""Bounded context LMP Nonconformity — domínio NC (E-NC-*).

Owner funcional: Engineering API (T1–T6, Plano 48). O adapter de
persistência responde pelo schema ``engineering.lmp_*`` (postgres-plugins)
apenas com principal dedicado; a storage compartilhada permanece sob a
api-delpi até aprovação formal do ADR-NC-OWNERSHIP (doc 47 §7).
"""
