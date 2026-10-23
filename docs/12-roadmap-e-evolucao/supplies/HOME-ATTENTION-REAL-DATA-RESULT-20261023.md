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
- Preview só é buscada quando `count>0`; falha de preview não derruba a contagem (preview=`[]`). Preview de SC deduplica por `request_number` (o contrato lista **linhas**, mas o card conta solicitações).
- As 4 fontes executam em **paralelo** (ThreadPoolExecutor, mesmo padrão do Overview) — uma fonte lenta limita a latência ao máximo da origem, não à soma.
- Cartões por categoria — nenhum total agregado soma populações sobrepostas; o hero mostra **quantidade de situações ativas**, não itens somados.
- Sem `estoque-seguranca.access`: o cartão de estoque exibe contagem (já autorizada via KPI da Visão geral) mas **sem ação** — o deep link só aparece com a permissão existente do app dono.

## 3. Cards congelados (A1 → implementado)

| Card | Fórmula | Unidade | Alvo |
|---|---|---|---|
| Solicitações aguardando pedido | `summary.buckets.ordering` no período `date_from`/`date_to` = mês corrente (alinhado ao default da lista) | solicitações (headers) | `/purchase-requests?overall_stage=awaiting_order&overall_stage=partially_ordered` |
| Solicitações aguardando recebimento | `summary.buckets.receiving` no mês corrente | solicitações (headers) | `/purchase-requests?overall_stage=ordered&overall_stage=awaiting_receipt&overall_stage=partially_received` |
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


## 9. Revisão GPT — HOME ATTENTION (2026-10-23)

**Veredito: `ACCEPT_WITH_RESIDUAL` para código e publicação técnica; `VISUAL_AUTHENTICATED=INCONCLUSIVE`.** Revisados em GitHub o resultado, `supplies-api/app/application/services/home_attention_service.py`, `plugins/supplies/src/api/homeAttention.ts` e `plugins/supplies/src/pages/HomePage.tsx` no commit source `1b80a8324c`. As cinco categorias são calculadas por produtores existentes; a Home omite zero confirmado, preserva `unavailable`, exibe preview limitada e usa target tipado. O código confirma que os sete cards genéricos não são mais a fonte das situações. Testes 450 BFF / 382 MFE, deploy, health, contagens produtivas 82/154/90/7/201 e smoke são **reportados pelo executor**, não reexecutados pelo GPT.

**Observações para aceite:** (1) validar em navegador autenticado que cada deep link realmente abre recorte igual ao critério count (sobretudo período de SC e entregas) e preserva URL/F5; `target.query` existe em código, mas não é prova de aplicação final dos filtros; (2) o card `safety_stock_below` mostra `preview` com código/descrição/saldo/ESTSEG a usuários com `supplies.access`, enquanto restringe **somente o link** pelo permission `estoque-seguranca.access`. Confirmar com owner/Core que exposição dessa prévia detalhada é permitida para o mesmo público da contagem agregada; até a confirmação, classificar `STOCK_PREVIEW_AUTHZ=TO_INVENTORY` e considerar supressão da preview para perfis sem acesso ao app; (3) a composição captura exceptions e retorna `unavailable`; rever em teste de integração se 401/403 downstream não são absorvidos como falha parcial comum em desacordo com a política fail-closed; (4) confirmar no browser os estados visual, responsividade e teclado. O smoke 401 anônimo comprova somente bloqueio sem token, não todas as dimensões de AuthZ.

**Estado formal:** `HOME_ATTENTION_CODE=ACCEPT_WITH_RESIDUAL`; `DEPLOY_TECHNICAL=PASS (executor-reported)`; `COUNTS_PRODUCTION=PASS (executor-reported)`; `VISUAL_AUTHENTICATED=INCONCLUSIVE`; `FOLLOW_UP=AUTHZ_DETAIL_AND_FILTERED_NAVIGATION_VALIDATION`. Essas ressalvas não autorizam alterar o cutover de fornecedores C1, que continua aguardando Gabriel/TOTVS.


