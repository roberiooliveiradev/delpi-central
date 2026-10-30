# Gate Contratual — R10 Centro de Custo + R11 NF a Desconsiderar + Comparação Universal (CLARA)

**Gate:** `CF-PROC0072-R10-R11-CLARA-COMPARISON-CONTRACT-GATE-019`
(fila 015 do Plano 113 §37)
**Data:** 2026-10-30 · **Tipo:** `READ → INVENTORY → VERIFY → CLASSIFY → CONTRACT → DECISION → REPORT` — documental/contratual, **zero runtime/migration/deploy**.
**Autoridade:** GO PO 30/10/2026. **BASE_HEAD:** `f0f84c7b94` (inclui REWORK-018 set-based TTAT + GLPI-1353 v0.5.1 + SEMANTIC-002).
**Depende de:** [doc 118 OPS-11/12 + §19 Q02/Q05](118-base-canonica-processo-fechamento-mensal-proc0072.md), [doc 85 §10](85-ciclo2-catalogo-regras-negocio-r01-r15.md), [doc 84 §5.4/§5.5](84-ciclo2-paridade-monetaria-relatorios-oficiais.md), [doc 122 §14](122-gate-contratual-r06-r07-kardex-inventarios-2026-10-30.md), [doc 120 §7](120-plano-integracao-relatorios-portal-clara-2026-10-30.md), [doc 121](121-clara-paridade-portal-matriz-cp-2026-10-29.md), [doc 119](119-plano-mestre-clara-mcp-semantico-2026-10-29.md).

---

## 1. Preflight (AC-01/02)

`git status` limpo; worktrees concorrentes inventariadas e preservadas (`delpi-central-f43-wt` GLPI-1353, `cf-audit-wt`, `cf-r01r02-wt`, delia-*/davi-*). Nenhuma sobreposição com este gate documental. Arquitetura CLARA vigente confirmada no HEAD: **6 tools semânticas** (`get_context`, `read`, `analyze`, `knowledge`, `execute`, `delete`), sem tools planas novas (doc 119) — preservada.

## 2. D1 — Inventário R10 · Notas por Centro de Custo — `PROVEN` (estoque), `TARGET` (integração)

**Produtor oficial:** `EDAPP` — consulta genérica monotabela **SD1** exportada (aba `SCAGQGA0.XML`, headers = títulos SX3 `D1_*`); artefato `CC matriz.xlsb` = 353 linhas, filial 01, 139 documentos, 46 centros de custo, Σ `Vlr.Total` = **169.704,12** — reconciliação física exata (doc 84 §5.4, `PASS`). **Grão = item SD1** (linha física). Não é relatório Protheus nativo nem consulta EDAPP com SQL própria a confirmar — regra de seleção reconstruída e corroborada pelo owner (rodada 25, BR-R10-001..005).

**Seleção homologável** (`PROVEN`, doc 85 §10):
`D1_FILIAL` escopo ∩ `D1_DTDIGIT` ∈ competência **[eixo digitação, não emissão]** − 13 TES excluídos `{001,003,016,020,030,040,080,083,085,120,159,204,318}` − `D1_TP='MP'` − 6 linhas coparticipação plano saúde/odonto (TES 046, tipo GG, sem CC, grupo benefícios).

**Campos:** `D1_DOC`, `D1_ITEM`, `D1_COD`+desc, `D1_QUANT`, `D1_VUNIT`, `D1_TOTAL`, `D1_TES`, `D1_CF`, `D1_CC`, `D1_PEDIDO`, `D1_LOCAL`, `D1_DTDIGIT`, `D1_EMISSAO`, `D1_FORNECE`/`D1_LOJA`+nome. Binding 353/353 (BR-R10-001).

**E10 — classificação Direto/Indireto/Adm:** `AS-IS` manual pós-exportação (coluna sem título: 122+2 Direto, 128 Indireto, 101 Adm; subtotais derivados Adm 99.297,81 · Ind 38.554,82 · Dir 31.851,49). **Não é campo SD1 nem CTT** — não automatizar sem fonte homologada → **D-01 `DECISION_REQUIRED`**.
**Q02 aberta:** lista narrada = "12 tipos" vs 13 fisicamente excluídos (`016`, `159` observados, ambos `F4_DUPLIC='N'`); ambiguidade transcrição `02`/`04` — confirmação formal do owner → E10.

