# Portal Suprimentos — Atenção com dados reais (execução)
**Data:** 2026-10-23 · **Estado:** `EXECUTED` · **Plano de origem:** [HOME-ATTENTION-REAL-DATA-REFACTOR-PLAN-20261023.md](./HOME-ATTENTION-REAL-DATA-REFACTOR-PLAN-20261023.md)

## 1. Inventário A0 — conclusão

O produtor anterior era estático: `ATTENTION_CARD_DEFS` emitia 7 cards com `count=None` e `status="available"` conforme capability — sem nenhuma chamada a fonte operacional. Os 7 itens eram atalhos de navegação com aparência de alerta (classificação `NAVIGATION_SHORTCUT`, não `REAL_ISSUE_COUNT`).

Fontes autorizadas inventariadas no HEAD:

| Origem | Owner | Rota/contrato | Regra real | Escopo |
|---|---|---|---|---|
| SCs aguardando pedido/recebimento | `purchase-requests-api` | `GET /purchase-requests/summary` (`buckets.ordering`, `buckets.receiving`) + `GET /purchase-requests` | `ATTENTION_BUCKETS` sobre `derive_overall_stage` (awaiting_order, partially_ordered, ordered, awaiting_receipt, partially_received) | `branch` por unidade; `supplies.access` via BFF confiável |
| Pedidos de compra em atraso | `api-delpi` | `GET /supplies/purchase-orders?late_only=true` | `late_lines` sobre linhas SC7 abertas com `C7_DATPRF` vencida; summary ignora `late_only`/paginação | `branch` lista |
| Recebimentos em atraso | `api-delpi` | `GET /supplies/purchase-order-otd/panel?status=late&start_date&end_date` | `DIAS < 0` sobre linhas de recebimento MP no período de digitação | `branch` por unidade |
| Estoque de segurança | `api-delpi` | `GET /supplies/safety-stock/summary` (`below_safety_stock`) + `GET /supplies/safety-stock/items?status=below_safety_stock` | saldo disponível < `BZ_ESTSEG` | `branch` por unidade; detalhe no app `/apps/estoque-seguranca` (perm `estoque-seguranca.access`) |

Categorias **não promovidas** (residual `TO_INVENTORY`):
- **Minhas tarefas** — não existe fonte de tarefas/owner; `my_tasks` é view placeholder.
- **Administração / Visão geral** — navegação, não situação de pendência (`EXCLUDE_BY_DEFAULT` no plano).
- Pedidos "em aberto" genérico — `late_only` já cobre a ocorrência relevante; sem segunda regra comprovada.

## 2. Congelamento funcional A1

Contrato `GET /home/attention` (política `can_use_portal`, sem mudança):

```jsonc
{
  "cards": [
    {
      "id": "purchase_requests_ordering",
      "title": "Solicitações aguardando pedido",
      "description": "…",
      "count": 4,                          // int; null quando unavailable
      "countUnit": "solicitações",         // "solicitações" | "linhas" | "itens"
      "status": "available",               // "available" | "unavailable"
      "preview": [{ "label": "SC 000123", "detail": "Fulano · Filial 01" }],
      "target": { "kind": "view", "viewId": "purchase_requests",
                  "query": "overall_stage=awaiting_order&overall_stage=partially_ordered" }
      // ou { "kind": "href", "href": "/apps/estoque-seguranca" } (cross-app)
    }
  ],
  "partialFailures": [{ "source": "safety_stock", "code": "source_unavailable" }]
}
```

Semântica congelada:
- `count=0` confirmado → cartão **omitido** (zero não é atenção).
- Falha de origem → cartão `status="unavailable"` + `partialFailures`; **nunca vira zero**.
- `count>0` → cartão com título de ocorrência, quantidade, prévia ≤3 e alvo contextual.
- Preview só é buscada quando `count>0`; falha de preview não derruba a contagem (preview=`[]`).
- Cartões por categoria — nenhum total agregado soma populações sobrepostas; o hero mostra **quantidade de situações ativas**, não itens somados.
- Sem `estoque-seguranca.access`: o cartão de estoque exibe contagem (já autorizada via KPI da Visão geral) mas **sem ação** — o deep link só aparece com a permissão existente do app dono.

## 3. Cards congelados (A1 → implementado)

