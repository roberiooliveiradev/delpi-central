# Ficha pública — cadastro ChatGPT da CLARA (MCP)

`EXECUTION_ID: CF-PROC0072-CLARA-CHATGPT-EARLY-VALIDATION-001`
(Doc 107) · SHA de referência: `e8d9361dee` · Ambiente:
`https://minhadelpi.com.br` (srv-api — produção, piloto somente
após gates; ver §Estado).

> **Nunca** publicar client secret, tokens, senhas ou valores de
> `.env`. O secret do client `mcp-clara` fica no cofre/canal
> seguro do Operador — referenciar, nunca copiar para cá.

## Valores de cadastro (verificados)

| Campo | Valor | Evidência |
|---|---|---|
| Nome sugerido | `CLARA — Central de Fechamento` | produto Doc 94 |
| MCP URL (connector endpoint) | `https://minhadelpi.com.br/apps/controllership-finance-api/mcp` | `GET`/`POST` ⇒ HTTP 401 JSON no edge (montado; SHA pré-rework em prod) |
| Protected-resource metadata (RFC 9728) | `https://minhadelpi.com.br/apps/controllership-finance-api/.well-known/oauth-protected-resource` | contrato no código; resposta JSON esperada pós-deploy do SHA `e8d9361dee` (a 401 atual é do header `WWW-Authenticate` → ver nota) |
| Issuer | `https://minhadelpi.com.br/auth/realms/delpi` | `/.well-known/openid-configuration` — verificado 2026-10-25 |
| Authorization URL | `https://minhadelpi.com.br/auth/realms/delpi/protocol/openid-connect/auth` | idem |
| Token URL | `https://minhadelpi.com.br/auth/realms/delpi/protocol/openid-connect/token` | idem |
| JWKS | `https://minhadelpi.com.br/auth/realms/delpi/protocol/openid-connect/certs` | idem |
| Client ID escolhido pelo PO | `mcp-controllership-finance` | DECISION_REQUIRED de compatibilização: o engine IAM ainda define `mcp-clara`; não afirmar provisionamento concluído |
| Client authentication | `client_secret_post` | padrão comprovado ChatGPT (runbook FASE B) |
| PKCE | `S256` | contrato do engine |
| Grant | `authorization_code` (+ `refresh_token`/`offline_access` opcional) | discovery do realm |
| Scopes | `openid profile email mcp:tools` (+ `offline_access` se refresh prolongado) | contrato `mcp:tools` compartilhado |
| Audience (resource) | `https://minhadelpi.com.br/apps/controllership-finance-api/mcp` (+ `delpi-central`) | audience mapper dedicado do client — nunca no scope `mcp:tools` |
| Redirect/callback URI | **fornecida pelo ChatGPT no fluxo real de cadastro** — registrar o valor exato aqui após o cadastro | ação do usuário no workspace |
| Secret | no cofre do Operador | NÃO publicar |

## Passos de cadastro (usuário, no ChatGPT)

1. Criar o conector/app com a MCP URL acima e OAuth "custom".
2. Informar Client ID `mcp-clara`, authorization/token URLs,
   scopes e `client_secret` (do cofre).
3. Copiar a **callback URI exata** exibida pelo ChatGPT e entregá-la
   ao Operador → registrá-la no `Valid redirect URIs` do client
   `mcp-clara` no Keycloak (`--apply` com a URI real).
4. Completar o login Keycloak no fluxo OAuth do ChatGPT.
5. Roteiro de aceite (Doc 107 §3): discovery `tools/list` → READ
   por usuário autorizado → consulta com fonte/citação → plano
   multiação → consentimento consolidado no Portal → ACT só sobre
   dados de teste → read-back + auditoria.

## Estado (2026-10-26, pós-deploy)

| Item | Estado |
|---|---|
| Deploy produção | **EXECUTADO** — `2eeb5fb943` (inclui `ecf765139d`) |
| Migrations | **V001–V014 aplicadas** (V006–V014 em 2026-10-26 07:03 -03) |
| MCP endpoint | **live** — 401 + `WWW-Authenticate` RFC 9728 + resource_metadata |
| Protected-resource metadata | **live** — `.well-known/oauth-protected-resource/mcp` 200 |
| Corpus governado | **PUBLICADO** — `5541097a-8608-4470-b971-7c28b3ae6c40` (52 fontes / 1 298 itens) |
| Cliente `mcp-clara` | **BLOCKED** — credenciais admin de Keycloak reportadas inválidas; aguarda owner IAM/Operador |
| Cadastro ChatGPT | `TEST_NOT_RUN` — depende do client provisionado |
| Redirect URI | `TEST_NOT_RUN` — será registrada do fluxo real |
| G1/G2/G3 | `PENDING` — registro formal pendente (deploy por GO operador, Adendos 3–5 Doc 107) |

**Próximo passo desbloqueante:** credencial admin Keycloak vigente (ou reset
autorizado pelo operador) → `keycloak-prod-delia-mcp-provision.sh --check` →
diff aprovado → `--apply` (somente `mcp-clara`, sem tocar TÉO/DAVI/VISTA/DÉLIA)
→ cadastro real no ChatGPT → smoke autenticado → ficha definitiva.


## Decisão do PO — 26/10/2026 — alteração de Client ID solicitada

O PO determinou **manter o Client ID `mcp-controllership-finance`** informado na tela de criação do Keycloak, em vez do ID anterior `mcp-clara`. Esta ficha passa a registrar **`mcp-controllership-finance` como TARGET aprovado de identificação do cliente OAuth**. O nome da especialista permanece CLARA; o nome do BFF e o MCP URL **não mudam**.

**Estado de implementação: `DECISION_REQUIRED / PENDING_RECONCILIATION`.** O desired-state em `infra/scripts/delia_mcp_keycloak_state.py` ainda aponta para `mcp-clara` e o provisionador compartilhado não pode ser executado sem conciliação. O fluxo de cadastro no Keycloak exibido pelo PO estava em `Capability config`, antes da confirmação de criação; portanto não declarar cliente criado. Não alterar automaticamente os clients DAVI/TÉO/VISTA, nem afirmar compatibilidade OAuth até validar os consumers, claims, audience, scopes, policies, documentação e testes. O campo `Client ID` da seção anterior é a decisão de produto, **não** evidência de runtime.

**Handoff técnico:** inventariar todas as referências a `mcp-clara` (código, scripts, testes, docs, env e deploy), distinguir identificador OAuth de resource/audience, preparar diff mínimo e testes, verificar necessidade de decisão IAM sobre token-exchange e alterações no engine compartilhado. Após aprovação do diff e testes, reconciliar provisionamento, obter callback exata no ChatGPT, validar login e smoke autenticado. Até lá, `CHATGPT_CONNECTION=TEST_NOT_RUN`.
