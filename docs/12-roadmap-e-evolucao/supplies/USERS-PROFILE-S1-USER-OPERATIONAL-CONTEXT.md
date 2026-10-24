# USERS.PROFILE.S1 — Ficha do usuário Minha DELPI + navegação contextual por avatar

Status: **CONCLUÍDO (ACCEPT_WITH_RESIDUAL)** · Escopo: Portal Suprimentos (`plugins/supplies` + `supplies-api`) · Sem escrita ERP, sem permission nova, sem segundo cadastro de usuários.

## Decisão arquitetural — reúso de ficha existente

A Minha DELPI já possui ficha de perfil de usuário implementada pelo kit (`createDashboardPortalUserProfilePage`) e servida pela rota federada `/apps/supplies/users/:userId` (view `user_profile`), composta pelo BFF `supplies-api` (`UserProfileService`, política **self|admin** via `_assert_can_view`). **Decisão: reutilizar a ficha existente** — nenhuma página nova criada. O path reservado `/apps/supplies/people/:code` (`DIRECTORY-OBJECTS.md`) foi **descartado**: a chave canônica é o `user_id` opaco da Core, nunca código TOTVS.

## Inventário Core (P0)

| Item | Fonte | Estado |
|---|---|---|
| `user_id` canônico + nome oficial + foto | Core `/me/person-profile` + `integrations/person-profiles/:id[/photo]` (S2S) | comprovado (PR.IDENTITY.S1–S3) |
| Vínculo Core↔TOTVS | `POST integrations/protheus-identities/lookup` — aceita `protheus_user_ids` **e** `user_ids` (bidirecional, `mapping_status=="mapped"`) | comprovado; gateway do BFF generalizado para `user_ids` |
| Consulta de perfil de terceiros | `supplies-api` `GET /users/:id/profile` — `can_enter_shell` + `_assert_can_view` (self ou `supplies.manage`) | já existia; reusada |
| Tarefas de terceiros | **sem contrato** de consulta | `BLOCKED` — seção não implementada (não expor tarefas privadas) |
| Pedidos por papel (criador/comprador/aprovador) | `C7_COMPRA` sem vínculo SYS_USR comprovado (PR.IDENTITY.S4); `order_user` sem filtro de listagem | `RESIDUAL` — seção não implementada |

## Contratos novos (supplies-api, backward-compatible)

| Rota | Policy | Semântica |
|---|---|---|
| `GET /users/:user_id/related-requests` | `can_use_operations` + `_assert_can_view` | SCs cujo requester ∈ `protheus_user_id` mapeados do **target** (Core lookup `user_ids` → `requester_user_id` na purchase-requests-api); filtro `branch` opcional — validado por `require_units` **somente quando fornecido** (fail-closed); `page`/`page_size` (máx 20); degrade parcial `{error:"related_requests_unavailable"}`; `requester_unmapped:true` sem vínculo |
| `GET /users/:user_id/photo` | `can_use_operations` + `_assert_can_view` | Proxy S2S dos bytes da foto Core — `Cache-Control: private`, 404 quando ausente; UUID/token nunca saem do backend |

`RequesterIdentityService` agora projeta `user_id` no `PersonRef` enriquecido (campo aditivo) — é o identificador opaco que habilita o link.

## Navegação contextual (MFE)

`SuppliesPersonIdentity` ganhou `basePath` opt-in (mesmo padrão de `SuppliesSupplierIdentity`/S1): com `person.user_id` + `canAccessUserProfile(target, session)` (self ou manage) envolve avatar+nome em `SuppliesEntityLink` → `buildUserProfileHref` → `navigatePluginPath`, `title="Abrir perfil de {nome}"`. Sem `user_id`/sem acesso → identidade informativa, **sem link falso**. Consumidores: lista, cards e detalhe de SC + detalhe de PC. Helpers reservados mortos (`reservedSupplierDetailPath`/`reservedPersonDetailPath`) removidos; `buildSelfProfileHref` movido para `features/users/userProfileNavigation.ts` (builder não-componente).

## Seção «Solicitações de compra relacionadas» (hero 7.1)

Lista paginada (5/pág, máx 20) na ficha do usuário: número da SC (`buildPurchaseRequestDetailPath`), data, situação, unidade; enriquecida com `display_name`/`photo_url` pelo mesmo `RequesterIdentityService` (sem N+1 — batch único deduplicado). «Ver todas» abre `/purchase-requests?requester_user_id=<pid>` — filtro já existente da lista. Estados: loading / empty (`requester_unmapped` ou zero) / error (degrade parcial) / forbidden. Tarefas e Pedidos **não** renderizados (residual documentado).

