# UI-07 — Detalhes da Resposta da Pesquisa

> **Status:** decisões de UX aprovadas para **página própria**, **identificação no Hero**, **dois cards de notas individuais** e visual de **cinco pontos nas dimensões** (11/11/2026); **NÃO IMPLEMENTADO**. `RatingDots` é **CANDIDATO À CRIAÇÃO no PluginUI**, não componente existente nem backlog autorizado. HEAD-base desta revisão `main` `70943a7867851cb5455e3f1429aa7bcf2d68ee6e`, revalidar para implementar.
>
> **Owner UI:** `plugins/commercial`; **owner primitiva visual candidata:** `plugins/plugin-ui`; **authority de dados e autorização:** `commercial-api`. Referências: [UI-06](./UI-06-RESPOSTAS-POR-EMPRESA.md), [UI-01](./UI-01-RESULTADOS-PESQUISA.md), [contrato da primeira entrega](./SURVEY-FIRST-RELEASE-CONTRACT.md), [formulário](./UI-03-FORMULARIO-PUBLICO.md).

## 1. Fluxo, papel e navegação aprovados

**Ver resposta** na UI-06 abre **uma página completa**, não drawer, modal, aba ou seção expansível. A identidade é a **resposta definitiva da empresa (código + loja) naquela campanha**, com acesso **somente a `commercial.marketing` OU `commercial.manage`** aprovado no backend. `commercial.access` isolado jamais recebe dados individuais. Nenhuma gravação, edição, exclusão, reenvio ou exportação privada sem decisão e autorização próprias.

**Não criar segunda topbar.** Usar `CommercialPagePath` e `CommercialPageHero` com `density="compact"`: `eyebrow` Portal Comercial/Marketing, `title` “Detalhes da resposta”, `description` contexto de campanha, e `actions` com **“Voltar às respostas”**, usando `CommercialActionButton`. **Identificação da empresa ocupa `children` do mesmo Hero**, com `CustomerAvatar`, `CommercialEntityLink`, `CommercialDetailFieldGrid` e, se necessário, `CommercialStatusBadge`, sem card de identificação duplicado. Sem filtros na página, sem ações de Configuração/Resultados repetidas. Retornar à UI-06 preservando campanha, filtros e posição de lista quando o contrato de navegação existente permitir. Avatar e nome levam separadamente à Conta do Cliente. **Rotas exatas PENDING** no `pluginRoutes.ts`/`pluginNavigation.ts`, não inventar URLs.

## 2. Ordem completa e wireframes

1. **Identificação da empresa — APROVADO dentro do Hero:** utilizar `CommercialPageHero.children`, com `CustomerAvatar` real (mesmo da Minha Carteira), nome vinculável à Conta, **código e loja**, campanha, data/hora de resposta e situação oficial, com `CommercialDetailFieldGrid` e `CommercialStatusBadge` quando apropriados. **Não renderizar `CommercialDetailCard` separado só para repetir identidade**. No celular reorganizar dados verticalmente, sem ocultar código/loja.
2. **Avaliação geral — APROVADO:** exatamente dois `CommercialMetricCard` neutros **e não interativos**, **Satisfação geral** `overall_score / 5` e **Recomendação** `recommendation_score / 10`. Cada card tem nota grande, ícone Lucide discreto, `hint` curto “Nota registrada pela empresa” e `titleHint` para o texto da pergunta oficial. Props previstas: `label`, `value`, `hint`, `titleHint`, `icon`, `hero=false`, `tone="default"`; **não passar `onClick`**, nem tendências, estados comparativos, percentuais ou cores que rotulem o cliente como crítico. **Não nomear IGS nem NPS** (indicadores agregados). Não colocar `RatingDots` na avaliação geral; reservado às dez dimensões. Desktop/tablet: dois lado a lado quando couberem; celular: empilhar.
3. **Avaliação das dez dimensões — APROVADO:** `CommercialSectionCard` em **uma única lista vertical de dez linhas**, nunca duas colunas de cinco, em desktop, tablet e celular. Manter dez dimensões **sempre visíveis** e na **ordem oficial do questionário**, cada uma com nome completo, **cinco pontos preenchidos/neutros** e valor numérico `n / 5`. No desktop e tablet alinhar rótulo à esquerda e pontos/nota à direita; no celular, quando a largura for insuficiente, pontos/nota podem passar para baixo do nome, **sem rolagem horizontal**. Se `null` em resposta **definitiva validada**: texto **“Não se aplica”**, sem pontos nem nota zero. A API deve garantir que esse `null` veio de escolha explícita, pois dimensão sem seleção **bloqueia envio** (Q08 revista em 11/11/2026). Não interpretar notas como críticas automaticamente; pontos somente leitura, com texto acessível e cores por tokens de tema. Visual aprovado; usar `RatingDots` apenas **após** sua criação verificada no PluginUI.
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
| Pontos 1–5 | **`RatingDots` CANDIDATO** | **Não encontrado** nas buscas/inventário realizados; não afirmar implementado |

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

