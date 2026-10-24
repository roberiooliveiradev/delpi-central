# Objetos de diretório — fornecedor e pessoa

Contrato de produto para identidade visual e rotas **reservadas**. Não autoriza implementar as fichas agora.

## O que já existe

Fornecedor (pedido) e pessoa (solicitante / comprador) aparecem com **avatar de iniciais + nome**, no mesmo padrão visual do Portal Comercial.

| Superfície | Componente |
|---|---|
| Chrome | `@delpi/plugin-ui` `EntityAvatarLabel` / `createDashboardEntityAvatarLabel` |
| Consumidor | `SuppliesSupplierIdentity` / `SuppliesPersonIdentity` |
| Listas / cards / fichas | Pedidos de compra e Solicitações de compras |

O MFE **não** baixa foto e **não** coloca `href`. Não copiar CSS de avatar no plugin.

## Rotas reservadas (TARGET)

Paths em inglês (`english-code-identifiers.mdc`). Ainda **não** entram no router, no catálogo do hub nem no Manual como destino clicável.

| Objeto | Coleção já placeholder | Ficha |
|---|---|---|
| Fornecedor (TOTVS A2) | `/apps/supplies/suppliers` | `/apps/supplies/suppliers/:code/:store` ✅ implementada (E14) |
| Pessoa (usuário Minha DELPI) | — | `/apps/supplies/users/:userId` ✅ implementada (USERS.PROFILE.S1 — reusa a ficha de perfil do Portal; `/people/:code` descartada: chave canônica é `user_id` Core, nunca código TOTVS) |

Builders canônicos: `buildSupplierDetailPath` e `buildUserProfileHref` em `plugins/supplies/src/app/pluginRoutes.ts` (os helpers `reserved*` foram removidos no USERS.PROFILE.S1 — código morto superado pelas rotas reais).

`/apps/supplies/people/:code` continua `not_found` e não será implementada — a ficha de pessoa é a rota canônica `/users/:userId`, com navegação condicionada a `user_id` Core comprovado + `canAccessUserProfile`.

## Quando as fichas existirem

1. Registrar view + rota canônica.
2. Ligar `href` + `title` no `EntityAvatarLabel` (não inventar destino antes).
3. Atualizar Manual, tooltips e este documento no mesmo entregável.
4. Não criar permission nova só para “ver avatar”.

## Fora de escopo deste entregável

- Página 360 de fornecedor ou pessoa
- Upload de foto
- Chamada a api-delpi ou purchase-requests-api a partir do MFE
