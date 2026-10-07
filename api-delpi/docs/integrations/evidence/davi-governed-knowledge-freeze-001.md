# DAVI Governed Knowledge — First Corpus Freeze

**taskId:** `DAVI-GOVERNED-KNOWLEDGE-FREEZE-PERSIST-001`
**status:** `FROZEN_CONTENT_GOVERNANCE`
**inventoryTaskId:** `DAVI-GOVERNED-KNOWLEDGE-FREEZE-001`
**auditTaskId:** `DAVI-GOVERNED-KNOWLEDGE-MINIMIZATION-AUDIT-001`
**evidenceHead:** `34244d81b7c381798247644299ec04f239492555`
**reviewedMainAtDecision:** `45c1d05df6f28fc5e4dd76f5e384bccc797fa798`
**persistedAt:** `c0cc026a70c5b7343206f86a18f20039ced811e8` (origin/main)
**correctiveTaskId:** `DAVI-GOVERNED-KNOWLEDGE-FREEZE-DRIFT-CORRECTIVE-001`
**correction:** document #1 (`supplies-inventory-adjustments.md`) was
revalidated after the CF direction fix (proven `DE0`=surplus/entrada,
`RE0`=shortage/saída against the Protheus movements report) and the
knowledge-minimization corrective: the frozen regression table and
per-record audit values were removed — they are regression/audit
evidence, not runtime knowledge — while canonical semantics, formulas,
fail-closed provenance, owners and AuthZ remain. Result:
`SAFE_AS_WHOLE_DOCUMENT`.

## Authority boundary

```text
KNOWLEDGE DOCUMENT != SOURCE OF TRUTH
```

Knowledge may explain: domain semantics, formulas, provenance rules,
capability contracts, limits, ownership/status.

Current operational data must come from:

```text
governed live capability → backend AuthZ → authoritative source
```

Documentation explains authoritative sources; it never becomes one.

## GENERIC_SQL_FORBIDDEN

Knowledge about Protheus tables/fields does not authorize arbitrary row
access, `POST /data/sql`, generic SELECT, table dumps, or SQL fallback when
a governed capability is missing. System Metadata discovery explains what
tables/fields represent; it never grants row access.

## Business-owner policy

Technical ownership (`api-delpi` module/bounded context) is proven for all
corpus domains. Organizational/business ownership is **not** inferred from
module naming. Where not formally ratified:

```text
BUSINESS_OWNER = TO_INVENTORY
```

## Runtime status

```text
CONTENT FREEZE               = YES
RUNTIME INGESTION            = NOT AUTHORIZED
RAG DESIGN                   = NOT AUTHORIZED
VECTOR DB                    = NOT SELECTED
EMBEDDING MODEL              = NOT SELECTED
OPENAI FILE UPLOAD           = NOT AUTHORIZED
MCP KNOWLEDGE RESOURCE       = NOT AUTHORIZED
AGENT STUDIO KNOWLEDGE       = NOT AUTHORIZED
DEPLOYMENT                   = NOT AUTHORIZED
```

This freeze is a content-governance decision only. It does not change the
DAVI operation surface, allowlist, Agent Intelligence, MCP, or GPT Actions.

## Status model

```text
FROZEN_FIRST_CORPUS    = in corpus V1, whole document, no edit required
SAFE_LATER             = SAFE_AS_WHOLE_DOCUMENT, not selected for V1
SECONDARY_REFERENCE    = safe doc excluded from V1 by canonical duplication
SPLIT_REQUIRED         = valuable semantics mixed with non-knowledge sections
MINIMIZATION_REQUIRED  = suitable scope; examples/details must be synthesized
DEFER                  = unresolved currentness/authority/quality question
EVIDENCE_ONLY          = verification material, not runtime knowledge
GOVERNANCE_ONLY        = architecture/ops material, not user-facing knowledge
HISTORICAL_ONLY        = dated changelog/incident/reconciliation evidence
```

## FROZEN_FIRST_CORPUS — 15 documents

