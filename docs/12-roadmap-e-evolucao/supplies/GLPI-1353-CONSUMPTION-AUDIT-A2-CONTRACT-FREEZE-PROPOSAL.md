# GLPI #1353 — A2 Contract-Freeze Proposal — Auditoria de Consumo OP×Operação

> **Estado:** PROPOSED / NOT FROZEN — 2026-10-29.
> **Proibido interpretar como OpenAPI publicado, rota implementada ou autorização de implementação/deploy.**
> **Base:** HEAD `cd4e41c438` (= `origin/main`), evidências A1 runtime (OP `24884201006` + família `C2_NUM=248842`, filial `01`), D2.1, D2.2, ADR-009, `protheus_production_orders.py`, padrões S2S vigentes.
> **GATE-D2 só é aprovado com homologações explícitas da matriz §8.**

## 1. Escopo desta proposta

Apenas **C2** (detalhe de uma OP). C1 (lista) e C3 (lookup inverso por componente) permanecem contratos independentes e posteriores. C4/C5 fora do MVP.

```text
Producer (api-delpi):  GET /supplies/consumption-audit/orders/{production_order}?branch=01|02
BFF (supplies-api):    GET /consumption-audit/orders/{production_order}?unit=01|02
MFE:                   não autorizado neste freeze
```

- `production_order`: **canônico 11 posições** — `C2_NUM`(6) + `C2_ITEM`(2) + `C2_SEQUEN`(3), conforme `protheus_production_orders.py` (`ORDER_KEY_LENGTH = 11`) e `docs/api/padroes-totvs/ordem-producao-chave.md`. Path param `^[0-9A-Z]{11}$`, preserva zeros à esquerda; sem normalização silenciosa (não concatenar nem truncar).
- `branch` (producer) / `unit` (BFF): obrigatório `01|02`; convenções locais preservadas (`branch` nas rotas `/supplies/*` do producer, `unit`/`OPERATIONAL_UNITS` no BFF). Sem "todas" implícita.

## 2. Autenticação e autorização (proposta — pendente Security)

| Salto | Mecanismo |
|---|---|
| Portal → BFF | JWT usuário (Keycloak) → Core `/me` → `EffectiveUser`; `require_policy(can_use_operations)` (`supplies.access`); `require_unit` restringe `unit` a `01|02`; Core indisponível → `503`. **Zero permissões novas** (ADR-009). |
| BFF → producer | **S2S individual client-credentials** (mecanismo `s2s_service_access.require_s2s_or_any_permission`): JWT em `X-Delpi-Service-Authorization`, validado por `ServiceTokenValidator` — assinatura, issuer, audience `S2S_AUDIENCE`, `allowed_clients=("supplies-api",)`, `required_scopes=("consumption-audit.read",)`. `X-Delpi-Caller-App` apenas telemetria. |
| Vetado | `API_DELPI_ACCESS` em `/production/*`; token compartilhado legado `X-Delpi-Service-Token`; claims de JWT de usuário como autoridade; header auto-atribuído. |

**Provisionamento pendente (não executado):** grant do scope `consumption-audit.read` ao client `supplies-api` no Keycloak; `S2S_SCOPE` no ambiente BFF; registro do escopo na política de emissão. Requer aprovação Security (G2-07). Convenção de nome segue `{resource}.{action}` vigente (`suppliers.read`, `suppliers.create`).

## 3. Response schema C2 — proposto

Fontes expostas **separadas, com proveniência** — nenhuma fusão silenciosa. `null`/`unknown` onde não suportado. Campos e enums em inglês.

