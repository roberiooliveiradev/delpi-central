# Factory Supply — Domain Model (Documentation 2/5)

> **Status:** domain + state machines + data + contract model — Documentation 2/5, com correção bounded aplicada (grain do agregado + idempotência)
> **Escopo:** modelo de domínio conceitual. **Não** define rotas HTTP, SQL, migrations, schemas físicos, permissões ou código.
> **Baseline aceito:** `docs/12-roadmap-e-evolucao/factory-supply/README.md` (Doc 1/5).
> **Natureza:** documentação canônica. Nada aqui autoriza implementação.

---

## 1. Purpose and status

Este documento define o modelo de domínio do Factory Supply antes de frontend, API e implementação: conceitos, fronteiras de agregado, dimensões de estado, semântica de quantidades, correlação com fatos ERP, comandos/consultas conceituais, invariantes, exceções, concorrência, idempotência e auditoria.

Classificações (`PROVEN` / `PLANNED` / `TARGET` / `TO_INVENTORY`) conforme Doc 1/5 § 1. Todo o modelo abaixo é `TARGET` salvo indicação explícita de `PROVEN` (evidência do Line Feeder de referência) ou `PLANNED` (direção aprovada).

## 2. Accepted architecture baseline

Preservado de Doc 1/5, sem reabertura:

| Decisão | Valor |
|---|---|
| Nome técnico / user-facing | `factory-supply` / Abastecimento Fabril |
| Boundary | capability de produto distinta (`PLANNED`, Product Master) |
| `production-control` / `line-feeder` | `PROVEN_REFERENCE_IMPLEMENTATION` |
| `production-control-api` como backend-alvo | `REJECTED_BY_PRODUCT_ARCHITECTURE` |
| TOTVS | fonte autoritativa de ERP |
| api-delpi | fronteira atual de leituras TOTVS |
| TOTVS writes | `NOT_AVAILABLE_CURRENTLY` |
| Estado operacional | Factory Supply, Minha DELPI PostgreSQL (`PLANNED`) |
| MFE → api-delpi direto | proibido pelas regras canônicas; backend/BFF próprio é requerido |

## 3. Ubiquitous language

| Termo (EN técnico) | PT-BR | Definição |
|---|---|---|
| Supply Need | Necessidade de abastecimento | Fato derivado: material X, quantidade Y, destino Z, janela T — calculado de fontes autoritativas (programação + empenho). Não é entidade persistida por si; é projeção corrente. |
| Demand Signal | Sinal de demanda | Fato registrado de que uma necessidade foi expressa: planejada (sistema), pedida (operador), antecipada (alimentador) ou contextualizada (PCP). Persistido com proveniência. |
| Supply Mission | Missão de abastecimento | Unidade de trabalho operacional: levar um **conjunto de materiais** a **um destino operacional** dentro de uma janela de necessidade e contexto de produção correlacionados. Agregado raiz (§ 6). |
| Supply Mission Item | Item da missão | Linha material-específica da missão: material, unidade, ledger de quantidades e dimensões de estado próprias. |
| Preparation | Preparo | Trabalho do almoxarifado sobre um item: separar fisicamente o material. **Não** é reserva ERP. |
| Collection | Coleta | Retirada do material preparado pelo alimentador, por item. Fato operacional; uma viagem pode coletar vários itens. |
| Handoff | Entrega entre atores | Transferência de custódia operacional com ator, timestamp, quantidade, origem e destino; referencia missão + itens cobertos. |
| Operational Delivery | Entrega operacional | Chegada física registrada no destino (CT), por item. **Não** é movimento ERP. |
| ERP Movement Evidence | Evidência de movimento ERP | Observação correlacionada de movimento oficial (ex.: SD3 DE0/RE0), por material. Referência, nunca estado local reescrito. |
| Return | Devolução | Fluxo operacional de retorno produção → almoxarifado, por item/material. |
| Decision-Time Snapshot | Fotografia do momento da decisão | Cópia de fatos autoritativos no instante de uma decisão, preservada como evidência — nunca verdade corrente. |
| Work Center (CT) | Centro de trabalho / bancada | Destino operacional; identidade vem de contrato TOTVS (via api-delpi). |
| Pickup Location | Local de retirada | Local físico cadastrado (SBZ `BZ_MPLOCAL`), fotografado por decisão. |
| Collection Round | Viagem/rodada de coleta | Identidade da execução física da missão (o alimentador coleta os itens da missão); atributo da missão. |

## 4. Domain boundaries

```text
┌─ Factory Supply (bounded context) ──────────────────────────────┐
│  DemandSignal   SupplyMission(+Items)   Handoff   ReturnRecord  │
│  OperationalQuantities   ErpCorrelation   AuditTrail            │
└───────────────────────────────┬─────────────────────────────────┘
                                │ contratos de leitura (anti-corruption)
┌─ api-delpi ───────────────────┼──────────────────────────────────┐
│  SD4 empenho · SB2 saldo · SH8 fila · SBZ local · SD3 movimento   │
│  · SC2/SH1 OP/CT · SB1 produto                                    │
└───────────────────────────────┬──────────────────────────────────┘
                                │
                            TOTVS (autoridade ERP)
```

O domínio consome fatos ERP **somente** por portas (ports) — `TO_DESIGN` na Doc 4/5, espelhando o padrão `domain/ports/*_gateway.py` do BFF de referência (`PROVEN`). Nenhum campo TOTVS cru vaza para o modelo: o domínio fala em `supply_need`, `stock_balance`, `erp_movement` — não em `D4_QUANT`/`B2_QATU`.

## 5. Demand signal model

**Problema:** sinais de demanda distintos não podem se reescrever mutuamente.

**Modelo `TARGET`:**

```text
DemandSignal {
  signal_id        — identidade própria (não ERP)
  branch           — filial (obrigatório; boundary multi-filial)
  kind             — planned | operator_request | feeder_anticipation | pcp_context
  need_key         — chave de correlação: (branch, material, destination_ct, order?, operation?, need_window)
  payload          — quantidade, janela/tempo, contexto do sinal
  source           — actor_id (humano) | system (recálculo planejado)
  signal_version   — versão do sinal planejado para o mesmo need_key
  supersedes       — signal_id anterior, quando o sinal substitui outro
  status           — active | superseded | cancelled | fulfilled (via missão)
  occurred_at / recorded_at
}
```

