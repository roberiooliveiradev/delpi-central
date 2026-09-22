# 03 — Contrato

> **Status:** contrato implementado; leitura ao vivo `PROVEN` em 21/09/2026
> **Arquitetura:** [`02-arquitetura.md`](./02-arquitetura.md)

O MFE consome só este contrato. Campos do GLPI não vazam quando o BFF consegue traduzir. Onde a tradução ainda não existe, o nome no JSON do BFF é o deste documento, não o nome cru do schema GLPI.

## 1. Convenções

- Paths do BFF em inglês, kebab-case.
- JSON em snake_case.
- Autenticação do MFE: JWT da Minha DELPI, como nas outras APIs de módulo.
- Sem JWT válido: 401.
- Com JWT e sem `helpdesk.access`: 403 do portão da plataforma, antes de chamar o GLPI.
- Com portão ok e sem sessão OAuth do GLPI: 409 `glpi_link_required`, com `authorize_url` para o navegador seguir.
- GLPI 403 no token da pessoa: 403 `glpi_forbidden`. A tela não esconde o motivo com uma lista vazia.
- Escrita sem `Idempotency-Key`: 400.
- POST de abertura e de acompanhamento: sem retry automático.

Base do MFE: `/apps/helpdesk-api`.

## 2. Sessão

| Método | Path | Função |
|---|---|---|
| GET | `/auth/glpi/start` | Responde 302 para `api.php/authorize` (PKCE S256, `state` ligado ao sujeito do JWT) |
| GET | `/auth/glpi/callback` | Troca o código em `api.php/token`, grava a sessão, redireciona para `/apps/helpdesk` |
| GET | `/auth/glpi/session` | `{ "linked": true }` ou `{ "linked": false }` |
| DELETE | `/auth/glpi/session` | Apaga o vínculo local. Não revoga a sessão SAML do GLPI |

`state` é de uso único e expira em 10 minutos. O código de autorização do GLPI também expira em 10 minutos. Access token do GLPI expira em 1 hora; o BFF renova com o refresh token no servidor.

## 3. Leitura

| Método | Path | Função |
|---|---|---|
| GET | `/ticket-categories` | Categorias que o token da pessoa pode usar |
| GET | `/urgencies` | Urgências do GLPI |
| GET | `/tickets` | Chamados visíveis para esse token |
| GET | `/tickets/{id}` | Detalhe + linha do tempo |

`GET /tickets` aceita recorte no helpdesk, não no navegador:

| Query | Papel |
|---|---|
| `q` | busca sanitizada no título **ou** no texto da abertura (`name=like` / `content=like`) |
| `status` | `open` (1,10,2,3,4), `in_progress` (2,3), `pending` (4), `approval` (10), `solved` (5), `closed` (6) |
| `urgency_id` | urgência 1–5 |
| `category_id` | categoria do token |
| `updated_from` / `updated_to` | `YYYY-MM-DD` em `date_mod` |
| `created_from` / `created_to` | `YYYY-MM-DD` em `date_creation` |
| `sort` | `updated_at:desc` (padrão), `created_at`, `solved_at`, `closed_at`, `title`, `id`, `status`, `category`, `urgency` + `:asc\|:desc` |
| `page` | página 1-based |
| `page_size` | padrão 20; a tela envia 10, 20 ou 50 (máximo 50) |

O BFF pede `limit = page_size + 1` à HLAPI e devolve `has_more`. Não inventa total do parque. Status ou sort desconhecidos, ou data inválida: 422 `validation_error`. `q` só conserva letra, número, espaço, hífen e underscore.

```json
{
  "items": [
    {
      "id": 1234,
      "title": "string",
      "status": "string",
      "status_id": 1,
      "category": "string",
      "urgency": "string",
      "updated_at": "2026-09-21T12:00:00Z",
      "created_at": "2026-09-20T08:00:00Z",
      "solved_at": "",
      "closed_at": "",
      "assigned_display_name": "string",
      "requester_display_name": "string"
    }
  ],
  "page": 1,
  "page_size": 20,
  "has_more": false
}
```

Lista vazia com sessão válida é `200`, `items: []` e `has_more: false`. Não é erro. Chamado na lixeira do GLPI (`is_deleted`) não entra na lista; o detalhe responde 404, sem o corpo.

`status` na lista e no detalhe é o **rótulo** do GLPI. `status_id` é o id ITIL (1, 2, 3, 4, 5, 6, 10), aditivo. `open` continua incluindo 10. `pending` e `approval` recortam 4 e 10. Ciclo e badges: [`14-pagina-e-estados-do-chamado.md`](./14-pagina-e-estados-do-chamado.md).

