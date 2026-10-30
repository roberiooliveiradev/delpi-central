# Gate Contratual — R10 Centro de Custo + R11 NF a Desconsiderar + Comparação Universal (CLARA)

**Gate:** `CF-PROC0072-R10-R11-CLARA-COMPARISON-CONTRACT-GATE-019` +
`CF-PROC0072-R10-R11-DECISION-EVIDENCE-GATE-020` (30/10/2026 — decisões
formalizadas pelo PO, evidências de vídeo/artefatos verificadas, catálogo
de divergências e contratos revisados na **Parte II, §14–§19**).
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

> **Superseded pelo gate-020 (30/10/2026):** D-01..D-08 foram formalizadas
> pelo PO — registro canônico em **§14**. A tabela abaixo permanece como
> histórico da rodada gate-019.

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

---

# PARTE II — DECISION-EVIDENCE-GATE-020 (30/10/2026)

Execução `CF-PROC0072-R10-R11-DECISION-EVIDENCE-GATE-020` — mesma natureza
documental do gate-019 (zero runtime/migration/deploy/corpus). Base: HEAD
`d63ef89e69`. Artefatos e vídeo verificados **diretamente** no acervo
autorizado do PO (arquivos privados — somente estrutura/contagens são
citadas; nenhum valor de linha, documento fiscal ou identificador
reproduzido).

## 14. Decisões D-01..D-08 — formalizadas pelo PO (30/10/2026)

Fonte: instrução direta do PO na sessão gate-020 (`APPROVED` = decisão
explícita; `APPROVED_WITH_EVIDENCE_GATE` = decisão com ponto ainda
condicionado à evidência documentada abaixo).

| # | Decisão | Estado | Registro |
|---|---|---|---|
| D-01 | R10 classificação/divergências | `APPROVED_WITH_EVIDENCE_GATE` | Classificação Direto/Ind/Adm **não** está registrada no Protheus de forma suficiente. Objetivo do relatório: **evidenciar lançamentos candidatos a divergência** (ex.: matéria-prima em CC administrativo), não classificar automaticamente. Preservar `UNCLASSIFIED` quando não comprovado; expor documento/referências para ajuste no Protheus; **não** corrigir cadastro/lançamento; **não** inventar regra automática; **não** criar tabela de classificação manual sem inventário+gate próprio |
| D-02 | R11 finalidade | `APPROVED_WITH_EVIDENCE_GATE` | R11 identifica possíveis divergências de NFs que devem ser **desconsideradas de uma determinada análise** ou receber tratamento corretivo no Protheus. Sem exclusão automática de relatórios; sem ajuste fiscal/contábil/estoque. Apuração exata e correção demonstrada: ponto condicionado à evidência (§15 — **não comprovado como vídeo**) |
| D-03 | Owner da comparação | **`APPROVED`** | **`controllership-finance-api`** — orquestração governada; cálculos continuam nos owners dos relatórios |
| D-04 | Capacidade de comparação | **`APPROVED`** | Operação governada reutilizável consumida pela CLARA via superfície MCP semântica (`analyze`), prioritariamente capacidade da CLARA via BFF. **Sem** tela genérica de comparação no Portal neste ciclo; sem novas tools MCP planas |
| D-05 | Compatibilidade semântica | **`APPROVED`** | Três resultados funcionais: `COMPARABLE`, `RELATED_REQUIRES_EXPLANATION`, `NOT_COMPARABLE` — classificações técnicas do §7 preservadas como refinamento; sem paridade por nome de coluna |
| D-06 | Conhecimento CLARA | **`APPROVED`** | Fichas técnicas R01–R15 versionadas, com evidência e citações, alimentando explicações FACT/POSSIBLE_DIVERGENCE/RECOMMENDATION/INSUFFICIENT_EVIDENCE (§18) |
| D-07 | Exportações comparativas | **`APPROVED` (negativa)** | **Não** implementar exportação de comparações nem tela de comparação neste ciclo; exports individuais CSV/PDF dos relatórios preservados |
| D-08 | Dados parciais | **`APPROVED`** | Apresentar resultados válidos autorizados + declarar explicitamente o que faltou/falhou/o que ainda é concluível; nunca zero implícito; `PARTIAL` nunca contorna acesso negado — fail-closed |

