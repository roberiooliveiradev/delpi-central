# ADR-001 — Criação da supplies-api

| Campo | Valor |
|-------|--------|
| Status | Aceito (documentação) · **não implementado** |
| Data | 2026-09-08 |
| Contexto | Portal Suprimentos (`supplies`) — Minha DELPI |
| Relacionados | [ADR-002](./ADR-002-purchase-requests-api.md), [ADR-004](./ADR-004-plugin-identity-and-css-root.md), [ADR-006](./ADR-006-unit-permissions.md), [ADR-007](./ADR-007-permission-minimization.md), [PLAYBOOK-01](../PLAYBOOK-01-fronteiras-api-delpi.md) |

---

## Contexto

O domínio de Suprimentos já possui MFEs que chamam `api-delpi` direto, um bounded context Delpi para Solicitações de Compras, KPIs em Strategic Indicators e dezenas de rotas TOTVS `/supplies/*` e `/products/*`.

O produto-alvo é um portal departamental com shell único, workflows Delpi e BFF de composição. Com API própria, o MFE não pode continuar acessando `api-delpi` diretamente.

Não existe pacote `supplies-api` no monorepo. **CONFIRMADO_NO_CODIGO.**

### DRIFT-FRAMEWORK-01

Há um conflito entre fontes do repositório:

- instruções oficiais do GPT Arquiteto: backend padrão **Python + Flask**;
- APIs departamentais recentes como `commercial-api` e `purchase-requests-api`: FastAPI.

Pela precedência do projeto, **a supplies-api adotará Flask**, salvo revisão futura explícita das instruções oficiais ou ADR de autoridade superior. `commercial-api` pode ser usado como referência de Clean Architecture, composição, gateways e ownership, mas não como precedência de framework.

### DRIFT-AUTHZ-01

O JWT Keycloak não é fonte canônica da lista completa de permissions. A supplies-api deve resolver permissions efetivas pelo Core API (`/me` ou mecanismo compartilhado equivalente) antes de autorizar capabilities/unidades.

Qualquer middleware Flask compartilhado que ainda leia `claims.permissions`/`claims.is_superadmin` é referência de compatibilidade legada, não padrão para a nova API.

## Decisão

1. Criar **`supplies-api/`** em **Flask**, Clean Architecture, Postgres próprio (schema `supplies` em `postgres-plugins`), OpenAPI próprio, container Compose e `ROOT_PATH=/apps/supplies-api`.
2. O MFE `plugins/supplies` chama somente `supplies-api`. Zero `/apps/api-delpi` no browser.
3. Leituras TOTVS permanecem na `api-delpi`. A supplies-api usa gateway HTTP e não replica SQL/regra ERP.
4. Estado Minha DELPI (preferências, tasks/follow-ups, notas, settings, auditoria funcional e, após C2, estado de Solicitações) pertence à supplies-api.
5. Core API continua dona de governança: apps, permissions, grupos, favoritos e resolução efetiva de RBAC.
6. Autorização server-side segue:

```text
JWT válido
  → identidade
  → Core API /me
  → effective permissions
  → capability + unit + resource scope + business rule
```

7. Permission catalog segue ADR-007: menor conjunto suficiente; não espelhar CRUD.
8. Naming técnico novo em inglês; UI em PT-BR.

## GATE-AUTHZ

A E2 não pode prosseguir enquanto a implementação escolhida não provar:

- JWT validado corretamente;
- permissions efetivas obtidas do Core;
- `is_superadmin` não confiado a claim não canônica;
- indisponibilidade do Core tratada de forma fail-closed para autorização nova;
- testes de positivo, negativo e filial cruzada.

## Consequências

### Positivas

- fronteira clara TOTVS × produto Delpi;
- authz coerente com a constituição do projeto;
- reduz risco de drift entre APIs;
- espaço para composição e estado próprio sem inflar api-delpi.

### Custos

- coexistência temporária com MFEs legados;
- necessidade de consolidar o middleware Flask de authz antes/na E2;
- absorção progressiva de `purchase-requests-api` conforme ADR-002.

## Alternativas rejeitadas

| Alternativa | Motivo |
|---|---|
| MFE chamar api-delpi só para leitura | viola boundary do MFE com API própria |
| Workflows de Suprimentos na api-delpi | ownership incorreto |
| Portal apenas com deep links | não unifica jornada nem escopo |
| Reusar purchase-requests-api como API do Portal inteiro | SC não é dona de estoque/OTD/SI |
| Adotar FastAPI apenas por copiar commercial-api | conflita com instrução oficial vigente |
| Autorizar por claims de permission do JWT | conflita com regra Core-first |

## Plano mínimo quando autorizado

1. Scaffold Flask + `/health` + `/ready`.
2. Auth middleware Core-first + testes de autorização.
3. Envelope e tratamento padronizado de erros.
4. Gateway api-delpi com timeout e caller.
5. Primeiro BFF somente após `GATE-AUTHZ` verde.
6. Estado Delpi depois dos contratos de leitura básicos.

## Referências

- instruções oficiais: `documentos/instrucoes_oficiais_gpt_arquiteto_delpi_central.md`
- regras: `mfe-own-api-no-direct-api-delpi.mdc`, `application-bounded-context-decoupling.mdc`
- referência arquitetural (não de framework): `commercial-api/`
