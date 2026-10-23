# PR.IDENTITY.S4 — Portal-wide Person Identity Consistency

**Data:** 2026-10-23 · **Owner da correção:** `supplies-api`
(`RequesterIdentityService`) · **Status:** PASS

## Sintoma comprovado

`/apps/supplies/purchase-requests/01/178764` — o hero da ficha exibia
`ELAINE` (nome TOTVS) enquanto a listagem da mesma SC já mostrava o nome
oficial Minha DELPI (`Elaine Gracielle Gracielle Romig`).

## Causa-raiz

O payload real do detalhe é `{header: {requester: {...}}, lines: [...],
timeline: [...]}`. O iterador `_requester_refs` do
`RequesterIdentityService` só coletava `payload["requester"]` (topo),
`items[].requester` e `lines[].requester` — **`payload["header"]["requester"]`
nunca era enriquecido**. O MFE caía corretamente no fallback `name` (TOTVS)
e o `photo_url` também ficava ausente.

O teste existente (`test_detail_payload_enriches_header_and_lines`)
usava o shape errado (`requester` no topo), por isso a regressão passou.

## Correção (menor diff no owner)

`supplies-api/app/application/services/requester_identity_service.py`:
`_requester_refs` passa a descer em `payload["header"]["requester"]` —
com isso o header recebe `display_name` + `photo_url` pelo mesmo fluxo
determinístico `protheus_user_id` → `user_protheus_identities(mapped)` →
directory. Nenhuma nova autoridade de identidade; nenhuma mudança de
contrato (campos já existiam em `PersonRef`). Nenhuma mudança no MFE —
`SuppliesPersonIdentity` já implementa `display_name → name → code` e
foto/iniciais.

## Matriz de inventário (páginas implementadas)

| Página | Campo | Componente | Identificador origem | Estado |
|---|---|---|---|---|
| SC lista (tabela) | Solicitante | `SuppliesPersonIdentity` | `requester.protheus_user_id` (`C1_USER`) | `CORE_RESOLVED` (S1–S3) |
| SC cards | Solicitante | `SuppliesPersonIdentity` | idem | `CORE_RESOLVED` |
| SC detalhe (hero) | Solicitante | `SuppliesPersonIdentity` | `header.requester.protheus_user_id` | **`MISSING_ENRICHMENT` → corrigido** |
| SC detalhe (linhas) | requester | não renderizado | `lines[].requester` | já enriquecido no payload |
| SC facet | Solicitante (filtro) | seletor | `protheus_user_id` | `CORE_RESOLVED` |
| SC export CSV | `requester` | arquivo | `name` (origem) | `SOURCE_FALLBACK` — residual documentado (export preserva dado de origem; enriquecer CSV ficou fora de escopo) |
| Pedido detalhe | Comprador | `SuppliesPersonIdentity` | `buyer_code` = `C7_COMPRA` | **`UNMAPPED`** — evidência DB: valores `003/004/007/011/022` não existem em `SYS_USR` (`USR_ID`/`USR_CODIGO`); cadastro separado de compradores, sem vínculo comprovado → não resolver por nome |
| Pedido lista | — | sem coluna de pessoa | — | n/a |
| SC detalhe linhas→orders | `order_user` (`C7_USER`) | não renderizado | `protheus_user_id` (`SYS_USR`) | em contrato (`purchase_orders[].order_user`), sem exibição — residual |
| `approval.approver_name` | aprovador | texto | sem identificador técnico | `UNMAPPED` — só nome TOTVS, sem `protheus_user_id` → bloqueado por regra anti-fuzzy |
| TopBar / UserProfile | avatar+nome próprio | `useMyPersonProfile` | self `user_id` Core | `CORE_RESOLVED` (self) |
| Fornecedores | `responsible_name` | campo texto | contato do fornecedor | `NOT_PERSON_IDENTITY` |
| Deliveries / Overview / Home / Inventory / Analytics / Users | — | — | — | `NOT_PERSON_IDENTITY` (sem campos de pessoa) |

**Sem matching por nome:** onde não há identificador técnico (`C7_COMPRA`,
`approver_name`), o texto de origem permanece e o caso fica classificado —
nenhuma identidade foi inferida.

## Segurança das fotos

`RequesterPhotoScopeGuard` preservado: foto só é servida quando o
`protheus_user_id` pertence ao facet `/requesters` autorizado do caller
para a mesma query branch+período (fail-closed, cache 120s por
token+query). A ficha passa `photoPeriod={issue_date}` + `allowedUnits` —
o requester da SC pertence ao universo autorizado por construção.
UUID Core e token S2S nunca saem do backend.

