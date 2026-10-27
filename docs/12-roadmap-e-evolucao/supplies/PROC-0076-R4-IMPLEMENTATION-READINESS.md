# PROC-0076.R4 — Implementation Readiness: Inteligência de Mercado

> **Status:** SPEC — decisões congeladas, gaps e sequência para a próxima execução (R4.S1+). Documental.
> **Base:** HEAD `8b9003f438`; produção roda a página R3 (`feeea8e1b9`) com IBGE real; Comex sem NCM; PTAX OFF (WAF); metais LME em quarentena de direitos.

## 1. Decisões congeladas

| # | Decisão | Base |
|---|---|---|
| D-01 | Página única com uma perspectiva ativa e um único painel de visualização | wireframe aprovado |
| D-02 | Perspectivas: `metals`, `fx`, `indicators` (mapeamento legado em Doc C §3) | wireframe + reconciliação R3 |
| D-03 | Metais = grade de 6 cards multi-seleção; seleção persistida em `metals` CSV na URL | wireframe §2 |
| D-04 | FrequencySwitcher `Dia\|Semana\|Mês\|Ano` reusa `SuppliesSegmentToggle`; `week` condicionado ao contrato BFF | Doc B + gap G-02 |
| D-05 | KPI strip via `SuppliesDataCardsGrid`+`SuppliesKpiCard` (padrão já em produção) | Doc B §1 |
| D-06 | ViewSwitcher `chart\|table\|compare`; `compare` disabled sem compatibilidade | Doc C §1.4 |
| D-07 | Cards de metais = `LOCAL_FEATURE_COMPONENT` novo (ex.: `MarketInstrumentCard`) — nenhum export do kit cobre seleção com `aria-pressed`; promovível a kit só com segunda demanda | Doc B §2 |
| D-08 | Zero componente novo no kit sem funil de reuso; nenhum hex arbitrário | regra `plugins-reusable-components` |
| D-09 | Quarentena LME mantida: metais só selecionáveis com `display_allowed===true`; sem fonte → estado `source_rights_pending` | source-rights ledger |
| D-10 | URL params válidos por allowlist; compat R3/R2 preservada | Doc C §3 |
| D-11 | Nenhum cálculo no frontend; médias/variações vêm de read model BFF | arquitetura |
| D-12 | Sem permission nova, sem mudança Core/Keycloak, sem deploy nesta fase | briefing |

## 2. Dependências e gaps

| Gap | Owner | Bloqueia | Decisão necessária |
|---|---|---|---|
| G-01: nenhum metal homologado (`display_allowed`) | external-data-api + aprovação de direitos | dados reais de Metais | escolha/homologação de fonte — fora de escopo da R4.S1 UI; UI já deve nascer com estado `source_rights_pending` |
| G-02: `MarketGranularity` não inclui `week` | supplies-api/external-data-api | Frequência "Semana" | incluir `week` no contrato ou desabilitar a opção até então |
| G-03: contrato de catálogo multi-instrumento de metais | supplies-api | grade de cards alimentada por API | extensão aditiva do endpoint de catálogo/filters com `instrument_kind:"metal"` |
| G-04: endpoint de séries multi-instrumento (metas[]) | supplies-api | gráfico/compare multi-metal | resposta com `series[]` por instrumento + cobertura agregada |
| G-05: contrato de comparação homologado | supplies-api + produto | habilitar `compare` | metodologia de compatibilidade (mesma unidade+granularidade) |
| G-06: KPIs de período (média/variação) | supplies-api | faixa de KPIs por seleção | `summary` agregado multi-série ou regra de 1º selecionado |
| G-07: boletins PTAX além de fechamento | external-data-api (BCB) | seletor de boletim completo | depende de feed liberado (WAF) |
| G-08: Comex sem NCM homologada | PO/produto | dados Comex | homologação de NCMs |
| G-09: PTAX OFF (WAF egress) | infra | dados Câmbio | egress habilitado |
| G-10: evidência visual autenticada | QA/dev | DoD visual | automação de browser autenticado (existe lacuna desde R3) |

## 3. Matriz RQ/AC