## 15. Etapa 2 — Evidência do vídeo (verificação direta de frames)

**Fonte localizada:** `Acompanhamento do Processo do Fechamento Mensal de
Estoques e Custos-20260930_143151-Gravação de Reunião (1) (1).mp4` — duração
**54:44**, 1920×1080, no acervo autorizado do PO. `SOURCE_AVAILABLE`.
Método: contact-sheets 1 frame/min (vídeo todo) + 1 frame/15–20s nos
segmentos 39:00–44:40 e 44:28–54:44 + frames full-res em 47:48, 50:10,
50:35. Áudio **não transcrito** (sem ferramenta); falas seguem via
transcrição guiada do PO no doc 56 — `OWNER_REPORTED_VIA_PO`, não prova de
execução.

### 15.1 Matriz vídeo × documentação

| Trecho | Conteúdo confirmado em frame | Confronto | Classe |
|---|---|---|---|
| 44:28–47:48 (Reg 17) | Tela genérica TOTVS (EDAPP), planilha `SCAGQGA0.XML`/`SD1`, filtros e ordenação | doc 56 Reg 17 + doc 85 BR-R10-001/002 + artefato 353 linhas | **`CONFIRMED_BY_VIDEO_AND_DOC`** |
| 47:48–54:44 (Reg 18) | Edição manual da coluna de classificação (coluna sem título entre `C Custo` e `C Contabil`), linhas percorridas uma a uma | doc 56 Reg 18 + artefato `col13`∈{Direto,direto,Indireto,Adm} em **353/353** linhas | **`CONFIRMED_BY_VIDEO_AND_DOC`** |
| ~50:10 | Narrado: lançamentos no CC `0404` que "não correspondem" | artefato: **4 linhas** com `D1_CC='0404'` (3 Indireto + 1 Direto) | `CONFIRMED_BY_VIDEO_AND_DOC` (existência) / `OWNER_REPORTED_VIA_PO` (incorreção) |
| ~50:35 | Frame full-res: linha destacada com `C Cust=0401`, produto tipo `MC` — narrado "centro inexistente/inválido, produto tipo cabo singelo deveria ir ao `CT`" | artefato: **exatamente 1 linha** com `D1_CC='0401'`, `Tipo Produto='MC'` | **`CONFIRMED_BY_VIDEO_AND_DOC`** |
| Produto não reconhecido (`PRODUTO-EXEMPLO-B`) | Narrado: analista precisa consultar cadastro TOTVS | doc 56 Reg 18 | `OWNER_REPORTED_VIA_PO` — classificação permanece pendente |
| Prefixos de CC (`02`→Adm, `03`/`0405`/`0504`→Ind, `05`→Adm-exemplo) | Narrado | CCs do artefato coerentes com a taxonomia observada, mas sem catálogo homologado | `OWNER_REPORTED_VIA_PO_TO_VALIDATE` — **não** vira regra automática |
| **R11 — demonstração do «desconsiderar»** | **Não encontrada**: varredura completa (54:44) não mostra tela SD2/roster/artefato `NF a desconsiderar.xlsb`; segmento 39:00–44:40 = app de extratos + câmeras; doc 117 já registrara "uso no vídeo não demonstrado" | **contra** a afirmação do prompt do PO ("a analista demonstra no vídeo") | **`INSUFFICIENT_EVIDENCE`** — alegação do PO pode referir-se a outra gravação; `PENDING_EVIDENCE` até confirmação |

### 15.2 Consequência para D-02