Regras:

1. **Sinal é fato imutável.** Necessidade planejada às 10:00 e pedido do operador às 08:30 são **dois sinais** correlacionados pelo `need_key` — nenhum reescreve o outro (`PROVEN` como lacuna: hoje só existe a versão calculada, não persistida).
2. **Sinal planejado é recalculado.** Cada refresh que muda a necessidade emite novo `DemandSignal` de `kind=planned` para o mesmo `need_key`, com `supersedes` apontando o anterior. História preservada; `status=superseded` no antigo. Reemissão do **mesmo** fato planejado não cria novo sinal (deduplicação — § 19).
3. **Sinais humanos não são recalculados** — são cancelados ou atendidos, nunca "ajustados" por refresh.
4. **Correlação sem fusão:** sinais com mesmo `need_key` convergem para o mesmo item de missão (§ 6), mas permanecem fatos separados no rastro — o item referencia `signal_ids`, não os absorve.
5. `pcp_context` é informacional por padrão (anotação/contexto na necessidade); efeitos autoritativos de PCP `TO_INVENTORY` — depende de contratos existentes, não inventados aqui.

## 6. Aggregate decision — SupplyMission

### Avaliação pelo Abstraction Gate (necessidade de um agregado central)

| Critério | Evidência |
|---|---|
| Ciclo de vida real? | Sim — necessidade → preparo → coleta → entrega → devolução → encerramento/cancelamento, com transições por atores distintos (`TARGET`, Doc 1/5 § 8). |
| Invariantes reais? | Sim — quantidades parciais não-negativas, não-completude com pendências, boundary de filial, estados fechados não aceitam transições (§ 27). |
| Dono real? | Sim — Factory Feeder coordena execução; Warehouse Operator executa preparo; cada transição tem ator responsável. |
| Fronteira de consistência transacional? | Sim — ver avaliação de grain abaixo. |
| Reduz acoplamento? | Sim — é o hub de correlação entre sinais, preparo, coleta, handoffs, entrega, devolução e evidência ERP. |
| Conceito existente já satisfaz? | **Não.** `MaterialRequirement` é projeção derivada por leitura, sem persistência nem lifecycle (`PROVEN`, `line_feeder_requirements.py`). `PickPlan/PickItem` é lista batelada por corte — prova o padrão plano+itens, mas sem requerente, sem rastro por destino, sem devolução, sem correlação ERP (`PROVEN`, V006/V007). |

### Avaliação de grain (correção bounded aplicada)

Dois grains candidatos foram comparados:

| Grain | Resultado |
|---|---|
| **A) Missão por (material × destino × janela)** | `REJEITADO` — o trabalhador executa **uma** missão operacional multi-material: uma viagem ao CT-10 leva MP-A + MP-B + MP-C. Uma missão por material fragmentaria a unidade real de trabalho, multiplicaria handoffs artificiais para o mesmo ato físico e espalharia a decisão "o que vai nesta viagem" em N objetos. |
| **B) Missão por (destino × janela de necessidade × contexto) com itens por material** | `ACEITO` — espelha a execução real e o padrão `PROVEN` plano+itens (`create_plan` grava plano e itens na mesma transação — a fronteira transacional real já é essa). O que exige atomicidade é: cabeçalho da missão + coerência de estado/quantidade dos seus itens + registro de handoff cobrindo um subconjunto de itens. |

Guarda contra o grain excessivo (risco B do prompt): a missão **não** é "tudo para o CT-10". É delimitada por **destino + janela de necessidade + contexto de produção + atribuição**. Material para o CT-10 às 10:00 e às 18:00 são duas missões; material para outro CT é outra missão; uma necessidade fora da janela não entra na missão. Se a prática operacional exigir viagem multi-CT, `collection_round` pode virar entidade própria — `TO_DESIGN`, não agora.

### Decisão

```text
SUPPLY_MISSION_ACCEPTED — grain: mission + items
```

### Fronteira do agregado

`SupplyMission` (raiz) — responsabilidades de **nível de missão**:

- identidade (`mission_id`), `branch`;
- destino operacional (CT; `production_order`/`operation` como referência correlacionada, não chave estrita);
- janela de necessidade e `need_key` de correlação;
- atribuição (alimentador responsável) e identidade da viagem (`collection_round`);
- `lifecycle` (`open/closed/cancelled`) e encerramento com `reason`;
- auditoria mínima (§ 20).

`SupplyMissionItem` (dentro do agregado) — responsabilidades de **nível de item**:

- material, descrição, **unidade** (por item — nunca agregada entre unidades incompatíveis);
- ledger de quantidades (`required/requested/supply/prepared/collected/delivered/returned` — § 8);
- dimensões de estado do item: `preparation`, `collection`, `delivery`, `erp_evidence`, `return` (§ 9–10);
- referências aos `DemandSignal`s correlacionados;
- correlações ERP material-específicas (§ 16);
- snapshots de decisão (§ 17);
- exceções material-específicas (§ 14).

**Por que os itens estão dentro da fronteira:** handoff e entrega cobrem um subconjunto de itens da mesma missão e devem gravar atomicamente; o encerramento da missão verifica a resolução de **todos** os itens; quantidade de item só faz sentido contra destino/janela da missão. Item não existe fora de missão — mesmo padrão `PROVEN` de PickPlan+PickItem.

**Fora do agregado:** `DemandSignal` (vida própria, referenciada), `Handoff` (evento referenciando missão + itens), `ReturnRecord`, `ErpMovementObservation`, trilha de auditoria — entidades ligadas por referência, persistidas em grupos próprios (§ 21). O "preparo agregado por material" do almoxarifado é **view derivada** dos itens abertos (espelha o padrão `PROVEN`: necessidade por bancada → lista por produto), preservando o rastro por-destino que a lista por-produto atual perde.

## 7. Entity / value-object candidates

