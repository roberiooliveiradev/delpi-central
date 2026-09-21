# E9 / WF-07 — P0 contract freeze (Entregas / atrasos)

- Data: 2026-09-21
- HEAD de revalidação: `4f3ed59483`
- Pré-condição E8: GATE-FEATURE WF-06 = PASS ([evidência](./e8-wf06-federated-runtime-gate.md))

## Product Owner

Autorização persistida:

> Autorizo a promoção de E9 / WF-07 — Entregas/Atrasos, condicionada ao fechamento do GATE-FEATURE E8 e ao freeze do P0/contrato antes de qualquer implementação.

| Estado | Valor |
|---|---|
| `E9 PROMOTION` | **AUTHORIZED** |
| `E9 P0 CONTRACT` | **FROZEN** (este arquivo + docs canônicos) |
| `E9 IMPLEMENTATION` | **BLOCKED** até o próximo bounded run executar a receita `E9.S*` |
| `E9 GATE-FEATURE` | ainda não existe — não marcar PASS |

Escopo da autorização: somente a página nativa P0. Não autoriza depreciação do BI, cutover, paridade P-03, Supplier 360, OTD de fornecedores, write-back TOTVS nem permission nova.

## Ownership

```text
Browser → Portal → MFE plugins/supplies → supplies-api → api-delpi
```

| Camada | Responsabilidade |
|---|---|
| `plugins/supplies` | UX, filtros, tabela, estados, Help, URL |
| `supplies-api` | AuthZ server-side, escopo `01`/`02`, composição BFF, mapeamento de erros |
| `api-delpi` | SQL/regra TOTVS; producer `GET /supplies/purchase-order-otd/panel` |

Proibido: MFE → api-delpi.

## Producer (CONFIRMADO_NO_CODIGO)

| Item | Valor |
|---|---|
| Path | `GET /supplies/purchase-order-otd/panel` |
| operationId | `get_supplies_purchase_order_otd_panel` |
| Universo | `TIPO_PRODUTO = MP` apenas (`VW_PONTUALIDADE_FORNECEDORES`) |
| Grão | **linha de recebimento** (não PC aberto SC7) |
| Query | `branch?`, `start_date?`, `end_date?`, `status?`, `page`, `page_size`, `sort_by?`, `sort_dir` |
| `branch` omitido | consolidado **sem filtro de filial** na view (todas as filiais da view) |
| `status` | `on_time` \| `late` \| omitido = ambos |
| Paginação | tier `page_20_1000` (default 20, máx. 1000) |
| Sort default (sem `sort_by`) | `status DESC`, `expected_delivery_date DESC`, `branch`, `order_number`, `order_item` |
| Sort permitido | `status`, `branch`, `order_number`, `order_item`, `product_code`, `product_description`, `supplier_code`, `supplier_name`, `supplier_short_name`, `expected_delivery_date`, `receipt_entry_date`, `quantity`, `days_diff` |

### Semântica de atraso

| Campo / regra | Significado |
|---|---|
| `expected_delivery_date` | `DT_ENTREGA` da view ≈ prazo prometido (`C7_DATPRF`) |
| `receipt_entry_date` | `DT_DIGITACAO` — data de digitação/entrada do recebimento |
| `days_diff` | `DIAS` da view |
| **No prazo** | `DIAS >= 0` → `status = on_time` |
| **Atrasado** | `DIAS < 0` → `status = late` |
| Sem recebimento | **fora deste universo** — a view é de pontualidade de recebimentos; PC aberto sem NF/entrada não aparece aqui |

O BFF **não** recalcula `DIAS` nem redefine atraso.

### Semântica do filtro de período

`start_date` / `end_date` filtram **`DT_DIGITACAO` (`receipt_entry_date`)**, não a data prometida e não a data de emissão do PC.

Help obrigatória: deixar isso explícito. Texto legado «atrasos do dia» no Manual/FAQ/tooltips é **drift** e deve ser corrigido na subetapa de Ajuda.

### Fronteira com outras páginas

| Página | O que é | O que não é |
|---|---|---|
| WF-07 Entregas / atrasos | Linhas **recebidas** MP classificadas por pontualidade | Lista de saldo em aberto |
| WF-05 Pedidos | SC7 **aberto**, inclusive `late_only` por prometida | Histórico de recebimento OTD |
| WF-OTD-A / Overview OTD | KPI/série analítica | Lista operacional de linhas |
| WF-11 OTD Fornecedores | Ranking/fornecedor (futuro) | Esta página |

## BFF contract (FROZEN)

```http
GET /apps/supplies-api/deliveries/late
```

Path interno Flask: `GET /deliveries/late` (gateway já reescreve `/apps/supplies-api/`).