O exemplo concreto de R11 no vídeo é `PENDING_EVIDENCE`. A finalidade do
«desconsiderar» permanece o que a decisão do PO estabelece (análise/
correção pontual, não exclusão automática) + o que o artefato prova
(roster investigativo SD2 9035∩594). A **apuração exata** que recebe a
desconsideração e a **ação corretiva** no ERP continuam `TO_INVENTORY` —
perguntar ao owner ou localizar a gravação correta antes de fechar
`affected_calculation` no contrato.

## 16. Etapa 3 — Catálogo de divergências R10/R11

Modelo de regra: `rule_id`, relatório, descrição, campos de entrada,
predicado, exclusões, grão, evidência, severidade (somente se aprovada),
explicação ao usuário, referência documental, dados para localização no
ERP, ação de conferência documentada, estado, testes previstos. Toda regra
produz `POSSIBLE_DIVERGENCE` — **nunca** `CONFIRMED_ERROR` automático.

### 16.1 R10 — regras candidatas

| rule_id | Descrição | Predicado (atributos SD1/CTT) | Evidência | Estado |
|---|---|---|---|---|
| DV-R10-01 | Matéria-prima em CC administrativo | `D1_TP='MP'` (ou tipo da linha) ∩ `D1_CC` em conjunto adm homologado — executável **antes** da exclusão MP da seleção, como flag investigativa | Decisão PO (D-01) + BR-R10-004 | `TARGET` — requer catálogo CC→categoria (E10) |
| DV-R10-02 | Lançamento em CC inexistente/inválido | `D1_CC` ∉ cadastro CTT vigente (join catálogo) — **exige consulta CTT**, hoje `TO_INVENTORY` na api-delpi | Vídeo 50:35 (`0401`) + artefato 1 linha | `TARGET` — CTT `TO_INVENTORY` |
| DV-R10-03 | Produto em CC semanticamente incompatível | coerência produto×CC (ex.: item produtivo em CC não-produtivo — caso `0404`/cabo→`CT`) | Vídeo 50:10 + artefato 4 linhas | `TARGET` — requer catálogo homologado; **não** inferir por prefixo sem owner |
| DV-R10-04 | Despesa sem centro de custo | `D1_CC=''` entre tipos de entrada de despesa | artefato: **5 linhas** sem CC na seleção final | `TARGET` — predicado direto |
| DV-R10-05 | Despesa sem classificação comprovada | linha sem classe homologada → `UNCLASSIFIED` | D-01 + BR-R10-006 | `TARGET` — estado, não regra |
| DV-R10-06 | Classificação divergente do esperado | classe informada ≠ classe sugerida por catálogo homologado | doc 56 Reg 18 (estados `unreviewed/suggested/confirmed/…` = `TARGET_DECISION_REQUIRED`) | `TARGET` — bloqueado por E10 |

### 16.2 R11 — regras candidatas

| rule_id | Descrição | Predicado | Evidência | Estado |
|---|---|---|---|---|
| DV-R11-01 | Candidata ao roster investigativo | `D2_GRUPO='9035'` ∩ `D2_TES='594'` ∩ `D2_EMISSAO`∈competência ∩ filial | `PROVEN` (doc 84 §5.5: 11/11, Σ97.462,71) | `TARGET` (predicado confirmado para set/2026; generalização → E11) |
| DV-R11-02 | Faturamento sem custo estrutural | `D2_TES` com `F4_ESTOQUE='N'` → `D2_CUSTO1=0` — **esperado**, explica ausência no CPV | `PROVEN` (BR-R11-003/005) | `TARGET` — regra explicativa, não alerta |
| DV-R11-03 | NF 594 sem item-irmão físico (TES 510) | documento com item 594 mas sem item `F4_ESTOQUE='S'` no mesmo `D2_DOC` | artefato: 3/11 NFs sem par 510 | `TARGET` — join mesmo documento |
| DV-R11-04 | Fora do predicado mas relacionada | `D2_GRUPO='9035'` com TES≠594 (511/505/610…) ou TES 594 em outro grupo | doc 85 BR-R11-002 (all-time 9035 com outros TES) | `TARGET` — revisão humana, não inclusão automática |

### 16.3 Modelo de resultado (`TARGET_CONTRACT`)

