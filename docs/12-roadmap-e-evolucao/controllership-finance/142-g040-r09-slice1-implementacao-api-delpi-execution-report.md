# CF-PROC0072 — Gate 040: R09 Faturamento × MOD — Slice 1 implementado na api-delpi + validação de paridade

Data: 2026-11-01. Autoridade: DR-1/DR-2 APPROVED (PO, 01/11/2026 — docs 138/140); DR-3 PENDING.
Baseline documental: `2f47ed985d` (doc 141). HEAD de início: `2f9eb7c331` = `origin/main` (sync).

## 1. Decisões aplicadas

| DR | Decisão | Aplicação |
|---|---|---|
| DR-1 APPROVED | Rota específica na api-delpi com modelo reconstruído por engenharia reversa | Implementada `GET /financeiro/billing-mod-breakdown` — reuse de código dos blocos canônicos (predicado SD2+SF4, expansão SG1, CTEs SG2 ranked, ponte SH1), não de contrato |
| DR-2 APPROVED | `costUnit`/`costTotal` sem fonte → ausência tipada | Nós `{value: null, state: "source_missing", reason: "cost_rate_basis_unavailable"}` por linha; `B1_CUSTD`/`BZ_CUSTD` **não** usados |
| DR-3 PENDING | Homologação informacional item a item com Controladoria | Permanece pendente; `official_parity = "pending"`; evidência determinística deste gate é insumo, não substituto |

## 2. Contrato implementado

`GET /financeiro/billing-mod-breakdown?period=YYYY-MM&branch=all|01|02`

- Envelope `api_delpi_success` + `meta.operationId`; `RouteContract("financeiro_billing_mod_breakdown", "playbook_report")`.
- `officiality: "operational_view"`, `officialParity: "pending"`, `provenance` com predicados e fontes, `limitations[]` com lacunas tipadas.
- `anchors[]`: `{product, branch, billedQty, modLines[], sourceMissing[], diagnostics{productsWithoutRouteOperations, unmappedResourceMod}}`.
- `modLines[]`: `{level: 02|04|06, anchorProduct, explodedProduct, modItem, modDescription, unit, operation, operationDescription, resource, stdTime{value,state:"sg2_cadastral"}, propagatedQty, hours{value,state}, costUnit, costTotal, modItemState}`.
- Ausência tipada: `SOURCE_MISSING != ZERO` — zero legítimo (`billedQty=0`, `hours=0`) distinguido de fonte ausente.

**Nota de idioma:** o segmento `financeiro` permanece PT por ser o namespace canônico consolidado da família (R03/R11/R12/R15 — decisão do contrato aprovado); o segmento novo `billing-mod-breakdown` é EN kebab-case.

## 3. Arquivos

| Arquivo | Camada |
|---|---|
| `app/application/dto/financeiro_billing_mod_breakdown/` (request) | request tipado (period/branch, `period_start/end`, `requested_branches`) |
| `app/domain/ports/financeiro_billing_mod_breakdown/billing_mod_breakdown_repository_port.py` | port (3 reads row-oriented) |
| `app/infrastructure/persistence/totvs/financeiro_billing_mod_breakdown/billing_mod_breakdown_sql.py` | builders parametrizados |
| `.../billing_mod_breakdown_repository.py` | adapter `BaseRepository`, chunking `_IN_CHUNK=500` |
| `app/application/use_cases/financeiro_billing_mod_breakdown/get_billing_mod_breakdown_use_case.py` | semântica DLP204 |
| `app/composition/financeiro_billing_mod_breakdown_composer.py` | wiring + gate compartilhado |
| `app/interface/http/routes/financeiro/billing_mod_breakdown_router.py` | rota + guard S2S |
| `app/interface/http/route_contract_registry.py` | contrato registrado |
| `app/interface/http/openapi_agent_metadata_builder.py` | label da entidade |
| `app/main.py` | `include_router` |
| `tests/test_financeiro_billing_mod_breakdown.py` | 24 testes |
| `api-delpi/scripts/r09_billing_mod_parity_probe.py` | probe determinístico XLSB×motor |

