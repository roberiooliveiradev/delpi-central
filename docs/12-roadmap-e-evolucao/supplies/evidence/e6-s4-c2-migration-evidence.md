# E6.S4 — Evidência para migração C2 (purchase_requests → supplies-api)

> **Status:** coletada em código (set/2026) · volumes de produção ainda `HIPOTESE_A_VALIDAR` até dump/medição em ambiente  
> **ADR:** [ADR-002](../adr/ADR-002-purchase-requests-api.md)  
> **Não autoriza C2:** esta evidência informa a janela; cutover continua em E16.

## 1. Owner atual do estado Delpi (CONFIRMADO_NO_CODIGO)

| Artefato | Local |
|---|---|
| Schema | `purchase_requests` (migrations V001–V004 em `purchase-requests-api/migrations/`) |
| Jobs | `purchase_order_linked_notification_job.py`, `purchase_receipt_recorded_notification_job.py` |
| Cursors | `purchase_requests.notification_cursors` + `dispatched_purchase_order_events` (V003) / receipt (V004) |
| Subscriptions | `purchase_requests.user_notification_subscriptions` (V002) |
| Escopo CC | `visibility_scopes*` (V001) |
| Mapping Protheus | tabelas de mapping em V001 |

SQL TOTVS (SC1/SC7/SD1) permanece na **api-delpi** — C2 não move TOTVS.

## 2. Tabelas a medir antes de C2

Rodar em Postgres do ambiente alvo (somente leitura):

```sql
SELECT schemaname, relname, n_live_tup
FROM pg_stat_user_tables
WHERE schemaname = 'purchase_requests'
ORDER BY n_live_tup DESC;

SELECT COUNT(*) AS visibility_scopes FROM purchase_requests.visibility_scopes;
SELECT COUNT(*) AS visibility_scope_users FROM purchase_requests.visibility_scope_users;
SELECT COUNT(*) AS visibility_scope_cost_centers FROM purchase_requests.visibility_scope_cost_centers;
SELECT COUNT(*) AS user_protheus_mappings FROM purchase_requests.user_protheus_mappings;
SELECT COUNT(*) AS notification_subscriptions FROM purchase_requests.user_notification_subscriptions;
SELECT COUNT(*) AS notification_cursors FROM purchase_requests.notification_cursors;
SELECT COUNT(*) AS dispatched_po_events FROM purchase_requests.dispatched_purchase_order_events;
```

Preencher:

| Métrica | Dev/local | Homolog | Produção |
|---|---|---|---|
| `n_live_tup` por tabela | TBD | TBD | TBD |
| subscriptions ativas | TBD | TBD | TBD |
| cursors PO / receipt | TBD | TBD | TBD |

## 3. Writers / jobs (único writer na C2)

| Writer | Tipo | Risco se dual-write |
|---|---|---|
| VisibilityScope admin HTTP | sync write | inconsistência de CC |
| UserProtheusMapping admin HTTP | sync write | mapping fantasma |
| NotificationSubscription admin HTTP | sync write | preferências divergentes |
| PO linked notification job | async + cursor | notificação duplicada / buraco |
| Receipt recorded notification job | async + cursor | idem |

**Estratégia travada (ADR-002):** um único writer no schema. Desligar jobs/gravações da `purchase-requests-api` **antes** de ligar os da `supplies-api`. Sem dual-write longo.

## 4. Reconciliação proposta (C2)

```text
1. Congelar writes na purchase-requests-api (admin + jobs)
2. Contagens pré-cutover (queries §2) → snapshot A
3. Transferir ownership do schema / redeploy supplies-api com jobs
4. Contagens pós → snapshot B
5. Diff A×B em rows + últimos cursors + sample de subscriptions por user_id
6. Smoke fail-closed CC + list/detail/export no Portal
7. Só então avançar E19 C3 (ocultar MFE legado)
```

Tolerância sugerida: 0 linhas perdidas em scopes/mappings/subscriptions; cursors iguais ou avançados monotonicamente.

## 5. Dependências que NÃO bloqueiam C1 (já entregue em E6)

- BFF gateway `/purchase-requests*` na supplies-api
- UI Portal lista/detalhe/export
- MFE legado permanece em coexistência até C3

## 6. Próximo gate

Medir §2 em homolog/prod e registrar números neste arquivo antes de abrir E16 (C2).
