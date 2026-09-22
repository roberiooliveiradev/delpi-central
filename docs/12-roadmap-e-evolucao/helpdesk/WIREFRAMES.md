# Wireframes — Meus Chamados de TI

> **Produto:** Meus Chamados de TI
> **Id técnico:** `helpdesk` · `basePath` `/apps/helpdesk`
> **API:** `/apps/helpdesk-api` (o navegador não chama o GLPI nem a api-delpi)
> **UI kit:** `@delpi/plugin-ui` via Module Federation · factories em [`plugins/helpdesk/src/ui/helpdeskUi.tsx`](../../../plugins/helpdesk/src/ui/helpdeskUi.tsx)
> **Regras:** `plugins-reusable-components.mdc`, `plugins-visual-design-system.mdc`
> **Estado:** lista com filtros/builder, conversa HTML, compositor rico e prévia de anexo **publicados**. H5/H10/H12 abaixo são especificação ou park, não autorização nova.
> **Lacunas restantes:** [`11-lacunas-da-experiencia.md`](./11-lacunas-da-experiencia.md).
> **Corpo da mensagem:** [`12-conteudo-da-mensagem.md`](./12-conteudo-da-mensagem.md) (vigente; M-23 park).
> **Listagem:** [`13-listagem-de-chamados.md`](./13-listagem-de-chamados.md) (vigente).
> **Página e estados:** [`14-pagina-e-estados-do-chamado.md`](./14-pagina-e-estados-do-chamado.md).
> **Matriz GLPI Assistência:** [`15-capacidades-glpi.md`](./15-capacidades-glpi.md).
> **Paridade E6…E13:** [`16-plano-paridade.md`](./16-plano-paridade.md) — **concluída**. Menção: [`evidence/e14-mentions.md`](./evidence/e14-mentions.md).

Implementar uma tela deste módulo é montar as factories já nomeadas. Não criar `button`, `input`, `select`, `textarea`, card ou badge com CSS próprio.

## Convenções

| Símbolo | Componente |
|---|---|
| `[ Botão ]` | `ActionButton` `primary` |
| `[ Botão ]` secundário | `ActionButton` default |
| `·····` | `HelpdeskTextField` |
| `[ texto ]` | `HelpdeskTextArea` (legado; preferir rich) |
| `[ HTML ]` | `HelpdeskRichTextField` → `RichTextEditor` |
| `[Select v]` | `HelpdeskSelect` |
| `│ ░░░ │` | `HelpdeskLoadingState` |
| `⚠` | `HelpdeskStateBanner` `variant="error"` |
| `ℹ` | `HelpdeskStateBanner` default |
| `∅` | `HelpdeskEmptyState` |
| `●` | `HelpdeskStatusBadge` |
| `▢` | `HelpdeskRecordCard` |

**Root:** `.dashboard-helpdesk.dashboard-page.dashboard-page--fill` em `App.tsx`. A lista e a conversa preenchem a área do portal; a tabela e o fio rolam por dentro do card.

**Chrome do portal:** a sidebar da Minha DELPI fica fora do MFE. Este módulo não desenha menu próprio.

```text
┌─ HelpdeskPageHeader (titleRow) ─────────────────────────────────────┐
│ Título                                              [ Atualizar ]   │
│ Subtítulo opcional                                                  │
└─────────────────────────────────────────────────────────────────────┘
┌─ HelpdeskSectionCard ───────────────────────────────────────────────┐
│ Título da seção                                          hint (?)   │
│ actions no canto direito, quando existirem                          │
│ corpo                                                               │
└─────────────────────────────────────────────────────────────────────┘
```

Largura: uma coluna, exceto **Abrir chamado**, que replica o recorte do GLPI (`col-lg-8` / `col-lg-4`): conteúdo à esquerda, classificação à direita. Em tela estreita o título do header quebra acima do atualizar e as duas faixas do formulário empilham. Sem largura fixa e sem tabela que exija rolagem horizontal.

## Tema claro e escuro

O portal define `data-theme` em `<html>` (`light`, `dark` ou `system`). O MFE não usa `prefers-color-scheme` e não redefine `:root` nem `body`.

