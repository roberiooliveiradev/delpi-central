# USERS.PROFILE.S3 — Tabela real de Solicitações na ficha do usuário

Status: **EXECUTADO** (deploy canônico)

## Objetivo

Substituir a listinha simplificada da seção «Solicitações de compras» da ficha
(`/apps/supplies/users/:userId`) pela **mesma** `PurchaseRequestsListTable` da
página `/apps/supplies/purchase-requests` — reuso real de componente, contrato,
colunas, ordenação e paginação; não uma tabela parecida.

## Inventário (evidência)

- `PurchaseRequestsListTable` (`features/purchase-requests/PurchaseRequestsListTable.tsx`)
  já era um componente desacoplado por props:
  `items`, `query`, `total`, `loading`, `canExport`, `basePath`,
  `onExport`, `onPatchQuery`, `onSelectRow`.
  Inclui toolbar (modo tabela/cards, visibilidade de colunas, tamanho de fonte,
  exportação condicional), `SuppliesDataTable`, `PurchaseRequestsCards` e
  `SuppliesCompactPagination` — nenhuma extração necessária.
- Consumidor existente: `PurchaseRequestsPage` (listagem principal).

## Reconciliação do grão dos dados — sem adaptador

O endpoint BFF `GET /users/:id/related-requests` devolve
`items: PurchaseRequestListItem[]` no **mesmo grão** da listagem principal
(linha de item: `branch`, `request_number`, `request_item`, `product_code`,
`product_description`, `requester` enriquecido com `user_id`/`photo`,
`cost_center`, `request_issue_date`, `derived.overall_stage`) — porque é o
mesmo payload do produtor, já enriquecido pelo `RequesterIdentityService`.

`total` tem a mesma semântica da listagem (itens do universo autorizado);
não há confusão entre total de SCs e total de linhas porque o contrato é
idêntico. Nenhuma coluna foi preenchida com valor inventado.

## Implementação

- `UserProfilePage` mantém `relatedQuery: PurchaseRequestsQuery` local
  (`page_size` inicial 25, `sort_by: "issue_date"`, `sort_dir: "desc"`) e
  passa-a à tabela via `query` + `onPatchQuery` → refetch server-side.
- `canExport={false}` — a ficha não ganha exportação própria (sem contrato de
  export por solicitante); o botão some por contrato do próprio componente.
- `onSelectRow` → `navigatePluginPath(buildPurchaseRequestDetailPath(...))`,
  igual à página principal.
- Estados de seção preservados: loading inicial, `error` (incl.
  `identity_lookup_unavailable`) + retry, `requester_unmapped`, empty;
  `loading` contínuo vai para a prop da tabela.
- «Ver todas as solicitações (total)» preservado com `requester_user_id` +
  `date_from` explícitos.
- BFF: `sort_by`/`sort_dir` viraram passthrough do cliente (o produtor possui
  a allowlist e rejeita chave inválida — degrade, nunca exceção solta).
- `_RELATED_REQUESTS_MAX_PAGE_SIZE`: 20 → **100**, alinhado às opções reais de
  paginação da tabela (25/50/100) e abaixo do teto do produtor (200).
- CSS morto removido (`sp-user-profile__related*`) — nenhum CSS novo
  (a tabela traz o visual canônico).
- Preferências de layout/colunas/fonte compartilham as mesmas storage keys da
  listagem — comportamento consistente entre as duas superfícies.

## AuthZ / segurança

- Política `self|admin` (`_assert_can_view`) e `can_use_operations` intactas.
- Escopo de unidades inalterado: filtro `branch` explícito validado por
  `require_units`; universo default = `allowed_units` do ator — nunca amplia.
- Frontend controla apenas affordances; autorização permanece server-side.

## Performance

Sem N+1: 1 lookup Core + 1 listagem paginada (máx. 100, sort server-side) +
1 enrich batch. Paginação server-side — as ~1.070 linhas nunca trafegam.
Seção carrega independente do restante da ficha.