| Conceito | Tipo | Justificativa | Status |
|---|---|---|---|
| `SupplyMission` | Aggregate root | destino, janela, contexto, atribuição, viagem, lifecycle (§ 6) | `TARGET` |
| `SupplyMissionItem` | Entity (dentro do agregado) | material, unidade, quantidades, dimensões de item | `TARGET` |
| `DemandSignal` | Entidade (raiz leve própria) | fatos com proveniência independente; missão/item referencia | `TARGET` |
| `SupplyQuantities` | Value object (embarcado no item) | ledger semântico § 8 | `TARGET` |
| `NeedKey` | Value object | chave de correlação (branch, material, ct, janela, refs) | `TARGET` |
| `Handoff` | Entidade registrada | custódia ator→ator cobrindo subconjunto de itens | `TARGET` |
| `ErpMovementObservation` | Entidade de correlação | por item/material (§ 16) | `TARGET` |
| `ReturnRecord` | Entidade | subfluxo de devolução por item (§ 15) | `TARGET` |
| `OperationalEvent` (audit) | Entidade append-only | trilha de transições (§ 20) | `TARGET` |
| `MaterialRequirement` (leitura) | Value/projeção derivada | computada por leitura dos contratos ERP; **não persistida como verdade** | `PROVEN` (padrão do Line Feeder) |
| `PickPlan`/`PickItem` (legado) | — | § 22 — não adotados como modelo-alvo; provam o padrão raiz+itens | `PROVEN_REFERENCE` |

## 8. Quantity semantics

Quantidades vivem **no item** (por material). Cada uma tem **um** significado, **um** dono e **uma** unidade — `unit` do item via contrato SB1. Nunca agregar unidades incompatíveis: soma só dentro do mesmo (item/material, unidade). Totais exibidos na missão são somas **por unidade**.

| Quantidade | Significado | Dono | Fonte | Autoritativa? | Mutável? |
|---|---|---|---|---|---|
| `required_qty` | Quanto a necessidade planejada exige para este item (saldo em aberto do empenho) | TOTVS | leitura api-delpi (SD4 `open_qty`) + snapshot no item | Sim (ERP) | Recomputa na fonte; no item é snapshot histórico |
| `requested_qty` | Quanto um sinal humano pediu para este item | Factory Supply | `DemandSignal` (operador/alimentador/PCP) | Não — é pedido, não fato ERP | Não (sinal imutável; novo sinal supersede) |
| `supply_qty` | Quanto a missão pretende cobrir neste item | Factory Supply | decisão na criação/planejamento | Não | Sim, por correção auditada (razão obrigatória) |
| `prepared_qty` | Quanto o almoxarifado separou para o item | Factory Supply | `RecordPreparedQuantity` | Não | Acumula por registros; correção exige razão |
| `collected_qty` | Quanto o alimentador retirou do item | Factory Supply | handoff warehouse→feeder | Não | Acumula por handoffs |
| `delivered_qty` | Quanto do item chegou operacionalmente ao destino | Factory Supply | handoff feeder→CT | Não | Acumula por entregas |
| `erp_transferred_qty` | Quanto o ERP registra movimentado deste material | TOTVS | observação correlacionada (SD3) | Sim (ERP) | Nunca escrita localmente |
| `erp_consumed_qty` | Quanto o ERP registra baixado deste material | TOTVS | observação (SH6/consumo) | Sim (ERP) | Nunca |
| `return_required_qty` | Quanto deveria voltar | **TO_INVENTORY** — fórmula autoritativa indefinida | § 15 | — | — |
| `returned_qty` | Quanto do item voltou operacionalmente | Factory Supply | handoffs CT→feeder→almoxarifado | Não | Acumula |

Invariantes de quantidade (por item): `0 ≤ delivered_qty ≤ collected_qty` (não se entrega mais do que se coletou), `collected_qty ≤ prepared_qty` (não se coleta mais do que o separado — tolerância/`reason` se exceção operacional for aceita, `TO_DESIGN`), e nenhuma quantidade derivada de outra silenciosamente — cada uma é fato registrado.

## 9. Lifecycle dimensions

O modelo usa **dimensões independentes**, não um enum gigante — e agora separadas por nível:

**Nível missão:**

| Dimensão | Estados | Significado |
|---|---|---|
| `lifecycle` | `open` → `closed` \| `cancelled` | Guarda-chuva de aceite de trabalho; encerramento cobre todos os itens |

**Nível item (por material):**

| Dimensão | Estados | Significado |
|---|---|---|
| `preparation` | `not_started` → `in_progress` → `prepared` | Separado no almoxarifado |
| `collection` | `not_collected` → `collected` | Custódia passou ao alimentador |
| `delivery` | `not_delivered` → `delivered` | Chegada operacional no destino |
| `erp_evidence` | `unobserved` → `correlated` \| `divergent` \| `not_found` | Observação do movimento oficial — estado de correlação, não posse |
| `return` | `not_applicable` → `requested` → `in_return` → `received` → `reconciled` | Subfluxo de devolução (§ 15) |

Estados são nominais; a **quantidade** carrega a parcialidade (item com prepared 80 de 100 mantém `preparation=in_progress`, não inventa "meio-preparado"). Itens da mesma missão progridem independentemente — MP-A pode estar `delivered` enquanto MP-B segue `in_progress`.

## 10. State machines

Autorização por transição: modelo resolvido no Doc 4/5 (§40-A, FROZEN FS-C0.T3) — toda transição de usuário exige `factory-supply.access` + `factory-supply.view.filial-{branch}`; não há permissão por transição. "Ator" abaixo é papel de negócio, não permission code.

### 10.1 `lifecycle` — nível missão

| Transição | Trigger | Precondição | Ator | Registra | Idempotência | Auditoria |
|---|---|---|---|---|---|---|
| → `open` | `PlanSupplyWork` | destino+janela resolvidos; ≥1 item com sinais correlacionados | sistema ou ator autorizado | itens, `supply_qty` por item, snapshots | `REQUIRED` | criação |
| `open` → `closed` | `CloseMission` | todo item resolvido (§ 12) ou fechamento com `reason` de exceção | ator autorizado | `closed_at/by`, `reason` | `REQUIRED` | sempre |
| `open` → `cancelled` | `CancelMission` | missão aberta | solicitante ou autorizado | `cancelled_at/by`, `reason`, sinais liberados | `REQUIRED` | sempre |
| `closed/cancelled` → *qualquer* | — | **proibido** (terminal) | — | — | — | tentativa registrada como rejeitada |

### 10.2 `preparation` — nível item

