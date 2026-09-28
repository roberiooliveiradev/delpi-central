# Factory Supply — Domain Model (Documentation 2/5)

> **Status:** domain + state machines + data + contract model — Documentation 2/5
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
| Supply Mission | Missão de abastecimento | Unidade de trabalho operacional que leva **um material** a **um destino operacional** dentro de um contexto de necessidade correlacionado. Agregado central (§ 6). |
| Preparation | Preparo | Trabalho do almoxarifado sobre a missão: separar físicamente o material. **Não** é reserva ERP. |
| Collection | Coleta | Retirada do material preparado pelo alimentador. Fato operacional. |
| Handoff | Entrega entre atores | Transferência de custódia operacional com ator, timestamp, quantidade, origem e destino. |
| Operational Delivery | Entrega operacional | Chegada física registrada no destino (CT). **Não** é movimento ERP. |
| ERP Movement Evidence | Evidência de movimento ERP | Observação correlacionada de movimento oficial (ex.: SD3 DE0/RE0). Referência, nunca estado local reescrito. |
| Return | Devolução | Fluxo operacional de retorno produção → almoxarifado. |
| Decision-Time Snapshot | Fotografia do momento da decisão | Cópia de fatos autoritativos no instante de uma decisão, preservada como evidência — nunca verdade corrente. |
| Work Center (CT) | Centro de trabalho / bancada | Destino operacional; identidade vem de contrato TOTVS (via api-delpi). |
| Pickup Location | Local de retirada | Local físico cadastrado (SBZ `BZ_MPLOCAL`), fotografado por decisão. |

## 4. Domain boundaries