Nome mantido conforme `API-ROUTES.md`. Apesar do sufixo `/late`, `status` pode ser `late`, `on_time` ou omitido.

### AuthZ

- Policy: `supplies.access` (mesmo padrão de operações / `can_use_operations` das listas).
- `supplies.manage` **não** concede acesso especial.
- Sem `supplies.deliveries.*`.
- Core = authority de permissions efetivas; JWT não autoriza sozinho.
- Core indisponível → fail-closed (401/403 conforme padrão vigente da BFF).

### Unit / data scope

Códigos permitidos: **somente** `01` e `02` (ADR-009).

| Entrada | Comportamento |
|---|---|
| `branch` ausente / vazio | efetivo `["01","02"]` (Todas) |
| `?branch=01` ou `02` | uma unidade |
| `?branch=01&branch=02` | Todas |
| código fora de `{01,02}` | **422** |
| unidade solicitada fora do escopo efetivo do usuário | **403** (fail-closed; UI esconder rota não conta) |

**Producer `branch` omitido é proibido como atalho de «Todas» do Portal**, porque o producer sem filial atravessa **todas** as filiais da view, não o universo `01`/`02`.

Composição P0:

- 1 unidade → uma chamada ao panel com esse `branch`.
- 2 unidades → duas chamadas ao panel (mesmos filtros/sort) + merge estável no BFF no universo autorizado; paginação/`total` refletem o merge. Falha upstream em qualquer perna → **502** (sem partial silencioso no P0).

### Request (query)

| Param | Default P0 | Notas |
|---|---|---|
| `branch` (repetível) | efetivo `01`+`02` | ver tabela acima |
| `status` | `late` | `on_time` \| `late` \| omitido (ambos). Valor inválido → 422 |
| `start_date` / `end_date` | mês civil corrente (`YYYY-MM-DD`) | filtro = `DT_DIGITACAO` |
| `page` | `1` | |
| `page_size` | `20` | máx. alinhado ao producer (1000) |
| `sort_by` / `sort_dir` | omitido → default do producer | só chaves do producer |

Sem busca textual P0. Sem export P0.

### Response

Espelhar o producer sem segunda fórmula:

```json
{
  "branch": "01" | "02" | "consolidated",
  "start_date": "YYYY-MM-DD",
  "end_date": "YYYY-MM-DD",
  "product_type": "MP",
  "applied_filters": { "branches": ["01","02"], "status": "late", "..." : "..." },
  "summary": {
    "total_lines": 0,
    "on_time_lines": 0,
    "late_lines": 0,
    "purchase_order_otd_pct": null,
    "late_percentage": 0.0
  },
  "items": [ { "...line fields..." } ],
  "page": 1,
  "page_size": 20,
  "total": 0,
  "total_pages": 0
}
```

Notas:

- Producer devolve linhas em `lines.items` + `lines.total`/`page`/`page_size`/`total_pages`. O BFF **achata** para `items` + paginação no topo (padrão das listas do Portal).
- `summary` do producer **não** aplica o filtro `status` (só período/unidade). Manter esse comportamento; não inventar summary filtrado no BFF.
- Campos de item (inglês, já no SQL): `branch`, `supplier_code`, `supplier_store`, `supplier_name`, `supplier_short_name`, `document`, `order_number`, `order_item`, `product_code`, `product_description`, `product_type`, `quantity`, `purchase_order_issue_date`, `expected_delivery_date`, `receipt_entry_date`, `invoice_issue_date`, `days_diff`, `is_on_time`, `status`.

### Erros

| Situação | HTTP |
|---|---|
| Sem sessão | 401 |
| Sem `supplies.access` / unidade fora do escopo | 403 |
| Query inválida (branch/status/datas) | 422 |
| Lista vazia | 200 + `items: []` (não 404) |
| Upstream 4xx relevant | mapear; não fabricar 404 |
| Upstream 5xx / timeout | 502 |

## MFE contract (FROZEN)

| Item | Valor |
|---|---|
| Rota | `/apps/supplies/deliveries` |
| Manifest | path já existe; `permission: supplies.access`; `showInMenu` pode passar a `true` na implementação |
| Placeholder atual | substituir `PLACEHOLDER.deliveries` por página real |
| Kit | `@delpi/plugin-ui` via `suppliesUi` — PagePath/PageHero, FilterBar, SectionCard, DataTable, MultiSelect, QuickPeriod, StatusBadge, Empty/Loading/StateBanner, pagination |

### Estados

| Estado | Comportamento |
|---|---|
| loading | `SuppliesLoadingCard` |
| success | tabela (+ cards se o padrão das listas irmãs for reutilizado) |
| empty | empty state + CTA para Ajuda / limpar filtros |
| error | banner + retry |
| 403 | forbidden de unidade/módulo (copy canônica) |
| 404 | **não material** na lista P0 |

