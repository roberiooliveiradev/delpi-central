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
| Registro no Core API | `plugins/transformometro/scripts/register-manifest.sh` | Pendente (manual no portal) |
| CI mínimo | `scripts/ci-transformometro-api.sh` (pytest calculador) | ✅ |

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
| UI medições/investimentos/recursos | Abas na revisão (vigência, medição, investimentos, vínculos) | ✅ |
| Catálogo recursos (menu) | `/recursos` — CRUD global + vínculo na revisão | ✅ |

**Critério de pronto:** criar processo completo só pela UI, sem abrir Sheets (baseline + melhoria + medições + vínculos).

**Deploy:** rebuild `transformometro-api` e `transformometro` no servidor (`TM_RUN_MIGRATIONS_ON_STARTUP=true` aplica V002).

## Fase 2 — Cálculo e dashboard (2 sprints) ✅ MVP no repo

**Objetivo:** paridade com Apps Script / `dashboard_calculos`.

| Entrega | Detalhe | Status |
|---------|---------|--------|
| Migration V003 `dashboard_calculos` | Materialização por revisão + competência | ✅ |
| `DashboardCalculatorService` | Spec (max economias, delta recursos, líquida = bruta − recorrente) | ✅ |
| Testes golden | `tests/test_dashboard_calculator.py` + fixture JSON | ✅ |
| `POST /dashboard/recalcular` | Rebuild síncrono TRUNCATE + insert | ✅ |
| `GET /dashboard/resumo`, `/evolucao`, `/processos` | Filtros filial/período; fallback cálculo em memória | ✅ |
| UI dashboard | Cards, tabela evolução, ranking, botão recalcular | ✅ |
| Import planilha | Removido — cadastro via CRUD | — |

**Critério de pronto:** números batem com planilha para amostra de ≥10 processos (incl. economia negativa).

**Diferença vs Transforma+ legado:** listagem legada subtrai custo compartilhado inteiro na economia diária; spec usa delta de recursos na economia bruta e não repete na líquida.

## Fase 3 — Produção e desligamento planilha (1 sprint) ✅ código / 🚧 ops

| Entrega | Detalhe | Status |
|---------|---------|--------|
| Dados em produção | Migração via backup JSON (`import_cadastro_json.py --apply --replace`) | ✅ |
| Documentação | [OPERATIONS.md](./OPERATIONS.md), [DEPLOYMENT.md](../../../transformometro-api/docs/DEPLOYMENT.md), [status-atual.md](./status-atual.md) | ✅ |
| Manifesto + script registro | `register-manifest.sh`, permissões completas | ✅ repo |
| Registro RBAC no portal | Atribuir `transformometro.*` às roles/grupos na **Core API** | Pendente (manual) |
| Desativar escrita na planilha | somente leitura ou desligada | Pendente (Google) |
| SI/engineering → transformometro-api HTTP | `transformometro_client` + gateway + token interno | ✅ |
| Testes integração engenharia | `tests/test_engineering_transforma_mais.py` | ✅ |

## Fase 4 — Melhorias (2 sprints) ✅ MVP no repo

| Entrega | Detalhe | Status |
|---------|---------|--------|
| Migration V004 | `familia_processo`, `agrupador_ferramenta` em `processos` | ✅ |
| Rateio / família | CRUD, filtro listagem, `GET /dashboard/por-familia` + tabela no dashboard | ✅ |
| Alertas economia negativa | `GET /dashboard/alertas` (≥ N meses consecutivos) | ✅ |
| Export dashboard | `GET /dashboard/export.csv` | ✅ |
| Comparativo revisões | `GET /processos/{id}/comparativo` + tabela no detalhe | ✅ |
| Diagnóstico rateio | `GET /revisoes/{id}/diagnostico-rateio` + painel na revisão | ✅ |
| UI Fase 4 | Alertas + CSV/Excel no dashboard; família no cadastro; comparativo + rateio | ✅ |
| Testes | `tests/test_phase4_services.py` | ✅ |
| Ativar revisão | `POST /revisoes/{id}/ativar` (sem workflow de aprovação; V006) | ✅ |
| Export Excel | `GET /dashboard/export.xls` (HTML formatado, abre no Excel) + botão no MFE | ✅ |
| Export PDF | Botão imprimir + CSS `@media print` no dashboard | ✅ |
| URLs processo/revisão | `/processos/{id}` e `/revisoes/{id}` no MFE | ✅ |
| Recálculo incremental | `POST /recalcular` com escopo | ✅ |

## Matriz de reaproveitamento

| Ativo | Status (jun/2026) |
|-------|-------------------|
| `DashboardCalculatorService` (`tm_app`) | ✅ Canônico — substitui `ProcessSummaryCalculator` |
| `process_repository.py` (Sheets, api-delpi) | 🧹 Código morto — não ligado ao composer; remover em limpeza |
| `dashboard-engineering/TransformaPage` | ✅ Ativo (read-only KPI) — dados via api-delpi → Postgres; não substitui cadastro |
| `documentacao_modelagem_transformometro.md` | Referência histórica + regras; sync com `regras-de-calculo.md` |
| Planilha Google Sheets | Fora do runtime; desligar escrita (ops) |
| Rotas `/engineering/transforma-mais/*` | Contrato HTTP mantido; backend = `TransformometroTransformaMaisGateway` |

## Riscos e mitigação

