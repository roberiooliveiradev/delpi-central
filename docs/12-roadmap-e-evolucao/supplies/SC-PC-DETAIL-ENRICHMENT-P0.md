# SC/PC Detail Enrichment — P0 (Discovery, Inventário e Proposta)

> Status: `DISCOVERY_COMPLETE` · `IMPLEMENTATION_NOT_AUTHORIZED` · `NO_CODE_CHANGE`
> Baseline: `f89e73376c` · Data: 2026-06-06 · Autor: Devin (investigação read-only)
> Documentos do pacote: `SC-PC-DETAIL-DATA-CONTRACT-MATRIX.md` ·
> `SC-PC-DETAIL-UX-WIREFRAMES.md` · `SC-PC-DETAIL-IMPLEMENTATION-ROADMAP.md`

## 1. Resumo executivo

O levantamento provou que as fichas de Detalhe da SC e Detalhe do PC renderizam
hoje **apenas uma fração** do que já chega ao MFE:

- **SC:** o produtor (`purchase-requests-api` + `api-delpi`) já emite — e o BFF
  repassa integralmente — pedidos vinculados por item, recebimentos, totais
  solicitado/pedido/recebido, datas de primeira/última emissão e recebimento,
  aprovador, fornecedor sugerido, UM, data de necessidade, saldo, resíduo e uma
  **timeline completa**. O `types.ts` do MFE declara ~30% disso.
  → Enriquecimento substancial é **Fase A: zero contrato novo**.
- **PC:** o contrato cobre itens abertos com fornecedor, comprador (código), SC
  de origem, quantidades, preço, valor aberto e recebimentos (SD1). O produtor
  **não emite header agregado** e a rota cobre **somente pedidos em aberto** —
  pedido entregue/residual retorna 404. Essas são decisões de contrato, não de UI.
- **Rastreabilidade SC→PC→NF é provada ponta a ponta** (`C7_NUMSC/C7_ITEMSC`,
  `D1_PEDIDO/D1_ITEMPC`+chave composta) e as rotas MFE das duas fichas já existem
  → links bidirecionais são Fase A.
- **Não há fonte para "próximo passo" ou "dono da ação"** — permanece `PLANNED`
  até existir um owner canônico de orquestração. Nenhuma UI deve inferi-lo do stage.

## 2. Problemas das telas atuais

| Problema | Página | Gravidade |
|---|---|---|
| ~70% do payload SC não é declarado/renderizado | SC | alta — informação operacional já paga |
| Pedidos vinculados invisíveis apesar de provados | SC | alta — pergunta central do usuário sem resposta |
| Timeline provada e componente de kit existente, ambos sem consumidor | SC | alta |
| Sem header agregado no contrato PC | PC | média — exige decisão (owner api-delpi) |
| PC só cobre pedidos abertos; 404 em entregue confunde "inexistente" com "concluído" | PC | média — copy/semântica |
| `buyer_code` sem nome; `source_request_*` sem link | PC | média |
| Ausência real × não reconciliado indistinguível nos vínculos | ambas | média |
| "Próximo passo/dono" sem fonte | SC | decisão de produto |

## 3. Baseline e authorities

- HEAD: `f89e73376c`; `origin/main` sincronizado; working tree limpo.
- Authorities lidas: `AGENTS.md`, `.cursor/rules` (constituição mínima +
  `plan-construction`, `platform-api-contracts-integration`,
  `platform-frontend-mfe-experience`, `platform-security-identity-authorization`,
  `application-bounded-context-decoupling`, `sql-query-development`,
  `feature-help-sync`, `contract-evolution-backward-compatibility`), docs
  `docs/12-roadmap-e-evolucao/supplies/` (README, IMPLEMENTATION-PLAN,
  API-ROUTES, WIREFRAMES, INTEGRACOES) e séries E11.* e PR-IDENTITY-*.

## 4. Owners e boundaries (preservados)

| Camada | Owner | Papel |
|---|---|---|
| MFE/fichas | `plugins/supplies` | render-only; nenhum join/cálculo de domínio |
| BFF portal | `supplies-api` | policy + `@require_unit` + identity enrich (SC) / passthrough (PC) |
| Produtor SC | `purchase-requests-api` | escopo por CC, estágios derivados, agregação, timeline |
| Leitura TOTVS SC1/SC7/SD1 | `api-delpi` | único owner de SQL Protheus |
| Identidade/RBAC | Core central | `can_use_purchase_requests` / `can_use_operations`; filial = filtro |