## 3. D1 — Inventário R11 · NF a desconsiderar — `PROVEN` (estoque), finalidade `E11`

**Produtor oficial:** `EDAPP` — export monotabela **SD2** (aba `Planilha2`, 184 colunas SX3 `D2_*`, sem `Emissao`/`Cliente`/`Serie`/`Custo`); artefato `NF a desconsiderar.xlsb` = **11 linhas**, filial 01, 11 documentos distintos, Σ `D2_TOTAL` = **97.462,71** — identidade de conjunto (não só cardinalidade) e paridade monetária 0,00 (doc 84 §5.5, `PASS`). **Grão = item SD2**. Conferência humana do faturamento ("desconsiderar" = roster de exceção, não regra de exclusão no ERP).

**Seleção:** `D2_FILIAL='01'` ∩ `D2_EMISSAO`∈[09/2026] ∩ `D2_GRUPO='9035'` ∩ `D2_TES='594'` — equivalência bidirecional observada **nesta competência**; qual predicado o operador usou (grupo vs TES) é indistinguível → E11.
**Semântica:** industrialização para terceiros — NF típica = item físico `9026*` TES 510 (`F4_ESTOQUE='S'`, custo>0, CFOP 5124) + item faturamento TES 594 (`F4_ESTOQUE='N'`, `D2_CUSTO1=0` **estrutural**, CFOP 5101); 8/11 NFs casam item-irmão 510+594; 3 têm só 594. Clientes terceiros (não intercompany). `F4_DUPLIC='S'` (gera receita/duplicata).
**Efeito no CPV canônico:** nulo — `GET /supplies/cpv` (`SUM(D2_CUSTO1)` CFOP∈{5101,5124,6101,6124}): as 11 linhas contribuem R$ 0,00 (custo=0 desde origem, TTAT insert MATA460A `COLD=CNEW=0`, zero alterações). Receita (97.462,71) integra faturamento/ROL.

**E11 — `DECISION_REQUIRED`:** qual apuração efetivamente "desconsidera" essas NFs (numerador CPV, denominador ROL, conferência DRE?); vigência por competência; aprovação/reversão; roster persistido vs. recalculado por predicado; estados do doc 56 §Reg.18 (`excluded_from_analysis` etc.) são `TARGET_DECISION_REQUIRED`.

## 4. D2 — Matriz de reuso

| Candidato | Owner | Classificação | Evidência |
|---|---|---|---|
| `vw_fin_despesas_centro_custo` + `GET /financeiro/despesas-centro-custo/*` (api-delpi, plugin `financeiro-centro-custo`) | api-delpi/TOTVS-SD1 | **`REUSE_PARTIAL`** | Mesmo domínio, seleção **diferente**: view usa `D1_EMISSAO` (não `D1_DTDIGIT`), exige `D1_CC<>''`, não exclui MP/13 TES/benefícios (448 linhas set/26 f01; 269/353 cobertas). **Não transplantar seleção da view.** Filtros/ordenação/paginação/rankings/exports prontos (BR-R10-007) |
| `CpvQueryRepository` `GET /supplies/cpv` | supplies/api-delpi SD2 | `REUSE_PARTIAL` | Semântica verificada e **coerente** com R11 (contribuição R$0); o "desconsiderar" é camada de conferência, não predicado da API (BR-R11-005/006) |
| `StockKardexQueryService` R06/R07 (SD1–SD4+TTAT+SB9) | api-delpi | `REUSE_PARTIAL` | `F4_ESTOQUE='S'` explica ausência das NFs R11 no MATR910; não produz lista de exceções (BR-R11-006) |
| `F4_*` catálogo TES (`SALES_INVOICE_COST_CFOPS`) | api-delpi/shared | `REUSE_CONFIRMED` | Reuso do predicado `F4_ESTOQUE`/`F4_DUPLIC`/`F4_CF` nos contratos R10/R11 |
| BFF proxies + `reports_router` GET `/reports/*` | controllership-finance-api | `REUSE_CONFIRMED` | Padrão `period`+`branch`+AuthZ+timeout 30s; adicionar proxies R10/R11 e comparação |
| Exports CSV/PDF (`/export` 120s) | BFF+MFE | `REUSE_PARTIAL` | Padrão existente; estender aos novos relatórios e à comparação exportável |
| `reports_matrix` entries R10/R11 = `MANUAL_EVIDENCE` | BFF | `TARGET` | Promover a `OPERATIONAL_VIEW` quando contratos homologados |
| Consumption-audit `/comparison` (api-delpi, GLPI-1353) | api-delpi | `REUSE_PARTIAL` (precedente de padrão) | Batch bounded 2–10 itens, mesma filial obrigatória, owner calcula, BFF proxy — template para contrato comparativo |
| CLARA `read`/`analyze` semânticos + registries | controllership-finance-api/MCP | `REUSE_CONFIRMED` | `read(report.*)` para consultas individuais; `analyze` para comparação — **sem novas tools planas** |
| `@delpi/plugin-ui` páginas/tab com estado vazio | MFE/kit | `REUSE_PARTIAL` | Páginas R10/R11 + painel comparativo seguem o kit |

