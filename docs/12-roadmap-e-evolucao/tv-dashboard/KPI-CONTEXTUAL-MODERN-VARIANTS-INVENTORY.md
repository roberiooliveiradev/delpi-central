# Inventário de evolução — KPI contextual, status de meta e variantes modernas (VISTA / TV)

> **Data:** 2026-11-03. **HEAD inventariado:** `52a7556efd9a053947f962cb0c1dbc350ef28254`; revalidar no HEAD de implementação.  
> **Status:** inventário **PROVEN/TO_INVENTORY** + proposta visual/contratual **TARGET/PLANNED**. **Nenhuma funcionalidade nova é implementada por este documento.**  
> **Referências:** [PLAYBOOK-KPI-CARD](./PLAYBOOK-KPI-CARD.md) · [template proporcional PR #132](https://github.com/roberiooliveiradev/delpi-central/pull/132) (branch docs ainda não integrada na data deste registro) · [Issue #129](https://github.com/roberiooliveiradev/delpi-central/issues/129) · [Catálogo plugin-ui](../../../plugins/plugin-ui/docs/component-catalog.md) · [VISTA capability matrix](../../../tv-dashboard-api/docs/integrations/vista-capability-matrix.md).

## 1. Objetivo de produto / comportamento esperado

Evoluir o **mesmo** `DelpiKpiCard` usado por `kpi_view` para oferecer composições modernas, selecionáveis pela VISTA e editáveis pelo usuário:

- número protagonista + unidade correta no próprio valor;
- ícone posicionado e dimensionado com intenção visual (esquerda/direita/topo/oculto, conforme layout/parts realmente suportados);
- texto contextual **dinâmico** e comprovável: “Acima da meta”, “Abaixo da meta”, “Na meta”, “Dentro da faixa”, “Referência operacional”, “Sem meta disponível”, “Sem dados”;
- diferença frente à meta, variação vs período anterior, setas ↑/↓/↔ e símbolos de tendência, distinguindo movimento matemático de avaliação de desempenho;
- barra/anel de progresso ou sparkline opcionais, com fonte, escala e semântica corretas;
- cores variáveis semanticamente (positivo/negativo/neutro/alerta), tema DELPI claro/escuro, acessibilidade e redundância texto/ícone;
- variantes Hero, Standard, Meta/Scorecard, Compact, Row e famílias visuais com/sem comparação/progresso/sparkline, **sem criar uma família de componentes duplicados**;
- proporções e reflow conforme geometria real do card, preservando personalizações manuais e paridade editor ≡ preview ≡ TV.

A visão aprovada anteriormente, com Hero escuro e valor OEE “93,73%” e comparação contextual, é **referência de estética**, não screenshot de implementação. A captura real posterior do LAB (rev27) comprova que número, percentual e glyph foram corrigidos naquele slide; **contexto de meta, seta e progresso ainda não foram demonstrados como E2E**.

## 2. Inventário técnico no HEAD — existente versus lacuna

| Recurso | Evidência de código existente | Classificação / gap |
|---|---|---|
| `DelpiKpiCard` e parts (`card,title,value,hint,icon,comparison,progress,sparkline`) | `plugins/plugin-ui/src/components/layout/DelpiKpiCard.tsx`; `kpiCardParts.ts` | **PROVEN**: render/slots, tamanho/frame e visibilidade; qualidade visual do conjunto contextual **TO_INVENTORY** |
| Variantes `hero,standard,scorecard,compact,row` | `KpiLayoutVariant`, `DelpiKpiCard`, CSS `kpi-card.css` | **PROVEN** como nomes/render; seleção semântica automática backend para todos papéis **TO_INVENTORY** |
| `kpiOptions.target`, `comparisonMode:none|target|previous`, `higherIsBetter`, `showComparison`, `showProgress` | `kpiCardParts.ts`, `comunicadoKpiOptions.ts` | **PROVEN** no contrato frontend; autoridade da meta, cálculo, estado e origem da comparação **TO_INVENTORY** |
| `comparisonText`, `comparisonTone`, `progressPct`, `sparklinePoints` | Props `DelpiKpiCard`, estilos positivos/negativos e barra/sparkline | **PROVEN** render; não prova que todos valores são calculados/persistidos pelo backend |
| `resolved.kpiPresentation.comparisonDisplay/comparisonTone/progressPct` | `plugins/tv-dashboard-presentation/src/resolveKpiPresentation.ts` consome payload do servidor | **PROVEN** pintura de payload enriquecido; localizar serviço produtor/contrato de source e testes é **TO_INVENTORY** |
| Modo `contextMode=auto|off|manual` | `resolveKpiAutoContext.ts`; omitido equivale a `off` | **PROVEN** como comportamento/compatibilidade; verificar se decisão semântica se deslocou indevidamente ao renderer e evitar ampliar esse papel |
| Paleta/tone/regras condicionais | `DelpiKpiCard.resolveDelpiKpiTone`, `colorRules`, `KpiColorRulesEditor`, CSS | **PROVEN** como mecanismo visual; thresholds/indicador “bom” x “ruim” por domínio **TO_INVENTORY** |
| Meta/variação/ícone no editor | `plugins/tv-dashboard/src/components/KpiViewOptionsInspector.tsx` inclui meta, comparação, `higherIsBetter`, ícone e regras | **PROVEN** editor parcial; controles de estilo de status/setas, posição semântica de contexto, progress mode e estados ainda **TO_INVENTORY** |
| Tamanho ícone auto/fixo | `kpiCardParts.ts iconSizeMode`; `slide_part_chrome_service.py` seeds | **PROVEN** recente; legado `iconSize<=36` sem modo tem ambiguidade de autoria **TO_INVENTORY** |
| Formato `displayValue` | `tv-dashboard-api/.../display_format_service.py`; frontend `resolveKpiPresentation` consome string do backend | **PROVEN** owner e % literal; **não** recalcular unidade ou %-scale no React |
| Inteligência VISTA | `design_intelligence.json`, `vista_agent_intelligence.json`, `visual_impact`, `visual_self_review` | **PROVEN** diretivas; seleção/cálculo automático do status e **E2E** **TO_INVENTORY** |
| Mutation e segurança | `tv-dashboard-api` PresentationMutation + PREPARE/CONFIRM/COMMIT | **PROVEN** autoridade; potencial operação typed nova só após Action Surface Gate; não inventar campo via JSON |

**EXISTING_EQUIVALENT=YES** para slots, progress, sparkline, comparações, cor, variantes, controle de ícone e formatação.  
**REUSE_DECISION=REUSE/EXTEND**; nenhuma engine, renderer, registry ou formatter novo autorizado por esta especificação.

**Precaução:** o histórico `PLAYBOOK-KPI-CARD.md` classifica Ondas B–D como concluídas em julho; isso documenta capabilities de base, **não** comprova o novo conjunto de status dinâmicos, thresholds, legibilidade contextual ou fluxo VISTA E2E. Não reclassificar retroativamente ondas antigas.

## 3. Biblioteca visual de composições — wireframes textuais

A seleção abaixo é combinação das mesmas parts e options, **não** sete componentes distintos.

### 3.1 Hero com comparação vs meta

```text
┌────────────────────────────────────────────────────┐
│ ┌──────────┐  OEE realizado                         │
│ │  GAUGE   │  93,70%                                │
│ │ (grande) │  [ ↑ +8,70 p.p.  •  Acima da meta ]    │
│ └──────────┘  Meta oficial: 85,00%                  │
│               Últimos 30 dias                      │
└────────────────────────────────────────────────────┘
```

Dados de ilustração coerentes com o LAB rev27 (93,70% vs 85,00%). O cálculo **+8,70 p.p.** pressupõe MESMA escala, período, escopo e indicador, validados no owner. “Acima” é comparação matemática; “bom”/verde só com política explícita de direção e meta.

### 3.2 Standard com barra de progresso

```text
┌───────────────────────────────────────────────┐
│ [ ICON ]  Eficiência da linha                  │
│           76,40%                              │
│           [██████████████░░░░░] 76,4%         │
│           Referência: 100%                    │
└───────────────────────────────────────────────┘
```

A barra acima é **ilustrativa**: só renderizar quando limites/denominador/meta e tipo de progresso são legitimamente conhecidos. Não inferir “progresso da meta” de um percentual de eficiência sem contrato. Se a razão `realizado/meta` ultrapassa 100%, a UI precisa definir explicitamente **clamp visual** versus valor real no texto; nunca truncar o dado silenciosamente.

### 3.3 Meta em estado neutro

```text
┌─────────────────────────────────────────┐
│ [ TARGET ] Meta oficial                 │
│            85,00%                      │
│            Referência operacional      │
└─────────────────────────────────────────┘
```

**Não** mostrar “dentro/fora da meta” no próprio card de meta se não houver realizado comparável.

### 3.4 Acima, abaixo, dentro de faixa

```text
┌───────────────────────────┐   ┌───────────────────────────┐
│ OEE realizado             │   │ Refugo                    │
│ 93,70%                    │   │ 5,20%                     │
│ ↑ Acima da meta (+8,70pp) │   │ ↓ Abaixo da meta (-1,30pp)│
└───────────────────────────┘   └───────────────────────────┘
┌───────────────────────────────────────────────────────────┐
│ Temperatura | 75,0 °C | ↔ Dentro da faixa 70–80 °C       │
└───────────────────────────────────────────────────────────┘
```

**Exemplos, não dados oficiais de refugo/temperatura.** “Acima”/“abaixo” são posição relativa; avaliação favorável depende de `higherIsBetter/lowerIsBetter` ou de **faixa** validada. Não pintar “Refugo baixo” de vermelho por convenção de seta; queda pode ser positiva. “Dentro” exige faixa mínima e máxima e inclusividade definidas no contrato. Se o domínio não oferece faixa oficial, omitir o texto.

### 3.5 Tendência vs período anterior (não meta)

```text
┌──────────────────────────────────────────────────┐
│ Horas improdutivas                 [ CLOCK ]     │
│ 12,4 h                                          │
│ ↓ -6,2% vs período anterior                    │
│ [ sparkline temporal opcional  ▁▃▅▂▂▁ ]        │
└──────────────────────────────────────────────────┘
```

Seta indica **movimento do dado**; cor semântica exige `lowerIsBetter` para horas improdutivas. Nenhum valor ou porcentagem derivada sem dois períodos comparáveis e regras de agregação aprovadas. Sparkline requer pontos reais, ordenados por tempo e da mesma unidade.

### 3.6 Compacto com ícone em cima/à direita e contexto reduzido

```text
┌───────────────────────────────┐  ┌─────────────────────────────┐
│ [⚙] OEE Filial 01             │  │ Filial 02             [⚙]  │
│     95,84%                    │  │ 91,56%                      │
│     ↑ Acima da meta           │  │ Meta: 85,00%                │
└───────────────────────────────┘  └─────────────────────────────┘
```

Layout escolhe posição do ícone a partir da anatomia disponível (parts/frame) e não por um novo booleano duplicado. Modo compacto cede primeiro contexto opcional, depois faz reflow; **nunca** corta unidade ou dado principal.

## 4. Semântica e política de status — contrato-alvo backend-first

### 4.1 Insumos oficiais necessários

`metric` (valor, unidade, escala, precisão, directionality); `target` opcional com mesma referência temporal/escopo; `previous` opcional; `range` opcional com limites/inclusividade; thresholds/colorRules aprovados; `period`, `branch`, `source` e atualização/staleness.

O owner dos dados especifica se meta pode ser aplicada a filial específica ou só ao consolidado. Não cruzar filial/período diferentes apenas para preencher o card.

### 4.2 Resultados enriquecidos preferidos (conceitual, não schema obrigatório)

```text
valueDisplay                 "93,70%"
targetDisplay                "85,00%"             (se meta oficial)
comparisonDisplay            "+8,70 p.p."        (se comparável)
comparisonBasis              target | previous
relativePosition             above | below | at | in_range | out_of_range | unknown
performanceAssessment        favorable | unfavorable | neutral | unknown
direction                    up | down | flat | none (movimento, não juízo)
contextText                  "Acima da meta" | "Referência operacional" | ...
progress                     valor + escala + limite + modo, ou null
sparkline                    série/ordem/fonte, ou ausente
statusTone                   positive | negative | warning | neutral
provenance                   fonte + janela + escopo + revisão
```

Isto é **vocabulário de design para inventário**, não autorização para criar todos os campos. Mapear primeiro ao payload enriquecido existente `kpiPresentation.comparisonDisplay/comparisonTone/progressPct/showSparkline`, `kpiOptions`, parts e `DisplayFormatService`. Só ampliar schema se o equivalente existente for insuficiente e após testes de compatibilidade. Evitar recalcular `delta`, `p.p.`, progresso ou status no React.

### 4.3 Regras negativas e ambiguidade

1. **Movimento não equivale a sucesso.** ↑ em refugos pode ser ruim; ↓ em horas improdutivas pode ser bom.
2. **Acima da meta não é necessariamente positivo.** Meta é limite máximo ou mínimo conforme dado.
3. **Dentro da meta** só com regra explícita de igualdade/tolerância ou faixa oficial, não usar epsilon inventado.
4. **Progresso** tem denominador, baseline, escala, saturação e unidade definidos. Não usar clamp para alterar texto do valor real.
5. **Sem meta/sem anterior/sem fonte** → apresentação neutra, sem badge falso.
6. **Sem dado ou stale** → distinguir de `0`; refresh não apaga último valor válido.
7. **Cores** devem acompanhar texto/ícone para acessibilidade; usar tokens DELPI e contraste em card claro/escuro.
8. **Overrides manuais** de cor, posição, tamanho/frames, typographyMode/iconSizeMode e modo `off/manual` prevalecem.

## 5. Funções e controles de edição almejados

| Grupo | Opções de produto | Situação |
|---|---|---|
| Estilo | visual claro/escuro; borda/sombra; `tone`; cor de destaque / texto / ícone | Base **PROVEN**, presets modernos e aplicação consistente **TARGET** |
| Composição | `hero/standard/scorecard/compact/row`; localização e dimensão do ícone; rótulo acima/ao lado | Base parts + frame **PROVEN**, policy semântica/backend **TO_INVENTORY** |
| Contexto | ocultar/manual/auto, hint, comparação vs meta/anterior, sufixo de contexto, linha auxiliar | Base **PROVEN**, texto oficial gerado e persistência de estilo/posição **TO_INVENTORY** |
| Status | em meta, acima, abaixo, dentro de faixa, sem referência; setas para movimento + cor separada | **TARGET**, owner/status mapping **TO_INVENTORY** |
| Progress | barra linear, anel somente se equivalente existente; labels interno/externo; clamp visual e alvo | Barra **PROVEN**; anel/design avançado **TO_INVENTORY / TARGET**, não inventar implementação |
| Tendência | sparkline, séries comparáveis, período e polaridade | Base **PROVEN**, roteamento/enrichment E2E **TO_INVENTORY** |
| Layout | auto-fit, densidade, espaço de comparação, ocultação progressiva, locale | Base **PROVEN**; testes perceptuais contextuais **TARGET** |
| VISTA | escolher composição segundo papel + dados, solicitar preview real e autocorrigir via mutation governada | Diretivas **PROVEN**, E2E novo **TO_INVENTORY** |

**Editor:** inventorariar `KpiViewOptionsInspector`, `KpiPartTypographyFields`, `KpiColorRulesEditor`, ribbon/flyouts. Não criar outro editor KPI. Expor somente controles autorizados pelo backend/capability real. Preview do inspetor deve refletir mesmo painter.

## 6. Owners, contratos e gates

| Responsabilidade | Owner canônico |
|---|---|
| Significado métrica/meta/faixa/período, avaliação favorável, delta/progresso materializado e formatado | `tv-dashboard-api` + fonte api-delpi aprovada; rastrear serviço produtor real |
| `PresentationMutation`, validação, RBAC/scope, PREPARE→CONFIRM quando exigido→COMMIT→READ-BACK | `tv-dashboard-api` |
| Templates/recipes/política de seleção VISTA | Inteligência de design/recipe no owner TV Dashboard; VISTA orienta e usa, não autoriza |
| Pintura/medição/animation/reflow/ícones/cores consumindo contrato | `plugins/plugin-ui` `DelpiKpiCard` + `kpiCardParts` + CSS |
| Render comum dos dados e paridade | `plugins/tv-dashboard-presentation` (`resolveKpiPresentation`, `KpiViewBlockView`), sem nova regra de negócio |
| Inspector UX e controls de authoring | `plugins/tv-dashboard` |
| Kiosk público | `plugins/public-hub`, consumidor do renderer compartilhado |

**Nenhum** cálculo percentual, decisão favorável/desfavorável, RBAC ou política paralela no MFE ou no card React. `capability_surface` informa; backend autoriza. Nenhum segundo renderer nem Action nova por conveniência.

## 7. Fases propostas de implementação e aceites

| Fase | Entrega | Teste/evidência |
|---|---|---|
| **C0 INVENTORY** | Reancorar HEAD; achar serviço real que produz `kpiPresentation` e mapear meta/progresso/cor/fonte; confirmar paridade `plugin-ui`/presentation/TV | Matriz `PROVEN/TO_INVENTORY`, contratos, probes, `EXISTING_EQUIVALENT/REUSE_DECISION` |
| **C1 DOMAIN** | Reusar/estender **somente** contrato necessário para status/threshold/target/progress/sparkline e proveniência | RED→GREEN da semântica acima/abaixo/dentro, higher/lower, igualdade, nulos, incompatibilidade de escopo |
| **C2 PAINTER** | Refinar variants/layout, badges/arrow/progress/ícone/cores e responsive sem quebrar manual | Browser E2E pixel + component test, 1080p e cards estreitos |
| **C3 EDITOR** | Expor opções reais e acessíveis para contexto/status, posição do ícone e modo auto/manual | Editor reload/undo/redo, CAS, persistência das parts/options |
| **C4 VISTA** | Policy de seleção e default seguro; typed mutation e revisão pelo PNG real | Pedido único + render de contexto correto, autorrevisão sem métricas inventadas |
| **C5 DELIVERY** | Tests cross-package, clean merge, deploy autorizado, smoke, captura antes/depois | SHAs, logs redigidos, parity editor/preview/TV e report |

### Critérios de aceite decisivos

- [ ] Hero, Standard, Meta e Compact apresentam diferenças legíveis em conteúdo e hierarquia, usando o mesmo card.
- [ ] Texto `Acima/Abaixo/Na/Dentro` vem de regra oficial; sem meta → nenhum status falso.
- [ ] Cores representam avaliação correta, e setas representam movimento; ambos podem divergir sem bug.
- [ ] `+8,70 p.p.` só aparece quando realizado/meta usam a mesma unidade, janela e escopo.
- [ ] Barra/progresso com referência explícita, valor real não adulterado; sem denominador não aparece.
- [ ] Variação de posição/tamanho do ícone respeita frames/auto/fixed e manual overrides.
- [ ] Loading/refresh/erro/null não exibem status indevido; labels legíveis em TV 1920×1080.
- [ ] VISTA escolhe receitas/capabilities existentes e grava via typed PREPARE/COMMIT, com read-back.
- [ ] Captura real `editor_live` do mesmo slide/revision é analisada, com antes/depois; se indisponível, `VISUAL_PENDING`, nunca PASS.
- [ ] Editor ≡ preview ≡ public-hub, sem segundo formatter/renderer e sem regressão em KPIs legados.

**Stop condition:** se não se provar o serviço produtor/envelope canônico ou a compatibilidade do schema, gerar root-cause report e inventário focalizado, não implementação às cegas. Não considerar testes verdes isolados ou HTTP 200 como aceite perceptual.

## 8. Referências verificadas

- `plugins/plugin-ui/src/components/layout/kpiCardParts.ts` — parts, options `target`/`comparisonMode`/`showProgress`/`showSparkline`, variants, iconSizeMode/typographyMode.
- `plugins/plugin-ui/src/components/layout/DelpiKpiCard.tsx` + `plugins/plugin-ui/src/styles/kpi-card.css` — comparison tone, progress, sparkline, scorecard/hero/compact etc.
- `plugins/tv-dashboard-presentation/src/resolveKpiPresentation.ts` — consume `kpiPresentation.comparisonDisplay/comparisonTone/progressPct`; não executa negócio da meta.
- `plugins/tv-dashboard-presentation/src/resolveKpiAutoContext.ts` — `contextMode`, legacy off e recomendações locais existentes a auditar.
- `plugins/tv-dashboard/src/components/KpiViewOptionsInspector.tsx` — controle meta, comparação, higherIsBetter, ícone e colorRules.
- `tv-dashboard-api/tv_app/content/design_intelligence.json` e `vista_agent_intelligence.json` — selection/review directives.
- `tv-dashboard-api/tv_app/application/services/data/display_format_service.py` — formatação oficial.
- `docs/12-roadmap-e-evolucao/tv-dashboard/PLAYBOOK-KPI-CARD.md` — Ondas B–D históricas, sem reclassificar retrospectivamente.
