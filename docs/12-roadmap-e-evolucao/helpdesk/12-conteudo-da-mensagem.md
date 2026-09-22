# 12 — Conteúdo da mensagem da conversa

> **Status:** leitura HTML + imagem + escrita rica **IMPLEMENTADAS** (E8); menção leitura **IMPLEMENTADA** (E14 / M-07); menção escrita `@` **IMPLEMENTADA** (M-23). Paridade E6–E13 fechada. Não altera [`06-plano-execucao.md`](./06-plano-execucao.md).
> **Tela publicada:** [`WIREFRAMES.md`](./WIREFRAMES.md) §3 — `bodyMode=html`, `description_html` / `content_html`, compositor `HelpdeskRichTextField`.
> **Conversa (estrutura):** [`10-conversa-do-chamado.md`](./10-conversa-do-chamado.md).
> **Contrato:** [`03-contrato.md`](./03-contrato.md) + campos HTML aditivos. Menção: [`evidence/e14-mentions.md`](./evidence/e14-mentions.md).
> **Identidade:** id do GLPI ou e-mail; nome é rótulo, nunca chave. [`04-seguranca.md`](./04-seguranca.md).
> **Lacuna de experiência:** C-08 em [`11-lacunas-da-experiencia.md`](./11-lacunas-da-experiencia.md).
> **Formatação por seleção / colar imagem no compositor:** diagnóstico **e soluções prescritas** do kit em [`plugins/plugin-ui/docs/rich-text-selection-format-study.md`](../../../plugins/plugin-ui/docs/rich-text-selection-format-study.md) (não autoriza implementação sozinha).

Este documento responde: o que o GLPI considera conteúdo de uma mensagem, o markup que a HLAPI 2.2 devolve, o que a Minha DELPI **entrega hoje**, e o que permanece BLOQUEADO / CONSOLE.

## 1. Recorte do produto

A mensagem é o corpo da bolha na conversa do colaborador:

```text
abertura       = Ticket.name (título, texto) + Ticket.content (HTML)
acompanhamento = Followup.content (HTML, público)
```

Não é o formulário central do técnico. Tarefa, solução, aprovação, modelo, origem, pendência, promover a chamado e base de conhecimento continuam no console (`helpdesk.console`), como já travado em [`10-conversa-do-chamado.md`](./10-conversa-do-chamado.md).

Há dois fluxos distintos. Um não implica o outro:

| Fluxo | Pergunta |
|---|---|
| Leitura | o que já está no GLPI precisa aparecer na bolha? |
| Escrita | o que a pessoa pode gravar ao abrir ou responder? |

Isto **estende** HD-009 (detalhe), HD-010 (abrir), HD-013 (acompanhamento) e HD-016 (ajuda). Não é HD-019. Upload de anexo novo = H12 (PROVEN, Document-only); satisfação/bancada = H10/CONSOLE — não abrem por este inventário.

## 2. Fontes e grau de evidência