## 5. D3 — Contratos TARGET (não implementados)

### R10 — `TARGET_CONTRACT`

```
api-delpi  GET /controllership/cost-center-expenses?period=YYYY-MM[&branch][&cc]
           [&natureza][&cost_class][&include_mp=false][&tes_excluded=true]
           [&sort][&page][&page_size≤100]
           → {period, branch_scope, referenceDate, selection:{axis:'D1_DTDIGIT',
             excluded_tes:[13], exclude_mp:true, exclude_benefits:true},
             totalValue Decimal(15,3), lineCount, costClassBreakdown?{…},
             items[], provenance{source:'SD1',producer:'EDAPP-replica',version,asOfConvention}}
BFF        GET /reports/cost-center-expenses (proxy + AuthZ + branch-scope) ; /export
CLARA      read(report.cost_center_expenses) — registry semântico
MFE        página + resumo por CC + classificação + paridade
```

`cost_class`∈{`DIRETO`,`INDIRETO`,`ADM`,`UNCLASSIFIED`} — **opcional até D-01**; `UNCLASSIFIED` é estado legítimo, não filtro inventado. Erros: `400` params, `401` sem credencial, `403` filial fora do escopo (fail-closed), `503` fonte, `504` upstream>timeout. Nunca `200` com zero implícito.

### R11 — `TARGET_CONTRACT`

```
api-delpi  GET /controllership/billing-exclusion-roster?period=YYYY-MM[&branch]
           [&group=9035][&tes=594][&doc][&supplier][&warehouse]
           [&review_state][&sort][&page][&page_size≤100]
           → {period, branch_scope, roster:[{doc,series?,item,cod,productDesc,
             tes,cf,group,quant,prcven,total,custo1=0,sibling_items?,cc?,store,
             review_state?,reason?,reviewer?,decided_at?}], summary{count,
             totalValue,byReviewState?}, provenance{source:'SD2',…}}
BFF        GET /reports/billing-exclusion-roster + /export
CLARA      read(report.billing_exclusion_roster)
```

`review_state`/`reason`/`reviewer` = **`TARGET` bloqueado em D-02** — se D-02 = "recalculado por predicado" os campos são derivados com `decided_at=null`; se = "roster governado" exige tabela+migration (gate futuro, **não** neste). Enriquecimento item-irmão TES 510/CFOP = join SD2 mesmo documento — `TARGET`.

## 6. D4 — Comparação Universal R01–R15 — `TARGET`

**Princípio:** motor comparativo **não recalcula** regras de negócio — orquestra contratos governados existentes e aplica operações comparativas aprovadas (diff mesma semântica, variação %, agregações suportadas). Owner do cálculo permanece no owner do relatório.

