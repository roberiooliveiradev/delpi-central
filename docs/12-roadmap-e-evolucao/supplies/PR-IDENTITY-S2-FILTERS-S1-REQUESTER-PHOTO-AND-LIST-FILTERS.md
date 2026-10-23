# PR.IDENTITY.S2 + PR.FILTERS.S1 — Foto real, nome TOTVS secundário e filtros da lista

**Data:** 2026-10-23 · **Status:** PROVEN · **Página:** Solicitações de Compras (`/apps/supplies/purchase-requests`)

Continuação de [PR-IDENTITY-S1-REQUESTER-CORE-RESOLUTION.md](./PR-IDENTITY-S1-REQUESTER-CORE-RESOLUTION.md).

## PR.IDENTITY.S2 — Identidade visual do solicitante

### Layout da identidade

```text
[Foto|Iniciais]  Nome oficial Minha DELPI     ← display_name (principal)
                 ELAINE                        ← requester.name TOTVS (secundário)
```

- **Principal:** `display_name` (Core) → `name` (origem) → `code`.
- **Secundário:** quando `display_name` resolveu, o **nome TOTVS de origem** (`requester.name`) quando diferente do oficial; caso contrário `code` — nunca duplica.
- **Foto:** `requester.photo_url` (caminho BFF) → blob autenticado → object URL → `src` do `EntityAvatarLabel`. Sem foto/erro → iniciais do nome exibido.
- Componente `SuppliesPersonIdentity` compartilhado cobre tabela, cards e ficha.

### Cadeia da fotografia (tudo contrato existente)

```text
requester.protheus_user_id
  → POST /integrations/protheus-identities/lookup   (S2S, mapped)
  → POST /integrations/person-profiles/lookup        (S2S, batch ≤50, has_photo)
  → requester.photo_url = /purchase-requests/requesters/{pid}/photo   (BFF)

GET /purchase-requests/requesters/{protheus_user_id}/photo   (BFF proxy)
  → resolve pid → user_id (mapped only) server-side
  → GET /integrations/person-profiles/{user_id}/photo (S2S bytes)
  → stream com content-type; Cache-Control: private, max-age=300; 404 → iniciais
```

- O UUID da Core e o token S2S **nunca** chegam ao browser — a URL da foto é chaveada por `protheus_user_id` (mesmo identificador já exposto).
- `usePersonPhoto` deduplica fetches por `photo_url` em cache de sessão (várias linhas → um fetch por pessoa).
- Não é possível pedir foto de um `protheus_user_id` não mapeado — resolução falha → 404.

### Comportamentos

| Cenário | Resultado |
|---|---|
| Mapeado + foto | foto real + nome oficial + TOTVS abaixo |
| Mapeado + sem foto | iniciais do nome oficial + TOTVS abaixo |
| Não mapeado | iniciais do nome origem + código abaixo |
| Foto 403/404/timeout | fallback iniciais, lista intacta |
| Core indisponível | nomes/fotos ausentes, listagem intacta (soft-fail) |

## PR.FILTERS.S1 — Filtros da listagem

### Inventário (comprovado no HEAD)

| Filtro | Param URL/API | Semântica no produtor | Estado |
|---|---|---|---|
| Unidade | `branch` (rep) | `C1_FILIAL` + units Core | já existia |
| Número SC | `request_number` | `C1_NUM = ?` **exato** (zeros preservados) | já existia |
| Produto | `product_code` | `C1_PRODUTO = ?` **exato, código apenas** | já existia |
| Situação | `overall_stage` (rep) | estágio derivado owner PR-api | já existia |
| Período | `date_from`/`date_to` | `C1_EMISSAO` = **abertura/emissão** ✓ | já existia |
| **Solicitante** | `requester_user_id` (rep) | `C1_USER IN (...)` | **implementado** |
| **Centro de custo** | `cost_center` (rep) | `C1_CC IN (...)` | **implementado** |

O parâmetro `requester_user_id` aceita **`protheus_user_id`** (o PR-api encaminha como `requester_protheus_user_id` ao api-delpi) — naming legado do contrato, mantido.

### Facets (fonte das opções do seletor)

| Endpoint | Owner | Conteúdo |
|---|---|---|
| `GET /purchase-requests/requesters` | já existia | solicitantes do universo autorizado; BFF agora enriquece com `display_name` |
| `GET /purchase-requests/cost-centers` | **novo** (api-delpi SQL + PR-api + BFF) | `C1_CC` + `CTT010.CTT_DESC01` no universo autorizado (`cc_scope`/`cost_centers` como carriers de escopo; o filtro explícito **não** estreita a própria facet) |

- Opções seguem branches + período (escopo), não os demais filtros — um filtro não esvazia as próprias opções.
- Opções de CC deduplicadas por código (mesma chave em filiais distintas → primeiro rótulo).
- Fail-closed: CC fora do escopo → `PermissionError` no PR-api (403); `requester_user_id` arbitrário não amplia universo (apenas filtra dentro dele).

### UX

- Dois `SuppliesMultiSelectField` (searchable) após Produto: **Solicitante** (rótulo = nome oficial Minha DELPI quando vinculado) e **Centro de custo** (`código — descrição`).
- Seleção reinicia `page=1`, serializa na URL (`requester_user_id`/`cost_center` repetidos), F5 restaura, vale para Tabela/Cards/exportação.
- `hasActivePurchaseRequestsFilters` inclui ambos → botão Limpar aparece.

## Contratos

- `requester.photo_url` — `string | null` — caminho BFF da foto quando `has_photo` no perfil Core (adição backward-compatible).
- `GET /purchase-requests/requesters/{protheus_user_id}/photo` — `200 image/*` | `404`; `supplies.access`.
- `GET /purchase-requests/cost-centers` — `{items:[{branch,code,description}]}`; `supplies.access` + units.
- `/purchase-requests/requesters` — items agora podem trazer `display_name` (adição).

## Testes

- api-delpi: SQL facet CC (DISTINCT, CTT010, scope tuple, sem OFFSET) + requesters SQL — `test_purchase_request_lines_sql.py`.
- purchase-requests-api: `test_cost_centers_facet.py` — escopo single/multi-branch, sem auto-filtro, negado sem permissão, sem scope → vazio sem chamada.
- supplies-api: photo_url/sem foto/não mapeado, `resolve_mapped_user_id`, `get_requester_photo`, rota proxy 200/404/401, facet requesters enriquecido, cost-centers pass-through.
- MFE: round-trip URL dos novos filtros, guards estruturais (secondary TOTVS, `usePersonPhoto`, campos).

## Residual

- Filtro produto = código exato (contrato); busca por descrição exigiria catálogo — registrado, não simulado.
- Facet CC deduplica por código entre filiais (mesma semântica do filtro `C1_CC IN` global por branch).
- Usuário TOTVS sem vínculo aparece no seletor com nome do ERP — filtra corretamente.
- `VISUAL_AUTHENTICATED` pendente de navegador.
