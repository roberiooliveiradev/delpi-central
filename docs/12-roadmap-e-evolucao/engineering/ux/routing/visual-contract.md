# EVA / Portal Engenharia — Routing Tab Visual Contract V1

**Status:** `TARGET / OWNER-DIRECTED / IMPLEMENTATION_NOT_AUTHORIZED_BY_THIS_DOC`  
**Data:** 2026-11-16  
**Owner de UX:** Portal Engenharia. **Owner de componentes:** `@delpi/plugin-ui`. **Owner dos dados:** Domain APIs/API-DELPI. **Owner do cálculo:** domínio determinístico Engenharia/EVA.  
**Fonte de decisão visual:** última referência compacta enviada pelo Product Owner na conversa, em que **Operações são cards expansíveis**, seguida da orientação explícita "simples, com cards e espaçamentos e componentes de Plugin UI; gráfico errado, tabela onde pode ser card".  
**Artefato visual versionado:** [references/operations-compact-target.svg](./references/operations-compact-target.svg) — reconstrução vetorial esquemática do modelo enviado, **não screenshot original nem equivalência pixel-perfect**. A captura original permanece no contexto da conversa; anexá-la separadamente se houver meio de upload binário oficial.  
**Precedência:** autoridades técnicas e de segurança > contrato de domínio > este contrato visual para apresentação > Doc 126 como histórico. Em conflito de apresentação, esta decisão posterior do owner substitui a alternativa "tabela ou cards" anterior; não reclassifica dados nem altera autoridade.
**Implementação atual inspecionada:** `plugins/engineering/src/features/products/routing/ProductRoutingTab.tsx` em `main` em 2026-11-16 — usa `DataTable` como apresentação primária, quatro `EngineeringKpiCard`, `EngineeringChartCard` + `ConfigurableSeriesChart`. O mapa estabelece reuso e substituições propostas, não afirma que o novo layout já está no runtime.

**REFERÊNCIA VISUAL APROVADA PELO PRODUCT OWNER — 2026-11-16:** painel PNG criado no chat e aprovado explicitamente, com **seis estados**: Operações, Balanceamento e Análise visual, cada um em **tema escuro e tema claro**. Nome do arquivo de origem anexado: `Painel DELPI em modos escuro e claro(1).png`. **Publicado:** [references/routing-all-tabs-dark-light-approved.png](./references/routing-all-tabs-dark-light-approved.png) — PNG 1024×576, `sha256:89cea3e90f8b0557c73890094db5ce065e044006b0b21710680926d7bcef89fa`, bytes íntegros do anexo do Product Owner (task `EVA-PORTAL-ROUTING-VISUAL-CONTRACT-IMPLEMENTATION-01`). O antigo `references/operations-compact-target.svg` está **SUPERSEDED**, por mostrar apenas Operações em dark e não representar o alvo visual integral. O PNG aprovado substitui a composição visual antiga como referência de produto, sem autorizar copiar números, cores hardcoded ou cálculos ilustrativos.\n\n## 1. Layout congelado para a seção Operações

**Ordem visual fixa:** Cabeçalho compacto (título, subtítulo, contexto/seletores) → navegação interna → 4 cartões de indicadores → cartão de seção "Operações do estágio" → lista vertical de cards de operação → detalhes técnicos secundários sob demanda → proveniência contextual discreta.

**Não fazer:** tabela como visualização primária de operações; cabeçalho com altura vazia; métricas secundárias com peso equivalente às quatro principais; três gráficos grandes ocupando a página quando faltam dados; texto de provenance enorme como rodapé de alerta; recriar componentes do Plugin UI.

### 1.1 Estrutura observável

| Bloco | Conteúdo e prioridade | Comportamento | Anti-exemplo bloqueante |
|---|---|---|---|
| Cabeçalho | Título `Roteiro de fabricação`, subtítulo `{code} · Operações e análises de processo`; contexto filial/estágio | Compacto, altura pelo conteúdo; controles acessíveis permitem mudar filial/estágio | Hero extra, faixas vazias, filtros em caixa alta isolada |
| Navegação | `Operações` / `Balanceamento` / `Análise visual` | Seleção clara, foco e teclado, sem mudar rota principal inadvertidamente | Tabs distantes do cabeçalho ou outra navegação global |
| Indicadores | 4 cards: `Operações`, `Centros de trabalho`, `Recursos`, `Tempo padrão` | Mesma família visual, contagem/soma do estágio sem converter total de linhas em operações | `MetricStrip` branco no dark, seis métricas sem priorização |
| Operações | Card de seção + contador; cada operação em um card expansível | Fechado mostra `01`, `EMBALAR`, `CT-99 · 0,06 min/peça`, chevron; aberto mostra dados adicionais | `DataTable` principal ou expansão com sete campos vazios em uma linha |
| Detalhes | Recurso, setup, tipo, obrigatoriedade e componentes reais | Grade curta e lista/card de componentes, somente atributos válidos em primeiro plano | Tabela aninhada como padrão sem justificativa de densidade |
| Contexto técnico | Fonte, parâmetros, classificação e limitações | Informação junto ao dado, por hint/rodapé breve, acessível por teclado | Parágrafo cru extenso em toda seção |

