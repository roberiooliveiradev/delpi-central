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
3. **Avaliação das dez dimensões:** `CommercialSectionCard`, dez linhas **sempre visíveis** e em **ordem oficial do questionário**, cada uma com nome completo, **cinco pontos preenchidos/neutros** e texto `n / 5`. Se `null`: texto **“Não se aplica”**, sem pontuação zero. Visual de pontos aprovado; usar `RatingDots` apenas **após** sua criação verificada no PluginUI.
4. **Comentários:** `CommercialDetailCard` contendo **Pontos fortes**, **Oportunidades de melhoria** e **Necessidades não atendidas**. Sem truncamento, preservar parágrafos/quebras de linha; texto ausente = **“Não informado”**.

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

## 4. Abstraction Gate — candidato `RatingDots` no PluginUI

**Problema:** falta uma primitiva de **avaliação discreta, só de leitura**, com cinco pontos preenchidos/neutros + nota numérica, independente de pesquisa. As alternativas verificadas são barras. Busca de descoberta por `RatingDots`, `DotRating`, `RatingScale`, `ScoreDots`, `createRating` e “rating dots” sem retorno; inspeção de `plugins/plugin-ui/src/components/data`, `forms` e exports públicos não apontou equivalente. **Resultado de busca não prova ausência universal**; fazer busca residual no HEAD de execução.

**Proposta (não aprovada para implementação automática):**
- Arquivo candidato: `plugins/plugin-ui/src/components/data/RatingDots.tsx`; exportar via `components/data/index.ts` e pacote `@delpi/plugin-ui/index` após decisão técnica.
- Props mínimas sugeridas: `value: number | null`, `max?: number` (default 5), `size?: "sm" | "md"`, `showValue?: boolean`, `emptyLabel?: string`, `aria-label?: string`. Confirmar necessidade de `max` variável; preferir API menor se só houver caso de 5.
- Somente visual, sem editar, sem foco/hover interativo, sem regra comercial. `null` → rótulo definido, não zero; valores fora da escala devem ser tratados com segurança. Pontos preenchidos obedecem nota, vazios são neutros; texto numérico e descrição acessível sempre disponíveis.
- Cores por **tokens do PluginUI** com light/dark, sem hexadecimal fixo ou semáforo (nota baixa não vira perigo automaticamente); BEM e estilos oficiais.
- Testes: notas 1–5, `null`, limites, leitura acessível, temas, responsividade; regressão de exports/pacote e do consumidor Comercial.
- **Antes de alterar código:** confirmar HEAD/branch/working tree, fontes do PluginUI, consumidores/contratos, testes; Abstraction Gate com composição mínima vs primitiva, menor diff e relatório de execução. Nenhuma implementação até autorização.

## 5. Estados, segurança e aceite

Loading via `CommercialLoadingCard`; não encontrado via `CommercialEmptyState`; falha via `CommercialStateBanner`; não autorizado por backend sem payload. Não expor token, dados pessoais de contato ou resposta a usuários somente `commercial.access`. Respeitar imutabilidade da resposta definitiva.

**Aceite visual:** página própria abre de UI-06, sem drawer; volta com contexto; identidade no próprio Hero (`children`) com avatar e código+loja, sem card repetido; dois `CommercialMetricCard` individuais neutros com ícones discretos, escalas e sem IGS/NPS; dez dimensões visíveis em ordem oficial com pontos e valor; N/A explícito; três comentários integrais; uso dos componentes oficiais; responsivo acessível; testes de negativas de permissão e nenhuma escrita. **Status permanece NÃO IMPLEMENTADO.**
