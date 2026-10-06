# 25 — Visão Geral — Indicadores Financeiros

## Estado

**TARGET / DOCUMENTATION_GATE PASS / READY_FOR_IMPLEMENTATION_BRIEF_WITH_INVENTORY**

Runtime do Portal Controladoria & Finanças: **NOT_IMPLEMENTED**.

A fase atual é exclusivamente documental.

```text
PORTAL_REVIEW_PHASE      = ACTIVE
IMPLEMENTATION_AUTHORIZED = NO
```

Este documento é a authority funcional/visual do **Item 3 — Visão geral**.

## Objetivo

A página **Visão geral** é a superfície analítica e gerencial do Portal Controladoria & Finanças.

Ela deve responder:

> Como está a situação financeira relevante ao domínio, no período selecionado, com números confiáveis, comparáveis e rastreáveis às fontes?

Decisão de produto já congelada:

```text
VISÃO_GERAL = INDICADORES FINANCEIROS
```

Não confundir:

```text
Início      = orientação, launcher e atenção operacional
Visão geral = análise financeira e gerencial
Cockpit P1  = estado operacional de uma competência de fechamento
```

## Família visual

```text
VISUAL_FAMILY = OVERVIEW / ANALYTICS
REFERENCE     = Portal Comercial / Overview family
PLUGIN_UI     = FIRST
```

Gramática:

```text
TopBar
→ PageHero compacto
   → título / descrição
   → Atualizar
   → período rápido
   → filtros
→ Indicadores
→ Tendências
→ Comparativos
→ Atenção / sources
→ drilldowns tabulares quando o indicador justificar
```

O Portal Controladoria & Finanças não redesenha a família Overview.

## Boundary com Portal Financeiro P0

`plugins/financial` + `financial-api` continuam produto distinto.

O novo Portal pode reutilizar:
- source canônica;
- fórmula já owned por contexto autorizado;
- contracts estáveis;
- strategic-indicators-api;
- componentes do `@delpi/plugin-ui`;
- conceitos visuais comprovados.

Não pode:
- copiar a tela do Portal Financeiro;
- importar seu domain/application;
- ler seu banco;
- assumir suas permissions;
- reproduzir SQL/fórmula localmente;
- usar `financial-api` como authority apenas porque o P0 já compõe o mesmo número;
- adotar seus códigos `financial.*` no novo Portal.

```text
REUSE OWNER/SOURCE
!= COPY LEGACY PRODUCT
```

O novo Portal continua usando somente:

```text
controllership-finance.access
controllership-finance.manage
```

Sem permission code por indicador, filial, gráfico, drilldown ou botão.

## Inventário PROVEN — Portal Financeiro P0

A implementação atual do Portal Financeiro comprova uma gestão à vista com:

### KPIs principais

| Indicador | Unidade | Fonte técnica comprovada | Classificação para o novo Portal |
|---|---|---|---|
| ROL | BRL | `api-delpi /financial/rol` | CANDIDATE / REUSE_SOURCE_RECOMPOSE_UI |
| EBITDA / ROL | % | `api-delpi /financial/ebitda_pct` | CANDIDATE / REUSE_SOURCE_RECOMPOSE_UI |
| Custo fixo / ROL | % | `api-delpi /financial/fixed_cost_pct` | CANDIDATE / REUSE_SOURCE_RECOMPOSE_UI |
| PMR | dias | `api-delpi /financial/pmr` | CANDIDATE / REUSE_SOURCE_RECOMPOSE_UI |

Observação material:
- ROL é consultada por rota canônica da `api-delpi`;
- EBITDA, custo fixo e PMR também possuem contratos na `api-delpi`;
- no runtime atual, parte desses dados deriva de planilhas financeiras sob ownership da camada canônica existente;
- source indisponível deve continuar indisponível, nunca zero.

### Contexto financeiro complementar

O P0 também comprova:

