# Autenticação S2S individual (Keycloak Client Credentials)

Padrão compartilhado de identidade técnica service-to-service. A primeira
integração migrada é `supplies-api → api-delpi`; os demais consumidores
seguem coexistindo no token interno compartilhado até migração própria.

## Motivação

O token interno compartilhado (`API_DELPI_INTERNAL_SERVICE_TOKEN`) tem três
falhas estruturais: uma única credencial para todos os serviços, o principal
mintado com `is_superadmin=True` (bypass genérico de decorators e branch
gates) e `X-Delpi-Caller-App` como header autodeclarado sem vínculo
criptográfico com o serviço chamador. O novo mecanismo dá a cada serviço uma
identidade exclusiva, verificável por assinatura, audience e claims.

## Contrato de transporte

```text
Authorization: Bearer <JWT do usuário final>          # delegação do ator
X-Delpi-Service-Authorization: Bearer <JWT do serviço> # credencial S2S
X-Delpi-Caller-App: supplies-api                     # telemetria, não prova
X-Request-Id: <correlação>
```

- `Authorization` mantém a semântica de sempre: o usuário final. O
  middleware existente resolve o principal de usuário normalmente
  (Core `/me`), que continua sendo o ator para auditoria e `codusr`.
- `X-Delpi-Service-Authorization` carrega o JWT client-credentials do
  serviço chamador. O header legado `X-Delpi-Service-Token` **não** é
  enviado nas chamadas migradas.
- Nunca há fallback automático do novo mecanismo para o token legado na
  superfície migrada: ausência de configuração ou falha do provider é
  erro, não degradação para o segredo compartilhado.

## Credencial S2S

OAuth2 Client Credentials no Keycloak da plataforma:

```text
POST <S2S_TOKEN_URL>          # .../realms/<realm>/protocol/openid-connect/token
grant_type=client_credentials
client_id=<cliente confidencial exclusivo do serviço>
client_secret=<secret do cliente>
scope=<escopos opcionais>
```

Cada serviço consumidor usa **cliente confidencial próprio** (ex.:
`supplies-api`). Compartilhar secret entre serviços reproduz a fraqueza do
token legado e é proibido.

## Claims validados (verificador)

| Claim | Regra |
|---|---|
| assinatura | JWKS do realm via `delpi_auth.jwt_validator` |
| `iss` | `KEYCLOAK_ISSUER` do serviço verificador |
| `aud` | deve conter `S2S_AUDIENCE` (ex.: `api-delpi`) — exige audience mapper/client scope no cliente |
| `exp` | rejeitado expirado (jose `ExpiredSignatureError`) |
| `azp` (fallback `client_id`) | deve pertencer a `S2S_ALLOWED_CLIENTS` — prova da identidade técnica |
| `sub` | obrigatório não-vazio |
| `scope` | deve conter todos os `required_scopes` da operação |

Um JWT de usuário do Portal (`azp=delpi-central`) nunca satisfaz a
allowlist de clientes técnicos. A decisão de autorização é
`authenticated_service AND allowed_audience AND allowed_operation` —
sem `is_superadmin` e sem consultar `X-Delpi-Caller-App`.

## Componentes (`shared/delpi_auth`)

| Componente | Papel |
|---|---|
| `service_contract.py` | header do contrato (`X-Delpi-Service-Authorization`), build/extract de Bearer |
| `service_identity.py` | `ServiceIdentity` — identidade técnica sem flag de superadmin |
| `service_errors.py` | erros tipados com `code` estável para observabilidade |
| `service_token_validator.py` | valida JWT S2S (signature/iss/aud/exp + cliente + scope); `from_env()` fail-closed |
| `service_token_provider.py` | `ClientCredentialsTokenProvider` — grant, cache com margem de expiração, timeout, erros tipados |

## Configuração (sem secrets no código)

Verificador (api-delpi e futuros):

```text
S2S_AUDIENCE=api-delpi                 # audience dedicada exigida
S2S_ALLOWED_CLIENTS=supplies-api       # CSV de client_ids aceitos
```

Solicitante (supplies-api e futuros):

```text
S2S_TOKEN_URL=<endpoint token do realm>
S2S_CLIENT_ID=supplies-api
S2S_CLIENT_SECRET=<injetado via env/secret store>
S2S_SCOPE=<opcional, separado por espaço>
S2S_TIMEOUT_SECONDS=10
```

Configuração obrigatória ausente falha fechado (`S2S_CONFIG_MISSING` →
503 no verificador, erro tipado no solicitante). Pré-requisito de
infraestrutura: provisionar o cliente confidencial no Keycloak com
service account habilitada e audience mapper para `S2S_AUDIENCE`
(autorização de infraestrutura separada — não é feita pelo código).

## Integração no consumidor (ex.: supplies-api)

`DelpiS2SApiGateway` estende `DelpiApiGateway` substituindo apenas a
montagem de headers: `Authorization` = Bearer do usuário,
`X-Delpi-Service-Authorization` = JWT S2S, caller-app e request-id
preservados, `X-Delpi-Service-Token` **nunca** enviado. O provider é
singleton por processo (`get_s2s_token_provider`) para o cache de token
sobreviver a gateways por request. Falha de token → `DelpiApiGatewayError`,
sem request.

## Integração no verificador (ex.: api-delpi)

`app/interface/http/s2s_service_access.py`:

