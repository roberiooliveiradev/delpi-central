# 12 — Conteúdo da mensagem da conversa

> **Status:** inventário. Ordem de código: [`16-plano-paridade.md`](./16-plano-paridade.md) E8 (HD-021, HD-022). Não altera [`06-plano-execucao.md`](./06-plano-execucao.md).
> **Pedido:** o componente de mensagem deve cobrir o que o GLPI já entrega no fio público do chamado (texto, formatação, imagem e afins). Este arquivo só documenta.
> **Tela publicada:** [`WIREFRAMES.md`](./WIREFRAMES.md) §3 — hoje `bodyMode=plain` e descrição em texto puro. O desenho publicado **não** muda até haver autorização de código.
> **Conversa (estrutura):** [`10-conversa-do-chamado.md`](./10-conversa-do-chamado.md).
> **Contrato vigente (texto puro):** [`03-contrato.md`](./03-contrato.md). Evolução do corpo: §10 deste arquivo.
> **Identidade:** id do GLPI ou e-mail; nome é rótulo, nunca chave. [`04-seguranca.md`](./04-seguranca.md).
> **Lacuna de experiência:** C-08 em [`11-lacunas-da-experiencia.md`](./11-lacunas-da-experiencia.md).

Este documento responde: o que o GLPI considera conteúdo de uma mensagem, o markup que a HLAPI 2.2 devolve, o que a Minha DELPI faz hoje, o contrato-alvo e o que **deve** entrar no componente quando houver autorização de código.

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

Isto **estende** HD-009 (detalhe), HD-010 (abrir), HD-013 (acompanhamento) e HD-016 (ajuda). Não é HD-019. H5 (anexo novo, satisfação, bancada) não abre por este inventário.

## 2. Fontes e grau de evidência

