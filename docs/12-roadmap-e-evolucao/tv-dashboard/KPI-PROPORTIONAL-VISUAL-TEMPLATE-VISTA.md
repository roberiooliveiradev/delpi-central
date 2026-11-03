# KPI proporcional para TV — template visual, wireframes e contrato-alvo da VISTA

> **Status:** **TARGET / PLANNED**, especificação de design aprovada conceitualmente em 2026-11-03; **NÃO IMPLEMENTADO por este documento**.  
> **Base de inventário:** \`origin/main\` em \`f1a0a67ab08dcdb4cc650502a46c226125dcbd43\` (revalidar no HEAD da implementação).  
> **Escopo:** evolução do componente **existente** \`DelpiKpiCard\` e do uso por \`kpi_view\` / VISTA no TV Dashboard.  
> **Relacionados:** [Playbook KPI Card](./PLAYBOOK-KPI-CARD.md) · [VISTA design intelligence inventory](./vista-semantic-tools-refactoring/27-di0-design-intelligence-inventory.md) · [Issue #129](https://github.com/roberiooliveiradev/delpi-central/issues/129) · [Catálogo plugin-ui](../../../plugins/plugin-ui/docs/component-catalog.md) · [ADR formatação](../../../tv-dashboard-api/docs/architecture/adr-tv-display-format-ownership.md).

## 1. Propósito e limites da referência visual

Esta especificação registra a proposta visual validada conceitualmente: **KPI com valor dominante, ícone expressivo, unidade incorporada no valor, contexto secundário e dimensionamento proporcional ao CARD**, em linguagem visual DELPI de alto contraste para TVs. A imagem apresentada pelo solicitante é **referência de intenção visual, não um PNG de execução nem contrato de pixel exato**.

O layout deve funcionar de um card compacto dentro de uma grade a um destaque Hero, sem assumir que todos têm a mesma largura, fonte ou número de caracteres. As proporções adiante são **faixas iniciais de design para prototipação** e não thresholds aceitos ou números fixos a codificar no backend.

**Não alterar o slide LAB** apenas por criar esta documentação; não criar novo renderer, novo componente KPI, outra fonte de dado, formatter no frontend, authority de mutação na VISTA ou GPT Action.

### 1.1 Antes → depois pretendido

| Problema observado no screenshot real da revisão 16 do LAB | Resultado-alvo |
|---|---|
| Número 93,73 sem símbolo; rótulo \`OEE realizado (%)\` | Título \`OEE realizado\`; **93,73% no VALOR** |
| Valor ocupa fração pequena do card | Número é foco visual, com auto-fit e limites de legibilidade |
| Ícone Gauge minúsculo e pouco expressivo | Box/glyph dimensionados proporcionalmente; ícone semanticamente escolhido |
| Informação no topo com muito espaço morto | Distribuição clara: título → valor → comparação/contexto, com equilíbrio vertical |
| Quatro KPIs com aparência idêntica | Papel semântico define Hero / Standard / Meta, preservando edição manual |
| Estado \`Atualizando...\` encobre o card | Refresh informativo, não compromete leitura do último dado válido |
| \`VERIFIED\` estrutural não vê tipografia pequena | Captura \`editor_live\` + revisão pixel-based e recaptura quando possível |

## 2. Wireframes detalhados (especificação textual)

Os diagramas são **wireframes, não segundo renderer**. O card real continua \`KpiViewBlockView → DelpiKpiCard\` no palco compartilhado.

### 2.1 HERO — indicador primário, expandido (referência)

\`\`\`text
┌────────────────────────────────────────────────────────────────┐
│                                                                │
│  ┌────────────────┐  │  OEE realizado                            │
│  │                │  │                                           │
│  │  ÍCONE GRANDE  │  │  93,73%                                   │
│  │  GEAR / GAUGE  │  │  VALOR DOMINANTE + UNIDADE NO VALOR       │
│  │                │  │                                           │
│  └────────────────┘  │  [ ↑ +8,73 p.p. vs meta ]                 │
│                      │  [ calendário ] Últimos 30 dias           │
│                                                                │
└────────────────────────────────────────────────────────────────┘
    ↑ box do ícone com presença       ↑ leitura rápida à distância
\`\`\`

**Ordem visual:** indicador → valor principal → comparação vs meta/período → recorte temporal. O rótulo é estável e curto; \`%\` pertence a \`displayValue\`, não ao texto do título. A comparação de pontos percentuais (\`p.p.\`) é semanticamente distinta de variação relativa em \`%\`; não inferir uma da outra sem dados e regra oficial.

**Distribuição inicial:** box do ícone 20–28% da largura útil, região de conteúdo restante; gap ícone/conteúdo 4–6% do card; padding 6–10%. O maior valor deve ganhar largura suficiente antes de permitir que o ícone cresça. Separador vertical é opcional e visual; não exige outra part.

### 2.2 STANDARD — destaque intermediário / visão em grade

\`\`\`text
┌───────────────────────────────────────────────────┐
│ ┌─────────┐ │ Horas improdutivas                   │
│ │  CLOCK  │ │ 12,4 h                              │
│ │  ÍCONE  │ │ [ ↓ -6,2% vs período anterior ]     │
│ └─────────┘ │                                    │
└───────────────────────────────────────────────────┘
\`\`\`

Ícone expressivo, mas inferior ao Hero; número deve continuar dominante. A unidade \`h\` acompanha o valor. Na redução de espaço, simplificar texto auxiliar primeiro, **não** truncar o número nem esconder o significado da unidade. Sem série/variação oficial, omitir comparação em vez de inventar.

### 2.3 META / TARGET — indicador de referência

\`\`\`text
┌───────────────────────────────────────────────────┐
│ ┌─────────┐ │ Meta OEE                             │
│ │ TARGET  │ │ 85,00%                               │
│ │  ÍCONE  │ │ [ Meta oficial ]                     │
│ └─────────┘ │                                    │
└───────────────────────────────────────────────────┘
\`\`\`

A meta **não é realizado**: identidade semântica explícita, sem indicação verde/vermelha de desempenho caso não exista realizado comparável. Contexto \`Meta oficial\` só quando procedência e período forem confirmados. A meta pode ter tom neutro/azul; status de atingimento exige comparação legítima.

### 2.4 COMPACTO — largura restrita ou muitas colunas

\`\`\`text
┌─────────────────────────────┐
│ [icon] OEE Filial 01        │
│        95,89%               │
│        Últimos 30 dias      │
└─────────────────────────────┘
\`\`\`

Quando a largura ou altura cai, reduzir box do ícone e densidade do contexto de forma **progressiva**; reflow para topo/linha conforme a geometria. O valor permanece legível, com unidade e sem clipping. Evitar colocar metas, sparklines, badges e labels simultaneamente num card estreito.

### 2.5 Estados que também exigem wireframe e QA

\`\`\`text
CARREGANDO / REFRESH:             SEM DADO / ERRO:
┌────────────────────────┐        ┌────────────────────────┐
│ OEE realizado   [↻]    │        │ OEE realizado          │
│ 93,73%                 │        │ —                      │
│ Atualizando (discreto) │        │ Fonte indisponível     │
└────────────────────────┘        └────────────────────────┘
\`\`\`

Manter o último valor válido em refresh se o contrato permitir; não aplicar overlay que torne texto ilegível. Em erro/vazio, NÃO exibir \`0%\` fictício; a diferença entre \`0\` e \`null\` é obrigatória. Inspecionar também loading prolongado, dados stale, conteúdo de alta precisão e contrastes claro/escuro.

## 3. Anatomia, proporções e comportamento dinâmico

| Parte existente | Faixa visual inicial **TARGET**, não valor codificado | Regras de adaptação |
|---|---|---|
| \`title\` | Região ~16–20% da altura útil (referência) | Label com 1–2 linhas; truncamento só com regra de contexto/tooltip quando aceitável na TV |
| \`value\` | Região ~36–52% da altura útil (referência) | Maior prioridade; ajustar ao texto **e** caixa; considerar separador decimal, sinal, unidade, valores extremos |
| \`hint/comparison\` | Região ~10–14% da altura útil | Mostrar apenas se houver dado e espaço; \`p.p.\` vs \`%\` corretos |
| \`icon\` | Box ~20–28% da largura útil em Hero, adaptável nas demais variantes | **Glyph** suficientemente visível dentro do box; não confundir \`iconSize\` do box com tamanho do SVG |
| \`card\` | Padding interno ~6–10%, gap ícone-conteúdo ~4–6% | Proporcional, mas com limites de acessibilidade/overflow; preservar bordas e foco do editor |
| Espaço entre título / valor / apoio | Referência ~2–4% da dimensão relevante | Não distribuir percentuais isolados que ultrapassem 100%; resolver via geometria efetiva |

**As faixas não devem ser aplicadas mecanicamente em CSS**: calcular disponibilidade (largura/altura reais do card e bounding boxes das partes), conteúdo e modo de uso. Avaliar geometria da fonte no palco 1920×1080 **e na escala de exibição real**. Tamanho mínimo aceitável é uma decisão de teste perceptual, não uma constante inventada nesta especificação.

### 3.1 Algoritmo-alvo de adaptação (comportamento; sem código novo exigido aqui)

1. **Receber layout/parts persistidos**: manual \`typographyMode=fixed\` e \`frame\` explícitos prevalecem e não devem ser reescritos por auto.
2. **Ler geometria disponível** depois do layout e escala do stage; calcular áreas de \`title\`, \`value\`, \`icon\`, \`hint/comparison\` com as capabilities já existentes.
3. **Escolher variante semântica** \`hero\`, \`row\` ou \`scorecard\` conforme prioridade, função e dimensão; não apenas a altura do card.
4. **Distribuir espaço** primeiro ao valor e sua unidade, depois à identificação, ícone e contexto. A proporção do ícone deve levar em conta o glyph SVG (~58% do box no CSS atual — hipótese de ajuste no kit).
5. **Adaptar fontes** com \`FitText\` / \`typographyMode:auto\` nos casos previstos; diagnosticar a dependência atual de \`valueFramed\` que impede auto-fit em alguns cards. Não destruir o modo fixed nem introduzir oscilação de ResizeObserver.
6. **Verificar legibilidade/clipping/overlap** no DOM e no PNG canônico; reduzir elementos acessórios ou reflow antes de reduzir indefinidamente o valor.
7. **Preservar preferências do usuário** e registros legacy, \`kpiParts\` e \`kpiOptions\`. Nenhuma migração silenciosa de geometria.

### 3.2 Casos de stress e restrições

- Valor \`1.234.567,89\`, \`-123,45%\`, \`0,00%\`, \`100,00%\`, \`R$ 1,2 mi\`, \`12,4 h\`, \`—\`; idioma PT-BR e NBSP/símbolo correto.
- Comparação \`+8,73 p.p.\` versus \`-6,2%\` temporal; não unir unidades equivocadamente.
- Altura baixa/largura alta; largura baixa/altura alta; grid 4 KPIs; card Hero isolado; zoom/TV 1080p; dark/light.
- Ícone desabilitado, SVG sem frame, box sem proporção, iconSize alto e contraste insuficiente.
- Metas sem realizado, realização sem meta, ausência de dados, dados stale e refresh concorrente.
- \`kpiProjection.metrics\` com múltiplas métricas e escolha individual de formatos.

## 4. Mapa de owners, contratos e equivalências

| Necessidade | Owner atual / caminho real | Estado |
|---|---|---|
| Card compartilhado, layout, estilos e glyph | \`plugins/plugin-ui/src/components/layout/DelpiKpiCard.tsx\`, \`kpiCardParts.ts\`, \`FitText.tsx\`, \`plugins/plugin-ui/src/styles/kpi-card.css\` | **PROVEN** |
| Render do \`kpi_view\` para editor/preview/TV | \`plugins/tv-dashboard-presentation/src/kpiViewBlockView.tsx\` → \`DelpiKpiCard\` | **PROVEN** |
| Variantes declaradas \`hero/row/scorecard\` e parts | \`kpiOptions\`, \`kpiParts\`, \`KPI_LAYOUT_PRESET_FRAMES\` | **PROVEN**, qualidade-alvo pendente |
| Métricas/bindings/format spec | \`kpiProjection.metrics[].format/displayFormat/decimalPlaces\` | **PROVEN** |
| Materialização de \`kpi.displayValue\` | \`tv-dashboard-api\` / \`DisplayFormatService\` + enrichment; ADR de ownership | **PROVEN** |
| Controles de edição de KPI | \`plugins/tv-dashboard/src/components/KpiPartTypographyFields.tsx\`, \`KpiViewOptionsInspector.tsx\`, \`KpiMetricsProjectionEditor.tsx\` | **PROVEN** |
| Decisão de composição VISTA | \`tv-dashboard-api/tv_app/content/design_intelligence.json\`, \`vista_agent_intelligence.json\`, recipes existentes | **PROVEN** como superfície; nova política **TARGET** |
| Inspeção de pixels | VISTA MCP \`read(... includePreview=true)\` + \`ImageContent\` \`editor_live\` | **PROVEN** na sessão multimodal anterior; host E2E automático **TO_INVENTORY** |
| Mutação de KPI | PresentationMutation typed ops → backend fresh RBAC + recurso + proposal | **PROVEN**; contrato adicional **não presumido** |

**EXISTING_EQUIVALENT=YES** para card, parts, styles, format, recipes, visual capture e mutation.  
**REUSE_DECISION=EXTEND**, condicionado a inventário de contrato. Não criar outro \`KpiCardV2\` nem CSS paralelo no MFE. O \`plugin-ui\` é owner do CSS do componente; \`tv-dashboard-api\` é owner de formatação, domínio e políticas de proposta; \`tv-dashboard-presentation\` pinta e reusa o kit; VISTA não vira autoridade concorrente.

### 4.1 Contratos-alvo — candidatos a validar antes do diff

- **Dimensionamento:** esclarecer semanticamente \`typographyMode:auto|fixed\`, \`fontSize\`, \`frame\` de cada part e auto-fit sem frame; alvo é proporcional ao card, não pixels fixos que só parecem funcionar em um viewport.
- **Ícone:** distinguir tamanho do box, área útil do SVG e visibilidade. Aproveitar \`kpiParts.icon.style.iconSize\` / \`frame\` existentes; qualquer metadado novo só após provar que os campos atuais são insuficientes.
- **Valor/unidade:** usar \`displayFormat\`/format preset existente com \`percent\`/currency/number/time de acordo com campo e escala reais; \`displayValue\` vem do backend. **Não** colocar \`(%)\` no título para compensar formato incorreto; **não** multiplicar 93,73 por 100 ou assumir ratio 0–1.
- **Papel visual:** conectar semântica já presente em receitas \`hero/row/scorecard\` ao layout escolhido, distinguindo valor realizado de meta e atual vs período anterior. Metadado novo só se \`design_intelligence\`/recipe/ops não permitirem a seleção necessária.
- **Gates:** estrutural \`layoutGatePassed\` não substitui leitura dos pixels. \`VISUAL_PENDING\` se PNG de mesmo slide/revision não chegar; não declarar \`VISUAL_PASS\` com preview esquemático.
- **Compatibilidade:** \`kpiParts\` manual, legado sem \`frame\`, \`kpiOptions\`, \`kpiProjection\`, \`serverProjectionApplied\`, \`serverDisplayApplied\`, compactação MCP/Actions, e todos os consumidores do kit.

**CONTRACT IMPACT = TO_INVENTORY.** Esta especificação é de produto/design; qualquer mudança de schema, persistência ou mutation op exige primeiro análise de compatibilidade e testes de round-trip.

## 5. Política-alvo de uso pela VISTA

A VISTA deve entender **o que o número significa**, **como formatá-lo** e **qual papel visual ele merece**.

1. Identificar \`realized | target | trend | secondary\` como papel semântico (não criar enum/API nova antes de inventariar receitas).
2. Ler metadata da fonte: medida, unidade, escala, sinal, período, escopo/filial, comparação e confiança.
3. Escolher \`hero\` para principal, \`scorecard\` para meta, \`row\`/compacto para secundários, conforme **quantidade e geometria dos KPIs**; evitar uma receita uniforme.
4. Selecionar ícone semanticamente coerente (Gauge/Clock/Target etc.) **se disponível e permitido**; garantir presença visual sem competir com o valor.
5. Persistir **format spec do valor** via typed ops permitidas, sem editar label para simular unidade. Confirmar \`kpi.displayValue\` no enrich / authoritative read-back.
6. Propor frames/parts e auto-fit só dentro dos campos realmente writeable; não inventar props ou handles.
7. Depois do COMMIT autorizado, solicitar PNG \`editor_live\` revision-bound, inspecionar legibilidade, proporção valor/ícone, símbolo/unidade, clipping, loading e contraste, e propor refinamento mínimo via PREPARE/CONFIRM/COMMIT (quando exigido).
8. Limitar iterações, respeitar conteúdo manual, pedir autorização quando necessário e recapturar. Sem PNG/model pixels: \`VISUAL_PENDING\`, nunca sucesso visual presumido.

### 5.1 Perguntas que a VISTA precisa responder pelo print

- A pessoa lendo a TV identifica **valor + unidade** à distância?
- O valor é visualmente dominante sem cortar número ou percentual?
- O ícone comunica o indicador e está realmente visível, ou ficou minúsculo dentro do box?
- Os quatro KPIs formam uma hierarquia, e não quatro cards clones?
- Meta e realizado estão distinguidos? \`+8,73 p.p.\` foi calculado com as grandezas corretas?
- Refresh, erro e estados vazios preservam legibilidade?
- O que está salvo, o que o editor mostra, o que o preview mostra e o que a TV mostra têm paridade?

## 6. Plano de implementação futuro (sem autorização implícita)

| Fase | Entrega | Evidência obrigatória |
|---|---|---|
| K0 — inventário de owner | Ler HEAD, rules/responsibility-map, playbook KPI, contracts/parts/format, CSS e testes; reproduzir defeitos no LAB | Diagnóstico screenshot + tracing + \`EXISTING_EQUIVALENT/REUSE_DECISION\` |
| K1 — contrato/UX da tipografia | Garantir comportamento auto/fixed proporcional, inclusive sem frame e com resize, sem quebrar manual | RED→GREEN, DOM effective font size e screenshots vários tamanhos |
| K2 — anatomia do card no kit | Rebalancear valor/ícone/contexto nas variantes existentes e CSS shared | Story/catalog + editor/preview/TV, claro/escuro |
| K3 — formatação semântica | VISTA usa format spec oficial e o backend materializa \`93,73%\` no value | READ-BACK \`displayValue\` e print com \`%\` no valor |
| K4 — raciocínio visual VISTA | Reusar design intelligence, recipes, typed ops e self-review para evitar KPI clone | Um pedido → Compose → Bind → Mutate → PNG → finding → fix → PNG |
| K5 — regressão e rollout | Consumidores reais do kit + staging + deploy autorizado + pós-deploy | Report SHA, testes, imagens before/after, paridade e rollback |

**STOP CONDITION:** se o problema decorrer de contratos não expressivos ou limite de host para inspeção pixel-based, devolver evidência, owner e gate de decisão. Não inventar serviço/field/Action por conveniência; não aceitar apenas build verde, HTTP 200, screenshot esquemático ou declaração do modelo.

## 7. Critérios de aceite perceptual e técnico

- [ ] A variante Hero apresenta \`93,73%\` com unidade no VALOR, título sem \`(%)\`, ícone legível, comparação \`+8,73 p.p.\` somente com dado oficial.
- [ ] A variante Standard exibe \`12,4 h\` com hierarquia consistente, contexto omitido quando não existe.
- [ ] Meta exibe \`85,00%\` como meta; não simula atingimento sem realizado.
- [ ] Adaptação verificada visualmente em 4 KPIs por linha, Hero isolado, card estreito/baixo, 1920×1080 e zoom real; sem clipping/overlap.
- [ ] Font-size \`fixed\` do usuário é preservado, \`auto\` responde à geometria sem encolher indevidamente nem oscilar.
- [ ] Box e glyph do ícone têm presença visual coerente, inclusive para \`showIcon=false\` e SVGs diferentes.
- [ ] Valores \`null\`, \`0\`, extremos, locale PT-BR, precisão e porcentagens são semanticamente corretos no backend.
- [ ] Refresh não encobre valor válido e capturas são feitas após estabilização ou reportam pending.
- [ ] Persistência/reload/undo/autosave não perdem parts/options/projection; RBAC/CAS intactos.
- [ ] Editor ≡ preview ≡ TV, incluindo public-hub, com o **mesmo** componente/formatter owner.
- [ ] VISTA gera e avalia os KPIs corretamente em solicitação normal, sem depender de valor hardcoded ou receita exclusiva de OEE.
- [ ] Evidence inclui screenshot real before/after, provenance e findings distintos de auditoria estrutural.

## 8. Referências de código observadas (HEAD-base)

- \`plugins/plugin-ui/src/components/layout/DelpiKpiCard.tsx\`: \`valueUsesFitText = valueAutoFit && valueFramed\` (investigar para auto-layout); caixa de SVG em \`kpi-card.css\` com glyph de 58%.
- \`plugins/plugin-ui/src/components/layout/kpiCardParts.ts\`: defaults \`value=40\`, \`iconSize=36\`, frames em %, \`typographyMode\`, \`KPI_LAYOUT_PRESET_FRAMES\`.
- \`plugins/tv-dashboard-presentation/src/resolveKpiPresentation.ts\`: paint usa \`kpi.displayValue\` ou \`kpiPresentation.valueDisplay\`, sem format fallback.
- \`plugins/tv-dashboard-presentation/src/resolveKpiAutoContext.ts\`: variantes \`hero/row/scorecard\` e regra de contexto, preservando \`contextMode\`.
- \`plugins/tv-dashboard-presentation/src/dataBlockRefreshChrome.tsx\` + \`native-screens.css\`: badge/overlay \`Atualizando...\`.
- \`tv-dashboard-api/tv_app/application/services/data/display_format_service.py\`: formatação \`percent\` já existe e materializa \`%\` sem inventar formatter no React.
- \`plugins/tv-dashboard/src/components/KpiPartTypographyFields.tsx\`: controles de fonte; \`KpiViewOptionsInspector.tsx\`: unidade/ícone; \`KpiMetricsProjectionEditor.tsx\`: métricas.
- \`tv-dashboard-api/tv_app/content/design_intelligence.json\` e \`vista_agent_intelligence.json\`: diretrizes/regras existentes para evolução governada.

**Nota sobre o playbook de julho:** \`PLAYBOOK-KPI-CARD.md\` documenta Ondas 0–D como implementadas; este refinamento de proporção dinâmica, hierarquia e avaliação pixel-based é **evolução posterior** e não deve apagar/reescrever a evidência histórica como se as ondas nunca tivessem sido feitas.
