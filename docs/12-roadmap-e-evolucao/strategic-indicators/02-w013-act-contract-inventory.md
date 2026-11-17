# W013-ACT — Inventário de contratos de escrita administrativa (Strategic Indicators ↔ DAVI)

**TASK_ID origem:** `DAVI-SI-W013-READ-CLOSURE-AND-ACT-READINESS-01` (Frente B)
**Status:** `READ_ONLY_INVENTORY / CONTRACT_SPEC / NO_CODE / NO_DEPLOY / NO_WRITE`
**Autoridade:** Strategic Indicators API é owner de dados, regras, AuthZ efetiva, persistência e auditoria. DAVI/api-delpi é façade semântica; nenhum write é executado em banco nem com service token.
**Wave:** W013-ACT (departments, indicators, settings, change requests). W014 (batch/jobs/config-import/cache) foi implementada neste mesmo contrato (§10); W015 (deletes destrutivos + mode=replace) segue bloqueado.

Este documento NÃO autoriza implementação. Cada operação abaixo requer briefing de implementação aprovado pela Coordination antes de virar capability `si.*` no `execute` governado.

## 1. Padrão governado obrigatório (todas as operações)

```text
PREPARE → DIFF → CONFIRMAÇÃO EXPLÍCITA NO CHAT → ACT → AUTHZ OWNER → OCC → AUDIT → READ-BACK
```

- `execute` permanece a única ferramenta semântica ACT — nunca uma tool por endpoint.
- PREPARE: proposta selada server-side bound a `actor + capability + state fingerprint + diff exato` (padrão W012 `si.goal.*` — ADR `davi/02-adr-proposta-consentimento-humano-confiavel-w012.md`).
- ACT: exige proposal selada, confirmação humana explícita (`confirm=true` é model-mediated, não prova criptográfica independente), revalidação AuthZ no owner, consumo single-use da proposta, execução pelo owner e read-back pós-condição.
- Identidade: end-user JWT encaminhado verbatim ao SI em PREPARE e ACT. `X-Delpi-Service-Token` jamais em fluxo user-parity.
- Permissão efetiva: enforcement final é o `require_permission` do owner — o BFF pode fail-fast mas nunca autoriza.
- `auto_act` proibido para operações consequenciais sem política aprovada por operação.

## 2. Operações inventariadas — Departamentos (owner routes `/admin/departments*`)

| # | Capability proposta | Owner route | Tipo | Classe |
|---|---|---|---|---|
| D1 | `si.department.create` | `POST /admin/departments` | direct mutation | READY_FOR_IMPLEMENTATION |
| D2 | `si.department.update` | `PUT /admin/departments/{department_id}` | direct mutation (full-replace body; `new_department_id` permite rename de PK) | READY_FOR_IMPLEMENTATION |
| D3 | `si.department.activate` | `POST /admin/departments/{id}/activate` | activation | READY_FOR_IMPLEMENTATION |
| D4 | `si.department.deactivate` | `POST /admin/departments/{id}/deactivate` | deactivation | RESOLVIDO §9 → `D4_IMPLEMENTED` |
| D5 | `si.department.delete` | `DELETE /admin/departments/{id}` | destructive | **W015 — BLOCKED** (não implementar nesta wave) |
| — | reorder/hierarquia/peso | sem rota dedicada — via D2 (`display_order`, `weight_pct`) | — | coberto por D2; sem endpoint separado no owner |

