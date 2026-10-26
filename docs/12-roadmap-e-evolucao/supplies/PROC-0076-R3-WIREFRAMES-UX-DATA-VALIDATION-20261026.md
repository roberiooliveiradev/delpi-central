# PROC-0076.R3 — Wireframes e contrato UX: Inteligência de Mercado

> **Status:** DESIGN / TARGET, validado contra código do HEAD `5c5483345f004b6acbef93c3e284c263426b3723` e capturas da produção fornecidas pelo PO em 2026-10-26; **não implementado neste PR**.
> **Decisão PO:** reduzir rolagem e cards repetidos, unificar navegação e indicadores com múltiplos modos visuais no hero; registrar wireframes de todos os componentes; em seguida investigar os vazios, corrigir read-models/UX e publicar a evolução.
> **Boundary:** `plugins/supplies` (UX) → `supplies-api` (BFF) → `external-data-api` (dados). Sem novo RBAC; `@delpi/plugin-ui` primeiro; CSS `.dashboard-supplies-portal`.
> **Source of truth:** instruções oficiais + .cursor + contratos, OpenAPI e HEAD; este wireframe não altera direito de uso, source rights, schema, nem autoriza deploy/feature cutover por si.

## 1. Diagnóstico da tela atual

**PROVEN em captura:** navegação e rota carregam em produção; gráfico e tabela IBGE apresentam observações (número-índice e variação M/M-1), seleção de séries funciona; meses sem observação estão identificados; PTAX, resumo do período, evolução da cotação e médias mensais aparecem vazios. A página exige rolagem longa e tem seções grandes empilhadas. O filtro global está em `instrument=usd-brl`, `currency=BRL`, `fx_kind=ptax_closing_sell`, período 26/10/2025–26/10/2026, enquanto o conteúdo efetivamente disponível é IBGE IPP.

**PROVEN em código:** `MarketIntelligencePage.tsx` (710 linhas) renderiza simultaneamente `SuppliesPageHero` com filtros antigos, `SuppliesSectionCard` com quatro KPI da rota legada `/summary`, três `MarketIntelligenceModuleSection` independentes (Comex, IBGE, PTAX), `MarketIntelligenceSeriesSection` e `MarketIntelligenceMonthlyTable` legados. Os dois últimos dependem de `ready` e do instrumento de cotação antigo, não da série IPP escolhida. Isso explica a **duplicação de superfícies e a falta de alinhamento semântico**, mas a causa de cada valor vazio exige rastrear os payloads reais antes de alterar cálculos.

**Classificação:** duplicação UX = PROVEN; resumo vazio sob USD/BRL sem feed = provável comportamento coerente com PTAX OFF, **TO_VERIFY com contrato/HTTP**; aviso IBGE sobre "câmbio correspondente" é texto potencialmente incorreto para índice IPP, **UX DEFECT to verify**; ausência de dado set/2026, out/2026 = **TO_VERIFY** calendário de publicação e janela do feed, não assumir falha; Comex NCM sem opções é esperado enquanto `comex_ncm_allowlist` não homologada, mas rótulo genérico "direitos em revisão" pode não refletir causa.

## 2. Direção de produto e modelo de navegação

**Uma página, uma área de trabalho e três perspectivas exclusivas**. O hero concentra título, freshness geral e troca de perspectiva. Abaixo: uma barra contextual de filtros, uma faixa compacta com no máximo 3–4 métricas relevantes à perspectiva, e um **único painel de análise reutilizável** com modo Gráfico | Tabela | Comparação/Detalhes quando semanticamente válido. Ocultar visualizações de perspectivas inativas (não apenas `display:none` com fetching desnecessário).

