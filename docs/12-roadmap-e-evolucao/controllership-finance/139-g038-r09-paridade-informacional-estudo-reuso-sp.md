# CF-PROC0072 — Gate 038: R09 Faturamento × MOD — Estudo de paridade informacional, reuso api-delpi e pacote decisório

Data: 2026-11-01. Escopo: investigação técnica read-only; **nenhum runtime alterado**.
Baseline: Gate 037 `16764ae9a4`; decisões PO no doc 138 (PR #126, branch `docs/cf-r09-po-decisions-g038-20261101`).

## 1. Autoridade e decisões vigentes (doc 138)

| Decisão | Estado |
|---|---|
| D1 — estudar SP + reuso antes de rota específica | DIRECTION APPROVED; design/implementação condicionados a este estudo + gate |
| D2 — `OPERATIONAL_VIEW` com `official_parity=PENDING` | APPROVED |
| D3 — api-delpi = autoridade SQL/TOTVS; BFF orquestra; CLARA/MFE só contrato | APPROVED |
| D4 — persona negativa IAM `INCONCLUSIVE`, não convertida em PASS | APPROVED |

## 2. Gate A — Inventário de rotas/building blocks api-delpi

| Recurso | Localizador | Semântica | Reuso R09 |
|---|---|---|---|
| `GET /products/{code}/structure` | `product_routes.py:633` + `bom_tree_builder.py` | Expansão SG1 **por produto** (componentes de material, conversões) | Parcial — grão por produto, não por período×lote |
| SHY+SG2 ranked CTEs | `production_fabril_standard_time_sql.py` | Tempo padrão canônico (`G2_TEMPAD`, `G2_SETUP`, SHY fallback), set-based por filial | **Alto — fonte canônica de MOD/horas** |
| Predicado faturamento | `billing_exclusion_roster` (R11) | Eixo `D2_EMISSAO` já governado | Padrão reutilizável |
| Machine load / OEE | `production/` routers | Roteiros/operações SG2 por contexto fabril | Referência de join, não shape R09 |

**Conclusão Gate A:** nenhum endpoint existente retorna o shape R09 (âncoras do período × linhas MOD×nível). Os **blocos canônicos** (predicado SD2+TES, expansão SG1, CTEs SHY/SG2) existem e são reusáveis dentro de uma rota nova — reuso de código, não de contrato.

## 3. Gate B — SP `STP_DELPI_FORMA_PRECO_<empresa>`

| Evidência | Resultado |
|---|---|
| `DLP204.prw:397` | `EXEC STP_DELPI_FORMA_PRECO_<emp>(aModPar1,2, aPars9, aPars1,2, aModPar3,5)` → alias `TRBMOD` |
| `sys.procedures` (DB DELPI, prod) | **zero** procedures `STP_%`/`FORMA_PRECO`/`DELPI%` — PROVEN ausente do catálogo produtivo |
| Repo/migrations/acervo SQL | search miss — sem script de criação no acervo autorizado |
| Schema `TRBMOD` (consumo, PRW:410) | `PA, COMP, B1_COD, B1_DESC, QTDFAT, B1_UM, G2_TEMPAD, CUSTO_UNIT, CUSTO_TOTAL, CUSTOPROD, HORAS` |
| Fallback PRW | `QTDFAT == 0 → aModPar[4]` (qty faturada propagada por parâmetro) |
| Indício interno | `G2_TEMPAD` aparece no output → SG2/roteiro é fonte interna provável da SP |

**Classificação: `SOURCE_MISSING_WITH_SEARCH_SCOPE`.** Escopo pesquisado: catálogo produtivo DELPI, acervo de scripts, repo. Não pesquisado: RPO Protheus binário, backups históricos, DBs de versões antigas — requer ação do DBA/owner TOTVS.

Cálculos que permanecem sem fonte comprovada: regra de classificação das linhas MOD (qual componente/operação vira linha), base de `CUSTO_UNIT`/`CUSTO_TOTAL`/`CUSTOPROD` (B1_CUSTD? custo médio? custom?), semântica exata de `QTDFAT` por linha, derivador de `HORAS` (provável `QTDFAT × G2_TEMPAD`, não provado).

## 4. Gate C — Paridade informacional (evidência live, DB prod, 2026-09)

| Dimensão | Artefato `Fat x MOD.xlsb` | Predicado literal PRW (teste live) | Estado |
|---|---|---|---|
| Âncoras PA | 1.767 ("âncoras") | **521 PA distintos** (f01=299, f02=222) | `TO_INVENTORY` — "âncora" do artefato provavelmente conta âncora×nível; exige inspeção campo a campo do .xlsb |
| Linhas | 2.459 + 2.017 = 4.476 | n/d sem motor | `PENDING` |
| Eixo/TES | `D2_EMISSAO`, `F4_DUPLIC='S'` | idêntico — literal confirmado no PRW | `PROVEN` |
| MOD linhas | níveis 0/1/2, COMP 02/04/06 | SG1 só material (top comps 1xxxxxx); sem itens MOD `02/04/06` em SB1 | `TO_INVENTORY` — MOD provável = operações SG2/roteiro, não itens SG1 |
| `G2_TEMPAD` | presente via SP | SG2 canônico existe (ops 01/02/03, tempos reais) | `PROVEN` fonte |
| Custos | via SP | base não comprovada | `SOURCE_MISSING` |

## 5. Gate D — Alternativas

| | A — Reuso/composição | B — Extensão compatível | C — Rota específica |
|---|---|---|---|
| Viabilidade | Nenhum endpoint compõe o shape; 1.767 chamadas/produto = O(n) proibitivo | `/{code}/structure` é por-produto; estender a período×lote quebra semântica | Compõe building blocks canônicos (SD2+TES, SG1 set-based, SHY/SG2 CTEs) |
| Impacto consumidores | zero (não factível) | risco de regressão em consumers do structure | zero — aditivo |
| Paridade informacional | insuficiente | distorce | máxima comprovável sem SP |
| Recomendação | rejeitada como estratégia primária | rejeitada | **recomendada** |

**Recomendação fundamentada:** Alternativa C — `GET /financeiro/billing-mod-breakdown` na api-delpi, reusando internamente os CTEs canônicos existentes (não duplicando regra). Campos com fonte comprovada retornam valor; campos dependentes da SP retornam nós tipados `SOURCE_MISSING` — mesmo padrão `closing_state` (nunca zero, nunca inventado).

## 6. Gate E — DECISION_REQUIRED para o PO

### DR-1 — Escopo informacional da rota R09

- **EVIDENCE:** sem SP, MOD-derivation, custos e QTDFAT não são reproduzíveis com prova; âncoras, níveis e tempo padrão são.
- **OPTION A:** implementar `OPERATIONAL_VIEW` com os campos comprovados (âncoras PA, expansão por nível, `G2_TEMPAD`, horas derivadas declaradas) + nós `SOURCE_MISSING` para custos/QTDFAT-semântica. IMPACT: entrega cedo, honesto, mas não replica custos do artefato.
- **OPTION B:** aguardar owner TOTVS localizar a SP/RPO para cobertura total. IMPACT: bloqueio indefinido.
- **RECOMMENDATION:** A — paridade informacional parcial provada > espera; contrato declara lacunas.
- **OWNER:** PO + Controladoria. **REQUIRED_APPROVAL:** PO. **NO CHANGE APPLIED.**

### DR-2 — Fonte MOD: operações SG2 vs componentes SG1

- **EVIDENCE:** SB1 sem itens MOD 02/04/06; SG2 tem operações+tempos por PA; artefato COMP=02/04/06 não corresponde a G2_OPERAC observado.
- **OPTION A:** MOD = operações SG2 por PA-âncora (tempo padrão = MOD). IMPACT: provável correto, requer validação contra artefato item a item.
- **OPTION B:** manter `TO_INVENTORY` até inspeção do artefato confirmar o que COMP representa. IMPACT: atrasa contrato.
- **RECOMMENDATION:** B — uma sessão de leitura do `.xlsb` (Controladoria) resolve em horas o que inferência não prova; depois A.
- **OWNER:** Controladoria + PO. **REQUIRED_APPROVAL:** PO. **NO CHANGE APPLIED.**

### DR-3 — Aprovação do contrato TARGET

`GET /financeiro/billing-mod-breakdown?period&branch` — envelope tipado: `anchors[] {product, billedQty, modLines[] {level, operation, stdTime, hours, costUnit?, costTotal?}, sourceMissing[]}`, `officiality=operational_view`, `official_parity=PENDING`, proveniência+limitações, ausência tipada. **REQUIRED_APPROVAL:** PO.

## 7. Readiness Slice 1

**`DECISION_REQUIRED`** — depende de DR-1 + DR-3 (e DR-2 ou sua resolução documental). Zero código neste gate.

## 8. Resíduos

- SP: `SOURCE_MISSING_WITH_SEARCH_SCOPE` — ação DBA/TOTVS (busca em RPO/backups).
- Persona negativa IAM: `INCONCLUSIVE` (D4 aprovado — permanece com owner IAM).
- Artefato `.xlsb`: inspeção campo a campo pendente (Controladoria) — resolve semântica "âncora" 1.767 vs 521 e COMP.
- Paridade oficial: `PENDING` até homologação informacional item a item.
