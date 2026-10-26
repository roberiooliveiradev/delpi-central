# Ficha pública — cadastro ChatGPT da CLARA (MCP)

`EXECUTION_ID: CF-PROC0072-CLARA-CHATGPT-EARLY-VALIDATION-001`
(Doc 107) · SHA de referência: `e8d9361dee` · Ambiente:
`https://minhadelpi.com.br` (srv-api — produção, piloto somente
após gates; ver §Estado).

> **Nunca** publicar client secret, tokens, senhas ou valores de
> `.env`. O secret do client `mcp-controllership-finance` fica no cofre/canal
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
| Client ID escolhido pelo PO | `mcp-controllership-finance` | RECONCILED 2026-10-26: engine IAM e constantes já apontam `mcp-controllership-finance`; provisionamento/validação de scopes via --check pelo owner IAM |
| Client authentication | `client_secret_post` | padrão comprovado ChatGPT (runbook FASE B) |
| PKCE | `S256` | contrato do engine |
| Grant | `authorization_code` (+ `refresh_token`/`offline_access` opcional) | discovery do realm |
| Scopes | `openid profile email mcp:tools` (+ `offline_access` se refresh prolongado) | contrato `mcp:tools` compartilhado |
| Audience (resource) | `https://minhadelpi.com.br/apps/controllership-finance-api/mcp` (+ `delpi-central`) | audience mapper dedicado do client — nunca no scope `mcp:tools` |
| Redirect/callback URI | **fornecida pelo ChatGPT no fluxo real de cadastro** — registrar o valor exato aqui após o cadastro | ação do usuário no workspace |
| Secret | no cofre do Operador | NÃO publicar |

## Passos de cadastro (usuário, no ChatGPT)

1. Criar o conector/app com a MCP URL acima e OAuth "custom".
2. Informar Client ID `mcp-controllership-finance`, authorization/token URLs,
   scopes e `client_secret` (do cofre).
3. Copiar a **callback URI exata** exibida pelo ChatGPT e entregá-la
   ao Operador → registrá-la no `Valid redirect URIs` do client
   `mcp-controllership-finance` no Keycloak (`--apply` com a URI real).
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
| Cliente `mcp-controllership-finance` | **CRIADO no Keycloak prod** pelo owner IAM — plugin ChatGPT já instalado com OAuth conectado (relato PO); validação de scopes/audience via --check pendente |
| Cadastro ChatGPT | plugin instalado + conta OAuth conectada (OWNER_REPORTED); tools/list autenticado = `TEST_NOT_RUN` |
| Redirect URI | `https://chatgpt.com/connector_platform_oauth_redirect` (cadastrada, OWNER_REPORTED) |
| G1/G2/G3 | `PENDING` — registro formal pendente (deploy por GO operador, Adendos 3–5 Doc 107) |

**Próximo passo desbloqueante:** credencial admin Keycloak vigente (ou reset
autorizado pelo operador) → `keycloak-prod-delia-mcp-provision.sh --check` →
diff aprovado → `--apply` (somente `mcp-controllership-finance`, sem tocar TÉO/DAVI/VISTA/DÉLIA)
→ cadastro real no ChatGPT → smoke autenticado → ficha definitiva.


## Decisão do PO — 26/10/2026 — alteração de Client ID solicitada

O PO determinou **manter o Client ID `mcp-controllership-finance`** informado na tela de criação do Keycloak, em vez do ID anterior `mcp-clara`. Esta ficha passa a registrar **`mcp-controllership-finance` como TARGET aprovado de identificação do cliente OAuth**. O nome da especialista permanece CLARA; o nome do BFF e o MCP URL **não mudam**.

**Estado de implementação: `RECONCILED` (código/testes/docs, 2026-10-26).** O desired-state em `infra/scripts/delia_mcp_keycloak_state.py` (`SPECIALISTS`), `MCP_PREDEFINED_CLIENT_ID`, os testes do engine e esta ficha já apontam para `mcp-controllership-finance`. O cliente foi criado no Keycloak prod pelo owner IAM e o plugin ChatGPT está instalado com conta OAuth conectada (OWNER_REPORTED); a validação `--check` do desired-state (scopes, audience mapper, PKCE, redirect) permanece pendente da credencial administrativa vigente. `mcp-clara` permanece apenas como referência histórica neste parágrafo — nenhum consumer o exige.

**Handoff técnico — residual:** credencial admin Keycloak prod vigente → `keycloak-prod-delia-mcp-provision.sh --check` (confirma que `mcp-controllership-finance` tem `mcp-audience-clara` + `mcp:tools` + PKCE S256 + redirect exato; verifica drift e ausência de alteração não autorizada em TÉO/DAVI/VISTA/DÉLIA) → `--apply` somente se o diff exigir → smoke autenticado `tools/list` + READ no ChatGPT. Até lá, `CHATGPT_CONNECTION=TEST_NOT_RUN`.