Tokens só dentro de `.dashboard-helpdesk`, mapeados para `--delpi-ui-*`:

| Token local | Origem |
|---|---|
| `--helpdesk-accent` | `var(--primary)` |
| `--helpdesk-title` | `var(--secundary)` no claro; mistura do primary com branco no escuro |
| `--helpdesk-text` | `var(--text)` |
| `--helpdesk-text-muted` | `var(--text-muted)` |
| `--helpdesk-surface` | `var(--surface)` |
| `--helpdesk-border` | `var(--border)` |
| `--helpdesk-danger` | `var(--danger)` |

O bloco escuro é `:root[data-theme="dark"] .dashboard-helpdesk`. Superfície, texto, borda, input, cartão, badge e banner vêm do CSS do kit. O `index.css` do plugin só declara esses tokens e o gap da lista (`.helpdesk-record-list`).

## Catálogo fechado

| Factory / export | Alias | Onde |
|---|---|---|
| `createDashboardPageHeader` | `HelpdeskPageHeader` | Todas as rotas conhecidas |
| `createDashboardSectionCard` | `HelpdeskSectionCard` | Lista, abertura, detalhe |
| `createDashboardStateBanner` | `HelpdeskStateBanner` | Vínculo, erro, proibido, indisponível, rota desconhecida |
| `createDashboardLoadingState` | `HelpdeskLoadingState` | Lista, abertura, detalhe |
| `createDashboardEmptyState` | `HelpdeskEmptyState` | Lista sem itens e sem erro |
| `createDashboardStatusBadge` | `HelpdeskStatusBadge` | Status do chamado |
| `createDashboardDataRecordCard` | `HelpdeskRecordCard` | Resumo do detalhe |
| `DataTable` | `HelpdeskDataTable` | Lista com ordenação de coluna (colunas via catálogo) |
| `TicketListToolbar` | — | Chips de recorte/sort + atualizar (H13) |
| `createDashboardMessageThread` | `HelpdeskMessageThread` | Abertura e acompanhamentos, `bodyMode=html` (HTML sanitizado + chips de menção) |
| `createDashboardTextField` | `HelpdeskTextField` | Título |
| `createDashboardTextAreaField` | `HelpdeskTextArea` | Legado; abertura/resposta usam rich |
| `HelpdeskRichTextField` | `RichTextEditor` | Descrição na abertura e Responder |
| `createDashboardSelectField` | `HelpdeskSelect` | Categoria (com busca) e urgência |
| `createDashboardFormActions` | `HelpdeskFormActions` | Rodapé dos formulários, vínculo e paginação |
| `createDashboardFiltersKit` | `HelpdeskFilterInput` / `HelpdeskFilterSelect` | Regras do construtor de filtros |
| `createDashboardSegmentToggle` | `HelpdeskSegmentToggle` | Tabela \| Cards |
| `createDashboardDataCardsGrid` | `HelpdeskDataCardsGrid` | Grade de cards |
| `createDashboardPaginationKit` | `HelpdeskListPaginationFooter` | Por página + paginação completa do kit (`HintAction`; has_more) |
| `createDashboardAttachmentPreviewStrip` | `HelpdeskAttachmentPreviewStrip` | Miniaturas no `belowBody` da abertura |
| `FilePreviewModal` | — | Prévia + Baixar; blob só na memória |
| `ActionButton` | — | Autorizar no helpdesk |
| `IconButton` | `HelpdeskIconButton` | Abrir, limpar filtros, paginar, voltar, enviar |

Texto de ajuda: `plugins/helpdesk/src/content/helpTooltips.ts`. O hint fica na prop `hint` do card ou do campo. Não colocar path de API no texto.

Tom do badge, em `statusBadgeVariant` (**por `status_id`**):

| Id | Variante |
|---|---|
| 1 Novo | `info` |
| 2 / 3 Em atendimento | `warning` |
| 4 Pendente / 6 Fechado | `neutral` |
| 5 Solucionado | `success` |
| 10 Approval | `warning` |
| demais | `neutral` |

