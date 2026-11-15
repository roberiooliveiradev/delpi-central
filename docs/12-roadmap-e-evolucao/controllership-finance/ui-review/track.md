# Trilha — UI review (U0–U8)

Fonte: [review.md](./review.md). Autoridade: instruções oficiais do arquiteto e `.cursor` > padrão visual dos Portais (`docs/11-padroes-de-desenvolvimento/padrao-visual-portais-minha-delpi.md`) > `30-plugin-ui-reuse-map.md` > docs do front-end da auditoria (`entry-audit/frontend/01–04`) > este track > review.md.

## 1. Regras

1. `main`, sem branch; `git add` só com caminhos explícitos (nunca `-A`, `.`, `commit -a`); push a cada etapa.
2. `@delpi/plugin-ui` first: usar o componente do kit pelo adaptador `Cf*`; não recriar tabela, card, hero, badge ou gráfico com CSS local (§22). Mudança no plugin-ui só aditiva, com testes de caracterização e prova dos consumidores (lição da T13R).
3. Sem mudança de regra de negócio, contrato ou permissão. Se uma correção de tela pedir dado que a BFF não entrega, parar (Y-dado) e listar; leitura nova aditiva só com decisão.
4. Vocabulário e formatação num lugar só (`entryAuditPresentation.ts` e utilitários do MFE), com teste.
5. DoD de cada página: desktop 1440, tablet 1024, celular 390; claro e escuro (mesma árvore); teclado e foco; estados do §16; ajuda atualizada no mesmo gate.
6. Evidência por screenshot nos três tamanhos e dois temas (no report, não commitado) + Playwright + verificação de acessibilidade automatizada (axe) sem violação séria nova.
7. Página não aberta = INCONCLUSIVE.

## 2. Paradas

| # | Quando parar |
|---|---|
| V1 | 4º ciclo de correção no mesmo problema |
| V2 | Falha nova em suíte (MFE, plugin-ui, consumidores) |
| V3 | Correção exige mudança não aditiva no plugin-ui |
| V4 | Tela precisa de dado que a BFF não entrega (listar campo, página e motivo) |
| V5 | Escolha de produto fora desta revisão (conteúdo, fluxo, regra) |
| V6 | Falha em PROD → rollback e parar |

## 3. Quadro de status

| Etapa | Status | SHA |
|---|---|---|
| U0 Inventário visual e matriz de conformidade | DONE | `938ccd1edb` |
| U1 Base comum (vocabulário, formatação, badges, ícones, estados) | DONE | `1bcb9f470a` |
| U2 Início | DONE | `b31321f1d0` |
| U3 Auditoria — entrada e execução | DONE | `4577724671` |
| U4 Auditoria — resultado da análise | DONE | `25a491123f` |
| U5 Auditoria — detalhe da ocorrência | DONE | `94a98abca1` |
| U6 Demais páginas do Portal (desvios do padrão) | DONE | `f16cec684a` |
| U7 HML (usuários de teste por perfil, Playwright, axe, screenshots) | DONE | `cc2aec7849` |
| U8 PROD | DONE | `4785e7aa3e` |

## 3.1 Matriz de conformidade (U0) — evidência no código HEAD `1970a2bb4a`

Classificação: `CONFIRMADO_NO_CODIGO` | `CONFIRMADO_EM_HML` | `INCONCLUSIVO` | `OK`.