## 4. Regras implementadas (fonte → regra → evidência)

| Regra | Fonte | Implementação |
|---|---|---|
| Âncora PA | `fGetProds` literal (PRW:121-136) | `SB1 ∩ SD2` por filial, `D2_EMISSAO ∈ mês`, `∃ SF4 F4_DUPLIC='S'`; sem filtro `D2_TIPO` (literal) |
| `Qtd Fat.` | BR-R09-006 (4.476/4.476) | `Σ D2_QUANT` com `D2_TIPO<>'D'`; linha = próprio billed do produto, fallback billed da âncora |
| Explosão | `Estrut` (PRW:323-382) | filhos **diretos** SG1 por nível (`Estrut` retorna só nível imediato — resultado da recursão interna é descartado); dedup `(pai,comp,trt)` (aScan); `ExplEstr>0` → `G1_QUANT>0` + vigência corrente; skip auto-referência |
| Níveis | BR-R09-005 | `02` PA · `04` componente direto · `06` subcomponente — os únicos níveis MOD do DLP204 (o '07' seria linha MP, par11=Não) |
| Multiplicidade | `Estrut`/aScan por chamada | mesma PI sob pais distintos = ocorrências separadas preservadas |
| MOD | BR-R09-007 + prova live | `SG2.G2_RECURSO` → `SH1010.H1_CCUSTO` → `B1_COD = 'MOD'+cc` (evidência: `CT-33A`→`393`→`MOD393`, `CT-31`→`20301`→`MOD20301`) |
| `Quantidade` | BR-R09-008 / doc 141 | `G2_TEMPAD` cadastral (roteiro `01` = MV_PAR09 default), ranked latest por (produto, operação), filial preferida |
| `Horas` | BR-R09-009 identidade | `propagatedQty × stdTime` |
| Custos | DR-2 | ausência tipada `source_missing` |
| Guard | ADR-010 + doc 49 §8 | S2S `stock-inventory.read` × client `controllership-finance-api` + delegated user + gate `FINANCEIRO_STOCK_INVENTORY_ENABLED` (fail-closed) |

## 5. Divergência conhecida — roteiro congelado da OP (SHY)

BR-R09-007/008: ~96% das linhas do artefato usam `HY_TEMPAD` do roteiro **congelado da OP** (`HY_OP = C2_NUM+C2_ITEM+C2_SEQUEN`). A seleção de OP por produto (e o divisor `÷C2_QUANT` de desdobramento) é `PENDING` (E9) — não há regra comprovada para reconstrução set-based. Slice 1 **não** implementa SHY: a lacuna é medida, não inventada.

## 6. Gate H — Paridade informacional vs `Fat x MOD.xlsb` (2026-09)

Execução real no container `delpi-api-delpi` local (read-only), probe determinístico:

| Métrica | Resultado |
|---|---|
| Âncoras faturadas | **521** — baseline histórico confirmado (f01 299 + f02 222) |
| Linhas MOD calculadas | 1.465 |
| Chaves (filial,PA,level,MOD) correspondentes | **1.395** |
| `QtdFat` corretas nas chaves | **1.395/1.395 = 100%** |
| `Quantidade` (=G2_TEMPAD) corretas | 1.179 (84,5%) — 216 divergências = roteiro OP (HY) ≠ cadastral (G2), causa documentada BR-R09-008 |
| `Horas` corretas | 1.179 (seguem `Quantidade`) |
| Linhas ausentes | 3.081 — proveniência SHY (roteiro congelado OP) + casos sem ponte MOD; amostras registradas |
| Linhas excedentes | 70 — ops cadastrais que a SP não emitiu (roteiro/revisão divergente); amostras registradas |
| Custos | fora de escopo (DR-2) |

`PASS` global **não** declarado por cobertura — divergências abertas e explicadas abaixo.

## 7. Gates executados

