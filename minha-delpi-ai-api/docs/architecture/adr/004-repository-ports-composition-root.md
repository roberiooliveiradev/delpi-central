# ADR 004 — Ports e composition root

**Status:** Aceito (jun/2026)

## Contexto

Rotas HTTP e use cases instanciavam `Postgres*Repository` diretamente, acoplando interfaces e application à infraestrutura.

## Decisão

1. Contratos em `app/domain/ports/` (`ExternalActionRepositoryPort`, `ChatSkillRepositoryPort`, `ChatQualityReportRepositoryPort`, …).
2. Implementações em `app/infrastructure/persistence/`.
3. Factories em `app/composition/repository_composer.py` com aliases sem prefixo `postgres` (`make_audit_repository`, `make_chat_skill_repository`, …).
4. Handlers HTTP chamam `make_*_use_case()` — nunca `Postgres*`.

## Consequências

- `rg 'Postgres.*Repository|make_postgres_' app/interfaces/` → 0.
- Use cases admin tipados com ports; default lazy via composer quando script CLI instancia sem DI.
- Novos repositórios exigem port + factory antes de uso em rotas.