**Body D1** (`CreateDepartmentBodySchema`): `department_id`, `department_name`, `short_name`, `strategic_summary`, `headline_goal`, `supporting_focus`, `weight_pct`, `aggregation_mode`, `display_order`.
**Body D2** (`UpdateDepartmentBodySchema`): idem + `new_department_id` (rename), `is_active`.
**Permission:** `strategic-indicators.settings.manage`. **Actor:** `_extract_actor(request)` → `actor_user_id`/`actor_email` gravados em audit columns.
**Side effects:** `_invalidate_read_cache_after_mutation` em todas as mutações — snapshots/árvore/cache ficam stale-consistent.
**OCC:** owner não expõe precondition token para departments → OCC deve ser state-fingerprint da proposta (read-back do estado atual no PREPARE) + revalidação AuthZ+estado no ACT; race residual aceito se documentado.
**Idempotência:** create é natural key (`department_id` → 400 duplicado tipado); activate/deactivate/update são idempotentes por natureza de estado; retry-safe.
**Erros:** `ValueError → 400` tipado; `500` genérico — mapear para `VALIDATION_ERROR`/`OWNER_ERROR` no orchestrator.
**Postcondition:** read-back via `GET /admin/departments` (op W013 `list_si_admin_departments`) + verificação de `updated_by`/campos aplicados.
**Classificação pendente:** nenhuma — D4 resolvido em §9 (impact list obrigatório no PREPARE diff, implementado).

## 3. Operações inventariadas — Indicadores (`/admin/**indicators*`)

| # | Capability proposta | Owner route | Tipo | Classe |
|---|---|---|---|---|
| I1 | `si.indicator.create` | `POST /admin/departments/{department_id}/indicators` | direct mutation (associa ao departamento na criação) | READY_FOR_IMPLEMENTATION |
| I2 | `si.indicator.update` | `PUT /admin/indicators/{indicator_id}` | direct mutation (`new_indicator_id` rename; `weight_pct`, `scope_type`, `performance_direction`, `value_*`, `aggregation implícito`) | READY_FOR_IMPLEMENTATION |
| I3 | `si.indicator.activate` | `POST /admin/indicators/{id}/activate` | activation | READY_FOR_IMPLEMENTATION |
| I4 | `si.indicator.deactivate` | `POST /admin/indicators/{id}/deactivate` | deactivation | READY_FOR_IMPLEMENTATION |
| I5 | `si.indicator.delete` | `DELETE /admin/indicators/{id}` | destructive | **W015 — BLOCKED** |
| — | re-associação entre departamentos | **não existe** no owner (update não aceita `department_id`) | — | **NEEDS_OWNER_CONTRACT** — se o portal suporta mover indicador, falta rota; não inventar |

**Body I1** (`CreateDepartmentIndicatorBodySchema`): `indicator_id`, `indicator_name`, `weight_pct`, `scope_type`, `performance_direction` (default `higher_is_better`), `strategic_description`, `source_key`, `value_unit`, `value_prefix`, `value_suffix`, `value_decimals` (0–6), `display_order`.
**Body I2** (`UpdateDepartmentIndicatorBodySchema`): idem + `new_indicator_id`, `is_active`.
**Permission:** `settings.manage`. **OCC/erros/idempotência/postcondition:** análogo a departments; read-back via `list_si_admin_department_indicators`.
**Validação BFF-side:** `value_decimals` bounds, `performance_direction` enum e `scope_type` permitidos devem ser espelhados só como fail-fast — owner valida de verdade.

## 4. Operações inventariadas — Settings (`/settings`)

| # | Capability proposta | Owner route | Tipo | Classe |
|---|---|---|---|---|
| S1 | `si.settings.update` | `PUT /settings` | direct mutation (full-replace de `parameters.items` + `governance.items`) | RESOLVIDO §9 → `S1_IMPLEMENTED` |
| — | weights/goals por seção | **não editáveis** via `/settings` — pesos vivem em D2/I2; metas em W012 `si.goal.*` | — | coberto por outros contratos |

**Body S1** (`UpdateStrategicIndicatorsSettingsBodySchema`): `parameters.items[] {key,label,value}` + `governance.items[] {key,label,value,observation}` — replace total, não merge parcial.
**Side effects:** invalida cache de leitura; afeta cálculo IGD/trends em snapshots futuros; cada update gera evento em `settings_audit` (read-back via `list_si_settings_audit`).
**Riscos classificados:** full-replace significa que PREPARE deve capturar o estado completo atual e produzir DIFF exato (itens adicionados/removidos/alterados) — omissão de item = remoção. Por isso NEEDS_SECURITY_DECISION: exige política de "complete-state proposal" no PREPARE.
**Postcondition:** read-back `GET /settings` + auditoria `settings_audit`.

