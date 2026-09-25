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
| `assignee_id` | id GLPI do técnico — **exceção Search legado** (`GLPI_LEGACY_*`, mesmo de H12/H10); ids via `search/Ticket`, hidratação/ACL via HLAPI OAuth |
| `updated_from` / `updated_to` | `YYYY-MM-DD` em `date_mod` |
| `created_from` / `created_to` | `YYYY-MM-DD` em `date_creation` |
| `sort` | `updated_at:desc` (padrão), `created_at`, `solved_at`, `closed_at`, `title`, `id`, `status`, `category`, `urgency`, `assigned` + `:asc\|:desc` — `assigned` usa a mesma exceção Search |
| `page` | página 1-based |
| `page_size` | padrão 20; a tela envia 10, 20 ou 50 (máximo 50) |

O BFF pede `limit = page_size + 1` à HLAPI (caminho normal) e devolve `has_more`. Sem `assignee_id`/`sort=assigned`, a listagem **não** usa apirest. Status ou sort desconhecidos, ou data inválida: 422 `validation_error`. `q` só conserva letra, número, espaço, hífen e underscore. Sem `GLPI_LEGACY_*` ligado, `assignee_id` / sort `assigned` → 503 `glpi_feature_disabled`.

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

`GET /tickets/{id}` inclui `description`, `description_html` (HTML sanitizado, aditivo), `created_at` (instante de abertura), `solved_at` / `closed_at` (aditivos, vazios se o GLPI não trouxer), `sla_ttr` / `sla_tto` (rótulos do SLA, aditivos), `status` (rótulo), `status_id` (id ITIL, aditivo), `can_followup` (aditivo: **false só se `status_id==6`**; solucionado 5 ainda aceita acompanhamento), `requester_display_name` (primeiro membro de `team` com papel `requester`; se faltar, `user_recipient`), `requester_mine`, `assigned_display_name` (primeiro `assigned` do `team`), `observers_display_name` (rótulos de `team` com papel `observer`, unidos por vírgula; vazio se não houver), `timeline[]` com `id`, `kind` (`followup` | `solution` | `task`), `content`, `content_html` (aditivo), `created_at`, `author_display_name`, `mine`, e `attachments[]` com `document_id`, `filename` e `mime`. `description` e `timeline[].content` continuam **texto puro**, derivados do HTML já sanitizado. `description_html` / `content_html` passam pela allowlist do BFF ([`12-conteudo-da-mensagem.md`](./12-conteudo-da-mensagem.md) §7): sem `script`/`on*`/`javascript:`; `src`/`href` de `document.send.php` só viram o GET autenticado se o `docid` estiver em `attachments` daquele chamado — caso contrário a imagem some. `kind=solution` é leitura da Timeline `Solution`/`ITILSolution`; `kind=task` é leitura pública de `Task`/`TicketTask`/`ITILTask` (entradas privadas não entram). Com H10 Branch B, o detalhe também publica `can_accept_solution` / `can_reject_solution` / `can_submit_satisfaction` (e `satisfaction` / `satisfaction_comment` quando já respondida) — **backend-first**, só se `requester_mine` e status coerente e legado ligado. O detalhe também publica capabilities de técnico (aditivas, backend-first): `can_create_solution` / `can_create_task` / `can_request_approval` — verdadeiras quando o viewer resolve para perfil técnico no GLPI (`GET /session` → `user_id` ∈ catálogo de técnicos, com fallback e-mail→catálogo) **e** o chamado não está fechado (`status_id!=6`). Distinto de `can_assign`. O nome de pessoa é só rótulo. `mine` / `requester_mine` vêm do id do usuário na sessão HLAPI (`GET /session` → `user_id`) ou do e-mail do JWT contra o e-mail do autor; nome nunca identifica pessoa. O nome visível usa o rótulo mais completo entre `firstname`+`realname` e `display_name`. A lista de anexos traz só arquivos já ligados àquele chamado. Lista vazia é `[]`. Acompanhamento privado e Validation **não** entram em `timeline` (Validation fica em `validations[]`). Os campos novos são aditivos.

A lista (`GET /tickets`) também publica `sla_ttr` / `sla_tto` e `requester_display_name` aditivos quando o GLPI os envia. `requester_display_name` segue a mesma regra do detalhe: primeiro `team` com papel `requester`; se faltar, `user_recipient`. Nome é só rótulo.

