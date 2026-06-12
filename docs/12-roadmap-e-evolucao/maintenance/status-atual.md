# Status atual — Manutenção

**Última atualização:** jun/2026

## O que existe no monorepo

| Peça | Caminho | Status |
|------|---------|--------|
| Docs produto | `docs/12-roadmap-e-evolucao/maintenance/` | ✅ Índice, overview, arquitetura, roadmap, playbook, especificação |
| Docs API | `maintenance-api/docs/` | ✅ README, arquitetura, contratos de integração |
| MFE (stub) | `plugins/maintenance/` | ✅ Scaffold Vite + placeholder (Fase 0) |
| API dedicada (código) | `maintenance-api/` | ✅ Skeleton FastAPI + health + gateway (Fase 0) |
| Rotas TOTVS na api-delpi | `api-delpi` prefixo `/engineering/mini-applicators/*` | ✅ `GET .../ferramentas` + detalhe (Fase 0) |
| Docker Compose / gateway | `infra/docker-compose*.yml` | ✅ Fase 0 |
| Registro Core API | manifesto no portal | ⏳ Após validação local |

## O que já existe fora do monorepo

| Peça | Status |
|------|--------|
| App WinForms `MiniAplicadores` | ✅ Produção legada (Access + TOTVS direto) |
| Regras de negócio documentadas | ✅ Reposição, média de golpes, status preventivo |

## Próximo passo recomendado

1. Fase 0 — esqueleto `maintenance-api` (`main.py`, health, V001 schema) + MFE hello world + compose.
2. Playbook 01 — implementar primeira rota api-delpi (`GET /engineering/mini-applicators/ferramentas`) com contrato registrado.
3. Fase 1 — CRUD reposições/motivos no Postgres + gateway de ferramentas.