**Contrato proposto** (owner recomendado: BFF `controllership-finance-api` — veja D-03):

```
POST /analysis/report-comparison
{ comparison_kind: 'PERIOD'|'BRANCH'|'REPORT'|'DOCUMENT'|'TREND'|'EXPLAIN',
  subjects: [{report_id|capability, period, branch, filters{...}}],   // 2..6
  measure: string,            // 'totalValue'|'lineCount'|measure canônica
  grain: 'period'|'branch'|'cc'|'doc'|'product'|'natureza',
  baseline: index }
→ { status:'EQUAL'|'DIFFERENT'|'INCOMPATIBLE'|'INSUFFICIENT_EVIDENCE'|'PARTIAL',
    subjects:[{…resumo por sujeito, provenance, parity…}],
    diffs:[{grain_key, base, target, delta, deltaPct}],
    normalization:[{rule,applied}],
    incompatibilities:[{reason, sub_i, sub_j}],
    provenance{contracts[], versions[], asOfConvention[]} }
```

**CLARA:** `analyze(report_comparison)` — novo entry em `ANALYZE_ACTIONS` (ou `read` composto — **D-04**); descrição declara medidas compatíveis. **Sem nova tool plana.**

**Limites TARGET:** 2–6 sujeitos; mesmo `branch_scope` de segurança para todos; timeout 30s sujeito + 60s agregação; `PARTIAL` se algum sujeito falhar (`subject_error` explícito, nunca zero implícito); cardinalidade `diffs` ≤ 500 itens + paginação.

**Semântica de `EXPLAIN`:** quando `INCOMPATIBLE`/`DIFFERENT`, resposta inclui campos explicativos com citação doc (ex.: "saída kardex ≠ CPV porque MATR910 mede custo de saída no kardex e CPV é faturamento gerencial por CFOP — doc 85 §8/§10").

## 7. Matriz de compatibilidade semântica

| Par | Classe | Regra |
|---|---|---|
| R05 × R06 | `COMPARABLE_WITH_NORMALIZATION` | R05 E/S agregado (quantidade) × R06 kardex **valorizado** — comparar `quantity` sim; `value` com aviso `RELATED_NOT_EQUIVALENT` (R05 bruto × R06 custo) |
| R06 × CPV | `RELATED_NOT_EQUIVALENT` | Saída de estoque ≠ CPV: kardex = `F4_ESTOQUE='S'`+valorização TTAT; CPV = `SUM(D2_CUSTO1)` CFOP venda — escopo, sinal e base distintos; explicável por item-irmão |
| R06 × R07 | `RELATED_NOT_EQUIVALENT` | R07 = subconjunto `D3_DOC='INVENT'` dos movimentos R06 — comparável com filtro explícito, nunca como totais |
| R03 × R05 | `RELATED_NOT_EQUIVALENT` | Estoque posição (SB9 snapshot) × movimentação (SD1–SD4) — dimensão estática × fluxo |
| R03 × R08 | `RELATED_NOT_EQUIVALENT` | Estoque físico × material em processo (SD3/SC2 loc99) — universo disjunto por `MV_LOCPROC` |
| R10 × R11 | `COMPARABLE_WITH_NORMALIZATION` | Despesas SD1 × roster SD2 — mesmo grão NF/item, eixos de data distintos (digitação × emissão); `DOCUMENT` comparison = `D1_DOC`∩`D2_DOC` com aviso de eixo |
| R09 × R10 | `RELATED_NOT_EQUIVALENT` | Faturamento/MOD × despesas CC — medidas distintas; `DOCUMENT`/`PRODUCT` linkage possível |
| R12 × R15 | `NOT_COMPARABLE` | Estado de custo (R12) × cutoff/processo (R15) — sem medida comum |
| Mesmo relatório × períodos | `DIRECTLY_COMPARABLE` | Mesma seleção/owner, `as_of` idêntico — ex.: R06 jul×ago×set (mesma convenção TTAT doc 122) |
| Mesmo relatório × filiais | `DIRECTLY_COMPARABLE` | Se AuthZ cobrir ambos os escopos; senão `403` fail-closed |
| Tabela não inventariada | `INSUFFICIENT_EVIDENCE` | Default — nunca comparar por rótulo similar |