Nenhuma proposta cruza boundary: campos `PROVEN_IN_BFF` só exigem trabalho no
MFE; campos `PLANNED`/`TO_INVENTORY` exigem contrato no owner correto — jamais
join ou SQL no MFE/BFF.

## 5. Inventário — resumo por classificação

(Matriz completa e evidências arquivo:linha em `SC-PC-DETAIL-DATA-CONTRACT-MATRIX.md`.)

| Classe | SC | PC |
|---|---|---|
| `PROVEN_IN_FRONTEND` | filial, nº, solicitante(+foto), abertura, estágio, nº itens, aprovação-resumo, item/produto/qtd/CC-código/stage | filial, nº, por item: produto, fornecedor, comprador(cód.), SC origem, qtds, preço, valor aberto, datas, delivery_status, recebimentos |
| `PROVEN_IN_BFF` | CC c/ descrição, pedidos vinculados, fornecedores, 1ª/últ. emissão e recebimento, totais solicitado/pedido/recebido, atraso (has/max dias), UM, necessidade, qtd pedida, saldo, aprovador(nome), fornecedor sugerido, conta, resíduo, pedidos por item c/ recebimentos+delivery+comprador, timeline completa | — (passthrough; campos extras não existem no produtor) |
| `TO_INVENTORY` | aprovador c/ identidade portal; histórico auditável | nome do comprador, `C7_UM`, `C7_COND`, `C7_MOEDA`, `C7_OBS/MSG`, `A2_CGC`+endereço, breakdown IPI/frete/desconto, `D1_NFORI/TES/TIPO` |
| `PLANNED` | próximo passo, dono da ação, comprador responsável | header agregado (total, recebido, situação geral), solicitante da SC origem, ocorrências/histórico de prazo |

## 6. Lacunas de contrato (`CONTRACT_GAPS`)

1. **Header agregado do PC ausente** — `compose_open_purchase_order` retorna só
   `{branch, order_number, items}`. Total do pedido / total recebido / situação
   geral exigem contrato novo na `api-delpi` (não somar no MFE).
2. **PC cobre apenas pedidos abertos** — `C7_QUANT > C7_QUJE` + `RESIDUO<>'S'`.
   Pedido concluído = 404. Decidir: ficha histórica separada, endpoint de
   "pedido fechado", ou copy clara de 404. **Decisão pendente do PO/arquitetura.**
3. **Nome do comprador** — só `buyer_code` (código Protheus). Resolução precisa
   de lookup (análogo ao requester identity) ou campo nome no produtor.
4. **`received` vs `receipts`** — `C7_QUJE` (baixa) vs. soma `D1_QUANT` (notas)
   podem divergir em processamento; a UX deve rotulá-los distintamente.
5. **Ausência vs. não-reconciliado** — linha SC sem `purchase_orders` significa
   "sem pedido provado", não "sem pedido no ERP". Copy deve ser honesta.
6. **SC sem dono da ação** — nenhum campo de responsável pela etapa em nenhum
   produtor. `PLANNED`; proibido inferir do `overall_stage`.

## 7. Impacto de segurança

- Zero mudança de AuthZ proposta: mesmas policies e `@require_unit` atuais;
  filial segue filtro de dados, sem permissão por filial.
- Novos campos sensíveis candidatos (`A2_CGC` CNPJ, `A2_END` endereço,
  `A2_TEL` telefone, `account_code` conta contábil) exigem decisão de exposição
  — classificados `TO_INVENTORY` e **não** incluídos na Fase A.
- `approver_name`/`order_user_name` são dados pessoais já emitidos pelo
  produtor; exibição herda o mesmo controle de acesso da ficha (sem novo vetor).
- Nenhuma escrita ERP; nenhum job; nenhuma permission nova.

## 8. Decisões necessárias (gate para fases futuras)