```json
{ "reportId":"R10", "findingId":"…", "ruleId":"DV-R10-02",
  "status":"POSSIBLE_DIVERGENCE", "period":"2026-09", "branch":"01",
  "sourceRecord":{"document":"…","series":"…","item":"…",
    "productCode":"…","productType":"…","costCenterCode":"…",
    "accountCode":"…","tes":"…","cf":"…","supplierCode":"…","store":"…",
    "entryDate":"…","issueDate":"…","quantity":0,"totalValue":0},
  "observedValues":{}, "expectedValues":{},
  "findingExplanation":"…", "evidenceRefs":["doc-85#BR-R10-001"],
  "erpReviewGuidance":"conferir cadastro CTT e o documento SD1 no Protheus",
  "provenance":{}, "classification":"TARGET" }
```

Estados de visão da listagem: `ALL_RECORDS` | `POSSIBLE_DIVERGENCES` |
`UNCLASSIFIED` — candidatos contratuais; `REVIEWED`/`excluded_from_analysis`
só existem se persistência governada for autorizada em gate próprio
(D-01 proíbe tabela nova por preferência arquitetural).

## 17. Etapa 4 — Contratos TARGET revisados

### R10 — `GET /controllership/cost-center-expenses` (revisado)

Request acrescenta: `view`∈{`all`,`divergences`,`unclassified`},
`include_findings=true`, `cost_class`, `cc`, `product`, `doc`, `supplier`,
`tes`, `cf`. Response: `items[]` do §5 + `findings[]` (modelo §16.3) +
`summary{totalValue, lineCount, byCostCenter, byCostClass?,
divergenceCount, unclassifiedCount}` + `selection`/`provenance` + estados
de visão. `erpReviewGuidance` sempre que `POSSIBLE_DIVERGENCE`. Ranking
continua sobre o conjunto autorizado completo.

### R11 — `GET /controllership/billing-exclusion-roster` (revisado)

Request: `period`, `branch`, `group`, `tes`, `doc`, `supplier`,
`view`∈{`all`,`candidates`,`out_of_criteria`}, `include_findings`.
Response: `roster[]`{doc, serieOrig, numSerie, item, produto+desc, tes, cf,
grupo, quant, prcven, total, loja, cContabil, armazem, custo1,
hasSiblingCostItem, reason?, affectedCalculation?} + `findings[]` +
`summary` + `provenance`. `affectedCalculation` ∈ {`BILLING_CONFERENCE`,
`CPV`,`ROL`,`DRE`} — **`TO_INVENTORY` até confirmação do owner** (§15.2);
`reason` permanece `TARGET` sem persistência de revisão.

### Comparação — `POST /analysis/report-comparison` (owner aprovado)

Owner: **`controllership-finance-api`** (D-03). Capability CLARA:
`analyze(report_comparison)` via `ANALYZE_ACTIONS` — **nenhuma tool
plana** (D-04). Resultados funcionais D-05: `COMPARABLE` |
`RELATED_REQUIRES_EXPLANATION` | `NOT_COMPARABLE`, com `reason`+citação
obrigatórias quando ≠`COMPARABLE`. Partial honesty D-08: `subjects[]`
individuais com `status` próprio; `PARTIAL` declara lacuna, nunca
preencher. Sem tela genérica e sem export comparativo (D-04/D-07).

## 18. Etapa 5 — Fichas R01–R15 + plano de ingestão CLARA

**Esquema canônico de ficha** (um doc governado por relatório ou seções em
doc único — recomendado: `docs/12-roadmap-e-evolucao/controllership-finance/
fichas/RXX-ficha.md`, entrada no `corpus_manifest` com `related_report_ids`):