```text
┌─ Factory Supply (bounded context) ──────────────────────────────┐
│  DemandSignal   SupplyMission   Handoff   ReturnRecord          │
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
2. **Sinal planejado é recalculado.** Cada refresh que muda a necessidade emite novo `DemandSignal` de `kind=planned` para o mesmo `need_key`, com `supersedes` apontando o anterior. História preservada; `status=superseded` no antigo.
3. **Sinais humanos não são recalculados** — são cancelados ou atendidos, nunca "ajustados" por refresh.
4. **Correlação sem fusão:** sinais com mesmo `need_key` convergem para a mesma Supply Mission (§ 6), mas permanecem fatos separados no rastro — a missão referencia `signal_ids`, não os absorve.
5. `pcp_context` é informacional por padrão (anotação/contexto na necessidade); efeitos autoritativos de PCP `TO_INVENTORY` — depende de contratos existentes, não inventados aqui.

## 6. Aggregate decision — SupplyMission

### Avaliação pelo Abstraction Gate

| Critério | Evidência |
|---|---|
| Ciclo de vida real? | Sim — necessidade → preparo → coleta → entrega → devolução → encerramento/cancelamento, com transições por atores distintos (`TARGET`, Doc 1/5 § 8). |
| Invariantes reais? | Sim — quantidades parciais não-negativas, não-completude com pendências, boundary de filial, estados fechados não aceitam transições (§ 27). |
| Dono real? | Sim — Factory Feeder coordena execução; Warehouse Operator executa preparo; cada transição tem ator responsável. |
| Fronteira de consistência transacional? | Sim — a missão é a unidade onde quantidade requerida/preparada/coletada/entregue/devolvida precisa ser coerente. |
| Reduz acoplamento? | Sim — é o único hub de correlação entre sinais, preparo, coleta, handoffs, entrega, devolução e evidência ERP; sem ele cada evento re-implementaria a correlação. |
| Conceito existente já satisfaz? | **Não.** `MaterialRequirement` é projeção derivada por leitura, sem persistência nem lifecycle (`PROVEN`, `line_feeder_requirements.py`). `PickPlan/PickItem` é uma lista batelada por corte com grain por-produto e status livre `pending/picked/delivered` — sem requerente, sem destino por linha, sem devolução, sem correlação ERP (`PROVEN`, V006/V007). Um modelo mais simples (itens avulsos com status) não satisfaz: multi-destino, quantidades parciais, devolução e correlação causal exigem identidade estável por (material × destino). |

### Decisão

```text
SUPPLY_MISSION_ACCEPTED
```

### Fronteira do agregado

`SupplyMission` = **um material** movendo-se para **um destino operacional** (CT/ordem/operação quando correlacionado), dentro de uma **janela de necessidade**. A missão contém:

- identidade própria (`mission_id`), `branch`;
- `need_key` e referências aos `DemandSignal`s correlacionados;
- destino operacional (CT; `production_order`/`operation` como referência correlacionada, não chave estrita — necessidade pode existir sem OP fixada no momento do pedido);
- `SupplyQuantities` (§ 8) — ledger de quantidades do material nesta missão;
- dimensões de estado (§ 9–10);
- decisões-tempo (snapshots de evidência — § 17);
- correlações ERP (§ 16);
- referências de handoff/devolução;
- auditoria mínima (§ 20).

**Explicitamente fora do agregado:** o "conjunto de coleta" (viagem do alimentador cobrindo N missões) e o "preparo agregado por material" (o almoxarifado prepara um lote que pode alimentar missões de destinos diferentes). Ambos são **agrupamentos derivados/referências leves**:

- `collection_round` — referência compartilhada gravada nos eventos de coleta; se virar entidade com invariants próprios, `TO_DESIGN` depois (Abstraction Gate novamente).
- Preparo agregado por material é **view derivada** das missões abertas (espelha o padrão `PROVEN`: necessidade por bancada → lista por produto), não um segundo agregado. A quantidade preparada por missão é registrada por alocação explícita — o que preserva exatamente o rastro por-destino que a lista por-produto atual perde.

## 7. Entity / value-object candidates

| Conceito | Tipo | Justificativa | Status |
|---|---|---|---|
| `SupplyMission` | Aggregate root | § 6 | `TARGET` |
| `DemandSignal` | Entidade (fora do agregado; raiz própria leve) | Fatos com proveniência independente; missão referencia, não contém | `TARGET` |
| `SupplyQuantities` | Value object (embarcado na missão) | Ledger semântico § 8 | `TARGET` |
| `NeedKey` | Value object | Chave de correlação (branch, material, ct, janela, refs) | `TARGET` |
| `Handoff` | Entidade registrada | Evento de custódia ator→ator; referenciável por N missões quando uma viagem cobre várias | `TARGET` |
| `ErpMovementObservation` | Entidade de correlação | Referência autoritativa observada + laço com a missão (§ 16) | `TARGET` |
| `ReturnRecord` | Entidade | Subfluxo de devolução da missão (§ 15) | `TARGET` |
| `OperationalEvent` (audit) | Entidade append-only | Trilha de transições (§ 20) | `TARGET` |
| `MaterialRequirement` (leitura) | Value/projeção derivada | Computada por leitura dos contratos ERP; **não persistida como verdade** | `PROVEN` (padrão do Line Feeder) |
| `PickPlan`/`PickItem` (legado) | — | § 22 — não adotados como modelo-alvo | `PROVEN_REFERENCE` |

## 8. Quantity semantics

Cada quantidade tem **um** significado, **um** dono e **uma** unidade (`unit` do material via contrato SB1). Nunca agregar unidades incompatíveis — quantidade só soma dentro do mesmo (material, unidade).

| Quantidade | Significado | Dono | Fonte | Autoritativa? | Mutável? |
|---|---|---|---|---|---|
| `required_qty` | Quanto a necessidade planejada exige (saldo em aberto do empenho) | TOTVS | leitura api-delpi (SD4 `open_qty`) + snapshot na missão | Sim (ERP) | Recomputa na fonte; na missão é snapshot histórico |
| `requested_qty` | Quanto um sinal humano pediu | Factory Supply | `DemandSignal` (operador/alimentador/PCP) | Não — é pedido, não fato ERP | Não (sinal imutável; novo sinal supersede) |
| `supply_qty` | Quanto a missão pretende cobrir | Factory Supply | decisão na criação da missão | Não | Sim, por correção auditada (nova decisão registra razão) |
| `prepared_qty` | Quanto o almoxarifado separou para a missão | Factory Supply | `RecordPreparedQuantity` | Não | Acumula por registros; correção exige razão |
| `collected_qty` | Quanto o alimentador retirou | Factory Supply | handoff warehouse→feeder | Não | Acumula por handoffs |
| `delivered_qty` | Quanto chegou operacionalmente ao CT | Factory Supply | handoff feeder→CT | Não | Acumula por entregas |
| `erp_transferred_qty` | Quanto o ERP registra oficialmente movimentado | TOTVS | observação correlacionada (SD3) | Sim (ERP) | Nunca escrita localmente |
| `erp_consumed_qty` | Quanto o ERP registra baixado por apontamento | TOTVS | observação (SH6/consumo) | Sim (ERP) | Nunca |
| `return_required_qty` | Quanto deveria voltar | **TO_INVENTORY** — fórmula autoritativa indefinida | § 15 | — | — |
| `returned_qty` | Quanto voltou operacionalmente | Factory Supply | handoff CT→feeder→almoxarifado | Não | Acumula |

Invariantes de quantidade: `0 ≤ delivered_qty ≤ collected_qty` (não se entrega mais do que se coletou sem evento adicional), `collected_qty ≤ prepared_qty` (não se coleta mais do que o separado — tolerância/`reason` se exceção operacional for aceita, `TO_DESIGN`), e nenhuma quantidade derivada de outra silenciosamente — cada uma é fato registrado.

## 9. Lifecycle dimensions

A missão tem **dimensões independentes**, não um enum gigante. Um estágio único de UX é **derivado** (§ 11).

| Dimensão | Estados | Significado |
|---|---|---|
| `lifecycle` | `open` → `closed` \| `cancelled` | Guarda-chuva de aceite de trabalho |
| `preparation` | `not_started` → `in_progress` → `prepared` | Trabalho do almoxarifado |
| `collection` | `not_collected` → `collected` | Custódia passou ao alimentador (pode ser parcial em quantidade, estado = ocorrência) |
| `delivery` | `not_delivered` → `delivered` | Chegada operacional no destino (parcial em quantidade) |
| `erp_evidence` | `unobserved` → `correlated` \| `divergent` \| `not_found` | Observação do movimento oficial — **estado de correlação, não posse** |
| `return` | `not_applicable` → `requested` → `in_return` → `received` → `reconciled` | Subfluxo de devolução (§ 15) |

Estados são nominais; a **quantidade** carrega a parcialidade (prepared 80 de 100 mantém `preparation=in_progress`, não inventa estado "meio-preparado").

## 10. State machines

Autorização por transição: `AUTHZ_TO_DESIGN` (catálogo de permissões não existe; Doc 4/5). "Ator" abaixo é papel de negócio, não permission code.

### 10.1 `lifecycle`

| Transição | Trigger | Precondição | Ator | Registra | Idempotência | Auditoria |
|---|---|---|---|---|---|---|
| → `open` | criação da missão | sinal(s) correlacionado(s) válido(s), destino resolvido | sistema ou ator autorizado | sinais, `supply_qty`, snapshot | `REQUIRED` | criação |
| `open` → `closed` | `CloseMission` | nenhuma dimensão pendente exigindo resolução (§ 12) ou fechamento com `reason` de exceção | ator autorizado | `closed_at/by`, `reason` se exceção | `REQUIRED` | sempre |
| `open` → `cancelled` | `CancelMission` | missão aberta | solicitante ou autorizado | `cancelled_at/by`, `reason`, sinais liberados | `REQUIRED` | sempre |
| `closed/cancelled` → *qualquer* | — | **proibido** (terminal) | — | — | — | tentativa auditável como rejeitada |

### 10.2 `preparation`

| Transição | Trigger | Precondição | Ator | Registra | Idempotência | Auditoria |
|---|---|---|---|---|---|---|
| `not_started` → `in_progress` | `StartPreparation` | missão `open` | Warehouse | `started_at/by` | `REQUIRED` | sempre |
| `in_progress` → `prepared` | `RecordPreparedQuantity` quando acumulado ≥ `supply_qty` | missão `open`, qty > 0 | Warehouse | `prepared_qty` (acumulado), snapshot de saldo visto | `REQUIRED` | cada registro |
| `prepared` → `in_progress` | correção com `reason` (quantidade revista) | nenhuma coleta ainda consumiu o preparo | Warehouse | correção, razão | `REQUIRED` | sempre |

`prepared` **não** implica reserva ERP (`PROVEN` como decisão Doc 1/5). Saldo observado no preparo é snapshot de evidência (§ 17).

### 10.3 `collection`

| Transição | Trigger | Precondição | Ator | Registra | Idempotência | Auditoria |
|---|---|---|---|---|---|---|
| `not_collected` → `collected` | `RecordCollection` (handoff warehouse→feeder) | `prepared_qty` > 0 coletável | Feeder (+ Warehouse na contraparte) | `collected_qty`, handoff, `collection_round` opcional | `REQUIRED` | sempre |

Handoffs adicionais (2ª viagem) são eventos novos; `collection` permanece `collected` — parcialidade mora na quantidade.

### 10.4 `delivery`

| Transição | Trigger | Precondição | Ator | Registra | Idempotência | Auditoria |
|---|---|---|---|---|---|---|
| `not_delivered` → `delivered` | `RecordOperationalDelivery` (handoff feeder→CT) | `collected_qty` > 0 | Feeder | `delivered_qty`, handoff, destino confirmado | `REQUIRED` | sempre |

Entrega operacional **não** é movimento ERP nem consumo — separação preservada.

### 10.5 `erp_evidence` (correlação, não posse)

| Transição | Trigger | Precondição | Ator | Registra | Idempotência | Auditoria |
|---|---|---|---|---|---|---|
| `unobserved` → `correlated` | `ObserveErpMovement` encontra movimento compatível | leitura api-delpi disponível | sistema | referência do movimento (doc/série/data/qty), confiança do match | interno | sempre |
| `unobserved` → `not_found` | busca sem match na janela | leitura realizada | sistema | janela consultada, `searched_at` | interno | sempre |
| `correlated` → `divergent` | observação posterior contradiz quantidade/janela | evidência nova | sistema | divergência detalhada | interno | sempre |

Re-leitura ERP é idempotente por natureza (observação); `not_found` é factual ("procuramos, não achamos"), nunca "quantidade zero".

### 10.6 `return`

§ 15 — máquina `requested → in_return → received → reconciled` com `AUTHZ_TO_DESIGN` por transição; quantidade autoritativa `TO_INVENTORY`.

### 10.7 Sinais de demanda

`active → superseded` (novo sinal planejado do mesmo `need_key`), `active → cancelled` (necessidade some / pedido cancelado), `active → fulfilled` (missão fechou cobrindo o sinal). Transições de sinal planejado são do sistema; humano, do autor ou autorizado.

## 11. Derived UX stage model

O estágio único do Kanban é **derivação pura** das dimensões — nunca estado persistido:

```text
stage = derive(mission)         # função pura, determinística
A separar     := open ∧ preparation=not_started
Em coleta     := preparation∈{in_progress, prepared} ∧ collection=not_collected
Pronto        := collection=collected ∧ delivery=not_delivered
Entregue      := delivery=delivered ∧ return∈{not_applicable, reconciled}
Em devolução  := return∈{requested, in_return, received}
Encerrado     := lifecycle=closed
Cancelado     := lifecycle=cancelled
```

Ordem de derivação (cancelado > encerrado > devolução > entregue > …) é `TO_DESIGN` na Doc 3/5 — o contrato expõe as dimensões; a coluna é computada. Colisão de sinais ("delivered mas return requested") é resolvida pela prioridade da derivação, não por enum híbrido. As colunas candidatas da Doc 1/5 § 13 são validadas contra este modelo — refinamento permitido em 3/5.

## 12. Partial fulfillment

Parcialidade é **quantidade**, não estado. Exemplo `required=100 → prepared=80 → collected=70 → delivered=60`:

- `preparation=prepared` (decisão de preparo encerrada com 80; ou `in_progress` se continuará — política `TO_DESIGN`), `collection=collected`, `delivery=delivered`;
- a missão **não** pode `close` como completa: fechamento exige `reason` de fechamento-parcial e o déficit permanece no rastro (`unfulfilled_qty = supply_qty - delivered_qty`, derivado);
- pendência residual pode gerar nova missão ou permanecer como débito registrado — política `TO_DESIGN`, nunca silenciosa;
- nenhuma consulta pode afirmar "atendido" olhando só o estado nominal — semântica de completude compara quantidades.

## 13. Replanning and cancellation

Cenários e tratamento:

| Cenário | Tratamento do modelo |
|---|---|
| Tempo planejado muda | Novo `DemandSignal` planejado supersede o anterior; missão aberta recebe o novo sinal correlacionado — janela planejada atual = sinal mais recente, história intacta |
| CT muda | Mesma mecânica; se a missão já executou custódia, a mudança exige correção de destino com `reason` ou cancelamento+nova missão (`TO_DESIGN` qual política — não silenciosa) |
| Quantidade requerida muda | Sinal supersede; `supply_qty` da missão só muda por decisão registrada, nunca por refresh |
| Necessidade desaparece | Sinal planejado → `cancelled`; missão ainda `open` sem sinal ativo → exige `CancelMission` ou confirmação explícita (necessidade fantasma é exceção visível) |
| Preparo já iniciado / material preparado / já coletado | Cancelamento ainda permitido, mas exige trilha de retorno ao almoxarifado (reversão operacional registrada, não delete) |
| Operador cancela pedido | `DemandSignal` humano → `cancelled`; missão correlacionada avalia se restam sinais ativos; sem sinais → `CancelMission` |
| Pedido duplicado | Correlação por `need_key` + idempotência de criação (§ 19); duplicado real recebe sinal próprio superseded/cancelled — não dupla missão |
| Pedido superseded por novo planejamento | Mesma mecânica de supersede |

**Nada é deletado.** Intenção corrente (sinais `active`) e evidência histórica (sinais `superseded`/`cancelled`, eventos) coexistem — é a própria razão do produto.

## 14. Exception model

| Exceção | Tratamento de domínio |
|---|---|
| Estoque insuficiente | Missão continua válida; `supply_qty` limitada a decisão informada; situação de risco derivada (espelha `at_risk` `PROVEN`) |
| Saldo indisponível | `unknown` — não afirmar cobertura nem zero (`PROVEN`, padrão do Line Feeder); criação de missão exigindo saldo falha fechada (`PROVEN`: `create_pick_plan` → 502) |
| Local de retirada ausente | Campo vazio + flag de ausência; nunca local inventado (`PROVEN`: SBZ ausente → sem local) |
| Empenho indisponível | Leitura necessária falhou → erro de gateway, sem degradação silenciosa (`PROVEN`) |
| Operação remanejada | § 13 supersede de sinal |
| Necessidade cancelada | § 13 cancelamento com rastro |
| Preparo/coleta/entrega parcial | § 12 quantidades |
| Movimento ERP não encontrado | `erp_evidence=not_found` factual + janela registrada; **não** é erro bloqueante (movimento pode nem ter ocorrido) |
| Movimento ERP diverge do registro operacional | `erp_evidence=divergent` + divergência descrita; nenhum lado é reescrito |
| Comando duplicado/replay | § 19 idempotência — mesmo efeito, mesmo resultado, sem duplicar registro |
| Transição concorrente | § 18 expected-state — segundo ator recebe conflito, não sobrescrita silenciosa |
| Quantidade de devolução indisponível | `RETURN_QUANTITY_RULE=TO_INVENTORY`; fluxo registra `returned_qty` factual sem afirmar "quanto devia" |
| Destino de devolução não resolvido | Devolução fica `in_return`/`received` sem `reconciled`; destino é input exigido para reconciliar |
| CT/operação sem cadastro | Contrato autoritativo decide; domínio nunca fabrica identidade ERP |

## 15. Return domain

`TARGET` conceitual — nada de devolução está implementado hoje.

```text
RETURN_QUANTITY_RULE = TO_INVENTORY
```

A fórmula autoritativa (ex.: candidatos `saldo_ponto_uso − empenho` visíveis no Power BI) **não** é regra de negócio até provada em contrato — frontend nunca computa quantidade de devolução (Doc 1/5 § 17).

O que o domínio modela **independente** da fórmula:

- `ReturnRecord` por missão: `requested_qty?` (declarada, se houver), `returned_qty` (factual, acumulada por handoffs CT→feeder→almoxarifado), destino de retorno, motivo;
- dimensão `return` na missão: `not_applicable → requested → in_return → received → reconciled`;
- `reconciled` exige quantidade esperada resolvida por fonte autoritativa — enquanto `TO_INVENTORY`, reconciliação é manual/declarativa e assim rotulada;
- devolução sem missão de origem correlacionada é possível (material avulso) — `need_key` opcional no retorno, `TO_DESIGN` se vira entidade solta.

## 16. ERP correlation

**Princípio:** correlação referencia fatos autoritativos; nunca copia autoridade nem fabrica IDs ERP.

```text
ErpMovementObservation {
  mission_id, branch,
  movement_kind        — ex.: warehouse_transfer (DE0→RE0)
  erp_document_ref     — documento/série/data conforme o contrato expõe (SD3)
  material, observed_qty, observed_at (data do ERP), warehouses
  match_confidence     — correlacao heuristicamente encontrada | confirmada
  correlation_basis    — campos usados no match
}
```

`need_key` da missão/sinal: `(branch, material, destination_ct, planned_window, production_order?, operation?)` — com `?` = correlacionado quando disponível, **nunca** obrigatório se o ERP não garante. `TO_INVENTORY`: o contrato SD3 não expõe ID causal estável ligando movimento a uma intenção operacional — a correlação é por **coincidência de atributos** (material+armazéns+quantidade+janela), registrada com `match_confidence` e `correlation_basis`; divergência futura reabre `divergent`. Filial é sempre parte da identidade (`PROVEN`: repository filtra tudo por `branch`).

## 17. Decision-time evidence

| Momento | Evidência preservada | Padrão de referência |
|---|---|---|
| Cálculo de necessidade | `required_qty`, saldos observados, janela programada, empenho fonte | `PROVEN` — pick item fotografa `required_qty`/`point_of_use_qty`/`to_deliver_qty` |
| Criação da missão | CT/janela planejada, sinais vigentes, `supply_qty` decidida | `TARGET` |
| Registro de preparo | saldo autoritativo visto naquele instante | `TARGET` |
| Coleta/handoffs | quantidade, atores, timestamps | `PROVEN` como padrão (`pickup_location` fotografado) |

Invariante: snapshot é **evidência histórica**; o valor corrente é sempre reconsultado na fonte. Nenhum read path resolve saldo "pela tabela do Factory Supply".

## 18. Concurrency

Múltiplos almoxarifados/alimentadores podem agir sobre a mesma missão. Requisitos conceituais:

- **Versão otimista** por agregado (`version` incrementa a cada transição): comando declara `expected_version`; divergência → conflito, não sobrescrita. `TO_DESIGN` o mecanismo físico (não congela DB).
- **Transição com expected-state:** comando declara o estado de onde parte; implementação valida atomicamente (ex.: UPDATE condicional). `PROVEN` como lacuna: o repositório atual faz last-write-wins (`update_item_status` sem versão nem checagem de estado anterior).
- **Chave de idempotência** nos comandos de mutação (§ 19).
- **Cliente stale:** leitura expõe `version` + dimensões; escrita com versão velha recebe conflito explícito — o cliente re-ler e redecidir, nunca retry cego que fabrica transição contraditória.
- **Invariante:** dois atores concorrentes nunca produzem silenciosamente transições contraditórias — exatamente um "vence"; o outro recebe conflito visível.

## 19. Idempotency

| Comando (categoria) | Replay pode duplicar efeito? | Classificação |
|---|---|---|
| Registrar sinal humano (`RequestMaterial`, antecipação) | Sim — duas missões do mesmo pedido | `IDEMPOTENCY_REQUIRED` (chave do cliente) |
| Criação de missão (`PlanSupplyWork`) | Sim | `IDEMPOTENCY_REQUIRED` |
| Registros de quantidade/evento (`StartPreparation`, `RecordPreparedQuantity`, `RecordCollection`, `RecordHandoff`, `RecordOperationalDelivery`) | Sim — retry de rede não pode dobrar quantidade | `IDEMPOTENCY_REQUIRED` |
| Devolução (`RequestReturn`, `RecordReturn…`) | Sim | `IDEMPOTENCY_REQUIRED` |
| Cancelamento/fechamento | Sim (terminal) | `IDEMPOTENCY_REQUIRED` |
| Observação ERP / refresh de sinais planejados | Não — projeção/observação | `IDEMPOTENCY_NOT_REQUIRED` |
| Todas as queries | Não | `IDEMPOTENCY_NOT_REQUIRED` |

Mecanismo de chave/transporte: `TO_DESIGN` (Doc 4/5 — headers/payloads não definidos aqui).

## 20. Audit / history

Trilha mínima por escrita material:

```text
who        — actor autenticado (identity do backend, não input do cliente)
when       — timestamp de registro (+ occurred_at quando difere)
what       — comando + transição (dimensão, from → to)
quantity   — delta e acumulado resultante quando aplicável
reason     — obrigatório em correções, exceções, cancelamentos, fechamento parcial
correlation— mission_id, signal_ids, handoff, erp_movement_ref quando houver
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
| demand_signals | sinais com proveniência e supersede-chain | owned |
| supply_missions | identidade, need_key, destino, dimensões de estado, quantidades, versão | owned |
| handoffs | eventos de custódia referenciando missões | owned |
| erp_correlations | observações de movimento ERP + confidence | owned (referência, não cópia de verdade) |
| return_records | dados de devolução por missão | owned |
| operational_events | trilha append-only de auditoria | owned |
| decision_snapshots | evidências do momento da decisão | owned (evidência, não verdade corrente) |