## Testes

- BFF `tests/application/test_user_profile.py`: +1 teste
  (`test_related_client_sort_passthrough`) — sort do cliente chega ao
  produtor. Suíte supplies-api: **481 passed** (+21 skipped pré-existentes).
- MFE `UserProfile.structural.test.ts`: +1 guard de reuso real — exige
  `PurchaseRequestsListTable` com `onPatchQuery`/`onSelectRow`/`canExport=false`
  e proíbe a listinha própria (`sp-user-profile__related*`).
- Suíte MFE: **391 passed** · `tsc -b` limpo · `build` OK.
- Lint: 0 problemas novos (32 problemas pré-existentes em `origin/main`,
  não relacionados — medido com o diff stasheado).

## Regressão

A listagem principal não recebeu nenhum diff — o componente foi consumido,
não modificado. Filtros, exportação, cards, ordenação e paginação da página
permanecem no mesmo código de antes.

## Deploy

- Commit: ver log (`feat(profile): USERS.PROFILE.S3 — tabela real de SC na ficha`).
- Serviços: `delpi-supplies` + `delpi-supplies-api`.
- Rollback: `git revert` + redeploy dos dois serviços.

## Residuais

- `VISUAL_AUTHENTICATED = INCONCLUSIVE` — validação visual com sessão
  autenticada pendente (browser).
- Exportar as SCs relacionadas a partir da ficha permanece sem contrato —
  a ação de exportação da seção intencionalmente fica oculta.


## Revisão GPT — USERS.PROFILE.S3 (2026-10-23)

**Veredito: `ACCEPT_WITH_RESIDUAL`** para implementação e contrato; `DEPLOY=PASS (executor-reported)`; `VISUAL_AUTHENTICATED=INCONCLUSIVE`. Inspecionados no GitHub (source `0c6ac0ffcd`) o documento S3, `PurchaseRequestsListTable.tsx` e `UserProfileService`. O componente de tabela já aceita `items/query/total/loading/canExport/basePath/onExport/onPatchQuery/onSelectRow` por props; a documentação relata reuso sem extração ou duplicação visual. O BFF aceita paginação até 100 e `sort_by/sort_dir` via allowlist do producer; o recorte de unidades autorizado e `self|admin` permanecem no serviço.

**Evidência do executor, sem reexecução independente pelo GPT:** BFF 481 PASS/21 SKIP, MFE 391 PASS, typecheck/build PASS, deploy `supplies-api` imagem `67ad9c895f1d` e `supplies` `289c0c45d5e2`, bundle `App-SSmBJjdj.js`. Apenas smoke anônimo 401 e health foram realizados; faltam teste visual autenticado e prova da paginação, sort, tabela/cards e navegação na ficha real. O resultado global não é PASS de runtime completo.

**Residual mantido do S2, confirmado novamente no source S3:** `related_purchase_requests` ainda extrai `items/total` sem checar explicitamente `data.error` quando o producer devolve erro num envelope JSON com HTTP 200; se esse formato for possível, pode aparecer vazio falso. Inventariar o envelope real e adicionar regressão/fail-closed sem ampliar escopo da tarefa visual. **Residual de UX compartilhada:** a tabela reutiliza as mesmas chaves de preferência de layout/colunas/fonte da listagem; testar se alterações na ficha afetando preferências da lista são comportamento intencional. **Cuidado semântico:** embora o documento use 'SCs', o `total` provém de linhas de itens (`PurchaseRequestListItem`); o rótulo exibido não deve sugerir quantidade de cabeçalhos distintos sem prova.

**Estado formal:** `S3_CODE=ACCEPT_WITH_RESIDUAL`, `S3_DEPLOY=PASS (executor-reported)`, `S3_VISUAL=INCONCLUSIVE`; próximo passo: PO validar na ficha da Elaine SC 178764, componentes e paginação/ordenação, além de link Ver todas com filtro correto.
