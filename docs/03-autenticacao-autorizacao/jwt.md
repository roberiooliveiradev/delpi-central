# JWT, claims e validação de token

> **Status:** documentação oficial e normativa — revisada em setembro/2026.

## Princípio

Na Minha DELPI:

```text
Keycloak/OIDC
→ JWT autentica identidade
→ backend valida token e claims
→ Core API / mecanismo canônico resolve autorização efetiva
```

O JWT **não é a fonte final da lista completa de permissões**.

## Invariantes obrigatórios

Toda API protegida deve validar, no backend:

- assinatura por JWKS;
- algoritmo permitido;
- `iss` contra `KEYCLOAK_ISSUER`;
- `aud` contra `KEYCLOAK_AUDIENCE`;
- `exp` e demais claims temporais relevantes;
- claims mínimas necessárias ao contexto.

Configuração ausente não pode desligar silenciosamente uma validação obrigatória.

```text
issuer/audience ausente ou inválido
→ configuração/token inválido
→ fail closed
```

É proibido transformar isso em:

```text
KEYCLOAK_AUDIENCE ausente
→ verify_aud = false
→ aceitar token mesmo assim
```

## Fonte canônica para APIs

Para APIs fora da Core API, novas implementações devem partir de:

```text
shared/delpi_auth/jwt_validator.py
shared/delpi_auth/middleware/
shared/delpi_auth/authorization.py
```

A Core API possui adapters próprios por ser o bounded context responsável por identidade local, RBAC e Permission Resolver.

Implementações JWT locais já existentes em APIs de domínio são dívida de migração e **não são template para novas APIs**.

Nova API não deve copiar `PyJWKClient`, `jwt.decode`, cache de JWKS ou decorators genéricos quando a responsabilidade já existe no shared.

## Variáveis

Configuração esperada em API protegida:

```env
KEYCLOAK_JWKS_URL=<jwks-interno-ou-discovery>
KEYCLOAK_ISSUER=<issuer-exato-do-token>
KEYCLOAK_AUDIENCE=<audience-esperada>
JWT_ALGORITHMS=RS256
```

`KEYCLOAK_JWKS_URL` pode usar endereço interno de container enquanto `KEYCLOAK_ISSUER` deve corresponder exatamente ao claim `iss` emitido pelo Keycloak.

## Estado atual confirmado — dívida P0

O padrão acima é o contrato obrigatório, mas o shared atual ainda possui dívida que **não deve ser escondida pela documentação**.

Em `shared/delpi_auth/jwt_validator.py`, `_decode_token()` atualmente:

```text
- lê KEYCLOAK_AUDIENCE;
- passa audience somente quando configurada;
- usa options.verify_aud = bool(audience);
- não passa KEYCLOAK_ISSUER ao jwt.decode.
```

Consequência: ausência de audience pode desabilitar sua verificação e issuer não é verificado nesse ponto compartilhado.

Classificação:

```text
SECURITY_DEBT: P0
TIPO: token validation / token confusion
CANONICO_ALVO: fail-closed issuer + audience + signature + expiry
```

Essa dívida deve ser corrigida de forma controlada após confirmar `KEYCLOAK_ISSUER` e `KEYCLOAK_AUDIENCE` nos ambientes e consumidores; não copiar o comportamento atual para novos serviços.

O `Architecture Enforcement` já impede **nova** introdução de:

- `verify_signature=false`;
- `verify_aud=false`;
- `verify_iss=false`;
- verificação condicional como `"verify_aud": bool(optional_value)`;
- novo `jwt.decode` local em APIs fora do shared/Core.

## Claims

Claims mínimas típicas:

| Claim | Uso |
|---|---|
| `sub` | identidade estável do usuário |
| `email` | sincronização/identificação quando necessária |
| `name` | apresentação/identidade |
| `iss` | emissor — obrigatório validar |
| `aud` | destinatário — obrigatório validar |
| `exp` | expiração — obrigatório validar |

Claims de role/permission no token podem auxiliar contexto, mas **não substituem** autorização efetiva da plataforma.

## Autorização

Fluxo esperado:

```text
Bearer JWT
→ validar JWT
→ resolver identidade/contexto
→ obter autorização efetiva
→ validar permission/resource/scope
→ controller/use case
```

Esconder botão no Portal não protege endpoint.

## Rotas públicas

Middleware pode permitir request sem token para superfícies explicitamente públicas, como health/readiness ou fluxos públicos de produto.

Isso não significa que “sem decorator = público”. Cada endpoint deve possuir classificação arquitetural intencional:

```text
PROTECTED
PUBLIC_INTENTIONAL
SERVICE_TO_SERVICE
```

Enquanto essa classificação ainda não estiver uniformemente materializada nos frameworks do monorepo, cobertura de rota deve ser validada por contrato e teste negativo; não por regex simplista.

## Service-to-service

Quando a chamada representa serviço e não usuário, usar mecanismo canônico de service token/credencial de serviço. Não reutilizar access token do usuário indiscriminadamente nem criar secret hardcoded.

Quando houver delegação de usuário, preservar explicitamente ator, serviço chamador e ponto da decisão de autorização.

## Frontend, plugins e iframes

- token não vai em query string;
- token não é persistido desnecessariamente;
- MFE recebe apenas o necessário do shell;
- API chamada pelo MFE valida o token novamente;
- iframe externo não recebe access token por URL;
- logout/refresh seguem o fluxo OIDC do Portal.

## Socket.IO

Preferir token no payload de autenticação do handshake (`auth.token` ou mecanismo vigente), nunca em URL/query quando houver alternativa segura.

O servidor deve aplicar as mesmas invariantes de assinatura/issuer/audience/expiração da superfície HTTP correspondente.

## Testes obrigatórios

Para mudança em autenticação/JWT:

```text
token ausente
assinatura inválida
issuer incorreto
audience incorreta
token expirado
algoritmo não permitido
configuração obrigatória ausente
claim obrigatório ausente
```

Para rota protegida, acrescentar 401/403/escopo conforme `platform-security-identity-authorization.mdc`.

## Gates

Aplicar:

```bash
python -m unittest scripts/ci/test_audit_platform_guardrails.py -v
python scripts/ci/audit_platform_guardrails.py --check --base <commit-base>
```

Regras relacionadas:

- `.cursor/rules/platform-security-identity-authorization.mdc`
- `.cursor/rules/architecture-ci-enforcement.mdc`
- `.cursor/rules/platform-api-contracts-integration.mdc`

## Critério de conclusão

Uma API protegida só está conforme quando:

```text
JWT criptograficamente válido
+ issuer correto
+ audience correta
+ expiração válida
+ autorização backend efetiva
+ testes negativos
```

Sem fallback fail-open por configuração ausente.