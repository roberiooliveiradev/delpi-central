# MyWEG → Demanda PCP — Etapa 1 (origem preparada)

> **TASK_ID:** `PCP-DEMAND-MYWEG-E1-SOURCE-INTEGRATION`  
> **Status:** implementação interna + documentação (sem wiring em `GET /demand`)  
> **Escopo:** filial DELPI `02` · cliente Protheus `000001` / loja `09` · MyWEG `1009`/`1106`  
> **Owner:** `production-control-api`  
> **EXISTING_EQUIVALENT:** `PARTIAL` · **REUSE_DECISION:** `EXTEND`

## 1. Objetivo

Preparar a origem de dados MyWEG Necessidades para futura composição da aba
**Demanda**, sem criar pedidos fictícios, sem alterar snapshots e sem misturar
fontes no endpoint público nesta etapa.

## 2. Arquitetura atual × alvo

### Atual (CONFIRMADO_NO_CODIGO)

```text
TOTVS VW pedidos abertos ──api-delpi──▶ DelpiProductionGateway
                                              │
                                              ▼
                                       DemandService
                                              │
                                              ▼
                                   DemandCoverageService
                                   (estoque=no_estoque, OP=saldo_op)
                                              │
                                              ▼
                                       GET /demand ──▶ MFE Demanda

MyWEG CSV/XLSX ──publisher──▶ POST S2S ──▶ V025 batches/records + V026 SB1
                                              │
                                              ▼
                                    MyWegNeedsService / Compare
                                              │
                                              ▼
                                    GET /myweg/need-batches* ──▶ MFE Necessidades
```

### Alvo Etapa 2 (PLANEJADO — não implementado)

```text
última coleta MyWEG (filial 02)
        │
        ▼
MyWegDemandSourceService.project_latest  ──(interno)──▶ linhas source=myweg
        │
        ├─ consolidação MyWEG × carteira Protheus (regra §7)
        ├─ estoque para produtos exclusivos MyWEG (§8)
        └─ DemandCoverageService (mesmo motor)
                │
                ▼
           GET /demand (itens mistos, contratos públicos preservados/estendidos)
```

**Etapa 1 entrega apenas o bloco `MyWegDemandSourceService` + projetor puro.**
`wired_to_demand_endpoint=false`.

## 3. Owners e consumidores

| Conceito | Owner | Consumidores atuais | Etapa 1 |
|---|---|---|---|
| Carteira aberta / `no_estoque` | api-delpi + view TOTVS | `DemandService`, commercial-api | sem alteração |
| Cobertura estoque/OP | `DemandCoverageService` | `DemandService`, detector uncovered | **não alterado** |
| Snapshots MyWEG | `PostgresMyWegNeedsRepository` | Needs/Compare/SB1/NF | **lido** via `get_latest_batch` + `list_batch_records_for_compare` |
| Identidade SB1 | V026 + `resolve_product_identity` | Compare E5, NF E2 | **reusado** |
| Projeção Demanda MyWEG | `myweg_demand_projection` + `MyWegDemandSourceService` | nenhum HTTP | **novo (interno)** |
| UI Demanda / Necessidades | MFE production-control | rotas existentes | **inalterado** |

## 4. EXISTING_EQUIVALENT e REUSE_DECISION

| Capacidade | Decisão | Evidência |
|---|---|---|
| Última coleta por `collected_at` | **REUSE** `get_latest_batch()` | `postgres_myweg_needs_repository.py` `ORDER BY collected_at DESC` |
| Linhas + SB1 persistido | **REUSE** `list_batch_records_for_compare()` | JOIN V025/V026 — sem reconsulta Protheus |
| Identidade produto | **REUSE** `resolve_product_identity()` | `myweg_needs_comparison.py` |
| Agregação produto+remessa | **REUSE** (disponível) `aggregate_needs()` | Etapa 1 projeta 1 linha/`record_id`; agregação fica para Etapa 2 se o motor exigir |
| Motor de cobertura | **REUSE futuro** — **não** duplicar | `DemandCoverageService` intacto |
| DTO público Demanda | **PRESERVE** | sem mudança de `GET /demand` |
| Estoque SB2 | **EXTEND futuro** `fetch_stock_balances_items` | ver §8 |

## 5. Fonte de cada campo da projeção

| Campo interno | Fonte |
|---|---|
| `source` | constante `myweg` |
| `branch` | `02` (`ALLOWED_BRANCH`) |
| `customer_code` / `store` / `name` | contrato WEG Linhares `000001` / `09` / `WEG Linhares` |
| `display_order` | `MyWEG` (rótulo; **não** é PK) |
| `product_code` | `sb1_resolution.protheus_product_code` quando identidade verified |
| `due_date` | `data_remessa` |
| `open_quantity` | `quantidade_original_un` (`Decimal`) |
| `quantity_mi` | `quantidade_mi` (diagnóstico; não alimenta cobertura) |
| `batch_id` / `record_id` / `id` | UUID do lote + registro → `myweg:{batch_id}:{record_id}` |
| `collected_at` | batch.`collected_at` (efetivo, não `imported_at`) |
| `resolution_status` | SB1 status persistido |
| `coverage_eligible` | `confirmed` + `verified_code` + `matched_by` ∉ provisório amostra |