## Segurança

- AuthZ exclusivamente backend: `_assert_can_view` (self|admin) reutilizado — **nenhuma permission nova**; `require_units` aplicado apenas a filtro não-vazio (bug do empty-list corrigido: `require_units` rejeita `[]` e o filtro é opcional).
- Frontend nunca decide: `canAccessUserProfile` só controla affordance do link; a ficha e a seção respondem 403/404 do BFF.
- Foto: bytes Core via S2S no BFF — sem expor `person-profiles` interno nem token.
- Minimização: seção retorna apenas campos da SC (número/data/status/unidade/requester) — e-mail/telefone/atributos Core não expostos.

## Testes / evidência

- `supplies-api`: **452 pass** (+191 linhas em `test_user_profile.py`): related-requests self/admin/403, filtro vazio/filial autorizada/não autorizada, unmapped→empty, foto 200/404/403, `user_ids` lookup.
- MFE: **391 pass** — guards estruturais novos: `SuppliesPersonIdentity` só navega via `buildUserProfileHref`+`SuppliesEntityLink` gated por `user_id`+`canAccessUserProfile` (nunca nome/`useNavigate`/`window.location`); consumidores exigem `basePath`; rotas `/users/u-1`→`user_profile`, `/people/:code`→`not_found`.
- `tsc -b` limpo · lint escopado 0 erros (1 warning `set-state-in-effect` preexistente em `UserProfilePage`) · `vite build` OK.
- `VISUAL_AUTHENTICATED = INCONCLUSIVE` — validado por contrato+testes+bundle.

## Residual / NEXT

- Tarefas e Pedidos por papel: aguardam contrato de tarefas (Core) e vínculo/filtro de criador-comprador nos producers.
- Comprador `C7_COMPRA`/aprovador seguem sem vínculo Core (PR.IDENTITY.S4) — identidade informativa preservada.
- Smoke visual autenticado pendente (clicar no solicitante de uma SC → ficha `/users/:userId` com seção de SCs relacionadas).

## Rollback

`git revert <sha>` + redeploy `supplies` e `supplies-api` (`infra/scripts/up-prod-sequential.sh --build`). Sem migração, sem flag, sem contrato removido.


## Revisão GPT — USERS.PROFILE.S1 (2026-10-23)

**Veredito:** `ACCEPT_WITH_RESIDUAL` (código e contrato), `DEPLOY=PASS (executor-reported)`, `VISUAL_AUTHENTICATED=INCONCLUSIVE`. Inspecionados no GitHub o `UserProfileService` do source `ca4dd130c8` e este documento. Reúso da ficha `/users/:userId` e composição `user_id → mapped protheus_user_id → requester_user_id` são coerentes com os owners Core e Purchase Requests; nada autoriza uma segunda base de usuários. Testes (BFF 452, MFE 390 no relatório / 391 no documento — **reconciliar contagem**) e deploy/imagens são relatados pelo executor, não reexecutados nesta revisão.

**Ressalva de produto/autorização:** `_assert_can_view` restringe o perfil a `self|admin`, e `canAccessUserProfile` apenas espelha essa condição na navegação. Portanto links no avatar/nome **não estarão ativos para perfis de terceiros quando o caller não possuir permissão de administração**. Isso preserva segurança, mas a navegação universal para colegas NÃO está entregue; exigir decisão PO/Core sobre política de perfil público profissional, sem reutilizar `supplies.manage` como autorização geral para ver informações privadas. Mesmo administrador continua sujeito à minimização, e informação profissional pública deve ser separada de preferências e contatos privados, se uma futura política for autorizada.

**Foco adicional de verificação:** o `UserProfileService.related_purchase_requests` valida `branches` apenas quando filtro explícito é fornecido, delegando o recorte padrão à AuthZ server-side do `purchase-requests-api`; confirmar por smoke autenticado e teste negativo que omitir `branch` nunca amplia o universo de SCs. `requester_unmapped` não deve ocultar falhas reais da Core como ausência definitiva de vínculo; distinguir degradação do lookup de lista vazia quando possível. A seção não autoriza consulta de tarefas privadas ou associação de `C7_COMPRA` por nome.

**Evidência runtime ainda pendente:** abrir ficha de perfil próprio e, com caller autorizado, de terceiro; verificar foto, `related-requests` paginadas e `Ver todas` com filtro, URL/F5, 403 de terceiro para caller comum, unidade e período; sem navegador autenticado, `INCONCLUSIVE`. **Estado formal:** `USERS.PROFILE.S1=ACCEPT_WITH_RESIDUAL`; sem mudança nos gates de escrita ERP e no cutover de fornecedores.
