# Roadmap — Manutenção

Entregas em fases para reduzir risco, reaproveitar padrões do monorepo e migrar o legado **MiniAplicadores** sem duplicar integração TOTVS.

## Fase 0 — Fundação (1–2 sprints) ✅ concluída

**Objetivo:** esqueleto deployável no Docker dev + contratos documentados.

| Entrega | Detalhe | Status |
|---------|---------|--------|
| Docs produto | `docs/12-roadmap-e-evolucao/maintenance/` | ✅ |
| Docs API | `maintenance-api/docs/` | ✅ |
| Manifesto MFE rascunho | `plugins/maintenance/maintenance.manifest.json` | ✅ |
| Pastas `maintenance-api/` + `plugins/maintenance/` | `main.py`, health, Dockerfile, MFE hello | ✅ |
| Migration `V001` schema `maintenance` | `schema_migrations` | ✅ |
| Compose + gateway | URLs `/apps/maintenance` e `/apps/maintenance-api` | ✅ |
| Playbook 01 — rotas api-delpi | Contrato + primeira rota `GET .../ferramentas` | ✅ |
| CI mínimo | `scripts/ci-maintenance-api.sh` | ✅ |

**Critério de pronto:** `GET /health` na API dedicada; MFE placeholder no portal; uma rota TOTVS na api-delpi consumida por gateway de teste.

## Fase 1 — CRUD operacional (2–3 sprints) ✅ concluída

**Objetivo:** substituir Access para reposições e configuração.

| Entrega | Detalhe |
|---------|---------|
| Migration V002 | `motivos`, `reposicoes`, `status_peca`, `audit_logs` (tabela; gravação ativa jun/2026) |
| API CRUD | reposições (soft delete), motivos, status, revisão programada, realizações |
| Gateways TOTVS | ferramentas, peças por ferramenta, golpes no período |
| UI mini-aplicadores | lista ferramentas, detalhe, form reposição, revisão programada, auditoria |
| Validações | espelhar `ReposicaoService` legado (golpes > 0, data > última troca) |
| RBAC filial | escopo 01/02 nas mutações |

**Critério de pronto:** registrar reposição completa pela UI web, sem Access; listar ferramentas/peças via api-delpi.

## Fase 2 — Preventiva e relatório (2 sprints) ✅ concluída

**Objetivo:** paridade com aba Relatório + alertas do WinForms.

| Entrega | Detalhe |
|---------|---------|
| `PreventivaService` | média golpes, % uso, classificação status |
| Endpoints | últimas reposições, alertas, histórico por ferramenta/peça |
| UI relatório | tabelas paginadas/ordenáveis, cores CRÍTICO/ATENÇÃO/OK, painel detalhe |
| Gráfico | histórico golpes (linha + tendência) e uso vs. média (Recharts) |
| Testes | golden cases a partir de fixtures legado |

**Critério de pronto:** ranking preventivo bate com amostra validada contra WinForms para ≥5 pares ferramenta/peça.

## Fase 3 — Migração de dados e produção (1 sprint) 🚧 em curso

| Entrega | Detalhe |
|---------|---------|
| Script import Access → Postgres | one-shot ou CLI |
| Registro manifesto na Core API + RBAC (perfis/roles) | `plugins/maintenance/scripts/register-manifest.sh` |
| Desligar WinForms | somente leitura ou descontinuado |
| Runbook | OPERATIONS.md |

## Fase 4 — Extensões do produto (backlog)

| Entrega | Detalhe |
|---------|---------|
| Outros tipos de ferramenta | além de mini-aplicadores, mesmo plugin |
| Fachada api-delpi | resumo preventivo para chat/SI se necessário |
| Parâmetros preventivos por filial | wireframe `telas.md` legado |
| Integração agente chat | OpenAPI snapshot + políticas |

## Matriz de reaproveitamento

| Ativo legado | Destino no monorepo |
|--------------|---------------------|
| `TabReposicoes`, `TabMotivo`, `TabStatusPeca` | Postgres V002 |
| Queries SB1010 / SG1010 | api-delpi `/engineering/mini-applicators/*` |
| Query golpes SD4/SHY/SH4/SH6 | api-delpi `.../golpes` |
| `FormMain` preventiva | `PreventivaService` + UI relatório |
| Access em rede | Postgres plugins — **sem** Access no runtime web |

## Riscos e mitigação

| Risco | Mitigação |
|-------|-----------|
| Duplicar SQL TOTVS na API do plugin | Playbook 01 + code review; gateways obrigatórios |
| Divergência números golpes vs legado | Testes de contrato api-delpi + amostra manual |
| `FerramentaService` legado engole erro → golpes 0 | Gateway com erro explícito + envelope |
| RBAC filial | Copiar modelo Transformômetro Playbook 18 |

## Dependências entre times / repos

```text
Fase 0: docs ✅ → api-delpi rota ferramentas → gateway → API skeleton → MFE skeleton → compose
Fase 1: migrations → CRUD API → UI cadastro
Fase 2: golpes gateway estável → preventiva → relatório UI
Fase 3: import Access → go-live
```
