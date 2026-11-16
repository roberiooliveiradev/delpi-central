# EVA / Routing — Component Map V1 (source-backed)

**Estado:** `PROVEN_EXPORT / TARGET_COMPOSITION / IMPLEMENTATION_PENDING`.  
**Fontes inspecionadas (2026-11-16):** `plugins/engineering/src/ui/engineeringUi.ts`, `plugins/engineering/src/features/products/routing/ProductRoutingTab.tsx`, `plugins/plugin-ui/src/index.ts`, `plugins/plugin-ui/docs/component-catalog.md`, Doc 61, Doc 126.  
**Regra:** distinguir `PROVEN_EXPORT`, `PROVEN_USAGE`, `TARGET` e `TO_INVENTORY`. Um export real não prova adequação da composição visual desejada.

## 1. Mapa decisório

| ID | Papel/área | Componente exportado/comprovado | Fonte/consumer | Decisão e estado |
|---|---|---|---|---|
| C01 | Cabeçalho da ficha | `EngineeringPageHero` | `engineeringUi.ts` / `ProductDetailPage.tsx` | **REUSE** hero existente, não renderizar segundo hero na aba — PROVEN_USAGE |
| C02 | Cartão de seção | `EngineeringSectionCard` ou `EngineeringDetailCard` | façade `createDashboardSectionCard` / `createDashboardDetailCard` | **REUSE** um shell por intenção, sem duplo contorno — PROVEN_EXPORT |
| C03 | Navegação interna | `EngineeringTabs` (`createDashboardUnderlineNav`) | façade | **REUSE**, mode=tabs quando aplicável; verificar props e foco — PROVEN_EXPORT |
| C04 | KPI | `EngineeringKpiCard` (`createDashboardKpiCard`) | façade / `ProductRoutingTab.tsx` | **REUSE** quatro cards com density compacta; verificar variant/props reais — PROVEN_USAGE |
| C05 | Filial/estágio | `EngineeringFiltersRow` + `EngineeringFilterSelect`, ou `EngineeringSelectField` | façade / routing | **REUSE**, compactar layout sem perder ação de troca — PROVEN_USAGE |
| C06 | Chip contextual | `EngineeringStatusBadge` ou `EngineeringScopeChipBar` | façade | **OPTIONAL**, não substituir seletor por badge estático — PROVEN_EXPORT |
| C07 | Lista de operações | `EngineeringInteractiveDataCard` | `plugins/plugin-ui/src/components/data/InteractiveDataCard.tsx`; façade `createDashboardInteractiveDataCard` | **COMPOSE** — campos-resumo via `EngineeringDetailFieldGrid` dentro de `children`; `DataTable` proibida como layout primário. Implementado em `OperationCard` — PROVEN_USAGE |
| C08 | Expansão/accordion | `EngineeringInteractiveDataCard` (`onActivate`/`openHint`, `role="button"`, Enter/Space, `aria-label`) | `InteractiveDataCard.tsx` — interação nativa do kit | **COMPOSE** — estado `expanded` é da feature; chrome, foco e teclado do kit — PROVEN_USAGE |
| C09 | Detalhes de operação | `EngineeringDetailFieldGrid` | façade `createDashboardDetailFieldGrid` | **REUSE**, mostrar atributos presentes/prioritários e honestidade dos ausentes — PROVEN_EXPORT |
| C10 | Componentes vinculados | Lista compacta (`<ul>` de texto) dentro do card expandido | `OperationDetail` — poucos itens não justificam densidade tabular | **REUSE/COMPOSE** — sem `DataTable` aninhada |
| C11 | Formulário | `EngineeringTextField`, `EngineeringFormFieldShell`, `EngineeringFieldLabel`, `EngineeringFormActions` | façade `createDashboardNativeFormFields` | **REUSE** 3+2 campos, resumo e CTA — PROVEN_EXPORT |
| C12 | Ações | `EngineeringActionButton`, `EngineeringIconButton` | façade | **REUSE** — PROVEN_EXPORT |
| C13 | Feedback/loading | `EngineeringStateBanner`, `EngineeringEmptyState`, `EngineeringLoadingActivityCard` | façade | **REUSE**, erros vs zero dados — PROVEN_EXPORT |
| C14 | Fonte/status | `EngineeringStatusBadge` | façade | **REUSE** status CALCULATED/PROVIDED/SIMULATION somente com dados pertinentes — PROVEN_EXPORT |
| C15 | Contêiner gráfico | `EngineeringChartCard` | façade | **REUSE se gráfico agregar valor**, chrome não determina o renderer — PROVEN_EXPORT |
| C16 | Renderer gráfico | `ConfigurableSeriesChart` | `ProductRoutingTab.tsx` (`ThemedSeriesChart`) | **REUSE** — tema/`backgroundColor` (token `--en-surface`)/`decimalPlaces`/unidade `s`/`polarity: high_is_bad` resolvem paridade claro/escuro e escala; evidência visual e2e nos dois temas — PROVEN_USAGE |
| C17 | Gráfico com uma operação | Card de métrica/detalhe nativo | C02/C04 | **TARGET** visual sintético em lugar de gráfico solitário; sem nova biblioteca |
| C18 | Comparação de cenários | Cards nativos C02/C04, tabela compartilhada sob condição | façade / catálogo | **TARGET** cards até cenários suportados, tabela apenas se dados/legibilidade justificarem |
| C19 | Estados de tabela densa | `DataTable` + wrapper da feature | `features/products/components/dataTableUi.ts` (verificar caminho real), `ProductRoutingTab.tsx` | **RETAIN ONLY where truly tabular**; não usar na operação primária — PROVEN_USAGE |
| C20 | Tema | tokens `--delpi-ui-*` e theme provider/host | `plugins/plugin-ui/docs/architecture.md`, `usePortalTheme` local | **REUSE**, contrastar plot e controles nos dois temas; nenhuma paleta hardcoded |

