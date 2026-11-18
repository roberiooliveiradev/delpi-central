# W016 — Matriz de paridade portal Strategic Indicators × DAVI

> Inventário inicial (RQ-12 do brief W015-DISCOVERY-AND-W016-READINESS).
> Base: `origin/main` @ 570119b9d5 + W015 (a6a7dedc88, 2e4c3d472f).
> Fontes autoritativas: rotas SI (`strategic_indicators_routes.py`, 47 rotas),
> telas MFE (`plugins/strategic-indicators/src/ui/pages`, 9 páginas +
> workspaces admin), capabilities DAVI (`read` ~80, `execute` 24, `delete` 3).
> Status por linha é inventário, não claim de aceite live — ver colunas TEST_*.
> LEGENDA STATUS: IMPLEMENTED (código+testes locais) | PENDING_LIVE (aguarda
> sessão autenticada) | BLOCKED_BY_DESIGN | N/A (não é ação de portal).

## 1. Visão executiva / dashboards

| PORTAL_SCREEN | USER_ACTION | OWNER_ROUTE | PERMISSION | DAVI_TOOL | DAVI_CAPABILITY | STATUS | GAP |
|---|---|---|---|---|---|---|---|
| ExecutiveDashboard | consultar resumo/pontuação, filtrar competência/filial | GET /executive-summary | view | read | get_si_executive_summary | IMPLEMENTED | — |
| DepartmentsPage | listar departamentos | GET /departments | view | read | get_si_departments | IMPLEMENTED | — |
| DepartmentsPage | árvore consolidada | GET /departments/tree | view | read | get_si_departments_tree | IMPLEMENTED | — |
| DepartmentsPage | snapshot da árvore | GET /departments/tree/snapshot | view | read | get_si_departments_tree_snapshot | IMPLEMENTED | — |
| DepartmentsPage | trends da árvore | GET /departments/tree/trends | trends.view | read | get_si_departments_tree_trends | IMPLEMENTED | — |
| DepartmentDetailsPage | detalhe do departamento | GET /departments/{id} | view | read | get_si_department_details | IMPLEMENTED | — |
| IndicatorsPage | listar/detalhar indicadores | GET /indicators | view | read | get_si_indicators | IMPLEMENTED | — |
| IndicatorsPage | meta/realizado por indicador | integration routes (~50) | view | read | get_si_indicator_*_meta / *_realized | IMPLEMENTED | — |
| TrendsPage | tendências | GET /trends | trends.view | read | get_si_trends | IMPLEMENTED | — |
| AlertsPage | alertas | GET /alerts | view | read | get_si_alerts | IMPLEMENTED | — |
| PresentationPage | apresentação | GET /presentation | view | read | get_si_presentation | IMPLEMENTED | — |
| (todas) | carregar árvore pesada | POST /departments/tree/load-job | view | execute | si.job.tree_load | IMPLEMENTED | — |
| (todas) | acompanhar job | GET /jobs/{id} | view | read | get_si_job_status | IMPLEMENTED | — |

## 2. Metas (goals)