## Rotas

| Path | Tela |
|---|---|
| `/apps/helpdesk` | Lista |
| `/apps/helpdesk/tickets/new` | Abrir chamado |
| `/apps/helpdesk/tickets/{id}` | Detalhe; `{id}` é só dígitos |
| qualquer outro sob `/apps/helpdesk` | Banner de endereço não encontrado |

Clique normal na linha usa `navigateHelpdesk`. Chamado e Título têm `href` estável; Ctrl, Shift, Alt ou clique do meio abrem o detalhe em outra aba.

## 1. Lista — `/apps/helpdesk`

```text
HelpdeskPageHeader
  título: Meus Chamados de TI
  subtítulo: Chamados no seu nome
  [ Atualizar ]

HelpdeskSectionCard  «Meus chamados»  hint = helpTooltips.list
  actions: [ + ]  aria-label Abrir chamado

  TicketListToolbar
    SegmentToggle Tabela | Cards
    chips de recorte / ordenação
    [ Limpar ]  só com recorte ativo
    [ Construtor de filtros ] [ Ordenação ] [ Colunas ] [ Atualizar lista ]

  TicketListFilterBuilder  (aberto por padrão; único editor do recorte)
    regras E (AND): busca, status, urgência, categoria, datas

  carregando     │ ░░░ │  «Carregando chamados…»
  proibido       ⚠  permissão do portal ou recusa do helpdesk
  indisponível   ⚠  «O helpdesk está indisponível…»
  outro erro     ⚠  mensagem genérica
  sem vínculo    ℹ  helpTooltips.link
                 [ Autorizar no helpdesk ]
  vazio          ∅  «Você ainda não tem chamados.»
                 ∅  «Nenhum chamado neste recorte.»  se filtro ativo
  lista tabela   HelpdeskDataTable  layout=scroll
                    colunas ordenáveis: Chamado, Título, Status, Categoria, Urgência, Aberto, Atualizado, Resolvido, Fechado
                    Técnico e Requerente sem ordenação (não são propriedade SQL da HLAPI)
                    Chamado e Título são <a href=/apps/helpdesk/tickets/{id}>; clique normal → navigateHelpdesk
                    Ctrl, Shift, Alt ou clique do meio abrem o href
                    datas absolutas; resolução e fechamento quando o GLPI trouxer
  lista cards    DataCardsGrid + HelpdeskRecordCard (#id · urgência · técnico)
  HelpdeskListPaginationFooter  (mesma linha)
    Por página 10/20/50  (HintAction)
    setas · números · Ir para · «Exibindo … · Página N de M»  (HintAction no bloco nav)
    has_more no BFF; total de páginas estimado; sem ícones ? soltos
```

Um estado por vez. Lista vazia só aparece com HTTP 200 e `items: []`. Proibido, vínculo e indisponível não podem parecer lista vazia.

A ordenação do cabeçalho pede de novo ao helpdesk; não reordena só a página visível. Em tela estreita a tabela usa scroll horizontal do kit. Sem coluna de entidade nem contadores do parque.

## 2. Abrir chamado — `/apps/helpdesk/tickets/new`

O GLPI 11 (`templates/components/itilobject/layout.html.twig`) parte a abertura em `itil-left-side` (`col-lg-8`: título e descrição) e `itil-right-side` (`col-lg-4`: categoria, urgência e demais propriedades). Esta tela copia esse recorte. Não copia atores, entidade, tipo, itens nem o accordion do painel direito.

```text
HelpdeskPageHeader
  [ ← ]  nav canto superior esquerdo  aria-label Voltar
  ícone TicketPlus
  título: Abrir chamado
  [ Atualizar ] oculto nesta rota

HelpdeskSectionCard  «Abrir chamado»  hint = helpTooltips.create  fill

  carregando categorias   │ ░░░ │
  erro                    ⚠

  form.helpdesk-create-form
    .helpdesk-create-layout          grid 2fr / 1fr; 1 coluna abaixo de 768px
      main  (esquerda, ~2/3)
        Título        ícone Type        ·····   obrigatório
        Descrição     ícone AlignLeft   [ HTML ] obrigatório, área alta
      aside (direita, ~1/3)
        Categoria     ícone FolderTree  [Select v] obrigatório, searchable
        Urgência      ícone Gauge       [Select v] obrigatório
                      Muito baixa | Baixa | Média | Alta | Muito alta
        Observadores  ícone Users       ·····   opcional (ids do helpdesk)
        [ Enviar ]    ícone Send        no rodapé da classificação
```

