# UI-07 — Detalhes da Resposta da Pesquisa

> **Status:** decisões de UX aprovadas para **página própria**, **identificação no Hero**, **dois cards de notas individuais** e visual de **cinco pontos nas dimensões** (11/11/2026); **NÃO IMPLEMENTADO** no código. Auditoria dos seis gates (DEVIN) em `main` HEAD `0cde0f674bd31e494f6af3f9f688d908f24f5542` (11/11/2026): contratos técnicos fechados onde possível; implementação e testes de runtime **pendentes**. `RatingDots` permanece **CANDIDATO À CRIAÇÃO no PluginUI** — contrato mínimo fechado abaixo; **não autorizado a implementar nesta auditoria**.
>
> **Owner UI:** `plugins/commercial`; **owner primitiva visual candidata:** `plugins/plugin-ui`; **authority de dados e autorização:** `commercial-api`. Referências: [UI-06](./UI-06-RESPOSTAS-POR-EMPRESA.md), [UI-01](./UI-01-RESULTADOS-PESQUISA.md), [contrato da primeira entrega](./SURVEY-FIRST-RELEASE-CONTRACT.md), [formulário](./UI-03-FORMULARIO-PUBLICO.md).

## 0. Matriz dos seis gates (auditoria 11/11/2026)

| Gate | Situação | Evidência resumida | Pendência de implementação |
|---|---|---|---|
| **G01** RatingDots / PluginUI | `CLOSED_SPEC` | Inventário de `plugins/plugin-ui/src/components/data` + exports públicos: sem equivalente read-only de cinco pontos; alternativas (`InlineMeter`, badges, estrelas interativas locais) inadequadas | Criar primitiva após autorização; ver §4 |
| **G02** Navegação UI-06→UI-07 | `CLOSED_SPEC` | Padrão real em `pluginRoutes.ts` / `pluginNavigation.ts` / `commercialNavigationReturn.ts`; **nenhuma** view/rota/página de satisfação no código | Registrar rotas propostas §1.1; páginas UI-06/UI-07 |
| **G03** Contrato de leitura | `CLOSED_SPEC` | R13 e payload definidos no [contrato da entrega 1](./SURVEY-FIRST-RELEASE-CONTRACT.md); **ausentes** migrations/rotas/use cases no `commercial-api` | Endpoint + persistência + `questionnaire_version` concreto |
| **G04** Permissões | `CLOSED_SPEC` (matriz) / `PENDING_IMPLEMENTATION` (runtime) | `commercial.access` e `commercial.manage` **CONFIRMADOS** em `commercial_permissions.py` + manifest; `commercial.marketing` **somente documental**; R13 inexistente | Adicionar `commercial.marketing` na etapa autorizada; gate R13 marketing **OU** manage; negar access isolado |
| **G05** Estados / responsividade | `CLOSED_SPEC` | Spec visual e estados aprovados (§§1–5); componentes Comercial existentes verificados em `commercialUi.ts`; **sem renderização nem teste** da página | Implementar página + validar desktop/tablet/320px/zoom/a11y/temas |
| **G06** Testes integrados | `PENDING_IMPLEMENTATION` | Matriz §6 definida; **nenhuma suíte** UI-07/R13 existe; só testes de permissões genéricas executáveis hoje | Criar e executar testes após código |

**Classificação:** nenhum gate é `CLOSED_VERIFIED` — não há comportamento comprovado em runtime. Nenhum gate está `BLOCKED` por impedimento arquitetural externo; o bloqueio é ausência de implementação autorizada.

## 1. Fluxo, papel e navegação aprovados

**Ver resposta** na UI-06 abre **uma página completa**, não drawer, modal, aba ou seção expansível. A identidade é a **resposta definitiva da empresa (código + loja) naquela campanha**, com acesso **somente a `commercial.marketing` OU `commercial.manage`** aprovado no backend. `commercial.access` isolado jamais recebe dados individuais. Nenhuma gravação, edição, exclusão, reenvio ou exportação privada sem decisão e autorização próprias.