## 10. HOME-ATTENTION.P2 — Compactação padrão Portal Comercial (2026-10-23)

Mudança contratual: cards passam a ser **compactos** — nome da pendência, quantidade real, descrição funcional curta e botão **Abrir** com o filtro correspondente. **Nenhuma listagem/prévia de registros é montada na Home** (decisão do PO; também remove o ponto de latência e a exposição de detalhes de itens na Home).

### Backend (`supplies-api`)
- `home_attention_service.py`: removidas todas as chamadas exclusivas de prévia —
  - `purchase-requests/summary` apenas (as 2 chamadas `purchase-requests` list por bucket foram eliminadas);
  - `get_purchase_orders` e `get_purchase_order_otd_panel` seguem, mas com `page_size=1` (o `summary` do producer é independente da página);
  - `get_safety_stock_items` (preview) removido — restam só os `summary` por filial.
- Campo `preview` removido do DTO público do card (único consumidor é o MFE Supplies — remoção direta, sem período de transição).
- Contagens, regras de negócio, unidades, AuthZ, `unavailable`+`partialFailures` inalterados.

### Frontend (`plugins/supplies`)
- `homeAttention.ts`: tipo `HomeAttentionPreviewItem` e campo `preview` removidos.
- `HomePage.tsx`: lista de prévia removida; item do `AlertQueue` = `title · count countUnit` + `description` + `actionLabel "Abrir"` + `leadingIcon` por categoria (mesmo padrão `EventsSection`/`AlertQueue` do Portal Comercial via `SuppliesEventsSection`).
- `index.css`: CSS órfão `sp-home-attention-list/card/preview` removido (o kit `delpi-ui-alert-queue` já estiliza).
- Conteúdo/Help/manual atualizados para remover menção a prévias.

### Navegação validada (universo contado = universo do destino)
| Card | Target | Evidência de filtro |
|---|---|---|
| SCs aguardando pedido | `purchase_requests?overall_stage=awaiting_order&overall_stage=partially_ordered` | `parseQueryFromSearch` aceita multi `overall_stage`; período default = mês corrente (mesma janela da contagem) |
| SCs aguardando recebimento | `purchase_requests?overall_stage=ordered&…partially_received` | idem |
| Pedidos em atraso | `purchase_orders?late_only=true` | `late_only` parseado (query.ts) e o `summary.late_lines` do producer usa a mesma regra `DIAS<0` |
| Recebimentos em atraso | `deliveries?status=late` | `status` parseado; defaults `start/end_date` = mês corrente (mesma janela `DT_DIGITACAO` da contagem) |
| Estoque abaixo da segurança | `/apps/estoque-seguranca` (só com `estoque-seguranca.access`) | `DEFAULT_QUERY_PARAMS.status = "below_safety_stock"` no app de destino |

### Testes
- Backend: 14 testes home-attention (inclui `test_compose_never_fetches_record_lists` — guard que falha se qualquer chamada de prévia voltar); suite completa **450 passed**.
- MFE: 382 passed (attention: 5 — contrato compacto, sem `preview`, estados loading/error/partial/unavailable); tsc ok; build ok; eslint sem achados nos arquivos alterados.
- Chamadas downstream por request: **10 → 6** (PR summary + PO + 2×OTD + 2×SS-summary); payload por chamada reduzido (`page_size` 3→1 nos endpoints com summary).

### Performance (medida em produção, unidades 01+02)
- **Antes**: composição fazia até 10 chamadas downstream; fonte PR ≈ summary serial (~29s) + 2 listas de prévia seriais → pior caso ~90s de loading.
- **Depois**: 6 chamadas (PR summary + PO + 2×OTD + 2×SS summary); `list_lines` do summary passou a buscar páginas 2..N em paralelo (pool de 8, ordem preservada — owner `purchase-requests-api`, gargalo comprovado por medição por fonte).
- **Endpoint real medido**: ~13,6s total (PR summary ~14s; PO 0,5s; OTD 2,4–4,6s; SS 1,4s — em paralelo).
- **Residual**: o `summary` de SCs ainda agrega linhas no `purchase-requests-api`; redução adicional exige agregação/count server-side no `api-delpi` (backlog, não bloqueio — o loading é limitado e com refresh).