| Gate | Estado |
|---|---|
| A inventário | PASS — blocos canônicos reutilizados por composição |
| B contrato | PASS — envelope/meta/registry padrão |
| C âncoras | PASS — 521 exato vs baseline |
| D explosão | PASS — níveis 02/04/06, dedup, multiplicidade, validade |
| E operações/MOD | PASS — ponte comprovada live; baselines 4 produtos reproduzíveis (match por regra) |
| F horas/qtd | PASS — identidades pinadas em teste; 100% qtdfat live |
| G custos | PASS — ausência tipada, nada calculado |
| H paridade | EXECUTADO — métricas reais acima; divergências abertas com causa |
| I regressão/segurança | PASS — ver §8 |
| J vídeo | `TEST_NOT_RUN` — sem decoder no ambiente (mantido) |
| K homologação técnica | EXECUTADA — motor vs DB real local, read-only |
| L documentação | este documento + ficha + ledger |

## 8. Testes e segurança

- `test_financeiro_billing_mod_breakdown.py`: **24 PASS** — superfície de rota, 401/403 S2S (token ausente/inválido, cliente errado, escopo insuficiente), gate fail-closed (`scope_unavailable`), principal de serviço ≠ usuário, params inválidos, envelope+meta, engine (níveis, fallback QTDFAT, dedup, multiplicidade, edges inválidas, unmapped→diagnóstico, ausência tipada ≠ zero, zero legítimo, ambas filiais), builders SQL parametrizados.
- Regressão financeiro: closing_state (3) + billing_exclusion_roster (36) + stock_kardex + settlements = **60 PASS**; total família = 84 PASS.
- Gates: `audit_openapi_operation_ids.py --check` OK · `audit_route_test_coverage.py --check` OK (sincronizado).
- Sem secrets em logs; NENHUM write no Protheus (queries `WITH (NOLOCK)` read-only); nenhuma permission nova; S2S padrão vigente preservado.
- `pytest` full-suite da api-delpi não executado (escopo: família financeiro); sem evidência de quebra — diff é aditivo.

## 9. Resíduos e owners

| Resíduo | Owner | Condição de resolução |
|---|---|---|
| SP `STP_DELPI_FORMA_PRECO_*` não localizada | DBA/TOTVS (E9) | busca RPO/backups |
| Roteiro congelado OP (SHY): seleção de OP + divisor desdobramento | Owner técnico + Controladoria | regra comprovada de OP-por-produto |
| Base de taxa MOD | Controladoria | `BZ_CUSTD` as_of (BR-R09-010, 4.469/4.469 em auditoria anterior) — candidato Slice 2 |
| Divergências qty/hours (216) + ausentes (3.081) + extras (70) | Controladoria (DR-3) | homologação item a item |
| Validade de estrutura na data de execução (vs ~06-07/10 do artefato) | técnico | drift estrutural é semântica fiel ao DLP204; registrar em paridade |
| Vídeo Gate 039 | executor | `TEST_NOT_RUN` mantido |
| Docs 138/140 (PRs #126/#127) | PO | branches remotas não integradas — autoridades lidas via `git show` |

## 10. Próximo slice (recomendado Gate 041)

1. SHY por OP: comprovar seleção de OP por produto (SC2 ↔ HY_OP) + divisor; adicionar `stdTimeSource:"shy_frozen_op"` como fonte preferencial mantendo G2 fallback.
2. Custos: validar `SBZ.BZ_CUSTD` as_of por emissão (BR-R09-010) sob decisão DR-2-revisão.
3. Contrato BFF na `controllership-finance-api` (effective permissions Core) — fora do Slice 1.
4. Homologação DR-3 com a Controladoria usando este motor como fonte.

## 11. Parecer

**`ACCEPT_WITH_RESIDUAL`** — Slice 1 tecnicamente implementado e validado: contrato aprovado, segurança S2S fail-closed, âncoras 521 exatas, QtdFat 100% nas chaves, ausência tipada honesta. Cobertura MOD parcial por lacuna de fonte (SHY) documentada — divergências com causa e owner, sem cálculo inventado.