Separados por natureza: **owned** (workflow), **referenced** (fatos ERP — só referências), **snapshot** (evidência histórica). `platform-data-persistence` governa migrations/transações — nada executado aqui.

## 22. Existing Line Feeder migration relationship

| Elemento atual | Classificação | Racional |
|---|---|---|
| `line_feeder_pick_plans` / `line_feeder_pick_items` (tabelas e linhas) | `KEEP_LEGACY_REFERENCE` | Permanecem propriedade do PCP/Line Feeder; não migrar linhas sem cutover decidido; histórico operacional consultável onde está |
| Conceito de lista de coleta por corte | `GENERALIZE` | Evolui para missões + views derivadas por material/destino |
| `pending/picked/delivered` | `GENERALIZE` | Informa as dimensões collection/delivery; free-form vira máquina com transições |
| Snapshot de decisão no item (`required_qty` etc.) | `GENERALIZE` | Vira padrão de decision-time evidence (§ 17) |
| Grain por-produto (sem destino) | `REJECTED` para o alvo | É exatamente a lacuna de rastreabilidade; alvo mantém grain por (material × destino) com view agregada |
| Motor de necessidade + FIFO + `unknown` | `PROVEN_REFERENCE` para reuso conceitual | Lógica de cálculo é candidata a porta/contrato na nova API (migração de código: `TO_DECIDE_LATER`) |