```jsonc
{
  "branch": "01",
  "production_order": "24884201006",
  "order": {
    "order_number": "248842",           // C2_NUM
    "order_item": "01",                 // C2_ITEM
    "order_sequence": "006",            // C2_SEQUEN
    "product_code": "50226108",
    "product_type": "PI",               // B1_TIPO
    "unit_of_measure": "MI",
    "planned_quantity": 0.125,          // C2_QUANT
    "produced_quantity": 0.0,           // C2_QUJE
    "produced_quantity_basis": "stock_receipt",   // v. §4.1 — confidence sibling_correlation
    "status": "N",
    "finished_at": null,                // C2_DATRF
    "emission_date": "2026-10-20",
    "due_date": "2026-10-29",           // C2_DATPRF
    "priority": "500",
    "order_type": "F"                   // C2_TPOP
  },
  "related_orders": [
    {
      "production_order": "24884201002",
      "product_code": "90350419",
      "relationship": "parent_commitment_via_d4_oporig", // pai empenha o PI desta OP
      "confidence": "proven"
    }
    // também derivável: mother via prefixo(8)+"001"; siblings via mesmo C2_NUM+C2_ITEM
  ],
  "operations": [
    {
      "operation": "01",
      "work_center": "CT-23",           // SG2 roteiro / H8_CTRAB
      "execution_evidence": {
        "sh8_allocation": {
          // SH8 = ALOCAÇÃO/cadastro. Padrão observado A1: linha some após apontamento.
          // Semântica geral PENDENTE PCP — não usar como prova de (não)execução.
          "row_present": false, "status": null, "source": "SH8010"
        },
        "hza_records": [
          { // canal coletor — vínculo a SH6 via HZA_IDAPON ⊃ H6_IDENT (PROVADO A1)
            "status": "2",               // 1 em-curso / 2 encerrado c/ apontamento / 3 descartado
            "started_at": "2026-10-29T05:13:23", "ended_at": "2026-10-29T05:27:59",
            "appointment_ref": "UDCGH1", "transaction_type": "1", "source": "HZA010"
          }
        ],
        "sh6_appointments": [
          { // apontamento efetivo — pode existir SEM HZA (canal manual, provado OP-04)
            "appointment_id": "UDCGH1", "reported_quantity": 0.125,
            "type": "P", "reported_at": "2026-10-29",
            "started_at": "2026-10-29T05:13", "ended_at": "2026-10-29T05:27",
            "linked_hza": true,          // HZA_IDAPON contém H6_IDENT
            "channel": "collector|manual|unknown",   // regra de derivação PENDENTE PCP
            "source": "SH6010"
          }
        ],
        // derivação CONSERVADORA proposta (regra geral pendente PCP):
        //   evidenced  = ≥1 SH6 (tipo P) ou HZA status=2 na operação
        //   pending    = SH8 presente E nenhum SH6/HZA status 2 na operação
        //   unknown    = demais casos / fonte indisponível
        "execution_state": "evidenced"   // evidenced | pending | unknown
      },
      "components": [
        {
          "component_code": "10010030",
          "component_type": "MP",        // B1_TIPO — MO e não-MP nunca entram em consumo MP
          "unit_of_measure": "MT",
          "bom": {                       // SG1 histórica — structure_as_of = emission_date (proposta)
            "structure_as_of": "order_emission_date",
            "reference_date": "2026-10-20",
            "quantity_per_unit": 646.0,  // G1_QUANT por 1 unidade do produto (UM do produto)
            "valid_from": "2026-10-20", "valid_to": "2049-12-31",
            "theoretical_quantity": 80.75,        // G1_QUANT × C2_QUANT
            "completeness": "complete"   // complete | partial | missing
          },
          "commitment": {                // SD4
            "original_quantity": 80.75,  // D4_QTDEORI
            "open_quantity": 0.0,        // D4_QUANT
            "derived_consumed_quantity": 80.75,    // QTDEORI-QUANT (guarda <0→0); NÃO é baixa física
            "origin_order": null,        // D4_OPORIG quando componente vem de OP-filha
            "lines": 1
          },
          "movements": {                 // SD3 — binding por D3_OP (nunca por documento)
            "eligible_consumption_quantity": 80.75,
            "classified": [
              { "document": "220039841", "cf": "RE2", "tm": "999", "quantity": 80.75,
                "kind": "production_consumption", "reversed": false }
            ],
            "excluded": [
              { "document": "220039839", "cf": "RE0", "tm": "999", "quantity": 0.64,
                "kind": "warehouse_transfer", "reason": "not_raw_material_consumption" },
              { "document": "220039840", "cf": "RE1", "tm": "999", "quantity": 0.233,
                "kind": "production_consumption", "component_type": "MO",
                "reason": "labor_not_material" }
            ]
            // estorno: par espelhado doc+cod+qty (RE↔DE), ambas D3_ESTORNO='S' — excluídas
            // do somatório; expostas em excluded com reversed:true para transparência.
          },
          "discrepancy": {
            "value": 0.0,
            "reference": "derived_commitment",   // derived_commitment | theoretical | none
            "within_tolerance": null              // null até G2-06 homologar tolerância
          },
          "classification": "reconciled",
          // reconciled | arithmetic_difference | requires_investigation | unclassified
          // "reconciled" aqui é por componente e válido porque op-01 tem fontes
          // completas e comparáveis + execução evidenciada; o warning global
          // permanece pela divergência SH6×SC2. NUNCA irregular/shortage sem
          // prova física. Execução não evidenciada ⇒ não concluir falta de
          // consumo (ver regra §4.3).
          "quality_flags": []            // ex.: "ambiguous_cf_semantics", "sg1_gap"
        }
      ]
    }
  ],
  "quality": {
    "status": "partial",                 // complete | partial | inconclusive
    "warnings": ["sh6_vs_sc2_quantity_mismatch"],
    "unresolved_semantics": [
      "automatic_issue_causality",       // correlação temporal provada; trigger não provado
      "re0_tm999_transfer_meaning",      // CF RE0+TM999 ambíguo (transfer-in vs devolução)
      "sh8_row_removal_semantics"
    ]
  },
  "metadata": {
    "generated_at": "2026-10-29T18:50:00Z",
    "source": "api-delpi",
    "tolerance_policy": { "id": "glpi1353-v0", "absolute": null, "percent": null },  // G2-06
    "contract_version": "a2-proposal-1"
  }
}
```