| Transição | Trigger | Precondição | Ator | Registra | Idempotência | Auditoria |
|---|---|---|---|---|---|---|
| `not_started` → `in_progress` | `StartPreparation` | item de missão `open` | Warehouse | `started_at/by` | `REQUIRED` | sempre |
| `in_progress` → `prepared` | `RecordPreparedQuantity` quando acumulado ≥ `supply_qty` | qty > 0 | Warehouse | `prepared_qty` acumulado, snapshot de saldo visto | `REQUIRED` | cada registro |
| `prepared` → `in_progress` | correção com `reason` | coleta ainda não consumiu o preparo | Warehouse | correção, razão | `REQUIRED` | sempre |

`prepared` **não** implica reserva ERP (decisão Doc 1/5). Saldo observado no preparo é snapshot de evidência (§ 17).

### 10.3 `collection` — nível item

| Transição | Trigger | Precondição | Ator | Registra | Idempotência | Auditoria |
|---|---|---|---|---|---|---|
| `not_collected` → `collected` | `RecordCollection` (handoff warehouse→feeder cobrindo itens) | `prepared_qty` > 0 coletável | Feeder (+ Warehouse na contraparte) | `collected_qty` por item, handoff, `collection_round` | `REQUIRED` | sempre |

Um handoff de coleta pode cobrir vários itens — ou um subconjunto (coleta parcial em itens, não só em quantidade). Handoffs adicionais (2ª viagem) são eventos novos; o estado permanece `collected`.

### 10.4 `delivery` — nível item

| Transição | Trigger | Precondição | Ator | Registra | Idempotência | Auditoria |
|---|---|---|---|---|---|---|
| `not_delivered` → `delivered` | `RecordOperationalDelivery` (handoff feeder→CT) | `collected_qty` > 0 | Feeder | `delivered_qty` por item, handoff, destino confirmado | `REQUIRED` | sempre |

Entrega operacional **não** é movimento ERP nem consumo — separação preservada.

### 10.5 `erp_evidence` — nível item (correlação, não posse)

| Transição | Trigger | Precondição | Ator | Registra | Idempotência | Auditoria |
|---|---|---|---|---|---|---|
| `unobserved` → `correlated` | `ObserveErpMovement` encontra movimento compatível | leitura api-delpi disponível | sistema | referência do movimento (doc/série/data/qty), confiança | `REQUIRED` (deduplicação na persistência — § 19) | sempre |
| `unobserved` → `not_found` | busca sem match na janela | leitura realizada | sistema | janela consultada, `searched_at` | `REQUIRED` | sempre |
| `correlated` → `divergent` | observação posterior contradiz quantidade/janela | evidência nova | sistema | divergência detalhada | `REQUIRED` | sempre |

Re-leitura ERP pura não é idempotente nem não-idempotente — é `NOT_APPLICABLE` (§ 19): a idempotência exigida é sobre **o que persistimos** da observação. `not_found` é factual ("procuramos, não achamos"), nunca "quantidade zero".

### 10.6 `return` — nível item

§ 15 — máquina `requested → in_return → received → reconciled` por item; AuthZ = `access`+`view.filial-*` (Doc 4/5 §40-A) por transição; quantidade autoritativa `TO_INVENTORY`.

### 10.7 Sinais de demanda

`active → superseded` (novo sinal planejado do mesmo `need_key` — só quando o fato mudou; reemissão idêntica é deduplicada, § 19), `active → cancelled` (necessidade some / pedido cancelado), `active → fulfilled` (item fechou cobrindo o sinal). Transições de sinal planejado são do sistema; humano, do autor ou autorizado.

## 11. Derived UX stage model

O estágio único do Kanban é **derivação pura** das dimensões dos itens + lifecycle da missão — nunca estado persistido:

```text
stage = derive(mission)   # função pura, determinística, sobre os itens

Cancelado    := lifecycle = cancelled
Encerrado    := lifecycle = closed
Em devolução := ∃ item com return ∈ {requested, in_return, received}
Entregue     := todo item com delivery = delivered ∧ nenhum return ativo
Pronto       := todo item pendente já coletado ∧ ∃ item com delivery = not_delivered
Em coleta    := ∃ item com preparation ∈ {in_progress, prepared} ∧ collection = not_collected
A separar    := caso contrário (missão open sem custódia iniciada)
```

Prioridade da derivação (cancelado > encerrado > devolução > entregue > pronto > em coleta > a separar) é candidata — `TO_DESIGN` na Doc 3/5 com a UX; o contrato expõe as dimensões, a coluna é computada. A granularidade por item permite card por missão com progresso parcial visível (ex.: "2/3 itens entregues") sem estado inventado. As colunas candidatas da Doc 1/5 § 13 são validadas contra este modelo em 3/5.

## 12. Partial fulfillment

Parcialidade é **quantidade e item**, não estado. Exemplo — missão CT-10 10:00 com MP-A `required=100 → prepared=80 → collected=70 → delivered=60` e MP-B completo:

- MP-A: `preparation=prepared`/`in_progress` conforme política de preparo parcial (`TO_DESIGN`), `collection=collected`, `delivery=delivered` — **mas** `unfulfilled_qty = supply_qty − delivered_qty = 40` derivado e visível;
- a missão **não** fecha como completa: `CloseMission` exige `reason` de fechamento-parcial e o déficit permanece no rastro;
- pendência residual pode gerar nova missão ou permanecer débito registrado — `TO_DESIGN`, nunca silenciosa;
- completude compara quantidades **por item**: "atendido" nunca vem do estado nominal da missão nem de agregação entre materiais.

## 13. Replanning and cancellation

| Cenário | Tratamento |
|---|---|
| Tempo planejado muda | Novo `DemandSignal` planejado supersede o anterior; item/missão abertos recebem o novo sinal correlacionado — janela corrente = sinal mais recente, história intacta |
| CT muda | Mudança de destino afeta a **missão inteira**: correção de destino com `reason` (se ainda sem custódia) ou cancelamento + nova missão (se custódia iniciada) — `TO_DESIGN` qual política, nunca silenciosa |
| Quantidade requerida muda | Sinal supersede por item afetado; `supply_qty` só muda por decisão registrada, nunca por refresh |
| Necessidade desaparece | Sinal → `cancelled`; item sem sinal ativo → exige cancelamento do item ou confirmação explícita; missão sem itens vivos → `CancelMission` |
| Preparo/coleta já iniciados | Cancelamento permitido com trilha de reversão ao almoxarifado registrada — nunca delete |
| Operador cancela pedido | Sinal humano → `cancelled`; item/missão reavaliam sinais ativos restantes |
| Pedido duplicado | Correlação por `need_key` + idempotência de criação (§ 19); duplicado real → sinal próprio superseded/cancelled, não item duplicado |
| Pedido superseded por novo planejamento | Mesma mecânica de supersede |
| Item cancelado em missão multi-material | Cancelamento por item é `TO_DESIGN` — avaliar se cancelar item exige evento próprio ou cancela a missão quando último item vivo cai |