## 8. D5 — Segurança (sem novas permissions)

`effective = capability(.access) AND branch_scope AND business_rule` — backend decide; MFE não é controle. Comparação exige autorização **sobre todos os sujeitos**: usuário com acesso a 1 relatório × outro restrito → sujeito restrito retorna `403`/`INCOMPATIBLE` sem revelar existência (fail-closed, sem shape anômalo). Filial fora do escopo do usuário → `403` por sujeito; comparação parcial só se ≥2 sujeitos autorizados. `.access.dre` = somente recursos documentais DRE — comparação não a usa. Export de comparação exige mesma autorização READ (não há permission de export nova — padrão atual). CLARA = identidade delegada, mesmos contratos. Audit: `COMPARISON_PERFORMED` com subjects+params+SHA resposta + quem negou.

## 9. D6 — Modelo de conhecimento CLARA — `TARGET`

**Ficha por relatório** (esquema canônico, entrega como docs governados + entries no `corpus_manifest` com `related_report_ids`):

```
Identificação: rid, nome, aliases, finalidade, processo, owner_funcional, owner_tecnico, produtor
Fonte: API responsável, tabelas/integrações, artefatos históricos, docs, versão_fonte, proveniência
Regras: filtros, fórmulas, campos, classificações, inclusões, exclusões, sinais, datas, granularidade, precisão
Uso: consultas, filtros autorizados, exports, detalhamentos, comparações válidas/inválidas
Governança: permissions, escopos, status_operacional, status_paridade, dependências, limitações, pendências, evidências
Explicativo: interpretação, diferenças vs outros relatórios, FAQ, exceções, exemplos PROVEN
```

**Proveniência obrigatória:** toda afirmação relevante → fonte verificável (doc+seção, código+arquivo, contrato, Evidence ID, SHA). Classificação `PROVEN|TO_INVENTORY|PLANNED|TARGET` por item — ficha nunca rebaixa hipótese a fato.
**Atualização transversal:** mudança em relatório → contrato + ficha + relações + Help + corpus + versão + hashes + teste de citação + paridade runtime. Corpus **não publicado neste gate** (autorização separada) — `TARGET` para pipeline E8.

## 10. D7 — Ledger RQ/AC (extraído; registro completo no doc 23 §gate-019)

| RQ | Regra | Status |
|---|---|---|
| RQ-R10-01 | Seleção SD1 = eixo `D1_DTDIGIT` − 13 TES − MP − benefícios | `PROVEN` (doc 84 §5.4 353/353, Σ169.704,12) |
| RQ-R10-02 | Classificação Direto/Ind/Adm homologada ou `UNCLASSIFIED` | `TARGET` — D-01 |
| RQ-R11-01 | Roster SD2 = `9035`∩`594`∩`D2_EMISSAO`∩filial | `PROVEN` (11/11, Σ97.462,71) |
| RQ-R11-02 | Finalidade do "desconsiderar" definida pelo owner | `TARGET` — D-02 |
| RQ-CMP-01 | Comparação só orquestra contratos governados, nunca recalcula | `TARGET` |
| RQ-CMP-02 | Semântica incompatível → `INCOMPATIBLE`/explicação citada, nunca paridade fabricada | `TARGET` |
| RQ-CMP-03 | `INSUFFICIENT_EVIDENCE` default para pares não classificados | `TARGET` |
| RQ-SEC-01 | AuthZ sobre todos os sujeitos, fail-closed, sem vazamento de existência | `TARGET` |
| RQ-CLARA-01 | `read(report.*)`/`analyze(report_comparison)` no dispatcher semântico, sem tools planas | `TARGET` |
| RQ-CLARA-02 | Fichas R01–R15 citáveis e classificadas por evidência | `TARGET` — D-06 |
| RQ-EXP-01 | Export comparação exportável, bounded, com watermark/proveniência | `TARGET` — D-07 |