## 5. Operações inventariadas — Change requests (`/change-requests`)

| # | Capability proposta | Owner route | Tipo | Classe |
|---|---|---|---|---|
| C1 | `si.change_request.create` | `POST /change-requests` | proposal workflow (não muta estado efetivo) | READY_FOR_IMPLEMENTATION |
| C2 | `si.change_request.comment` | `POST /change-requests/{id}/comments` | workflow comment | READY_FOR_IMPLEMENTATION |
| C3 | `si.change_request.submit` | `POST /change-requests/{id}/submit` | state transition `→ submitted` (registro governance, sem auto-apply) | READY_FOR_IMPLEMENTATION |
| — | approve / reject / cancel / update / apply | **não existem** no owner | — | **NEEDS_OWNER_CONTRACT** — portal não expõe; submitted é estado final registrado |

**Body C1** (`CreateChangeRequestBody`): `title`, `description`, `target_block` ∈ `{departments, department_indicators, indicator_goals, parameters.global, governance.notes}`, `proposed_payload` (dict livre — bounded size aplicável).
**Body C2:** `comment_text`.
**Semântica:** CR é canal de proposta governada do próprio SI — não executa mutação; `submit` apenas marca `status='submitted'` com `submitted_by`. Aplicar o payload proposto é ato humano fora da API (ou via as capabilities diretas D*/I*/S1 acima).
**Nota de paridade:** como CR não aplica mudança, o fluxo DAVI pode expor C1–C3 sem OCC/pós-condição de estado efetivo — pós-condição é o read-back do CR (`list_si_change_requests`).

## 6. Fora do escopo W013-ACT (inventariado para fronteira de wave)

| Família | Owner routes | Wave destino |
|---|---|---|
| Goals unitários | `POST/PUT /indicator-goals*`, `activate`, `deactivate` | **JÁ IMPLEMENTADO — W012** (`si.goal.create/update/activate/deactivate`, OCC via `expected_max_version`/`expected_row_xmin`) |
| Goal delete | `DELETE /indicator-goals/{id}` | W015 |
| Batch goals | `bulk-create`, `duplicate-year`, `fill-missing` | W014 (mass write → política de risco dedicada; `overwrite_existing`) |
| Config export/import | `GET /admin/config/export` (READ já em W013), `import/preview`, `import/apply`, `import` | W014 (replace mode é destrutivo parcial — PREPARE+preview obrigatórios) |
| Cache | `POST /cache/invalidate`, `POST /cache/refresh` (`view`) | W014 (operacional, side-effect leve) |
| Tree load job | `POST /departments/tree/load-job` (`view`) | W014 (async job dispatch; read-back via `get_si_job_status`) |

## 7. Matriz de decisão consolidada

| Classe | Operações |
|---|---|
| READY_FOR_IMPLEMENTATION (contrato completo no owner) | D1, D2, D3, I1, I2, I3, I4, C1, C2, C3 |
| IMPLEMENTED (§9) | D4 `si.department.deactivate` + S1 `si.settings.update` (owner OCC corrigido; 16 capabilities governadas no total) |
| NEEDS_OWNER_CONTRACT | indicator re-association; CR approve/reject/cancel/update |
| BLOCKED (outra wave) | D5, I5 (W015); `mode=replace` destrutivo do import (W015); `si.config.import` genérico (sem capability) — batch/import-merge/jobs/cache (W014) implementados, ver §10 |

## 8. Próximo briefing de implementação (proposta para Coordination)

`TASK_ID sugerido: DAVI-SI-W013-ACT-IMPLEMENTATION-01`
`MODE: GOVERNED_WRITE_IMPLEMENTATION / CONTRACT_REVIEW_REQUIRED`

