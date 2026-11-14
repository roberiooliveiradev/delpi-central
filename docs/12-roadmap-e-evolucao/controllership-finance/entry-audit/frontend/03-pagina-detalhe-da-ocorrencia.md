# Entry audit · Front-end · Página 03 — Detalhe da ocorrência

| Campo | Valor |
|---|---|
| Rota | `/apps/controllership-finance/entry-audit/analyses/:analysisId/occurrences/:occurrenceKey` (e `…/unmatched/:unmatchedKey` para nota sem par — rota **só do MFE**; os dados vêm da mesma rota da BFF de ocorrência) |
| Forma | painel lateral sobre o dashboard (desktop); página inteira (≤ 768px) |
| Permissão | `controllership-finance.access` |
| Wireframe | seção 3 do [HTML](./wireframes-auditoria-entradas.html) |
| Contrato | reconciliado com a BFF publicada (T10.0, 2026-11-14) — [README](./README.md#reconciliação-t100) |

## 1. Objetivo

Explicar uma ocorrência por inteiro para quem vai corrigir no Protheus: o que diverge, por quê, o que fazer, qual regra pegou, o documento para conferir (chave e XML; DANFE/DACTE só quando há pedido no LNF) e o histórico. Daqui o usuário marca como resolvida ou leva a pergunta para a CLARA.

A rota é própria (deep link): abrir o link mostra o dashboard da análise com o painel aberto. Fechar o painel volta para a URL do dashboard, preservando os filtros.

## 2. Estrutura e dimensionamento

```text
┌ DrawerShell (440px) ───────────────────────────────┐
│ título: CT-e: crédito de ICMS em frete sem direito │
│ descrição: CT-e 25655 · J.J. Sul · TES 036         │
│ [badge Alta] [badge Pendente]                      │
│ ┌ DetailCard «Valores» ──────────────────────────┐ │
│ │ Campo · Protheus · XML · Diferença (— se nula)  │ │
│ └────────────────────────────────────────────────┘ │
│ ┌ DetailCard «Por quê» ──────────────────────────┐ │
│ ┌ DetailCard «O que fazer» ──────────────────────┐ │
│ ┌ DetailCard «Regra» (+ HelpTooltip) ────────────┐ │
│ ┌ DetailCard «Documento» (chave, XML; DANFE/DACTE se LNF) ┐ │
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
| `title` | `title` da ocorrência |
| `description` | «CT-e 25655 · <supplier_name> · TES 036» montada só com `document_number`, `series`, `supplier_name`, `tes` (sem filial, emissão nem CNPJ: não estão na resposta) |
| `onClose` | volta para a URL do dashboard |
| `closeAriaLabel` | `"Fechar detalhe da ocorrência"` |
| `closeOnBackdropClick` | `true` |
| `footer` | 3.8 |
| `portalScopeClassName` | `CF_PORTAL_SCOPE` |

No topo do corpo: `CfStatusBadge` da severidade (`severity`, PT) e `CfStatusBadge` do status (`status`: `warning` Pendente · `success` Resolvida; «em 13/11 por <actor>» vem do último evento `resolved` de `history`).

### 3.2 Valores — `CfDetailCard` + `DataTable` — existem

`CfDetailCard`: `title="Valores"`.
`DataTable` sem toolbar e sem paginação, colunas: Campo · Protheus · XML · Diferença (`align="right"`). **Uma única linha**, do campo da ocorrência: `field_label` · `protheus_value` · `xml_value` · `difference` (a resposta é plana, sem lista `values[]`). **`difference` `null` → «—»** (campo de código — CST, CFOP, série, chave… — não tem diferença numérica); valor ausente (`null`/vazio) também «—». Quando a ocorrência é de item (`item` ≠ ""), uma linha de contexto: «Item 0003» (produto e CFOP não vêm no contrato).

### 3.3 Por quê — `CfDetailCard` — existe

`title="Por quê"`. Texto vindo da BFF (`why` — **não** existe `reason` na ocorrência; `why` é a leitura e é diferente de `action`), gerado pelo motor, por exemplo: «As NF-e transportadas só têm CFOP de uso e consumo (x556); frete de consumo não dá direito a crédito. A TES 036 credita.» Se `why` vier vazio (campo do contrato opcional), o card não aparece. O MFE não monta texto de leitura por conta própria.

### 3.4 O que fazer — `CfDetailCard` — existe

`title="O que fazer"`. Texto da BFF (`action`), por exemplo «Lançar na TES de frete sem crédito (CST 090)». Quem corrige, quando relevante, já vem dentro do texto de `action`; o MFE não acrescenta.

### 3.5 Regra — `CfDetailCard` + `CfHelpTooltip` — existem

`title="Regra"`, `titleHint` com o grupo, traduzido do prefixo de `theme` («CT-e» para `cte`). Conteúdo: `rule_name` e o identificador `rule_id` (ex.: `cte.credit_without_right`, em texto secundário/copiável). A BFF **não serve** o catálogo (`regras.md`), condição nem severidade padrão da regra: sem `CfHelpTooltip` com condição e sem explicação própria do MFE. Se uma ajuda da regra for desejada, é evolução futura com contrato novo.

### 3.6 Documento — `CfDetailCard` — existe

`title="Documento"`. Campos: `access_key` (com botão copiar; ausente → «Sem chave de acesso»), `document_number`/`series`, `supplier_name`. Emissão, recebimento, valor e CNPJ **não** vêm na ocorrência e não são exibidos aqui. Ações (`CfActionButton` variante secundária), todas a partir de `links` da resposta (o MFE usa o valor como entregue e não monta URL):
- «Baixar XML» → `links.xml` = `/entry-audit/xml/{chave}?branch=…&document_type=…` (BFF; `application/xml`, anexo). `links.xml` `null` (sem chave de 44 dígitos e sem pedido no LNF) → botão ausente e texto «XML indisponível: nota sem chave de acesso». 404 `XML_NOT_FOUND` no download → `CfStateBanner` «XML não encontrado no Questor»;
- «Ver DANFE» (`links.danfe`, NF-e) / «Ver DACTE» (`links.dacte`, CT-e): **só aparecem quando há pedido no LNF** (`links.danfe`/`links.dacte` ≠ `null`; a rota é `/lancamento-notas-fiscais/requests/{id}/danfe|dacte`) e abrem pelo `FilePreviewModal` do kit. Sem pedido no LNF, nenhum dos dois botões. Como a base dessa rota é a do LNF e o MFE só fala com a própria BFF, o caminho de consumo na T11 é `TO_INVENTORY` (gateway do Portal, como o LNF já faz) — o doc não presume rota nova.

### 3.7 Histórico — `CfDetailCard` + `CfTimeline` — existem

`title="Histórico"`. `CfTimeline` com `history[]` da própria resposta, lista `{event, at, actor}` em ordem: `event` ∈ `pending` → «Aberta», `resolved` → «Resolvida por <actor>», `reopened` → «Reaberta por <actor>»; `at` pode ser `null` (evento `pending` sem data: mostrar sem data); `actor` pode ser vazio (omitir o «por»). Sem evento «Continua na execução de …» (não existe no contrato). Eventos da trilha de auditoria podem trazer outros valores de `event`: texto desconhecido é exibido como veio, sem ícone.

### 3.8 Rodapé — `CfResolutionStatusCell` (novo, doc 04 §2) + `CfActionButton` — existe/novo

| Elemento | Props |
|---|---|
| `CfResolutionStatusCell` | `variant="full"`, `status` (`pending`\|`resolved`), `resolvedAt`/`resolvedBy` do último evento `resolved` em `history` (`at`, `actor`), `onResolve`, `onReopen`, `pending` (enviando). Em nota sem par com `severity = Info` (explicada): sem botão |
| «Copiar pergunta para a CLARA» | `CfActionButton` ghost; copia «Explique a ocorrência <chave> da auditoria de 01/10 a 31/10/2026 e o que devo corrigir» |
| Anterior / Próxima | `CfActionButton` ghost com ícone; navegam na ordem da **página já carregada** da tabela (mesmos filtros e `sort`) — a BFF não devolve `prev_key`/`next_key`; desabilitados nas pontas da página carregada; `aria-label` «Ocorrência anterior» / «Próxima ocorrência»; atalhos `[` e `]` |

## 4. Dados

| Bloco | Rota da BFF |
|---|---|
| Tudo do painel | `GET /entry-audit/analyses/{id}/occurrences/{key}` → objeto **plano**: `stable_key`, `rule_id`, `rule_name`, `severity`, `theme`, `title`, `document_number`, `series`, `supplier_name`, `item`, `field`, `field_label`, `protheus_value`, `xml_value`, `difference`, `tes`, `why`, `action`, `access_key`, `status`, `history[{event,at,actor}]`, `links{xml,danfe,dacte}` (sem `occurrence`/`values[]`/`reason`/`rule`/`document`/`prev_key`/`next_key`). 404 `NOT_FOUND` = «chave não encontrada nesta análise» |
| Resolver / reabrir | `POST /entry-audit/occurrences/{key}/resolve` · `/reopen` → `{stable_key, kind, status, status_id}`; idempotente. Para nota sem par, as rotas irmãs `/entry-audit/unmatched/{key}/resolve` · `/reopen` têm o mesmo efeito |
| XML | `links.xml` → `GET /entry-audit/xml/{chave}?branch&document_type` (BFF) |
| DANFE / DACTE | `links.danfe`/`links.dacte`, **só com pedido no LNF** (`/lancamento-notas-fiscais/requests/{id}/…`) |

`{key}` = `stable_key` opaca, com `|`: `encodeURIComponent` na rota e na chamada.

**Nota sem par: não existe `GET …/unmatched/{key}`.** O detalhe usa a mesma `GET …/occurrences/{key}` (a BFF procura também entre as sem par): `rule_id` `unmatched.xml_only`/`unmatched.protheus_only` define «Onde está» (Só no XML / Só no Protheus), `title` é o Motivo/Situação e `links` funciona igual. O objeto **não traz** emitente, CNPJ, UF, valor, natureza, CFOP, CST, ICMS/IPI nem `lnf_request_id`: o MFE os lê do item da lista `…/unmatched` já em cache ou, em deep link, de `GET …/unmatched?q=<document_number>` casando por `stable_key`. «Valores» vira o bloco «Onde está» e «Por quê» fica oculto (`why` vazio).

## 5. Estados

| Estado | Comportamento |
|---|---|
| Carregando | esqueleto do `DetailCard` (`CfLoadingCard` compacto) |
| Chave não encontrada nesta análise (404 `NOT_FOUND`) | `CfEmptyGuidance` «Esta ocorrência não está nesta análise» com link para o dashboard |
| Análise sem filial concluída (409 `ANALYSIS_NOT_READY`) | volta ao dashboard, que mostra «Análise em andamento» |
| Resolvendo | botão em estado `pending`; tabela atrás atualiza junto (otimista) |
| Erro ao resolver | `CfStateBanner variant="error"` dentro do painel; status volta ao anterior |

## 6. Acessibilidade

O painel é um diálogo (`role="dialog"`, `aria-labelledby` no título); foco vai para o título ao abrir e volta para a linha da tabela ao fechar; `Esc` fecha. No mobile, página comum com `h1`. Os links de documento abrem em visualizador acessível do kit.