Implicação de migração (sem executar): convivência Line Feeder ↔ Factory Supply durante transição é `TO_DESIGN` (Doc 5/5 roadmap); nenhuma escrita cruzada entre schemas `production_control` e o futuro schema de factory-supply.

## 23. Operator request semantics

Domínio apenas (sem UI/endpoint):

```text
OperatorRequest (DemandSignal kind=operator_request) precisa de:
  branch, material, destination_ct (ou contexto de operação que o resolva),
  requested_qty + unit, need_window (quando precisa), actor autenticado, reason/contexto livre curto
```

Um pedido do cockpit **é sinal**: não autoriza movimento de estoque, não altera programação ERP, não muda prioridade, não cria transferência oficial. Aceite/execução passam pelo workflow normal (validação de backend, AuthZ, decisão de missão).

## 24. Priority semantics

```text
PRIORITY_POLICY = TO_DESIGN
```

Entradas candidatas (todas sinais, nenhuma fórmula inventada): tempo planejado da necessidade (`first_scheduled_at` `PROVEN`), tempo do pedido do operador, criticidade de produção se autoritativa (`TO_INVENTORY` — existe prioridade em `machine_load_priority`? candidata a reuso), risco de estoque (`at_risk`), estado do preparo.

Kanban consome a política; não a possui. Ordenação manual de cards nunca é prioridade de negócio.

