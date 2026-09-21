# 12 — Conteúdo da mensagem da conversa

> **Status:** inventário e alvo. **Não autoriza implementação.** Não altera [`06-plano-execucao.md`](./06-plano-execucao.md).
> **Pedido:** o componente de mensagem deve cobrir o que o GLPI já entrega no fio público do chamado (texto, formatação, imagem e afins). Este arquivo só documenta.
> **Tela publicada:** [`WIREFRAMES.md`](./WIREFRAMES.md) §3 — hoje `bodyMode=plain` e descrição em texto puro.
> **Conversa (estrutura):** [`10-conversa-do-chamado.md`](./10-conversa-do-chamado.md).
> **Contrato vigente:** [`03-contrato.md`](./03-contrato.md).
> **Identidade:** id do GLPI ou e-mail; nome é rótulo, nunca chave. [`04-seguranca.md`](./04-seguranca.md).

Este documento responde: o que o GLPI considera conteúdo de uma mensagem, o que a HLAPI 2.2 devolve, o que a Minha DELPI faz hoje e o que **deve** entrar no componente quando houver autorização de código.

## 1. Recorte do produto

A mensagem é o corpo da bolha na conversa do colaborador:

```text
abertura      = Ticket.name (título) + Ticket.content
acompanhamento = Followup.content  (público)
```

Não é o formulário central do técnico. Tarefa, solução, aprovação, modelo, origem, pendência, promover a chamado e base de conhecimento continuam no console (`helpdesk.console`), como já travado em [`10-conversa-do-chamado.md`](./10-conversa-do-chamado.md).

Há dois fluxos distintos. Um não implica o outro:

| Fluxo | Pergunta |
|---|---|
| Leitura | o que já está no GLPI precisa aparecer na bolha? |
| Escrita | o que a pessoa pode gravar ao abrir ou responder? |

## 2. Fontes e grau de evidência

