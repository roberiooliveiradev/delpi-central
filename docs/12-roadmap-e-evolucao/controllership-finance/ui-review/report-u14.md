# Report U14 — acabamento visual e CLARA fora do Portal

Data: 2026-11-15. HEAD de código no fecho F5: `c78d4a51d9`. PROD runtime no deploy: `c0891eb1a5` (inclui F5 + commits concorrentes posteriores). Tags de rollback F2–F5: `rollback-ui-review-u14-controllership-finance-api`, `rollback-ui-review-u14-controllership-finance`. Tag F1 isolada: `rollback-ui-review-u14-f1-controllership-finance`.

## Fases

| Fase | SHA | Verifier | Deploy |
|---|---|---|---|
| F0 | `8553acecab` | n/a (rebaseline) | Screenshots «antes» `/tmp/ui-review-u14-f0` |
| F1 | `ea31b4a1e8` | ACCEPT_WITH_RESIDUAL (r1) | HML → PROD |
| F2 | `fb81da0a96` | ACCEPT_WITH_RESIDUAL (r1) | HML |
| F3 | `88f10f1e0b` | ACCEPT_WITH_RESIDUAL (r2; r1 REWORK AC-KPI-4) | HML |
| F4 | `92d25b1385` | ACCEPT_WITH_RESIDUAL (r3; r1/r2 REWORK) | HML |
| F5 | `c78d4a51d9` | ACCEPT_WITH_RESIDUAL (r1) | HML → PROD BFF→MFE |

## Verificador — tabela de rodadas (veredito sem edição)

| Fase | Rodada | Veredito | OCs |
|---|---|---|---|
| F1 | 1 | ACCEPT_WITH_RESIDUAL | nenhum |
| F2 | 1 | ACCEPT_WITH_RESIDUAL | nenhum |
| F3 | 1 | REWORK | OC: AC-KPI-4 ordem NF-e/CT-e (`DOCUMENT_TYPE_ORDER`) |
| F3 | 2 | ACCEPT_WITH_RESIDUAL | OC r1 corrigida |
| F4 | 1 | REWORK | OC: alinhamento série `previous` esparsa |
| F4 | 2 | REWORK | OC: header `Status` em ProductionOrderConsumptionPage; residual barras vs área |
| F4 | 3 | ACCEPT_WITH_RESIDUAL | OCs r1/r2 fechadas; residual AC-GRA-3 (área linear do kit) |
| F5 | 1 | ACCEPT_WITH_RESIDUAL | nenhum (CSS morto `.cf-analysis-clara-actions` removido no commit) |

### F5 — veredito integral (sem edição)

```text
veredito: ACCEPT_WITH_RESIDUAL
rodada: 1
escalar: NAO
escopo: working tree @ bcf231d7cd
contrato: PRESENTE
independencia: OK (verificador: SWE-2 High; executor: Composer)
registro: OK

## Resumo
Pedido: remover da feature entry-audit do MFE controllership-finance todo convite à CLARA (card «Pergunte à CLARA», botão «Copiar pergunta», bloco «Sugestão da CLARA», clara_suggestion do tipo, CF_HELP.entryAudit.clara), criar teste de ausência e documentar no README a dependência realKit↔plugin-ui, mantendo ClaraConsentPage/MCP intactos. Entregue exatamente isso nos 7 arquivos alegados; remoções confirmadas por diff e grep residual limpo; suíte src/features/entry-audit reproduzida com 9 arquivos/28 testes verdes. Resíduos não bloqueantes: seletor CSS .cf-analysis-clara-actions ficou morto e erros de tsc pré-existentes em arquivos fora do escopo.
```

## Por fase — o que mudou

### F0
Rebaseline ≥`8ec4e602`; suítes MFE/BFF; defeito «Limpar seleção» reproduzido em HML; screenshots «antes» 1440/1024/390 fora do git.

### F1 — RQ-U14-SEL (MFE)
`onSelect(null)` limpa filtro; segundo clique limpa; «Limpar filtros»; testes de seleção. HML + PROD com tag F1.

### F2 — RQ-U14-BFF + AC-SEL-3
Sort `branches`/`document_types`; `breakdowns.tes[].label` (SF4); cada dimensão de breakdown sem o próprio filtro; README §6; MFE não aplica o filtro da própria dimensão no gráfico de seleção. HML.

### F3 — RQ-U14-ENT + RQ-U14-KPI
Colunas ordenáveis + sentence case; uma moldura no hero; botão Executar na linha ≥1024; KPI monetário compacto; títulos nowrap; aviso «sem anterior» único; `formatAnalysisScope` com `DOCUMENT_TYPE_ORDER`; Exportar primary. HML.

