# DATA-MODEL — supplies-api (estado Minha DELPI)

Princípio: **não persistir cópia de TOTVS**. External keys = códigos Protheus (`branch`, `product_code`, `supplier_code`+`store`, `request_number`, `order_number`).

Schema Postgres proposto: `supplies` em `postgres-plugins`.  
Schema `purchase_requests` **permanece** até C2 (ADR-002); não duplicar as tabelas abaixo.

---

## Hipóteses rejeitadas (não criar)

| Entidade | Motivo |
|----------|--------|
| `totvs_sc1_clone` / snapshot diário de SC | Já há SQL na api-delpi |
| `savings_targets` | Meta = SI |
| `supplier_scorecard_facts` | Calcular no BFF a partir de TOTVS/qualidade até P2 justificar materialização |
| Espelho SA2/SB1 | Cadastro TOTVS |

---

## Entidades justificadas

### 1. `supply_user_preferences`

- **Propósito:** última filial, densidade de tabela, atalhos Home.  
- **Owner:** supplies-api.  
- **Caso de uso:** WF-01 filtro default.  
- **PK:** `user_id` (text Keycloak/sub).  
- **Campos:** `default_branch CHAR(2)`, `locale` default pt-BR, `home_layout_json` (opcional P2), timestamps.  
- **Unique:** PK.  
- **Lifecycle:** upsert. Sem retenção especial.  
- **Justificativa:** estado de UI que o Core não tem por app.

### 2. `supplier_notes`

- **Propósito:** notas internas do comprador no 360.  
- **Caso de uso:** WF-10.  
- **PK:** `id UUID`.  
- **External:** `branch`, `supplier_code`, `store`.  
- **Campos:** `body`, `created_by_user_id`, `updated_by`, timestamps, `deleted_at` (soft).  
- **Index:** `(branch, supplier_code, store, created_at DESC)`.  
- **Auditoria:** created/updated by.  
- **Concorrência:** updated_at optimistic opcional.  
- **Justificativa:** não existe em SA2.

### 3. `supplier_actions` / `purchase_followups`

Unificar em **`supply_tasks`** (uma fila, vários tipos).

- **Propósito:** follow-up de SC/PC/fornecedor/item.  
- **Caso de uso:** WF-03, 360.  
- **PK:** `id UUID`.  
- **Campos:** `task_type` (`follow_up`, `alert_ack`, `note_action`), `status` (`open`,`done`,`canceled`), `due_on`, `assignee_user_id`, `created_by`, `title`, `body`,  
  `ref_kind` (`supplier`,`product`,`purchase_request`,`purchase_order`,`safety_stock_item`),  
  `ref_branch`, `ref_keys_json` (códigos TOTVS, não FKs TOTVS), timestamps.  
- **Index:** `(assignee_user_id, status, due_on)`, `(ref_kind, ref_branch)`.  
- **Justificativa:** worklist P0 precisa de ack/follow-up além do snapshot TOTVS.

### 4. `supply_alert_events` (P1; não P0)

- **Propósito:** materializar alerta gerado por job (OTD drop, SC parada) para não recalcular só no GET da Home.  
- **Justificativa P1:** P0 da Home pode ser composição on-read. Só criar se latência/carga exigir.  
- **HIPOTESE_A_VALIDAR** na E13.S1.

### 5. `portal_settings`

- **Propósito:** flags funcionais do módulo (ex. threshold `due_soon` quando o PO homologar).  
- **PK:** `key TEXT`.  
- **Campos:** `value_json`, `updated_by`, timestamps.  
- **Justificativa:** thresholds hoje em JSON de conteúdo; settings **operados** por admin vão aqui, textos PT continuam em `content/`.

### 6. `audit_logs` (funcional)

- **Propósito:** CUD de notes/tasks/settings.  
- **Não** substitui audit Core de RBAC.  
- Campos: actor, action, entity, entity_id, payload_redacted, at.  
- Retenção: alinhar política da plataforma (não inventar anos).

### 7. `outbox_events`

- **Propósito:** se jobs de notificação SC migrarem na C2.  
- **Não criar na E2.** Herdar padrão purchase-requests na C2.

---

## Schema `purchase_requests` (existente — não redesenhar)

Já justificado pelo contrato Fase 0.2:

- `visibility_scopes`, `_users`, `_cost_centers`
- `user_protheus_mappings`
- subscriptions / cursors PO / receipt events (V002–V004)

**C2:** mudar o **processo dono** (supplies-api) sem rename obrigatório de schema (migrations imutáveis). Novo código lê o mesmo schema.

---

## Idempotência

Jobs de alerta/task: unique `(task_type, ref_kind, ref_keys_hash, open)` para não duplicar follow-up do mesmo PC atrasado.

---

## Anexos

Se tasks ganharem arquivo: volume bind mount (`persistent-upload-storage.mdc`), path EN, nunca disco efêmero do container. **Não** na E2.
