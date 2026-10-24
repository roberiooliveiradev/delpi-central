# SC/PC Detail Enrichment — P0 (Discovery, Inventário e Proposta)

> Status: `DISCOVERY_COMPLETE` · `IMPLEMENTATION_NOT_AUTHORIZED` · `NO_CODE_CHANGE`
> Baseline: `f89e73376c` · Data editorial: 2026-10-24 (corrigida em P0.R1) · Autor: Devin (investigação read-only)
> Documentos do pacote: `SC-PC-DETAIL-DATA-CONTRACT-MATRIX.md` ·
> `SC-PC-DETAIL-UX-WIREFRAMES.md` · `SC-PC-DETAIL-IMPLEMENTATION-ROADMAP.md`

## 1. Resumo executivo

O levantamento provou que as fichas de Detalhe da SC e Detalhe do PC renderizam
hoje **apenas uma fração** do que já chega ao MFE:

- **SC:** o produtor (`purchase-requests-api` + `api-delpi`) já emite — e o BFF
  repassa integralmente — pedidos vinculados por item, recebimentos, totais
  solicitado/pedido/recebido, datas de primeira/última emissão e recebimento,
  aprovador, fornecedor sugerido, UM, data de necessidade, saldo, resíduo e uma
  **coleção `timeline` de eventos derivados** (não é auditoria — ver §P0.R1).
  O `types.ts` do MFE declara ~30% disso.
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
| `PROVEN_IN_BFF` | CC c/ descrição, pedidos vinculados, fornecedores, 1ª/últ. emissão e recebimento, totais solicitado/pedido/recebido ⚠¹, atraso (has/max dias), UM, necessidade, qtd pedida, saldo, aprovador(nome), fornecedor sugerido, conta, resíduo, pedidos por item c/ recebimentos+delivery+comprador, eventos derivados da timeline | — (passthrough; campos extras não existem no produtor) |

⚠¹ **Totais de quantidade agregados sem distinção de UM** (`_aggregate_header` soma
`C1_QUANT`/`C1_QUJE`/`C7_QUJE` por todas as linhas, sem agrupar por `unit` nem
converter) e **somente sobre as linhas autorizadas pelo escopo de CC** — não são
indicador único confiável quando a SC mistura UMs (UN/MT/KG/PC) ou quando o usuário
vê subconjunto da solicitação. Ver §P0.R1 e matriz.
| `TO_INVENTORY` | aprovador c/ identidade portal; histórico auditável | nome do comprador, `C7_UM`, `C7_COND`, `C7_MOEDA`, `C7_OBS/MSG`, `A2_CGC`+endereço, breakdown IPI/frete/desconto, `D1_NFORI/TES/TIPO` |
| `PLANNED` | próximo passo, dono da ação, comprador responsável | header agregado (total, recebido, situação geral), solicitante da SC origem, ocorrências/histórico de prazo |

## 6. Lacunas de contrato (`CONTRACT_GAPS`)

1. **Header agregado do PC ausente** — `compose_open_purchase_order` retorna só
   `{branch, order_number, items}`. Total do pedido / total recebido / situação
   geral exigem contrato novo na `api-delpi` (não somar no MFE).
2. **PC cobre apenas pedidos abertos** — `C7_QUANT > C7_QUJE` + `RESIDUO<>'S'` +
   `D_E_L_E_T_=''` + filial. 404 significa «não localizado entre os abertos
   consultáveis» — **não comprova** conclusão (pedido pode estar entregue,
   residual, excluído, em outra filial ou inexistente). **D1** — ver §P0.R1.
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
| D1 | Mensagem do 404 do PC — **A:** neutra «não localizado entre os pedidos em aberto» (sem contrato novo, recomendada); **B:** contrato de histórico/concluídos na api-delpi (futura) | EN.A6 |
| D2 | Expor `approver_name`, `suggested_supplier`, `account_code` — recomendação: aprovador sim (junto ao badge); fornecedor sugerido sim, rotulado «sugerido»; conta contábil **não** na área principal sem validação funcional | EN.A1–A3 |
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
  aprovação, UM/necessidade/saldo **por item**, eventos derivados via
  `SuppliesEventsSection` (rótulo «Acompanhamento», não auditoria) — **sem KPI
  único de quantidade** (UMs heterogêneas, §P0.R1); links SC↔PC com tratamento
  neutro de 403/404; PC: link SC origem + copy neutra de 404 (após D1).
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

