# DAVI health & MCP (RQ-7)

## Before

`delpi-api-delpi` Up (unhealthy) — startup RuntimeError on V024
checksum; DAVI `mcp_unavailable` to DÉLIA.

## After (post-reconciliation restart)

- `delpi-api-delpi` Up (healthy); zero migration errors;
  "Nenhuma migration pendente" all plugins.
- DÉLIA semantic_tool_catalog: `catalog_len=12`, `failures=-`,
  owners `api-delpi:4, transformometro-api:4, tv-dashboard-api:4`.
- `native_mcp_toolsets groups=mcp:davi,mcp:teo,mcp:vista` —
  initialize + tools/list exercised via real delegated identity.
- Governed READ (`HTTP multiturn eval, correlation http-mt-351936f0111f`):
  `davi.read` invoked `arguments.code=90260921` →
  `tool_observed status=SUCCESS` → product structure returned:
  90260921 "21010421 CHICOTE DE LIGACAO", type PA, components listed,
  `capability=get_product_structure`, `operation_class=READ`,
  `is_complete=true`, provenance `source_id=davi`.
- Delegated authN/authZ: same subject fingerprint across both turns;
  `exchange_configured`; zero writes; 401 on unauthenticated probe
  preserved.