### Deploy P2
- Commits `0baa937c15` (compactação) + `35cfe26e9a`/`303104af38` (fan-out paralelo).
- Serviços publicados: `supplies-api` (`sha256:3ab12e661d09`), `supplies` (`sha256:2464c0b5b522`), `purchase-requests-api` (`sha256:c70585fe251b`) — todos healthy.
- Smoke: 5 cards com contagens reais `[81,156,90,7,201]`, sem `preview`, `partialFailures: []`; 401 sem token (verificado na entrega anterior, contrato inalterado).

### Residual
- `VISUAL_AUTHENTICATED=INCONCLUSIVE` mantém-se (sem navegador autenticado).
- A prévia detalhada de estoque deixou de existir — a observação (2) da revisão GPT sobre exposição de prévia sem `estoque-seguranca.access` fica **resolvida por remoção** (não há mais dados de itens na Home).


## 11. Revisão GPT — HOME-ATTENTION.P2 (2026-10-23)

**Veredito: `ACCEPT_WITH_RESIDUAL` para P2 compactação e deploy técnico; `PERFORMANCE_TARGET_5S=FAIL`; `VISUAL_AUTHENTICATED=INCONCLUSIVE`.** Revisados em GitHub o source `c92f480eb1`, `supplies-api/app/application/services/home_attention_service.py` e este documento. O BFF deixou de buscar previews, reduziu payloads com `page_size=1`, preservou cinco contagens e estados de falha. O MFE adotou cards compactos com ações de navegação. Resultados de 450 testes BFF, 69 testes do `purchase-requests-api`, 382 MFE, deploy das três imagens, health e smoke com contagens `[81,156,90,7,201]` são **executor-reported**, não reexecutados pelo GPT.

**Benefício medido pelo executor:** chamadas downstream `10→6` e duração ponta a ponta no smoke de `~90s` pior cenário anterior para `13,6s` após fan-out no owner de SC. **Comparação limitada:** são tempos pontuais, não p50/p95 rigorosos em amostras equivalentes; não declarar SLA cumprido. A meta anterior de orçamento total ≤5s não foi atingida. `PR_SUMMARY_AGGREGATION=TO_INVENTORY`: investigar agregação server-side no `api-delpi` ou interface contratada equivalente com owner `purchase-requests-api`, mantendo semântica de buckets, janela temporal, unidade e AuthZ. Não aumentar concorrência indefinidamente.

**Segurança/navegação:** remoção de previews elimina a exposição de linhas de estoque anteriormente apontada; contador agregado e link continuam condicionados aos contratos/permissões existentes. Filtros para SC, PO, OTD e estoque possuem validação estrutural reportada, mas `FILTERED_NAVIGATION_AUTHENTICATED=INCONCLUSIVE` até navegação real + URL/F5 em sessão. 401 anônimo não substitui testes efetivos de usuário/unidade. Recomendar reteste visual de cards compactos em claro/escuro, mobile, teclado e origem sem permissão ao destino estoque.

**Release:** `P2_CODE=ACCEPT_WITH_RESIDUAL`, `P2_DEPLOY=PASS (executor-reported)`, `P2_SMOKE=PASS (executor-reported)`, `P2_PERFORMANCE=ACCEPT_WITH_RESIDUAL` (melhoria substantiva mas meta 5s não alcançada), `P2_VISUAL=INCONCLUSIVE`. Não modificar cutover C1 de fornecedores, ainda aguardando Gabriel/TOTVS. Próxima frente, se PO priorizar: agregação eficiente das solicitações e benchmark p50/p95.


## 12. HOME-ATTENTION.P3 — Remoção da seção (2026-10-23)

**Decisão: `REMOVE_ATTENTION`.** O PO autorizou ponta a ponta: remover os cinco cards operacionais e investigar uma fonte canônica de "Minhas tarefas"; se inexistente, remover Atenção por completo.