### Lacunas registradas (2026-11-16)

- **PLUGIN_UI_GAP C08a — `aria-expanded` ausente em `InteractiveDataCard`:** o card interativo expõe `role="button"` + teclado, mas não aceita `ariaExpanded`/estado de disclosure. Mitigação aplicada na feature: `ariaLabel` inclui "— expandida" quando aberto. Correção correta é no owner `@delpi/plugin-ui` (prop `ariaExpanded?: boolean` no `<article>`), não wrapper local.

## 2. Gates de escolha de componente (antes do JSX)

Para C07/C08/C10/C16, registrar em tabela de implementação:

```text
UI_ID:
Intenção visual:
Candidate export + path:
Props que viabilizam composição:
Consumer real que utiliza:
Screenshot de referência do componente:
Comportamento dark/light:
Responsividade / teclado:
Decision: REUSE | COMPOSE | PLUGIN_UI_GAP
Limitações / testes:
```

`COMPOSE` permite layout/painel da feature e handlers de domínio, **não** reescrever chrome de botões, inputs, cards e expansores. `PLUGIN_UI_GAP` exige Abstraction Gate e avaliação owner, nunca import privado de outro MFE.

## 3. Escolha dos gráficos — inventário obrigatório

O catálogo confirma `ChartCard` e `ConfigurableSeriesChart`, mas **não comprova que são a combinação visual desejada**. O executor deve:

1. Selecionar pelo menos duas telas referência com gráficos considerados adequados, preferindo Visão Geral Engenharia e dashboards corporativos.
2. Localizar no código o renderer gráfico, factory, props e tokens.
3. Registrar screenshot do componente em dark e light.
4. Testar com 1 operação e com múltiplas operações, valores `0,0012 min` e `0,06 min`, meta takt.
5. Optar por renderer oficial comprovado ou registrar `PLUGIN_UI_GAP`; evitar criação de gráfico local paralelo.

**GATE:** sem esta evidência, C16 é `TO_INVENTORY` e não pode ser apresentado como componente gráfico aprovado.

## 4. Fontes navegáveis

- [Façade Engineering](../../../../../plugins/engineering/src/ui/engineeringUi.ts)
- [Aba Roteiro atual](../../../../../plugins/engineering/src/features/products/routing/ProductRoutingTab.tsx)
- [Plugin UI catálogo](../../../../../plugins/plugin-ui/docs/component-catalog.md)
- [Plugin UI exports](../../../../../plugins/plugin-ui/src/index.ts)

Nota: os caminhos relativos acima são auxiliares; paths GitHub absolutos prevalecem se links relativos forem refatorados.