| Fonte | Classe | Uso |
|---|---|---|
| [Tickets](https://help.glpi-project.org/documentation/modules/assistance/tickets) | CONFIRMADO_EM_DOCUMENTACAO_CANONICA | o chamado nasce com conteúdo; o ciclo de vida não redefine o editor |
| [Followup](https://help.glpi-project.org/documentation/modules/assistance/tabs/followup) | CONFIRMADO_EM_DOCUMENTACAO_CANONICA | comentário, documento opcional, motivo de pendência, modelo, origem, privado, editar, promover a chamado. **Não** descreve as teclas do TinyMCE |
| [Documents](https://help.glpi-project.org/documentation/modules/management/documents) | CONFIRMADO_EM_DOCUMENTACAO_CANONICA | arquivo ou link; item associado inclui `Ticket`, `Followup`, `Solution`; MIME/extensão no Setup |
| Changelog HLAPI 11 (`html` + `x-supports-mentions`) | CONFIRMADO_EM_DOCUMENTACAO_CANONICA | schema marca conteúdo rico e menção |
| Schema HLAPI 2.2 no GLPI 11.0.5 (`Ticket.content`, `Followup.content`) | CONFIRMADO_NO_CODIGO | `format=HTML`, `x-supports-mentions=true` |
| Código / CSS GLPI (`[data-user-mention="true"]`, `document.send.php?docid=`) | CONFIRMADO_NO_CODIGO (upstream) | markup de menção e de imagem embutida |
| Colar imagem no TinyMCE → `image_paste*.png` + Documento | CONFIRMADO_EM_DOCUMENTACAO_CANONICA (issues 11.0.6/11.0.7) | escrita de imagem **é upload**; A-08 |
| `GET /session`, `team[].id`, `Followup.user.id` | CONFIRMADO_NO_CODIGO | identidade; fora do corpo |
| `helpdesk_app/.../mapping.py` `display_text` / `_text` | CONFIRMADO_NO_CODIGO | o BFF remove toda tag HTML do conteúdo |
| Teste `test_mapping_repairs_legacy_text_and_strips_html` | CONFIRMADO_EM_TESTE | `<p>…</p>` vira texto puro |
| `HelpdeskMessageThread` `bodyMode="plain"` | CONFIRMADO_NO_CODIGO | a bolha mostra texto cru |
| `stripDangerousRichTextTags` | CONFIRMADO_NO_CODIGO | **denylist** de 6 tags; não é allowlist |
| `MessageThread` + `RichTextEditor` no plugin-ui | CONFIRMADO_NO_CODIGO | kit sanitiza markdown/HTML no cliente e tem editor rico; o helpdesk não os usa no fio |
| `MentionComposer` | CONFIRMADO_NO_CODIGO | compositor das **salas**; cola imagem inline; **não** é o compositor do helpdesk |
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

Perfil GLPI pode desligar ou restringir menção (Assistance: Disabled / Full / Restricted aos atores). O BFF **lê** o que já foi gravado; não precisa reimplementar essa política na leitura. Na escrita, a lista de quem pode ser mencionado depende do perfil — HIPOTESE até haver endpoint HLAPI de atores/usuários mencionáveis; sem isso M-23 não vira etapa.

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
- enviar arquivo novo: BLOQUEADO (HLAPI JSON-only, API legada desligada) — A-08 / HD-017 fora;
- imagem no HTML da mensagem: leitura possível se a URL for reescrita para o download autenticado do BFF; escrita de imagem nova no compositor = mesmo bloqueio de A-08.

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

Não há, neste inventário, operação HLAPI de “usuários mencionáveis” confirmada. M-23 permanece dependente disso.

## 5. O que a Minha DELPI faz hoje

```text
GLPI HTML
  → mapping.display_text / _text  (remove <…>, repara CP850, unescape)
  → description / timeline[].content  texto puro
  → HelpdeskMessageThread bodyMode=plain
  → bolha sem formatação
```

| Superfície | Hoje |
|---|---|
| Abertura | título + texto sem marca; anexos do chamado no `belowBody` da abertura |
| Acompanhamento | texto sem marca; sem arquivo próprio (A-07) |
| Responder / abrir | `HelpdeskTextArea` — texto puro; POST reenvia string como `content` |
| Validação de escrita | não vazio; sem teto de tamanho nem sanitizer HTML |
| Lista `q` | só título (`name=like=`); HTML da descrição **não** entra na busca |
| Identidade | `mine` / `requester_mine` no BFF (id ou e-mail) |
| Foto | Core só se `mine`; demais iniciais |
| Kit `MessageThread` | `markdown` (converte MD → HTML, `dangerouslySetInnerHTML`) e `plain`; **não** tem modo `html` |
| Kit strip | remove `script`, `style`, `iframe`, `object`, `embed`, `form`; **mantém** o resto, inclusive `on*` e `src` arbitrário |
| Kit `RichTextEditor` | toolbar WYSIWYG (ênfase, cor, H2, lista, alinhamento, fonte, tabela, link, fonte HTML/MD); **sem** botão de imagem |
| Kit `MentionComposer` | salas; `@` + cola imagem; **proibido** no helpdesk enquanto A-08 existir |
| Ajuda | `helpTooltips.create` / `.detail` descrevem texto e prévia de anexo, não formatação no corpo |

**Causa do achatamento:** o tradutor trata conteúdo de mensagem com a mesma função de rótulo (`display_text`). Não é limitação do GLPI.

**⚠ Desvio se o MFE renderizar o HTML do GLPI com o strip do kit:** o cliente não é autoridade de sanitização; o strip não é allowlist. **Responsabilidade canônica:** `platform-security-identity-authorization.mdc` + BFF. **Risco:** XSS e o browser ir a `helpdesk.centraldelpi.com.br`.

## 6. Paridade TinyMCE (GLPI) × kit × alvo

O GLPI 11 carrega TinyMCE em toda página. A doc oficial não lista os botões; a paridade abaixo usa o que o editor ITIL costuma gravar + o que o `RichTextEditor` já faz. Botão ausente no kit **não** autoriza TinyMCE no MFE.

| Capacidade | GLPI | Kit hoje | Alvo na conversa |
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
| Menção `@` | plugin TinyMCE | `MentionText` / `MentionComposer` (salas, por **label**) | leitura por `data-user-id`; escrita só com catálogo por **id** |
| Imagem no corpo | insert/colar → Documento | `MentionComposer` cola blob | leitura reescrita; escrita BLOQUEADA |
| Vídeo / iframe / objeto | TinyMCE media (se ligado) | strip remove | **fora** — nunca publicar |
| Emoji | possível | unicode | unicode no texto; sem sprite do GLPI |
| Desfazer / refazer | sim | sim no editor | só no compositor |
| HTML fonte | sim | sim no editor | compositor; a bolha nunca mostra fonte |
| Documento anexo (não inline) | «Add a document» | `FilePreviewModal` | leitura na abertura (hoje); por bolha se A-07 |

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

## 8. Ledger — o que deve ser implementado

Estado neste inventário (nenhum item autoriza diff):

```text
ALVO_LEITURA          → a bolha deve mostrar o que o GLPI já gravou
ALVO_ESCRITA          → abrir / responder deve gravar o mesmo tipo de conteúdo
KIT_A_ESTENDER        → o primitivo falta no plugin-ui; o helpdesk não copia CSS
HERDA_KIT             → o primitivo já existe; só ligar
HIPOTESE_A_VALIDAR    → falta captura no pipeline real
BLOQUEADO             → evidência impede agora
CONSOLE_GLPI          → fora do MFE
FORA                  → não entra neste produto
```

### 8.1 Leitura da bolha

| ID | Capacidade | Estado | Dono quando houver código |
|---|---|---|---|
| M-01 | Preservar o HTML do `content` no contrato (não passar pelo strip de rótulo) | ALVO_LEITURA | BFF: campo HTML distinto de `display_text` |
| M-02 | Texto plano derivado para busca, aria e fallback | ALVO_LEITURA | BFF, a partir do HTML sanitizado |
| M-03 | Parágrafo, quebra, lista, ênfase | ALVO_LEITURA | kit + MFE render-only |
| M-04 | Link (`http`, `https`, `mailto`); sem `javascript:` | ALVO_LEITURA | sanitizer canônico no BFF |
| M-05 | Título, citação, alinhamento e cor **se** vierem no HTML | ALVO_LEITURA | same allowlist |
| M-06 | Tabela e bloco de código | ALVO_LEITURA | kit; tokens `--delpi-ui-*` |
| M-07 | Menção visível (chip), sem usar o nome como identidade | ALVO_LEITURA | parse `data-user-id`; rótulo só visual |
| M-08 | Imagem **no** corpo, autenticada | ALVO_LEITURA + HIPOTESE URL | rewrite `src` para o GET de anexo; clique reusa `FilePreviewModal` |
| M-09 | Documento ligado **àquela** mensagem | HIPOTESE_A_VALIDAR (A-07) | não inventar vínculo |
| M-10 | Documento só do chamado, sem mensagem dona | IMPLEMENTADO hoje na abertura | invariante até A-07 |
| M-11 | HTML de e-mail / Outlook sobrevive sanitizado | ALVO_LEITURA | mesmo sanitizer; irmão do P0 |
| M-12 | `[data-form-tag]` e lixo TinyMCE | ALVO_LEITURA | strip; não vira controle |

### 8.2 Escrita (abrir e responder)

| ID | Capacidade | Estado | Dono quando houver código |
|---|---|---|---|
| M-20 | Compositor rico no lugar do textarea (parágrafo, ênfase, lista, link) | ALVO_ESCRITA | `RichTextEditor` do kit (`HERDA_KIT`) |
| M-21 | POST `content` em HTML sanitizado, não texto achatado | ALVO_ESCRITA | mesmos paths; semântica HTML |
| M-22 | Título, tabela, código, cor, alinhamento no compositor | ALVO_ESCRITA | toolbar do `RichTextEditor` |
| M-23 | Menção no compositor (`@`) | ALVO_ESCRITA + HIPOTESE catálogo | só com id; sem `MentionComposer` das salas |
| M-24 | Inserir imagem ou arquivo novo no envio | BLOQUEADO | A-08; JSON-only |
| M-25 | Colar imagem da área de transferência | BLOQUEADO | vira upload |
| M-26 | Editar mensagem já gravada | CONSOLE_GLPI | a doc do GLPI tem Edit; o BFF não publica PATCH |
| M-27 | Modelo, origem, pendência no envio | CONSOLE_GLPI | follow-up doc |
| M-28 | Abrir e responder compartilham o mesmo compositor | ALVO_ESCRITA | uma factory; sem editor paralelo |
| M-29 | Teto de tamanho do HTML no BFF | ALVO_ESCRITA | definir no plano de código; hoje só “não vazio” |

### 8.3 Componente (kit)

| ID | Capacidade | Estado |
|---|---|---|
| M-30 | Modo de corpo **HTML já sanitizado** no `MessageThread` (além de `markdown` / `plain`) | KIT_A_ESTENDER |
| M-31 | `RichTextEditor` como compositor do helpdesk | HERDA_KIT |
| M-32 | Prévia / modal / baixar anexo | HERDA_KIT — já ligados na abertura |
| M-33 | CSS de bolha no MFE helpdesk | proibido — factories do plugin-ui |
| M-34 | Chip de menção a partir de `data-user-id`, sem casar `@nome` | KIT_A_ESTENDER (hoje `MentionText` é label) |
| M-35 | `resolveAttachmentImageSrc` para `document_id` do BFF (não `attachment:{uuid}` das salas) | KIT_A_ESTENDER ou adapter no host |

Enquanto M-30 não existir, o helpdesk **não** implementa um renderer HTML próprio e **não** reusa `bodyMode=markdown` para HTML do GLPI.

### 8.4 Satélites

| ID | Capacidade | Estado |
|---|---|---|
| M-40 | `helpTooltips.create` e `.detail` descrevem formatação e imagem no corpo | ALVO_LEITURA + ALVO_ESCRITA — mesmo entregável |
| M-41 | F5 no detalhe mostra o mesmo HTML sanitizado | invariante de persistência (dono = GLPI) |
| M-42 | Lista / `q` / cartão **não** passam a buscar HTML | FORA deste inventário; busca no texto da abertura é G-21 em [`13-listagem-de-chamados.md`](./13-listagem-de-chamados.md) |
| M-43 | Log do BFF continua sem corpo da mensagem | invariante [`04-seguranca.md`](./04-seguranca.md) |

## 9. Ownership — produtores e consumidores

```text
PRODUCER          GLPI Ticket.content / Followup.content (HTML)
TRANSFORMER       mapping.py (hoje display_text; alvo: sanitize + rewrite + derive text)
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

## 13. Estado antes × depois (alvo perceptível)

| Caso | Hoje | Alvo |
|---|---|---|
| P0 — chamado 6288 com imagem no fio | texto sem marca; imagem no máximo como anexo da abertura | texto formatado; imagem no lugar em que o GLPI a gravou, via BFF |
| Irmão — listas e link num follow-up | uma linha corrida | lista e link clicável (https) |
| Irmão — follow-up de e-mail | texto achatado | HTML sanitizado; `cid:` some |
| Negativo — HTML com script | hoje some tudo; amanhã o script continua fora | allowlist; sem execução |
| Negativo — `src` para host do GLPI | — | não sobrevive no HTML publicado |
| Invariante | privado, tarefa, solução, entidade, upload novo | não mudam |
| Identidade | id / e-mail | não volta a usar nome |
| Contrato antigo | `description` texto | continua texto; HTML no campo novo |

## 14. Decisões travadas × ainda não prontas

### Travadas (READY_CONFIRMED / READY_BOUNDED)

| ID | Decisão | Evidência |
|---|---|---|
| D-01 | Evolução ADDITIVE (`description_html` / `content_html`); campos atuais ficam texto | contrato vigente + consumidores `plain` |
| D-02 | Sanitizer allowlist no BFF; kit é defesa | strip do kit é denylist |
| D-03 | Sem TinyMCE e sem renderer HTML no MFE | kit + boundaries |
| D-04 | Sem `MentionComposer` no helpdesk | cola imagem = A-08; menção por label |
| D-05 | Browser não chama o host do GLPI | A-06 + 04-segurança |
| D-06 | Identidade continua id ou e-mail | C-05 |
| D-07 | Um compositor para abrir e responder | SRP |
| D-08 | Lista/`q` não muda neste trabalho | L-01 |
| D-09 | Sem PATCH, privado, tarefa, solução, modelo | 10 + follow-up doc |
| D-10 | Sem API legada / multipart | A-08 |

### Não prontas (não viram receita E*.S*)

| ID | Falta | Bloqueia |
|---|---|---|
| H1–H4 | captura do `content` cru no 6288 e no 1114 | M-08, M-09 |
| H5 menção | markup exato + lista HLAPI de mencionáveis | M-23, parte de M-07 se o atributo divergir |
| H6 teto | tamanho máximo que o GLPI/BFF aceita | M-29 (número) |

## 15. Hipóteses a fechar **antes** de receitar o rewrite de imagem

```text
H1  o HTML de produção aponta para /front/document.send.php?docid=N
H2  o HTML embute data-URI ou URL absoluta do host do GLPI
H3  a imagem do 6288 é só Document da Timeline, sem <img> no content
H4  o Followup da HLAPI traz lista de documentos (fecha A-07) ou não traz
```

Uma captura do `GET /tickets/{id}` (BFF) **e** do `content` cru do GLPI no 6288 e no 1114 decide H1–H4. Sem isso, M-08 e M-09 não viram etapa executável.

Como capturar (quando autorizado a **investigar**, ainda sem produto):

1. no GLPI, abrir o chamado 6288 como o mesmo perfil do token;
2. no BFF, log temporário **proibido** (corpo não vai a log);
3. caminho aceitável: teste de homologação que persiste o `content` **só** em fixture de teste, sem commit de dado pessoal; ou inspeção na HLAPI com o token da sessão, sem gravar senha.

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

| Tooltip | Hoje | Alvo |
|---|---|---|
| `helpTooltips.create` | título e descrição à esquerda | descrever que a descrição aceita formatação (negrito, lista, link); sem imagem nova |
| `helpTooltips.detail` | foto só nas minhas; prévia de anexo; sem arquivo novo | + formatação na conversa; imagem no texto quando o helpdesk já tiver o arquivo; sem colar imagem |

## 18. O que este arquivo não faz

- não abre E*.S* nem marca H5 `PROVEN`;
- não cria HD-019;
- não liga a API legada;
- não autoriza PATCH de follow-up, tarefa, solução ou privado;
- não autoriza renderer HTML no MFE fora do kit;
- não trata nome como identidade;
- não muda busca da lista;
- não autoriza investigação live que grave senha ou corpo em log.

Quando o pedido passar de «documentar» para «implementar», a primeira subetapa é fechar H1–H4 no pipeline real e classificar a evolução do contrato (já pré-classificada aqui como ADDITIVE). Só então M-01…M-23 viram plano executável.

Capacidades de Assistência que não são corpo da mensagem (Forms, SLA, vínculos): [`15-capacidades-glpi.md`](./15-capacidades-glpi.md).