## 25. Conceptual command catalog

Catálogo de domínio — **não são rotas HTTP**. AuthZ sempre `AUTHZ_TO_DESIGN`.

| Comando | Intent | Inputs conceituais | Result | Pré-condições | Dep. autoritativa | Efeitos | Idempotência |
|---|---|---|---|---|---|---|---|
| `SyncPlannedNeeds` (interno) | Recalcular sinais planejados | branch, janela/corte | sinais emitidos/superseded | leituras ERP ok | SH8+SD4+SB2 via api-delpi | sinais; snapshot de cálculo | NOT_REQUIRED (observação) |
| `RequestMaterial` | Sinal humano de material | § 23 | `DemandSignal` ativo | destino/material resolvíveis | validação de material/CT via api-delpi | sinal; correlação a missão | REQUIRED |
| `AnticipateSupply` | Antecipação do alimentador | material, destino/janela, qty | sinal `feeder_anticipation` | idem | idem | idem | REQUIRED |
| `PlanSupplyWork` | Decidir cobertura → missão | sinais/need_key, `supply_qty`, destino | `SupplyMission` open | sinais ativos; saldo medido se a regra exigir | saldo via api-delpi | missão + snapshot | REQUIRED |
| `StartPreparation` | Almoxarifado inicia separação | mission_id, expected_version | preparation=in_progress | open, not_started | — | evento+audit | REQUIRED |
| `RecordPreparedQuantity` | Registrar separado | mission_id, qty_delta, version | acumula; ≥supply_qty → prepared | in_progress | snapshot saldo | qty+evento | REQUIRED |
| `RecordCollection` | Feeder retira material | mission_id(s), qty, round? | collected; handoff warehouse→feeder | prepared_qty>0 | — | handoff+qty | REQUIRED |
| `RecordHandoff` | Custódia genérica ator→ator | mission_id(s), from/to role, qty | handoff registrado | custódia coerente | — | handoff+qty | REQUIRED |
| `RecordOperationalDelivery` | Entrega no CT | mission_id(s), qty, handoff ref | delivered | collected_qty>0 | — | qty+handoff | REQUIRED |
| `ObserveErpMovement` | Correlacionar movimento oficial | mission_id | erp_evidence transiciona | leitura disponível | SD3 via api-delpi | observação+divergência | NOT_REQUIRED |
| `RequestReturn` | Iniciar devolução | mission_id?, material, qty?, destino retorno | return=requested | mission coerente | — | ReturnRecord | REQUIRED |
| `RecordReturnProgress` / `RecordReturnReceipt` | Avanços da devolução | return_id, qty | in_return/received | fluxo aberto | — | qty+handoffs | REQUIRED |
| `ReconcileReturn` | Fechar devolução | return_id, expected_qty resolvida | reconciled | quantidade autoritativa ou declaração rotulada | fórmula TO_INVENTORY | audit | REQUIRED |
| `CancelMission` / `CancelSignal` | Cancelar trabalho/sinal | id, reason, version | cancelled | não-terminal | — | libera correlações | REQUIRED |
| `CloseMission` | Encerrar missão | mission_id, version, reason se parcial | closed | § 12 | — | audit | REQUIRED |