| Fonte | Classe | Uso |
|---|---|---|
| [Tickets](https://help.glpi-project.org/documentation/modules/assistance/tickets) | CONFIRMADO_EM_DOCUMENTACAO_CANONICA | o chamado nasce com conteúdo; o ciclo de vida não redefine o editor |
| [Followup](https://help.glpi-project.org/documentation/modules/assistance/tabs/followup) | CONFIRMADO_EM_DOCUMENTACAO_CANONICA | comentário, documento opcional, motivo de pendência, modelo, origem, privado, editar, promover a chamado. **Não** descreve as teclas do TinyMCE |
| [Documents](https://help.glpi-project.org/documentation/modules/management/documents) | CONFIRMADO_EM_DOCUMENTACAO_CANONICA | arquivo ou link; item associado inclui `Ticket`, `Followup`, `Solution`; MIME/extensão no Setup |
| Changelog HLAPI 11 (`html` + `x-supports-mentions`) | CONFIRMADO_EM_DOCUMENTACAO_CANONICA | schema marca conteúdo rico e menção |
| Schema HLAPI 2.2 no GLPI 11.0.5 (`Ticket.content`, `Followup.content`) | CONFIRMADO_NO_CODIGO | `format=HTML`, `x-supports-mentions=true` |
| Código / CSS GLPI (`[data-user-mention="true"]`, `document.send.php?docid=`) | CONFIRMADO_NO_CODIGO (upstream) | markup de menção e de imagem embutida |
| Colar imagem no TinyMCE → `image_paste*.png` + Documento | CONFIRMADO_EM_DOCUMENTACAO_CANONICA (issues 11.0.6/11.0.7) | no MFE: H12 cola → Document |
| `GET /session`, `team[].id`, `Followup.user.id` | CONFIRMADO_NO_CODIGO | identidade; fora do corpo |
| `mapping.py` `sanitize_message_html` + `description_html` / `content_html` | CONFIRMADO_NO_CODIGO | BFF allowlist + rewrite de `document.send.php`; texto plano derivado em `description` / `content` |
| Testes `test_mapping_publishes_sanitized_html_*` / create sanitize | CONFIRMADO_EM_TESTE | HTML sanitizado publicado; script fora |
| `HelpdeskMessageThread` `bodyMode="html"` | CONFIRMADO_NO_CODIGO | bolha renderiza HTML já sanitizado + chips de menção |
| `stripDangerousRichTextTags` | CONFIRMADO_NO_CODIGO | defesa no cliente; **não** substitui o BFF |
| `MessageThread` (`html`/`markdown`/`plain`) + `RichTextEditor` | CONFIRMADO_NO_CODIGO | kit ligado no fio e no compositor do helpdesk |
| `enrichGlpiUserMentionSpans` | CONFIRMADO_NO_CODIGO | M-07 — chip a partir de `data-user-id` |
| `MentionComposer` | CONFIRMADO_NO_CODIGO | salas; **não** é o compositor do helpdesk (M-23) |
| URL exata da `<img>` no HTML de produção (6288) | HIPOTESE_A_VALIDAR | típico `document.send.php?docid=N`; precisa de captura |
| Vínculo documento↔acompanhamento na Timeline | HIPOTESE_A_VALIDAR | A-07 em [`11-lacunas-da-experiencia.md`](./11-lacunas-da-experiencia.md) |

A documentação oficial do follow-up descreve o **fluxo** (Responder, comentário, documento, pendência). O **formato do comentário** (HTML, menção, imagem no meio do texto) está no schema da HLAPI, no TinyMCE do GLPI 11 e no código `RichText`/`UserMention`, não num capítulo isolado de “rich text”.

## 3. O que o GLPI coloca numa mensagem

### 3.1 Corpo (abertura e acompanhamento público)

| Peça | Onde o GLPI guarda | Evidência |
|---|---|---|
| Parágrafo e quebra de linha | `content` HTML (`<p>`, `<br>`) | schema `FORMAT_STRING_HTML` |
| Negrito, itálico, sublinhado, riscado | tags de ênfase | editor TinyMCE |
| Lista ordenada e não ordenada | `<ul>`, `<ol>`, `<li>` | editor |
| Título / subtítulo | `<h1>`…`<h6>` quando o editor oferece | editor |
| Alinhamento, cor, tamanho, fonte | `style` / `align` / `font` | editor |
| Link | `<a href>` | editor |
| Tabela | `<table>` | editor |
| Citação / bloco | `<blockquote>` | editor |
| Código | `<pre>`, `<code>` | editor |
| Linha horizontal | `<hr>` | editor |
| Menção a usuário | `[data-user-mention="true"]` + id | CSS `_richtext.scss`; `x-supports-mentions` |
| Imagem no meio do texto | `<img>` (em geral dentro de `<a>`), Documento | `document.send.php?docid=N`; foto do 6288; URL exata HIPOTESE |
| Documento ao lado do texto | item `Document` ligado a `Ticket` ou `Followup` | doc de Documents + follow-up «Add a document» |
| Marcador de formulário | `[data-form-tag="true"]` | CSS do TinyMCE; console / modelo |

O título do chamado (`Ticket.name`) não é HTML. Na Minha DELPI ele já é `headingText` da abertura.

### 3.2 Markup persistido (leitura)

O que o BFF deve **esperar** no `content` cru — não inventar outro formato.

**Menção** (CONFIRMADO_NO_CODIGO upstream; atributos exatos no 6288/1114 ainda HIPOTESE):

```html
<span data-user-mention="true" data-user-id="123">@Nome visível</span>
```

- identidade da menção = `data-user-id` (número);
- texto do chip = conteúdo do nó (rótulo);
- **proibido** casar menção pelo nome.

Perfil GLPI pode desligar ou restringir menção (Assistance: Disabled / Full / Restricted aos atores). O BFF **lê** o que já foi gravado e na escrita reutiliza `GET /users` (mesmo catálogo do assignee). Falha de write por política Restricted = `glpi_forbidden` — o BFF não inventa matriz de atores.

**Imagem embutida** (CONFIRMADO_NO_CODIGO upstream; produção HIPOTESE H1/H2):

```html
<a href="/front/document.send.php?docid=391" target="_blank">
  <img src="/front/document.send.php?docid=391" alt="…tag…" width="484" />
</a>
```

Variantes a tratar no sanitizer (não hardcoded de um chamado):

| Variante | Ação-alvo |
|---|---|
| path relativo `/front/document.send.php?docid=N` | reescrever para o GET autenticado do BFF se `N` ∈ `attachments` daquele chamado |
| URL absoluta `https://helpdesk.centraldelpi.com.br/front/document.send.php?docid=N` | idem |
| `docid` com `=` HTML-encoded (`&#61;`) | decodificar antes de casar |
| query extra `itemtype=Ticket&items_id=…` | ignorar no rewrite; o dono é o chamado do path |
| `data:` / `blob:` / `javascript:` no `src` | remover a imagem |
| host de terceiro no `src` | não proxiar (SSRF); remover ou virar texto |

**Documento sem `<img>`:** continua `attachments[]` + `belowBody`. Não inventar que todo Documento é inline.

### 3.3 Metadados do follow-up que **não** são o corpo

| Peça GLPI | Destino |
|---|---|
| Origem (Direct, E-Mail, Helpdesk, Phone…) | CONSOLE_GLPI |
| Modelo de acompanhamento | CONSOLE_GLPI |
| Motivo de pendência | CONSOLE_GLPI |
| Privado / público | privado já some da `timeline` |
| Editar follow-up | CONSOLE_GLPI até existir PATCH no contrato |
| Promover follow-up a chamado | CONSOLE_GLPI |
| Buscar / gravar na base de conhecimento | CONSOLE_GLPI |
| Notificação por e-mail | servidor GLPI; não é UI |
| `[data-form-tag]` de modelo | strip na leitura; não renderizar controle |

Follow-up vindo de **e-mail** (origem E-Mail) pode trazer HTML sujo (Outlook, assinatura, `cid:`). É caso irmão da sanitização, não um compositor à parte.

### 3.4 Documento

A doc de Documents: o arquivo pode vir do disco, de URL ou de upload FTP interno; tem MIME e extensão autorizada no Setup. O objeto associa-se a `Ticket` e a `Followup`.

Na Minha DELPI:

- baixar o que já está no chamado: publicado (`GET /tickets/{id}/attachments/{document_id}`);
- enviar arquivo novo: **PROVEN** H12 — `POST /tickets/{id}/attachments` via apirest Document (App-Token + User-Token técnico); HLAPI continua sem multipart;
- imagem no HTML da mensagem: leitura com rewrite BFF; escrita = upload H12 + `src` no path autenticado (preview no editor via blob).

## 4. O que a HLAPI 2.2 confirma

Lido no schema do GLPI 11.0.5 (`ITILController`):

| Campo | Formato | Notas |
|---|---|---|
| `Ticket.content` | HTML + menções | abertura |
| `Followup.content` | HTML + menções | acompanhamento |
| `Followup.is_private` | boolean | o BFF já exclui privado |
| `Followup.user` | dropdown `{id, name}` | identidade por `id`, não pelo `name` |
| `Followup.request_type` | dropdown | origem; não publicar no MFE |
| `Solution.content` | HTML + menções | fora desta conversa |
| Timeline `Document` | `documents_id`, `filename`, `mime` | hoje o BFF junta todos na abertura |

POST de abertura e de acompanhamento aceita `content` string. A HLAPI não define multipart. Por isso HTML no JSON é o caminho de escrita rica; binário de arquivo novo não é.

Catálogo de usuários por id: `GET /users` (BFF → HLAPI `Administration/User`) — **PROVEN** na onda assignee. **M-23 = IMPLEMENTADO**: `@` no create/reply grava `span[data-user-mention][data-user-id]` via kit `RichTextEditor` + `listUsers`. M-07 (chip na leitura) **IMPLEMENTADO** E14 via `enrichGlpiUserMentionSpans`.

## 5. O que a Minha DELPI faz hoje

```text
GLPI HTML
  → mapping.sanitize_message_html (+ rewrite document.send.php)
  → description_html / content_html  (sanitizado)
  → description / content            (texto derivado)
  → HelpdeskMessageThread bodyMode=html
  → enrichGlpiUserMentionSpans → chip de menção
```

| Superfície | Hoje |
|---|---|
| Abertura | título + HTML sanitizado; anexos do chamado no `belowBody` da abertura |
| Acompanhamento | HTML sanitizado; sem arquivo próprio por bolha (A-07) |
| Responder / abrir | `HelpdeskRichTextField` → `RichTextEditor`; POST HTML via `prepare_outbound_message_html` |
| Validação de escrita | não vazio; teto `MAX_MESSAGE_HTML_CHARS`; sanitizer no BFF |
| Lista `q` | título **ou** conteúdo (`name=like` / `content=like`); ver G-21 |
| Identidade | `mine` / `requester_mine` no BFF (id ou e-mail) |
| Foto | Core só se `mine`; demais iniciais |
| Kit `MessageThread` | `html` (helpdesk), `markdown`, `plain` |
| Kit strip | defesa no cliente após o BFF |
| Kit `RichTextEditor` | toolbar WYSIWYG (ênfase, cor, H2, lista, alinhamento, fonte, tabela, link, HR, fonte HTML/MD); **sem** botão de imagem |
| Kit `MentionComposer` | salas; `@` markdown por label — **não** usado no helpdesk; M-23 usa `RichTextEditor` + span por id |
| Ajuda | `helpTooltips.create` / `.detail` descrevem formatação, imagem no corpo e `@` para mencionar |

**Causa histórica do achatamento (corrigida):** o tradutor usava `display_text` no corpo. Hoje o corpo passa pelo sanitizer canônico do BFF.

**Invariante:** o MFE **não** é autoridade de sanitização. HTML cru do GLPI não entra no browser. **Responsabilidade canônica:** BFF + `platform-security-identity-authorization.mdc`.

## 6. Paridade TinyMCE (GLPI) × kit × estado na conversa

O GLPI 11 carrega TinyMCE em toda página. A doc oficial não lista os botões; a paridade abaixo usa o que o editor ITIL costuma gravar + o que o `RichTextEditor` já faz. Botão ausente no kit **não** autoriza TinyMCE no MFE.

| Capacidade | GLPI | Kit | Na conversa helpdesk |
|---|---|---|---|
| Parágrafo, quebra | sim | sim | leitura + escrita |
| Negrito / itálico / sublinhado / riscado | sim | sim | leitura + escrita |
| Lista | sim | sim | leitura + escrita |
| Título | sim (vários níveis) | H2 na toolbar | leitura `h1`–`h6`; escrita no nível do kit (H2) |
| Alinhamento | sim | sim | leitura + escrita |
| Cor / destaque | sim | sim | leitura (allowlist de `style`); escrita pelo kit |
| Fonte / tamanho | sim | sim | leitura limitada; escrita pelo kit |
| Link | sim | diálogo do kit | `http`/`https`/`mailto`; sem `javascript:` |
| Tabela | sim | sim | leitura + escrita |
| Código | sim | modo fonte + bloco | leitura + escrita |
| Citação | sim | via HTML | leitura; escrita se o kit já emitir |
| Menção `@` | plugin TinyMCE | `RichTextEditor` + `MentionMenu` (helpdesk, por **id**); salas usam `MentionComposer` (label) | leitura + escrita por `data-user-id` (E14 / M-23) |
| Imagem no corpo | insert/colar → Documento | `MentionComposer` cola blob | leitura reescrita; escrita BLOQUEADA |
| Vídeo / iframe / objeto | TinyMCE media (se ligado) | strip remove | **fora** — nunca publicar |
| Emoji | possível | unicode | unicode no texto; sem sprite do GLPI |
| Desfazer / refazer | sim | sim no editor | só no compositor |
| HTML fonte | sim | sim no editor | compositor; a bolha nunca mostra fonte |
| Documento anexo (não inline) | «Add a document» | `FilePreviewModal` | leitura na abertura; por bolha se A-07 |

## 7. Allowlist e segurança (BFF é a autoridade)

O HTML publicado **não** é o HTML do GLPI. É o resultado de um sanitizer no BFF.

### 7.1 Tags e atributos-alvo

Allowlist inicial (pode encolher; não cresce sem evidência):

| Tag | Atributos |
|---|---|
| `p`, `div`, `br`, `hr` | `style` só com `text-align` |
| `strong`, `b`, `em`, `i`, `u`, `s`, `strike`, `del` | — |
| `ul`, `ol`, `li` | — |
| `h1`…`h6` | — |
| `blockquote`, `pre`, `code` | — |
| `table`, `thead`, `tbody`, `tfoot`, `tr`, `th`, `td` | `colspan`, `rowspan` |
| `a` | `href` (`http`/`https`/`mailto`), `rel` (`noopener noreferrer`), `target` (`_blank` só com rel) |
| `img` | `src` (só URL reescrita do BFF), `alt`, `width`, `height` |
| `span` | `data-user-mention`, `data-user-id` (dígitos), classe de menção do **kit** depois do rewrite |

Remover sempre: `script`, `style`, `iframe`, `object`, `embed`, `form`, `input`, `button`, `video`, `audio`, `svg`, `math`, `link`, `meta`, `base`, `textarea`, event handlers (`on*`), `srcdoc`, `formaction`, `javascript:`, `data:`, `blob:`, `vbscript:`.

`style` no restante: só `color`, `background-color`, `text-align`, `font-size`, `font-family` com valores limitados (cor hex/`rgb`, tamanho `px`/`em`/`rem` com teto). Sem `url()`, `expression`, `position:fixed`.

### 7.2 Rewrite de documento

```text
src/href document.send.php?docid=N
  → se N ∈ attachments do chamado
      → /apps/helpdesk-api/tickets/{id}/attachments/{N}
  → senão
      → remove a imagem/link (não vazar id de outro chamado)
```

O browser **não** chama o host do GLPI. O GET já exige o token da pessoa e 404 se o documento não for daquele chamado (A-06). Blob só na memória, como a prévia atual.

### 7.3 O que o kit faz e o que não substitui o BFF

`stripDangerousRichTextTags` é defesa no cliente. Continua depois do BFF. **Não** autoriza `dangerouslySetInnerHTML` com HTML cru. O modo `markdown` do `MessageThread` **não** pode receber HTML do GLPI: ele interpreta markdown e quebraria listas/HTML.

## 8. Ledger — estado vigente

```text
IMPLEMENTADO          → já na tela/contrato
ALVO_LEITURA          → ainda não entregue (raro neste arquivo)
KIT_A_ESTENDER        → primitivo do kit ainda incompleto
HERDA_KIT             → primitivo do kit ligado
HIPOTESE_A_VALIDAR    → falta captura no pipeline real
BLOQUEADO             → evidência impede agora
CONSOLE_GLPI          → fora do MFE
FORA                  → não entra neste produto
```

### 8.1 Leitura da bolha

| ID | Capacidade | Estado | Dono |
|---|---|---|---|
| M-01 | Preservar o HTML do `content` no contrato (não passar pelo strip de rótulo) | **IMPLEMENTADO** | BFF `description_html` / `content_html` |
| M-02 | Texto plano derivado para busca, aria e fallback | **IMPLEMENTADO** | BFF `description` / `content` a partir do HTML sanitizado |
| M-03 | Parágrafo, quebra, lista, ênfase | **IMPLEMENTADO** | allowlist + `bodyMode=html` |
| M-04 | Link (`http`, `https`, `mailto`); sem `javascript:` | **IMPLEMENTADO** | sanitizer canônico no BFF |
| M-05 | Título, citação, alinhamento e cor **se** vierem no HTML | **IMPLEMENTADO** | same allowlist |
| M-06 | Tabela e bloco de código | **IMPLEMENTADO** | kit + tokens `--delpi-ui-*` |
| M-07 | Menção visível (chip), sem usar o nome como identidade | **IMPLEMENTADO** E14 | `enrichGlpiUserMentionSpans` + `bodyMode=html` |
| M-08 | Imagem **no** corpo, autenticada | **IMPLEMENTADO** | rewrite `document.send.php` → GET anexo; blob + `FilePreviewModal` |
| M-09 | Documento ligado **àquela** mensagem | HIPOTESE_A_VALIDAR (A-07) | não inventar vínculo |
| M-10 | Documento só do chamado, sem mensagem dona | **IMPLEMENTADO** na abertura | invariante até A-07 |
| M-11 | HTML de e-mail / Outlook sobrevive sanitizado | **IMPLEMENTADO** (mesmo sanitizer) | irmão do P0 |
| M-12 | `[data-form-tag]` e lixo TinyMCE | **IMPLEMENTADO** | strip; não vira controle |

### 8.2 Escrita (abrir e responder)

| ID | Capacidade | Estado | Dono quando houver código |
|---|---|---|---|
| M-20 | Compositor rico no lugar do textarea (parágrafo, ênfase, lista, link) | IMPLEMENTADO | `HelpdeskRichTextField` → `RichTextEditor` |
| M-21 | POST `content` em HTML sanitizado, não texto achatado | IMPLEMENTADO | BFF `prepare_outbound_message_html` |
| M-22 | Título, tabela, código, cor, alinhamento no compositor | IMPLEMENTADO | toolbar do `RichTextEditor` |
| M-23 | Menção no compositor (`@`) | **IMPLEMENTADO** | `RichTextEditor` + `GET /users` → span `data-user-id`; sem `MentionComposer` das salas |
| M-24 | Inserir imagem ou arquivo novo no envio | **IMPLEMENTADO** H12 | `uploadTicketAttachment` + Document |
| M-25 | Colar imagem da área de transferência | **URGENTE / DRIFT** — runtime quebra; alvo = paridade `MentionComposer` via `RichTextEditor.onPasteImages` | kit `richTextClipboardImages` + host upload |
| M-25b | Preview autenticado após F5 no compositor | **URGENTE / DRIFT** — imagem quebra no reload | `resolveAttachmentImageSrc` + persist path BFF (contrato das salas) |
| M-26 | Editar mensagem já gravada | CONSOLE_GLPI | a doc do GLPI tem Edit; o BFF não publica PATCH |
| M-27 | Modelo, origem, pendência no envio | CONSOLE_GLPI | follow-up doc |
| M-28 | Abrir e responder compartilham o mesmo compositor | IMPLEMENTADO | `HelpdeskRichTextField` |
| M-29 | Teto de tamanho do HTML no BFF | IMPLEMENTADO | `MAX_MESSAGE_HTML_CHARS = 50_000` |
| M-36 | Redimensionar imagem no compositor | **IMPLEMENTADO** | plugin-ui `richTextImageResize` (width/height HTML) |

### 8.3 Componente (kit)

| ID | Capacidade | Estado |
|---|---|---|
| M-30 | Modo de corpo **HTML já sanitizado** no `MessageThread` (além de `markdown` / `plain`) | **IMPLEMENTADO** | `bodyMode="html"` + `htmlMessageBody` |
| M-31 | `RichTextEditor` como compositor do helpdesk | HERDA_KIT — **IMPLEMENTADO** via `HelpdeskRichTextField` |
| M-32 | Prévia / modal / baixar anexo | HERDA_KIT — já ligados na abertura |
| M-33 | CSS de bolha no MFE helpdesk | proibido — factories do plugin-ui |
| M-34 | Chip de menção a partir de `data-user-id`, sem casar `@nome` | **IMPLEMENTADO** E14 | `enrichGlpiUserMentionSpans` no kit |
| M-35 | `resolveAttachmentImageSrc` para `document_id` do BFF (não `attachment:{uuid}` das salas) | **IMPLEMENTADO** (adapter no host / rewrite BFF) |

O helpdesk **não** importa `MentionComposer` das salas; M-23 reutiliza só `detectActiveMention` + `MentionMenu` no `RichTextEditor`.

### 8.4 Satélites

| ID | Capacidade | Estado |
|---|---|---|
| M-40 | `helpTooltips.create` e `.detail` descrevem formatação e imagem no corpo | IMPLEMENTADO |
| M-41 | F5 no detalhe mostra o mesmo HTML sanitizado | invariante de persistência (dono = GLPI) |
| M-42 | Lista / `q` / cartão **não** passam a buscar HTML | FORA deste inventário; busca no texto da abertura é G-21 em [`13-listagem-de-chamados.md`](./13-listagem-de-chamados.md) |
| M-43 | Log do BFF continua sem corpo da mensagem | invariante [`04-seguranca.md`](./04-seguranca.md) |

## 9. Ownership — produtores e consumidores

```text
PRODUCER          GLPI Ticket.content / Followup.content (HTML)
TRANSFORMER       mapping.py (sanitize + rewrite + derive text) + message_html_sanitizer
CANONICAL OWNER   helpdesk-api (contrato do corpo)
CONSUMERS         MFE helpdesk (MessageThread, create form, reply)
NÃO-CONSUMIDOR    api-delpi, Chat AI, portal (não leem este JSON)
FALLBACK          content_text / description atual (texto)
PERSISTENCE       GLPI; Minha DELPI não grava o corpo
RELOAD            GET /tickets/{id} de novo (F5)
SURFACES          /tickets/new, /tickets/{id}, (lista não mostra corpo)
TESTS             test_mapping_* ; testes de sanitizer/rewrite ainda inexistentes
DOCS/HELP         este arquivo + helpTooltips no entregável de código
```

Ler o MFE (`conversationMessages`, `HelpdeskMessageThread`, formulário de abertura) **antes** de mudar o JSON. Não mudar `description` / `timeline[].content` de texto para HTML no mesmo campo.

## 10. Contrato-alvo (quando for implementar)

Decisão travada neste inventário: evolução **ADDITIVE**. Não é etapa de código.

Campos atuais permanecem **texto puro** (rótulo, aria, fallback, testes vigentes):

| Hoje | Permanece | Novo (opcional no JSON) |
|---|---|---|
| `description` | texto derivado do HTML sanitizado | `description_html` |
| `timeline[].content` | texto derivado | `timeline[].content_html` |
| POST `description` / `content` | aceitar HTML **ou** texto; o BFF sanitiza e grava `content` no GLPI | sem path novo |

Classificação (`contract-evolution-backward-compatibility.mdc`): **ADDITIVE** nos GET. POST no mesmo campo com HTML é **BEHAVIORAL** para o GLPI (já aceita string) e para o BFF (hoje reenvia cru). O MFE antigo que continuar em `plain` **não quebra** se os campos atuais seguirem texto.

Não publicar: e-mail do autor, `data-user-id` cru além do necessário ao chip, path `/front/document.send.php`, HTML sem sanitizar.

Compatibilidade de escrita: um cliente que ainda envia texto puro continua válido (`<p>` implícito ou texto). Um cliente novo envia HTML da allowlist.

## 11. Arquitetura-alvo (quando for implementar)

Não executar agora. Só trava o ownership correto.

```text
GLPI HTML (Ticket.content / Followup.content)
  → BFF: allowlist + rewrite de documento + deriva texto puro
  → contrato: *_html (seguro) + description/content (texto)
  → MFE: MessageThread modo HTML do kit  render-only
  → compositor: RichTextEditor → POST HTML → BFF sanitiza de novo → GLPI
```

| Camada | Faz | Não faz |
|---|---|---|
| Domain/BFF | allowlist, rewrite, `mine` por id/e-mail, teto de tamanho | regra de bolha, CSS |
| Contrato | HTML seguro + texto; `mine` | e-mail cru, path do GLPI |
| plugin-ui | modo HTML, editor, modal, chip por id | path `/apps/helpdesk` |
| MFE | monta factory, passa `mine` e blobs | strip/sanitize paralelo, `if` de formatação |

Campos de rótulo (`title`, nomes) continuam em `display_text`. Conteúdo de mensagem **não** reutiliza essa função.

## 12. Superfícies (fluxo × recorte)

| Fluxo | Superfície | Papel deste inventário |
|---|---|---|
| Ler abertura | detalhe, primeira bolha | P0 — HTML + imagem |
| Ler acompanhamento | detalhe, demais bolhas | irmão |
| F5 / Atualizar | mesmo GET | M-41 |
| Abrir chamado | `/tickets/new` descrição | M-20/M-21/M-28 |
| Responder | rodapé do detalhe | mesmo compositor |
| Prévia de anexo | `belowBody` + modal | herda; não some quando houver `<img>` |
| Lista / filtro / `q` | `/apps/helpdesk` | FORA — título |
| Console técnico | host GLPI | FORA |
| Ajuda | `helpTooltips` | M-40 |
| Tema claro/escuro | tokens do kit | invariante |

## 13. Estado antes × depois (perceptível)

| Caso | Antes (pré-E8) | Depois (vigente) |
|---|---|---|
| P0 — imagem no fio (id 6288 **inexistente**; substituto **1108**) | — | **ATENDIDO** — `<img>` no HTML usa GET BFF; F5 sem cookie GLPI; `docid` alheio some; A-07 sem vínculo por bolha |
| Irmão — listas e link num follow-up | uma linha corrida | **ATENDIDO** — HTML sanitizado na bolha |
| Irmão — follow-up de e-mail | texto achatado | HTML sanitizado; `cid:` some |
| Negativo — HTML com script | sumia tudo | **ATENDIDO** — allowlist; sem execução |
| Negativo — `src` para host do GLPI | — | **ATENDIDO** — não sobrevive no HTML publicado |
| Invariante | privado, tarefa, solução write, entidade | não mudam; upload = H12 |
| Identidade | id / e-mail | não volta a usar nome |
| Contrato antigo | `description` texto | continua texto; HTML no campo novo |

## 14. Decisões travadas × ainda não prontas

### Travadas (READY_CONFIRMED / READY_BOUNDED)

| ID | Decisão | Evidência |
|---|---|---|
| D-01 | Evolução ADDITIVE (`description_html` / `content_html`); campos atuais ficam texto | contrato vigente + consumidores `plain` |
| D-02 | Sanitizer allowlist no BFF; kit é defesa | strip do kit é denylist |
| D-03 | Sem TinyMCE; HTML só via kit `bodyMode=html` (não renderer no MFE) | kit + boundaries |
| D-04 | Sem `MentionComposer` no helpdesk | menção `@` = M-23; cola/upload = H12 no RichTextEditor |
| D-05 | Browser não chama o host do GLPI | A-06 + 04-segurança |
| D-06 | Identidade continua id ou e-mail | C-05 |
| D-07 | Um compositor para abrir e responder | SRP |
| D-08 | Lista/`q` não muda neste trabalho | L-01 |
| D-09 | Sem PATCH, privado, tarefa, solução, modelo | 10 + follow-up doc |
| D-10 | API legada só Document (H12) | HLAPI dona do chamado; sem multipart HLAPI |

### Não prontas (não viram receita E*.S*)

| ID | Falta | Bloqueia |
|---|---|---|
| H1–H4 | captura do `content` cru (6288 inexistente; 1108/1045/467) | **fechado** em §15 — M-08 liberado; A-07 permanece FORA |
| H5 menção | lista HLAPI de usuários por **id** via `GET /users` | M-23 **IMPLEMENTADO**; M-07 **IMPLEMENTADO** E14 (attrs `data-user-*` no bleach) |
| H6 teto | tamanho máximo que o GLPI/BFF aceita | M-29 = 50 000 caracteres no BFF |

## 15. Hipóteses de imagem — vereditos (E6.S1, 21/09/2026)

Captura HLAPI `GET /Assistance/Ticket/{id}` + Timeline + um item da lista. Só chaves e formato do `content` (tags / padrão de URL). Sem corpo pessoal.

O id **6288 não existe** neste GLPI (`MAX(id)=1119`). Substitutos com `<img>`: 1108 (content + Timeline `Document`), 1045 e 467 (Followup/Solution).

| ID | Veredito | Evidência |
|---|---|---|
| H1 | **PROVEN** | `content` traz `<img>` / `<a>` com `src`/`href` relativo `/front/document.send.php` e query `docid` (+ `items_id`, `itemtype`) |
| H2 | **FORA** | nenhum data-URI `data:image` nem URL absoluta do host nos corpos amostrados |
| H3 | **FORA** | 6288 inexistente; 1108 tem `<img>` **e** item Timeline `Document` (`documents_id`) |
| H4 | **FORA** (A-07) | schema e JSON de `Followup` **não** listam documentos; `Document` é tipo irmão na Timeline |

M-08 (rewrite de `document.send.php`) **IMPLEMENTADO** (E8.S1 + E8.S2 + E8.S4). M-09 / A-07 **não** desbloqueiam: a imagem no HTML e o `Document` da Timeline não vêm amarrados ao Followup — a bolha de acompanhamento **não** ganha `belowBody` inventado.

## 15b. Menção — vereditos (E14, 21/09/2026)

| ID | Veredito | Evidência |
|---|---|---|
| M-07 leitura | **IMPLEMENTADO** | BFF preserva `data-user-mention`/`data-user-id` (dígitos); kit `enrichGlpiUserMentionSpans` + `MessageThread` `bodyMode=html` aplica chip; identidade = id, rótulo = texto do span |
| M-23 escrita `@` | **IMPLEMENTADO** | create/reply → `RichTextEditor` + `GET /users` → span `data-user-id`; sem `MentionComposer` das salas |

M-23 fechado com catálogo assignee (`GET /users`). Não reabrir E8/E14.

## 16. Prova, quando houver autorização

| Caso | Resultado |
|---|---|
| Positivo — formatação | um follow-up com negrito e lista no GLPI aparece com negrito e lista na Minha DELPI |
| Irmão — link | `https://` abre; `javascript:` não entra no HTML publicado |
| Irmão — e-mail | HTML de Outlook não quebra a bolha; script/`cid:` somem |
| Negativo — XSS | `<script>`, `iframe` e `onerror` não sobrevivem ao BFF |
| Positivo — imagem (se H1/H2) | a `<img>` usa o GET autenticado do BFF; F5 não pede cookie do GLPI |
| Irmão — anexo sem HTML | prévia no `belowBody` continua |
| Negativo — A-07 | sem evidência de vínculo, a imagem de outro follow-up não muda de bolha |
| Negativo — documento alheio | `docid` fora de `attachments` some do HTML; GET continua 404 |
| Escrita | o HTML enviado reaparece no GLPI e, no reload, na bolha |
| Cliente antigo | GET sem usar `*_html` continua vendo texto; não vê tags cruas |
| Identidade | dois «Roberio» com id diferente não trocam foto; menção não casa por nome |
| Tema | tokens do kit; sem verde do GLPI |

Testes de unidade do mapping **atual** (`strips_html`) **não** podem ser invertidos para “aceitar o HTML cru”. Quando M-01 existir, o teste passa a: texto derivado sem tags + HTML sanitizado sem script. Alterar o expected para esconder XSS é proibido.

## 17. Ajuda in-app (satélite)

Quando houver implementação, no **mesmo** entregável, sem path de API:

| Tooltip | Vigente |
|---|---|
| `helpTooltips.create` / `createUi.*` | formatação, clipe/colar, resize; textos curtos |
| `helpTooltips.detail` / `detailUi.*` | conversa, reply, attach, attachments, openInGlpi |
| `attachHint` | clipe na abertura e na resposta |

## 18. O que este arquivo não faz

- não abre E*.S* nem marca H5 `PROVEN`;
- não cria HD-019;
- não liga a API legada **além** da exceção H12 Document já PROVEN;
- não autoriza PATCH de follow-up, tarefa, solução ou privado;
- não autoriza renderer HTML no MFE fora do kit;
- não trata nome como identidade;
- não muda busca da lista;
- não autoriza investigação live que grave senha ou corpo em log.

Quando o pedido for **nova** capacidade de corpo (ex.: M-23 `@`, A-07 vínculo por bolha), revalidar HLAPI + ownership antes de abrir plano. M-01…M-22, M-24…M-25, M-28…M-36 e E14/H12 já estão no código; não reabrir como inventário «a implementar».

Capacidades de Assistência que não são corpo da mensagem (Forms, SLA, vínculos): [`15-capacidades-glpi.md`](./15-capacidades-glpi.md).