> **Nota:** o exemplo mostra apenas a operação `01` por brevidade. A resposta real da OP `24884201006` incluiria a operação `02` com `execution_state="pending"` (SH8 presente, sem SH6/HZA) e componente `10080329` classificado `requires_investigation`/`unclassified` — é por isso que `quality.status="partial"` mesmo com a op-01 reconciliada.

## 4. Regras de cálculo e semântica — grau de confiança por regra

### 4.1 Provadas por evidência A1 (recorte; regra geral ainda a homologar PCP)

| Regra | Evidência | Confiança no contrato |
|---|---|---|
| `production_order` = 11 posições (6+2+3) | `protheus_production_orders.py` + dados reais | canonical |
| `C2_QUJE` = qtd recebida em estoque (PR0/op final), **não** apontamento de operação | OP-03 única com PR0 → `C2_QUJE=0.125`+`C2_DATRF`; OPs 04/05/06 com SH6 0.125 e `C2_QUJE=0` | `sibling_correlation` — expor `produced_quantity_basis`, não usar QUJE como denominador de auditoria |
| HZA↔SH6 link: `HZA_IDAPON` = `"01"+produto(15)+"01"+H6_IDENT` | 3/3 ops do coletor (UDCAUD/UDCB63/UDCGH1) | `proven` |
| SH6 existe sem HZA (canal manual) | OP-04: SH6 UDCAWQ, zero HZA010 | `proven` — execution evidence = SH6 ∪ HZA |
| SH8 linha some após apontamento da operação | OP-03 (completa) zero SH8; OPs 04/05/06 só op-02; op-01 OP-06 removida após apontamento hoje | `pattern_observed` — SH8 presença ≈ alocação pendente; rótulo final PENDENTE PCP |
| `D4_OPORIG` = OP-filha produtora do componente intermediário | SD4 OP-02: 50226108←OP-06 (op 07), 50215487/106/107←OPs 03/04/05 (op 08) | `proven` |
| Estorno = par espelhado mesmo doc+cod+qty `RE2`+`DE2`, ambos `D3_ESTORNO='S'`; exclusão flag → net correto | 10/10 amostras filial-01 | `proven` (amostra 44d) |
| Doc não é chave — linhas SD3 carregam `D3_OP` distintos | doc `220039841` tem linha de `24880701002` | `proven` |
| SG1 `G1_QUANT` por unidade do produto na UM do produto; aritmética exata (646×0.125=80.75; 2000×0.125=250) | reproduzido | `proven` (sem conversão no recorte) |
| MOVIMENTOS SD3 emitidos no dia do apontamento (correlação temporal) | `D3_EMISSAO=20261029` = DTAPONT | `inferred` — trigger apontamento→baixa NÃO provado |

### 4.2 Pendentes de homologação (nunca derivar)