---

## P0.R1 — Reconciliação GPT / Product Architecture (2026-10-24)

Respostas aos 5 residuais da revisão GPT, com evidência de código em `HEAD`.

### R1.A — Semântica de quantidades e UMs

**Evidência:** `purchase_request_aggregation_service._aggregate_header` soma
`requested_total += C1_QUANT`, `ordered_total += C1_QUJE` e
`received_total += C7_QUJE` (por pedido) **sem agrupar por `line.unit`
(`C1_UM`) e sem conversão**. Cada item da SC traz sua própria UM
(`lines_sql.py:310`). Além disso, `build_detail_payload` agrega **apenas as
linhas que passaram por `filter_authorized_lines`** (escopo de CC do usuário).

**Conclusão:** os três totais de `header` existem no contrato mas **não são
indicador único confiável** quando (a) a SC mistura UMs ou (b) o usuário tem
visão parcial da SC. Em ambos os casos o número pode parecer um total da
solicitação inteira e induzir decisão errada.

**Decisão documental:** a Fase A **não exibe** `requested/ordered/received_quantity`
como KPI de header. Substitutos semanticamente seguros: contagem de itens,
contagem de pedidos vinculados, contagem de recebimentos, quantidades **por
item com sua UM** e situação por item. Agrupamento por UM = `PLANNED`
(exigiria contrato novo no produtor; não é quick win).

### R1.B — Semântica da timeline

**Evidência:** `_build_timeline` (agregação :499) emite 4 tipos derivados:
`request_created` (C1_EMISSAO), `purchase_order_created` (C7_EMISSAO),
`expected_delivery` (C7_DATPRF — **data planejada, não evento passado**) e
`receipt` (D1_DTDIGIT). Não cobre aprovação, alteração de prazo, cancelamento,
bloqueio nem encerramento residual.

**Decisão documental:** seção rotulada **«Acompanhamento»** (padrão UX do
portal) — nunca «Histórico completo»/auditoria. `expected_delivery` exibido
como marco de *previsão*, não como ocorrência. Lacunas explicitadas no hint
da seção. Auditoria real = `PLANNED` (EN.D2, fonte não provada).

### R1.C — Semântica do 404 do PC

**Evidência:** `get_open_order`/`build_purchase_orders_list_filters`
(`purchase_orders_list_sql.py:178-205`) exigem `C7_QUANT > C7_QUJE`,
`C7_RESIDUO <> S`, `D_E_L_E_T_ = ` e filial válida → 404 cobre: entregue,
residual, logicamente excluído, outra filial ou inexistente.
**Não comprova conclusão.**

**D1 — pronta para PO:**
- **Opção A (recomendada, Fase A, zero contrato novo):** copy neutra
  «Pedido não localizado entre os pedidos em aberto disponíveis para
  consulta.» Não afirma conclusão; sem backend.
- **Opção B (futura):** contrato de consulta a pedidos concluídos/histórico
  na `api-delpi`, somente se houver necessidade de negócio — `PLANNED`, fora
  da Fase A.

### R1.D — Links SC↔PC e autorização

**Evidência:** chaves compostas reais — SC→PC: `C7_NUMSC`+`C7_ITEMSC` por
linha (1:N); PC→SC: `source_request_number`/`source_request_item` por item
(N:1 por item). Ambas as rotas MFE existem. **AuthZ difere:** SC detail exige
`can_use_purchase_requests` + `@require_unit` + **escopo de CC no produtor**
(pode renderizar SC parcial ou 404); PC detail exige `can_use_operations` +
`@require_unit`. Um mesmo usuário pode ter acesso a uma ficha e 403 na outra.

**Decisão documental:** links técnicos **não** são concessão de acesso —
autorização permanece server-side no BFF. Destino 403/404 → mensagem neutra
«Conteúdo não disponível para o seu perfil» / «registro não localizado»,
sem vazar dados; retorno à ficha anterior preservado (`?from=`). Nenhum link
para rota inexistente.