| Bloco | Contrato/source | Classificação |
|---|---|---|
| Pontualidade / inadimplência | `api-delpi /financeiro/inadimplencia/*` | CANDIDATE CONTEXT |
| Valor/títulos em atraso | mesma família | CANDIDATE CONTEXT |
| Despesas por centro de custo | `api-delpi /financeiro/despesas-centro-custo/*` | CANDIDATE CONTEXT |
| Top centros de custo | mesma família | CANDIDATE CONTEXT |

Esses blocos possuem drills/rotas próprias no produto P0. No novo Portal, qualquer drilldown deve apontar para uma superfície autorizada do próprio produto ou owner, sem criar rota falsa.

### Indicadores estratégicos

Owner:

```text
strategic-indicators-api
```

O P0 lê diretamente o owner por S2S para:
- IDD do Financeiro;
- IGD da Delpi;
- indicadores do departamento;
- meta;
- realizado;
- gap;
- score/classificação.

O provider financeiro do `strategic-indicators-api` comprova atualmente os source keys:
- `financial-ebitda`;
- `financial-fixed-cost`;
- `financial-pmr`.

Classificação:

```text
STRATEGIC_SCORES = CANDIDATE
OWNER = strategic-indicators-api
```

O novo Portal não deve passar pela `financial-api` para IDD/IGD se o contrato S2S do owner continuar disponível no HEAD futuro.

## Decisões congeladas pelo Product Owner

### D-OVW-01 — conjunto inicial = C

A Visão geral V1 terá três grupos visualmente separados.

#### 1. Desempenho financeiro

```text
ROL
EBITDA / ROL
Custo fixo / ROL
PMR
```

Sources canônicas candidatas já comprovadas:
- `api-delpi /financial/rol`;
- `api-delpi /financial/ebitda_pct`;
- `api-delpi /financial/fixed_cost_pct`;
- `api-delpi /financial/pmr`.

#### 2. Contexto operacional financeiro

```text
Pontualidade / inadimplência
Valor / títulos em atraso
Despesas por centro de custo
Top centros de custo
```

Sources candidatas já comprovadas:
- `api-delpi /financeiro/inadimplencia/*`;
- `api-delpi /financeiro/despesas-centro-custo/*`.

#### 3. Desempenho estratégico

```text
IDD Financeiro
IGD Delpi
Indicadores do departamento
Meta / realizado / gap / score quando fornecidos pelo owner
```

Owner:
- `strategic-indicators-api`.

Regras:
- os três grupos permanecem visual e semanticamente distintos;
- score estratégico não é apresentado como KPI financeiro;
- nenhuma fórmula do P0 é copiada para o MFE/BFF;
- contract físico de cada indicador ainda deve ser revalidado antes da implementação;
- source/formula conflict continua stop condition.

### D-OVW-02 — período inicial = A

Quando a rota abrir sem filtros válidos na URL:

```text
start_date = primeiro dia do mês atual
end_date   = hoje
```

A competência pode ser derivada quando o contract suportar essa relação.

Regras:
- URL explícita sempre vence o default;
- QuickPeriodSelector permanece disponível;
- F5 preserva o recorte;
- última seleção do usuário não substitui silenciosamente o default quando não houver query.

### D-OVW-03 — unidade inicial = A

Default:

```text
Consolidado
```

Regras:
- unidade continua dimensão de dado;
- unidade não gera permission code;
- não selecionar arbitrariamente a primeira filial;
- URL explícita de unidade vence o default;
- contract da source precisa suportar consolidado; quando uma source específica não suportar, o bloco deve declarar sua limitação e degradar corretamente, nunca fabricar consolidação.

