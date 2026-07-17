# Painéis TV (`tv-dashboard`)

Plugin MFE para **gerenciar programações rotativas** exibidas em TVs corporativas.

Documentação completa: [`docs/12-roadmap-e-evolucao/tv-dashboard/README.md`](../../docs/12-roadmap-e-evolucao/tv-dashboard/README.md)  
Roadmap editor de slides: [playbook §17](../../docs/12-roadmap-e-evolucao/tv-dashboard/PLAYBOOK-EXCELENCIA.md#17-editor-de-slides-personalizados--paridade-canva--powerpoint)  
Indicadores live api-delpi: [playbook §18](../../docs/12-roadmap-e-evolucao/tv-dashboard/PLAYBOOK-EXCELENCIA.md#18-indicadores-live-api-delpi-em-slides-personalizados)  
Gráfico / KPI / tabela compostos: [playbook §19](../../docs/12-roadmap-e-evolucao/tv-dashboard/PLAYBOOK-EXCELENCIA.md#19-gráfico-composto-por-primitivos--edição-no-palco-onda-4g)  
Dois escopos de seleção: [playbook §19.19](../../docs/12-roadmap-e-evolucao/tv-dashboard/PLAYBOOK-EXCELENCIA.md#1919-dois-escopos-de-seleção--chrome-de-partes-jul2026)

Power Query M: [playbook](../../docs/12-roadmap-e-evolucao/tv-dashboard/PLAYBOOK-POWER-QUERY-M.md) · [status da Fase 7](../../docs/12-roadmap-e-evolucao/tv-dashboard/FASE-7-STATUS-M-DELPI.md). O editor avançado usa o textarea canônico do kit, mas recebe realce, autocomplete/contexto, diagnostics, formatter e rename do backend. Busca de etapa, DAG simples e undo/redo vivem somente no draft local; o browser não analisa nem executa M. O piloto funcional está ativo com telemetria segura; profiling, explain e caches continuam desligados.

---

## Funcionalidades

- CRUD de programações (playlists) e telas (slides)
- Telas **nativas** (OEE, OTD, PPM, estoque, comunicado) e **externas** (iframe)
- Reordenação (drag-and-drop), duplicar, pausar tela
- **Pré-visualização** fullscreen (`/playlists/{id}/preview`)
- **Link público** sem login: `/p/tv-dashboard/present/{token}`
- Copiar link, QR, regenerar token, desativar / excluir
- Status «TV online» via heartbeat na rota pública
- **Colaboração ao vivo:** alterações do slide são transmitidas por `slide_draft`; a seleção de outros editores aparece no componente com borda vermelha e balão de identidade. Não é CRDT: conflitos simultâneos no mesmo bloco continuam last-write-wins.
- Catálogo de presets e importação de telas prontas
- RBAC por filial e visão consolidada
- **Editor visual v1.5+** (slide Personalizado): undo/redo, multi-seleção, camadas, templates, biblioteca de mídia, crop, ícones Lucide
- **Histórico de revisões:** a Timeline canônica de `@delpi/plugin-ui` mostra autor (nome/e-mail), campos e telas adicionadas, removidas, editadas ou reordenadas; snapshots antigos mantêm o resumo por motivo/prévia. Undo/redo e restauração manual usam snapshots atômicos do backend com controle otimista de revisão.
- **Dados live api-delpi (4F):** painel Dados, `data_source` + `chart_view` / `table_view` / `kpi_view`, catálogo de rotas GET, gráficos/tabelas/KPI com **partes selecionáveis** no palco
- **Preparar dados (M DELPI):** workbench de consultas em modal via `createHostContainedModalShell` do `@delpi/plugin-ui` — ocupa a área útil do MFE e não cobre a sidebar/chrome da Minha DELPI
- **Preparar dados M (Fase 7):** editor multiline e ribbon das fases anteriores,
  profiling opt-in, qualidade/distribuição amostradas, explain e tempo por etapa;
  AbortController cancela requests e o backend aplica deadline
- **Tabela live incremental:** rotas paginadas carregam a próxima página ao chegar ao fim do scroll; cabeçalho seleciona a coluna inteira, com alças de largura e quebra automática
- **Períodos relativos:** hoje; esta semana/mês/trimestre/ano; semana/mês/trimestre/ano anteriores; últimos 7/30/90/N dias; ou datas fixas. As datas relativas são recalculadas no fetch.
- **Séries temporais fiéis à API:** a granularidade da rota é preservada (ex.: `day` = um dia por linha), sem reagrupar datas em faixas; a tabela recebe todos os pontos retornados pela API (até 366 pontos em séries anuais diárias).
- **Dados em texto/forma (4P):** título, texto e forma podem projetar um campo da fonte (`textProjection` ou `contentRuns[].dataRef`) — ribbon «Campo em texto», inspetor e TV pública via enrichment
- **Multi-métrica:** rotas com vários `valueFields` (ex. LMP summary) entregam `kpiMetrics`; o gestor marca quais campos exibir na fonte e/ou no visual (KPI em grade, barras ou tabela indicador/valor)
- **Dois escopos no palco:** seleção **global** do widget (frame no slide) vs **subcomponente** (fundo, valor, título, chartArea, etc.) — ver [§19.19](../../docs/12-roadmap-e-evolucao/tv-dashboard/PLAYBOOK-EXCELENCIA.md#1919-dois-escopos-de-seleção--chrome-de-partes-jul2026)
- **Aplicar estilo a irmãos:** botão no inspetor KPI (título/valor/subtítulo), tabela (células/cabeçalhos) e marcadores do gráfico
- **Efeitos tipográficos:** sombra, contorno e **reflexo** (aba Formatar → Efeitos; reflexo Chromium)
- **Fontes personalizadas:** upload WOFF2/TTF/OTF na faixa Fonte, persistido como mídia da playlist e disponível no seletor tipográfico
- **Cores recentes** no seletor de cor; **export PNG/PDF/PPTX (MVP)** na faixa Início
- **Tabela (canvas):** grade estática editável, separada de `table_view` (dados live)
- **Notas do apresentador:** salvas por tela; preview admin com `?presenter=1` mostra notas e próxima tela sem afetar o kiosk
- **Presença no editor:** chip «Também editando» via WebSocket (sem merge CRDT)
- **Conectores MVP:** selecione 2 elementos → **Conectar** no ribbon Alinhar (seta entre centros); arrastar a seta solta a ligação — [§19.22](../../docs/12-roadmap-e-evolucao/tv-dashboard/PLAYBOOK-EXCELENCIA.md#1922-conectores-mvp-entre-blocos-jul2026)
- **Telas nativas OEE/OTD/PPM:** dual-KPI + série temporal SVG (`ConfigurableSeriesChart`)
- Filmstrip: prévia centralizada (`CenteredScaledPreview`), menu de contexto nas telas

---

## Seleção no palco (KPI / gráfico / tabela)

| Clique | Escopo | O que controla |
|--------|--------|----------------|
| **1º** no widget | **Global** | Posição, tamanho, rotação e camadas do **bloco** no slide. Outline/handles com padding (`--td-global-selection-pad`). Não altera fill/fonte das partes. |
| **Duplo clique** (já selecionado) | **Parte** | Fundo, valor, título, chartArea, etc. — chrome e frame da parte. **Esc** ou clique simples no bloco volta ao global. |

- Opacidade: **0%–100%** (Organizar); com parte selecionada grava na parte, senão no bloco.
- Preench./Contorno na ribbon Forma miram a **parte selecionada** (`resolveKpiShapeChromePartRef` / `resolveTableShapeChromePartRef` / chart part) — sem parte = só controles globais.
- Handles amarelos de raio do KPI no palco só no chrome da parte (não no nível global do card).
- TV / preview: `interactive={false}` — sem handlers de edição; mesmos `kpiParts` / `chartParts` / `tableParts`.

Contrato: `@delpi/plugin-ui` (`kpiCardParts`, `seriesChartParts`, `configurableTableParts`) + `@delpi/tv-dashboard-presentation`.

---

## Rotas do plugin

| Rota | Página |
|---|---|
| `/` | Lista de programações |
| `/playlists/new` | Nova programação |
| `/playlists/{id}` | Editor |
| `/playlists/{id}/preview` | Preview (motor compartilhado) |
| `/playlists/{id}/share` | Compartilhar |

Base gateway: `/apps/tv-dashboard/`

---

## Dependências

| Pacote | Uso |
|---|---|
| `tv-dashboard-api` | Backend (`/apps/tv-dashboard-api/`) |
| `@delpi/tv-dashboard-presentation` | `usePresentationEngine`, `NativeSlideView`, CSS `tdp-*` |
| `@delpi/plugin-ui` | Tooltips, labels, `Timeline`, `DataRouteCatalogPanel`, `FormatPaneShell`, `ContextMenu`, `CenteredScaledPreview` — **remote MF** |
| `public-hub` | View pública `present` (rebuild separado ao alterar apresentação) |

Integração: `@delpi/tv-dashboard-presentation` bundled (`COPY` no Dockerfile); `@delpi/plugin-ui` via `pluginUiRemote()` + `preparePluginUiRemote()`. Ver [module-federation.md](../plugin-ui/docs/module-federation.md).

---

## API admin (resumo)

```http
GET    /apps/tv-dashboard-api/playlists
POST   /apps/tv-dashboard-api/playlists
GET    /apps/tv-dashboard-api/playlists/{id}
GET    /apps/tv-dashboard-api/playlists/{id}/history
GET    /apps/tv-dashboard-api/playlists/{id}/history/{snapshotId}
POST   /apps/tv-dashboard-api/playlists/{id}/history/{snapshotId}/restore
PATCH  /apps/tv-dashboard-api/playlists/{id}
DELETE /apps/tv-dashboard-api/playlists/{id}
GET    /apps/tv-dashboard-api/playlists/{id}/preview-payload
WS     /apps/tv-dashboard-api/playlists/{id}/presentation-ws # refresh + presença no editor
GET    /apps/tv-dashboard-api/playlists/{id}/slides
POST   /apps/tv-dashboard-api/playlists/{id}/slides
PATCH  /apps/tv-dashboard-api/playlists/{id}/slides/{slideId}
DELETE /apps/tv-dashboard-api/playlists/{id}/slides/{slideId}
POST   /apps/tv-dashboard-api/playlists/{id}/slides/reorder
GET    /apps/tv-dashboard-api/playlists/{id}/media          # listar assets (biblioteca)
POST   /apps/tv-dashboard-api/playlists/{id}/media          # upload
GET    /apps/tv-dashboard-api/playlists/{id}/media/{assetId}
GET    /apps/tv-dashboard-api/data/routes
GET    /apps/tv-dashboard-api/data/routes/{operationId}
POST   /apps/tv-dashboard-api/data/preview-block
POST   /apps/tv-dashboard-api/data/m/compile
POST   /apps/tv-dashboard-api/data/m/explain
GET    /apps/tv-dashboard-api/data/m/capabilities
GET    /apps/tv-dashboard-api/data/m/functions
GET    /apps/tv-dashboard-api/content/ui
GET    /apps/tv-dashboard-api/native-screens
```

O histórico consome `PlaylistHistoryEntry` com `authorName`, `authorEmail` e `change`
(`available`, `comparedToRevision`, `playlistFields`, diferenças de slides e `totals`).
Quando `change.available` não existe ou é falso, o painel usa `reason` e `preview` como
fallback compatível com snapshots antigos. O frontend apenas apresenta esse contrato;
o cálculo das diferenças permanece no backend.

### Editor — blocos de dados (slide Personalizado)

| Aba / painel | Função |
|---|---|
| **Inserir → Dados** | Catálogo de rotas GET (`DataRouteCatalogPanel`) → insere `data_source` |
| **Inserir → Gráficos / Tabelas** | Insere `chart_view` ou `table_view` |
| **Elemento → Conexão de dados** | Dropdown **Fonte de dados** (`dataSourceId`) |
| **Elemento → Elementos do gráfico / KPI / tabela** | Visibilidade de partes; com parte selecionada → inspetor da parte |
| **Forma** (ribbon) | Preench./contorno/sombra da **parte** ou mensagem de seleção global |
| **Dados** (painel lateral) | Busca e configuração de parâmetros da fonte |

Atalhos: botão **Abrir fontes de dados** no inspetor; clique na fonte no palco conecta visual selecionado.

---

## Registro no portal

```bash
TOKEN="<jwt com apps.manage>" bash scripts/register-manifest.sh
```

Permissões: `tv-dashboard.read`, `.write`, `.manage`, `.view.filial-*`, `.view.consolidated`.

---

## Build e testes

```bash
npm install
npm run check:css-scope   # gate anti-vazamento CSS (.dashboard-tv-dashboard)
npm test                  # vitest
npm run typecheck         # tsc (tsconfig.build.json)
npm run build             # typecheck + vite build
npm run ci                # circular + css + lint + test + build
```

Docker: contexto `plugins/` (ver `Dockerfile`). Bundled: **`tv-dashboard-presentation`** apenas. **`plugin-ui`** entra via Module Federation (`pluginUiRemote()` + `preparePluginUiRemote()`), sem `COPY plugin-ui`. Container: `delpi-tv-dashboard`.

---

## Deploy

Alterou **só o admin** → rebuild `tv-dashboard` (fase **mfe**).  
Alterou **preview + link público** (`tv-dashboard-presentation` ou view no `public-hub`) → rebuild **`public-hub`** também.  
Alterou **`plugin-ui`** → rebuild remote **antes** dos MFEs consumidores.

```bash
# Preferir scripts sequenciais (evita OOM e garante ordem remote → mfe)
./infra/scripts/up-dev-sequential.sh --fase remote
./infra/scripts/up-dev-sequential.sh --fase mfe
```

Antes do merge (regressão Docker):

```bash
python3 scripts/ci/check_plugin_docker_shared_libraries.py --check
python3 scripts/ci/check_tv_dashboard_css_scope.py --check
bash scripts/ci/build-tv-dashboard.sh
```
