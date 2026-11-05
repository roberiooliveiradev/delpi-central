# Rótulos de dados — eliminação de presets legados e formatação canônica em Número

> **Status: TARGET / PLANNED — autorização de direção de produto, não implementação.**
> **TASK:** TV-CHART-DATA-LABELS-NUMBER-OWNER-001
> **Data:** 2026-11-05
> **Autoridade técnica:** HEAD, Project Instructions, .cursor/rules, TV API + ADR Display Format Ownership, contratos reais.
> **Regras:** owner antes de patch; reuse antes de invention; expand/migrate/verify/contract antes de remover contrato persistido; editor ≡ preview ≡ TV.
> **Decisão de produto:** formatação numérica dos dados tem um só fluxo de autoria, a seção **Número**; atalhos de rótulos oferecem presença e posição; conteúdo (quais dados) é configuração semântica do rótulo, não um formatador numérico alternativo.
> **Não significa:** remover conteúdo categoria/série/valor/% do total, perder configurações de gráficos existentes ou transportar regra de format para React.

## 0. Contexto e reancoragem

Usuário identificou que menu **Adicionar elemento → Rótulos de dados** misturava posição e conteúdo/formato. O PR #139 foi reaplicado à main nos commits d214b30a5d, ac1022367c e adff7b3d6f, removendo quatro opções somente do menu visual. A implementação manteve contratos/presets legados em código e deixou sem superfície explícita a autoria dos quatro modos removidos.

Revalidar antes de mexer: `git rev-parse HEAD`, `git status --short`, regras Cursor, responsibility-map, [README TV](./README.md), [TV API](../../../tv-dashboard-api/README.md), [ADR Display Format Ownership](../../../tv-dashboard-api/docs/architecture/adr-tv-display-format-ownership.md), catálogo de PresentationMutation, playbook de políticas de gráficos, componentes, testes, snapshots/MDD e runtime.

**Snapshot de inventário no HEAD consultado (2026-11-05; HEAD pode avançar):**
- `plugins/tv-dashboard/src/content/chartAddElementMenuCatalog.ts`: flyout de dataLabels contém apenas none/center/insideEnd/outsideEnd/bestFit. A ribbon e toolbar flutuante consomem o mesmo ChartAddElementMenu.
- `plugins/plugin-ui/src/components/charts/seriesChartDataLabels.ts`: `SeriesChartDataLabelsPresetId`, `dataLabelsConfigFromPreset`, `matchDataLabelsPreset` retêm categoryPercent/valuePercent/percent/category, além de opções de posição. O tipo `SeriesChartDataLabelsConfig` modela conteúdo (showCategoryName/showValue/showPercentage/showSeriesName), posição, separador, linhas guia e limiar; **isso não é todo "legado descartável"**.
- `plugins/plugin-ui/src/components/charts/seriesChartAddElementChoices.ts`: `ChartAddElementChoiceId` e `DATA_LABEL_CHOICE_PRESET` retêm quatro IDs; `applyDataLabelsChoice` chama `dataLabelsConfigFromPreset` e substitui `base.dataLabels` integralmente ao aplicar posição. Isso pode resetar o conteúdo, separador, limiar etc. em gráficos personalizados.
- `plugins/tv-dashboard/src/components/selectionSections/NumberFormatSection.tsx`: fluxo UI canônico de DisplayFormatSpec/preview. `displayFormatSelection.ts`: no chart_view mira `chartCategory` se eixo X selecionado, ou `chartValue` em outros contextos. Precisa provar a semântica de escopo quando a parte "rótulos de dados" estiver selecionada; não presumir format exclusivo de rótulo.
- `plugins/tv-dashboard/src/components/ChartPartInspector.tsx`: não foi localizado picker equivalente para showCategoryName/showValue/showPercentage/showSeriesName no trecho inventariado; pesquisar outros consumidores e inspeção runtime antes de concluir ausência global.
- `plugins/plugin-ui/src/components/charts/seriesChartDataLabels.ts`: `formatSeriesChartDataLabelText` possui fallback de formatação no cliente, e `showPercentage` deriva `Math.round(abs(value)/total*100)`. Auditar relação com a projeção servidor/ADR: não ampliar formatação semântica paralela no paint; backend é owner para dados resolvidos.
- `tv-dashboard-api/tv_app/application/services/data/display_format_service.py`: entrega display series/label e formatação canônica. Inventariar se percentual-de-total e composições dos data labels já são materializados em contrato pronto-para-pintar.
- Os quatro IDs removed do flyout ainda são válidos no código de presets. **Não há prova de que nunca aparecem em MDD, histórico, templates, snapshots ou consumidores externos; inventariar antes de apagar.**