## Layout — desktop

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│ Início | Visão geral | Sala | Minhas tarefas | Administração | Ajuda       │
│                                      Buscar | Favoritos | [avatar] Usuário │
└──────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│ PORTAL CONTROLADORIA & FINANÇAS                              [Atualizar]     │
│ Visão geral                                                                 │
│ Indicadores financeiros do período, com fonte, contexto e drilldowns.       │
│                                                                              │
│ Período rápido: [Este mês] [Mês anterior] [...] [Personalizado]             │
│                                                                              │
│ Data inicial | Data final | Competência | Unidade | [dimensões aprovadas]   │
└──────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│ DESEMPENHO FINANCEIRO                                                       │
│                                                                              │
│ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐         │
│ │ ROL          │ │ EBITDA / ROL │ │ Custo fixo   │ │ PMR          │         │
│ │ R$ ...       │ │ ... %        │ │ ... %        │ │ ... dias     │         │
│ │ meta/context │ │ meta/context │ │ meta/context │ │ meta/context │         │
│ │ fonte/status │ │ fonte/status │ │ fonte/status │ │ fonte/status │         │
│ └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘         │
└──────────────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────┐ ┌────────────────────────────────────┐
│ TENDÊNCIA PRINCIPAL                │ │ COMPARATIVO                        │
│ [toolbar / agrupamento]            │ │ [unidade/período/dimensão]        │
│                                    │ │                                    │
│          gráfico                   │ │          gráfico                   │
│                                    │ │                                    │
└────────────────────────────────────┘ └────────────────────────────────────┘

┌────────────────────────────────────┐ ┌────────────────────────────────────┐
│ CONTEXTO FINANCEIRO*               │ │ DESEMPENHO ESTRATÉGICO*           │
│ inadimplência / CC                 │ │ IDD / IGD / metas                 │
│                                    │ │                                    │
└────────────────────────────────────┘ └────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│ DRILLDOWN / DETALHE*                                                        │
│ filtros herdados + DataTableSection                                         │
└──────────────────────────────────────────────────────────────────────────────┘

* os blocos fazem parte do escopo V1 por D-OVW-01=C; a renderização final depende dos contracts físicos e da disponibilidade comprovada de cada source.
```

## Layout — mobile

```text
TOPBAR COMPACTA

┌───────────────────────────────┐
│ Visão geral        [Atualizar]│
│ descrição                     │
│                               │
│ Período rápido                │
│ [Este mês] [...]              │
│                               │
│ Filtros                       │
│ Data inicial                  │
│ Data final                    │
│ Competência                   │
│ Unidade                       │
└───────────────────────────────┘

┌───────────────────────────────┐
│ Desempenho financeiro        │
│ [KPI]                        │
│ [KPI]                        │
│ [KPI]                        │
│ [KPI]                        │
└───────────────────────────────┘

┌───────────────────────────────┐
│ Tendência                    │
│ [toolbar]                    │
│ [gráfico responsivo]         │
└───────────────────────────────┘

┌───────────────────────────────┐
│ Comparativo                  │
│ [gráfico]                    │
└───────────────────────────────┘

[contexto / strategic / drilldown]
```

No mobile:
- não manter quatro KPIs comprimidos na mesma linha;
- não depender de hover;
- legends/toolbar devem continuar utilizáveis;
- tabela usa comportamento responsive do kit ou representação deliberada.

## PageHero

Densidade:

```text
compact
```

Eyebrow:

```text
Portal Controladoria & Finanças
```

Título:

```text
Visão geral
```

Descrição TARGET:

```text
Indicadores financeiros do período, com contexto, fonte e drilldowns para investigação.
```

Ação:
- `Atualizar`.

Durante refresh:
- preservar dados anteriores quando seguro;
- indicar refreshing;
- não substituir conteúdo por skeleton total.

## Filtros

### Regra de moldura

Filtros ficam dentro do Hero seguindo:

```text
PageHero
→ QuickPeriodSelector
→ FilterBar / FiltersRow
```

Aplicar regra de uma moldura do padrão visual.

### Filtros base

Podem ser congelados como capability visual:

```text
Período rápido
Data inicial
Data final
Competência
Unidade
```

Mas cada indicador só responde a filtro que seu contract suporta.

Não enviar dimensão a uma source que não a entende apenas para manter uniformidade visual.

### Dimensões adicionais

Somente após inventário de grain/source:
- centro de custo;
- fornecedor;
- conta;
- natureza;
- outras dimensões gerenciais.

Não copiar filtros do Comercial como cliente, carteira ou segmento.

### Unidade

```text
UNIT = DATA DIMENSION
UNIT != PERMISSION CODE
```

O backend continua autorizado por ACCESS e regras do owner; o filtro não concede acesso.

## URL / deep link

A Visão geral deve ser shareable.

Rota:

```text
/apps/controllership-finance/overview
```

Query TARGET conceitual:

```text
?start_date=YYYY-MM-DD
&end_date=YYYY-MM-DD
&competence=YYYY-MM
&unit=...
```

Somente filtros aprovados entram na URL.

Regras:
- URL tem precedência ao abrir deep link;
- F5 reconstrói o mesmo recorte;
- filtro inválido é normalizado/rejeitado de forma explícita;
- drilldown carrega o contexto relevante;
- retorno preserva filtros;
- não colocar informação sensível em query.

O nome físico final de cada parâmetro deve ser congelado no contract do BFF antes da implementação.

## Cards KPI

Usar:
- `KpiCard` / `createDashboardKpiCard` quando houver meta, score, badges e contexto rico;
- `MetricKpiCard` para métrica simples.

Cada KPI deve exibir ou disponibilizar:

```text
NAME
VALUE
UNIT
PERIOD/CONTEXT
SOURCE
FRESHNESS
STATUS
GOAL/COMPARISON somente quando owner fornecer
DRILLDOWN somente quando real
```

### Estado do valor

```text
0
= zero real comprovado