**Não criar segunda topbar.** Usar `CommercialPagePath` e `CommercialPageHero` com `density="compact"`: `eyebrow` Portal Comercial/Marketing, `title` “Detalhes da resposta”, `description` contexto de campanha, e `actions` com **“Voltar às respostas”**, usando `CommercialActionButton`. **Identificação da empresa ocupa `children` do mesmo Hero**, com `CustomerAvatar`, `CommercialEntityLink`, `CommercialDetailFieldGrid` e, se necessário, `CommercialStatusBadge`, sem card de identificação duplicado. Sem filtros na página, sem ações de Configuração/Resultados repetidas. Retornar à UI-06 preservando campanha, filtros e posição de lista quando o contrato de navegação existente permitir. Avatar e nome levam separadamente à Conta do Cliente.

### 1.1 Contrato de rota e navegação (G02 — `CLOSED_SPEC`, não implementado)

Padrão real do Comercial: roteamento manual em `plugins/commercial/src/app/pluginRoutes.ts` + `pluginNavigation.ts` + retorno seguro em `commercialNavigationReturn.ts` (`returnTo` / `returnLabel`, sanitizado sob `/apps/commercial`). **Não existe** React Router; paths novos em inglês kebab-case.

| Item | Contrato proposto | Owner |
|---|---|---|
| UI-06 (lista) | `/apps/commercial/satisfaction-survey-responses` | `pluginRoutes.ts`, `App.tsx`, manifest |
| UI-07 (detalhe) | `/apps/commercial/satisfaction-survey-responses/:responseId` | idem |
| `PluginView` | `satisfaction_survey_responses` / `satisfaction_survey_response_detail` | `pluginRoutes.ts` |
| Identidade da resposta | **somente** `responseId` (UUID da resposta definitiva); campanha/empresa vêm do payload R13 | `commercial-api` |
| Query UI-06 | `campaign_id`, `status`, `group` (valores oficiais da API), `q`, `page`, `sort`, `dir` | helper de sanitização do domínio |
| Query UI-07 | `returnTo` (pathname+query completos da lista), `returnLabel` (ex.: “Respostas por empresa”) | `commercialNavigationReturn.ts` |
| “Ver resposta” | Builder que monta detalhe + `buildHrefWithReturn` a partir da URL atual da lista | `pluginNavigation.ts` |
| Conta do Cliente | `buildCustomerDetailHref` / `navigateCustomerDetail` com `returnNav` contextual; **não** copiar filtros da pesquisa para a Conta | padrão Minha Carteira/OTD |
| Acesso direto URL | Página chama R13; 404/403/loading conforme backend; sem inventar dados | UI + API |
| Pendente na UI-06 | Sem ação “Ver resposta” | UI-06 |

**Evidência de ausência:** greps e inspeção de `PluginView`, `App.tsx`, `commercial.manifest.json` e features — zero rotas/páginas de satisfação. **Não registrar como implementado.**

## 2. Ordem completa e wireframes