`GET /tickets/{id}/attachments/{document_id}` devolve o arquivo com o token da pessoa (Bearer). O `document_id` precisa estar em `attachments` daquele chamado; caso contrário a resposta é 404, sem o corpo. O arquivo não é gravado na Minha DELPI: o BFF só repassa o download do GLPI. Por isso o compositor **não** usa essa URL como `src` de `<img>` sem resolver blob autenticado.

`POST /tickets/{id}/attachments` (multipart, H12) grava um Documento no GLPI via API legada (`apirest.php/Document` + App-Token + User-Token técnico), liga ao Ticket e devolve `{ document_id, filename, mime }`. Cabeçalho `Idempotency-Key` obrigatório. Feature flag `GLPI_LEGACY_UPLOAD_ENABLED`; sem flag/token → `503` / feature disabled. A mesma sessão legada cobre o ciclo H10 (aceite/recusa/satisfação) — ver §4.

Imagens no HTML de follow-up/descrição: `src` só no path `/apps/helpdesk-api/tickets/{id}/attachments/{document_id}`; `width`/`height` numéricos (≤4096) passam na allowlist. CSS `width`/`height` em `style` **não** entram na allowlist de estilo — o resize do editor persiste pelos atributos HTML.

## 4. Escrita

`POST /tickets`

Cabeçalho `Idempotency-Key` obrigatório, gerado na intenção de envio e reutilizado se a mesma intenção for repetida. Chave nova só para um novo envio.

```json
{
  "title": "string",
  "description": "string | HTML",
  "category_id": 1,
  "urgency_id": 3,
  "observer_ids": [15, 22],
  "assignee_id": 15
}
```

`description` e `content` do follow-up aceitam **texto puro ou HTML**. O BFF re-sanitiza com a mesma allowlist da leitura ([`12`](./12-conteudo-da-mensagem.md) §7) antes de gravar no GLPI: remove `script`/`on*`/`javascript:`, imagens estrangeiras e `document.send.php` sem `docid` permitido. Payload com mais de **50 000** caracteres (M-29) ou sem texto visível após a limpeza: `422 validation_error`. Título continua texto puro.

`observer_ids` (aditivo, opcional) é a lista de ids de usuário do GLPI. Depois de criar o chamado, o BFF chama `POST …/TeamMember` só com `{type: User, role: observer, id}` — **sem** `requester` nem `entity` (HD-011). Lista vazia ou ausente = nenhum observador. Máximo 10 ids.

`assignee_id` (aditivo, opcional) é o id do técnico atribuído. Depois de criar, o BFF chama `POST …/TeamMember` com `{type: User, role: assigned, id}` (mesmo contrato HD-011). Ausente = sem atribuído na abertura.

Não existe campo de solicitante nem de entidade. O BFF não reenvia esses campos ao GLPI. O chamado nasce na entidade padrão do usuário do token.

Resposta `201`:

```json
{ "id": 1234 }
```

Repetir a mesma chave depois de sucesso devolve o mesmo `id`, sem segundo chamado.

`PUT /tickets/{id}/assignee` — atribuir ou reatribuir (idempotente). Exige `Idempotency-Key`.

```json
{ "user_id": 15 }
```

Resposta `200`: `{ "user_id": 15, "assigned_display_name": "Ana Silva" }`. Se já houver atribuído diferente, o BFF remove o anterior (`DELETE …/TeamMember` com o mesmo body type/role/id) e cria o novo.

`GET /users?q=&limit=20&purpose=mention|assignee` — catálogo de usuários. Busca **união** de (1) HLAPI `Administration/User` por nome/username/e-mail e (2) Directory Minha DELPI (`app=helpdesk`), amarrando pelo e-mail ou pelo nome quando o e-mail Delpi não existe no GLPI. Resposta: `{ "items": [{ "id": 15, "display_name": "Ana Silva", "email": "ana.silva@delpi.com.br" }] }`. Contas de sistema do GLPI e rótulos inválidos (`0`) são omitidos.

- `purpose=mention` (default): catálogo amplo para menções `@`.
- `purpose=assignee`: só técnicos GLPI (perfis em `GLPI_ASSIGNEE_PROFILE_IDS`, default Technician=`6`); o picker «Técnico atribuído» usa este modo. Atribuição (`assignee_id` / `PUT …/assignee`) também rejeita id fora desse conjunto.