Perspectivas:
- **Preços industriais / IBGE** (default inicial enquanto for a única fonte com observações reais; source availability dirigida pelo BFF, nunca hardcode de ambiente). Índice da Metalurgia ou variação mensal, unidade explicitada.
- **Importações / Comex Stat**. NCM permitida por catálogo, USD FOB/t calculado; sem allowlist ou feed, painel compacto de status e próximo requisito, sem card em branco.
- **Câmbio / BCB PTAX**. Compra/venda e período diário/mensal; feed OFF significa `not_collected`/`source_unavailable`, não sugerir "ajuste filtros" como se o usuário pudesse resolver.
- **Legado LME**: fora da navegação principal, source rights em quarentena, sem preço nem fallback. Nenhum elemento de "cotação de metais" enquanto a fonte principal real não fornece tal cotação.

**Default permitido:** ao abrir sem parâmetros, seleção inicial deriva de `catalog.selectable === true` + dados disponíveis (freshness/cobertura comprovados); priorizar visualização útil e explicar o porquê. Um deep link legado `instrument=usd-brl` não deve forçar a perspectiva IBGE para cálculo cambial. Se parâmetros conflitarem, resolver por precedência `view` explícita válida > `ipp_series`/NCM/FX válidos > default catalog; preservar compatibilidade de links antigos com aviso não intrusivo quando necessário.

## 3. Wireframe W0 — Desktop, first fold (largura ~1440)

```text
┌──────────────────────────────────────────────────────────────────────────────────────┐
│ ‹ Início / Inteligência de Mercado                       [Fonte / atualização] [?]    │
│ INTELIGÊNCIA DE MERCADO                                   [Atualizar] [Favorito]      │
│ Preços industriais, importações e câmbio — metodologia e fonte em contexto            │
│ [● Preços industriais · IBGE] [Importações · Comex] [Câmbio · PTAX]                    │
├──────────────────────────────────────────────────────────────────────────────────────┤
│ Série [IPP Metalurgia — Número-índice ▾]  Período [12 meses ▾] [Personalizar ▾]        │
│ Variável [Número-índice | Variação M/M-1]      [Dados até ago/2026] [Fonte IBGE ↗]    │
├──────────────────────────────────────────────────────────────────────────────────────┤
│  [Último índice  • • •] [Variação no mês  • • •] [Média período* • • •] [Cobertura]      │
│  *Somente se média de índice for metodologicamente aceita e identificada               │
├──────────────────────────────────────────────────────────────────────────────────────┤
│ [ Gráfico ] [ Tabela ] [ Comparar* ]                       [CSV] [Excel] [PDF] [?]     │
│                                                                                       │
│   GRÁFICO IPP (única visualização principal, altura ~300–360px)                        │
│   [eixo y com unidade e zero/baseline adequada]              [legenda]                 │
│                                                                                       │
│ Fonte: IBGE/SIDRA • Série 6903/842/46641 • Base dez/2018=100 • 11 meses válidos        │
└──────────────────────────────────────────────────────────────────────────────────────┘
```

**First fold target:** a troca de fonte, filtros, resumo pertinente e início do gráfico são visíveis sem descer vários cards; não prometer altura fixa em todas resoluções. Evitar KPI independente repetindo dado da mesma série; o resumo não pode citar USD/BRL quando a aba IBGE está ativa.

## 4. Wireframe W1 — Mobile (largura ~375)

```text
┌────────────────────────────────┐
│ ‹ Inteligência de Mercado  [?] │
│ [ IBGE | Comex | PTAX ]         │
│ [Fonte • Última atualização]   │
│ Série ▾                         │
│ Período [12 meses ▾] [Filtro]   │
│ [Último índice] [Variação]      │
│ [ Gráfico | Tabela ]            │
│                                │
│    gráfico responsivo           │
│   scroll apenas eixo X se       │
│   necessário e com indicação   │
│                                │
│ [Dados válidos / lacunas]       │
│ [Exportar ▾]                   │
└────────────────────────────────┘
```