—
= indisponível / ainda não carregado / sem valor conforme estado explícito
```

Nunca usar 0 como fallback de exception.

### Meta

Meta só aparece quando:
- owner identificado;
- periodicidade definida;
- escopo compatível;
- strategic-indicators-api ou outro owner canônico fornecer.

Sem meta:
- não calcular gap localmente;
- não mostrar badge "abaixo/acima da meta".

## Gráficos

Escolha por semântica:

### Linha/área
Para evolução temporal contínua.

Preferir:
- `LineSeriesChart`;
- `AreaSeriesChart`;
- `MultiTypeSeriesChart` quando séries/tipos mistos forem semanticamente necessários.

### Barras
Para comparação categórica:
- unidade;
- centro de custo;
- fornecedor;
- período discreto.

Preferir:
- `BarSeriesChart`.

### ComparativeAreaChart

Somente quando houver contrato explícito de comparação entre séries/períodos.

### ChartCard

Todo gráfico usa `ChartCard`, com:
- título;
- hint;
- fonte/contexto;
- toolbar quando necessário;
- empty/loading/error próprio.

### Toolbar

Pode usar `createDashboardChartToolbarKit` para:
- agrupamento;
- export de série quando autorizado;
- ações auxiliares.

Não criar seletor de gráfico arbitrário só porque o kit suporta múltiplos tipos.

## Tendências

A primeira tendência deve ser escolhida durante o inventário físico dos contracts da V1, respeitando o conjunto já congelado por D-OVW-01=C.

Candidatos PROVEN:
- evolução de ROL;
- evolução de inadimplência/pontualidade;
- despesas por centro de custo ao longo do tempo;
- séries dos strategic indicators quando owner expuser.

Sem série canônica:
- não reconstruir histórico por chamadas ad hoc no browser.

## Comparativos

Permitidos quando a source oferecer grain compatível:
- período atual vs anterior;
- atual vs ano anterior;
- unidade A vs B;
- consolidado vs unidade.

Proibido:
- somar percentuais para consolidar;
- calcular média não ponderada sem owner;
- comparar períodos de tamanho diferente sem explicitar;
- fabricar baseline.

## Contexto financeiro complementar

Por D-OVW-01=C, o bloco de contexto operacional financeiro inclui:
- pontualidade;
- valor em atraso;
- títulos em atraso;
- despesas por CC;
- top centros de custo.

Eles devem aparecer como contexto/drilldown, não competir visualmente com os KPIs principais.

## Desempenho estratégico

Por D-OVW-01=C:

Section separada:

```text
Desempenho estratégico
→ IDD Financeiro
→ IGD Delpi
→ indicadores do departamento
```

Owner:

```text
strategic-indicators-api
```

Regras:
- não recalcular IDD/IGD no Portal;
- não copiar peso/meta para storage local;
- partial_success permanece explícito;
- ausência de indicador publicado não vira score 0;
- link externo/deep link para Indicadores estratégicos só quando autorizado e contract vigente.

## Drilldown

Drilldown existe apenas quando responde:

> Que registros explicam este número?

Regras:
- preserva filtros relevantes;
- usa owner canônico;
- não muda fórmula;
- não reconsulta uma base diferente sem sinalizar;
- deep link/F5;
- volta ao Overview preservando contexto.

`DataTableSection` é preferencial para drilldown tabular.

Se o detalhe pertence a outro produto/owner:
- navegação externa deve ser explícita;
- não fingir que a rota faz parte internamente do novo Portal.

## Source / freshness

Cada card/seção deve permitir ao usuário distinguir:
- dado atual;
- período;
- source;
- indisponibilidade;
- parcialidade.

Modelo lógico:

```text
source.status
source.asOf / freshness quando disponível
source.owner
```

Não inventar `asOf` quando o producer não fornecer timestamp confiável.

## Estados de experiência

### INITIAL / LOADING

- Hero/filtros disponíveis;
- blocos usam loading do kit;
- não mostrar zero.

### REFRESHING

- manter último dado confiável quando seguro;
- sinalizar atualização;
- falha no refresh preserva dado anterior com aviso, se contract permitir.

### SUCCESS

Valor + unidade + contexto coerentes.

### EMPTY

Somente quando consulta válida retornou ausência real de registros.

Não usar empty para source offline.

### PARTIAL

Indicadores/blocos independentes degradam isoladamente.

Exemplo:

```text
ROL          SUCCESS
EBITDA       UNAVAILABLE_SOURCE
PMR          SUCCESS
IDD          PARTIAL
```

A página continua útil.

### UNAVAILABLE_SOURCE

Mostrar bloco indisponível com source afetada e recovery quando aplicável.

### ERROR

Erro total apenas quando não é possível resolver a superfície analítica minimamente.

### FORBIDDEN

Sem `controllership-finance.access` → 403.

### NOT_FOUND

Não é estado normal da rota Overview, mas pode ocorrer em deep link/drilldown inválido.

## AuthZ

```text
authenticated
AND effective_permission(controllership-finance.access)
AND owner/resource rule quando aplicável
```

- Core effective permissions são authority;
- JWT não é authority final;
- MANAGE não substitui ACCESS;
- nenhum filtro de unidade cria permission;
- drilldown deve autorizar novamente no backend;
- UI hide/disable não autoriza.

## IA contextual

Pode:
- explicar indicador;
- traduzir fórmula para linguagem de negócio;
- resumir variação;
- comparar períodos com dados fornecidos;
- apontar source/freshness;
- sugerir perguntas de investigação.

Não pode:
- recalcular fórmula canônica por conta própria;
- substituir owner;
- criar meta;
- afirmar causalidade não suportada;
- ocultar indisponibilidade;
- executar write;
- concluir fechamento.

## Reuso obrigatório de @delpi/plugin-ui

Import preferencial:

```ts
import {
  createDashboardPageHero,
  createDashboardSectionCard,
  KpiCard,
  createDashboardKpiCard,
  MetricKpiCard,
  ChartCard,
  QuickPeriodSelector,
  createDashboardQuickPeriodSelector,
  createDashboardFiltersKit,
  FilterBarShell,
  LineSeriesChart,
  AreaSeriesChart,
  BarSeriesChart,
  ComparativeAreaChart,
  MultiTypeSeriesChart,
  createDashboardChartToolbarKit,
  DataTableSection,
  EmptyState,
  StateBox,
  StateBanner,
  LoadingState,
  createDashboardLoadingActivityCard,
  ActionButton,
} from "@delpi/plugin-ui/index";
```

Styles:

```ts
await import("@delpi/plugin-ui/styles");
```

### DO NOT RECREATE

- PageHero;
- KPI card;
- ChartCard;
- QuickPeriodSelector;
- FiltersRow/FilterBar;
- chart toolbar;
- chart primitives existentes;
- DataTableSection;
- loading/empty/state chrome.

Se faltar componente reutilizável:
```text
inventory plugin-ui
→ prove gap
→ propose plugin-ui contribution
→ do not clone locally
```

## Light / dark

Mesma árvore:

```text
SAME DOM
SAME KPI ORDER
SAME CHART TYPE
SAME DATA
+ THEME TOKENS
```

Não trocar gráfico ou hierarquia por tema.

Validar:
- contraste de séries;
- grid/axis;
- tooltip;
- legenda;
- tone de KPI;
- empty/loading;
- focus;
- border/surface.

Não hardcodear cores de séries no MFE quando o kit/theme fornecer palette canônica.

## Responsividade

Desktop:
- KPIs em grid conforme largura;
- gráficos 2 colunas quando útil;
- drilldown full width.

Tablet:
- reduzir colunas;
- filtros quebram conforme kit.

Mobile:
- KPI em 1 coluna ou densidade suportada;
- gráfico full width;
- toolbar sem overflow inacessível;
- legenda legível;
- filtro em stack;
- tabela com comportamento responsivo intencional.

## Acessibilidade

Obrigatório:
- heading correto;
- labels de filtros;
- foco visível;
- cards clicáveis com keyboard;
- gráfico acompanhado de título/contexto;
- tooltip não é única fonte de informação crítica;
- status não depende de cor;
- valores/unidades legíveis por screen reader;
- botão Atualizar anuncia busy;
- erro/partial anunciado.

## Help

A Ajuda deve publicar a seção Visão geral somente quando a rota estiver implementada.

Explicar:
- objetivo da página;
- significado de cada indicador aprovado;
- fórmula em linguagem de negócio;
- unidade;
- período;
- source;
- freshness;
- meta;
- diferença entre zero/sem dado/indisponível;
- filtros;
- drilldowns;
- strategic score quando aplicável;
- limites da IA.

## RQ / AC

### RQ-OVW-01 — Overview family comum

Aceite:
- PageHero compacto;
- período/filtros no Hero;
- KPI grid;
- charts;
- plugin-ui first.

### RQ-OVW-02 — indicador governado

Aceite:
- nenhum indicador entra sem NAME/MEANING/OWNER/SOURCE/FORMULA/GRAIN/PERIOD/FRESHNESS/UNIT/FAILURE/DRILLDOWN/AUTHZ/TEST;
- ausência != zero.

### RQ-OVW-03 — filtros shareable

Aceite:
- URL preserva filtros aprovados;
- F5 reconstrói recorte;
- unidade é dimensão, não permission.

### RQ-OVW-04 — partial isolation

Aceite:
- falha de um bloco não derruba os demais;
- refreshing preserva último dado quando seguro;
- source failure visível.

### RQ-OVW-05 — charts semanticamente corretos

Aceite:
- tipo deriva do indicador;
- sem baseline inventada;
- chart usa kit.

### RQ-OVW-06 — drilldown rastreável

Aceite:
- detalhe explica o KPI;
- contexto preservado;
- owner/source consistentes;
- rota inexistente não é inventada.

### RQ-OVW-07 — strategic owner

Aceite quando aplicável:
- IDD/IGD vêm de `strategic-indicators-api`;
- Portal não recalcula score/meta;
- partial_success explícito.

### RQ-OVW-08 — AuthZ simples

Aceite:
- somente ACCESS/MANAGE como permission codes do Portal;
- ACCESS requerido;
- MANAGE não implica ACCESS;
- nenhum permission code por unidade/indicador.

### RQ-OVW-09 — light/dark/mobile/a11y

Aceite:
- mesmo DOM/ordem;
- tokens;
- desktop/mobile;
- teclado/foco.

### RQ-OVW-10 — Help sync

Aceite:
- somente indicadores realmente implementados são ensinados;
- fórmula/source/freshness consistentes;
- links válidos.

## Matriz futura de testes

### Positive
- ACCESS abre Overview;
- período default aprovado;
- filtro por datas;
- filtro por competência;
- filtro por unidade quando suportado;
- zero real;
- KPI com meta;
- KPI sem meta;
- chart com série;
- drilldown;
- refresh.

### Sibling
- falha EBITDA não altera ROL;
- troca de unidade não reutiliza valor da unidade anterior;
- filtro de CC não contamina KPI que não suporta CC;
- drilldown A não altera card B;
- strategic score partial não altera KPI financeiro.

### Negative
- sem ACCESS;
- MANAGE sem ACCESS;
- source offline;
- null interpretado como zero;
- filtro inválido;
- unidade não suportada;
- meta ausente com gap calculado localmente;
- média percentual indevida;
- drilldown para rota inexistente;
- query não autorizada;
- stale response sobrescrevendo filtro novo.

### Experiência
- initial loading;
- refreshing;
- partial;
- empty;
- unavailable source;
- error;
- 403;
- 404 de drilldown;
- desktop;
- mobile;
- light;
- dark;
- keyboard/focus;
- F5;
- Help.

## Scripts/validators planejados para futura implementação

Não criar agora.

```text
validate-overview-indicator-catalog
- todo indicador possui owner/source/formula/unit/grain/failure behavior