```yaml
identity: {id:R10, name, purpose, business_owner, technical_owner, producer}
source:   {api, tables, artifacts, docs, source_version, provenance}
rules:    {selection, filters, formulas, classifications, inclusions,
           exclusions, signs, dates, grain, monetary_precision}
operation:{how_used, divergences_detectable[], erp_review_guidance,
           erp_actions_by_user[], non_automatable[]}
comparison:{related_reports[], comparable_measures[], related_measures[],
           incompatible_measures[], allowed_normalizations[]}
governance:{evidence[], impl_status, parity_status, limitations,
           pendings, version, citations[]}
```

Cada afirmação carrega `PROVEN|TO_INVENTORY|PLANNED|TARGET` + locator
(doc §, arquivo, contrato, SHA). **Ingestão (preparar, não executar):**
atualizar `corpus_manifest` por ficha → ingestão local → verificar
`get_catalog`/`list_knowledge_sources` + busca citável → Help → versão de
corpus → publish governado — **sem ingestão produtiva neste gate**.

## 19. Decisões residuais e próximo ciclo

| # | Pendência | Estado |
|---|---|---|
| E10a | Catálogo homologado CC→categoria (adm/ind/dir) + exceções (prefixos 02/03/05/0405/0504/`CT-*`) | `DECISION_REQUIRED` — owner Controladoria |
| E10b | Persistência de revisão/classificação (tabela+audit) | `DECISION_REQUIRED` — gate próprio se necessário (D-01) |
| E11a | Apuração consumidora do «desconsiderar» + ação corretiva no ERP | `TO_INVENTORY`/`PENDING_EVIDENCE` — possível gravação alternativa (§15.1) |
| E11b | Predicado oficial roster (grupo 9035 vs TES 594 vs ambos) | `TO_INVENTORY` |
| CTT | Consulta/catálogo de centros de custo vigentes na api-delpi | `TO_INVENTORY` — requer DV-R10-02 |
| LISTA-13 | Confirmação formal lista 12-vs-13 TES excluídos | `PENDING` (herdado) |
| TEST | Toda a suíte prevista (doc 23 §gate-020) | `TEST_NOT_RUN` |

**Sequência do próximo ciclo (não autorizada):** E1 contratos aprovados →
E2 api-delpi (SD1/SD2/CTT) → E3 BFF proxies + `analysis/report-comparison`
→ E4 MFE páginas R10/R11 com findings → E6 CLARA `analyze(report_comparison)`
+ `read` R10/R11 → E7 fichas → E8 corpus/Help → E9 paridade → E10 deploy.

## 20. Status pós-stage-01 (2026-10-31) — contrato R10 `IMPLEMENTED`

Execução `CF-PROC0072-R10-IMPLEMENTATION-STAGE-01` (doc 127 Etapa 1).
Divergências entre o alvo do §17 e o contrato entregue — registradas, não
silenciadas:

| Aspecto | TARGET (§17) | Entregue (stage-01) | Nota |
|---|---|---|---|
| Rota produtor | `GET /controllership/cost-center-expenses` | `GET /financeiro/cost-center-expenses` (+`/export`) na api-delpi | prefixo `/financeiro` = padrão vigente do domínio no repo (não `/controllership`) |
| Rota BFF | — | `GET /closing/cost-center-expenses` (+`/export`) | mesma família dos proxies `closing/*` |
| CLARA | `read(report.cost_center_expenses)` | idem — registrado em `READ_ACTIONS`; handler chama a mesma rota BFF | paridade por reúso de rota |
| `universe` | `view` único | `universe`∈{`calculation`,`investigation`} **+** `view`∈{`all`,`divergences`,`unclassified`} | separação explícita dos dois universos (gate 2 do plano) |
| Findings | DV-R10-01..06 | executados DV-R10-01/02/04; `costClass=UNCLASSIFIED` (D-01); DV-R10-03/06 declaradas `implemented:false` + `pendingReason` (E10a) | findings sempre `POSSIBLE_DIVERGENCE` |
| CTT | `TO_INVENTORY` | `TOP 1 OUTER APPLY` CTT010 (filial específica → fallback filial-branca) | snapshot vigente; **não** comprova validade histórica |
| Paridade | 353 linhas / R$ 169.704,12 | **reproduzida ao vivo** no TOTVS: 353 / R$ 169.704,12 / 139 docs / 46 buckets CC (45 + grupo sem-CC) | `PROVEN` para 2026-09 f01 |