- Trigger apontamento→baixa automática (G2-01): expor correlação; `consumption_linkage` não existe no schema — evidências separadas bastam.
- Semântica final de `C2_PRIOR=500` (norma da família), `RE0`+`TM999` (classificar `warehouse_transfer` + flag `ambiguous_cf_semantics`), remoção de linha SH8, escolha de `reference_date` BOM (emission vs movement), política de conversão UM/arredondamento (B1_SEGUM/B1_CONV existe em componentes-irmãos fora do recorte).
- Tolerâncias/categorias/severidade (G2-06 — Joici/Michael).

### 4.3 Guarda de classificação (invariante)

```text
se execution_state != "evidenced"  → classification ∈ {requires_investigation, unclassified}
se quality.status != "complete"    → nunca "reconciled" sem ressalva (warning obrigatório)
estorno/transferência/MO/ajuste    → nunca somar em eligible_consumption
discrepância                       → NUNCA "falta física" / "fraude" / "erro do ERP"
```

## 5. Erros e estados — proposta

| Caso | Producer | BFF |
|---|---|---|
| `production_order` malformado (`^[0-9A-Z]{11}$`) | 400 `INVALID_PRODUCTION_ORDER` | 400 (valida antes de chamar) |
| `branch`/`unit` ausente ou ≠ 01/02 | 400 `INVALID_BRANCH` | 403 `UNIT_NOT_ALLOWED` |
| OP inexistente ou fora da filial | 404 `PRODUCTION_ORDER_NOT_FOUND` | 404 (sem vazar existência cruzada) |
| Sem JWT/identidade | — | 401 |
| Sem `supplies.access` ou escopo S2S | 403 `INSUFFICIENT_SCOPE` | 403 |
| Core `/me` indisponível | — | 503 `AUTHORIZATION_UNAVAILABLE` |
| S2S não provisionado/credencial inválida | 401 `S2S_UNAUTHORIZED` | 503 `S2S_CREDENTIALS_UNAVAILABLE` (fail-closed) |
| Fonte parcial (SG1 gap, SH6 indisponível) | 200 + `quality.status=partial` + warnings | propaga |
| Timeout/5xx upstream | — | 502/504 sanitizado (sem payload upstream) |

Envelope producer: `{success, message, data, error:{code,recoverable,fields}, meta}` — BFF `unwrap_delpi_envelope` + projeção allowlisted.

## 6. OpenAPI fragment — PROPOSTA (não publicar)

```yaml
# api-delpi (producer) — operationId: get_consumption_audit_order
/supplies/consumption-audit/orders/{production_order}:
  get:
    parameters:
      - {name: production_order, in: path, required: true,
         schema: {type: string, pattern: '^[0-9A-Z]{11}$'}}
      - {name: branch, in: query, required: true, schema: {type: string, enum: ['01','02']}}
    responses: {'200': ConsumptionAuditOrderDetail, '400', '401', '403', '404', '502'}
# supplies-api (BFF) — operationId: get_consumption_audit_order
/consumption-audit/orders/{production_order}:
  get:
    parameters:
      - {name: production_order, in: path, required: true,
         schema: {type: string, pattern: '^[0-9A-Z]{11}$'}}
      - {name: unit, in: query, required: true, schema: {type: string, enum: ['01','02']}}
    responses: {'200': ConsumptionAuditOrderDetail(projection), '400','401','403','404','502','503','504'}
```

## 7. Plano de testes de contrato — proposta (positive / sibling / negative)

| # | Caso | Dado de aceite (A1) | Resultado exigido |
|---|---|---|---|
| P1 | OP-06 op-01 cabo 10010030 | SG1 646/MI→80.75; SD4 80.75/0/80.75; SD3 RE2 80.75 | `reconciled`, eligible=80.75; RE0 0.64 **excluído** (nunca 81.39) |
| P2 | OP-06 op-02 terminal 10080329 | SD4 250/250/0; zero SH6/HZA; SH8 op-02 presente | `execution_state=pending`, `requires_investigation`/`unclassified` — **sem** alerta de falta |
| P3 | MOD216 | `B1_TIPO=MO` | excluído com `reason=labor_not_material` |
| P4 | Doc multi-OP 220039841 | linha op `24880701002` CF RE0 | atribuição por `D3_OP`; doc nunca agrega |
| S1 | OP-02 (mãe) | `D4_OPORIG`→4 filhas | `related_orders` com `parent_commitment_via_d4_oporig` invertido (child_of via prefixo); sem dupla contagem |
| S2 | OP-03 | PR0 → `C2_QUJE=0.125` | `produced_quantity_basis=stock_receipt`; SH6∪HZA evidenciado; zero SH8 |
| S3 | OP-04 | SH6 sem HZA | `execution_state=evidenced`, `channel=manual\|unknown` |
| S4 | Estorno (doc 220039260/364/268/086) | par RE2/DE2 ambos 'S' | net=0; linhas em `excluded` com `reversed:true` |
| N1 | `branch=03` / ausente | — | producer 400; BFF 403 |
| N2 | OP inexistente/curta | — | 400/404 conforme formato |
| N3 | S2S: sem token / escopo errado / client errado / token legado | — | 401/403; legado denied |
| N4 | BFF: `manage`-only; Core down; upstream 5xx/malformado | — | 403; 503; 502 sanitized |
| N5 | OP de outra filial | — | 404 sem vazamento cruzado |
| C1 | Schema producer↔BFF | — | contract test OpenAPI/DTO coerente (após freeze) |
| R1 | Regressão | E12 `consumption-analysis` | intocado |