## 4. Abstraction Gate — candidato `RatingDots` no PluginUI

**Problema:** falta uma primitiva de **avaliação discreta, só de leitura**, com cinco pontos preenchidos/neutros + nota numérica, independente de pesquisa. As alternativas verificadas são barras. Busca de descoberta por `RatingDots`, `DotRating`, `RatingScale`, `ScoreDots`, `createRating` e “rating dots” sem retorno; inspeção de `plugins/plugin-ui/src/components/data`, `forms` e exports públicos não apontou equivalente. **Resultado de busca não prova ausência universal**; fazer busca residual no HEAD de execução.

**Proposta (não aprovada para implementação automática):**
- Arquivo candidato: `plugins/plugin-ui/src/components/data/RatingDots.tsx`; exportar via `components/data/index.ts` e pacote `@delpi/plugin-ui/index` após decisão técnica.
- Props mínimas sugeridas: `value: number | null`, `max?: number` (default 5), `size?: "sm" | "md"`, `showValue?: boolean`, `emptyLabel?: string`, `aria-label?: string`. Confirmar necessidade de `max` variável; preferir API menor se só houver caso de 5.
- Somente visual, sem editar, sem foco/hover interativo, sem regra comercial. `null` → rótulo definido, não zero; valores fora da escala devem ser tratados com segurança. Pontos preenchidos obedecem nota, vazios são neutros; texto numérico e descrição acessível sempre disponíveis.
- Cores por **tokens do PluginUI** com light/dark, sem hexadecimal fixo ou semáforo (nota baixa não vira perigo automaticamente); BEM e estilos oficiais.
- Testes: notas 1–5, `null`, limites, leitura acessível, temas, responsividade; regressão de exports/pacote e do consumidor Comercial.
- **Antes de alterar código:** confirmar HEAD/branch/working tree, fontes do PluginUI, consumidores/contratos, testes; Abstraction Gate com composição mínima vs primitiva, menor diff e relatório de execução. Nenhuma implementação até autorização.

**Gate Q08 — FECHADO por decisão do solicitante (11/11/2026):** para resposta definitiva, todas as dez dimensões requerem escolha explícita nota 1–5 ou “Não se aplica”. O estado sem seleção só existe antes de finalizar o formulário e **não é resposta persistível**. O contrato de `dimensions` deve manter as dez chaves canônicas; `null` da resposta definitiva = alternativa “Não se aplica” realmente marcada. API não pode inferir essa alternativa a partir de ausência do campo. Ver [BUSINESS-DECISIONS.md — Q08](./BUSINESS-DECISIONS.md) e [contrato da entrega 1](./SURVEY-FIRST-RELEASE-CONTRACT.md).

## 5. Estados, segurança e aceite

Loading via `CommercialLoadingCard`; não encontrado via `CommercialEmptyState`; falha via `CommercialStateBanner`; não autorizado por backend sem payload. Não expor token, dados pessoais de contato ou resposta a usuários somente `commercial.access`. Respeitar imutabilidade da resposta definitiva.

**Aceite visual:** página própria abre de UI-06, sem drawer; volta com contexto; identidade no próprio Hero (`children`) com avatar e código+loja, sem card repetido; dois `CommercialMetricCard` individuais neutros com ícones discretos, escalas e sem IGS/NPS; dez dimensões visíveis em ordem oficial com pontos e valor; N/A explícito; três comentários integrais; uso dos componentes oficiais; responsivo acessível; testes de negativas de permissão e nenhuma escrita. **Status permanece NÃO IMPLEMENTADO.**
