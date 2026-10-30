# SURI-MCP-TOOLS-SEMANTIC-001 — Relatório de execução R0–R5

Refatoração da superfície MCP SURI de 8 tools endpoint-oriented para
4 tools semânticas. Plano: `SURI-MCP-SEMANTIC-TOOLS-REFACTOR-PLAN.md`.
Baseline: `16d18bf17d` (+docs `6f80280ce5`).

## R0 — REBASELINE + INVENTORY — PASS

- HEAD `16d18bf17d` → ff para `6f80280ce5` (plano + links no baseline).
- Consumers da superfície antiga: **nenhum vivo** (Keycloak não
  registrado, ChatGPT não conectado, nenhum MFE/agente consome o MCP) →
  substituição atômica sem aliases autorizada pelo plano §2.
- Corpus (`suri_knowledge.json`) e persona/perfil não referenciam nomes
  de tools.
- Padrão TÉO/VISTA estudado: famílias semânticas com `entity`/`action`
  `Literal` + discriminadores fechados — adotada a abstração, não a
  regra de negócio.

## R1 — SEMANTIC CONTRACT FREEZE — PASS

`docs/SURI-S1-CONTRACT-FREEZE-V2.md`: 4 tools, discriminadores fechados,
paridade 8→4, registry `SEMANTIC_CAPABILITIES`, `CATALOG_VERSION=2`,
AuthZ inalterada, composição stateless. Rev.1 marcada SUPERSEDED.

## R2 — IMPLEMENTATION — PASS

- `constants.py`: `TOOL_CLASS` (4), `CATALOG_VERSION=2`, registry
  (`READ_ENTITIES`, `READ_ACTIONS`, `ANALYSIS_KINDS`,
  `KNOWLEDGE_ACTIONS`, `CONTEXT_ACTIONS`, `PO_*_FILTER_KEYS`,
  `SEMANTIC_CAPABILITIES`).
- `schemas.py` (novo): `PurchaseOrderSearchFilters`,
  `PurchaseOrderAnalyzeFilters`, `PurchaseOrderIdentity` — pydantic
  `extra="forbid"` → `additionalProperties: false` no wire.
- `tool_bridge.py`: dispatchers `tool_get_context`/`tool_read`/
  `tool_analyze`/`tool_knowledge` (enums fechados, combinações inválidas
  → 422), handlers legados preservados como impls privadas,
  `ValidationError`→422, catálogo semântico.
- `server.py`: 4 tools com `Literal` discriminators → `const`/`enum`
  no `inputSchema`.
- `branding.py`: instruções reescritas (4 tools + composição +
  invariants).

## R3 — PARITY + COMPOSITION TESTS — PASS

62 testes `tests/interface/suri_mcp/` verdes + suíte completa
`supplies-api` sem regressão:

- Paridade 8/8: context, catalog, PO search (params/late_only/
  paginação/cap 100), PO get (detail/identity), analyze (FACT/CALC/REC,
  hash reproduzível, vazio, branch), knowledge search/get/sources
  (citações, 404, corpus meta).
- Negativos semânticos: entity/action/analysis desconhecidos, filter
  key desconhecida, identity em search, filters em get, identity
  incompleta/extra, parâmetros errados por knowledge action — todos 422
  e **zero chamada ao gateway**.
- AuthZ: anônimo 401 + challenge, service-principal 403, sem
  `supplies.access` 403, branch fora/vazia 403, upstream 404/5xx.
- Composição: `read → analyze → knowledge` encadeado (2 chamadas BFF +
  1 local, cada uma re-autorizada); falha parcial isolada.
- Wire: `tools/list` = exatamente `['get_context','read','analyze',
  'knowledge']`, classes corretas, `readOnlyHint`, zero ACT/PREPARE.

## R4 — BUILD + SMOKE + DOCS — PASS

- `docker build -f supplies-api/Dockerfile` real: OK.
- Container smoke: `healthz`=200; RFC 9728 metadata 200;
  `POST /mcp` sem bearer → 401 + `WWW-Authenticate` completo;
  `list_tools` dentro do container → 4 tools semânticas.
- Docs atualizados: freeze V2, handoff Keycloak (4 tools),
  rev.1 SUPERSEDED, residual search limpa (nomes antigos só restam como
  impls internas `tool_get_my_context`/`tool_get_catalog` e no
  histórico documentado).

## R5 — VERIFY FINAL — PASS

Gate acceptance:

```text
SURI_SEMANTIC_TOOLS        4          PASS
TOOLS_DISCOVERABLE         PASS       (wire tools/list + catalog)
LEGACY_BEHAVIOR_PARITY     8/8        PASS
SEMANTIC_DISPATCH          PASS       (enums + closed models + 422)
COMPOUND_REQUESTS          PASS       (read→analyze→knowledge + partial)
AUTHZ_REGRESSION           PASS
KNOWLEDGE_CITATIONS        PASS
ANALYSIS_REGRESSION        PASS
DOCKER_BUILD               PASS
MCP_SMOKE                  PASS       (container real)
DOCUMENTATION              PASS

FUTURE_EXECUTE             PLANNED    (não registrado)
FUTURE_DELETE              PLANNED    (não registrado)
KEYCLOAK_REGISTERED        NO
CHATGPT_CONNECTED          NO
PRODUCTION_DEPLOYED        NO
```

## FILES CHANGED

- `app/interfaces/mcp/{constants,schemas,tool_bridge,server,branding}.py`
  (`schemas.py` novo)
- `tests/interface/suri_mcp/{test_tool_bridge,
  test_knowledge_and_analysis}.py` reescritos
- `docs/SURI-S1-CONTRACT-FREEZE-V2.md` (novo),
  `docs/SURI-S1-CONTRACT-FREEZE.md` (superseded note),
  `docs/SURI-MCP-KEYCLOAK-HANDOFF.md` (4 tools)

## RESIDUAL

- Impls internas mantêm nomes `tool_get_my_context`/`tool_get_catalog`/
  `tool_*_purchase_orders` (handlers privados sob os dispatchers — não
  são superfície pública).
- `initialize`/`tools/call` autenticados end-to-end: não prováveis sem
  client Keycloak registrado (fora de escopo — mesma limitação do
  baseline S0–S9).
