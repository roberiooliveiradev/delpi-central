# MyWEG → Demanda PCP — Etapa 1 (origem preparada)

> **TASK_ID:** `PCP-DEMAND-MYWEG-E1-SOURCE-INTEGRATION`  
> **Residual:** `PCP-DEMAND-MYWEG-E1-RESIDUAL-HOMOLOGATION`  
> **Status:** origem interna pronta · homologação live **INCONCLUSIVE** · `GET /demand` inalterado  
> **Escopo:** filial DELPI `02` · cliente Protheus `000001` / loja `09` · MyWEG `1009`/`1106`  
> **Owner:** `production-control-api`  
> **EXISTING_EQUIVALENT:** `PARTIAL` · **REUSE_DECISION:** `EXTEND`  
> **Decisão consolidação:** `ARCHITECTURE_DECISION_REQUIRED` (não `ACCEPTED`)

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

### Homologação residual (amostra real) — `PCP-DEMAND-MYWEG-E1-RESIDUAL-HOMOLOGATION`

Mecanismos autorizados (somente leitura):

1. MyWEG: `get_latest_batch()` + `list_batch_records_for_compare(batch_id)` (PG plugins, schema
   `production_control`) — filtrar `branch=02`, empresa `1009`, centro `1106`.
2. Protheus: `DelpiProductionGateway.fetch_open_sales_orders()` →
   `/pedidos-venda-abertos/totvs-open-orders`, recorte
   `filial=02` + `codigo_cadastro=000001` + `loja_cadastro=09` + `tipo_entidade=CLIENTE`.

| Leitura exigida | Resultado |
|---|---|
| Última coleta MyWEG + SB1 | **CONFIRMADO** (08/11/2026 srv-api): collection `20261108_080025_…` · 464/464 confirmed · 157 produtos · 680.325 UN |
| Carteira Protheus `000001`/`09` | **CONFIRMADO** (mesma data): **0** linhas abertas Linhares; não confundir lojas 11/14 |
| Estoque SB2×`no_estoque` | **PARCIAL**: 157/157 com registro wh=01; amostra 8 coincidiu; equivalência universal ainda HIPOTESE |
| Contagens exclusivos / overlap | Linhares sem pedido aberto → overlap cartão vazio na foto; exclusivos MyWEG = elegíveis sem linha 09 |

Fotografia ≠ invariante. Detalhe e prévia E2: [MYWEG-DEMAND-COVERAGE-E2.md](./MYWEG-DEMAND-COVERAGE-E2.md).

### Matriz de classificação

| Classe | Critério | Ação E2 prévia | Estado evidência 08/11 |
|---|---|---|---|
| Exclusivo MyWEG | P verificado; ausente na carteira filtrada | Incluir MyWEG | esperado (0 linhas loja 09) |
| Exclusivo Protheus | linha carteira outros clientes/lojas | Manter Protheus | 50 linhas filial 02 (não Linhares) |
| Sobreposição comprovada | evidência documental além de P | **nunca somar** | sem caso Linhares na foto |
| Sobreposição provável | mesmo P; datas próximas | `overlap_pending` | fixture E2 |
| Compromisso adicional | pedido sem contraparte MyWEG | incluir Protheus | lojas 11/14 ≠ Linhares |
| DELPI não confirmado | `coverage_eligible=false` | diagnóstico | 0 na foto (464 confirmed) |

**Regra essencial (CONFIRMADO_NO_CONTRATO / código comparação):** não somar MyWEG+Protheus
sobrepostos; não abater NF da necessidade atual.

### Decisão proposta (não ACCEPTED)

```text
STATUS: ARCHITECTURE_DECISION_REQUIRED
AUTHORITY: Product Master / owner Production Control + revisão arquitetural
RECOMMENDATION (mais segura, sem amostra live):
  - Autoridade previsão WEG Linhares = última coleta MyWEG elegível
  - Autoridade faturamento imediato = carteira Protheus (quando existir)
  - Sobreposição sem prova documental → não somar; marcar overlap_pending
  - Pedidos adicionais sem contraparte MyWEG elegível → manter Protheus
  - Ambíguos / SB1 não elegível → fora da cobertura; rastreáveis
  - NF → diagnóstico apenas (nunca reduz open_quantity MyWEG)
  - Matching NÃO é produto+data sozinho
BLOQUEIO Etapa 2: amostra live das leituras 1–5 acima + aceite da authority
```

**Etapa 1 / residual não implementa deduplicação no motor.**

## 8. Estoque — análise e estratégia Etapa 2

### Fonte atual da Demanda

`DemandCoverageService` lê `no_estoque` da carteira aberta (view TOTVS
`VW_PEDIDOS_VENDA_ABERTOS_COMPRADORES`), repetido por `(filial, produto)`, e
distribui FIFO por data de entrega.

### Fonte SB2 tipada

`GET /supplies/stock-balances/items` via `fetch_stock_balances_items`:

| Aspecto | Contrato |
|---|---|
| Filial | `branch=02` |
| Armazém default PCP reports | `01` (almoxarifado) — `reports.json` |
| Campo quantidade | `quantity` ← `B2_QATU` (físico do local) |
| Empenhos/reservas | **não** no items de stock-balances; disponível tipado só em `/products/{code}/stock` = `QATU−QEMP−RESERVA` |
| UM | `SB1.B1_UM` |
| Sem registro | ausente se `only_positive=true`; com `false` pode retornar 0 |
| Paginação | `page_size` máx. 500; `product_codes` |