E10a, E10b, E11a, E11b, LISTA-13 e G6 permanecem `PENDING`/`DECISION_REQUIRED` conforme §19.

## 21. Status pós-stage-02 (2026-10-31) — contrato R11 `IMPLEMENTED`

Execução `CF-PROC0072-R11-IMPLEMENTATION-STAGE-02` (doc 127 Etapa 2).
Divergências entre o alvo do §17 e o contrato entregue — registradas, não
silenciadas:

| Aspecto | TARGET (§17) | Entregue (stage-02) | Nota |
|---|---|---|---|
| Rota produtor | `GET /controllership/billing-exclusion-roster` | `GET /financeiro/billing-exclusion-roster` (+`/export`) na api-delpi | prefixo `/financeiro` = padrão vigente do domínio no repo |
| Rota BFF | — | `GET /closing/billing-exclusion-roster` (+`/export`) | mesma família dos proxies `closing/*` |
| CLARA | `read(report.billing_exclusion_roster)` | idem — registrado em `READ_ACTIONS`; handler chama a mesma rota BFF | paridade por reúso de rota |
| `view` | roster único | `view`∈{`candidates`,`out_of_criteria`,`all`} | separação explícita das duas populações; totais nunca somados |
| Findings | DV-R11-01..04 | DV-R11-03 executado como `POSSIBLE_DIVERGENCE`; DV-R11-01 exposta como `selection`; DV-R11-02 como `costStatus=structural_zero_expected` (explicação); DV-R11-04 como visão `out_of_criteria` | nunca `CONFIRMED_ERROR` |
| `affectedCalculation` | `TO_INVENTORY` até owner | `TO_INVENTORY` + `correctiveAction=PENDING_EVIDENCE` em `selection`/`provenance` | E11a preservado honesto — nenhuma exclusão automática (D-02) |
| Paridade | 11 linhas / R$ 97.462,71 | **reproduzida ao vivo** no TOTVS via o próprio engine (`build_lines_query`): 11 / R$ 97.462,71 / 11 docs / 3 docs sem item-irmão (103033, 103199, 103202) | `PROVEN` para 2026-09 f01 |
| Export | CSV/PDF individual | entregue — mesmo engine; cabeçalho declara competência/filial/visão/critério observado/caráter investigativo/fonte/hash/paridade | documento operacional, não emissão oficial |

E11a e E11b **permanecem** `PENDING`/`DECISION_REQUIRED` conforme §4 e §19 — o relatório expõe a seleção como evidência histórica e a orientação limita-se a localizar/conferir o lançamento no Protheus; o predicado não foi publicado como regra oficial universal. G6 (homologação humana) e smoke produtivo `PENDING`.

## 22. Status pós-stage-03 (2026-10-31) — comparação transversal `IMPLEMENTED`

Execução `CF-PROC0072-CLARA-REPORT-COMPARISON-IMPLEMENTATION-STAGE-03`
(doc 127 Etapa 3). O contrato de comparação definido neste documento
passou de TARGET para `IMPLEMENTED` na `controllership-finance-api`.

Divergências entre o alvo contratual e o entregue — registradas, não
silenciadas:

| Aspecto | TARGET (§B/§§6-8) | Entregue (stage-03) | Nota |
|---|---|---|---|
| Endpoint | `POST /analysis/report-comparison` | `POST /closing/analysis/report-comparison` | prefixo `/closing` = padrão vigente do roteador BFF (mesma família de `/closing/analytics/stock-reconciliation`) |
| Sujeitos | 2–6 | 2–6 (Pydantic `min_length=2, max_length=6`) | conforme |
| Tipos | PERIOD/BRANCH/REPORT/DOCUMENT/TREND/EXPLAIN | idem — único contrato compartilhado | PERIOD/BRANCH/TREND exigem mesmo `reportId` + `measure` |
| Compatibilidade | COMPARABLE / RELATED_REQUIRES_EXPLANATION / NOT_COMPARABLE (+INSUFFICIENT_EVIDENCE default) | idem — matriz curada em `domain/report_comparison/compatibility.py`; par não listado → `INSUFFICIENT_EVIDENCE` | nenhuma compatibilidade inferida por nome de coluna |
| Normalizações | somente §D4 | delta absoluto + percentual (denominador não nulo) somente sob `numeric_delta_allowed`; grãos usam apenas agregações completas do produtor (top-N excluídos) | `normalizations[]` declara cada regra |
| Partial honesty | PARTIAL honesto | `subjects[].status` ∈ ok/empty/unavailable/denied/unsupported + `missingData[]` + `baseline_shifted` + `subjectTruncated` | nenhum zero implícito; `EMPTY` ≠ zero |
| AuthZ | por sujeito, fail-closed | upstream 401/403 → `denied` sem valor/existência; S2S + Bearer delegado idêntico às rotas do Portal; sem permission nova | `security.subjectsDenied` contado |
| Limites | bounded | sujeito 30s; diffs ≤500 paginados (`diffTruncated`); documentos ≤1000/sujeito (200×5 páginas) | resposta declara `limits{}` |
| R10 universos | nunca misturar | `calculation`×`investigation` → NOT_COMPARABLE `r10_universe_mismatch` | invariante preservado |
| R10×R11 | chave confiável | kind=DOCUMENT cruza `branchCode+document+series`; itens sem chave completa → `incompleteKeys`; nota de eixo `D1_DTDIGIT`×`D2_EMISSAO` por match | nunca só número de documento |
| CLARA | `analyze(report_comparison)` | registrado em `ANALYZE_ACTIONS`; handler chama a mesma rota BFF (`_call_route`) | superfície segue com 6 tools |
| Escopo | sem tela genérica, sem export, sem corpus | confirmado — nada disso foi criado | Etapa 4 intacta |

Capacidades realmente suportadas nesta etapa (contratos implementados):
R01, R02, R03, R05, R06, R07, R08, R10, R11, CPV.
R04/R09/R12/R15 respondem `report_not_implemented`; R13/R14 são evidência
externa; ids desconhecidos → `unknown_report`. Pares sem regra na matriz
→ `INSUFFICIENT_EVIDENCE` — o endpoint ser genérico **não** significa
cobertura universal efetiva.

## 23. Status pós-stage-04 (2026-10-31) — D-06 conhecimento `IMPLEMENTED`

Execução `CF-PROC0072-CLARA-KNOWLEDGE-R01-R15-IMPLEMENTATION-STAGE-04`
(doc 127 Etapa 4). A decisão **D-06** (fichas CLARA: estrutura,
versionamento, publicação) passou de `APPROVED` para **`IMPLEMENTED`**:

| Item da decisão | Entregue |
|---|---|
| Fichas R01–R15 versionadas | `fichas/R01..R15-ficha.md` no esquema canônico §18 — identidade/fonte/regras/interpretação/operação/comparação/governança com `PROVEN\|TO_INVENTORY\|PLANNED\|TARGET` por afirmação |
| Entrada no `corpus_manifest` com `related_report_ids` | 17 `SourceSpec` (`ficha-index`, `ficha-processo`, `ficha-r01..r15`) — inventário explícito, classificação do vocabulário canônico |
| Explicações FACT/POSSIBLE_DIVERGENCE/RECOMMENDATION/INSUFFICIENT_EVIDENCE | fichas explicitam FACT provado × hipótese pendente por seção; pares não curados seguem `INSUFFICIENT_EVIDENCE` |
| Ingestão/publish | pipeline vigente executado no ambiente local (corpus `f9857be6`, 88 fontes/2.170 itens; rollback `57109de5`); **publicação produtiva `PENDING_APPROVAL`** — gate separado, conforme §9.2 |
| Atualização obrigatória por gate | registrado como regra permanente das fichas (README do diretório) |