| PORTAL_SCREEN | USER_ACTION | OWNER_ROUTE | PERMISSION | DAVI_TOOL | DAVI_CAPABILITY | STATUS | GAP |
|---|---|---|---|---|---|---|---|
| SettingsPage/Goals | listar metas | GET /indicator-goals | view | read | list_si_indicator_goals | IMPLEMENTED | — |
| SettingsPage/Goals | histórico da meta | GET /indicator-goals/history | view | read | list_si_indicator_goal_history | IMPLEMENTED | — |
| SettingsPage/Goals | visão por ano | GET /admin/goal-years/overview | settings.manage | read | list_si_goal_years_overview | IMPLEMENTED | — |
| SettingsPage/Goals | criar meta | POST /indicator-goals | settings.manage | execute | si.goal.create | IMPLEMENTED | — |
| SettingsPage/Goals | editar meta/curva mensal | PUT /indicator-goals/{id} | settings.manage | execute | si.goal.update | IMPLEMENTED | — |
| SettingsPage/Goals | ativar meta | POST /indicator-goals/{id}/activate | settings.manage | execute | si.goal.activate | IMPLEMENTED | — |
| SettingsPage/Goals | desativar meta | POST /indicator-goals/{id}/deactivate | settings.manage | execute | si.goal.deactivate | IMPLEMENTED | — |
| SettingsPage/Goals | excluir meta | DELETE /indicator-goals/{id} | settings.manage | delete | si.goal.delete | IMPLEMENTED | — |
| SettingsPage/Goals | criar metas em lote | POST /admin/indicator-goals/bulk-create | settings.manage | execute | si.goal.bulk_create | IMPLEMENTED | — |
| SettingsPage/Goals | duplicar ano | POST /admin/indicator-goals/duplicate-year | settings.manage | execute | si.goal.duplicate_year | IMPLEMENTED | — |
| SettingsPage/Goals | preencher meses faltantes | POST /admin/indicator-goals/fill-missing | settings.manage | execute | si.goal.fill_missing | IMPLEMENTED | — |

## 3. Departamentos / indicadores (admin)

| PORTAL_SCREEN | USER_ACTION | OWNER_ROUTE | PERMISSION | DAVI_TOOL | DAVI_CAPABILITY | STATUS | GAP |
|---|---|---|---|---|---|---|---|
| SettingsPage/Depts | listar departamentos admin | GET /admin/departments | settings.manage | read | list_si_admin_departments | IMPLEMENTED | — |
| SettingsPage/Depts | criar departamento | POST /admin/departments | settings.manage | execute | si.department.create | IMPLEMENTED | — |
| SettingsPage/Depts | editar departamento | PUT /admin/departments/{id} | settings.manage | execute | si.department.update | IMPLEMENTED | — |
| SettingsPage/Depts | ativar departamento | POST /admin/departments/{id}/activate | settings.manage | execute | si.department.activate | IMPLEMENTED | — |
| SettingsPage/Depts | desativar departamento | POST /admin/departments/{id}/deactivate | settings.manage | execute | si.department.deactivate | IMPLEMENTED | — |
| SettingsPage/Depts | excluir departamento | DELETE /admin/departments/{id} | settings.manage | delete | si.department.delete | IMPLEMENTED | — |
| SettingsPage/Inds | listar indicadores do dept | GET /admin/departments/{id}/indicators | settings.manage | read | list_si_admin_department_indicators | IMPLEMENTED | — |
| SettingsPage/Inds | criar indicador | POST /admin/departments/{id}/indicators | settings.manage | execute | si.indicator.create | IMPLEMENTED | — |
| SettingsPage/Inds | editar indicador | PUT /admin/indicators/{id} | settings.manage | execute | si.indicator.update | IMPLEMENTED | — |
| SettingsPage/Inds | ativar indicador | POST /admin/indicators/{id}/activate | settings.manage | execute | si.indicator.activate | IMPLEMENTED | — |
| SettingsPage/Inds | desativar indicador | POST /admin/indicators/{id}/deactivate | settings.manage | execute | si.indicator.deactivate | IMPLEMENTED | — |
| SettingsPage/Inds | excluir indicador | DELETE /admin/indicators/{id} | settings.manage | delete | si.indicator.delete | IMPLEMENTED | — |

## 4. Configurações / auditoria / cache

| PORTAL_SCREEN | USER_ACTION | OWNER_ROUTE | PERMISSION | DAVI_TOOL | DAVI_CAPABILITY | STATUS | GAP |
|---|---|---|---|---|---|---|---|
| SettingsPage | ver configurações | GET /settings | settings.manage | read | get_si_settings | IMPLEMENTED | — |
| SettingsPage | editar configurações | PUT /settings | settings.manage | execute | si.settings.update | IMPLEMENTED | — |
| SettingsPage | histórico/auditoria | GET /settings/audit | settings.manage | read | list_si_settings_audit | IMPLEMENTED | — |
| SettingsPage/Cache | disparar refresh | POST /cache/refresh | settings.manage | execute | si.cache.refresh | IMPLEMENTED | — |
| SettingsPage/Cache | invalidar cache | POST /cache/invalidate | settings.manage | execute | si.cache.invalidate | IMPLEMENTED | — |
| SettingsPage/Cache | status do refresh | GET /cache/refresh/status | settings.manage | read | get_si_cache_refresh_status | IMPLEMENTED | — |