`GET /session/capabilities` — `{ "can_assign": true|false }` derivado do direito real de listar usuários no GLPI (nunca flag só no MFE). O detalhe do chamado também inclui `can_assign`, `assigned_user_id` e `assigned_display_name`.

`POST /tickets/{id}/followups`

```json
{ "content": "string | HTML" }
```

Também exige `Idempotency-Key`. Resposta `201` com `{ "id": 1 }`.

### Ciclo do solicitante (H10 Branch B — legado)

HLAPI não fecha o ciclo; o BFF usa `apirest` após ACL OAuth (mesmo token técnico de H12). Só o solicitante (`requester_mine`). `Idempotency-Key` obrigatório nas escritas.

| Método | Path | Efeito |
|---|---|---|
| POST | `/tickets/{id}/solution/accept` | body opcional `{ "content": "…" }` → fecha (status 6) |
| POST | `/tickets/{id}/solution/reject` | body opcional `{ "content": "…" }` → reabre (status 1) |
| GET | `/tickets/{id}/satisfaction` | `{ "satisfaction": 1..5, "comment": "…" }` ou 404 |
| PUT | `/tickets/{id}/satisfaction` | `{ "satisfaction": 1..5, "comment": "…" }` → 201; duplicata → 422 |

Não solicitante → 403. Status incoerente → 422. Legado desligado → 503.

### Operações de técnico (Solution / Task / pedido de aprovação)

HLAPI Timeline. Exigem `Idempotency-Key`. AuthZ: mesmo gate de `can_create_*` (sessão técnico + chamado não fechado). Conteúdo HTML re-sanitizado. Solution e Task são gravadas **públicas** (`is_private=0`) para aparecerem na conversa.

| Método | Path | Body | Resposta |
|---|---|---|---|
| POST | `/tickets/{id}/solutions` | `{ "content": "…" }` | `201` `{ "id", "status_id" }` |
| POST | `/tickets/{id}/tasks` | `{ "content": "…" }` | `201` `{ "id" }` |
| POST | `/tickets/{id}/validations` | `{ "approver_user_id": N, "content"?: "…" }` | `201` `{ "id", "status", "requested_approver_id" }` |

Não técnico → 403. Chamado fechado → 422. Aprovador inacessível → 422.

### Aprovação (TicketValidation — HLAPI)

| Método | Path | Efeito |
|---|---|---|
| POST | `/tickets/{id}/validations/{validation_id}/accept` | body opcional `{ "content": "…" }` → status 3 |
| POST | `/tickets/{id}/validations/{validation_id}/reject` | body opcional `{ "content": "…" }` → status 4 |

Só o aprovador designado (`mine_to_decide`). Detalhe publica `validations[]` e `can_decide_validation`.

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
| Solução | `POST /api.php/v2.2/Assistance/Ticket/{id}/Timeline/Solution` |
| Tarefa | `POST /api.php/v2.2/Assistance/Ticket/{id}/Timeline/Task` |
| Pedido / decisão de aprovação | `POST` / `PATCH` `/api.php/v2.2/Assistance/Ticket/{id}/Timeline/Validation` |

Categoria: `GET /api.php/v2.2/Dropdowns/ITILCategory?filter=is_helpdesk_visible==true`, usando `completename`, com página `start`/`limit`. A HLAPI não devolve o catálogo do formulário de chamado se o perfil não tiver leitura de `itilcategory`; quem só abre chamado precisa dessa leitura. Urgência é o enum 1–5 do schema de Ticket (Muito baixa, Baixa, Média, Alta, Muito alta), não um dropdown.

Fora do mapa, mesmo que o escopo `api` permita: `Change`, `Problem`, ativo, inventário, GraphQL. O BFF não publica rota para isso.

## 6. Erros

| Situação | HTTP do BFF |
|---|---|
| GLPI indisponível ou timeout | 502 `glpi_unavailable` |
| GLPI 401 no token, refresh também falhou | 409 `glpi_link_required` |
| GLPI 403 | 403 `glpi_forbidden` |
| GLPI 404 no chamado | 404 |
| Validação (título vazio, categoria inexistente) | 422 com os campos |

Timeout de conexão e de leitura são explícitos no cliente HTTP. POST não é repetido. GET pode ser repetido no máximo duas vezes, com backoff, só em 502/503/504 e timeout.