1. Implementar primeiro lote READY: departments (D1–D3) + indicators (I1–I4) + change requests (C1–C3), reusando o orchestrator/proposal-store W012 sem duplicar governed-write infra.
2. Resolver decisões de segurança antes de liberar: S1 (política complete-state) e D4 (aviso de impacto no DIFF).
3. Abrir pedido de contrato ao owner para: re-associação de indicador e transições CR (se o portal as exigir).
4. Golden scenarios: create→update→activate→deactivate ciclo completo; rename de PK; race concorrente; token revogado; usuário sem `settings.manage`; CR create→comment→submit; diff fidelity em settings.
5. Proibições herdadas: sem delete, sem batch/import, sem service token, sem auto_act, sem tool por endpoint.

## 9. Decisões de segurança — D4 e S1 (aceite W013-ACT, wave closure)

Investigação executada em `DAVI-SI-W013-ACT-ACCEPTANCE-AND-SECURITY-CLOSURE-01` sobre o código owner real (routes → use case → repo).

### D4 — `si.department.deactivate` → `D4_APPROVABLE`

| Dimensão | Evidência (CONFIRMADO_NO_CODIGO) |
|---|---|
| Owner route | `POST /admin/departments/{id}/deactivate` com `@require_permission("strategic-indicators.settings.manage")` |
| Efeito exato | `_set_department_active` executa `UPDATE departments SET is_active=FALSE ... AND xmin = %s` — **flag-only, sem cascata**; OCC via `expected_xmin` no predicado do UPDATE (sem FOR UPDATE neste path; FOR UPDATE existe no path de update/rename) |
| Dependentes | Indicadores e metas do departamento **não** são alterados na tabela (cada um tem `is_active` próprio); efeito indireto é exclusão dos agregados ativos (árvore/IGD/dashboard) via flag do pai |
| Reversibilidade | `si.department.activate` já é capability aprovada (D3) — reversão simétrica |
| Audit/OCC | Mesmo caminho transacional de D3: `settings_audit` na mesma UoW |
| Contrato PREPARE | Deve enumerar no impact: indicadores ativos do departamento e metas vigentes afetadas (reads já existentes: `list_si_admin_indicators` + `list_si_indicator_goals`) |
| Risco residual | Dashboards/IGD recomputam sem o departamento — efeito de apresentação/cálculo reversível, não destrutivo |

Decisão original: **`D4_APPROVABLE`** — contrato owner completo e paridade total com o portal.

**Resolução (`DAVI-SI-W013-ACT-D4-S1-COMPLETION-01`): `D4_IMPLEMENTED`.** Coordination aprovou a implementação. PREPARE lista indicadores ativos + metas vigentes + impacto persistido-vs-indireto (árvore/IGD/dashboard) + reversibilidade via D3; ACT envia `expected_xmin`, consome proposta única e verifica read-back `is_active=false`. Sem cascata em flags de indicadores/metas.

### S1 — `si.settings.update` → `S1_CONTRACT_GAP`

| Dimensão | Evidência |
|---|---|
| Owner route | `PUT /settings` (prefixo `/strategic-indicators`) com `settings.manage` |
| Semântica | **Full-replace** de `parameters.global` + `governance.notes` (jsonb overwrite por `setting_key`) + atualização de weights/goals de departamentos |
| Transação/audit | Atomicidade existe: tudo em `with self.db()` + `settings_audit` por setting_key |
| Lacuna crítica | **Sem OCC**: `module_settings` não expõe `xmin` nem versão; update é `WHERE setting_key=%s` sem precondition — check→write race para dois administradores (portal + DAVI) |
| Semântica de omissão | Item ausente no payload = removido da lista persistida (full-replace) — PREPARE deve obrigatoriamente computar remoções implícitas |

Decisão original: **`S1_CONTRACT_GAP`** — bloqueado até o owner ganhar precondition atômica.

**Resolução (`DAVI-SI-W013-ACT-D4-S1-COMPLETION-01`): `S1_IMPLEMENTED`.** Coordination autorizou a correção owner. Executado:

