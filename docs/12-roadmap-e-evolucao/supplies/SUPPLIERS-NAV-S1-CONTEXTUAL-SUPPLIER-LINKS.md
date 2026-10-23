# SUPPLIERS.NAV.S1 — Navegação contextual para a ficha do fornecedor (E14)

**Status:** CONCLUÍDO · **Data:** 2026-10-24 · **Executor:** Devin

## Objetivo

Permitir abrir a ficha cadastral do fornecedor (E14) clicando no avatar ou no
nome do fornecedor nas páginas operacionais implementadas, usando a identidade
exata `(supplier_code, supplier_store)` — sem criar página nova, sem alterar a
API de cadastro/edição e sem lógica de URL duplicada por página.

## Contrato de navegação

- **Destino canônico:** `buildSupplierDetailPath(code, store, basePath)` →
  `/apps/supplies/suppliers/{supplier_code}/{supplier_store}` (view
  `supplier_detail`, parser `^suppliers\/(\d{1,6})\/(\d{1,2})$`).
- **Condição obrigatória:** link só é renderizado quando `basePath`, `code` e
  `store` estão presentes e não vazios. Código ou loja ausentes → identidade
  permanece informativa (sem link).
- **Proibidos e ausentes no diff:** navegação por nome/razão social, CNPJ como
  chave, busca aproximada, primeira loja, loja `01` presumida, identificador de
  outro contexto, `window.location`, `useNavigate` ad hoc.

## Componente central

`SuppliesSupplierIdentity` (`plugins/supplies/src/app/SuppliesDirectoryIdentity.tsx`)
ganhou a prop opcional `basePath`. Com `basePath` + `code` + `store`, o avatar
e o nome viram **uma única área de navegação** via `SuppliesEntityLink`
(`InlineNavLink` do kit — safe-href, clique SPA, `stopPropagation` nativo para
não disparar o clique da linha) + `navigatePluginPath` (história/f5/voltar
preservados). Sem `basePath` ou sem identidade completa → renderização inalterada.

- Acessibilidade: `<a>` real (foco por Tab, Enter ativa), `title` =
  `Abrir cadastro do fornecedor {nome}` (tooltip + aria-label default),
  `focus-visible` com outline accent; hover sublinha o nome.
- Visual preservado: mesmas iniciais/nome/código, sem underline no bloco;
  cursor pointer só onde há link.

## Inventário de ocorrências

| Página | Campo | Identidade no contrato | Estado |
|---|---|---|---|
| Pedidos de Compra — lista | `supplier` | `supplier_code` + `supplier_store` + `supplier_name` (SC7→SA2) | `NAVIGABLE` ✅ |
| Pedidos de Compra — cards | `supplier` | idem | `NAVIGABLE` ✅ |
| Pedidos de Compra — detalhe (itens) | `supplier` | `supplier_code` + `supplier_store` + `supplier_name` | `NAVIGABLE` ✅ |
| Entregas / Atrasos — lista | `supplier` | `supplier_code` + `supplier_store` + `supplier_name`/`supplier_short_name` | `NAVIGABLE` ✅ |
| Pedidos de Compra — filtros | `supplier_code` | input de busca textual — não é exibição de identidade | `NOT_SUPPLIER` |
| Fornecedores — lista (E13) | linha | clique da linha já navega (existe) | `NAVIGABLE` (pré-existente) |
| Solicitações de Compras | — | contrato SC não carrega fornecedor | sem ocorrência |
| Overview/Analytics/Home/Estoque | — | nenhum campo de fornecedor renderizado | sem ocorrência |
| Negociações | — | página não implementada | sem ocorrência |

**Páginas sem loja no contrato:** nenhuma — todos os consumidores de identidade
já trazem `supplier_store` projetado pelo owner (`api-delpi`). Nenhuma correção
de BFF/produtor foi necessária.

## Permissões

- Os 4 consumidores e a E14 compartilham a mesma política BFF
  `can_use_operations` (`supplies.access`) — quem vê a identidade já tem acesso
  à ficha; o backend continua sendo a autoridade (403/404 no destino).
- Nenhuma permission nova; edição permanece nos gates E14 existentes; flags de
  escrita Protheus intocadas.

## Arquivos alterados

- `plugins/supplies/src/app/SuppliesDirectoryIdentity.tsx` — prop `basePath`,
  navegação centralizada.
- `plugins/supplies/src/index.css` — `.sp-supplier-identity-link` (cursor,
  hover no nome, focus-visible).
- `plugins/supplies/src/features/purchase-orders/PurchaseOrdersListTable.tsx`,
  `PurchaseOrdersCards.tsx`, `PurchaseOrderDetailPage.tsx` — `basePath` no
  `SuppliesSupplierIdentity`.
- `plugins/supplies/src/features/deliveries/DeliveriesListTable.tsx` — nova
  prop `basePath`; `DeliveriesPage.tsx` — repasse.
- `plugins/supplies/src/app/suppliesDirectory.test.ts` — guard atualizado:
  navegação só via contrato canônico + wiring dos 4 consumidores.
- `plugins/supplies/src/content/userManualContent.ts` — manual/FAQ
  sincronizados.

## Testes e gates

- supplies MFE: **389/389** (`vitest run`), incluindo guards estruturais novos.
- `tsc -b` limpo; `vite build` OK.
- Casos cobertos por contrato/rota: zeros à esquerda (`001234/01`),
  lojas diferentes para mesmo código (chave composta), não-numérico rejeitado
  (`resolvePluginRoute` → `not_found`), sem loja → sem link (guard estrutural).
- `VISUAL_AUTHENTICATED = INCONCLUSIVE` — sem navegador autenticado; validado
  por contrato + testes estruturais + bundle.

## Residual

- Ficha de pessoa continua reservada (`reservedPersonDetailPath` inativa) —
  avatar de solicitante não navega, conforme manual.
- Registro inexistente/não autorizado no destino é tratado pela E14 (404/403).