Sem quatro tabelas sequenciais. Inputs com touch targets, rótulos completos e focus order; `aria-selected`/tabs keyboard. Preferir componentes existentes de SegmentedToggle/Tabs do kit conforme inventário.

## 5. Wireframes por componente (IDs para rastreabilidade)

| ID | Componente | Estados e comportamentos obrigatórios |
|---|---|---|
| C01 | PagePath/voltar | Navegação legítima sem reload desnecessário; link direto/F5/back-forward |
| C02 | PageHero condensado | Título, descrição não enganosa, refresh, Ajuda, provenance; não ancorado à fonte legada |
| C03 | SourceSwitcher / perspectives | 3 opções IBGE/Comex/PTAX; selecionada acessível, teclado; indisponível pode abrir painel de diagnóstico **sem fingir dado** |
| C04 | FilterBar contextual | IBGE: série/variável/período; Comex: NCM/dimensões/período; PTAX: compra/venda/dia/mês. Sem FX ou moeda para índices |
| C05 | Freshness / Quality banner | `available`, `partial`, `delayed`, `disabled`, `no_data`, `error` como semânticas distintas; datas de referência vs coleta |
| C06 | KPI strip contextual | Somente KPIs válidos por metric_kind: IPP último valor + delta; Comex FOB/ton + massa; PTAX última taxa/média; null mostrado com motivo |
| C07 | ViewSwitcher | Gráfico/Tabela/Comparação (quando há contrato e séries compatíveis); uma visualização ativa, preservada na URL |
| C08 | ChartPanel | Gráfico de índice ou %, USD/t, R$/USD; eixo/legenda/unidade exclusivos; dias/meses faltantes `null` |
| C09 | TablePanel | Meses reais, valor, unidade, cobertura, status e timestamp; paginação bounded sem card extra |
| C10 | ComparePanel | Apenas duas séries com mesma unidade/granularidade; caso contrário desabilitado com explicação |
| C11 | ExportMenu | CSV/XLSX/PDF respeitando filtro e view, fonte e rótulos; não exportar dados protegidos |
| C12 | SourceInfo / methodology | Informar origem (IBGE 6903, MDIC, BCB), granularidade e direitos; no Comex disclaimer FOB médio ≠ spot |
| C13 | Empty/Unavailable | Sem NCM homologada / feed OFF / sem observações / erro de rede distinguíveis; sem tabelas 13 meses zeradas |
| C14 | Error/AuthZ | 401, 403 Core, 503 source, 504 timeout e falha parcial sem mascaramento; ações coerentes |
| C15 | Help/context | Ajuda sincronizada aos três indicadores e aos filtros, explicação de coverage e IPP base |
| C16 | URL State | `view=ipp|comex|fx`, `mode=chart|table|compare`, `period`, seletor de série; fallback compatível |
| C17 | Loading skeleton | Esqueleto curto da aba ativa, sem apagar dados de outra aba indevidamente |
| C18 | Compact source health | Cards/status pequenos no hero para 3 fontes: IBGE dados, Comex aguardando NCM/feed, PTAX indisponível por integração |

### C06 — KPI contract details

| Perspectiva | Resumo possível | Não mostrar |
|---|---|---|
| IBGE IPP número-índice | Última referência e valor; variação da mesma atividade (fonte secundária validada); meses válidos vs esperados; frescor | Dólar PTAX, "última cotação do metal", média do índice sem justificativa |
| IBGE IPP M/M-1 | Última variação %, média aritmética das variações **somente se business rule aprovar**; amplitude/mínima e máxima com metodologia; cobertura | Unidade BRL/USD |
| Comex NCM | Último FOB/t ponderado; FOB total, massa importada, observações cobertas | Spot LME / custo DELPI |
| BCB PTAX | Última taxa (tipo e data), média do período (metodologia documentada), variação entre dias válidos, cobertura | Números sem PTAX coletada |

As métricas dependem de read models autorizados na supplies-api; UI não recalcula regra de negócio. Campos sem fonte são `null + reason` e não aparecem como dash sem contexto.