1. **Identificação da empresa — APROVADO dentro do Hero:** utilizar `CommercialPageHero.children`, com `CustomerAvatar` real (mesmo da Minha Carteira), nome vinculável à Conta, **código e loja**, campanha, data/hora de resposta e situação oficial, com `CommercialDetailFieldGrid` e `CommercialStatusBadge` quando apropriados. **Não renderizar `CommercialDetailCard` separado só para repetir identidade**. No celular reorganizar dados verticalmente, sem ocultar código/loja.
2. **Avaliação geral — APROVADO:** exatamente dois `CommercialMetricCard` neutros **e não interativos**, **Satisfação geral** `overall_score / 5` e **Recomendação** `recommendation_score / 10`. Cada card tem nota grande, ícone Lucide discreto, `hint` curto “Nota registrada pela empresa” e `titleHint` para o texto da pergunta oficial. Props previstas: `label`, `value`, `hint`, `titleHint`, `icon`, `hero=false`, `tone="default"`; **não passar `onClick`**, nem tendências, estados comparativos, percentuais ou cores que rotulem o cliente como crítico. **Não nomear IGS nem NPS** (indicadores agregados). Não colocar `RatingDots` na avaliação geral; reservado às dez dimensões. Desktop/tablet: dois lado a lado quando couberem; celular: empilhar.
3. **Avaliação das dez dimensões — APROVADO:** `CommercialSectionCard` em **uma única lista vertical de dez linhas**, nunca duas colunas de cinco, em desktop, tablet e celular. Manter dez dimensões **sempre visíveis** e na **ordem oficial do questionário**, cada uma com título curto **e pergunta literal do Word em linha secundária**, **cinco pontos preenchidos/neutros** e valor numérico `n / 5`. No desktop e tablet alinhar rótulo à esquerda e pontos/nota à direita; no celular, quando a largura for insuficiente, pontos/nota podem passar para baixo do nome, **sem rolagem horizontal**. Se `null` em resposta **definitiva validada**: texto **“Não se aplica”**, sem pontos nem nota zero. A API deve garantir que esse `null` veio de escolha explícita, pois dimensão sem seleção **bloqueia envio** (Q08 revista em 11/11/2026). Não interpretar notas como críticas automaticamente; pontos somente leitura, com texto acessível e cores por tokens de tema. Visual aprovado; usar `RatingDots` apenas **após** sua criação verificada no PluginUI.
4. **Comentários — VISUAL APROVADO:** um único `CommercialDetailCard` com cabeçalho de ícone discreto (`message-square-text`), título **“Comentários do cliente”** e descrição curta. No interior, três blocos **em uma única coluna**, separados por divisórias suaves: **Pontos fortes** (ícone `thumbs-up`), **Oportunidades de melhoria** (ícone `message-circle`) e **Necessidades não atendidas** (ícone `circle-help`). Cada título tem ícone pequeno neutro e resposta em **superfície de fundo neutro** ligeiramente distinta do card, com borda arredondada e espaçamento do kit. Respostas em texto normal, sem aspas, sem itálico e sem classificação automática; **sem truncamento**, mantendo parágrafos/quebras de linha e seleção/cópia. Se ausente, exibir ícone neutro `minus` com **“Não informado”** em tom secundário. Ícones são ornamentais, não indicam avaliação positiva/negativa; validar nomes/exports dos ícones e usar tokens oficiais do PluginUI, sem novo componente comercial nem CSS paralelo. Responsivo: mesmas três seções empilhadas em desktop/tablet/celular.

```text
TOPBAR EXISTENTE
[CommercialPagePath: Marketing / Respostas por empresa / Detalhes]
[CommercialPageHero: Detalhes da resposta               ← Voltar às respostas]
[  children: CustomerAvatar + Empresa / código / loja / situação           ]
[            Campanha 2026/2 / data resposta                              ]
[CommercialMetricCard: Satisfação geral 4/5] [CommercialMetricCard: Recomendação 9/10]
┌─ Avaliação das dez dimensões ───────────────────────────┐
│ Qualidade             ● ● ● ● ●    5 / 5               │
│ Prazo de entrega      ● ● ● ○ ○    3 / 5               │
│ Atendimento           ● ● ● ● ○    4 / 5               │
│ Agilidade             ● ● ● ● ○    4 / 5               │
│ Comunicação           ● ● ● ● ○    4 / 5               │
│ Suporte técnico       Não se aplica                    │
│ Suporte comercial     ● ● ● ● ●    5 / 5               │
│ Flexibilidade         ● ● ● ○ ○    3 / 5               │
│ Confiabilidade        ● ● ● ● ●    5 / 5               │
│ Parceria              ● ● ● ● ●    5 / 5               │
└────────────────────────────────────────────────────────┘
[Comentários: Pontos fortes | Oportunidades de melhoria | Necessidades não atendidas]
```

**Dados fictícios, rótulos ilustrativos:** texto integral e ordem oficial vêm do Word/questionário versionado; chaves canônicas do backend, não posição de array.