## 1. Modelo de responsabilidades alvo

| Dimensão | Única UI de autoria / owner | Semântica |
|---|---|---|
| Presença de rótulos | Elementos do gráfico | ligar/desligar sem apagar dados |
| Posição dos rótulos | Atalho flutuante e seção de layout/parte | center/insideEnd/outsideEnd/bestFit; alterar somente position/leader lines quando necessário e contratado |
| Conteúdo dos rótulos | **Configuração de conteúdo do subitem Rótulos de dados** | mostrar categoria, valor, nome da série, participação no total; separador, visibilidade; sem formatter duplicado |
| Formatação dos valores | **Seção Número (único autor de formato)** | formato, escala, locale, percentual, moeda, precisão, unidade, exibição personalizada, fallback |
| Materialização dos valores dinâmicos | **tv-dashboard-api**, conforme ADR e owner real | numeração pronta para pintura, percent-of-total tipado, diagnostics |
| Layout/render | motor compartilhado `tv-dashboard-presentation` + kit de gráficos | compor parts prontos, sem reformatar quando backend já aplicou exibição |
| MDD/import e persistência | owner de contrato TV e PresentationMutation | preservar opções/migração/versionamento, sem valores runtime |

**Distinguir:** escolher mostrar *participação percentual no total* é seleção do conteúdo, não a mesma operação que formatar um número como percentual. A representação "94,39%" no label deve usar o formatter canônico do valor resolved; a grandeza % do total precisa respeitar semântica definida no backend. Rótulo pode conter múltiplos tokens, mas não criar template arbitrário no browser.

## 2. Contratos: manter, substituir, eliminar

### Manter como capacidade semântica (não deletar)

- `showDataLabels`, posição e partes `chartParts`.
- Conteúdo campo/flag: categoria/valor/série/% do total (se usados por produto).
- Preservação das opções persistidas `chartOptions.dataLabels` até existir migração validada, com controle tipado.
- `DisplayFormatSpec` e owner backend/ADR.
- IDs de campo/modelo, configs de tipo, unidades e resultados de enriquecimento.
- Paridade editor/preview/TV, dados autorizados/filial.

### Contratos legados candidatos a remoção APÓS inventário

- `SeriesChartDataLabelsPresetId` como união que mistura posições e modos de conteúdo.
- `dataLabelsConfigFromPreset` e `matchDataLabelsPreset` quando os consumidores forem migrados para operação explícita de presença/posição e configuração de conteúdo.
- Quatro `ChartAddElementChoiceId` legados `dataLabels:categoryPercent`, `dataLabels:valuePercent`, `dataLabels:percent`, `dataLabels:category`.
- `DATA_LABEL_CHOICE_PRESET` e branches switch para esses IDs.
- Formatação percentual ad hoc no paint somente quando owner backend e equivalência de output estiverem provados.
- Helpers/formatters de número redundantes, apenas após rastreamento de consumidores e testes.

**Importante:** um ID de preset transitório não é automaticamente um campo persistido. Remover o ID da API TypeScript de editor pode ser fácil; remover flags/valores persistidos e lógica de apresentação pode ser BREAKING. Classificar cada família (DEPRECATED/BEHAVIORAL/BREAKING), sem reconciliação implícita.

## 3. Lacuna adicional comprovada: posição pode apagar conteúdo