## 6. Wireframes de estados

### Estado S-AVAILABLE (IPP real)
```text
[IBGE: dados até ago/2026]  [Índice 183,...] [M/M-1 +2,13%] [11/13 meses]
[Gráfico ▣ | Tabela] [série com 11 pontos, lacunas explicitadas]
```

### Estado S-NOT-CONFIGURED (Comex)
```text
[Comex Stat] [Ainda não disponível]
NCMs de referência não homologadas para este Portal.
Dados de importação não serão exibidos até aprovação e coleta validada.
[Entenda o indicador]  [Ver metodologia]
```

### Estado S-FEED-BLOCKED (PTAX)
```text
[Câmbio PTAX] [Integração temporariamente indisponível]
A série não foi coletada para o intervalo. Não é um erro de filtro.
[Recarregar] [Sobre a fonte]
```

### Estado S-PARTIAL
```text
[IPP] [Dados parciais: 11 de 13 competências]
[Gráfico com lacunas, sem ligar indevidamente pontos separados]
Períodos sem dado: outubro/2025, setembro-outubro/2026.
```

### Estado S-ERROR / FORBIDDEN
```text
[Não foi possível carregar a fonte.] [Tentar novamente]
[Sem autorização para usar Inteligência de Mercado.] (403 Core)
```

Não classificar o conjunto como `partial` por ausência de PTAX quando a perspectiva IBGE não precisa de câmbio. Ajustar mensagens estritamente à dependência da métrica corrente.

## 7. Sequência de implementação R3 — depois do wireframe

**R3.S0 (este PR):** inventário + wireframes e contrato UX por componente, desktop/mobile, estados, dados, dependências e gate de UX. **Nenhuma alteração de runtime**.

**R3.S1 — Data audit read-only:** no ambiente-alvo e sob autorização, obter JSON sanitizado de: catalog, `/market-intelligence/filters`, `/summary`, `/series`, `/monthly-averages`, `/producer-prices/series`, `/imports/series`, `/fx/series`; registrar queries e metadados de fonte, `metric_kind`, `unit`, série/período, `data_status`, `coverage`, `freshness`, observações e `null reasons`; validar contra PostgreSQL `external_data` no owner com read-only e SIDRA. Provar por que o resumo/FX antigo vem nulo mesmo com IBGE disponível; checar mapeamento de moeda BRL/IPP e período diário x mensal, independência do FX. Não modificar política/source rights para fabricar dados. Tratar feed OFF como indisponível e falta de observação como no_data; revisar se meses ausentes são esperados pelo release calendar. Produzir matriz campo→fonte→fórmula→exemplo real→status.

**R3.S2 — Producer/BFF mínimo diff:** somente se o audit revelar lacuna de DTO/erro/quality/reason no owner; novos read models tipados e seguros, sem quebrar endpoints antigos. IBGE resumo coerente com `ipp_index` e `ipp_monthly_change_pct`, Comex e PTAX independentes. AuthZ Core e S2S intactos. TEST positive+sibling+negative.

**R3.S3 — MFE refactor:** composição por perspective única, hero contextual e barra de filtros, 1 painel gráfico/tabela, C01–C18, ajuda e URLs. Reaproveitar kit; reduzir DOM/fetch desnecessários e layout vertical. Estado de data vazio por fonte, não herdar `usd-brl` como default quando IBGE ativo. Testes de URL/F5, races, todas as perspectivas, dark/light/mobile/focus/export/403.

**R3.S4 — Verify & deploy:** validar IBGE com dado real e comprovável, comparar série/valores pelo SIDRA e DB, checks 401/403/200, build, smoke federado autenticado e screenshots desktop/mobile. Commit/push/PR/review, deploy pelo fluxo canônico com rollback; sem ativar feeds Comex/PTAX/LME e sem mudanças de permission.