| # | Decisão | Bloqueia |
|---|---|---|
| D1 | Copy/semântica do 404 de PC concluído (vs. endpoint de fechados) | Fase A PC |
| D2 | Expor `approver_name`, `suggested_supplier`, `account_code` na UI | Fase A SC |
| D3 | Header agregado do PC: contrato novo api-delpi vs. não mostrar | Fase B PC |
| D4 | Lookup de nome do comprador (Core identity vs. campo produtor) | Fase B |
| D5 | Exposição de dados fiscais do fornecedor (CNPJ/endereço) | Fase C/D |
| D6 | Owner canônico de "próximo passo/dono da ação" | Fase D |

## 9. Riscos

- **Risco de semântica dupla** (baixa SC7 vs. SD1) — mitigar com rótulos e hint.
- **Payload SC pode crescer** — linhas já trazem pedidos+receipts aninhados;
  monitorar tamanho em fichas com muitos itens (semântica já existente no produtor).
- **C2/C3 de Purchase Requests** — qualquer mudança de ownership do produtor SC
  deve respeitar a sequência C1→C2→C3; esta proposta é render-only e não antecipa nada.
- **Achados TOTVS não provam vigência** — toda coluna `TO_INVENTORY` exige prova
  em consulta real antes de contrato.

## 10. Roadmap recomendado (resumo)

Detalhe por etapa em `SC-PC-DETAIL-IMPLEMENTATION-ROADMAP.md`.

- **Fase A — Quick wins (zero contrato novo):** SC exibe pedidos vinculados,
  totais, aprovação, UM/necessidade/saldo, timeline via `SuppliesEventsSection`;
  links SC↔PC; PC: link SC origem + copy de 404 (após D1) + hierarquia de seções.
- **Fase B — Enriquecimento com dados existentes:** header agregado PC (D3),
  nome do comprador (D4), `C7_UM` e campos simples comprovados.
- **Fase C — Rastreabilidade:** campos fiscais/opcionais aprovados (D5),
  rótulos baixa-vs-NF, página de NF só se rota/contrato provados.
- **Fase D — Acompanhamento gerencial:** alertas, histórico auditável,
  "próximo passo/dono" — somente com owner canônico definido (D6).


## Revisão GPT — Discovery SC/PC (2026-10-24)

**Veredito: `ACCEPT_WITH_RESIDUAL` para o pacote de levantamento; `IMPLEMENTATION_NOT_AUTHORIZED` permanece.** Revisados no GitHub os quatro documentos do pacote no commit `8c90033681` (matriz de campos, proposta visual, roadmap e síntese). O inventário de campos, a separação frontend/BFF/produtores e os caminhos SC↔PC são base válida para planejar a Fase A, mas a implementação depende da reconciliação destes residuais:

1. **Grandezas e unidades:** antes de expor KPIs `header.requested_quantity/ordered_quantity/received_quantity`, comprovar como são agregados e se há itens em UMs heterogêneas. Não somar UN/MT/KG como total de quantidade; preferir indicadores por UM/item ou contagem de itens quando a agregação não for semanticamente válida. Atualizar wireframes e AC antes do código.
2. **Timeline:** é trilha de eventos de processo **derivada das fontes consultadas**, não histórico auditável completo. Usar rótulos como «Acompanhamento»/«Eventos disponíveis» e explicitar lacunas.
3. **PC 404:** a rota só consulta pedidos abertos; 404 não demonstra por si só conclusão do pedido. Evitar mensagem categórica «concluído» e distinguir não localizado/filtro/indisponibilidade conforme contrato comprovado. D1 deve ser decidido antes de EN.A6.
4. **Navegação e escopo:** vínculos SC↔PC exigem preservar chave composta (filial, documento e item quando material), AuthZ efetiva e escopo CC da SC no producer; link técnico não é concessão de acesso. Cobrir 403/404 e evitar vazamento de dados.
5. **Metadados documentais:** o cabeçalho dos documentos registra `2026-06-06`, incompatível com a entrega de 24/10/2026. Corrigir a data editorial mantendo o `BASE HEAD` histórico sem reescrever evidências.

**Sequência recomendada:** corrigir somente estes pontos documentais e promover decisões mínimas D1 (404 PC) e D2 (exposição de campos opcionais/sensíveis) ao PO; então planejar/autorizar EN.A1–A7 em fatias com testes positive+sibling+negative. EN.B–D permanecem apenas propostas. `NO_CODE_CHANGE`, `NO_DEPLOY`.
