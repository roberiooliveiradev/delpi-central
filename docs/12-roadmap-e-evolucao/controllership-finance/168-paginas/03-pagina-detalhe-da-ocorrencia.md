# 168 · Página 03 — Detalhe da ocorrência

| Campo | Valor |
|---|---|
| Rota | `/apps/controllership-finance/entry-audit/analyses/:analysisId/occurrences/:occurrenceKey` (e `…/unmatched/:unmatchedKey` para nota sem par) |
| Forma | painel lateral sobre o dashboard (desktop); página inteira (≤ 768px) |
| Permissão | `controllership-finance.access` |
| Wireframe | seção 3 do [HTML](../168-anexos/wireframes-auditoria-entradas.html) |

## 1. Objetivo

Explicar uma ocorrência por inteiro para quem vai corrigir no Protheus: o que diverge, por quê, o que fazer, qual regra pegou, os documentos para conferir e o histórico. Daqui o usuário marca como resolvida ou leva a pergunta para a CLARA.

A rota é própria (deep link): abrir o link mostra o dashboard da análise com o painel aberto. Fechar o painel volta para a URL do dashboard, preservando os filtros.

## 2. Estrutura e dimensionamento

```text
┌ DrawerShell (440px) ───────────────────────────────┐
│ título: CT-e: crédito de ICMS em frete sem direito │
│ descrição: CT-e 25655 · J.J. Sul · Matriz · 11/10  │
│ [badge Alta] [badge Pendente]                      │
│ ┌ DetailCard «Valores» ──────────────────────────┐ │
│ │ Campo · Protheus · XML · Diferença              │ │
│ └────────────────────────────────────────────────┘ │
│ ┌ DetailCard «Por quê» ──────────────────────────┐ │
│ ┌ DetailCard «O que fazer» ──────────────────────┐ │
│ ┌ DetailCard «Regra» (+ HelpTooltip) ────────────┐ │
│ ┌ DetailCard «Documento» (chave, DANFE/DACTE/XML)┐ │
│ ┌ DetailCard «Histórico» (Timeline) ─────────────┐ │
│ footer: [Marcar como resolvida] [Copiar p/ CLARA] │
│         [‹ anterior] [próxima ›]                   │
└────────────────────────────────────────────────────┘
```

| Faixa | Forma | Largura |
|---|---|---|
| > 1100px | `DrawerShell` à direita, sem bloquear a rolagem da tabela | 440px |
| ≤ 1100px | `DrawerShell` à direita | 400px |
| ≤ 768px | página inteira com `CfPagePath` («‹ Ocorrências») | 100% |

Rodapé fixo no painel (≥ 44px de altura de alvo). Corpo com rolagem própria.

## 3. Componentes

### 3.1 `CfDrawerShell` (← `DrawerShell`) — existe

| Prop | Valor |
|---|---|
| `open` | rota de detalhe ativa |
| `title` | texto da ocorrência |
| `description` | «CT-e 25655 · J.J. Sul Transportes · Matriz · emissão 11/10/2026 · TES 036» |
| `onClose` | volta para a URL do dashboard |
| `closeAriaLabel` | `"Fechar detalhe da ocorrência"` |
| `closeOnBackdropClick` | `true` |
| `footer` | 3.8 |
| `portalScopeClassName` | `CF_PORTAL_SCOPE` |

No topo do corpo: `CfStatusBadge` da severidade e `CfStatusBadge` do status (`warning` Pendente · `success` Resolvida em 13/11 por Michael).

### 3.2 Valores — `CfDetailCard` + `DataTable` — existem

`CfDetailCard`: `title="Valores"`.
`DataTable` sem toolbar e sem paginação, colunas: Campo · Protheus · XML · Diferença (`align="right"`). Uma linha por campo comparado (ex.: ICMS, Base, Alíquota). Quando a ocorrência é de item, uma linha extra de contexto: «Item 0003 · produto 10080680 · CFOP 1556».

### 3.3 Por quê — `CfDetailCard` — existe