### Inventário da fonte de tarefas (evidência)
| Candidato | Veredito |
|---|---|
| `my_tasks` (rota supplies) | placeholder navegacional — App.tsx: "A fila de acompanhamento será composta nas jornadas seguintes" |
| Core `GET /me/notifications` | caixa de entrada informativa ao destinatário: `list_unread(user_id)` marca lida/não lida; não modela atribuição nem pendência a executar (ler ≠ concluir tarefa) |
| Dispatchers `purchase-requests-api` | notificam o **solicitante** sobre mudanças de estado (aprovada/rejeitada/PC vinculado/recebimento) — informação, não tarefa atribuída |
| `assigned_to` em api-delpi | somente contextos alheios (helpdesk, LNF) — fora do escopo Suprimentos e de `supplies.access` |
| Endpoint de contagem de tarefas | inexistente em todos os serviços inspecionados |

Sem owner, sem ciclo de vida "pendente→feita", sem endpoint de contagem: renderizar "Minhas tarefas · N" seria contador fictício ou semântica errada (notificação ≠ tarefa). `TASKS_ONLY` inviável → remoção conforme autorização.

### Removido
- `supplies-api`: rota `GET /home/attention` (`home_routes.py`), `HomeAttentionService`, blueprint no composer, suite `test_home_attention.py` (14 testes).
- `plugins/supplies`: `api/homeAttention.ts`, `app/homeAttentionStore.ts`, bloco Atenção da `HomePage` (panel/queue-ok/loading/error), destaque "Atenção" do hero do `PluginShell` (derivado dos cards), CSS `sp-home-attention-error`/`sp-home-queue-ok`, chaves `attention*` de conteúdo/Help/manual, teste `Home.attention.test.ts` (substituído por `Home.noAttention.test.ts` — 6 guards anti-regressão).
- **Não removido** (outros consumidores): gateways `PurchaseRequestsGateway`/`SuppliesDelpiReads`, endpoints produtores (summary SC, POs abertos, OTD, ESTSEG), fan-out paralelo do P2, faixas Atenção das páginas de lista, rota `my_tasks` na navegação.

### Efeito
- Abrir a Home não dispara nenhuma chamada operacional: 6 downstream calls/request → **0** no fluxo da Home (~13,6s → latência só de hero/favoritos/recentes locais).
- Sem loading permanente, sem contador inventado, sem mensagem de "sem tarefas".
- AuthZ: nada novo; dados pessoais de outros contextos não são acessados.

### Testes
- Backend: suite completa sem falhas após remoção (436+ passam; 14 testes de atenção removidos junto com o código).
- MFE: **383 passed** (6 guards novos: módulos ausentes, HomePage/PluginShell sem atenção, sem `/home/attention`, demais blocos intactos); tsc ok; eslint limpo; vite build ok.

### Deploy
- Commit `66bf028bcc` → `main` (ff-only). Serviços publicados: `supplies-api` (`sha256:d4a88f111cab`) + `supplies` (`sha256:b6170a770508`) — somente os afetados; `purchase-requests-api`/`api-delpi` intactos (otimizações do P2 continuam servindo as páginas de destino). `delpi-supplies-api` Up healthy.
- Smoke autenticado: `GET /home/attention` → **404** em 12ms (contrato removido — verificado `url_map` sem rotas home, 38 rotas restantes); `GET /me/capabilities` → 200 em 10ms; anônimo → 401 (fail-closed).
- Bundle federado: `App-C1cf8iYo.js` sem marcadores `homeAttention`/`sp-home-attention`; `my_tasks` presente na navegação.
- Antes/depois: Home → 1 chamada BFF + 6 downstream (~13,6s composição) → **0 chamadas** de atenção; hero/favoritos/recentes/caminhos renderizam sem espera operacional.

### Residual
- `my_tasks` segue placeholder na navegação (`TO_INVENTORY` mantido) — quando existir owner canônico de tarefas, o card "Minhas tarefas" pode voltar via Cenário A do P3.
- `VISUAL_AUTHENTICATED=INCONCLUSIVE` (sem navegador autenticado neste ambiente).