| Fonte | Classe | Uso |
|---|---|---|
| [Tickets](https://help.glpi-project.org/documentation/modules/assistance/tickets) | CONFIRMADO_EM_DOCUMENTACAO_CANONICA | o chamado nasce com conteúdo; o ciclo de vida não redefine o editor |
| [Followup](https://help.glpi-project.org/documentation/modules/assistance/tabs/followup) | CONFIRMADO_EM_DOCUMENTACAO_CANONICA | comentário, documento opcional, motivo de pendência, modelo, origem, privado, editar, promover a chamado |
| [Documents](https://help.glpi-project.org/documentation/modules/management/documents) | CONFIRMADO_EM_DOCUMENTACAO_CANONICA | arquivo ou link; item associado inclui `Ticket`, `Followup`, `Solution`; tipos MIME/extensão no Setup |
| Schema HLAPI 2.2 no GLPI 11.0.5 (`Ticket.content`, `Followup.content`) | CONFIRMADO_NO_CODIGO | `format=HTML`, `x-supports-mentions=true` |
| `GET /session`, `team[].id`, `Followup.user.id` | CONFIRMADO_NO_CODIGO | identidade; fora do corpo |
| `helpdesk_app/.../mapping.py` `display_text` / `_text` | CONFIRMADO_NO_CODIGO | o BFF remove toda tag HTML do conteúdo |
| `HelpdeskMessageThread` `bodyMode="plain"` | CONFIRMADO_NO_CODIGO | a bolha mostra texto cru |
| `MessageThread` + `RichTextEditor` no plugin-ui | CONFIRMADO_NO_CODIGO | kit já sanitiza markdown/HTML e tem editor rico; o helpdesk não os usa no fio |
| URL exata da `<img>` embutida no HTML de produção | HIPOTESE_A_VALIDAR | típico `document.send.php` / `docid`; precisa de captura no chamado 6288 |
| Vínculo documento↔acompanhamento na Timeline | HIPOTESE_A_VALIDAR | já é A-07 em [`11-lacunas-da-experiencia.md`](./11-lacunas-da-experiencia.md) |

A documentação oficial do follow-up descreve o **fluxo** (Responder, comentário, documento, pendência). O **formato do comentário** (HTML, menção, imagem no meio do texto) está no schema da HLAPI e na interface TinyMCE do GLPI 11, não num capítulo isolado de “rich text”.

## 3. O que o GLPI coloca numa mensagem

### 3.1 Corpo (abertura e acompanhamento público)

| Peça | Onde o GLPI guarda | Evidência |
|---|---|---|
| Parágrafo e quebra de linha | `content` HTML (`<p>`, `<br>`) | schema `FORMAT_STRING_HTML` |
| Negrito, itálico, sublinhado, riscado | tags de ênfase no HTML | editor do chamado / follow-up |
| Lista ordenada e não ordenada | `<ul>`, `<ol>`, `<li>` | editor |
| Título / subtítulo | `<h1>`…`<h6>` quando o editor oferece | editor |
| Alinhamento e cor | `style` / alinhamento no HTML | editor |
| Link | `<a href>` | editor |
| Tabela | `<table>` | editor |
| Citação / bloco | `<blockquote>` | editor |
| Código | `<pre>`, `<code>` | editor |
| Menção a usuário | HTML com marca de menção | `x-supports-mentions` em `Ticket.content` e `Followup.content` |
| Imagem no meio do texto | `<img>` no HTML, em geral um Documento | foto do chamado 6288; URL exata HIPOTESE |
| Documento ao lado do texto | item `Document` ligado a `Ticket` ou `Followup` | doc de Documents + follow-up «Add a document» |

O título do chamado (`Ticket.name`) não é HTML. Na Minha DELPI ele já é `headingText` da abertura.

### 3.2 Metadados do follow-up que **não** são o corpo

A doc de follow-up lista ações ao redor do comentário. Na conversa do colaborador elas **não** viram peça da bolha:

| Peça GLPI | Destino |
|---|---|
| Origem (Direct, E-Mail, Helpdesk, Phone…) | CONSOLE_GLPI |
| Modelo de acompanhamento | CONSOLE_GLPI |
| Motivo de pendência (o chamado pode ir a pendente) | CONSOLE_GLPI |
| Privado / público | privado já some da `timeline` |
| Editar follow-up | CONSOLE_GLPI até existir PATCH no contrato |
| Promover follow-up a chamado | CONSOLE_GLPI |
| Buscar / gravar na base de conhecimento | CONSOLE_GLPI |
| Notificação por e-mail | servidor GLPI; não é UI |

### 3.3 Documento

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
| Responder / abrir | `HelpdeskTextArea` — texto puro |
| Identidade | `mine` / `requester_mine` no BFF (id ou e-mail) |
| Foto | Core só se `mine`; demais iniciais |
| Kit | `MessageThread` sabe `markdown` (sanitizado) e `plain`; não tem modo `html` do GLPI |
| Kit | `RichTextEditor` + `stripDangerousRichTextTags` existem e não são o compositor do helpdesk |

**Causa do achatamento:** o tradutor trata conteúdo de mensagem com a mesma função de rótulo (`display_text`). Não é limitação do GLPI.

## 6. Ledger — o que deve ser implementado

Estado neste inventário (nenhum item autoriza diff):

```text
ALVO_LEITURA          → a bolha deve mostrar o que o GLPI já gravou
ALVO_ESCRITA          → abrir / responder deve gravar o mesmo tipo de conteúdo
KIT_A_ESTENDER        → o primitivo falta no plugin-ui; o helpdesk não copia CSS
HERDA_KIT             → o primitivo já existe; só ligar
HIPOTESE_A_VALIDAR    → falta captura no pipeline real
BLOQUEADO             → evidência impede agora
CONSOLE_GLPI          → fora do MFE
```

### 6.1 Leitura da bolha

| ID | Capacidade | Estado | Dono quando houver código |
|---|---|---|---|
| M-01 | Preservar o HTML do `content` no contrato (não passar pelo strip de rótulo) | ALVO_LEITURA | BFF: campo de conteúdo distinto de `display_text` |
| M-02 | Texto plano derivado para busca, aria e fallback | ALVO_LEITURA | BFF, a partir do HTML sanitizado |
| M-03 | Parágrafo, quebra, lista, ênfase (negrito/itálico/sublinhado/riscado) | ALVO_LEITURA | kit sanitizado + MFE render-only |
| M-04 | Link (`http`, `https`, `mailto`); sem `javascript:` | ALVO_LEITURA | sanitizer canônico no BFF |
| M-05 | Título, citação, alinhamento e cor **se** vierem no HTML | ALVO_LEITURA | mesmo sanitizer; allowlist, não paleta do GLPI |
| M-06 | Tabela e bloco de código | ALVO_LEITURA | kit; tokens `--delpi-ui-*` |
| M-07 | Menção visível (chip), sem usar o nome como identidade | ALVO_LEITURA | parse da marca HTML; `user id` se existir |
| M-08 | Imagem **no** corpo, autenticada | ALVO_LEITURA + HIPOTESE URL | reescrever `src` para o GET de anexo do BFF; clique reusa `FilePreviewModal` |
| M-09 | Documento ligado **àquela** mensagem | HIPOTESE_A_VALIDAR (A-07) | não inventar vínculo; se a Timeline provar, `belowBody` dessa bolha |
| M-10 | Documento só do chamado, sem mensagem dona | IMPLEMENTADO hoje na abertura | invariante até A-07 |

Sanitização: o BFF é a autoridade. O kit (`stripDangerousRichTextTags`) é defesa no cliente. Proibido `dangerouslySetInnerHTML` com HTML cru do GLPI. Proibido o browser buscar `helpdesk.centraldelpi.com.br/front/document.send.php`.

### 6.2 Escrita (abrir e responder)

| ID | Capacidade | Estado | Dono quando houver código |
|---|---|---|---|
| M-20 | Compositor rico no lugar do textarea (parágrafo, ênfase, lista, link) | ALVO_ESCRITA | `RichTextEditor` do kit (`HERDA_KIT`) |
| M-21 | POST `content` em HTML sanitizado, não texto achatado | ALVO_ESCRITA | mesmo contrato `description` / `content`; semântica HTML |
| M-22 | Título, tabela, código, cor, alinhamento no compositor | ALVO_ESCRITA | já estão na toolbar do `RichTextEditor` |
| M-23 | Menção no compositor (`@`) | ALVO_ESCRITA | `MentionComposer` / menção do kit; id de usuário, não nome |
| M-24 | Inserir imagem ou arquivo novo no envio | BLOQUEADO | A-08; JSON-only |
| M-25 | Colar imagem da área de transferência | BLOQUEADO | vira upload |
| M-26 | Editar mensagem já gravada | CONSOLE_GLPI | a doc do GLPI tem Edit; o BFF não publica PATCH |
| M-27 | Modelo, origem, pendência no envio | CONSOLE_GLPI | follow-up doc |

Abrir chamado e responder compartilham o mesmo tipo de corpo. Não criar um editor na abertura e outro no detalhe.

### 6.3 Componente (kit)

| ID | Capacidade | Estado |
|---|---|---|
| M-30 | Modo de corpo HTML sanitizado no `MessageThread` (além de `markdown` / `plain`) | KIT_A_ESTENDER |
| M-31 | `RichTextEditor` como compositor do helpdesk | HERDA_KIT |
| M-32 | Prévia / modal / baixar anexo | HERDA_KIT — já ligados na abertura |
| M-33 | CSS de bolha no MFE helpdesk | proibido — factories do plugin-ui |

Enquanto M-30 não existir, o helpdesk **não** implementa um renderer HTML próprio.

## 7. Arquitetura-alvo (quando for implementar)

Não executar agora. Só trava o ownership correto.

```text
GLPI HTML (Ticket.content / Followup.content)
  → BFF: sanitiza + reescreve URL de documento + deriva texto puro
  → contrato: content (HTML seguro) + content_text (fallback)
  → MFE: MessageThread (modo HTML do kit)  render-only
  → compositor: RichTextEditor → POST HTML sanitizado
```

| Camada | Faz | Não faz |
|---|---|---|
| Domain/BFF | allowlist, rewrite de `src`/`href` de documento, `mine` por id/e-mail | regra de bolha, CSS |
| Contrato | HTML seguro + texto; `mine` | e-mail cru do autor, path do GLPI |
| plugin-ui | render sanitizado, editor, modal | path `/apps/helpdesk` |
| MFE | monta factory, passa `mine` e blobs | strip/sanitize paralelo, `if` de formatação |

Campos de rótulo (`title`, nomes) continuam em `display_text`. Conteúdo de mensagem **não** reutiliza essa função.

Compatibilidade: quem já consome `description` / `timeline[].content` como texto puro precisa de evolução **aditiva** (`content_html` ou equivalente) ou de decisão explícita de mudança comportamental no mesmo campo. Classificar antes do diff (`contract-evolution-backward-compatibility.mdc`).

## 8. Estado antes × depois (alvo perceptível)

| Caso | Hoje | Alvo |
|---|---|---|
| P0 — chamado 6288 com imagem no fio | texto sem marca; imagem no máximo como anexo da abertura | texto formatado; imagem no lugar em que o GLPI a gravou, via BFF |
| Irmão — listas e link num follow-up | uma linha corrida | lista e link clicável (https) |
| Negativo — HTML com script | hoje some tudo; amanhã o script continua fora | allowlist; sem execução |
| Invariante | privado, tarefa, solução, entidade, upload novo | não mudam |
| Identidade | id / e-mail | não volta a usar nome |

## 9. Hipóteses a fechar **antes** de receitar o rewrite de imagem

```text
H1  o HTML de produção aponta para /front/document.send.php?docid=N
H2  o HTML embute data-URI ou URL absoluta do host do GLPI
H3  a imagem do 6288 é só Document da Timeline, sem <img> no content
H4  o Followup da HLAPI traz lista de documentos (fecha A-07) ou não traz
```

Uma captura do `GET /tickets/{id}` (BFF) **e** do `content` cru do GLPI no 6288 e no 1114 decide H1–H4. Sem isso, M-08 e M-09 não viram etapa executável.

## 10. Prova, quando houver autorização

| Caso | Resultado |
|---|---|
| Positivo — formatação | um follow-up com negrito e lista no GLPI aparece com negrito e lista na Minha DELPI |
| Irmão — link | `https://` abre; `javascript:` não entra no HTML publicado |
| Negativo — XSS | `<script>` e `iframe` não sobrevivem ao BFF |
| Positivo — imagem (se H1/H2) | a `<img>` usa o GET autenticado do BFF; F5 não pede cookie do GLPI |
| Irmão — anexo sem HTML | prévia no `belowBody` continua |
| Negativo — A-07 | sem evidência de vínculo, a imagem de outro follow-up não muda de bolha |
| Escrita | o HTML enviado reaparece no GLPI e, no reload, na bolha |
| Identidade | dois «Roberio» com id diferente não trocam foto |
| Tema | tokens do kit; sem verde do GLPI |

Ajuda in-app (`helpTooltips.create` e `.detail`) muda no **mesmo** entregável da implementação, descrevendo formatação e imagem, sem path de API.

## 11. O que este arquivo não faz

- não abre E*.S* nem marca H5 `PROVEN`;
- não liga a API legada;
- não autoriza PATCH de follow-up, tarefa, solução ou privado;
- não autoriza renderer HTML no MFE fora do kit;
- não trata nome como identidade.

Quando o pedido passar de «documentar» para «implementar», a primeira subetapa é fechar H1–H4 no pipeline real e classificar a evolução do contrato. Só então M-01…M-23 viram plano executável.