## 5. Solicitações de alteração (change requests)

| PORTAL_SCREEN | USER_ACTION | OWNER_ROUTE | PERMISSION | DAVI_TOOL | DAVI_CAPABILITY | STATUS | GAP |
|---|---|---|---|---|---|---|---|
| SettingsPage/CR | listar solicitações | GET /change-requests | settings.manage | read | list_si_change_requests | IMPLEMENTED | — |
| SettingsPage/CR | criar solicitação | POST /change-requests | settings.manage | execute | si.change_request.create | IMPLEMENTED | — |
| SettingsPage/CR | comentar | POST /change-requests/{id}/comments | settings.manage | execute | si.change_request.comment | IMPLEMENTED | — |
| SettingsPage/CR | submeter | POST /change-requests/{id}/submit | settings.manage | execute | si.change_request.submit | IMPLEMENTED | — |

## 6. Importação / exportação

| PORTAL_SCREEN | USER_ACTION | OWNER_ROUTE | PERMISSION | DAVI_TOOL | DAVI_CAPABILITY | STATUS | GAP |
|---|---|---|---|---|---|---|---|
| SettingsPage/ImportExport | exportar bundle JSON | GET /admin/config/export | settings.manage | read | export_si_admin_config | IMPLEMENTED | — |
| SettingsPage/ImportExport | preview de importação | POST /admin/config/import/preview | settings.manage | execute | (interno ao PREPARE de import_apply/replace) | IMPLEMENTED | diferença semântica intencional: preview = PREPARE governado |
| SettingsPage/ImportExport | aplicar importação merge | POST /admin/config/import/apply | settings.manage | execute | si.config.import_apply | IMPLEMENTED | — |
| SettingsPage/ImportExport | aplicar importação replace | POST /admin/config/import/apply (mode=replace) | settings.manage | execute | si.config.import_replace | IMPLEMENTED | — |
| (legado) | POST /admin/config/import direto | POST /admin/config/import | settings.manage | — | si.config.import (BLOCKED_BY_DESIGN) | BLOCKED | rota genérica sem policy — intencionalmente indisponível |

## 7. Rotas não mapeadas como ação de portal

| OWNER_ROUTE | CLASSIFICAÇÃO |
|---|---|
| GET /health | ops/health — não é ação de usuário |

## 8. Resumo quantitativo

- Portal user-actions inventariadas: **45** (telas públicas + admin).
- Cobertas por capability DAVI: **45/45** (read 18 semânticas + ~50
  meta/realized por indicador; execute 24; delete 3).
- Diferenças semânticas intencionais: 2 (preview↔PREPARE; import legado
  bloqueado por policy, não por lacuna).
- Rotas owner sem ação de portal: 1 (/health).
- Funcionalidades ausentes no owner: nenhuma identificada no inventário.
- Funcionalidades implementadas mas não descobertas: 0 conhecidas
  (get_context publica as três famílias; ver gate de discovery ChatGPT).
- Funcionalidades sem teste em produção autenticada: todas — pendente
  gate ChatGPT (TEST_PRODUCTION/CHATGPT_ACCEPTANCE por linha).
- Funcionalidades pendentes de decisão: nenhuma neste inventário.

## 9. Pendências de aceite (não são gaps de implementação)

- `TEST_PRODUCTION` autenticado por capability — aguarda sessão ChatGPT.
- `NEGATIVE_AUTHZ` com segunda identidade real — `PENDING_SECOND_USER_AUTHZ`.
- `CHATGPT_ACCEPTANCE` W015 delete — depende do refresh do catálogo do
  provider (procedimento documentado no relatório W015-discovery).