## 6. Semântica de resolução do produto

| Situação | `coverage_eligible` | Tratamento |
|---|---|---|
| `confirmed` + produção (`code_and_reference` / `reference_prefer_production`) | **sim** | entra na cobertura futura |
| `confirmed` + `provisional_*_sample_*` | **não** | rastreável; fora da cobertura produtiva |
| `pending` / `ambiguous` / `divergent` / `blocked` / `not_found` | **não** | permanece no diagnóstico; qty ≠ 0 silenciosa |
| sem remessa | omitido | mesma regra de `aggregate_needs` |

## 7. Sobreposição MyWEG × Protheus — matriz e decisão

### Premissas comprovadas

1. Pedidos WEG costumam entrar no Protheus perto do faturamento (contexto de negócio).
2. Necessidades MyWEG são a previsão contínua (snapshots diários imutáveis).
3. Módulo de comparação: **variação observada ≠ abatimento reconhecido pela WEG** (`myweg_needs_comparison.py`, NF E2).
4. NF portal/indicativa **não** baixa a necessidade atual.
5. `produto + data + cliente` **não** prova duplicidade sozinho.

### Investigação carteira Protheus (somente leitura)

Mecanismo autorizado: `ProductionOrdersGateway.fetch_open_sales_orders()` →
api-delpi `/pedidos-venda-abertos/totvs-open-orders`, filtrando
`filial=02`, `codigo_cadastro=000001`, `loja_cadastro=09`.

Nesta Etapa 1 **não** houve dump live homologado no ambiente do agente
(`INCONCLUSIVE` para volume atual da carteira). A regra abaixo é a recomendação
segura sustentada pelos contratos e pelo módulo de comparação; a Etapa 2 deve
validar com amostra real antes de ligar o endpoint.

### Matriz de cenários

| # | MyWEG | Pedido Protheus aberto | NF emitida recente | Ação recomendada (Etapa 2) | Confiança |
|---|---|---|---|---|---|
| A | qty Q, remessa D, produto P verificado | ausente | ausente | Incluir linha MyWEG | ALTA |
| B | ausente | saldo S, entrega D, P | — | Incluir linha Protheus (carteira clássica) | ALTA |
| C | Q em D/P | saldo S em D′≈D / P | ausente | **Não somar** Q+S. Preferir MyWEG como previsão; marcar `overlap_pending` com pedido como compromisso comercial | MÉDIA → ADR |
| D | Q | S | NF ≥ redução observada entre coletas | Não abater Q automaticamente; usar NF só como diagnóstico (E2) | ALTA (anti-abatimento) |
| E | Q | S | NF sem cobertura complete | `reconciliation_pending` — sem soma/subtração | ALTA |
| F | identidade não elegível | qualquer | — | Só diagnóstico MyWEG; Protheus segue regra B | ALTA |
| G | provisório amostra 8… | — | — | Fora da cobertura produtiva | ALTA |

### Decisão documentada

```text
ARCHITECTURE_DECISION_REQUIRED (fechamento operacional Etapa 2)
RECOMMENDATION (mais segura):
  - Demanda planejada WEG Linhares = projeção MyWEG elegível da última coleta
  - Pedidos Protheus do mesmo cliente entram quando NÃO houver contraparte MyWEG
    com product_code verificado no mesmo horizonte de entrega (regra de matching
    a provar com amostra — não assumir igualdade produto+data)
  - Sobreposição ambígua → pendência explícita, nunca double-count
  - NF nunca reduz open_quantity MyWEG nesta integração
ALTERNATIVA descartada nesta etapa: somar carteira + MyWEG por produto/data
```

**Etapa 1 não implementa deduplicação no motor.**

## 8. Estoque — análise e estratégia Etapa 2

### Fonte atual da Demanda

`DemandCoverageService` lê `no_estoque` da carteira aberta (view TOTVS),
repetido por `(filial, produto)`, e distribui FIFO por data de entrega.

### Fonte SB2 tipada

`GET /supplies/stock-balances/items` via `fetch_stock_balances_items`:

| Aspecto | Contrato |
|---|---|
| Filial | `branch=02` |
| Armazém default PCP reports | `01` (almoxarifado) — `reports.json` |
| Campo quantidade | `quantity` ← `B2_QATU` |
| Disponível tipado (outro contrato produto) | `B2_QATU - B2_QEMP - B2_RESERVA` em `/products/{code}/stock` — **não** é o campo de `/stock-balances/items` |
| UM | `SB1.B1_UM` |
| Sem registro | linha ausente se `only_positive=true`; com `only_positive=false` pode retornar 0 |
| Paginação | `page_size` máx. 500; filtro `product_codes` |

