# SURI-MCP-SUPPLIERS-WRITE-001 — Evidência de execução (2026-10-30)

Registro de evidência dos gates S0–S7. Histórico de bloqueios preservado;
classificações anteriores corrigidas por evidência de runtime, nunca por
relato isolado.

## S0 — Verificação de produção (runtime, não-destrutiva)

| Prova | Resultado |
|---|---|
| `PROTHEUS_SUPPLIER_CREATE_ENABLED` (env api-delpi prod) | `true` |
| `PROTHEUS_SUPPLIER_UPDATE_ENABLED` (env api-delpi prod) | `true` |
| S2S provider no container `delpi-supplies-api` | `s2s_configured=True`, `s2s_config_ok`; scope resolvido `suppliers.read suppliers.create suppliers.update consumption-audit.read` |
| Probe UPDATE `999999/01`, ator mapeado (`rober` → `codusr`) | `PROTHEUS_SUPPLIER_NOT_FOUND` — cadeia completa: validação → gate → Core identity → params/target → **Protheus REST** → upstream 404. Zero escrita. |
| Probe UPDATE fornecedor inválido | `PROTHEUS_SUPPLIER_ID_INVALID` (validação antes do upstream) |
| Probe UPDATE campo não editável (`nome`) | `PROTHEUS_SUPPLIER_FIELD_NOT_EDITABLE` (allowlist PUT) |
| Probe UPDATE ator UUID não mapeado | `PROTHEUS_IDENTITY_UNMAPPED` (gate aberto, resolução de identidade alcançada) |
| Probe CREATE payload canônico válido, ator não mapeado | `PROTHEUS_IDENTITY_UNMAPPED` — gate aberto + validação completa; POST real **não** disparado (criaria fornecedor fake em produção) |

Conclusão S0: `SUPPLIER_CREATE`/`SUPPLIER_UPDATE` = **PROVEN em runtime**
(create com gate+cadeia pré-escrita provados; update end-to-end ao REST).
Classificação `BLOCKED` dos docs P0 = `STALE_EVIDENCE`, superada pelo
cutover X4.PROD-C1 efetivado em produção.

## S1 — Contract freeze

`SURI-S1-CONTRACT-FREEZE-V3.md` (rev.3, aditiva): superfície passa a 5
tools — `get_context, read, analyze, knowledge, execute`.
`execute(entity="suppliers", action="create"|"update", operations=[1..10])`
com `SupplierWriteOperation` fechado (`extra="forbid"` + validação em
profundidade), allowlists canônicas `POST_SUPPLIER_FIELDS`/
`PUT_SUPPLIER_FIELDS`, identidade inequívoca para update, sem URL/SQL/
handler arbitrário.

## S2 — Fundação de escrita governada

- **AuthZ**: transporte JWT/aud/`mcp:tools` (service principal banido) +
  `can_use_operations` (`supplies.access`) re-derivado por chamada —
  mesma policy das rotas `POST/PUT /suppliers` do Portal.
- **Registry fechado**: `EXECUTE_ACTIONS_BY_ENTITY` em `constants.py` é a
  única fonte do dispatch.
- **Idempotência**: `idempotency_key` por operação; claim durável atômico
  `supplies.suri_execute_operations` (V005, deploy-001/D1) — replay retorna
  `replayed` sem reexecutar, payload divergente → `idempotency_conflict`,
  chave em voo → `in_progress`, store indisponível → fail-closed 503.
- **Auditoria**: uma linha estruturada `suri_execute` por operação —
  ator, correlação, identidade normalizada, nomes de campos (nunca
  valores — LGPD), outcome, `operation_id`, http_status.
- **Delegação**: `DelpiS2SApiGateway` (mesma credencial S2S do BFF,
  `X-Delpi-Service-Authorization`); nunca Protheus/banco direto.
- **Correlação**: `X-Correlation-ID` propagado ao tracker api-delpi.
- **Erros canônicos**: `classify_supplier_write_error` em
  `suppliers_dto.py` — fonte única BFF↔MCP (`write_disabled`/`rejected`/
  `indeterminate`/upstream).

## S3 — Execute semântico

`tool_execute` no `tool_bridge`; annotations `readOnlyHint=false`,
`destructiveHint=false`, `idempotentHint=true`. Fluxo:
ChatGPT → SURI.execute → identidade/AuthZ → validação →
`DelpiS2SApiGateway` → `POST/PUT /integrations/protheus/suppliers*` →
api-delpi (gate → codusr → tracker → REST único → ACK → read-back) →
resultado estruturado.

## S4 — Multi-operação

Lote 1–10 operações sequenciais; resultado individual por operação;
`summary` agrega por outcome; sem transação presumida; nenhuma escrita
repetida implicitamente (retry proibido — `indeterminate` exige checar
`operation_id`).

## S5 — Testes

- `tests/interface/suri_mcp/test_execute.py` (novo): contrato fechado,
  identidade ambígua, campos protegidos, AuthZ deny, service principal,
  erros api-delpi, indeterminate, idempotência/replay/conflict, batch
  parcial, regressão das 4 tools.
- suíte `suri_mcp`: **92 passed** · suíte completa `supplies-api`:
  **756 passed, 21 skipped**.
- Docker build `supplies-api/Dockerfile`: PASS — imagem contém
  `supplier_execute`, `CATALOG_VERSION=3`, `tools/list` = exatamente
  `get_context, read, analyze, knowledge, execute`.

## S6 — Documentação reconciliada

- Matriz/inventário: denominador normalizado (34 READ + 9 WRITE + 2
  supplier ERP writes = 45 capacidades); supplier create/update
  reclassificados `BLOCKED → PROVEN` com evidência datada; blocos
  históricos preservados.
- Freeze rev.3 criado; rev.2 marcada SUPERSEDED (conteúdo histórico
  intacto); handoff Keycloak e master plan ajustados para 5 tools.
- Roadmap supplies (`README` + `IMPLEMENTATION-PLAN`): notas datadas de
  «ERP write OFF» anotadas como superadas por evidência 2026-10-30.
- `SURI_MCP_INSTRUCTIONS` corrigidas — removida a negação de execute
  (instrução stale ensinava ao cliente que não existia escrita).

## S7 — Entrega

Escopo commitado isolado dos diffs alheios (delia-api, engineering-api,
api-delpi products, commercial-api preservados no working tree).
Deploy **não executado** — produção segue com catalog v2 (4 tools);
`execute` fica disponível após rebuild/deploy de `delpi-supplies-mcp`
e `delpi-supplies-api` (mesma imagem Dockerfile). Keycloak, scopes,
audiences e secrets inalterados. ChatGPT: funcionalidade não declarada —
exige deploy + `tools/list` autenticado como evidência.

## Residual

- Idempotência cross-restart: **resolvido no deploy-001/D1** — claim
  atômico em `supplies.suri_execute_operations` (V005) substitui o cache
  in-process; DECISION-E1 encerrada como store pg no owner supplies-api.
- `persistence_proven=false`/`tracking_warning` propagados verbatim —
  ACK nunca é persistência.
- `S2S_SCOPE` vazio no `.env` host vs scope completo resolvido no
  container — drift de arquivo, não de runtime; `TO_INVENTORY` para
  saneamento do `.env` fora deste escopo.