### Filtros URL / F5

Query shareable: `branch`, `status`, `start_date`, `end_date`, `page`, `page_size`, `sort_by`, `sort_dir`. F5 restaura o mesmo recorte. Trocar filtro reseta `page=1`.

### Drill

**NO DRILL P0.**

Motivo: o painel é de **recebimentos históricos**; a ficha E8 (`/purchase-orders/:branch/:number`) só cobre o universo **SC7 aberto**. Linha atrasada de PC já encerrado cairia em «não encontrado». Não congelar navegação enganosa.

### Help (obrigatório no mesmo entregável da página)

Corrigir/criar:

- tooltip da página;
- Manual + Quero→onde (label já aponta `deliveries`);
- FAQ OTD × Entregas (remover «atrasos do dia» se permanecer ambíguo);
- glossário se entrar termo novo de `DT_DIGITACAO` / digitação do recebimento.

Explicar: atraso = recebimento depois do prometido (`DIAS < 0`); período = digitação do recebimento; universo = MP; distinto de Pedidos abertos e de OTD analytics.

## RQ / AC ledger

| RQ | Requisito | AC verificável |
|---|---|---|
| RQ-E9-01 | Acesso à página | Usuário com `supplies.access` abre `/apps/supplies/deliveries`; sem access → 403/forbidden |
| RQ-E9-02 | Lista operacional | Com filtros default, BFF devolve `items`/`summary` do panel MP; MFE renderiza linhas |
| RQ-E9-03 | Escopo de unidade | Só `01`/`02`; inválida 422; fora do escopo 403; Todas = merge 01+02 sem omitir branch no producer |
| RQ-E9-04 | Filtros período/status | `status` e datas alteram o request; período mapeia a `DT_DIGITACAO`; default status=`late`, mês corrente |
| RQ-E9-05 | Sort/paginação | Server-side via producer; default e colunas = contrato; troca de filtro → page 1 |
| RQ-E9-06 | Drill PC | **FORA_DO_ESCOPO_COM_JUSTIFICATIVA** — NO DRILL P0 |
| RQ-E9-07 | Estados/erros | loading/empty/error/403/retry cobertos; lista vazia ≠ 404 |
| RQ-E9-08 | Help | Manual/FAQ/tooltip/glossário coerentes com semântica; teste estrutural de chaves |
| RQ-E9-09 | URL/F5 | deep link restaura filtros; F5 não perde recorte |
| RQ-E9-10 | AuthZ BFF | MFE só chama `/apps/supplies-api/...`; zero browser→api-delpi; Core down fail-closed |

## Test contract (para a implementação)

### api-delpi

Preferência: **sem mudança de producer**. Suítes existentes de panel/SQL/routes permanecem a prova do contrato.

### supplies-api

Happy path; 1 branch; Todas (merge 01+02); branch negada 403; branch inválida 422; status inválido 422; mapeamento 4xx/5xx; paginação/sort; Core fail-closed; prova de que omitir branch no producer **não** é usado para Todas.

### MFE

loading/success/empty/403/error; filtros; sort; paginação; URL/F5; Help; ausência de drill P0; structural kit-first.

### Runtime GATE-FEATURE (após implementação)

Portal → `/apps/supplies/deliveries` → só BFF → sem api-delpi direto.

## Legacy / P-03

| Tema | Estado |
|---|---|
| Página nativa WF-07 | **pode proceder** após este freeze |
| Paridade BI Atraso SC | **BLOQUEADO_COM_EVIDENCIA** (P-03) |
| Depreciação / redirect / cutover do BI | bloqueados até comparação real |
| Afirmação «WF-07 = BI legado» | **proibida** sem evidência |

## Non-goals P0

Alterar regra TOTVS de atraso; permission nova; supplier OTD/ranking/360; previsão de atraso; follow-up externo; edição/write-back; export; busca free-text; drill para ficha PC; depreciação do BI.

## Recipe executável (não executar neste freeze)

| ID | Escopo |
|---|---|
| E9.S1 | Revalidar producer no HEAD de implementação; wiring gateway BFF read-only |
| E9.S2 | BFF `GET /deliveries/late` + AuthZ + merge 01/02 + testes API |
| E9.S3 | MFE página kit-first (substituir placeholder) |
| E9.S4 | Help + estados + URL/F5 + sync Manual/FAQ/tooltips |
| E9.S5 | Suites MFE + smoke federado → GATE-FEATURE WF-07 |

## Readiness

```text
E9 P0 CONTRACT = FROZEN
E9 READINESS = READY_TO_EXECUTE
```