### Equivalência `no_estoque` × SB2

| Afirmação | Estado |
|---|---|
| Ambos descrevem físico do produto na filial | CONFIRMADO_EM_DOCUMENTACAO (view + SB2) |
| `no_estoque` ≡ `B2_QATU` do armazém `01` | **HIPOTESE_A_VALIDAR** — view não documenta o `B2_LOCAL` agregado |
| Usar SB2 sem validar = risco de estoque duplo ou distinto | CONFIRMADO (risco) |

### Estratégia proposta (Etapa 2 — não implementar agora)

1. Montar mapa `(filial, produto) → stock` a partir das linhas Protheus (`no_estoque`) **quando existirem**.
2. Para produtos **exclusivos MyWEG** (elegíveis sem linha de carteira), buscar
   `fetch_stock_balances_items(branch=02, warehouse=01, product_codes=[…], only_positive=false)`.
3. Homologar amostra: para produtos presentes nas duas fontes, exigir
   `|no_estoque - SB2.quantity| ≤ ε` antes de misturar no mesmo pool.
4. Um único pool por `(filial, produto)` alimenta `DemandCoverageService` — **nunca**
   somar `no_estoque` + SB2 do mesmo código.
5. Se homologação falhar → `ARCHITECTURE_DECISION_REQUIRED` sobre armazém/agregação da view.

## 9. Contrato interno consumível (Etapa 2)

```text
MyWegDemandSourceService.project_latest(user, branch="02") →
{
  source: "myweg",
  branch: "02",
  wired_to_demand_endpoint: false,
  batch: { id, collection_id, collected_at, imported_at, ... },
  items: [ MyWegDemandProjectionLine.to_dict(), ... ],
  summary: { coverage_eligible_count, unresolved_identity_count, ... }
}
```

Composer: `build_myweg_demand_source_service()`.
**Sem rota HTTP nesta etapa.**

## 10. Segurança (RQ-08)

- Exige `production-control.access` + `myweg-needs.view` + `view.filial-02` + `demand.view`.
- Somente leitura; sem escrita Protheus/MyWEG.
- Filial `01` rejeitada (`InvalidBranch`).

## 11. Matriz de testes

| Cenário | Resultado esperado | Teste |
|---|---|---|
| Duas remessas confirmadas | 2 linhas elegíveis | `test_positive_confirmed_product_multiple_remessas` |
| Mesmo produto/qty distintas | linhas distintas; agg soma 280 | `test_sibling_same_product_different_quantities_*` |
| Coleta antiga importada depois | usa `collected_at` mais recente | `test_service_uses_latest_by_collected_at_*` |
| Sem código confirmado | `coverage_eligible=false`, qty preservada | `test_negative_unconfirmed_identity_*` |
| Amostra provisória | código exposto, não elegível | `test_provisional_sample_*` |
| Só MyWEG | linha sem `sales_order` | `test_myweg_only_product_projected` |
| UN vs MI | `open_quantity=1500`, `quantity_mi=1.5` | `test_quantity_un_not_confused_with_mi` |
| Filial 01 | `InvalidBranch` | `test_service_rejects_filial_01` |
| Sem coleta | `MyWegNeedsBatchNotFound` | `test_service_empty_batch_raises` |
| Permissões | `PermissionError` | `test_service_requires_permissions` |

Regressão: suíte MyWEG existente + `test_demand.py` (motor intacto).

## 12. Prontidão Etapa 2

| Item | Estado |
|---|---|
| Projeção última coleta | **PRONTO** |
| Identidade / amostras | **PRONTO** |
| Contrato interno | **PRONTO** |
| Consolidação MyWEG×Protheus | **PENDENTE** (`ARCHITECTURE_DECISION_REQUIRED` + amostra live) |
| Estoque exclusivos MyWEG | **PENDENTE** (homologar `no_estoque`×SB2) |
| Wiring `GET /demand` / UI / KPIs | **BLOQUEADO** até decisões acima |
| Pedidos fictícios / write Protheus | **FORA DE ESCOPO** |

## 13. Arquivos

| Arquivo | Papel |
|---|---|
| `domain/myweg_demand_source_contract.py` | constantes internas |
| `domain/services/myweg_demand_projection.py` | projetor puro |
| `application/services/myweg_demand_source_service.py` | orquestração + RBAC |
| `composition/pc_composer.py` | `build_myweg_demand_source_service` |
| `tests/test_myweg_demand_projection_e1.py` | testes E1 |
| este documento | autoridade da Etapa 1 |

## 14. Fora de escopo (não executar)

Alterar `GET /demand`, `DemandCoverageService`, UI/KPIs, criar pedidos,
reprocessar coletas, migrations, timers, deploy que habilite a fonte na Demanda.