validate-overview-route-contracts
- endpoint/drilldown existe
- owner correto
- nenhuma dependência direta MFE → api-delpi

validate-overview-filter-url
- parse/serialize roundtrip
- F5
- filtros inválidos
- parâmetros permitidos

validate-overview-source-states
- unavailable != zero
- partial isolation
- stale response protection

validate-overview-help
- indicador implementado possui Help
- fórmula/source/freshness não divergem
```

Os nomes são conceituais; forma/localização devem seguir o padrão de testes vigente no HEAD futuro.

## Inventários restantes

### O01 — conjunto inicial de indicadores

```text
CLOSED / PRODUCT_DECISION
```

D-OVW-01=C: núcleo financeiro + contexto operacional + desempenho estratégico.

### O02 — período inicial

```text
CLOSED / PRODUCT_DECISION
```

D-OVW-02=A: primeiro dia do mês atual até hoje, quando não houver query válida.

### O03 — unidade inicial

```text
CLOSED / PRODUCT_DECISION
```

D-OVW-03=A: Consolidado, quando não houver unidade explícita na URL.

### O04 — contracts físicos do novo BFF

```text
TO_INVENTORY_BEFORE_IMPLEMENTATION
```

Após indicador set fechado:
- mapear producer;
- OpenAPI;
- failure;
- freshness;
- auth;
- cache.

### O05 — source/formula conflicts

Se duas fontes/fórmulas diferentes existirem para o mesmo nome:

```text
EXECUTION_DRIFT
→ STOP
→ não escolher silenciosamente
```

## Gate

Já fechados:

```text
VISUAL_FAMILY_DEFINED   = PASS
WIREFRAME_DESKTOP       = PASS
WIREFRAME_MOBILE        = PASS
PLUGIN_UI_REUSE         = PASS
FILTER_GRAMMAR          = PASS
URL_F5_PATTERN          = PASS
STATES                  = PASS
AUTHZ_MODEL             = PASS
LIGHT_DARK              = PASS
A11Y                    = PASS
RQ_AC_TEST_MATRIX       = PASS
IMPLEMENTATION          = NOT_AUTHORIZED
```

Fechados por decisão do Product Owner:

```text
D-OVW-01 = C
D-OVW-02 = A
D-OVW-03 = A
```

Inventários técnicos restantes não reabrem essas decisões:
- O04 contracts físicos do novo BFF;
- O05 conflitos de source/fórmula como stop condition.

```text
ITEM 3 STATUS = READY_FOR_IMPLEMENTATION_BRIEF_WITH_INVENTORY
IMPLEMENTATION = NOT_AUTHORIZED
```