## 26. Conceptual query catalog

| Consulta | Propósito | Fonte |
|---|---|---|
| `GetSupplyBoard` | Fila do alimentador (missões por estágio derivado) | owned |
| `GetWarehousePreparationQueue` | Preparo agregado por material (view derivada das missões) | owned (projeção) |
| `GetSupplyNeeds` | Necessidades planejadas correntes | leitura ERP via api-delpi (não persistida como verdade) |
| `GetMissionDetail` | Missão + quantidades + sinais + evidências + trilha | owned |
| `GetReturnQueue` | Devoluções por dimensão `return` | owned |
| `GetOperationalHistory` | Linha do tempo de eventos por missão/need_key | owned |
| `GetOverviewSummary` | KPIs operacionais para "Visão geral" | owned + derivado |

## 27. Invariants

1. Estado operacional nunca é inventário ERP autoritativo.
2. Observações ERP não são reescritas por workflow local (`erp_evidence` transiciona só por nova observação).
3. Necessidade planejada e pedido humano permanecem fatos distinguíveis (sinais com `kind` e supersede-chain).
4. Nenhuma completude com quantidades requeridas pendentes não resolvidas (fechamento parcial exige `reason`).
5. Nenhuma agregação entre unidades incompatíveis.
6. Nenhuma transição a partir de `expected_version`/estado esperado divergente sem conflito explícito.
7. Comandos duplicados não duplicam efeitos (idempotência § 19).
8. `closed`/`cancelled` não aceitam transições normais de avanço.
9. Movimento ERP nunca é fabricado — correlação só por observação real de contrato.
10. Quantidade de devolução não deriva de fórmula não aprovada (`TO_INVENTORY`).
11. Toda escrita operacional material é atribuível a ator autenticado (backend resolve identidade).
12. Boundary de filial preservada em toda leitura/escrita (`PROVEN` no legado; obrigatório no alvo).
13. `prepared ≠ reserved`, `collected ≠ transferred`, `delivered ≠ ERP movement`, `ERP movement ≠ consumed`.
14. Desconhecido nunca vira zero (`unknown` separado de ausência de saldo).

