# EVA.MCP.V1.R1 — Strict OAuth Metadata Public Path Matching

Correção de segurança na allowlist de caminhos públicos da
`engineering-api`, introduzida na EVA.MCP.V1.

Baseline: `3060ab0741` (EVA.MCP.V1). BASE_HEAD efetivo: HEAD de
`origin/main` no momento da execução.

## 1. Causa raiz

`_is_engineering_public_path` classificava como público qualquer path que
**contivesse** a substring `/.well-known/oauth-protected-resource`:

```python
return "/.well-known/oauth-protected-resource" in normalized
```

Isso tornava públicos caminhos arbitrários como
`/fake/.well-known/oauth-protected-resource` ou
`/.well-known/oauth-protected-resource/extra` — violação do contrato de
allowlist estrita de F1.S2R1. Embora essas URLs não resolvessem rotas
reais (404 após o middleware), a política pública não pode depender do
destino da rota: um path futuro registrado sob um prefixo coincidente
passaria a ser servido sem autenticação.

## 2. Comportamento de root_path e gateway

- Uvicorn inicia com `--root-path /apps/engineering-api`; no tráfego de
  produção o `request.url.path` chega **com** o prefixo
  (`/apps/engineering-api/health` aparece no access log).
- Chamadas internas sem prefixo também resolvem (Starlette aplica
  `get_route_path` — subtrai root_path quando presente).
- Conclusão: a allowlist precisa das **duas** formas — bare e prefixada —
  mas somente das rotas realmente registradas.

## 3. Rotas de metadata registradas

`MCP_RESOURCE_CONFIG.metadata_paths` (resource_metadata.py):

```text
/.well-known/oauth-protected-resource
/.well-known/oauth-protected-resource/mcp
```

Com a variante prefixada, a allowlist efetiva é:

```text
/.well-known/oauth-protected-resource
/.well-known/oauth-protected-resource/mcp
/apps/engineering-api/.well-known/oauth-protected-resource
/apps/engineering-api/.well-known/oauth-protected-resource/mcp
```

## 4. Correção (menor diff)

`engineering_app/middleware/auth_middleware.py`:

- Nova constante `_PUBLIC_OAUTH_METADATA_PATHS` — `frozenset` derivada de
  `MCP_RESOURCE_CONFIG.metadata_paths` ∪ prefixo `MCP_GATEWAY_ROOT`.
  Fonte única de verdade: se os aliases registrados mudarem, a allowlist
  acompanha o contrato, sem duplicar strings.
- Predicado passa a comparação exata:
  `normalized in _PUBLIC_PATHS or normalized in _PUBLIC_OAUTH_METADATA_PATHS`.
- Nenhuma mudança em `mcp_transport_auth`, JWT, audience, scope,
  service-token gate, Core `/me` ou tools — o defeito era exclusivamente
  a classificação de caminhos públicos.

Antes / depois:

```text
ANTES:  "/.well-known/oauth-protected-resource" in normalized
DEPOIS: normalized in _PUBLIC_OAUTH_METADATA_PATHS  (exact match)
```

## 5. Testes

Adicionados a `tests/test_auth_middleware.py` (+24 testes):

- `test_oauth_metadata_exact_paths_are_public` — 4 rotas oficiais → ≠ 401
  (discovery segue funcional).
- `test_oauth_metadata_arbitrary_paths_require_auth` — 20 caminhos falsos
  (prefixos `/fake/…`, `/x/apps/…`; sufixos `/extra`, `-fake`, `XYZ`,
  `mcpX`; substring em outros segmentos; `.well-known` pais) → **401**,
  nunca 404.
- `test_oauth_metadata_allowlist_exact_matching` — unitário do predicado:
  exatos, trailing slash, query string → público; prefixos/sufixos/
  substrings/`//` → privado; asserção do conteúdo exato da allowlist.

Suíte completa engineering-api: **243 passed** (baseline 219 + 24 novos).

## 6. Regressões de AuthN/AuthZ verificadas

- Sem Bearer → 401; Bearer inválido → 401 (transport gate MCP e rotas).
- aud ausente / scope `mcp:tools` ausente → 401 (test_eva_mcp).
- Service token na superfície MCP → 401 (`service_token_gate`).
- Principal service / sem `engineering.access` → 403.
- Trailing slash: `/health/` etc. → 404 (não 401) — contrato preservado.
- Dot-segments/encoding: normalização do transporte → rota canônica;
  não é bypass (documentado em testes existentes).
- `//`-dupla-barra: não casa a allowlist exata → 401.

## 7. Audits e build

- `audit_backend_boundaries` — 0 findings.
- `audit_fastapi_authz` — 0 findings.
- `audit_platform_guardrails` — 0 findings.
- `audit_architecture_phase3` — 0 findings.
- Docker build `delpi-engineering-api:eva-r1-test` — OK; import da app OK.

## 8. Deploy e smoke

- Deploy: `up-prod-sequential.sh --build engineering-api` (somente o
  serviço afetado; gateway inalterado).
- Smoke produtivo: metadata oficial 200; `/mcp` sem token → 401 +
  challenge; caminhos falsos com a substring → 401 (não 404);
  health/ready 200; `/v1/home`/`/v1/overview` sem JWT → 401.
- Rollback: revert do commit + redeploy de `engineering-api`.

## 9. Residuais

Nenhum. O residual anterior ("substring permissiva na allowlist") fica
encerrado neste documento. O Activation Gate da EVA V1 segue pendente
apenas das etapas administrativas de Keycloak/ChatGPT (docs 28/29).