| Card | Fórmula | Unidade | Alvo |
|---|---|---|---|
| Solicitações aguardando pedido | `summary.buckets.ordering` | solicitações (headers) | `/purchase-requests?overall_stage=awaiting_order&overall_stage=partially_ordered` |
| Solicitações aguardando recebimento | `summary.buckets.receiving` | solicitações (headers) | `/purchase-requests?overall_stage=ordered&overall_stage=awaiting_receipt&overall_stage=partially_received` |
| Pedidos de compra em atraso | `summary.late_lines` (SC7 abertas, `late_only=true`) | linhas | `/purchase-orders?late_only=true` |
| Recebimentos em atraso | Σ `summary.late_lines` por unidade, `status=late`, mês corrente | linhas | `/deliveries?status=late` |
| Itens abaixo do estoque de segurança | Σ `below_safety_stock` por unidade | itens | `/apps/estoque-seguranca` (href, gated pela permissão do app) |

Ordem de exibição: SCs → pedidos em atraso → recebimentos → estoque de segurança. Determinística, sem inventar prioridade de negócio.

## 4. Implementação A2/A3

**BFF (`supplies-api`):**
- `home_attention_service.py` reescrito: composição real por origem, `AuthorizationService.allowed_units` fail-closed, preview ≤3, falha isolada por origem (`partialFailures` + card unavailable).
- `supplies_delpi_reads.py`: novos métodos tipados `get_purchase_orders` e `get_safety_stock_items` (sempre com branch concreta — nunca omitida).
- `supplies_permissions.py`: constante `SAFETY_STOCK_APP_ACCESS = "estoque-seguranca.access"` (permissão existente reutilizada só para o deep link — nenhuma permissão por alerta criada).
- Rota `GET /home/attention` **inalterada** (`require_policy(can_use_portal)`).

**MFE (`plugins/supplies`):**
- `api/homeAttention.ts`: contrato evoluído — `countUnit`, `preview[]`, `target` (`view`/`href`).
- `HomePage.tsx`: renderiza prévia (≤3) dentro da descrição do card; navegação por `target` — `view` via `navigatePluginView` com query string de filtro real, `href` via `navigatePluginPath` (app externo). Cartão indisponível: tom neutro, sem ação.
- `index.css`: estilos `sp-home-attention__preview*` (tokens do kit, claro/escuro).
- Conteúdo (`pluginRouteCatalog`, `helpTooltips`, `userManualContent`): textos da seção e ajuda sincronizados com o comportamento real.

## 5. Semântica de estados

| Estado | Comportamento |
|---|---|
| loading | `SuppliesLoadingCard` (preservado) |
| error (rota/BFF) | banner de erro + botão Atualizar; caminhos continuam |
| zero confirmado (todas as fontes) | estado compacto `attentionQueueOk` |
| parcial | cards disponíveis + cartões `unavailable` + banner `attentionPartial` |
| unauthorized | 401/403 pela política existente; fail-closed |

## 6. Testes A4

- **BFF unit/contract** (`test_home_attention.py`, 14 testes): contagens por unidade de cálculo, alvos/filtros, preview ≤3 e só quando `count>0`, zero→omissão, falha→unavailable (nunca zero), isolamento entre origens, falha de preview preserva contagem, gating do deep link por `estoque-seguranca.access`, superadmin, código legado→403, ausência de auth→401/403.
- **BFF regressão:** suíte completa `supplies-api` verde.
- **MFE:** contrato de target/preview/indisponível (estrutural), store loading/error/partial; suíte completa verde.
- **MFE tooling:** `tsc -b`, `eslint` escopado, `vite build` PASS.

## 7. Residuais (TO_INVENTORY)

- `my_tasks` — sem fonte/owner; view placeholder permanece fora da Atenção.
- Overview/Administração — navegação (não são alertas).
- Card "minhas solicitações" (SCs do solicitante logado) exigiria mapeamento Core→`requester_protheus_user_id` — reservado para jornada futura com contrato explícito.
- Preview por item de SC mostra cabeçalho (SC, solicitante, filial) — detalhe por item disponível via lista.

## 8. Referências

- [HOME-ATTENTION-REAL-DATA-REFACTOR-PLAN-20261023.md](./HOME-ATTENTION-REAL-DATA-REFACTOR-PLAN-20261023.md)
- [API-ROUTES.md](./API-ROUTES.md)
- [IMPLEMENTATION-PLAN.md](./IMPLEMENTATION-PLAN.md)