**Nada é deletado.** Intenção corrente (sinais `active`) e evidência histórica (`superseded`/`cancelled`, eventos) coexistem — é a própria razão do produto.

## 14. Exception model

Exceções podem ser **por item** (material-específicas) ou **por missão**:

| Exceção | Nível | Tratamento |
|---|---|---|
| Estoque insuficiente | item | `supply_qty` limitada à decisão informada; risco derivado (`at_risk` `PROVEN`) |
| Saldo indisponível | item/leitura | `unknown` — não afirmar cobertura nem zero (`PROVEN`); criação exigindo saldo falha fechada (`PROVEN`: `create_pick_plan` → 502) |
| Local de retirada ausente | item | campo vazio + flag; nunca local inventado (`PROVEN`: SBZ ausente → sem local) |
| Empenho indisponível | leitura | erro de gateway, sem degradação silenciosa (`PROVEN`) |
| Operação remanejada | missão | § 13 supersede de sinal / mudança de janela |
| Necessidade cancelada | item→missão | § 13 |
| Preparo/coleta/entrega parcial | item | § 12 quantidades |
| Movimento ERP não encontrado | item | `erp_evidence=not_found` + janela registrada; não bloqueante |
| Movimento ERP diverge do operacional | item | `erp_evidence=divergent`; nenhum lado reescrito |
| Comando duplicado/replay | qualquer | § 19 — mesmo efeito, mesmo resultado, sem duplicar registro |
| Transição concorrente | missão/item | § 18 expected-state — segundo ator recebe conflito |
| Quantidade de devolução indisponível | item | `RETURN_QUANTITY_RULE=TO_INVENTORY`; `returned_qty` factual sem afirmar "quanto devia" |
| Destino de devolução não resolvido | item | retorno para em `in_return`/`received` sem `reconciled` |
| CT/operação/material sem cadastro | missão/item | contrato autoritativo decide; domínio nunca fabrica identidade ERP |
| Material de item fora do escopo MP | item | elegibilidade por `product_type` (`PROVEN`: só `MP`; fail-closed sem tipo cadastrado) |

## 15. Return domain

`TARGET` conceitual — nada de devolução está implementado hoje.

```text
RETURN_QUANTITY_RULE = TO_INVENTORY
```

A fórmula autoritativa (ex.: candidatos `saldo_ponto_uso − empenho` visíveis no Power BI) **não** é regra de negócio até provada em contrato — frontend nunca computa quantidade de devolução (Doc 1/5 § 17).

O que o domínio modela **independente** da fórmula, **por item**:

- `ReturnRecord` por item de missão: `requested_qty?` (declarada, se houver), `returned_qty` (factual, acumulada por handoffs CT→feeder→almoxarifado), destino de retorno, motivo;
- dimensão `return` no item: `not_applicable → requested → in_return → received → reconciled`;
- `reconciled` exige quantidade esperada resolvida por fonte autoritativa — enquanto `TO_INVENTORY`, reconciliação é manual/declarativa e assim rotulada;
- devolução sem item de origem correlacionado é possível (material avulso) — `need_key` opcional no retorno, `TO_DESIGN` se vira entidade solta.

## 16. ERP correlation

Correlação referencia fatos autoritativos; nunca copia autoridade nem fabrica IDs ERP. **Por item** (material-específica):

```text
ErpMovementObservation {
  item_id, mission_id, branch,
  movement_kind        — ex.: warehouse_transfer (DE0→RE0)
  erp_document_ref     — documento/série/data conforme o contrato expõe (SD3)
  material, observed_qty, observed_at (data do ERP), warehouses
  match_confidence     — correlacao heuristicamente encontrada | confirmada
  correlation_basis    — campos usados no match
}
```

`need_key` (em sinal e item): `(branch, material, destination_ct, planned_window, production_order?, operation?)` — `?` = correlacionado quando disponível, **nunca** obrigatório se o ERP não garante. `TO_INVENTORY`: o contrato SD3 não expõe ID causal estável ligando movimento a intenção operacional — a correlação é por **coincidência de atributos** (material+armazéns+quantidade+janela), registrada com `match_confidence` e `correlation_basis`; divergência futura reabre `divergent`. Filial é sempre parte da identidade (`PROVEN`: repository filtra tudo por `branch`). Observar o mesmo movimento duas vezes não duplica correlação (§ 19).

## 17. Decision-time evidence

| Momento | Evidência preservada | Nível | Padrão de referência |
|---|---|---|---|
| Cálculo de necessidade | `required_qty`, saldos observados, janela programada, empenho fonte | item | `PROVEN` — pick item fotografa `required_qty`/`point_of_use_qty`/`to_deliver_qty` |
| Criação da missão | destino, janela, sinais vigentes, `supply_qty` decidida por item | missão+item | `TARGET` |
| Registro de preparo | saldo autoritativo visto naquele instante | item | `TARGET` |
| Coleta/handoffs | quantidade, atores, timestamps, `collection_round` | item/handoff | `PROVEN` como padrão (`pickup_location` fotografado) |

Invariante: snapshot é **evidência histórica**; o valor corrente é sempre reconsultado na fonte. Nenhum read path resolve saldo "pela tabela do Factory Supply".

## 18. Concurrency

Múltiplos almoxarifados/alimentadores podem agir sobre a mesma missão/item. Requisitos conceituais:

