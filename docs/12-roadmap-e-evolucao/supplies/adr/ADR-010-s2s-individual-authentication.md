# ADR-010 — Autenticação S2S individual entre supplies-api e api-delpi

| Campo | Valor |
|-------|--------|
| Status | Aceito — infraestrutura implementada e testada; piloto depende de cliente Keycloak provisionado |
| Contexto | Revisão P1.SEC comprovou que `API_DELPI_INTERNAL_SERVICE_TOKEN` + `X-Delpi-Caller-App` mintam principal `is_superadmin=True` sem vínculo criptográfico de serviço |
| Relacionados | ADR-009 (refina a seção "Fronteiras" sem alterar as decisões de acesso de produto), [padrão S2S](../../11-padroes-de-desenvolvimento/padrao-autenticacao-s2s-individual.md) |

## Decisão

A identidade técnica de `supplies-api` ao chamar `api-delpi` passa a ser um
JWT OAuth2 **Client Credentials** de cliente confidencial exclusivo,
transportado em `X-Delpi-Service-Authorization: Bearer <jwt>`.

A `api-delpi` valida assinatura (JWKS), issuer, audience dedicada
(`S2S_AUDIENCE`), cliente técnico (`azp`/`client_id` dentro de
`S2S_ALLOWED_CLIENTS`) e escopo de operação — via
`delpi_auth.ServiceTokenValidator`, sem `is_superadmin` e sem usar
`X-Delpi-Caller-App` como prova.

O usuário final continua em `Authorization: Bearer <user JWT>`; o principal
resolvido pelo middleware (Core `/me`) permanece o ator delegado para
auditoria e futura resolução de `codusr`. Autorização funcional segue
`supplies.access`/`supplies.manage` na BFF — sem permission CRUD nova.

## Consequências

- O token compartilhado legado permanece para consumidores não migrados e
  **não autoriza** superfícies marcadas com os decorators S2S.
- Não há fallback automático S2S → token legado em chamadas migradas.
- `jwt_middleware`, `authorization.py` e decorators existentes não foram
  alterados; o mecanismo é aditivo e route-scoped.
- Cliente confidencial `supplies-api` + audience mapper no Keycloak são
  pré-requisito de infraestrutura (provisão autorizada separada); sem eles
  o smoke live fica `INCONCLUSIVE` e o verificador falha fechado em 503.
- Escritas POST/PUT de fornecedor continuam atrás dos feature gates
  existentes; este ADR não habilita gravação nem promove E13/E14.

## Migração progressiva

Novos serviços adotam o padrão provisionando cliente próprio e
adicionando o `client_id` à `S2S_ALLOWED_CLIENTS` do verificador —
substituindo gradualmente a autoridade do token compartilhado sem big bang.