Caminho atual:

~~~text
dataLabels:outsideEnd
  → applyDataLabelsChoice
    → dataLabelsConfigFromPreset
      → { showDataLabels:true, dataLabels: next.dataLabels }
        → substitui propriedades customizadas anteriores
~~~

**TARGET:** uma mudança de posição deve fazer patch **somente** na posição e propriedades correlatas explicitamente governadas (ex.: leaderLines se semântica provar necessidade). Nunca zerar `showCategoryName`, `showValue`, `showPercentage`, `showSeriesName`, `separator`, `hideBelowPercent`, `colorFromCategory` sem ação autoral explícita. Desligar deve preservar config. Estado ativo do atalho deve derivar de posição/presença e não exigir coincidência de um preset completo.

Esse bug deve ter teste de regressão prévio e pós-fix com configuração mista/custom.

## 4. UI alvo — wireframes de autoria

### Rótulos de dados no menu rápido

~~~text
Adicionar elemento → Rótulos de dados
  Nenhum
  Centro
  Dentro da extremidade
  Fora da extremidade
  Melhor ajuste
  Mais opções de rótulos de dados…
~~~

### Inspector da parte (conteúdo e presença, não formatter)

~~~text
Parte: Rótulos de dados
  [x] Mostrar
  Conteúdo do rótulo
    [x] Valor
    [ ] Categoria
    [ ] Nome da série
    [ ] % do total
  Separador: [Espaço v]
  Posição: [Fora da extremidade v]
  Linhas guia: [x]
  [Número: editar formato dos valores]  ← navega/reusa seção Número
~~~

Decidir se a UI mostra "Número" contextual sem duplicar os controles de format. O usuário pode selecionar a parte e usar a seção Número existente; não criar panel de Number dentro do inspector.

### Número — único picker de formato

~~~text
Formatar gráfico → Número
  Alvo: [Valores da série / Rótulos de dados / Categoria quando aplicável]
  Formato: [Número / Percentual / Moeda / Data / Geral]
  Casas decimais: [...]
  Localidade / separador / unidade / preset personalizado
  Prévia de backend: [...]
~~~

Esse wireframe é conceitual; reutilizar `NumberFormatSection`/`DisplayFormatRibbonGroup` já existentes e comprovar a política do alvo. Não inventar um segundo formatter ou produzir alteração global indevida quando rótulos estiverem selecionados.

## 5. Entregas condicionadas E0–E6

- **E0 — Inventário/Gate sem patch:** HEAD/status, refs/consumidores, tipagem, serializers, catalog, conteúdo UI, chart parts, backend formatting, MDD/templates/históricos/playlists e modos de gráfico; classificar `EXISTING_EQUIVALENT`, `REUSE_DECISION`, contratos e dados em uso. STOP para conflitos não resolvidos.
- **E1 — Desacoplar posição de conteúdo:** corrigir apply choice, isActive e preserving config; tests target + sibling + negative; mesmo menu compartilhado; sem mudança de formato. Não remover presets antes disso.
- **E2 — Completar autoria de conteúdo:** campos semânticos no inspector da parte, preservar edição e ocultar/mostrar, add/remove, F5, history e MDD. Reusar capacidade de parts e DataModel; nenhuma propriedade deve desaparecer por mudança de posição.
- **E3 — Único formatter:** assegurar `NumberFormatSection` como única UI de formatação numérica; backend valida e materializa os textos, incluindo percentual total se for grandeza real; não adicionar formatter no MFE. Provar escopo chartValue/chartCategory/dataLabels; testes cross-variant.
- **E4 — Deprecar e eliminar legado:** após inventário de todos os consumidores, substituir referências ao preset heterogêneo por ações tipadas de posição ou conteúdo; eliminar quatro choice IDs e helpers mortos. Para persistidos, migrar via expand→migrate→verify→contract com schema/versionamento aprovado; não "deletar e esperar fallback". Residual search não pode encontrar chamadas executáveis legadas.
- **E5 — Testes e paridade:** chart types linha, barra, área, pizza, funil, radar, gauge conforme aplicabilidade; casos label único/múltiplos, percent, 0/null, datasets filtrados, séries ocultas, label longo, formatação de R$ e %, gráfico antigo, MDD round-trip, screenshot editor=preview=TV. Não fabricar valores ou percentuais no paint pós-enrich.
- **E6 — Deploy controlado:** commits + push + build/tests/CI e gates oficiais, rollout de serviços realmente afetados (tv-dashboard, plugin-ui, package compartilhado, public-hub, tv-dashboard-api somente se mudar), SHA real, compatibilidade mixed-version e rollback, pixel pós-deploy. Deployment **não** pode prosseguir com gate crítico vermelho sem decisão de responsabilidade e solução aprovada.