## 28. Decisions frozen (nesta etapa)

- Agregado central: **`SUPPLY_MISSION_ACCEPTED`** — grain (material × destino × janela de necessidade); viagens/preparo agregado = views/referências derivadas.
- Dimensões de estado independentes (§ 9) — sem enum de lifecycle único.
- Sinais de demanda como fatos persistidos com supersede, nunca overwrite.
- Quantidades semânticas separadas, cumulativas por registro auditado.
- Concorrência: versão otimista + expected-state + idempotência (conceitual; físico `TO_DESIGN`).
- Auditoria append-only; **`EVENT_SOURCING_REQUIRED = NO`**.
- `RETURN_QUANTITY_RULE = TO_INVENTORY`; `PRIORITY_POLICY = TO_DESIGN`.
- Persistência operacional em schema dedicado no Postgres Minha DELPI; tabelas físicas não nomeadas.

## 29. Decisions NOT frozen

- Nomes físicos de tabelas/colunas/schema; modelo físico completo.
- Grain do handoff (por missão vs por viagem/`collection_round` como entidade própria).
- Política de "preparação encerrada parcial" (continua vs congela em 80).
- Tratamento de destino mudando após custódia (correção vs cancelar+recriar).
- Devolução sem missão correlacionada (entidade solta?).
- Política de prioridade final e entradas autoritativas.
- Catálogo de permissões e mapeamento ator→transição (`AUTHZ_TO_DESIGN` em toda a § 10).
- Transporte de idempotência (header vs payload), formato de `expected_version` no contrato.
- Convivência/cutover Line Feeder ↔ Factory Supply.
- Reuso de código do motor de necessidade/FIFO (porta nova vs dependência).
- `collection_round` como entidade com identidade própria.