| # | Path | Domain |
|---|------|--------|
| 1 | `api-delpi/docs/api/supplies-inventory-adjustments.md` | supplies / inventory adjustments (RE0/DE0, SB7 fail-closed) |
| 2 | `api-delpi/docs/api/supplies-stock-balances.md` | supplies / stock balances by warehouse |
| 3 | `api-delpi/docs/api/supplies-purchase-order-otd.md` | supplies / purchase OTD |
| 4 | `api-delpi/docs/api/comercial-sales-order-otd.md` | commercial / sales-order OTD |
| 5 | `api-delpi/docs/api/padroes-totvs/armazem-custo.md` | warehouse × cost model |
| 6 | `api-delpi/docs/api/padroes-totvs/filiais.md` | branch semantics + per-filial AuthZ |
| 7 | `api-delpi/docs/api/padroes-totvs/unidades-medida.md` | unit conversion (MI/PC/MT) |
| 8 | `api-delpi/docs/api/padroes-totvs/producao-entrada-estoque.md` | produced-qty → stock-entry reconciliation |
| 9 | `api-delpi/docs/api/padroes-totvs/apontamento-operacao-hza.md` | HZA010 "in production" semantics |
| 10 | `api-delpi/docs/api/padroes-totvs/cadastro-produto.md` | product master (SB1) semantics |
| 11 | `api-delpi/docs/api/padroes-totvs/ordem-producao-chave.md` | OP/set key format |
| 12 | `api-delpi/docs/api/padroes-totvs/materiais-terceiros-sb6.md` | third-party materials (SB6) |
| 13 | `api-delpi/docs/api/padroes-totvs/carteira-semanal-previsto-realizado.md` | forecast × realized vocabulary (canonical) |
| 14 | `api-delpi/docs/api/padroes-totvs/rol-mercado-cfop.md` | ROL market/CFOP semantics |
| 15 | `api-delpi/docs/api/production-machine-load.md` | SH8/HZA machine-load semantics |

## SECONDARY_REFERENCE — not in corpus

| Path | Status | Reason |
|------|--------|--------|
| `api-delpi/docs/api/commercial-billing-portfolio.md` | SAFE_AS_WHOLE_DOCUMENT / SECONDARY_REFERENCE / NOT_FIRST_CORPUS | semantic overlap with canonical `padroes-totvs/carteira-semanal-previsto-realizado.md`; minimum sufficient context selects the pattern doc for V1 |

## Source audits (conclusions)

`DAVI-GOVERNED-KNOWLEDGE-FREEZE-001` (CURRENT DAVI-RELEVANT API-DELPI
KNOWLEDGE INVENTORY): 92 documents reviewed → 50 APPROVE_CANDIDATE,
5 DEFER, 11 EVIDENCE_ONLY, 22 GOVERNANCE_ONLY, 4 HISTORICAL_ONLY.

`DAVI-GOVERNED-KNOWLEDGE-MINIMIZATION-AUDIT-001` (whole-document audit of
the 50): **25** SAFE_AS_WHOLE_DOCUMENT, **8** SPLIT_REQUIRED,
**17** MINIMIZATION_REQUIRED, **0** DEFER.

Architecture selected **15** of the 25 SAFE documents for corpus V1.
Of the remaining 10 SAFE documents, 9 are `SAFE_LATER` (eligible, not
selected) and 1 (`commercial-billing-portfolio.md`) is `SECONDARY_REFERENCE`:

```text
SAFE_LATER:
api-delpi/docs/api/production-pcp-orders.md
api-delpi/docs/api/production-shared-structure-intermediates.md
api-delpi/docs/api/production-unproductive-hours.md
api-delpi/docs/api/process-inspection-plans.md
api-delpi/docs/api/13-producao-operacional.md
api-delpi/docs/api/regras-faixa-eficiencia-producao.md
api-delpi/docs/api/padroes-totvs/pedido-venda-criador.md
api-delpi/docs/api/padroes-totvs/pedido-venda-postergacao.md
api-delpi/docs/api/padroes-totvs/transportadora.md
```

## Non-first-corpus backlog (governance status only — no edits here)

Examples:

- `estoque-seguranca.md` → SPLIT_REQUIRED
- `financeiro-inadimplencia.md` → MINIMIZATION_REQUIRED
- `padroes-totvs/cadastro-cliente.md` → MINIMIZATION_REQUIRED
- `padroes-totvs/playbooks/playbook-analise-preco-materia-prima.md` → SPLIT_REQUIRED

Full correction work is a later authorized task. Sensitive values observed
during the audit are intentionally not reproduced in this artifact.

## DAVI runtime context (evidence, unchanged by this freeze)

```text
allowlist            = v19 (davi_external_read_allowlist.json)
governed READ ops    = 89
Agent Intelligence   = 2026.10.07.2
MCP tools            = 2 (discover_delpi_information, execute_delpi_information)
```

Contextual evidence only — the knowledge freeze does not authorize or
alter the operation surface.

## Related

- [DAVI integration baseline](../openai-workspace-agent-davi.md)
- [DAVI read AuthZ policy](./davi-read-authz-policy-rebaseline-001.md)