### 1.2 Dimensões e densidade — TARGET, não tokens do kit

- Alvo desktop: 4 KPIs por linha quando houver largura real; 2×2 em tablet, 1 ou 2 colunas em mobile conforme componentes e conteúdo. Não fixar px de componente do kit.
- Cabeçalho: **sem espaço vertical vazio**: título/subtítulo alinhados ao topo e navegação imediatamente após contexto/controles. Não usar `min-height` artificial; gap/padding derivados de tokens oficiais.
- Card de operação fechado: número/ordem em destaque discreto; descrição dominante; CT e tempo como metadados; indicação de expansão no fim; um item deve caber em leitura rápida sem varrer colunas.
- Seletores de filial/estágio devem ser controles reais ou context chips + affordance para trocar filtro. Não trocar `select` funcional por badge estático.
- Card de seção e operacionais não devem duplicar títulos nem aninhar dois containers visuais espessos sem necessidade.
- Dark e light são equivalentes de primeiro nível; o SVG é apenas referência composicional em dark, não paleta a copiar.

## 2. Balanceamento — composição congelada

**Ordem:** condições de produção (demanda/turno/pausas) → configuração opcional (postos/lote, menor destaque) → **resumo em dois cards visíveis** (tempo produtivo e prévia do takt) → ação primária `Calcular balanceamento` → resultado oficial com provenance `CALCULATED/PARTIAL` → comparação de cenários `SIMULATION` quando existir.

- Layout de formulário responsivo; campos não devem atravessar 5 colunas comprimidas.
- Valores com unidades e precisão adequadas; demanda e turno recebidos do usuário são `PROVIDED`; takt local é apenas prévia. Não reexecutar motor nem mudar algoritmo por requisito de UX.
- Resultados com hierarquia orientada à ação: gargalo candidato, mínimo teórico de postos, operações acima do takt, limitações; não declarar dimensionamento aprovado.
- Sem cenário: estado compacto com convite de próxima ação, não card gigante.
- Não transformar a seção em formulário administrativo de grande altura.
- Comparação de cenários: cartões sintéticos para poucos cenários; tabela compartilhada só se densidade/volume o exigir e isso for comprovado no componente map.

## 3. Análise visual — seleção consciente

- **Primeiro decidir se gráfico agrega valor.** Com uma operação apenas, apresentar card de tempo e leitura contextual, não gráfico de coluna solitária obrigatório.
- Com múltiplas operações: gráfico de tempos de operações e comparação com takt somente após cenário; simulação por postos apenas com resultado correspondente.
- Identificar **componente gráfico efetivamente usado** em página de referência do Portal que atenda ao visual; mapear path, export, props, tokens de tema e screenshot real. **Não é suficiente encontrar `ConfigurableSeriesChart` no catálogo.**
- Plot, título, ticks, tooltip, fundo e legenda devem harmonizar com tema claro/escuro; nada de plot branco/título preto no dark.
- Tempos pequenos precisam manter ticks significativos (ex.: `0,06 min = 3,6 s` como conversão só de apresentação). Não alterar dado canônico nem unidades silenciosamente.
- Se não existir opção adequada no kit, `PLUGIN_UI_GAP` com especificação neutra e Abstraction Gate para owner; não criar gráfico de biblioteca paralela no MFE.

## 4. Estados visuais mínimos

`operations_closed`, `operations_expanded`, `operations_multi`, `loading`, `empty`, `forbidden`, `unavailable`, `balance_empty`, `balance_filled_preview`, `balance_result`, `scenario_comparison`, `visual_one_operation`, `visual_many_operations`, `visual_with_takt`, `visual_simulation`; dark/light e desktop/mobile para estados críticos.

## 5. Processo de mudança

Antes de abrir task de implementação: o agente deve devolver **(a)** matriz de componente com exemplos reais, **(b)** captura comparável do shell visual, **(c)** diferenças em relação ao SVG/mock e **(d)** pendências de exports/tema. Se houver lacuna de kit, interromper só o bloco afetado, não inventar solução visual.

**Critério de aceite de UX:** match de hierarquia, escolha card vs tabela, densidade, interação, tema, gráfico e viewport; testes funcionais e presença de imports não substituem validação visual. Aprovação de arquitetura/deploy permanece sob regras canônicas.
