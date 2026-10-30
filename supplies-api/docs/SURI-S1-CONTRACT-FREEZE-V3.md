# SURI — Semantic Contract Freeze (rev.3)

> **Status:** FROZEN — executado em `SURI-MCP-SUPPLIERS-WRITE-001`.
> **Substitui:** rev.2 (`SURI-S1-CONTRACT-FREEZE-V2.md`, superfície de 4
> tools), que permanece como registro histórico. A evolução é **aditiva**:
> as 4 tools e seus schemas permanecem inalterados; `execute` é a quinta.
> **Evidência S0:** gates TOTVS + cadeia REST provados em runtime produtivo
> em 2026-10-30 (ver `SURI-MCP-FULL-PARITY-MATRIX.md` §Reconciliação).

## 1. Superfície pública — exatamente 5 tools

| Tool | Classe | Discriminador | Capacidades rev.3 |
|---|---|---|---|
| `get_context` | DISCOVERY | `action` | `context`, `catalog` |
| `read` | READ | `entity` + `action` | `purchase_orders`: `search`, `get` |
| `analyze` | ANALYSIS | `analysis` | `purchase_orders_summary` |
| `knowledge` | READ | `action` | `search`, `get`, `sources` |
| `execute` | ACT | `entity` + `action` | `suppliers`: `create`, `update` |

`delete` permanece família TARGET documentada — nunca registrada até
existir contrato + autorização + canal de confirmação explícita.

Annotations do wire: `execute` publica `readOnlyHint=false`,
`destructiveHint=false`, `idempotentHint=true` — hints descrevem
semântica, nunca autorizam.

## 2. `execute` — contrato por ação

```text
execute(entity="suppliers", action="create"|"update", operations=[1..10])
```

Cada item de `operations` é um `SupplierWriteOperation` fechado
(`extra="forbid"` — wire `additionalProperties: false` + validação em
profundidade no dispatcher):

| Chave | create | update |
|---|---|---|
| `idempotency_key` | opcional (1–128) | opcional (1–128) |
| `supplier` | **obrigatório** — payload cadastral na allowlist canônica `POST_SUPPLIER_FIELDS` | proibido |
| `supplier_code` + `supplier_store` | proibidos | **obrigatórios** — identidade inequívoca (6+2 dígitos normalizados) |
| `fields` | proibido | **obrigatório** — allowlist `PUT_SUPPLIER_FIELDS`; `tax_id`/`supplier_code`/`supplier_store`/`codusr`/`*_id` rejeitados |

Preservações do contrato Portal (fonte única em `suppliers_dto` +
use cases api-delpi — o MCP não redefine regras):

- normalização de CNPJ/CPF e demais campos cadastrais (upstream);
- verificação de duplicidade — pré-checagem por `tax_id` via leitura
  governada (`/supplies/suppliers?query=`), igual à UX do Portal;
- escopo de permissão: `can_use_operations` (`supplies.access`) — a mesma
  policy das rotas `POST/PUT /suppliers`, re-derivada por chamada;
- erros TOTVS/api-delpi mapeados por `classify_supplier_write_error`
  (fonte única compartilhada BFF↔MCP): `write_disabled` (gate 503),
  `rejected` (4xx/validação/denial), `indeterminate` (transporte/5xx);
- rastreabilidade: `operation_id` do tracker api-delpi +
  `correlation_id` propagado via `X-Correlation-ID`;
- read-back honesto: `creation_confirmed`/`persistence_proven`
  propagados verbatim — ACK nunca é apresentado como persistência.

## 3. Semântica de execução

- **Direct path**: solicitação clara, inequívoca e autorizada executa sem
  confirmação conversacional adicional (contrato da missão). O Portal
  não exige aprovação formal para estas writes — nenhum bypass é criado.
- **Batch**: operações sequenciais, resultado individual por operação,
  sem transação presumida. Falha de uma não impede as demais; o `summary`
  agrega por outcome.
- **Idempotência**: `idempotency_key` por operação. Claim durável e
  atômico em `supplies.suri_execute_operations` (V005 — UNIQUE
  actor+entity+action+key + payload_hash + resultado sanitizado,
  retenção 24h): primeira claim vence; replay retorna
  `outcome=replayed` + `replayed_outcome` sem reexecutar; mesma chave
  com payload divergente → `idempotency_conflict` (409); chave ainda em
  voo ou não resolvida → `in_progress` (nunca reexecuta); store
  indisponível → `idempotency_store_unavailable` fail-closed (503,
  nenhuma escrita emitida). O registro de escrita durável continua sendo
  o integration tracker da api-delpi.
- **Retry**: nenhuma escrita é repetida implicitamente — nem pelo MCP,
  nem pelo gateway (contrato "no blind write retries"). `indeterminate`
  exige verificação via `operation_id` antes de nova tentativa.
- **Auditoria**: uma linha estruturada por operação (`suri_execute`) com
  ator, correlação, ação, identidade normalizada, **nomes** de campos
  (nunca valores — LGPD), outcome, `operation_id` e http_status.

## 4. Registry semântico

`constants.EXECUTE_ACTIONS_BY_ENTITY = {"suppliers": {"create","update"}}`
é a única fonte do dispatch; não há executor genérico, URL, SQL, método
HTTP ou handler arbitrário. Adicionar capability = contrato + owner
AuthZ + handler + testes.

FUTURE (não executável): demais entidades `read`; demais `execute`
(plugin-db/comex/enrichment/preferences — lotes P2-E1..E4); `delete`.

## 5. AuthZ e erros — inalterados

Cadeia rev.2 preservada: transporte (JWT + aud exata + `mcp:tools`,
service-token banido) → `_operations_user` (`can_use_operations`) →
handler. 401 → `mcp/www_authenticate` meta; 403 forbidden; 422
validation; 502/503 upstream. `execute` usa `DelpiS2SApiGateway` (mesma
credencial S2S do BFF para suppliers — `X-Delpi-Service-Authorization`),
nunca o token legado compartilhado.

## 6. Versão

`CATALOG_VERSION = 3` (rev.1 = 1, rev.2 = 2). Mudança aditiva e
non-breaking: conectores existentes continuam funcionando; `tools/list`
apenas ganha `execute`.

> **Adendo rev.4 (SURI-MCP-FULL-PARITY-V4-G1):** `CATALOG_VERSION = 4`.
> Extensão aditiva e non-breaking deste freeze: `read` ganha as entidades
> `suppliers` (search, get, catalogs, search_by_tax_id, existing,
> operations, integration_status — manage-only) e `postal_codes`
> (lookup); `analyze` ganha `supplier_creation_preview` (read-only,
> `write_enabled=false`). As cinco tools, classes, envelope e o contrato
> `execute(suppliers, create|update)` permanecem inalterados.