## 30. TO_INVENTORY

| Item | Bloqueia |
|---|---|
| Fórmula autoritativa de quantidade de devolução | `ReconcileReturn` com quantidade autoritativa |
| Contrato ERP de correlação estável (ID causal no SD3?) | `match_confidence` confirmado vs heurístico |
| Criticidade de produção autoritativa para prioridade | PRIORITY_POLICY |
| Permissões por ator (almoxarifado, alimentador, operador, PCP) | § 10 AUTHZ em todas as transições |
| Comportamento quando material preparado é usado para outra necessidade | política de alocação de preparo |
| Tolerância coletada > preparada (exceção física real) | invariante de quantidade § 8 |

## 31. Inputs required by Documentation 3/5 and 4/5

**Para Doc 3/5 (Frontend/UX):** dimensões de estado e derivação de estágio (§ 9–11); que a parcialidade é quantidade (badges de qty, não cores de estado); superfícies mapeadas a queries (§ 26); ações por ator mapeadas a comandos (§ 25); `unknown` exige UI distinta de "zero".

**Para Doc 4/5 (APIs/RBAC/Persistência):** catálogo de comandos/queries (§ 25–26) → rotas/OpenAPI; `AUTHZ_TO_DESIGN` → catálogo de permissões real; idempotência → transporte (Idempotency-Key etc.); versão otimista → contrato de `version`; grupos de persistência § 21 → schema/migrations; portas api-delpi → contratos de gateway; `TO_INVENTORY` de § 30 → decisões pendentes antes de endpoints de devolução/prioridade.

---

## Referências

- Doc 1/5: `docs/12-roadmap-e-evolucao/factory-supply/README.md`
- Evidência de referência: `production-control-api/production_control_app/domain/services/line_feeder_requirements.py`, `application/services/line_feeder_service.py`, `infrastructure/persistence/postgres_line_feeder_pick_plan_repository.py`, `migrations/V006`, `V007`