- **Versão otimista** por agregado (`version` na missão; item transiciona sob a versão da missão ou versão própria — `TO_DESIGN` qual o nível físico, o invariante é: comando declara a versão observada e divergência → conflito, não sobrescrita). `PROVEN` como lacuna: o repositório atual faz last-write-wins (`update_item_status` sem versão nem checagem de estado anterior).
- **Transição com expected-state:** comando declara o estado de onde parte; implementação valida atomicamente (ex.: UPDATE condicional).
- **Chave de idempotência** nos comandos de mutação (§ 19).
- **Cliente stale:** leitura expõe `version` + dimensões; escrita com versão velha recebe conflito explícito — o cliente re-ler e redecidir, nunca retry cego que fabrica transição contraditória.
- **Invariante:** dois atores concorrentes nunca produzem silenciosamente transições contraditórias — exatamente um "vence"; o outro recebe conflito visível. Isto vale também para dois atores em **itens diferentes** da mesma missão: eventos de item são independentes, mas writes no cabeçalho (fechar, atribuir) respeitam a versão da missão.

## 19. Idempotency

Correção bounded aplicada — distinguir **leitura ERP pura** de **efeito local persistido**:

| Comando/categoria | Classificação |
|---|---|
| Leitura ERP autoritativa pura (sem persistir nada) | `IDEMPOTENCY = NOT_APPLICABLE` |
| Observação ERP que persiste correlação/transição local (`ObserveErpMovement`) | `IDEMPOTENCY_REQUIRED` — repetir a observação do **mesmo** movimento não duplica correlação nem efeito (dedup por identidade do movimento observado) |
| `SyncPlannedNeeds` (cria/supersede/muta `DemandSignal` local) | `REPLAY_SAFE / IDEMPOTENT = REQUIRED` — ressincronizar o mesmo fato planejado não cria sinais ativos duplicados (dedup por `need_key` + fingerprint do fato) |
| `RequestMaterial`, `AnticipateSupply` | `IDEMPOTENCY_REQUIRED` (chave do cliente) |
| `PlanSupplyWork` (criação de missão+itens) | `IDEMPOTENCY_REQUIRED` |
| `StartPreparation`, `RecordPreparedQuantity`, `RecordCollection`, `RecordHandoff`, `RecordOperationalDelivery` | `IDEMPOTENCY_REQUIRED` — retry de rede não dobra quantidade nem duplica handoff |
| `RequestReturn`, `RecordReturnProgress`, `RecordReturnReceipt`, `ReconcileReturn` | `IDEMPOTENCY_REQUIRED` |
| `CancelMission`, `CancelSignal`, `CloseMission` | `IDEMPOTENCY_REQUIRED` (terminal) |
| Todas as queries | `IDEMPOTENCY_NOT_REQUIRED` |

Mecanismo de chave/transporte: `TO_DESIGN` (Doc 4/5 — headers/payloads não definidos aqui).

## 20. Audit / history

Trilha mínima por escrita material:

```text
who        — actor autenticado (identity do backend, não input do cliente)
when       — timestamp de registro (+ occurred_at quando difere)
what       — comando + transição (nível missão/item, dimensão, from → to)
quantity   — delta e acumulado resultante quando aplicável (por item)
reason     — obrigatório em correções, exceções, cancelamentos, fechamento parcial
correlation— mission_id, item_id, signal_ids, handoff, erp_movement_ref quando houver
command_id — chave de idempotência do comando
```

Registro **append-only**: transições são fatos; estado corrente é materializado. Padrão `PROVEN` parcial no legado (`created_by/at`, `updated_by/at`) — alvo exige trilha por transição, não só último escritor.

### Event sourcing?

```text
EVENT_SOURCING_REQUIRED = NO
```

Abstraction Gate: auditoria append-only cobre rastreabilidade exigida; não há necessidade provada de rebuild por replay, projeções temporais ou integração por eventos. História auditável ≠ event sourcing. Se Doc 4/5+ evidenciar projeção temporal real, reavaliar com evidência.

## 21. Persistence ownership

Postgres Minha DELPI, schema dedicado (`PLANNED`). Grupos lógicos — **nomes físicos não congelados**:

| Grupo lógico | Contém | Natureza |
|---|---|---|
| demand_signals | sinais com proveniência e supersede-chain + dedup fingerprint | owned |
| supply_missions | identidade, branch, destino, janela, contexto, atribuição, `collection_round`, lifecycle, versão | owned |
| supply_mission_items | material, unidade, ledger de quantidades, dimensões de item, signal refs | owned (mesmo agregado/transação que a missão) |
| handoffs | eventos de custódia referenciando missão + itens | owned |
| erp_correlations | observações de movimento ERP + confidence, por item | owned (referência, não cópia de verdade) |
| return_records | dados de devolução por item | owned |
| operational_events | trilha append-only de auditoria | owned |
| decision_snapshots | evidências do momento da decisão | owned (evidência, não verdade corrente) |

Separados por natureza: **owned** (workflow), **referenced** (fatos ERP — só referências), **snapshot** (evidência histórica). `platform-data-persistence` governa migrations/transações — nada executado aqui.

## 22. Existing Line Feeder migration relationship

| Elemento atual | Classificação | Racional |
|---|---|---|
| `line_feeder_pick_plans` / `line_feeder_pick_items` (tabelas e linhas) | `KEEP_LEGACY_REFERENCE` | Permanecem propriedade do PCP/Line Feeder; não migrar linhas sem cutover decidido; histórico consultável onde está |
| Padrão raiz+itens em uma transação | `GENERALIZE` | Confirmado como a fronteira transacional correta do agregado SupplyMission+Items |
| Conceito de lista de coleta por corte | `GENERALIZE` | Evolui para missões (destino+janela) + views derivadas por material |
| `pending/picked/delivered` | `GENERALIZE` | Informa as dimensões collection/delivery por item; free-form vira máquina com transições |
| Snapshot de decisão no item (`required_qty` etc.) | `GENERALIZE` | Vira padrão de decision-time evidence (§ 17) |
| Grain por-produto sem destino por linha | `REJECTED` para o alvo | Perde o rastro por destino; alvo mantém item por material dentro da missão com destino |
| Motor de necessidade + FIFO + `unknown` | `PROVEN_REFERENCE` para reuso conceitual | Lógica de cálculo candidata a porta/contrato na nova API (migração de código: `TO_DECIDE_LATER`) |

Implicação de migração (sem executar): convivência Line Feeder ↔ Factory Supply durante transição é `TO_DESIGN` (Doc 5/5 roadmap); nenhuma escrita cruzada entre schemas `production_control` e o futuro schema de factory-supply.

