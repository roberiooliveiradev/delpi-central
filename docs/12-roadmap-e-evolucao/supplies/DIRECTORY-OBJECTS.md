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

| Objeto | Coleção já placeholder | Ficha reservada |
|---|---|---|
| Fornecedor (TOTVS A2) | `/apps/supplies/suppliers` | `/apps/supplies/suppliers/:code/:store` (loja omitida só se o dado não vier) |
| Pessoa (solicitante / comprador) | — | `/apps/supplies/people/:code` |

Helpers: `reservedSupplierDetailPath` e `reservedPersonDetailPath` em `plugins/supplies/src/app/suppliesDirectory.ts`.

`/apps/supplies/suppliers/:code/:store` e `/apps/supplies/people/:code` devem continuar `not_found` até a página existir. A fila de produto em `README.md` já reserva o 360 do fornecedor; pessoa ainda não tinha path — este documento o congela.

## Quando as fichas existirem

1. Registrar view + rota canônica.
2. Ligar `href` + `title` no `EntityAvatarLabel` (não inventar destino antes).
3. Atualizar Manual, tooltips e este documento no mesmo entregável.
4. Não criar permission nova só para “ver avatar”.

## Fora de escopo deste entregável

- Página 360 de fornecedor ou pessoa
- Upload de foto
- Chamada a api-delpi ou purchase-requests-api a partir do MFE