1. `GET /settings` expõe `meta.versions` = `{setting_key: xmin::text}` lido na mesma query do estado.
2. `update_settings` exige `expected_versions`; UPDATE atômico `WHERE setting_key=%s AND xmin::text=%s ... RETURNING` por setting_key dentro da UoW; conflito tipado `StrategicIndicatorsAdminConflictError` → 409; versão parcial/ausente rejeitada para o conjunto tocado.
3. `PUT /settings` exige query params `expected_parameters_xmin` + `expected_governance_xmin` (422 sem eles) e o repo rejeita `expected_versions` vazio — não existe caminho de escrita sem precondition.
4. **Drift owner corrigido:** o repo exigia kwargs `weights`/`goals` que port/use case não passavam — `PUT /settings` falhava com TypeError (500) em produção. `weights`/`goals` agora opcionais; o bloco legado executa somente quando enviado.
5. Portal compatibilizado: MFE lê `meta.versions` e envia os dois xmin no save — o guard OCC vale para portal e DAVI.
6. Capability `si.settings.update`: complete-state proposal — PREPARE lê estado completo, diffs por `key` (preserved/modified/added/removed + remoções implícitas), versões seladas; ACT full-replace com versões; read-back compara blocos persistidos com o proposto.

## 10. Atualização de wave — W014 implementada (bulk goals, import merge, cache, jobs)

**`DAVI-SI-W014-BULK-IMPORT-JOBS-IMPLEMENTATION-01`:** as quatro famílias mapeadas na §6 foram implementadas sob o mesmo contrato governado PREPARE→ACT. O conjunto executável passou de 16 → **23 capabilities**; nenhuma tool MCP nova (5 estáveis).

| Capability | Owner route | Controles aplicados |
|---|---|---|
| `si.goal.bulk_create` | `POST /admin/indicator-goals/bulk-create` | tx única p/ o lote (UoW re-entrante); `expected_max_version` por escopo (schema passou a aceitar — antes strippado); cap 500 itens; audit `indicator_goal.created` na mesma tx; superseded em `_audit_meta` |
| `si.goal.duplicate_year` | `POST /admin/indicator-goals/duplicate-year` | locks advisory sorted + re-read pós-lock; `expected_source_digest`/`expected_existing_digest` conferidos SOB LOCK → 409; audit mesma tx |
| `si.goal.fill_missing` | `POST /admin/indicator-goals/fill-missing` | locks por indicador; `expected_target_digest`/`expected_source_digest` sob lock → 409; audit mesma tx |
| `si.config.import_apply` | `POST /admin/config/import/apply` | **merge only** — `mode=replace` rejeitado no BFF (W015); `expected_counts` (departments/department_indicators/indicator_goals) conferidos DENTRO da tx de mutação → 409; `config.imported` audit na mesma tx (era pós-commit) |
| `si.cache.refresh` | `POST /cache/refresh` (`view`) | single-flight owner (`already_running` não é falha); fingerprint sobre status do refresh |
| `si.cache.invalidate` | `POST /cache/invalidate` (`settings.manage`) | zero-args; wipe snapshots + schedule refresh (semântica owner inalterada) |
| `si.job.tree_load` | `POST /departments/tree/load-job` (`view`) | `created_by_user_id` bound; `get` actor-scoped fail-closed (cross-actor/anon → 404); admission caps 2/ator + 8 global → 429; worker interno usa lookup sem scoping (OC-1 do verificador corrigida) |

Permanecem BLOCKED: `si.config.import` (nome genérico — sem capability), `mode=replace` destrutivo (W015), todos os deletes (W015), `http.post`/SQL genérico. Rotas W014 validam `write_origin`/`correlation_id` via `_validate_audit_meta` (allowlist `davi-mcp`); `except HTTPException: raise` adicionado nas rotas W014 **e** W012/W013 (write_origin inválido era 500 — agora 400).