**Critério de entrada E4:** E0–E3 PASS, sem owner conflitante e com migração de configurações antigas comprovada. Nunca remover antes de recuperar a funcionalidade equivalente na UI e preservar o que o usuário salvou.

## 6. Matriz de aceite essencial

| Caso | Resultado |
|---|---|
| Gráfico salvo como categoria+% | continua apresentando mesmo conteúdo |
| Clique "Centro" após categoria+% | **somente posição** muda; categoria e % permanecem |
| Mostrar/ocultar label | não apaga campos/config |
| Conteúdo: valor+categoria+% do total | pode ser composto sem preset legado |
| Número: alterar decimais | somente a semântica de formato definida para o alvo muda |
| Número: alterar percentual | valor exibido utiliza formatter do backend, não JS ad hoc |
| Formatar ≠ conteúdo | selecionar % do total não muda por si só unidade da métrica |
| Serie/lenda/categoria | nenhum modo perde rótulo por inércia |
| Ausência/zero/divisão por zero | zero ≠ ausência; output sem NaN/Infinity |
| Legacy snapshot / MDD | round-trip e render sem perda |
| Novos gráficos | sem comando legacy exposto |
| Testes de contratos | nenhuma referência executável a presets retirados, salvo adaptador de migração transitório com retirada agendada |
| Paridade | editor, preview e TV mostram mesmo label com mesmo payload/revisão |

## 7. Checklist de execução, gates e evidência

~~~text
GOAL: centralizar formatação de dados em Número sem remover conteúdo útil.
OWNER: TV API (format/data) + MFE (UX) + presentation package e plugin-ui (part/paint).
AUTHORITIES: HEAD → rules → ADR → API → code → tests → runtime.
CURRENT FACTS: como §0 (revalidar).
ROOT CAUSE: preset inteiro substitui dataLabels em mudança de posição; outros gaps a inventariar.
EXISTING_EQUIVALENT: YES (DisplayFormatSpec, Número, dataLabels config, part selection).
REUSE_DECISION: EXTEND/REUSE, sem novo formatter.
ALLOWED: mudanças nos owners reais e seus contratos, testes, docs, deploy após gates.
FORBIDDEN: apagar configuração persistida, 2º formatter, duplicação de catálogo, hotfix de TV, bypass RBAC/MDD.
SECURITY: Core RBAC/resource/filial backend-first; nenhum dado exposto por config de UI.
TESTS: positive+sibling+negative + parity + roundtrip + runtime.
ACCEPTANCE: matriz §6.
STOP: quebra sem migração; campos de conteúdo sem UI; ausência de formatter canônico; mixed versions incompatíveis.
EVIDENCE: VISTA/TV EXECUTION REPORT (SHA, arquivos, contratos, diffs, consumidores, CI, deploy, screenshots, gaps).
~~~

**Estado na criação:** inventário parcial com cause de perda de conteúdo PROVEN no código. Migração completa, consumidores externos, output porcentagem no backend, execução CI e deploy **TO_INVENTORY / TEST_NOT_RUN**.

**Decisão final:** remover legados depois de assegurar autoria/format em seus respectivos owners. Um simples `grep -R` limpo não é prova de que dados persistidos e experiências de usuários foram preservados.