- `require_s2s_service(required_scopes=..., allowed_clients=...)` —
  superfície exclusiva de serviço; header ausente/malformado → 401;
  cliente ou scope errado → 403; config ausente → 503.
- `require_s2s_or_any_permission(permission_codes, ...)` — S2S para
  serviços, permissão de usuário para chamadas diretas. Com o header
  presente a validação é estrita (não degrada para o path de usuário);
  sem o header, um principal `service` (token legado) é negado — o token
  compartilhado não autoriza a superfície migrada.

A identidade validada é anexada a `request.state.service_identity` para
auditoria. `X-Delpi-Caller-App` continua existindo apenas como metadado.

## Delegação do usuário

O ator é sempre o principal resolvido do `Authorization` Bearer —
Keycloak valida assinatura/issuer/audience/expiração e o Core `/me`
resolve o UUID e permissões efetivas. Nunca headers `X-Delpi-Actor-*`
(comportamento do PAC actor middleware é precedente negativo, não
template). Para escritas futuras, a resolução do ator usa
`load_user_rbac(token, force_refresh=True)` (fail-closed, sem cache
stale) antes de `resolve_actor_codusr` pelo Core — gates de feature,
normalizadores e semântica MATA020 permanecem inalterados.

## Coexistência e migração progressiva

- O token interno segue disponível para consumidores legados; nenhuma
  rota existente foi alterada.
- A migração é por operação/rota: novas superfícies exigem S2S;
  rotas antigas continuam no contrato atual até migração explícita.
- Migrar outro serviço = provisionar cliente confidencial próprio,
  adicioná-lo a `S2S_ALLOWED_CLIENTS` e trocar o gateway/headers —
  sem alterar `jwt_middleware`, `authorization.py` ou decorators legados.

## Rollback e rotação

- Rollback de consumo: gateway S2S é código novo — reverter restaura o
  comportamento anterior; rotas verificadoras são aditivas.
- Rollback de verificação: remover o decorator da rota nova; nenhum
  consumidor legado depende dele.
- Rotação de credencial: trocar o secret do cliente no Keycloak e na
  env do serviço; o provider busca token novo na expiração. Revogar o
  cliente remove imediatamente a capacidade do serviço — sem afetar os
  demais.

## Evidências

- `shared/delpi_auth/tests/test_service_{contract,token_validator,token_provider}.py`
- `api-delpi/tests/test_s2s_service_access.py`
- `supplies-api/tests/infrastructure/gateways/test_delpi_s2s_gateway.py`

Cobrem: grant, cache e margem de expiração, timeout, resposta malformada,
assinatura/issuer/audience/expiração inválidos, cliente não autorizado,
scope insuficiente, config ausente fail-closed, token legado negado,
caller-app falsificado irrelevante, principal de usuário delegado e
ausência de `X-Delpi-Service-Token` na chamada migrada.

## Limites declarados

- O smoke live depende do cliente confidencial provisionado no Keycloak —
  `INCONCLUSIVE` até a infraestrutura autorizada existir.
- `azp` é a prova de identidade técnica: um JWT de usuário com `azp`
  inadvertidamente na allowlist passaria — a allowlist é controle
  administrativo explícito e restrito.
- Permissões funcionais do usuário permanecem responsabilidade da BFF
  (`supplies.access`/`supplies.manage` via Core); o verificador S2S não
  cria autoridade paralela sobre autorização de produto.

## Evidência de produção (P1.SEC.5)

Executado em `srv-api` (Keycloak 24, realm `delpi`):

- Cliente confidencial `supplies-api` provisionado (service account;
  standard flow e direct access grants desabilitados); cliente
  `api-delpi` criado como audience holder; mapper de audience
  `oidc-audience-mapper` inclui `api-delpi` no access token.
- Emissão real: `client_credentials` retorna JWT com `azp=supplies-api`,
  `aud` contendo `api-delpi`, `iss` igual ao `KEYCLOAK_ISSUER` do ambiente.
- Validação real dentro do container `delpi-api-delpi`: token aceito com
  cliente/audience corretos via JWKS do realm.
- Negativos reais: token `delpi-core-admin` negado (`S2S_TOKEN_INVALID`),
  segredo legado como Bearer negado, header opaco sem scheme negado,
  assinatura adulterada negada, scope exigido ausente → `S2S_SCOPE_DENIED`,
  allowlist por rota excluindo `supplies-api` → `S2S_CLIENT_DENIED`.
- Gateway real dentro de `delpi-supplies-api`: `_build_headers` emite
  `X-Delpi-Service-Authorization` com JWT válido, preserva o Bearer do
  usuário e nunca inclui `X-Delpi-Service-Token` nem o segredo legado.
- Injeção por cliente: `/purchase-requests` sem JWT → 401; headers
  S2S/actor forjados → 401.
- Coexistência: `delpi-core-api`, `delpi-gateway`, `delpi-portal` e
  consumidores legados saudáveis após o deploy; `supplies-api` →
  `core-api`/`api-delpi` health 200.
- SHAs integrados na `main`: `0d4c7375e2`, `96b0424ee1`, `633390da36`,
  `c22d30eefa`, `0b349670c0`.
- Sem rota de negócio migrada nesta etapa: o wiring produtivo de rotas é
  `INCONCLUSIVE` por desenho (decorators aditivos, nenhum consumer ativo).