### Equivalência `no_estoque` × SB2

| Afirmação | Estado |
|---|---|
| Ambos descrevem quantidade física na filial | CONFIRMADO_EM_DOCUMENTACAO |
| DDL da view / `B2_LOCAL` usado em `no_estoque` | **não auditado no repo** (DDL ilegível / não versionado) |
| `no_estoque` ≡ `B2_QATU` armazém `01` | **HIPOTESE_A_VALIDAR** (amostra 8/08/11 favorável, não universal) |
| Comparação live produtos nas duas fontes | **PARCIAL** — 8 coincidiram; 157 MyWEG com registro SB2 wh=01 |
| Usar SB2 sem validar = risco de estoque duplo/distinto | CONFIRMADO (risco) — prévia E2 **não soma** fontes |

### Estratégia segura (bloqueada até prova)

1. Pool único `(filial, produto)` para o motor — **nunca** `no_estoque + SB2`.
2. Quando o produto já vem da carteira: usar **somente** `no_estoque` (paridade Demanda atual).
3. Produto **exclusivo MyWEG**: só após amostra live com
   `|no_estoque − SB2(warehouse=01).quantity| ≤ ε` em produtos que existam nas duas fontes.
4. Se divergência material → manter bloqueio; não “ajustar” valores para coincidir.
5. Sem prova: **não** alimentar cobertura MyWEG com SB2 na Etapa 2.

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

Port: `MyWegNeedsRepositoryPort.list_batch_records_for_compare` declarado
(alinhado a `PostgresMyWegNeedsRepository` e aos fakes de compare).

## 10. Segurança e proposta de autorização (Etapa 2)

### Inventário atual (CONFIRMADO_NO_CODIGO / manifest)

| Superfície | Permissões |
|---|---|
| `GET /demand` | `access` + `demand.view` + filial |
| Necessidades WEG / compare | `access` + `myweg-needs.view` + `view.filial-02` |
| `MyWegDemandSourceService.project_latest` (interno) | `access` + `myweg-needs.view` + `view.filial-02` + `demand.view` |

Códigos: `production-control.demand.view`, `production-control.myweg-needs.view`.

### Proposta backend-first (não implementada; não altera Keycloak/Core/MFE)

```text
1. GET /demand permanece acessível com demand.view + filial (comportamento atual).
2. Linhas source=myweg só entram no payload consolidado se o usuário também tiver
   myweg-needs.view (+ view.filial-02). Sem essa permissão → Demanda = só Protheus
   (degradação segura; sem vazamento MyWEG).
3. Não ampliar demand.view para incluir MyWEG implicitamente.
4. Não exigir myweg-needs.view para ver a carteira Protheus.
5. summary/horizon/KPIs: se misturar fontes, calcular dois escopos ou documentar
   que totais MyWEG só aparecem quando o usuário tem as duas permissões.
6. Qualquer mudança de policy exige aprovação dos owners (Core RBAC + PCP)
   antes da Etapa 2.
```

Estado: **proposta documentada** · Keycloak/manifest **inalterados** nesta tarefa.

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
| Port declara compare | método no Protocol | `test_repository_port_declares_list_batch_records_for_compare` |

Regressão: suíte MyWEG existente + `test_demand.py` (motor intacto).

## 12. Prontidão Etapa 2

| Item | Estado |
|---|---|
| Projeção última coleta | **PRONTO** |
| Identidade / amostras provisórias | **PRONTO** |
| Contrato interno + Port compare | **PRONTO** |
| Política auth proposta | **DOCUMENTADA** (não ACCEPTED) |
| Consolidação MyWEG×Protheus | **PRÉVIA E2 pronta** · ADR ainda **não ACCEPTED** · produtivo bloqueado |
| Estoque exclusivos MyWEG | **PRÉVIA E2** usa SB2 wh=01 sem somar `no_estoque` · equivalência universal pendente |
| Wiring `GET /demand` / UI / KPIs | **BLOQUEADO** |
| Pedidos fictícios / write Protheus | **FORA DE ESCOPO** |

**Recomendação:** **não iniciar Etapa 2** até AC-01 e AC-03 com evidência live e
decisão ACCEPTED pela authority.

## 13. Arquivos

| Arquivo | Papel |
|---|---|
| `domain/myweg_demand_source_contract.py` | constantes internas |
| `domain/services/myweg_demand_projection.py` | projetor puro |
| `domain/ports/myweg_needs_repository.py` | Protocol + `list_batch_records_for_compare` |
| `application/services/myweg_demand_source_service.py` | orquestração + RBAC |
| `composition/pc_composer.py` | `build_myweg_demand_source_service` |
| `tests/test_myweg_demand_projection_e1.py` | testes E1 + residual port |
| este documento | autoridade da Etapa 1 / residual |

## 14. Fora de escopo (não executar)

Alterar `GET /demand`, `DemandCoverageService`, UI/KPIs, criar pedidos,
reprocessar coletas, migrations, timers, deploy que habilite a fonte na Demanda,
alterar Keycloak/Core/manifests.
