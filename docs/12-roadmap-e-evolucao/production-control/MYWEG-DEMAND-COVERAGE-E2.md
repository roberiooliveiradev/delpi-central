# MyWEG → Demanda PCP — Etapa 2 (prévia de cobertura)

> **TASK_ID:** `PCP-DEMAND-MYWEG-E2-COVERAGE-PREVIEW`  
> **Status:** prévia interna implementada · **produtivo bloqueado** · `GET /demand` inalterado  
> **Escopo:** filial `02` · WEG Linhares `000001`/`09`  
> **Owner:** `production-control-api`  
> **EXISTING_EQUIVALENT:** `YES` · **REUSE_DECISION:** `EXTEND`

## 1. Objetivo

Integrar necessidades MyWEG ao **mesmo** `DemandCoverageService` da Demanda,
em memória, somente leitura, sem alterar endpoint/UI/KPIs.

## 2. Evidências produtivas (fotografia 08/11/2026)

Fonte: consultas somente leitura no `srv-api` (operador). **Não** são invariantes.

| Fonte | Evidência |
|---|---|
| MyWEG última coleta | `20261108_080025_…` · 464 linhas · 464 SB1 confirmed · 157 produtos elegíveis · 680.325 UN (= 680,325 MI) |
| Conversão | `UN_TO_MI_DIVISOR = 1000` confirmada |
| Protheus abertos | 280 total · 50 filial 02 · **0** linhas `000001`/`09` · lojas 11/14 são outras WEG |
| SB2 wh=01 filial 02 | 157 produtos com registro · 74 >0 · 83 =0 · UM SB1 `MI` · amostra 8 `no_estoque`≡`SB2.quantity` |
| OPs | 330 OPs · 104 produtos com OP · 53 sem OP · todas com data prevista |

Amostra de 8 produtos favorece equivalência `no_estoque`×`SB2@01`, **sem** prova universal.

## 3. Arquitetura da prévia

```text
MyWegDemandSourceService.project_latest_lines
        │
        ▼
adapter UN→MI + classify_consolidation + stock pool
        │
        ▼
DemandCoverageService.build  (REUSE — sem segundo motor)
        │
        ▼
DemandService._summary / _horizon (REUSE)
        │
        ▼
MyWegDemandCoveragePreviewService.build_preview
  wired_to_demand_endpoint=false
  productive_activation_blocked=true
  adr_status=ARCHITECTURE_DECISION_REQUIRED
```

Composer: `build_myweg_demand_coverage_preview_service()`.  
CLI: `python -m production_control_app.jobs.myweg_demand_coverage_preview`.

## 4. Normalização de unidades

| Etapa | Regra |
|---|---|
| Necessidade MyWEG | `quantidade_original_un` |
| Cobertura | `qty_mi = qty_un / 1000` (`UN_TO_MI_DIVISOR`) |
| Estoque / OP | tratados em MI (paridade motor atual) |
| Linha Protheus `unidade=PC` | `reconciliation_blocked` — não entra no consolidado |
| OP `saldo_op` | endpoint sem B1_UM → `ASSUMED_PRODUCT_UM` (mesmo que Demanda hoje) |

Exemplo canônico: 1.500 UN → 1,500 MI; estoque 0,500 + OP 0,700 → descoberto 0,300 MI.

## 5. Consolidação

| Classe | Tratamento na prévia |
|---|---|
| Demais clientes/lojas Protheus | entram |
| `000001`/`09` aberto | `overlap_pending` — **não soma** com MyWEG |
| MyWEG elegível | entra (previsão principal Linhares) |
| SB1 não elegível / amostra provisória | pendência de identidade |
| Unidade incompatível | `reconciliation_blocked` |

Total definitivo consolidado **não** é publicado (`definitive_total_published=false`) enquanto ADR não for ACCEPTED.

## 6. Estoque

Pool único `(filial, produto)`:

1. Produto na carteira → só `no_estoque`.
2. Exclusivo MyWEG → `fetch_stock_balances_items(branch=02, warehouse=01, only_positive=false)`.
3. Nunca `no_estoque + SB2`.
4. Erro/ausência SB2 → incompleto; **não** vira zero silencioso.

## 7. Autorização

Prévia exige `access` + `demand.view` + `myweg-needs.view` + `view.filial-02`.  
Filial 01 rejeitada. Sem mudança Keycloak/Core/manifest.

## 8. Isolamento

| Superfície | Estado |
|---|---|
| `GET /demand` | **inalterado** |
| MFE / Excel / KPIs | **inalterados** |
| Rota HTTP pública prévia | **não criada** |
| Ativação produtiva | **bloqueada** |

## 9. Comandos no srv-api

```bash
# Dentro do container production-control-api (após git pull + rebuild inerte):
python -m production_control_app.jobs.myweg_demand_coverage_preview \
  --user-json '{"is_superadmin":true}'
```

Alternativa: script Python chamando `build_myweg_demand_coverage_preview_service().build_preview(user)`.

## 10. Testes

`tests/test_myweg_demand_coverage_preview_e2.py` — UN/MI, FIFO estoque/OP, overlap loja 09 vs 11, PC bloqueado, SB2 erro, auth, conservação.

## 11. Pendências para ativação futura

1. ADR consolidação ACCEPTED pela authority.
2. Homologação live da prévia no srv-api (snapshot muda).
3. Decisão OP UM explícita se divergir de SB1.
4. Gate de feature + contrato público (fora desta etapa).