## 23. Operator request semantics

Domínio apenas (sem UI/endpoint):

```text
OperatorRequest (DemandSignal kind=operator_request) precisa de:
  branch, material, destination_ct (ou contexto de operação que o resolva),
  requested_qty + unit, need_window (quando precisa), actor autenticado, reason/contexto livre curto
```

Um pedido do cockpit **é sinal**: não autoriza movimento de estoque, não altera programação ERP, não muda prioridade, não cria transferência oficial. O sinal correlaciona a um item de missão pelo `need_key`; aceite/execução passam pelo workflow normal (validação de backend, AuthZ, decisão de missão).

## 24. Priority semantics

```text
PRIORITY_POLICY = TO_DESIGN
```

Entradas candidatas (sinais, nenhuma fórmula inventada): tempo planejado da necessidade (`first_scheduled_at` `PROVEN`), tempo do pedido do operador, criticidade de produção se autoritativa (`TO_INVENTORY` — `machine_load_priority` é candidata a reuso, não confirmada), risco de estoque (`at_risk`), estado do preparo.

Kanban consome a política; não a possui. Ordenação manual de cards nunca é prioridade de negócio.

## 25. Conceptual command catalog

Catálogo de domínio — **não são rotas HTTP**. AuthZ sempre `factory-supply.access`+`view.filial-{branch}` (Doc 4/5 §40-A, FROZEN) — sem permissão por comando. Nível = missão (M) ou item (I).

| Comando | Nível | Intent | Inputs conceituais | Result | Pré-condições | Dep. autoritativa | Efeitos | Idempotência |
|---|---|---|---|---|---|---|---|---|
| `SyncPlannedNeeds` | — | Recalcular sinais planejados | branch, janela/corte | sinais emitidos/superseded deduplicados | leituras ERP ok | SH8+SD4+SB2 via api-delpi | sinais; snapshot de cálculo | `REPLAY_SAFE REQUIRED` |
| `RequestMaterial` | — | Sinal humano de material | § 23 | `DemandSignal` ativo | destino/material resolvíveis | validação de material/CT via api-delpi | sinal; correlação a item | `REQUIRED` |
| `AnticipateSupply` | — | Antecipação do alimentador | material, destino/janela, qty | sinal `feeder_anticipation` | idem | idem | idem | `REQUIRED` |
| `PlanSupplyWork` | M | Decidir cobertura → missão+itens | destino, janela, itens {material, `supply_qty`, signal refs} | `SupplyMission` open | sinais ativos; saldo medido se a regra exigir | saldo via api-delpi | missão+itens+snapshots | `REQUIRED` |
| `StartPreparation` | I | Almoxarifado inicia separação | item_id, expected_version | preparation=in_progress | open, not_started | — | evento+audit | `REQUIRED` |
| `RecordPreparedQuantity` | I | Registrar separado | item_id, qty_delta, version | acumula; ≥supply_qty → prepared | in_progress | snapshot saldo | qty+evento | `REQUIRED` |
| `RecordCollection` | I(+handoff multi-item) | Feeder retira material | mission_id, itens {item_id, qty}, round? | collected nos itens; handoff warehouse→feeder | prepared_qty>0 | — | handoff+qty | `REQUIRED` |
| `RecordHandoff` | I(+evento) | Custódia genérica ator→ator | mission_id, itens {item_id, qty}, from/to role | handoff registrado | custódia coerente | — | handoff+qty | `REQUIRED` |
| `RecordOperationalDelivery` | I(+handoff) | Entrega no destino | mission_id, itens {item_id, qty}, handoff ref | delivered nos itens | collected_qty>0 | — | qty+handoff | `REQUIRED` |
| `ObserveErpMovement` | I | Correlacionar movimento oficial | item_id | erp_evidence transiciona | leitura disponível | SD3 via api-delpi | observação deduplicada+divergência | `REQUIRED` (dedup; leitura pura seria `NOT_APPLICABLE`) |
| `RequestReturn` | I | Iniciar devolução | item_id?, material, qty?, destino retorno | return=requested | item coerente | — | ReturnRecord | `REQUIRED` |
| `RecordReturnProgress` / `RecordReturnReceipt` | I | Avanços da devolução | return_id, qty | in_return/received | fluxo aberto | — | qty+handoffs | `REQUIRED` |
| `ReconcileReturn` | I | Fechar devolução | return_id, expected_qty resolvida | reconciled | quantidade autoritativa ou declaração rotulada | fórmula `TO_INVENTORY` | audit | `REQUIRED` |
| `CancelMission` / `CancelSignal` | M / sinal | Cancelar trabalho/sinal | id, reason, version | cancelled | não-terminal | — | libera correlações | `REQUIRED` |
| `CloseMission` | M | Encerrar missão | mission_id, version, reason se parcial | closed | § 12 (todos os itens resolvidos ou reason) | — | audit | `REQUIRED` |

## 26. Conceptual query catalog

| Consulta | Propósito | Fonte |
|---|---|---|
| `GetSupplyBoard` | Fila do alimentador (missões por estágio derivado, progresso por item) | owned |
| `GetWarehousePreparationQueue` | Preparo agregado por material (view derivada dos itens abertos) | owned (projeção) |
| `GetSupplyNeeds` | Necessidades planejadas correntes | leitura ERP via api-delpi (não persistida como verdade) |
| `GetMissionDetail` | Missão + itens + quantidades + sinais + evidências + trilha | owned |
| `GetReturnQueue` | Devoluções por dimensão `return` | owned |
| `GetOperationalHistory` | Linha do tempo de eventos por missão/need_key | owned |
| `GetOverviewSummary` | KPIs operacionais para "Visão geral" | owned + derivado |

## 27. Invariants

