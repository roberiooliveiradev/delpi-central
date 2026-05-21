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
| Registro no Core API | App + permissões iniciais | Pendente (manual) |
| CI mínimo | lint + testes do calculador | Fase 2 |

**Critério de pronto:** `GET /health` e MFE “hello” carregando no portal com JWT.

## Fase 1 — CRUD e catálogos (2–3 sprints) ✅ MVP no repo

**Objetivo:** substituir cadastro na planilha.

| Entrega | Detalhe | Status |
|---------|---------|--------|
| Migration V002 | Tabelas cadastrais + `audit_logs` | ✅ |
| API CRUD | processos, revisões (+ ativar), medições, investimentos, recursos, vínculos | ✅ |
| Validações | catálogos §4, exclusão lógica | ✅ |
| UI cadastro | lista processos + novo processo + revisões no detalhe | ✅ |
| Auditoria | `audit_logs` nas mutações | ✅ |
| UI medições/investimentos/recursos | Formulários no detalhe da revisão (clique na linha) | ✅ |

**Critério de pronto:** criar processo completo só pela UI, sem abrir Sheets (baseline + melhoria + medições + vínculos).

**Deploy:** rebuild `transformometro-api` e `transformometro` no servidor (`TM_RUN_MIGRATIONS_ON_STARTUP=true` aplica V002).

## Fase 2 — Cálculo e dashboard (2 sprints) 🚧 MVP no repo

**Objetivo:** paridade com Apps Script / `dashboard_calculos`.

| Entrega | Detalhe | Status |
|---------|---------|--------|
| Migration V003 `dashboard_calculos` | Materialização por revisão + competência | ✅ |
| `DashboardCalculatorService` | Spec (max economias, delta recursos, líquida = bruta − recorrente) | ✅ |
| Testes golden | `tests/test_dashboard_calculator.py` + fixture JSON | ✅ |
| `POST /dashboard/recalcular` | Rebuild síncrono TRUNCATE + insert | ✅ |
| `GET /dashboard/resumo`, `/evolucao`, `/processos` | Filtros filial/período; fallback cálculo em memória | ✅ |
| UI dashboard | Cards, tabela evolução, ranking, botão recalcular | ✅ |
| Migração planilha | script import + relatório diff | Pendente |

**Critério de pronto:** números batem com planilha para amostra de ≥10 processos (incl. economia negativa).

**Diferença vs Transforma+ legado:** listagem legada subtrai custo compartilhado inteiro na economia diária; spec usa delta de recursos na economia bruta e não repete na líquida.

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

1. **Deploy** Fase 2 (`TM_RUN_MIGRATIONS_ON_STARTUP` aplica V003; rebuild API + MFE)
2. Rodar **Recalcular** no dashboard após cadastrar dados
3. Script de **import da planilha** + diff contra golden
4. Registrar app no Core API (manifesto + permissões)
