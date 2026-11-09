# MyWEG → Demanda PCP — Etapa 2 (prévia de cobertura)

> **TASK_ID:** `PCP-DEMAND-MYWEG-E2-COVERAGE-PREVIEW` (+ rework / residual)  
> **Status:** prévia interna corrigida · **produtivo bloqueado** · `GET /demand` inalterado  
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
| OPs | 330 OPs · endpoint **sem** `B1_UM` no payload |

Amostra de 8 produtos favorece equivalência `no_estoque`×`SB2@01`, **sem** prova universal.

## 3. Arquitetura da prévia

```text
ACCESS_TOKEN (JWT) → delpi_auth.validate_token + Core /me RBAC
        │
MyWegDemandSourceService.project_latest_lines
        │
        ▼
adapter UN→MI + classify_consolidation + stock pool (SB2 validado)
        │
        ▼
DemandCoverageService.build  (REUSE — sem segundo motor)
  · protheus_only: OPs como hoje (paridade)
  · myweg_only: somente estoque (OP_UNIT_UNVERIFIED)
  · consolidated_proposed: **um único build** + pool `(filial, produto)`;
    somente estoque enquanto OP_UNIT_UNVERIFIED (sem concatenar alocações)
        │
        ▼
MyWegDemandCoveragePreviewService.build_preview
  wired_to_demand_endpoint=false
  productive_activation_blocked=true
  adr_status=ARCHITECTURE_DECISION_REQUIRED
  integrity.{sources_readable, stock_data_complete,
             productive_coverage_complete, consolidation_adr_blocked,
             op_unit_unverified, consolidated_coverage_reliable}
```

Composer: `build_myweg_demand_coverage_preview_service()`.  
CLI: `python -m production_control_app.jobs.myweg_demand_coverage_preview`.

## 4. Unidades

| Etapa | Regra comprovada |
|---|---|
| Necessidade MyWEG | `quantidade_original_un` → cobertura `÷ 1000` (`UN_TO_MI_DIVISOR`) |
| Estoque SB2 exclusivo | exige UM `MI`; filial `02`; armazém `01`; sem somar duplicatas |
| Linha Protheus `PC` | `reconciliation_blocked` no consolidado; cenário `protheus_only` rotula `MIXED` se MI+PC |
| OP `saldo_op` | **HIPOTESE_A_VALIDAR** — `ops_abertas_sql` não seleciona `B1_UM`; status `OP_UNIT_UNVERIFIED` |

Não declarar cobertura MyWEG por OP como confirmada enquanto a unidade da OP não for comprovada.

## 5. Consolidação

| Classe | Tratamento na prévia |
|---|---|
| Demais clientes/lojas Protheus | entram no **mesmo** `build` que MyWEG |
| `000001`/`09` via **`codigo_cadastro` + `loja_cadastro`** | `overlap_pending` — **não soma** com MyWEG |
| `codigo_cliente` (ref. produto) ≠ cadastro | nunca identifica Linhares |
| Cadastro ausente + `codigo_cliente=000001`/`09` | `customer_identity_pending` |
| Lojas `11` e `14` | independentes |
| Unidade incompatível | `reconciliation_blocked` |
| NF | **não** abatida automaticamente |
| Estoque compartilhado | alocado **uma vez** no motor (FIFO por data); soma ≤ pool |
| OP no consolidado | **desligada** enquanto `OP_UNIT_UNVERIFIED` |

`scenarios.consolidated_proposed.reliable=false` e `definitive_total_published=false` enquanto ADR ≠ ACCEPTED.

## 6. Estoque SB2

Pool único `(filial, produto)`:

1. Produto na carteira → só `no_estoque`.
2. Exclusivo MyWEG → `fetch_stock_balances_items(branch=02, warehouse=01, only_positive=false)`.
3. Nunca `no_estoque + SB2`.
4. Cada linha SB2 **exige** `branch=02`, `warehouse=01`, `unit_of_measure=MI`, produto solicitado e qty finita (ausência bloqueia o saldo).
5. Distingue: zero confirmado · produto ausente · UM incompatível · duplicata (incl. entre páginas) · paginação incompleta/inconsistente · falha de comunicação.
6. `sb2_complete=true` só sem rejeições/incompletude; `reliable` exige `stock_data_complete` (não basta `error` vazio).
7. Payload inválido **não** vira lista vazia silenciosa (`PreviewPayloadError`).

## 7. Autorização operacional (CLI)

Prévia exige permissões efetivas (Core `/me` após JWT válido):

- `production-control.access`
- `production-control.demand.view`
- `production-control.myweg-needs.view`
- `production-control.view.filial-02`

**Removido:** `--user-json` / `is_superadmin` sintético.

### Homologação segura no srv-api

```bash
# 1) JWT de usuário real (Portal) — NÃO imprimir o token em logs/tickets
export ACCESS_TOKEN='<jwt>'

# 2) Dentro do container production-control-api (após pull + rebuild inerte):
python -m production_control_app.jobs.myweg_demand_coverage_preview \
  --branch 02 --warehouse 01
```

Sem `ACCESS_TOKEN` válido + RBAC Core: execução live **bloqueada** (`LIVE_EXECUTION_BLOCKED`).  
Não criar endpoint público só para teste. Não inventar token S2S como “usuário”.

## 8. Isolamento

| Superfície | Estado |
|---|---|
| `GET /demand` | **inalterado** |
| MFE / Excel / KPIs | **inalterados** |
| Rota HTTP pública prévia | **não criada** |
| Ativação produtiva | **bloqueada** |
| Contratos públicos `api-delpi` | **inalterados** nesta etapa |

## 9. Testes

`tests/test_myweg_demand_coverage_preview_e2.py` — pool único consolidado, SB2 campos obrigatórios/paginação/duplicata entre páginas, `reliable` vs `integrity`, auth CLI JWT, OP não confirmada, MI+PC, Linhares, conservação, regressão Demanda/MyWEG.

## 10. Pendências

1. ADR consolidação ACCEPTED.
2. Homologação live com JWT real (RBAC Core alcançável no container).
3. Decisão de expor `B1_UM` (ou equivalente) em ops-abertas — **somente** com análise de consumidores/compatibilidade.
4. Etapa 3 (`GET /demand` + UI) — ver `MYWEG-DEMAND-E3-INTEGRATION.md` (consolidação oficial permanece bloqueada).

## 11. Correção posterior #1546 (09/11/2026)

A fotografia de 08/11 acima documenta a limitação original, quando `ops-abertas` não expunha unidade. A correção posterior adicionou `C2_UM` e `B1_UM` ao contrato da API, e a integração E2/E3 agora normaliza cada OP elegível para MI: unidade MI permanece inalterada; PC/UN são divididas por 1000. OPs sem unidade confirmada ou saldo válido não entram na cobertura; o item recebe `op_coverage_incomplete` e o usuário vê aviso de cálculo parcial. A alocação única por produto/filial preserva o saldo disponível e evita duplicar OP entre origens na leitura `both`. A prévia E2 passa a mostrar a cobertura válida, mas a publicação de total consolidado oficial **continua bloqueada** pela ADR. A regra anterior de não considerar OPs era preventiva, não evidência de inexistência de produção.

### Homologação

Validar no ambiente real o produto `90263964`, filial `02`, incluindo a conversão da OP do dia 09/11/2026 e o saldo da necessidade MyWEG (0,026 MI = 26 unidades), sem presumir a unidade até consultar `C2_UM/B1_UM`. A execução dos testes automatizados do código não substitui a validação do saldo real no Protheus.