`title="Por quê"`. Texto vindo da BFF (`occurrence.reason`), gerado pelo motor, por exemplo: «As NF-e transportadas só têm CFOP de uso e consumo (x556); frete de consumo não dá direito a crédito. A TES 036 credita.» Quando o crédito foi decidido pelo livro fiscal (SFT), uma linha: «Decidido pelo livro fiscal: FT_VALICM = 29,43».

### 3.4 O que fazer — `CfDetailCard` — existe

`title="O que fazer"`. Texto da BFF (`occurrence.action`), por exemplo «Lançar na TES de frete sem crédito (CST 090)». Quando a correção é de cadastro (fornecedor fora do Configurador de Tributos, TES), o card diz quem corrige.

### 3.5 Regra — `CfDetailCard` + `CfHelpTooltip` — existem

`title="Regra"`, `titleHint` com o nome do grupo («CT-e»). Conteúdo: nome da regra, severidade padrão e a explicação curta do catálogo (`references/regras.md`, servido pela BFF como `occurrence.rule`). `CfHelpTooltip` com `content` = condição da regra («TES/livro credita e direito ao crédito = Não»).

### 3.6 Documento — `CfDetailCard` — existe

`title="Documento"`. Campos: chave de acesso (com botão copiar), número/série, fornecedor + CNPJ, emissão, recebimento, valor. Ações (`CfActionButton` variante secundária): «Ver DANFE»/«Ver DACTE» e «Ver XML», abrindo pelo `FilePreviewModal` do kit (como o LNF já faz) a partir das rotas existentes da BFF (`/lancamento-notas-fiscais/received-invoices/{id}/danfe|dacte|xml`). Sem XML (nota só no Protheus): o card diz «XML não encontrado no Questor».

### 3.7 Histórico — `CfDetailCard` + `CfTimeline` — existem

`title="Histórico"`. `CfTimeline` com eventos: «Aberta pela execução de 13/11 22:10», «Resolvida por Michael em 14/11 09:02», «Reaberta por …», «Continua na execução de 20/11» (quando reaparece numa reexecução). Dados: `occurrence.history` da BFF.

### 3.8 Rodapé — `CfResolutionStatusCell` (novo, doc 04 §3) + `CfActionButton` — existe/novo

| Elemento | Props |
|---|---|
| `CfResolutionStatusCell` | `variant="full"`, `status`, `resolvedAt`, `resolvedBy`, `onResolve`, `onReopen`, `pending` (enviando) |
| «Copiar pergunta para a CLARA» | `CfActionButton` ghost; copia «Explique a ocorrência <chave> da auditoria de 01/10 a 31/10/2026 e o que devo corrigir» |
| Anterior / Próxima | `CfActionButton` ghost com ícone; navegam na ordem da tabela atual (mesmos filtros e ordenação); `aria-label` «Ocorrência anterior» / «Próxima ocorrência»; atalhos `[` e `]` |

## 4. Dados

| Bloco | Rota da BFF |
|---|---|
| Tudo do painel | `GET /entry-audit/analyses/{id}/occurrences/{key}` → `{occurrence, values[], reason, action, rule, document, history[], prev_key, next_key}` (`prev/next` calculados com os filtros e a ordenação enviados na query) |
| Resolver / reabrir | `POST /entry-audit/occurrences/{key}/resolve` · `/reopen` |
| DANFE / DACTE / XML | rotas do LNF já existentes na BFF |

Para nota sem par, o mesmo desenho com `GET …/unmatched/{key}`: Valores vira «Onde está» (Só no XML / Só no Protheus) e Motivo.

## 5. Estados

| Estado | Comportamento |
|---|---|
| Carregando | esqueleto do `DetailCard` (`CfLoadingCard` compacto) |
| Chave não encontrada nesta análise | `CfEmptyGuidance` «Esta ocorrência não está nesta análise» com link para o dashboard |
| Resolvendo | botão em estado `pending`; tabela atrás atualiza junto (otimista) |
| Erro ao resolver | `CfStateBanner variant="error"` dentro do painel; status volta ao anterior |

## 6. Acessibilidade

O painel é um diálogo (`role="dialog"`, `aria-labelledby` no título); foco vai para o título ao abrir e volta para a linha da tabela ao fechar; `Esc` fecha. No mobile, página comum com `h1`. Os links de documento abrem em visualizador acessível do kit.
