# Roadmap — Transformômetro App

Entregas em fases para reduzir risco e reaproveitar o que já funciona no monorepo.

## Fase 0 — Fundação (1–2 sprints) ✅ entregue no repo

**Objetivo:** esqueleto deployável no Docker dev, sem quebrar legado.

| Entrega | Detalhe | Status |
|---------|---------|--------|
| Pastas `transformometro-api/` + `plugins/transformometro/` | `main.py`, health, Dockerfile, manifest MFE | ✅ |
| Migrations `V001` schema `transformometro` | Schema + `schema_migrations` | ✅ |
| Compose + gateway | URLs `/apps/transformometro` e `/apps/transformometro-api` | ✅ |
| Build MFE | `npm run build` no plugin | ✅ |
| Registro no Core API | App + permissões iniciais | Manual (menu já pode aparecer antes do deploy do MFE) |
| Serviços em `docker-compose.yml` (prod) | `transformometro` + `transformometro-api` | ✅ |
| CI mínimo | lint + testes do calculador | Fase 2 |

**Critério de pronto:** `GET /health` e MFE “hello” carregando no portal com JWT.

## Fase 1 — CRUD e catálogos (2–3 sprints)

**Objetivo:** substituir cadastro na planilha.

| Entrega | Detalhe |
|---------|---------|
| API CRUD | processos, revisões (+ ativar), medições, investimentos, recursos, vínculos |
| Validações | catálogos §4 da spec, exclusão lógica, versão texto |
| UI cadastro | listas + formulários + detalhe processo |
| Auditoria | `audit_logs` nas mutações |

**Critério de pronto:** criar processo completo só pela UI, sem abrir Sheets.

## Fase 2 — Cálculo e dashboard (2 sprints)

**Objetivo:** paridade com Apps Script / `dashboard_calculos`.

| Entrega | Detalhe |
|---------|---------|
| `DashboardCalculatorService` | Calculador spec-compliant + testes golden |
| `POST /dashboard/recalcular` | Job síncrono ou background |
| UI dashboard | cards, evolução mensal, ranking, filtros |
| Migração | script import planilha atual + relatório diff |

**Critério de pronto:** números batem com planilha para amostra de ≥10 processos (incl. economia negativa).

## Fase 3 — Produção e desligamento planilha (1 sprint)

| Entrega | Detalhe |
|---------|---------|
| Permissões finas + revisão de segurança | |
| Documentação OPERATIONS / DEPLOYMENT | |
| Desativar escrita na planilha | somente leitura ou desligada |
| Opcional: SI/engineering leem `transformometro-api` | trocar fonte do indicador engenharia |

## Fase 4 — Melhorias (backlog)

- Rateio por família de processo / agrupador “ferramenta”
- Alertas (processo com economia líquida negativa > N meses)
- Export Excel/PDF
- Comparativo multi-revisão na UI
- Workflow de aprovação de revisão

## Matriz de reaproveitamento

| Ativo atual | Ação |
|-------------|------|
| `process_summary_calculator.py` | Mover para `tm_app`, ajustar à spec, testes |
| `process_repository.py` (Sheets) | Referência para migração; deprecar após Fase 2 |
| `dashboard-engineering/TransformaPage` | Inspirar UX; redirecionar para novo plugin |
| `documentacao_modelagem_transformometro.md` | Fonte de verdade das regras (manter sync) |
| Planilha `193G5ff5...` | Snapshot de migração; não produção |

## Riscos e mitigação

| Risco | Mitigação |
|-------|-----------|
| Divergência spec vs calculador legado | Testes golden + doc de breaking changes |
| Volume de vínculos ChatGPT/Robério | UX avisa quando rateio > ganho operacional |
| Datas UTC | `DATE` no PG; API só `yyyy-MM-dd` |
| Performance recálculo | Recalcular competências incrementais |

## Próximo passo imediato

1. Aprovar estrutura de pastas e permissões ([OVERVIEW.md](./OVERVIEW.md))
2. Iniciar **Fase 0** (scaffold API + MFE + migration V001)
3. Paralelo: extrair calculador com suite de testes da planilha

Quando quiser começar a implementação da Fase 0 no código, peça explicitamente para subir o scaffold no repositório.