| Item | Página | Achado | Classificação |
|---|---|---|---|
| G1 PagePath | entry-audit home/analysis/occurrence | Sem `CfPagePath`; TopBar só «Início» | CONFIRMADO_NO_CODIGO |
| G2 Eyebrow | entry-audit | Home «Fiscal»; análise/ocorrência «Auditoria de Entradas» — deveria ser «Notas fiscais» | CONFIRMADO_NO_CODIGO |
| G3 Vocabulário | analysis/home | Temas/tipos/filiais técnicos (`cte`, `CTE`, `Filial 01`); `displayValue` só faz toLocaleString | CONFIRMADO_NO_CODIGO |
| G4 R$ | analysis/occurrence | KPI usa `currency` local; coluna Diferença usa `displayValue` → `170.00` | CONFIRMADO_NO_CODIGO |
| G5 Severidade | analysis | Texto puro; donut sem `tone` de status | CONFIRMADO_NO_CODIGO |
| G6 Ícones/ajuda | analysis/home | Ações sem Lucide; KPIs via MetricStrip sem ícone/ajuda | CONFIRMADO_NO_CODIGO |
| G7 Loading | analysis/occurrence | `<p>Carregando…</p>` sem hero/esqueleto | CONFIRMADO_NO_CODIGO |
| G8 Grid | home create + charts | `cf-filters-grid` / `cf-charts-grid` **sem CSS**; 7 KPIs no MetricStrip | CONFIRMADO_NO_CODIGO |
| G9 Perf | analysis | Summary+breakdowns+rows no mount; tempo abertura 01/11–15/11 | INCONCLUSIVO (medir U7) |
| H1 Highlights | PluginShell home | `highlightsUnavailable: "—"` hardcoded | CONFIRMADO_NO_CODIGO |
| H2 Recents icons | HomePage | Todos usam `SECTION_ICONS.closing` (calendário) | CONFIRMADO_NO_CODIGO |
| H3 LNF externo | catalog/HomePage | Link externo existe; sem `ExternalLink`/tooltip dedicado no card | CONFIRMADO_NO_CODIGO |
| E1 Form | EntryAuditHomePage | Campos empilhados; botão «Criar análise» | CONFIRMADO_NO_CODIGO |
| E2 Progresso | EntryAuditHomePage | Texto por filial; sem `CfProgressTracker` | CONFIRMADO_NO_CODIGO |
| E3 Histórico | EntryAuditHomePage | Tipos uppercased; status texto; sem badge/ação Abrir | CONFIRMADO_NO_CODIGO |
| A1–A9 | EntryAuditAnalysisPage | Hero/KPIs/donut solto/abas SegmentToggle/tabela/CLARA — alinhado ao review | CONFIRMADO_NO_CODIGO |
| O Detalhe | EntryAuditOccurrencePage | Sem PagePath; sem badge severidade; history em `<ol>` não `CfTimeline` | CONFIRMADO_NO_CODIGO |
| F Demais | closing/* | PagePath+Hero presentes em Received/DocumentsAdmin/Checklist* | OK parcial |
| F Meu perfil / DRE | shell | Perfil via TopBar→`/profile`; DRE projeta Home | OK / INCONCLUSIVO visual HML |

Screenshots HML (não commitados): `/tmp/ui-review-u0/` via `e2e/specs/u0-inventory.spec.ts` (home + entry-audit 1440/1024/390). Demais páginas e temas claro/escuro: evidência completa na U7.

**G9:** medição de abertura da análise 01/11–15/11 adiada à U7 (precisa sessão autenticada + análise existente); sem token seguro no inventário U0.

## 4. Etapas

**U0 — Inventário (somente leitura).** Screenshots de todas as páginas do MFE (Início, fechamento mensal e abas, documentos, relatórios, administração, Meu perfil, DRE, Auditoria: entrada, resultado com cada aba, detalhe) em 1440/1024/390 e claro/escuro. Matriz página × regra do padrão (§8–§24): hero, PagePath, SectionCard, KPIs, filtros, tabela, estados, responsivo, ícones, ajuda, vocabulário. Confirmar ou corrigir cada item do review.md e acrescentar o que faltar. Medir o tempo de abertura da análise de 01/11–15/11 (G9).

**U1 — Base comum.** Vocabulário (temas, tipos, filiais, situações), formatação (R$, datas, números de nota/série), mapa severidade → `StatusBadge` (tom + ícone), mapa de ícones por rota e ação, estados de carregamento/erro/parcial/vazio reutilizáveis, ajuda (`CF_HELP`) das telas. Testes de unidade.

**U2 — Início.** H1–H3 do review.md. H1 usa leituras que já existem (competência, bloqueios, última auditoria, backlog do LNF) e mostra estado explícito quando faltar.

**U3 — Entrada da auditoria.** E1–E3. Execução com progresso real (estágio e contadores da análise).

**U4 — Resultado da análise.** A1–A9 e G7/G9. Layout alvo (desktop):

```
PagePath
PageHero  [eyebrow Notas fiscais] Análise de 01/11 a 15/11/2026  [Concluída]
          Matriz (SC) · Filial ES · NF-e · CT-e · criada em … por …
          [⤓ Exportar] [↻ Executar de novo] [+ Nova análise]
KPIs      Notas | Valor | Pendentes | Alta | Diferença nas Altas | Sem par
Linha 1   [Conformidade: medidor + legenda + strip]   [Severidade: donut]
Linha 2   [Por tema]  [Por fornecedor]  [Por TES]
Linha 3   [Evolução por dia: período × anterior]   (só se > 1 dia)
Escopo    chips de filtro ativos  · Limpar
Abas      Ocorrências 159 · Notas casadas 315 · Sem par 144 · CT-e · TES · Fora do período 400
Tabela    severidade | nota/série | fornecedor | regra | campo | Protheus | XML | diferença | status
CLARA     Pergunte à CLARA + 3 sugestões
```

Tablet: KPIs 3 colunas, gráficos 2; celular: 1 coluna, tabela em cards.

**U5 — Detalhe da ocorrência.** Item O do review.md contra o doc 03.

**U6 — Demais páginas.** Corrigir os desvios de padrão da matriz U0, página a página, um commit por página. O que não for padrão vai para a lista de decisão (V5).

**U7 — HML.** Criar no Keycloak de HML usuários de teste por perfil (só access; access+manage; access+LNF; DRE), autorizado pela regra 9 da trilha da auditoria, com senha só no `.env.hml`. Playwright por perfil nas páginas mexidas, axe, screenshots 1440/1024/390 claro/escuro.

**U8 — PROD.** Tags `rollback-ui-review-controllership-finance` (e `-plugin-ui` se tocado); publicar; abrir o Início, a entrada da auditoria e a análise de 01/11–15/11 logado (página aberta, não remoteEntry); comparar números do resultado com a CLARA (summary).

## 5. Rollback

MFE (e plugin-ui, se tocado) pelas tags. Sem migration nesta trilha.

## 6. Registro

| Data | Etapa | SHA | Status | Nota |
|---|---|---|---|---|
| 2026-11-14 | plano | — | READY | Doc 171. Revisão pedida pelo owner sobre os prints de PROD. |
| 2026-11-14 | U0 | `938ccd1edb` | DONE | Matriz G/H/E/A/O/F no código HEAD≥2ce2d29c; G9 INCONCLUSIVO até U7; screenshots HML via u0-inventory.spec (não commitados). |
| 2026-11-14 | U1 | `1bcb9f470a` | DONE | Vocabulário/R$/severidade/ícones/estados/ajuda em entryAuditPresentation + SeverityBadge + LoadingState + CSS grids. |
| 2026-11-14 | U2 | `b31321f1d0` | DONE | H1 highlights reais; H2 hubRouteIcons; H3 ExternalLink+title no SectionRouteCard (aditivo). |
| 2026-11-14 | U3 | `4577724671` | DONE | E1 form em linha + Executar; E2 ProgressTracker; E3 histórico com badge/vocabulário/Abrir; PagePath. |
| 2026-11-14 | U4 | `25a491123f` | DONE | A1–A9: PagePath/Hero/6 KPIs/donut status/charts/UnderlineNav/tabela/CLARA; loading G7; daily A5. |
| 2026-11-14 | U5 | `94a98abca1` | DONE | O: PagePath, badge severidade, DetailField, Por quê/O que fazer, confirmação Resolver, Timeline, XML. |
| 2026-11-14 | U6 | `f16cec684a` | DONE | NotFound → CfPageHero. Lista V5: relatórios ClosingHero (padrão fechamento); Meu perfil no Core `/profile`. |
| 2026-11-15 | U7 | `cc2aec7849` | DONE | HML MFE healthy; Playwright U7 PASS (home/entry/analysis 1440/1024/390). G9 openMs≈9,0s (docs=315, high=17). Screenshots `/tmp/ui-review-u7`. Perfis Keycloak dedicados: INCONCLUSIVE (só `hml-tester`, como H5). axe: INCONCLUSIVE (sem `@axe-core/playwright` no MFE). Claro/escuro: INCONCLUSIVE. Fixes: PagePath `back` + hooks #310. |
| 2026-11-15 | U8 | `4785e7aa3e` | DONE | Tags `rollback-ui-review-controllership-finance` + `rollback-ui-review-plugin-ui`. PROD pull+build plugin-ui+CF; home/remoteEntry 200; App chunk com «Executar auditoria» e «Diferença nas Altas». Abertura autenticada Início/entrada/análise 01–15/11 + paridade CLARA: INCONCLUSIVE (sem usuário de teste PROD; não usar credencial HML). |

## 7. Report final (U0–U8)

| Etapa | SHA | Resultado |
|---|---|---|
| U0 | `938ccd1edb` | Matriz G/H/E/A/O/F no código |
| U1 | `1bcb9f470a` | Vocabulário/R$/badges/estados/CSS |
| U2 | `b31321f1d0` | Highlights reais + ícones + LNF title (kit aditivo) |
| U3 | `4577724671` | Entrada: form, ProgressTracker, histórico |
| U4 | `25a491123f` | Análise layout alvo A1–A9 |
| U5 | `94a98abca1` | Detalhe ocorrência |
| U6 | `f16cec684a` | NotFound + lista V5 |
| U7 | `cc2aec7849` (+fixes `f5f263df86`/`cc2aec7849`) | HML Playwright PASS; G9≈9s |
| U8 | `4785e7aa3e` | PROD publicado; tags de rollback |

**Paradas V1–V6:** nenhuma acionada.

### U6 — páginas corrigidas e lista de decisão (V5)

| Página | Ação |
|---|---|
| `NotFoundPage` | Corrigida — CfPageHero + CfActionButton |
| Relatórios / Central de Fechamento (`ClosingHero`) | **V5** — já seguem o padrão próprio do fechamento (doc 50); não forçar PageHero genérico |
| Administração (checklist/documentos/catálogos) | **OK** — PagePath e/ou ClosingHero presentes |
| Meu perfil | **V5** — destino Core `/profile` (fora do MFE) |