## 8. RQ/AC e testes de aceite

| RQ | AC verificável | Owner | Evidência |
|---|---|---|---|
| R3-01 | Três perspectivas substituem seis seções empilhadas | MFE | Browser desktop/mobile, screenshot before/after |
| R3-02 | Hero permite troca da perspectiva sem recarregar a página | MFE | Keyboard/click/E2E |
| R3-03 | Só há um gráfico/tabela principal por perspectiva | MFE | DOM/layout, scroll height |
| R3-04 | Filtros e KPIs são específicos da métrica selecionada | BFF/MFE | Payload/testes, nenhuma PTAX em IPP |
| R3-05 | IBGE com 11 pontos reais é refletido no resumo apropriado | BFF/MFE | Compare DB→BFF→UI |
| R3-06 | Meses faltantes têm status e motivo sem zeros artificiais | Data/BFF/MFE | Real source + null tests |
| R3-07 | Comex sem NCM homologada mostra estado de configuração | MFE | Catalog sem allowlist |
| R3-08 | PTAX OFF não ocupa grandes áreas vazias | MFE | E2E feed disabled |
| R3-09 | Eixos, unidades, tooltip, labels, metodologia corretos | MFE | IBGE índice/%, Comex USD/t, PTAX R$/USD |
| R3-10 | URL/F5/back preservam source/metric/mode/period | MFE | Browser test |
| R3-11 | Exportação corresponde ao modo/filtro selecionado | MFE/BFF | CSV/XLSX/PDF |
| R3-12 | Ajuda e acessibilidade sincronizadas | MFE | Tab/focus/aria/Help |
| R3-13 | Core AuthZ + S2S + LME quarantine intactos | API/BFF | 401/403/503 tests |
| R3-14 | Produção validada com screenshots autenticados | Release | Smoke E2E + SHA/digest |

**Definition of Done UX:** primeiro viewport já contém orientação, perspectiva, filtros contextuais, KPIs contextualizados e visualização inicial do IPP; não exige passar por seções sem dado para chegar ao conteúdo útil. Em mobile, empilhar apenas conteúdos da perspectiva selecionada. Não prometer "página curta" se a tabela possuir muitos registros: usar view switch/paginação.

## 9. Alertas e separação de fatos

- Capturas **provam visual** e seleção IBGE, não provam isoladamente a igualdade de cada número com a API do SIDRA. Validação numérica é R3.S1, com source/live e SQL read-only.
- `IBGE 11/13` é contagem aproximada da captura para 26/10/2025–26/10/2026; confirmar o calendário e contagem pelo payload antes de escrever textos fixos.
- `Comex Stat` oferece valores médios FOB por NCM, não preço internacional do metal nem custo da DELPI.
- `PTAX` feed OFF por problema de egress; não inventar taxa ou orientar usuário a alterar filtros quando o feed não está disponível.
- Dados LME permanecem em quarentena. Nenhuma UI pode reabilitar por omissão.
- Incidente de tokens Core expostos, registrado no review do PR #116, é trilha de segurança P0 separada e não deve desaparecer por causa do redesenho visual.

## 10. Referências

- Página em produção: `/apps/supplies/market-intelligence`.
- Código vigente: `plugins/supplies/src/features/market-intelligence/{MarketIntelligencePage.tsx,MarketIntelligenceModuleSection.tsx,MarketIntelligenceSeriesSection.tsx,MarketIntelligenceMonthlyTable.tsx,useMarketIntelligenceFilters.ts}`.
- BFF: `supplies-api/app/application/services/market_intelligence_service.py`, `market_intelligence_routes.py`.
- Contratos PROC-0076.R2 em `docs/12-roadmap-e-evolucao/supplies/` e `shared-integrations/`.
- Source oficiais: IBGE SIDRA tabela 6903 variáveis 10008/1396 classificação 842 atividade 46641; MDIC base Comex CSV; BCB PTAX.