**Responsivo:** Hero reorganiza identidade dentro de `children`, sem outro card; desktop com dois cartões numéricos lado a lado, rótulos/pontos/nota na mesma linha; tablet adapta sem esconder conteúdo; celular mostra os dois cards empilhados, dez linhas em fluxo vertical e comentários empilhados. Sem rolagem horizontal; testar nomes longos, zoom 200–400%, contraste, teclado e leitores de tela. Sempre manter **nota numérica legível** além dos pontos.

### Decisão de layout das dez dimensões (11/11/2026)

**Aprovado:** **lista vertical única** em todos os tamanhos de tela, sem distribuir dimensões em duas colunas no desktop. Nome à esquerda, pontos e nota à direita quando couberem; no celular, quebrar a composição de cada linha verticalmente se necessário, sem esconder dados. `RatingDots` permanece candidato do PluginUI, **não implementado**. Essa decisão é exclusivamente de apresentação; não altera as respostas nem seu contrato.

### Gate Q09 — fidelidade das 15 perguntas ao Word (conferência 11/11/2026)

**Fidelidade textual documental: FECHADA.** Todas as **15/15 perguntas** constam literalmente no [catálogo canônico da entrega 1](./SURVEY-FIRST-RELEASE-CONTRACT.md#14-catálogo-textual-canônico-das-15-perguntas--conferência-com-o-word-em-11112026): dez dimensões, satisfação geral, recomendação e três abertas, com suas chaves técnicas e escalas. Conferência feita diretamente com as seções 3–6 do Word original, não com exemplos fictícios.

**Padrão visual aprovado da página completa:** na lista vertical única, cada dimensão mostra **título curto + pergunta literal abaixo + cinco pontos + nota**; manter o texto sem truncamento no celular. As duas notas em `CommercialMetricCard` exibem o valor em destaque, acompanhadas das **perguntas literais** em ajuda acessível ou texto explicativo conforme composição; os três comentários mantêm **ícone, título, pergunta literal e resposta completa** dentro de um único card. Nomes curtos como “Prazo de entrega” não substituem a frase original. A prévia com respostas fictícias não representa dados gravados.

**Risco técnico residual:** o identificador concreto de `questionnaire_version`, a localização do catálogo no backend e os endpoints de leitura/versionamento ainda estão **PENDING**, não implementados nem verificados em execução. Não inferir versão a partir de data da campanha, nem reconstruir histórico sempre com o questionário corrente.

## 3. Componentes verificados versus candidato

| Região | Componente existente | Evidência |
|---|---|---|
| Trilha/Hero/retorno e identidade | `CommercialPagePath`, `CommercialPageHero`, `CommercialActionButton`, `CommercialEntityLink`, `CommercialStatusBadge` | `commercialUi.ts`; `PageHero.tsx` suporta `eyebrow`, `title`, `description`, `actions`, `children`, `density`; identidade aprovada em `children` |
| Empresa | `CustomerAvatar` | `features/customers/components/CustomerAvatar.tsx`; iniciais/imagem, `code`, `store`, `hasAvatar` |
| Blocos | `CommercialDetailCard`, `CommercialSectionCard` | `DetailCard.tsx`: `title`, `hint`, `children`, `headerActions` |
| Campos | `CommercialDetailFieldGrid` | `DetailFieldGrid.tsx`: `fields: {label,value,hint?,wide?}[]`, `valueFallback` |
| Duas notas individuais | `CommercialMetricCard` | `label`, `value`, `hint`, `titleHint`, `icon`, `hero=false`, `tone="default"`; sem `onClick` nem tendências; 1–5 e 0–10 |
| Alternativa parcial | `InlineMeter` | `data/InlineMeter.tsx`: barra contínua/segmentada, **não** pontos |
| Alternativa inadequada | `JourneyProgressBar` | `feedback/JourneyProgressBar.tsx`: barra percentual |
| Alternativa inadequada | `HorizontalValueBars` | Ranking por barras, não pontos individuais |
| Pontos 1–5 | **`RatingDots` CANDIDATO (`CLOSED_SPEC`)** | Inventário 11/11/2026 em HEAD `0cde0f67…`: sem export em `components/data` nem no pacote; ver residual §4; **não implementado** |

## 3.1 Detalhamento aprovado — bloco de Avaliação Geral

**Contexto:** notas são respostas **individuais** de uma única empresa naquela campanha; não equivalem ao **IGS** nem ao **NPS**, que exigem cálculos agregados no backend.

| Elemento | Satisfação geral | Recomendação |
|---|---|---|
| Componente | `CommercialMetricCard` | `CommercialMetricCard` |
| `label` | `Satisfação geral` | `Recomendação` |
| `value` | nota inteira `overall_score` formatada como `4 / 5` (exemplo) | nota inteira `recommendation_score` como `9 / 10` (exemplo) |
| `hint` | `Nota registrada pela empresa` | `Nota registrada pela empresa` |
| `titleHint` | Texto oficial da pergunta geral | Texto oficial da pergunta de recomendação |
| `icon` | Ícone Lucide discreto candidato: `smile` | Ícone Lucide discreto candidato: `thumbs-up` |
| Configuração | `hero=false`, `tone="default"`, `onClick` omitido | `hero=false`, `tone="default"`, `onClick` omitido |

**Não renderizar:** pontos de rating nesses cards, cores de aprovação/reprovação, etiquetas de “cliente promotor/detrator/crítico”, comparação temporal, delta, trend, percentual, semáforo ou botão falso. Não permitir edição. Os ícones são ornamentais e podem ser refinados conforme catálogo oficial de ícones do Portal, sem alterar a semântica dos cards.

**Wireframe:** desktop/tablet em **duas colunas quando couber**; celular **um card por linha**. Valor numérico grande com escala explícita, descrição curta e ícone secundário; sem truncar o rótulo. Respostas gerais são obrigatórias no contrato da pesquisa; dado inválido/indisponível vindo da API deve ser tratado como **erro de integridade ou estado específico**, não nota zero inventada.

**Aceite do bloco:** 2 cards e nenhum terceiro KPI; escalas corretas; nomes não agregados; sem clique/ícone de navegação; legíveis em 320px/zoom 200–400%; valores lidos somente da API autorizada; sem `RatingDots` aqui.

## 3.2 Detalhamento aprovado — Comentários do Cliente (11/11/2026)

**Decisão visual aprovada pelo usuário:** manter os **ícones pequenos junto aos títulos de cada pergunta**. Reusar **um** `CommercialDetailCard` para os três comentários, com ícone do cabeçalho, descrição curta, divisórias discretas e áreas de leitura com fundo neutro; **não criar três cards independentes**. Os exemplos visuais usavam `message-square-text` no cabeçalho, `thumbs-up`, `message-circle` e `circle-help` para os três títulos, e `minus` no estado não informado. São escolhas de ícones propostas para a implementação, sujeitas à disponibilidade no catálogo oficial; a decisão de **usar ícones** está aprovada.

- **Pontos fortes:** título/ícone neutro e conteúdo textual integral.
- **Oportunidades de melhoria:** título/ícone neutro e conteúdo textual integral, sem cor de alerta gerada pelo frontend.
- **Necessidades não atendidas:** título/ícone neutro e conteúdo textual integral, ou `Não informado` quando vazio.
- **Texto:** respeitar parágrafos, quebras de linha, seleção e cópia; nunca cortar, usar `Ver mais` nem usar controle de formulário desabilitado.
- **Tamanho:** altura de cada área cresce com o conteúdo; sem altura fixa ou barra de rolagem interna. Um bloco por pergunta no celular; mesma ordem do questionário em todas as larguras.
- **Visual:** superfícies e tipografia do PluginUI, tons neutros, bordas/cantos/espaçamento oficiais e divisórias suaves. Não criar CSS/kit paralelo. Ícones decorativos com semântica no texto; evitar que leitor de tela anuncie redundâncias.
- **Segurança:** conteúdos são respostas privadas e definitivas fornecidas pela API autorizada, sem edição, exclusão, classificação automática ou ação operacional nesta seção.

**Critérios de aceite:** um único card, três blocos, os três ícones visíveis ao lado das perguntas, indicador do card, ausência tratada explicitamente, textos longos sem truncamento, desktop/tablet/celular acessíveis e nenhuma ação de escrita. **Registro de UX, NÃO IMPLEMENTADO.**

## 4. Abstraction Gate — candidato `RatingDots` no PluginUI (G01 — `CLOSED_SPEC`)

**Problema:** falta uma primitiva de **avaliação discreta, só de leitura**, com cinco pontos preenchidos/neutros + nota numérica, independente de pesquisa. Alternativas verificadas no HEAD `0cde0f67…`:

| Candidato | Por que não reutiliza |
|---|---|
| `InlineMeter` (`data/InlineMeter.tsx`) | Barra contínua/`role="meter"`, não cinco unidades discretas |
| `DepartmentScoreBadge` | Texto/classificação, sem pontos |
| Sparklines / `TrendDelta` / `HorizontalValueBars` | Séries, deltas ou rankings — outra semântica |
| Estrelas em `public-hub` / `customer-experience` | Interativas, locais ao domínio, não exportadas no PluginUI |
| Escalas 1–5 em helpdesk/transformômetro/chat admin | Controles editáveis, não indicador read-only |

**Decisão Abstraction Gate:** composição ad hoc no Comercial (CSS/divs) **duplicaria** um primitivo visual transversal sem ownership no kit → **criar `RatingDots` no PluginUI** é a menor solução correta **quando autorizado**. Não criar cópia comercial. Não implementar nesta auditoria.

**Contrato mínimo fechado (implementação pendente):**

```ts
// Candidato — não existe no código
type RatingDotsProps = {
  value: 1 | 2 | 3 | 4 | 5 | null;
  max?: 5;                 // fixo em 5 na v1; prop opcional só se surgir segundo consumidor
  size?: "sm" | "md";
  showValue?: boolean;     // default true → "n / 5"
  emptyLabel?: string;     // default genérico; UI-07 mapeia null → "Não se aplica" no consumidor
  "aria-label": string;    // obrigatório
  className?: string;
};
```

- Arquivo candidato: `plugins/plugin-ui/src/components/data/RatingDots.tsx` + CSS canônico `styles/rating-dots.css` (tokens `--delpi-ui-*`, light/dark); export via `components/data/index.ts` e `@delpi/plugin-ui/index`.
- Somente leitura: sem `onChange`, sem foco interativo, sem hover de seleção, sem semáforo por nota baixa.
- `value` 1–5 preenche os primeiros N pontos; fora da escala → estado seguro (não inventar nota).
- Regra comercial N/A **não** vive na primitiva: a UI-07, com `null` de resposta definitiva validada, **omite pontos** e mostra “Não se aplica” (pode usar `emptyLabel` ou ramo do consumidor).
- Testes mínimos (quando implementar): 1–5, `null`/emptyLabel, a11y `aria-label`, temas, export/regressão do pacote.

**Residual search (além de texto):** barrels `data`/`forms`/`feedback`/`layout`/`index.ts`; catálogo visual do kit; padrões `[1,2,3,4,5]`/estrelas no monorepo; “dots” no PluginUI = marcadores de gráfico, não rating. **G01 não é `EXISTENTE_REUTILIZÁVEL`.**

**Gate Q08 — FECHADO por decisão do solicitante (11/11/2026):** para resposta definitiva, todas as dez dimensões requerem escolha explícita nota 1–5 ou “Não se aplica”. O estado sem seleção só existe antes de finalizar o formulário e **não é resposta persistível**. O contrato de `dimensions` deve manter as dez chaves canônicas; `null` da resposta definitiva = alternativa “Não se aplica” realmente marcada. API não pode inferir essa alternativa a partir de ausência do campo. Ver [BUSINESS-DECISIONS.md — Q08](./BUSINESS-DECISIONS.md) e [contrato da entrega 1](./SURVEY-FIRST-RELEASE-CONTRACT.md).

## 5. Estados, segurança e aceite (G05 — `CLOSED_SPEC`; runtime não validado)

| Estado | Componente / comportamento | Validado em runtime? |
|---|---|---|
| Loading | `CommercialLoadingCard` | Não — página inexistente |
| Resposta inexistente | `CommercialEmptyState` | Não |
| Erro de conexão | `CommercialStateBanner` | Não |
| Acesso negado | Backend 403 **sem** payload sensível; UI sem inventar dados | Não (R13 ausente) |
| Dados incompletos/inconsistentes | Erro de integridade — **não** forçar nota zero | Spec only |
| Comentário ausente | “Não informado” + ícone `minus` | Spec only |
| Dimensão N/A | “Não se aplica” sem pontos/zero | Spec only |
| Sem avatar | `CustomerAvatar` com iniciais | Componente existe; página não |
| Nome longo / 320px / zoom 200–400% | Reorganizar Hero/`children`; sem scroll horizontal | Spec only |
| Troca rápida entre respostas | Abort/cancelar fetch anterior; loading por `responseId` | Spec only |
| Teclado / leitores / contraste / claro-escuro | Tokens kit; texto acessível além dos pontos | Spec only |
| Somente leitura | Sem inputs, PATCH/DELETE, classificação IA ou ações de tratamento | Spec only |

Componentes Comercial confirmados em `plugins/commercial/src/app/commercialUi.ts`: `CommercialPageHero` (`density="compact"` default), `CommercialMetricCard` (`label`/`value`/`hint`/`titleHint`/`icon`/`hero`/`tone`/`onClick` omitido), `CommercialLoadingCard`, `CommercialEmptyState`, `CommercialStateBanner`, `CommercialDetailCard`, `CommercialDetailFieldGrid`, `CommercialSectionCard`, `CommercialActionButton`, `CommercialPagePath`.

**Não declarar responsividade validada** sem renderização e testes. **Aceite visual** permanece o da especificação aprovada; **status NÃO IMPLEMENTADO.**

## 6. Matriz de testes (G06 — `PENDING_IMPLEMENTATION`)

| # | Cenário | Suíte candidata | Resultado nesta auditoria |
|---|---|---|---|
| T01 | Navegação UI-06 → UI-07 com `responseId` + `returnTo` | `plugins/commercial` href/route tests | **TEST_NOT_RUN** — código inexistente |
| T02 | Retorno preserva campanha/filtros/página | `commercialNavigationReturn` + domínio | **TEST_NOT_RUN** |
| T03 | Identidade empresa código+loja; Conta separada de “Ver resposta” | UI + `buildCustomerDetailHref` | **TEST_NOT_RUN** |
| T04 | Payload R13: escalas 1–5 e 0–10; 10 dimensões ordem oficial; textos do catálogo versionado | `commercial-api` contract tests | **TEST_NOT_RUN** — R13 ausente |
| T05 | `null` dimensão = N/A; nunca nota 0 | API + UI | **TEST_NOT_RUN** |
| T06 | Comentários integrais / “Não informado” | UI | **TEST_NOT_RUN** |
| T07 | `questionnaire_version` histórica ≠ inferência por data | API + catálogo | **TEST_NOT_RUN** |
| T08 | Auth: marketing OK; manage OK; access isolado 403; sem token 401 | `commercial-api` | **TEST_NOT_RUN** para R13; permissões genéricas existem em `tests/test_commercial_permissions.py` (**pytest ausente neste ambiente** — não executado) |
| T09 | R16 agregado sem comentários/notas individuais / reidentificação | API | **TEST_NOT_RUN** |
| T10 | Estados loading/404/403/erro; sem writes | UI | **TEST_NOT_RUN** |
| T11 | Layout 320px / zoom / a11y / temas | UI | **TEST_NOT_RUN** — sem render |

**Proibido afirmar “testes verdes”** para UI-07 enquanto as suítes acima não existirem e não forem executadas.