## 8. Matriz de homologação — GATE-D2 (owners)

| # | Decisão | Owner | Proposta default | Estado |
|---|---|---|---|---|
| D-01 | Regra geral execução/operação (SH6 ∪ HZA→`evidenced`; SH8→pendente; causalidade baixa) | PCP | derivação conservadora §3 | PENDING |
| D-02 | Rótulo `C2_QUJE`=`stock_receipt`; SH6=qtd por operação; denominador de auditoria = C2_QUANT | PCP | conforme §4.1 | PENDING |
| D-03 | Semântica RE0/DE0/RE1/RE2 com TM999; devolução≠estorno; netting | PCP | classificador canônico + `quality_flags` | PENDING |
| D-04 | `structure_as_of` (emission_date proposto); conversão UM; arredondamento; substituições BOM | PCP | emission_date; sem conversão quando não há B1_SEGUM | PENDING |
| D-05 | `C2_PRIOR=500` = emergencial?; elegibilidade de OPs ao recorte | PCP | sem filtro por prior no MVP | PENDING |
| D-06 | Tolerâncias absolutas/%, categorias, severidade, timing de alerta | Joici/Michael | `tolerance_policy.id=glpi1353-v0`, valores null | PENDING |
| D-07 | S2S individual: escopo `consumption-audit.read`, client `supplies-api`, claims/audience | Segurança | conforme §2 | PENDING |
| D-08 | Schemas/envelope/códigos de erro finais (D2.2 → OpenAPI) | Segurança+Arquitetura | conforme §3/§5 | PENDING |
| D-09 | Nome/rota Portal, posição no roadmap, relação com E11 gate e E12 | Product Owner | página dedicada, distinta de E12 | PENDING |
| D-10 | `channel` de SH6 sem HZA (manual vs outro coletor) | PCP | `unknown` permitido | PENDING |

**Agrupamento por responsável (ordem sugerida de circulação):**

| Owner | Decisões | Bloqueio |
|---|---|---|
| PCP / owner Protheus | D-01, D-02, D-03, D-04, D-05, D-10 | semântica Protheus — pré-requisito dos demais |
| Joici / Michael | D-06 | tolerâncias e severidade — depende de D-01..D-05 |
| Segurança | D-07, D-08 | S2S/schema — independente; pode circular em paralelo |
| Product Owner | D-09 | naming/roadmap — independente; pode circular em paralelo |

## 9. Prontidão para B1 — checklist

```text
[ ] GATE-D2 aprovado com D-01..D-10 homologadas (explícito, por owner)
[ ] Escopo Keycloak `consumption-audit.read` provisionado (Security) — sem provisionamento manual
[ ] OpenAPI/DTO publicados a partir deste freeze (não antes)
[ ] HEAD reconciliado e limpo da superfície GLPI no momento do GO
[ ] Autorização explícita B1
```

**B1 = NOT_AUTHORIZED.** Esta proposta não implementa rota, DTO, OpenAPI, Keycloak, permissão, MFE ou deploy.

## 10. Controle documental

- Deriva de D2.1/D2.2 (DRAFT) + evidência A1; não substitui freeze formal.
- Divergência futura código×proposta ⇒ `EXECUTION_DRIFT`, correção no plano, nunca ajuste silencioso.
- Campos/códigos/identificadores em inglês (`english-code-identifiers`); PT só em docs/copy.
