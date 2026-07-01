# Playbook — Revisões versionadas de planos PAC (jun/2026)

## Objetivo

Permitir **reverter alterações** em planos de ação (`quality_action_plans`) sem apagar o histórico linear: cada gravação relevante gera uma **revisão** (snapshot JSON); **restaurar** aplica um snapshot antigo e cria uma **nova** revisão (`change_scope: restore`).

Alinha-se ao padrão documentado para Kaizen (`ESPECIFICACAO-REVISOES.md`) e complementa (não substitui) `quality_action_history` + `quality_audit_log`.

## Princípios

| Princípio | Decisão |
|-----------|---------|
| Fonte de verdade do estado corrente | Tabelas transacionais existentes (`quality_action_plans`, `quality_actions`, …) |
| Fonte de verdade das versões | `quality.quality_action_plan_revisions` (append-only) |
| Restore | Novo snapshot — **não** apaga revisões posteriores |
| Evidências (arquivos) | Snapshot guarda **metadados**; blobs permanecem no volume; restore não apaga anexos novos |
| Histórico / auditoria | Mantidos; evento `plan_revision_restored` no histórico |
| Módulo canônico | `PacPlanRevisionSnapshotService` + métodos no `PostgresQualityActionPlanRepository` |

## Modelo de dados (V027)

```sql
quality.quality_action_plan_revisions
  plan_id, revision_number (1..N, UNIQUE por plano)
  snapshot_schema_version (default 1)
  snapshot JSONB
  change_scope, change_summary
  restored_from_revision (nullable)
  created_by, created_by_name, created_by_email, created_at

quality.quality_action_plans.current_revision_number
```

### `change_scope` (v1)

| Scope | Quando gravar |
|-------|----------------|
| `created` | Após `create_plan` |
| `identification` | `PATCH` identificação |
| `status` | `PATCH` status / reabertura |
| `ishikawa` | `PUT` Ishikawa |
| `five_whys` | `PUT` 5 Porquês |
| `rnc_8d` | `PUT` relatório 8D |
| `actions` | Criar/atualizar/remover ações (fase 1b) |
| `effectiveness` | Fluxos de eficácia (fase 1b) |
| `restore` | `POST .../revisions/{n}/restore` |

### Formato `snapshot` (schema_version 1)

```json
{
  "schema_version": 1,
  "plan": { },
  "ishikawa": null,
  "five_whys": null,
  "actions": [],
  "team_members": [],
  "evidences": []
}
```

- `plan`: cabeçalho sem campos derivados (`contact_roles`, `was_ever_completed`, SLA).
- `evidences`: só `id`, `type`, `section`, `description`, `knowledge_visible`, `action_id`, `file_name` (sem binário).

## API (api-delpi)

| Método | Rota | `operationId` |
|--------|------|----------------|
| GET | `/quality/action-plans/{plan_id}/revisions` | `list_quality_action_plan_revisions` |
| GET | `/quality/action-plans/{plan_id}/revisions/{revision_number}` | `get_quality_action_plan_revision` |
| POST | `/quality/action-plans/{plan_id}/revisions/{revision_number}/restore` | `restore_quality_action_plan_revision` |

**Delegação:** api-pac-quality repassa com `X-Delpi-Actor-*` (mesmo padrão das demais rotas PAC).

## Pipeline de gravação

```
Mutação existente (update_plan, upsert_ishikawa, …)
  → SQL da mutação (auto_commit=False)
  → record_plan_revision(scope, summary, actor)
  → prune revisões além de PAC_PLAN_REVISION_RETENTION_LIMIT (50)
  → history/audit existentes
  → commit
```

## Pipeline de restore

```
POST restore(revision_number)
  → validar plano ativo (não deleted_at)
  → carregar snapshot da revisão N
  → apply_plan_snapshot (SQL transacional, sem history por sub-operação)
  → record_plan_revision(scope=restore, restored_from=N)
  → append_history(plan_revision_restored)
  → commit
  → retornar get_plan_detail
```

## Governança (fases)

| Fase | Regra |
|------|--------|
| **1 (atual)** | Restore permitido se plano não excluído (`deleted_at IS NULL`) |
| **2** | Bloquear restore se `was_ever_completed` ou eficácia aprovada (alinhar à política de exclusão) | ✅ |
| **2** | `expected_revision_number` opcional nas escritas (concorrência otimista, padrão Auditoria 5S) | ✅ |
| **3** | Diff por seção na UI; retenção (ex.: últimas 50 revisões) | ✅ |

## Frontend (`quality-action-plans`)

| Fase | Entrega |
|------|---------|
| **1b** | Aba/lista de revisões + botão Restaurar + confirmação | ✅ |
| **2** | Comparar revisão vs. atual (campos principais + diff expandível) | ✅ |
| **2** | Enviar `expected_revision_number` em todas as gravações do detalhe do plano | ✅ |
| **3** | Diff por seção (identificação, Ishikawa, 5 Porquês, ações, equipe, evidências, eficácia) | ✅ |
| **3** | Retenção automática das últimas 50 revisões por plano | ✅ |

## Testes obrigatórios

- `test_pac_plan_revision_snapshot_service.py` — build/validate snapshot
- `test_quality_action_plan_revision_repository.py` — record + restore (mock SQL)
- `test_pac_plan_revision_lock_service.py` — assert de revisão esperada (409)
- `test_pac_plan_revision_retention.py` — retenção + record/restore (mock SQL)
- Regressão: gravação gera `revision_number` incrementado

## Referências

- `api-delpi/docs/api/quality-action-plans-pac.md`
- `quality_action_history` / soft delete (V020)
- Auditoria 5S — `expected_version` em respostas de critério

## Status da implementação (jun/2026)

| Item | Status |
|------|--------|
| Playbook | ✅ |
| Migration `V027__pac_plan_revisions.sql` | ✅ (aplicar no ambiente) |
| `PacPlanRevisionSnapshotService` | ✅ |
| `QualityActionPlanRevisionMixin` (record/list/get/restore) | ✅ |
| Hooks em todas as escritas principais | ✅ |
| Rotas HTTP + `route_contract_registry` | ✅ |
| Proxy api-pac-quality (plugin-only) | ✅ |
| Use cases + composer | ✅ |
| Testes snapshot + smoke rotas | ✅ snapshot; smoke requer `delpi_auth` no ambiente |
| Frontend lista + restore | ✅ fase 1b |
| Governança `was_ever_completed` no restore | ✅ fase 2 |
| `current_revision_number` no detalhe do plano | ✅ |
| `expected_revision_number` nas escritas (API + plugin) | ✅ fase 2 |
| Testes lock otimista | ✅ |
| Diff por seção na UI | ✅ fase 3 |
| Retenção (50 revisões/plano) | ✅ fase 3 |