Não há campo de solicitante nem de entidade. Observadores são só papel `observer` (HD-011). Sucesso navega para `/apps/helpdesk/tickets/{id}` devolvido pela API. A mesma intenção de envio reutiliza a `Idempotency-Key`; não há segundo clique automático. O rascunho (título, descrição, classificação) sobrevive ao F5 neste navegador até o envio.

## 3. Detalhe — `/apps/helpdesk/tickets/{id}`

A tela publicada é a conversa abaixo. O inventário da conversa está em [`10-conversa-do-chamado.md`](./10-conversa-do-chamado.md). Página completa e estados: [`14-pagina-e-estados-do-chamado.md`](./14-pagina-e-estados-do-chamado.md).

```text
HelpdeskPageHeader
  [ ← ]  nav canto superior esquerdo  aria-label Voltar
  título: título do chamado, ou «Chamado» enquanto carrega
  [ Atualizar ]

HelpdeskSectionCard  «Conversa»  hint = helpTooltips.detail

  carregando    │ ░░░ │  «Carregando chamado…»
  erro          ⚠  inclui chamado indisponível para esta pessoa

  ▢  título = categoria
     subtítulo = urgência
     ● status
     Chamado / Técnico quando existirem

  HelpdeskMessageThread  bodyMode = html
    abertura
      autor = requester_display_name
      hora = «Criado em …»
      título = título do chamado
      corpo = description_html (sanitizado; chips de menção)
      prévia = HelpdeskAttachmentPreviewStrip; clique abre FilePreviewModal com Baixar
    acompanhamento
      autor, hora, content_html
      sem arquivo próprio (A-07 ainda não inventa o vínculo)

  Responder   [ HTML ]  obrigatório  hint = helpTooltips.detail   (oculto se can_followup=false)
  HelpdeskFormActions
    [ enviar ]
```

A abertura existe mesmo sem acompanhamento. Tarefa, solução, aprovação e acompanhamento privado não entram. `mine` e `requester_mine` vêm do BFF (id do GLPI ou e-mail). A tela não compara nome. A foto da Core só entra nessa bolha; as outras usam iniciais. Rascunho de resposta em `sessionStorage` sobrevive a F5.

## 4. Fora destas rotas

```text
⚠  «Endereço não encontrado em Meus Chamados de TI.»
```

Sem header e sem formulário.

## 5. H5 — especificado, não implementar

Estas telas só entram depois de decisão nova. Quando entrarem, usam o kit abaixo. Não desenhar estrela, dropzone ou fila no CSS do MFE.

| Capacidade | Onde | Componentes |
|---|---|---|
| Anexo | detalhe, na bolha de abertura | arquivos do chamado, com `ActionButton` «Baixar». Não é o arquivo de um acompanhamento. O envio de arquivo novo continua fora até a API do GLPI receber o binário. Sem dropzone próprio no CSS do MFE |
| Satisfação | detalhe, só se o status estiver solucionado | `HelpdeskSelect` ou botões `ActionButton` com os valores que o GLPI devolver. Sem componente de estrela no MFE |
| Bancada do técnico | rota de menu `/apps/helpdesk/console`, fora do MFE | abre `helpdesk.centraldelpi.com.br` em nova aba, com `samlIdpId=1`, só para `helpdesk.console` |
| Entidade | não há campo | continua a entidade padrão do usuário |

Se o kit não tiver o primitivo na hora de H5, o primitivo nasce em `plugins/plugin-ui` e só depois o MFE ganha a factory. O wireframe desta seção é atualizado no mesmo passo.