### F4 — RQ-U14-GRA + RQ-U14-TAB
Sem quadrinhos SEM PAR/EXPLICADAS; Explicadas na legenda; alturas gauge/donut; série diária preenchida + previous alinhado; `smooth=false`; temas «Itens/Cabeçalho da nota»; contadores CT-e/TES; Situação; ellipsis; page_size 25. Residual: barras pedidas vs área linear do kit (V3 se plugin-ui). HML.

### F5 — RQ-U14-CLARA + AC-DOD-5
Removidos card/copy/sugestão CLARA, helpers, tipo `clara_suggestion`, ajuda e CSS morto; `ClaraConsentPage`/MCP intactos; teste `entryAuditClaraAbsence.test.ts`; README realKit. HML MFE; PROD BFF depois MFE. Bundle PROD: 0 ocorrências de «Pergunte à CLARA» / «Copiar pergunta para a CLARA» / «Sugestão da CLARA».

## TES (F2) — como a descrição chegou
`breakdowns.tes[].label` preenchido na BFF a partir do dado SF4 já presente na análise (sem consulta nova ao Protheus). MFE exibe `código · label` quando `label` existe.

## Tabela de ocorrências (F4) — largura 1440
Critério AC-TAB-3: Fornecedor/Regra com max-width + ellipsis; numéricos à direita; `defaultColumnVisibility`. Medição DOM «depois» em 1440 fica a cargo dos prints do owner (fora do git). Antes (review-3): tabela ~1856 px para ~1341 px de espaço.

## Critérios de aceite (review-3.md)

| AC | Status | Evidência |
|---|---|---|
| AC-SEL-1 | PASS | F1 + testes seleção; HML/PROD |
| AC-SEL-2 | PASS | F1 toggle null |
| AC-SEL-3 | PASS | F2 BFF + MFE own-dimension |
| AC-SEL-4 | PASS | F1 Limpar filtros |
| AC-SEL-5 | PASS | testes componente F1; Playwright HML na reprodução (fase F1) |
| AC-BFF-1 | PASS | sort whitelist F2 |
| AC-BFF-2 | PASS | TES label SF4 |
| AC-BFF-3 | PASS | breakdowns sem filtro próprio |
| AC-BFF-4 | PASS | README §6 + testes BFF |
| AC-ENT-1 | PASS | F3 sortable + sentenceHeadersWrap |
| AC-ENT-2 | PASS | F3 hero/grid |
| AC-ENT-3 | PASS | F3 toolbar nowrap ≥1024 |
| AC-KPI-1 | PASS | formatMoneyBRLForKpi |
| AC-KPI-2 | PASS | CSS nowrap títulos |
| AC-KPI-3 | PASS | aviso único |
| AC-KPI-4 | PASS | DOCUMENT_TYPE_ORDER (após OC F3) |
| AC-KPI-5 | PASS | Exportar primary |
| AC-GRA-1 | PASS | F4 |
| AC-GRA-2 | PASS | CSS altura (residual visual sem DOM) |
| AC-GRA-3 | ACCEPT_WITH_RESIDUAL | dias preenchidos + smooth=false; **barras** = residual kit (área linear) |
| AC-GRA-4 | PASS | TES label |
| AC-GRA-5 | PASS | THEME_LABELS |
| AC-TAB-1 | PASS | prefetch CT-e/TES |
| AC-TAB-2 | PASS | Situação (após OC F4 r3) |
| AC-TAB-3 | PASS código / INCONCLUSIVE visual 1440 | ellipsis no código; print owner |
| AC-TAB-4 | PASS | page_size 25 |
| AC-CLARA-1 | PASS | F5 |
| AC-CLARA-2 | PASS | F5 |
| AC-CLARA-3 | PASS | F5; ClaraConsentPage intacta |
| AC-CLARA-4 | PASS | entryAuditClaraAbsence.test.ts |
| AC-DOD-1 | INCONCLUSIVE parcial | «antes» F0; «depois» PROD — **pedir prints ao owner** |
| AC-DOD-2 | INCONCLUSIVE | axe U14 não reexecutado; herança U13 |
| AC-DOD-3 | PASS | suítes por fase verdes; ajuda no commit |
| AC-DOD-4 | PASS | verificador F1–F5 |
| AC-DOD-5 | PASS | README realKit |

## Parada

Deploy PROD F2–F5 concluído (BFF → MFE). **Owner:** enviar prints da entrada da Auditoria e de uma análise em PROD (1440 / 1024 / 390, claro e escuro) para fechar AC-DOD-1 e a evidência visual de AC-TAB-3 / AC-GRA-2.