| Risco | Mitigação |
|-------|-----------|
| Divergência spec vs calculador legado | Testes golden + doc de breaking changes |
| Volume de vínculos ChatGPT/Robério | UX avisa quando rateio > ganho operacional |
| Datas UTC | `DATE` no PG; API só `yyyy-MM-dd` |
| Performance recálculo | Recalcular competências incrementais |

## Fase 5 — Instâncias, filiais UUID e escopo híbrido ✅ entregue (jun/2026)

**Objetivo:** processo-mestre + instâncias `(filial × setor)`, PK UUID, rateio híbrido, visões consolidado/filial/dept, RBAC filial — sem quebrar contrato **api-delpi** Transforma+.

Plano: [PLAYBOOK-18-instancias-filial-setor-escopo.md](./PLAYBOOK-18-instancias-filial-setor-escopo.md) · status: [playbook-18-implementation-status.md](../../../transformometro-api/docs/playbook-18-implementation-status.md).

| Sprint | Entrega | Status |
|--------|---------|--------|
| S1–S2 | Filiais/setores UUID (V011–V012) | ✅ |
| S3–S4 | Instâncias + processo mestre (V013–V015) | ✅ |
| S5 | `escopo_recurso` (V016) | ✅ |
| S6 | Cache UUID (V017) | ✅ |
| S7 | Visões `view` dashboard | ✅ |
| S8 | Duplicar instância (V018) | ✅ |
| S9 | Integração api-delpi por instância | ✅ |
| S10 | RBAC filial server-side | ✅ |
| MFE §9 | Instâncias, rotas, toggle dashboard, escopo recurso | ✅ |
| Docs | MODELAGEM, ARCHITECTURE, regras-de-calculo | ✅ |

**Deploy:** export JSON → migrations V011–V028 (auto) → bootstrap filiais → recalc dashboard → rebuild API + MFE → manifesto RBAC.

## Fase 7 — Diagramas de processo ✅ entregue (jul/2026)

**Objetivo:** diagrama-macro no processo, escopo por instância, overlay as-is/to-be por revisão — documentação visual estruturada (não BPMN XML).

Plano: [PLAYBOOK-19-diagramas-processo-revisao-escopo.md](./PLAYBOOK-19-diagramas-processo-revisao-escopo.md) · status: [playbook-19-implementation-status.md](../../../transformometro-api/docs/playbook-19-implementation-status.md).

| Sprint | Entrega | Status |
|--------|---------|--------|
| S0 | ADR + JSON Schema | ✅ |
| S1 | V026 + macro + editor processo | ✅ |
| S2 | V027 + escopo instância | ✅ |
| S3 | V028 + overlay revisão + merge | ✅ |
| S4 | Backup JSON + audit | ✅ |
| S5 | Diff baseline/melhoria + PNG evidência | ✅ |
| S6 | Swimlanes BPMN-lite, tema, auto-layout, gestão de faixas | ✅ |

**Backlog pós-MVP:** action chat com Mermaid da revisão; swimlanes automáticas por unidade/departamento.

## Fase 8 — Decomposição de processo (árvore + planilha) 🚧 roadmap (jul/2026)

**Objetivo:** árvore WBS no processo-mestre (processo-chave → tarefa → sub-tarefa), export tabular no formato planilha operacional, escopo/overlay por instância/revisão, vínculo com diagrama macro (Playbook 19).

Plano: [PLAYBOOK-20-decomposicao-processo-arvore-mapeamento.md](./PLAYBOOK-20-decomposicao-processo-arvore-mapeamento.md) · status: [playbook-20-implementation-status.md](../../../transformometro-api/docs/playbook-20-implementation-status.md).

| Sprint | Entrega | Status |
|--------|---------|--------|
| S0 | Playbook + JSON Schema + ADR | ✅ doc |
| S1 | V030 + árvore + editor processo | ✅ |
| S2 | Export CSV/Excel | ✅ CSV |
| S3 | V031 + escopo instância + contexto V033 | ✅ |
| S4 | V032 + overlay revisão + backup | ✅ |
| S5 | Vínculo fluxo + assistente rascunho | ✅ parcial |
| S6 | Colaboração + diff textual | ✅ parcial |

## Fase 6 — Limpeza de legado (pendente)

**Objetivo:** remover código e config órfãos após confirmação em produção.

| Entrega | Detalhe | Status |
|---------|---------|--------|
| Remover `google_sheets/transforma_mais` da api-delpi | `process_repository.py`, `sheet_sources.py`, port morto | Pendente |
| Remover `TRANSFORMA_MAIS_SHEET_*` e `TRANSFORMA_MAIS_DATA_SOURCE` | Env vars sem consumidor | Pendente |
| Planilha somente leitura | Google Workspace | Pendente (ops) |
| Atualizar docs que citam Sheets como fonte ativa | README, ESPECIFICACAO (nota histórica) | ✅ parcial |
| (Opcional) Link do TransformaPage → plugin transformometro | UX — painel read-only pode permanecer | Pendente |

## Próximo passo imediato

1. **Deploy produção** com runbook em [status-atual.md](./status-atual.md) e [OPERATIONS.md](./OPERATIONS.md) (incl. V026–V028 na 1ª subida pós-pull)
2. **Registrar manifesto** na Core API + RBAC escopado (quem precisar)
3. **Planilha somente leitura** (checklist Google)
4. Validar smoke pós-deploy: diagrama macro → escopo instância → overlay revisão → export PNG
5. **Limpeza Fase 6** — apagar código Sheets morto na api-delpi