## Performance

Detalhe: +0 consultas extras — o mesmo batch `lookup` já cobria
`lines[].requester`; `header.requester` apenas entra no conjunto
deduplicado de ids. Sem N+1; Core indisponível → fallback honesto.

## Testes

- `test_detail_payload_enriches_header_and_lines` agora usa o shape real
  `{header:{requester}}` (regressão do bug) + novos
  `test_detail_header_requester_gets_photo_url` e
  `test_legacy_top_level_requester_still_enriched` (sibling).
- Novo `test_detail_enriches_header_requester_via_identity_service` (rota
  BFF: payload do detalhe passa pelo enrich e devolve `display_name`).
- Structural guard MFE: hero deve receber `person={header?.requester}` e
  nunca `header?.requester?.name|display_name` literal.
- supplies-api identity + BFF: **36/36** · MFE purchase-requests: 20/20.

## Evidência live (container deployado)

`enrich_payload` executado no `delpi-supplies-api` prod
(`sha256:6a7d25694898`) com shape real `{header:{requester},lines}` e
Core S2S real: `header.requester` recebeu
`photo_url=/purchase-requests/requesters/000007/photo` (Fabiano, mapeado
+ foto) — prova de que o header entra no conjunto do enrich; o
`display_name` segue o mesmo batch já comprovado na listagem.

`VISUAL_AUTHENTICATED = INCONCLUSIVE` — token de usuário portal expirado
e o mint exige credencial interativa; o `user` de teste do realm não é
usuário Core (`/me` → invalid_token).

## Residuais

- `VISUAL_AUTHENTICATED = INCONCLUSIVE` (sem navegador autenticado).
- Comprador (`C7_COMPRA`) e aprovador sem vínculo comprovado — exibem dado
  de origem; resolver exigiria contrato novo (cadastro de compradores ↔
  usuários) no owner api-delpi/Core.
- CSV de exportação preserva `requester.name` de origem (decisão, não bug).
- `order_user` (`C7_USER`) presente no contrato do detalhe mas ainda não
  exibido no MFE — quando a ficha renderizar criador do pedido, o mesmo
  `PersonRef`/`enrich` já se aplica.


## Revisão GPT — PR.IDENTITY.S4 (2026-10-23)

**Veredito:** `ACCEPT_WITH_RESIDUAL` para código e deploy técnico reportado; `VISUAL_AUTHENTICATED=INCONCLUSIVE`. Conferidos no source `97587080b9` o `RequesterIdentityService` e a documentação de execução. A causa-raiz é consistente com o código: `_requester_refs` percorria `requester` top-level, `items[]`, `lines[]`, mas não `header.requester`. O diff inclui agora `payload.get("header")` e `detail_header["requester"]` no **mesmo** batch, sem nova consulta por linha, sem mudança de DTO e sem matching textual. O fluxo `display_name → name → code` no MFE foi mantido.

**Evidências do executor, não reexecutadas pelo GPT:** supplies-api 36/36 testes, MFE 20/20, deploy `delpi-supplies-api` imagem `sha256:6a7d25694898` healthy; `enrich_payload` em container produtivo retornou `photo_url` em um header de caso mapeado. **Isso não equivale a um GET autenticado da ficha SC 01/178764 nem prova independente de `display_name` nela**. O smoke pela rota humana permaneceu `INCONCLUSIVE` por ausência de credencial autenticada válida. Não chamar o gate visual da ficha de PASS.

**Inventário e limites corretos:** SC lista/cards/detalhe/facet resolvíveis por `C1_USER`; `C7_COMPRA` é código de cadastro de compradores, não um `SYS_USR` comprovado, e `approver_name` carece de identificador — ficam `UNMAPPED` sem fuzzy matching. Export CSV preserva nome fonte (residual explícito). `RequesterPhotoScopeGuard` continua fail-closed por identidade mapeada e universo autorizado; ainda é necessário smoke autenticado de foto na ficha real. 

**Estado:** `S4_CODE=ACCEPT_WITH_RESIDUAL`; `S4_DEPLOY=PASS (executor-reported)`; `SC_178764_AUTHENTICATED_RUNTIME=INCONCLUSIVE`; `S4_VISUAL=INCONCLUSIVE`. Próxima verificação PO: abrir `/apps/supplies/purchase-requests/01/178764`, confirmar nome oficial Minha DELPI no hero e foto/iniciais corretas. Nenhuma mudança na frente de fornecedores `X4.PROD-C1`.
