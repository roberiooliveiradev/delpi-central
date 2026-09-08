# Policies, decorators e autorização de rotas

> **Status:** documentação oficial e normativa — revisada em setembro/2026.

## Objetivo

Definir como APIs da Minha DELPI protegem endpoints sem duplicar primitives de autenticação/autorização entre bounded contexts.

## Separação obrigatória

```text
Autenticação
→ validar JWT/identidade

Autorização
→ resolver permissões efetivas
→ validar permission/resource/scope/policy

Regra de negócio
→ use case/domain
```

Essas responsabilidades não devem ser misturadas em controller, MFE ou helper local.

## Dois contextos canônicos

### Core API

A Core API é o bounded context dono de:

- usuário local;
- RBAC;
- Permission Resolver;
- superadmin;
- policies administrativas centrais.

Ela pode manter adapters/decorators próprios em sua camada HTTP, por exemplo `require_auth`, `require_permission`, `require_any_permission`, `require_all_permissions`, `require_superadmin` e Policy Engine.

Esses decorators **não são um template para serem copiados por outras APIs**.

### Demais APIs

Para APIs de domínio, primitives transversais devem partir de:

```text
shared/delpi_auth/jwt_validator.py
shared/delpi_auth/authorization.py
shared/delpi_auth/middleware/
shared/delpi_auth/service_token.py
shared/delpi_auth/policy_engine.py
```

Se Flask/FastAPI/outro framework exigir adaptação, criar adapter fino que delega ao shared. Não recriar JWKS validation, Permission Resolver ou decorators genéricos.

Implementações locais antigas são dívida de migração, não referência para novo código.

## Fluxo de rota protegida

```text
Request
→ middleware/dependency valida identidade
→ contexto de usuário/serviço
→ authorization primitive/policy
→ permission + resource + scope
→ controller
→ use case
```

O frontend pode esconder ações por UX, mas o backend continua sendo a barreira de segurança.

## Primitives simples

Usar primitive/decorator simples quando a decisão for direta:

```text
usuário autenticado
permission X
qualquer uma de X/Y
X e Y
superadmin
```

A primitive deve somente aplicar autorização. Não deve conter regra principal de produto nem SQL complexo.

## Policies contextuais

Usar policy quando a decisão depender de recurso/contexto, por exemplo:

- ownership;
- estado do recurso;
- impedir autoexclusão;
- impedir remoção do último superadmin;
- relação usuário/grupo/app;
- escopo de filial/unidade;
- regra composta que exige contexto adicional.

Policy não substitui use case. Ela responde se a ação pode ocorrer naquele contexto.

## Permissões efetivas

O token identifica o usuário, mas a decisão final deve usar a autorização efetiva canônica.

```text
JWT válido
→ contexto
→ Core/Permission Resolver ou mecanismo canônico
→ permission/scope
→ allow | deny
```

Proibido recalcular RBAC independentemente em cada API ou confiar em `permissions[]` fornecido pelo frontend.

## Fail closed

Indisponibilidade do resolver de permissões não equivale a “usuário sem permissão” nem a “permitir por fallback”. Deve produzir falha controlada/indisponibilidade conforme contrato.

Não usar:

```text
except auth_error: allow
resolver indisponível → permissions=[] → mascarar como 403
```

quando o estado real é incapacidade de decidir autorização.

## Rotas públicas e service-to-service

Nem toda rota precisa de `require_permission`, mas toda rota deve ter **classificação intencional**:

```text
PROTECTED
PUBLIC_INTENTIONAL
SERVICE_TO_SERVICE
```

Exemplos legítimos podem incluir health/readiness, callback público ou endpoint público de produto. A ausência de um decorator textual não é prova suficiente de vulnerabilidade porque os stacks usam middleware/dependencies diferentes.

Por esse motivo, CI não deve aplicar regex genérica “rota sem decorator = falha” até a classificação estar uniformemente materializada.

## Ações de escrita/admin

Operação sensível deve considerar:

- permission específica;
- scope/filial/tenant;
- policy de recurso;
- idempotência quando aplicável;
- audit log;
- confirmação de intenção no frontend quando apropriado.

## Superadmin

Superadmin é conceito central governado pela Core API. Não criar flag, header ou regra local equivalente em outra aplicação.

Se uma API precisa reconhecer bypass de superadmin, deve receber esse contexto pelo mecanismo de autorização canônico, preservando trilha auditável.

## Testes obrigatórios

Para rota protegida, conforme risco:

```text
sem token → 401
token inválido → 401
token válido sem permission → 403
scope incorreto → 403/erro canônico
permission correta → sucesso
resolver indisponível → falha controlada, não fail-open
```

Para policy contextual, testar também recurso pertencente/não pertencente, estado permitido/proibido e superadmin quando aplicável.

## Enforcement atual

O `Architecture Enforcement` bloqueia no diff:

- `JWT_VALIDATOR_DUPLICATION` — novo `jwt.decode` local em API de domínio;
- `AUTHZ_PRIMITIVE_DUPLICATION` — nova redefinição local de `require_auth`, `require_permission`, `require_any_permission`, `require_all_permissions` ou `require_superadmin`;
- `JWT_VERIFY_DISABLED` — desligamento/condicionamento inseguro de assinatura/audience/issuer.

Esses gates evitam **nova duplicação**; não declaram automaticamente que toda rota histórica está correta.

## Checklist de nova rota

- [ ] Classifiquei como `PROTECTED`, `PUBLIC_INTENTIONAL` ou `SERVICE_TO_SERVICE`?
- [ ] Se protegida, qual permission/resource/scope governa a ação?
- [ ] AuthN/AuthZ ocorre no backend?
- [ ] Estou reutilizando `shared/delpi_auth` fora da Core API?
- [ ] Evitei copiar validator/decorator genérico?
- [ ] Regra contextual está em policy e regra de produto no use case/domain?
- [ ] 401 e 403 foram testados quando aplicáveis?
- [ ] Indisponibilidade do resolver não resulta em fail-open?
- [ ] Operação sensível possui auditoria quando necessária?

## Referências

- [jwt.md](./jwt.md)
- [rbac.md](./rbac.md)
- [permission-resolver.md](./permission-resolver.md)
- [superadmin.md](./superadmin.md)
- `.cursor/rules/platform-security-identity-authorization.mdc`
- `.cursor/rules/architecture-ci-enforcement.mdc`
- `shared/delpi_auth/`

## Critério de sucesso

```text
uma fonte de AuthN/AuthZ transversal
+ Core dona do RBAC
+ APIs delegam primitives genéricas
+ policies contextuais pequenas
+ backend enforce
+ negative tests
+ fail closed
```
