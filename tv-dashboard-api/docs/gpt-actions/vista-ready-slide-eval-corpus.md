# VISTA — eval corpus (ready slide)

Corpus estável para regressão de inteligência (sem Action nova). Critério PASS alinhado a `write_quality` + `compound_slide`.

| ID | Pedido (NL) | Expectativa |
|---|---|---|
| C1 | crie um slide com ppm externo (playlist única) | `dateRangePreset=this_month`; VERIFIED sem “Informe o período”; KPI Delpi; projection não vazia |
| C2 | crie um slide com ppm externo (>1 playlist, sem nome) | UMA pergunta com nomes (PLAYLIST_CLARIFICATION) |
| C3 | otd + série no mesmo slide | recipe `TV_KPI_PLUS_CHART` ou `TV_KPI_SERIES_TABLE`; chrome Delpi |
| C4 | tabela por filial | `TV_TABLE_FOCUS` / table_view Delpi; params vivos se date_range |
| C5 | negative: fonte date_range com params `{}` | patch rejeita **ou** enrich injeta preset; nunca erro de período no editor após VERIFIED |
| C6 | agora deixe ele azul | muta referente INFORMED (último slide/bloco); não cria slide novo |
| C7 | painel do dia / reordene | `playlist_curation` READ + update/reorder; sem playlist inventada |
| C8 | join duas fontes com branch comum | `joinHints` / `JoinPlanService` → merge tipado |
| C9 | rota `exposesSiGoal` | directives `si_goals` — meta vs realizado sem inventar números |
| C10 | dois KPIs no mesmo slide | recipe `TV_KPI_ROW_2`; frames sem overlap |
| C11 | quatro indicadores em grade | `TV_KPI_GRID_4`; ≤ `maxPrimarySignalsPerSlide` |
| C12 | negative: overlap / contraste baixo | `OUTCOME_NOT_VERIFIED` `slide_layout_quality` |
| C13 | mude o bloco selecionado (editor aberto) | `editorFocus.selectedIds` INFORMED; não criar slide novo |
| C14 | painel operacional Delpi | `THEME_DELPI` + cards `brand.card` brancos + accent; partes ≥ `partChrome` |
| C15 | filtros período/filial no slide | `TV_FILTER_STRIP` e/ou `dataFilters` + inputs |
| C16 | defaults da programação | `patch_playlist_data_defaults` (branch/período) |
| C17 | comparação categórica | `TV_KPI_PLUS_CHART_BAR` / `chartType=bar`; negative: pie em série diária |
| C18 | ajuste o KPI sem criar slide novo (sem print) | `layoutDigest` INFORMED → upsert_block no blockId existente; mode `LAYOUT_PERCEPTION`; sem `add_blank_slide` |
| C19 | melhore hierarquia visual (com prévia) | `includePreview=true` → raciocinar sobre `slidePreview.previewUrl` + digest; DESIGN_REFINE tipado; PREPARE/ACT inalterados |
| C20 | negative: inventar frames ignorando digest | anti_pattern; deve ler `layoutDigest` do context antes de frames novos |
| C21 | filial/período padrão da programação | `patch_playlist_data_defaults`; não copiar branch em toda `data_source` |
| C22 | período só deste slide | `dataFilters` / `TV_FILTER_STRIP`; herança das fontes |
| C23 | TOP N só numa tabela | params na fonte; negative: não colocar `top_limit` em `dataDefaults` |
| C24 | negative: date_range com params `{}` ou datas absolutas eternas | `write_quality` + `filter_layering.dates` |
| C25 | melhore/revise esta programação | `continuous_review`: READ + patch no existente; negative: create_playlist sem pedido explícito |
| C26 | corrija os filtros duplicados nas fontes | re-layer para dataDefaults/dataFilters; sem slide novo |
| C27 | breakdown por filial / comparação | `visual_selection` → `bar`/`horizontal_bar` / `TV_KPI_PLUS_CHART_BAR`; **não** area |
| C28 | composição de status (poucas fatias) | `pie`/`doughnut` / `TV_KPI_PLUS_CHART_PIE` |
| C29 | ranking / TOP N muitas linhas | `table_view` banded / `TV_TABLE_FOCUS` / `TV_HERO_PLUS_TABLE` |
| C30 | negative: pie em série diária densa | anti_pattern `chartTypeHints.forbidden.dense_daily_series` |
| C31 | melhore o visual (slide só KPI+área) | `DESIGN_REFINE` + `visual_selection`: diversificar chartType/família se a forma do dado permitir; não só tipografia |

Smoke automatizado parcial: `tests/test_ready_slide_ux.py`, `tests/test_slide_layout_quality.py`, `tests/test_slide_part_chrome.py`, `tests/test_editor_focus_store.py`, `tests/test_layout_digest_and_slide_preview.py`, `tests/test_vista_agent_intelligence.py`.

**Gate vivo (FAIL = regressão):** `tests/fixtures/vista_ready_slide_corpus.json` + `tests/test_vista_ready_slide_corpus_gate.py` (C15–C31 + gates G_* para logo/tema, auto-layout, blank slide, templates, editorFocus, mediaInventory). Comando:

```bash
cd tv-dashboard-api && PYTHONPATH=. .venv/bin/python -m pytest tests/test_vista_ready_slide_corpus_gate.py tests/test_filter_digest_and_relayer.py -q
```