1. Estado operacional nunca é inventário ERP autoritativo.
2. Observações ERP não são reescritas por workflow local (`erp_evidence` transiciona só por nova observação).
3. Necessidade planejada e pedido humano permanecem fatos distinguíveis (sinais com `kind` e supersede-chain).
4. Nenhuma completude com quantidades requeridas pendentes não resolvidas — verificado **por item**; fechamento parcial exige `reason`.
5. Nenhuma agregação entre unidades incompatíveis — soma só por (material, unidade); totais de missão por unidade.
6. Nenhuma transição a partir de `expected_version`/estado esperado divergente sem conflito explícito.
7. Comandos duplicados não duplicam efeitos (§ 19): sinal planejado reemitido ≠ novo sinal; movimento ERP re-observado ≠ nova correlação.
8. `closed`/`cancelled` não aceitam transições normais de avanço — em nenhum nível.
9. Movimento ERP nunca é fabricado — correlação só por observação real de contrato.
10. Quantidade de devolução não deriva de fórmula não aprovada (`TO_INVENTORY`).
11. Toda quantidade operacional carrega unidade — `accepted_unit` do item vem da unidade autoritativa `B1_UM` (TC §51) e é estável durante o trabalho operacional; sem unidade confiável, escrita que muda quantidade **falha fechado** (`unit_unknown` explícito, nunca default silencioso).
12. Mudança de unidade autoritativa em re-sync/replanejamento = `UNIT_DIVERGENCE` (exceção de reconciliação explícita), **não** delta numérico — quantidades históricas preservam a unidade registrada; nunca subtrair entre unidades distintas.
13. Correlação ERP compara quantidade **e** unidade — igualdade numérica com unidade divergente é `divergent`, nunca `matched`; unidade ausente no movimento → `unknown`.
14. Sem engine/tabela/configuração de conversão de unidades (`UNIT_CONVERSION_*=NOT_REQUIRED` — FS-C0.T7); conversão futura exige decisão de owner/contrato.
11. Toda escrita operacional material é atribuível a ator autenticado (backend resolve identidade).
12. Boundary de filial preservada em toda leitura/escrita (`PROVEN` no legado; obrigatório no alvo).
13. `prepared ≠ reserved`, `collected ≠ transferred`, `delivered ≠ ERP movement`, `ERP movement ≠ consumed`.
14. Desconhecido nunca vira zero (`unknown` separado de ausência de saldo).
15. Item não existe fora de missão; missão não aceita item de outro destino/janela.

## 28. Decisions frozen (nesta etapa)

- Agregado central: **`SUPPLY_MISSION_ACCEPTED` — grain missão + itens**: missão = destino × janela × contexto × atribuição; item = material × unidade × quantidades × dimensões.
- Dimensões de estado separadas por nível (§ 9) — sem enum de lifecycle único; estágio Kanban derivado, nunca persistido.
- Sinais de demanda como fatos persistidos com supersede **e deduplicação de reemissão**.
- Quantidades semânticas por item, cumulativas por registro auditado.
- Concorrência: versão otimista + expected-state + idempotência (conceitual; físico `TO_DESIGN`).
- Idempotência refinada: leitura ERP pura `NOT_APPLICABLE`; observação persistida e sync de sinais `REQUIRED`.
- Auditoria append-only; **`EVENT_SOURCING_REQUIRED = NO`**.
- `RETURN_QUANTITY_RULE = TO_INVENTORY`; `PRIORITY_POLICY = TO_DESIGN`.
- Persistência operacional em schema dedicado no Postgres Minha DELPI; tabelas físicas não nomeadas.

## 29. Decisions NOT frozen

- Nomes físicos de tabelas/colunas/schema; modelo físico completo.
- Se `collection_round` precisa virar entidade própria (viagem multi-CT / reatribuição de viagem).
- Nível físico da versão otimista (missão vs item).
- Política de "preparação encerrada parcial" (continua vs congela em 80).
- Cancelamento por item dentro de missão multi-material (evento próprio vs efeito cascata).
- Tratamento de destino mudando após custódia (correção vs cancelar+recriar).
- Devolução sem item correlacionado (entidade solta?).
- Política de prioridade final e entradas autoritativas.
- ~~Catálogo de permissões e mapeamento ator→transição~~ — RESOLVIDO Doc 4/5 §40-A (FROZEN FS-C0.T3): `access`+`view.filial-*`; ator→transição é regra de negócio, não RBAC.
- Transporte de idempotência (header vs payload), formato de `expected_version` no contrato.
- Convivência/cutover Line Feeder ↔ Factory Supply.
- Reuso de código do motor de necessidade/FIFO (porta nova vs dependência).

## 30. TO_INVENTORY

| Item | Bloqueia |
|---|---|
| Fórmula autoritativa de quantidade de devolução | `ReconcileReturn` com quantidade autoritativa |
| Contrato ERP de correlação estável (ID causal no SD3?) | `match_confidence` confirmado vs heurístico |
| Criticidade de produção autoritativa para prioridade | PRIORITY_POLICY |
| ~~Permissões por ator~~ — RESOLVIDO Doc 4/5 §40-A | 3 permissões `access`+`view.filial-*`; papel do ator não vira permission code |
| Comportamento quando material preparado é usado para outra necessidade | política de alocação de preparo |
| Tolerância coletada > preparada (exceção física real) | invariante de quantidade § 8 |

## 31. Inputs required by Documentation 3/5 and 4/5

**Para Doc 3/5 (Frontend/UX):** dimensões por nível e derivação de estágio (§ 9–11); progresso parcial por item dentro do card da missão; parcialidade como quantidade (badges, não cores); superfícies mapeadas a queries (§ 26); ações por ator mapeadas a comandos (§ 25); `unknown` exige UI distinta de "zero".

**Para Doc 4/5 (APIs/RBAC/Persistência):** catálogo de comandos/queries por nível (§ 25–26) → rotas/OpenAPI; autorização → modelo FROZEN §40-A (`access`+`view.filial-*`, decidido FS-C0.T3); idempotência → transporte (Idempotency-Key etc.) + dedup keys (`need_key`+fingerprint, movement identity); versão otimista → contrato de `version`; grupos de persistência § 21 → schema/migrations; portas api-delpi → contratos de gateway; `TO_INVENTORY` de § 30 → decisões pendentes antes de endpoints de devolução/prioridade.

---

## Referências

- Doc 1/5: `docs/12-roadmap-e-evolucao/factory-supply/README.md`
- Evidência de referência: `production-control-api/production_control_app/domain/services/line_feeder_requirements.py`, `application/services/line_feeder_service.py`, `infrastructure/persistence/postgres_line_feeder_pick_plan_repository.py`, `migrations/V006`, `V007`