| RQ | Wireframe (Doc A) | Componente (Doc B) | Contrato (Doc C / api) | Owner | Teste futuro | Evidência requerida |
|---|---|---|---|---|---|---|
| R4-01 Página única | §1 cadeia | PagePath+PageHero+SectionCard | `/apps/supplies/market-intelligence` | MFE supplies | structural: 1 panel mount | screenshot prod |
| R4-02 Três perspectivas | §2–4 | `SuppliesSegmentToggle` | `view=metals|fx|indicators` | MFE supplies | url state test | F5/back |
| R4-03 Seis cards | §2 | `MarketInstrumentCard` (novo local) | catálogo `instrument_kind:"metal"` (G-03) | MFE supplies | a11y/selection test | grid render |
| R4-04 Seleção múltipla | §2 tabela | idem | `metals=cu,al,…` | MFE supplies | multi-select/url test | URL roundtrip |
| R4-05 Frequência | §5 | `SuppliesSegmentToggle` | `freq=day|week|month|year` (G-02) | supplies-api + MFE | disabled-option test | query observada |
| R4-06 KPIs contextuais | §6 | `SuppliesKpiCard`/`MetricStrip` | `MarketSeriesSummary` ext. (G-06) | supplies-api | unit/contract test | payload prod |
| R4-07 Gráfico/Tabela/Comparação | §7 | `MultiTypeSeriesChart`+`DataTable` | `mode` + compare contract (G-05) | MFE supplies | mode-switch test | 3 modos |
| R4-08 Estados honestos | Doc C §2 | `EmptyState/StateBanner/StatusBadge` | `data_status`/`unavailable_reason` | supplies-api + MFE | error/empty test matrix | cada estado |
| R4-09 Tokens DELPI | Doc C §6 | todos | `--sp-*`/`--delpi-ui-*` | plugin-ui/MFE | lint de hex | zero hex na feature |
| R4-10 Responsivo | Doc C §7 | kit breakpoints | — | MFE supplies | visual test | 3 viewports |
| R4-11 Acessibilidade | Doc C §4 | `aria*` do kit + card novo | — | MFE supplies | axe/focus test | leitura AT |
| R4-12 URL/F5 | Doc C §3 | `marketIntelligenceUrl.ts` | params allowlist | MFE supplies | url parse/compat test | F5/back |
| R4-13 Exportação | Doc A §7 | `SuppliesTabularExportButtons` | CSV/XLSX/PDF por modo | MFE supplies | export test | arquivo gerado |
| R4-14 Ajuda | Doc A §10 | `HelpTooltip`+manual | `helpTooltips.ts` sync | MFE supplies | feature-help-sync test | docs render |
| R4-15 Independência de provedor | Doc C §5 | catálogo-driven | `source_id` dinâmico | external-data-api | contract test | sem hardcode |
| R4-16 Reuso plugin-ui | Doc B todo | tabela de classificação | — | plugin-ui/MFE | kit-inventory lint | imports verificados |
| R4-17 Sem dados não autorizados | Doc C §2/8 | gate `display_allowed` | default-deny | external-data-api + BFF | security test | quarentena ok |
| R4-18 Doc pronta p/ implementação | este doc | — | — | produto/arq | revisão PO | PR aprovado |

## 4. Sequência sugerida (próximas execuções — não nesta)

1. **R4.S1 — contratos** (supplies-api/external-data-api): G-02 `week`, G-03 catálogo metais, G-04 séries multi-instrumento, G-06 KPIs — todos aditivos/retrocompatíveis.
2. **R4.S2 — UI Metais**: `MarketInstrumentCard` local + grade + URL `metals` + estados `source_rights_pending`.
3. **R4.S3 — perspectivas fx/indicators + modos** incl. `compare` quando G-05.
4. **R4.S4 — hardening**: a11y, responsivo, exports, help sync, testes + smoke prod.

Cada S respeita: implementação em branch dedicada, gates de arquitetura, testes antes de deploy.

## 5. Restrições que seguem vigentes

Quarentena LME; feeds OFF permanecem OFF até homologação; sem permission nova; nada de dados simulados; default-deny; documentação não autoriza uso de dados LME nem promete cotação diária antes de provedor homologado.