### R1.E — Metadados editoriais

Data `2026-06-06` → `2026-10-24` nos 4 documentos; baseline SHA, evidências e
SHAs preservados.

### R1.F — D2: campos opcionais da SC (pronta para PO)

| Campo | Chega ao BFF? | Produtor | Fonte TOTVS | Sensibilidade | Recomendação |
|---|---|---|---|---|---|
| Nome do aprovador (`approval.approver_name`) | Sim (passthrough) | purchase-requests-api ← api-delpi | `C1_NOMAPRO` (`lines_sql.py:328`) | Dado pessoal (nome), mesma classe do solicitante já exibido | **Exibir** quando presente, junto ao badge de aprovação — decisão pendente apenas de posição |
| Fornecedor sugerido (`suggested_supplier{code,store,name}`) | Sim | idem | `C1_FORNECE`/`C1_LOJA` + SA2 (`:330-332`) | Comercial leve — sugestão ≠ contratado | **Exibir** sempre rotulado «Sugerido», nunca como fornecedor do pedido; por item ou seção secundária |
| Conta contábil (`account_code`) | Sim | idem | `C1_CONTA` (`:326`) | Potencial sensibilidade contábil/interna | **Não exibir** na área principal; seção técnica secundária somente após validação funcional do PO |

`supplies.access` + escopo CC autorizam os três campos conforme contrato
vigente — a decisão é de **exposição de produto**, não de permissão nova.

### R1.G/H — Wireframes e roadmap

Wireframes desktop/mobile reconciliados em `SC-PC-DETAIL-UX-WIREFRAMES.md`
(v2): sem KPI único de quantidade, «Acompanhamento» no lugar de «Histórico»,
previsão vs. eventos separados, 404 neutro, PC sem dias de atraso (campo não
existe no contrato PC — só `delivery_status`), links com tratamento 403/404.
Roadmap atualizado em `SC-PC-DETAIL-IMPLEMENTATION-ROADMAP.md` (EN.A* com
dados comprovados/excluídos, decisões e stop conditions por etapa).

**Resultado P0.R1:** pacote consistente; **Fase A avaliada como READY_FOR_PO**
— todas as etapas EN.A1–A7 têm dados provados, decisões D1/D2 prontas e
nenhuma dependência de contrato novo.


## Revisão GPT — P0.R1 (2026-10-24)

**Veredito: `ACCEPT_WITH_RESIDUAL` para reconciliação documental; `FASE_A_READINESS=READY_FOR_PO`; `IMPLEMENTATION_NOT_AUTHORIZED` permanece.** Conferidos os quatro documentos da revisão `ab67150ce8`: inventário, matriz de contratos, wireframes v2 e roadmap EN.A1–A7. Foram incorporados os cinco residuais: soma transversal de quantidades sem agrupar por UM retirada dos KPIs propostos; `timeline` descrita como «Acompanhamento» com `expected_delivery` explicitamente previsto; 404 de PC aberto com texto neutro, sem inferir conclusão; vínculos SC↔PC com chaves compostas e autorização distinta por owner/escopo CC; datas editoriais corrigidas para 2026-10-24 sem alterar o baseline histórico.

**Decisões ainda reservadas ao PO:** **D1**, recomendar opção A, mensagem «Pedido não localizado entre os pedidos em aberto disponíveis para consulta», sem contrato novo; **D2**, recomendar nome do aprovador junto ao estado de aprovação e fornecedor identificado explicitamente como **sugerido**, quando entregues e autorizados; não mostrar conta contábil na ficha principal nesta fase. Até deliberação explícita do PO, não tratar recomendações como decisões aprovadas. **D3–D6** seguem `PLANNED/TO_INVENTORY` fora de EN.A. Links relacionados não conferem acesso automático e não devem mascarar 403/404. Nenhum teste de aplicação, runtime ou deploy foi executado nesta revisão; a execução anterior foi somente documentação.

**Próximo gate:** decisão PO D1/D2 → autorização separada das fatias EN.A1–A7, com verificação do HEAD e dos payloads/contratos reais, testes positivos/irmãos/negativos e Help sincronizada.