Testes previstos (todos `TEST_NOT_RUN`): contratos (400/401/403/503/504), grão/seleção R10 (353, Σ169.704,12 vs artefato), R11 (11/11, Σ97.462,71, custo1=0), ranking sobre conjunto autorizado completo, comparação `DIRECTLY_COMPARABLE` (R06 multi-período), `INCOMPATIBLE` (R12×R15), `INSUFFICIENT_EVIDENCE` (par novo), fail-closed multi-branch, paridade Portal×CLARA, citação de ficha, corpus stale→rejeitar publicação.

## 11. D8 — Plano de implementação (TARGET, não autorizado)

`E1` contratos R10/R11 (fechar D-01/D-02) → `E2` api-delpi (reuso `vw_fin_despesas`/SD2 repo) → `E3` BFF proxies+AuthZ → `E4` MFE páginas `@delpi/plugin-ui` → `E5` owner/contrato comparação (D-03/D-04) → `E6` CLARA registry semântico → `E7` fichas R01–R15 → `E8` corpus+Help → `E9` paridade Portal×CLARA × fontes → `E10` deploy governado+rollback (imagem anterior registrada).

## 12. D9 — Decisões materiais pendentes

| # | Decisão | Status | Recomendação (não aplicada) |
|---|---|---|---|
| D-01 | Classificação Direto/Ind/Adm: manual, híbrida ou automática? fonte homologada? | `DECISION_REQUIRED` | Persistir classe manual governada (roster editável com auditoria); `UNCLASSIFIED` legítimo até fonte automática provada |
| D-02 | "Desconsiderar" = conferência informativa, orientação de fechamento ou exclusão governada? afeta numerador/denominador/DRE? vigência/aprovação? | `DECISION_REQUIRED` | Começar como roster informativo recalculado por predicado (9035∩594∩filial∩mês) + metadado de propósito documentado; exclusão governada = gate próprio com migration |
| D-03 | Owner da comparação: BFF Controladoria, serviço compartilhado ou outra autoridade? | `DECISION_REQUIRED` | **BFF `controllership-finance-api`** — já é o orquestrador AuthZ/gateway de todos os contratos dos relatórios; api-delpi continua dona dos cálculos |
| D-04 | Comparação = operação transversal dedicada ou composição de contratos? | `DECISION_REQUIRED` | Operação dedicada `POST /analysis/report-comparison` + `analyze(report_comparison)` — composição pura não consegue garantir cardinalidade, `INCOMPATIBLE` e `PARTIAL` honestos |
| D-05 | Normalizações admitidas | `DECISION_REQUIRED` | Lista branca: agregação por período/filial/grão comum, diff absoluto/% com mesma medida, comparação de quantidade quando `value` não é comparável; **proibido** normalizar sinal/moeda/eixo de data sem flag explícita |
| D-06 | Fichas CLARA: estrutura/versionamento/publicação | `DECISION_REQUIRED` | Um doc canônico `fichas-relatorios-r01-r15.md` + entries manifest por rid; atualização obrigatória em todo gate que tocar relatório |
| D-07 | Exports: CSV/PDF, comparação exportável, limites | `DECISION_REQUIRED` | CSV sempre; PDF para comparação com watermark `INCOMPLETO/NÃO-HOMOLOGADO`; export comparação ≤ 6 sujeitos |
| D-08 | Dados parcialmente disponíveis | `DECISION_REQUIRED` | `PARTIAL` + `subject_error` explícito + nunca preencher ausente com zero; UI/CLARA declaram lacuna |

## 13. Limites declarados

Zero runtime/migration/deploy/corpus — `TARGET` ≠ implementado; `TEST_NOT_RUN` para todos os testes previstos; smoke autenticado R10/R11 impossível sem identidade `controllership-finance.access` (não concedida artificialmente). Artefatos `CC matriz.xlsb`/`NF a desconsiderar.xlsb` são privados — evidências citadas por reconciliação já publicada (docs 84/85/118), não por novo acesso ao arquivo. Producers `EDAPP` comprovados pela reconciliação física; **não** se assume que qualquer view de nome semelhante é o produtor (BR-R10-007/BR-R11-006 provam a diferença de seleção).