`GET /tickets/{id}` inclui `description`, `description_html` (HTML sanitizado, aditivo), `created_at` (instante de abertura), `solved_at` / `closed_at` (aditivos, vazios se o GLPI não trouxer), `sla_ttr` / `sla_tto` (rótulos do SLA, aditivos), `status` (rótulo), `status_id` (id ITIL, aditivo), `can_followup` (aditivo: **false só se `status_id==6`**; solucionado 5 ainda aceita acompanhamento), `requester_display_name` (primeiro membro de `team` com papel `requester`; se faltar, `user_recipient`), `requester_mine`, `assigned_display_name` (primeiro `assigned` do `team`), `observers_display_name` (rótulos de `team` com papel `observer`, unidos por vírgula; vazio se não houver), `timeline[]` com `id`, `kind` (`followup` | `solution`), `content`, `content_html` (aditivo), `created_at`, `author_display_name`, `mine`, e `attachments[]` com `document_id`, `filename` e `mime`. `description` e `timeline[].content` continuam **texto puro**, derivados do HTML já sanitizado. `description_html` / `content_html` passam pela allowlist do BFF ([`12-conteudo-da-mensagem.md`](./12-conteudo-da-mensagem.md) §7): sem `script`/`on*`/`javascript:`; `src`/`href` de `document.send.php` só viram o GET autenticado se o `docid` estiver em `attachments` daquele chamado — caso contrário a imagem some. `kind=solution` é leitura da Timeline `Solution`/`ITILSolution` — sem botão aprovar/recusar (H10 write continua CONSOLE). O nome de pessoa é só rótulo. `mine` / `requester_mine` vêm do id do usuário na sessão HLAPI (`GET /session` → `user_id`) ou do e-mail do JWT contra o e-mail do autor; nome nunca identifica pessoa. O nome visível usa o rótulo mais completo entre `firstname`+`realname` e `display_name`. A lista de anexos traz só arquivos já ligados àquele chamado. Lista vazia é `[]`. Acompanhamento privado, tarefa e Validation não entram em `timeline`. Os campos novos são aditivos.

A lista (`GET /tickets`) também publica `sla_ttr` / `sla_tto` e `requester_display_name` aditivos quando o GLPI os envia. `requester_display_name` segue a mesma regra do detalhe: primeiro `team` com papel `requester`; se faltar, `user_recipient`. Nome é só rótulo.

`GET /tickets/{id}/attachments/{document_id}` devolve o arquivo com o token da pessoa. O `document_id` precisa estar em `attachments` daquele chamado; caso contrário a resposta é 404, sem o corpo. O arquivo não é gravado na Minha DELPI: o BFF só repassa o download do GLPI.

Enviar um arquivo novo continua fora desta entrega. A API nova do GLPI 11.0.5 não aceita o binário do documento; o envio legado permanece desligado.

## 4. Escrita

`POST /tickets`

Cabeçalho `Idempotency-Key` obrigatório, gerado na intenção de envio e reutilizado se a mesma intenção for repetida. Chave nova só para um novo envio.

```json
{
  "title": "string",
  "description": "string | HTML",
  "category_id": 1,
  "urgency_id": 3,
  "observer_ids": [15, 22]
}
```

`description` e `content` do follow-up aceitam **texto puro ou HTML**. O BFF re-sanitiza com a mesma allowlist da leitura ([`12`](./12-conteudo-da-mensagem.md) §7) antes de gravar no GLPI: remove `script`/`on*`/`javascript:`, imagens estrangeiras e `document.send.php` sem `docid` permitido. Payload com mais de **50 000** caracteres (M-29) ou sem texto visível após a limpeza: `422 validation_error`. Título continua texto puro.

`observer_ids` (aditivo, opcional) é a lista de ids de usuário do GLPI. Depois de criar o chamado, o BFF chama `POST …/TeamMember` só com `{type: User, role: observer, id}` — **sem** `requester` nem `entity` (HD-011). Lista vazia ou ausente = nenhum observador. Máximo 10 ids.

Não existe campo de solicitante nem de entidade. O BFF não reenvia esses campos ao GLPI. O chamado nasce na entidade padrão do usuário do token.

Resposta `201`:

```json
{ "id": 1234 }
```

Repetir a mesma chave depois de sucesso devolve o mesmo `id`, sem segundo chamado.

`POST /tickets/{id}/followups`

```json
{ "content": "string | HTML" }
```

Também exige `Idempotency-Key`. Resposta `201` com `{ "id": 1 }`.

## 5. Mapa para o GLPI

Chamadas com `Authorization: Bearer` do access token da pessoa e cabeçalho `GLPI-API-Version: 2.2.0`.

| Caso de uso | GLPI 11.0.5 |
|---|---|
| Autorizar | `GET /api.php/authorize` |
| Token e refresh | `POST /api.php/token` |
| Listar e criar chamado | `GET` e `POST /api.php/v2.2/Assistance/Ticket` |
| Detalhe | `GET /api.php/v2.2/Assistance/Ticket/{id}` |
| Linha do tempo | `GET /api.php/v2.2/Assistance/Ticket/{id}/Timeline` |
| Acompanhamento | `POST /api.php/v2.2/Assistance/Ticket/{id}/Timeline/Followup` |

Categoria: `GET /api.php/v2.2/Dropdowns/ITILCategory?filter=is_helpdesk_visible==true`, usando `completename`, com página `start`/`limit`. A HLAPI não devolve o catálogo do formulário de chamado se o perfil não tiver leitura de `itilcategory`; quem só abre chamado precisa dessa leitura. Urgência é o enum 1–5 do schema de Ticket (Muito baixa, Baixa, Média, Alta, Muito alta), não um dropdown.

Fora do mapa, mesmo que o escopo `api` permita: `Change`, `Problem`, ativo, inventário, GraphQL, tarefa de técnico, validação e solução. O BFF não publica rota para isso.

## 6. Erros

| Situação | HTTP do BFF |
|---|---|
| GLPI indisponível ou timeout | 502 `glpi_unavailable` |
| GLPI 401 no token, refresh também falhou | 409 `glpi_link_required` |
| GLPI 403 | 403 `glpi_forbidden` |
| GLPI 404 no chamado | 404 |
| Validação (título vazio, categoria inexistente) | 422 com os campos |

Timeout de conexão e de leitura são explícitos no cliente HTTP. POST não é repetido. GET pode ser repetido no máximo duas vezes, com backoff, só em 502/503/504 e timeout.
