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
| GET | `/auth/glpi/session` | `{ "linked": true }` ou `{ "linked": false }`; quando `linked`, o campo aditivo `profile_sync` reporta o resultado da reconciliação de identidade (`synced`, `noop`, `deferred_write_authority`, `failed_write`, `failed_verification`, `skipped_*` ou `failed_*`) |
| DELETE | `/auth/glpi/session` | Apaga o vínculo local. Não revoga a sessão SAML do GLPI |

`state` é de uso único e expira em 10 minutos. O código de autorização do GLPI também expira em 10 minutos. Access token do GLPI expira em 1 hora; o BFF renova com o refresh token no servidor.

### 2.1. Paridade de identidade (HELPDESK-IDENTITY-001B / 002A)

Em todo acesso autenticado ao Helpdesk BFF (`require_actor`, portão de todas as rotas), o backend verifica a projeção de identidade do usuário no GLPI — de forma idempotente, memoizada por sessão Keycloak (`sub`+`sid`, sem hash de token) e nunca bloqueante para o acesso:

```text
Keycloak = owner canônico da identidade
        ↓
projeção da sessão: claims validados do JWT (given_name / family_name)
        ↓
GET /api.php/v2.2/session → user_id (mapeamento estável, resolução interna)
        ↓
GET /api.php/v2.2/Administration/User/{user_id}
        ↓
diff → noop
     → deferred_write_authority            (sem writer técnico — zero write)
     → write técnico names-only → reread → synced | failed_verification
```

Regras invioláveis:

- a fonte é a projeção da sessão (claims validados do JWT; owner = Keycloak), **nunca** body/query do cliente;
- o `user_id` alvo é sempre resolvido internamente da sessão OAuth — nunca de request/route/body;
- valor canônico vazio nunca conta como drift — claim ausente nunca projeta nome em branco; sem `given_name`/`family_name` o sync é `skipped_no_canonical_name` (nenhum split silencioso de `name`);
- o token OAuth da pessoa (perfil "Colaborador - Chamados", right `user`=READ) **não pode** escrever `Administration/User` — sem o writer técnico, drift retorna `deferred_write_authority` com **zero write**;
- o write técnico (IDENTITY-002A, `GLPI_PROFILE_SYNC_ENABLED=false` por padrão) usa principal dedicado (`minha-delpi-profile-sync` / apiclient próprio — distinto do H12), via apirest legado `PUT /User/{id}` com **somente** `firstname`/`realname` divergentes; campos arbitrários não passam pelo porto;
- `synced` exige releitura autoritativa (mesmo path de leitura do usuário) provando paridade — HTTP 2xx sozinho não conta;
- direção única: Minha DELPI → GLPI. Não existe sincronização reversa;
- `linked: true` nunca prova paridade — `profile_sync` é a evidência separada;
- falha de sync não invalida autenticação nem quebra o acesso ao Helpdesk;
- novos usuários nascem corretos via **JIT_CREATE_PARITY**: o client SAML do Keycloak emite `givenname`/`surname`/`emailaddress` (claims WS-* lidos pelo samlsso JIT); usuários já existentes não são atualizados pelo SSO (JIT só cria).

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

`POST /tickets/{id}/attachments` (multipart, H12) grava um Documento no GLPI via API legada (`apirest.php/Document`) sob **sessão do próprio ator** (`initSession` com o `api_token` do usuário GLPI, provisionado uma única vez por principal dedicado), liga ao Ticket e devolve `{ document_id, filename, mime, author_state, author_verified, outcome }` (últimos aditivos; `outcome` ∈ `verified` | `verification_failed` — `verification_failed` nunca é sucesso de negócio completo; `document_id` permanece para reconciliação e o retry cego duplicaria o anexo). Cabeçalho `Idempotency-Key` obrigatório. Feature flag `GLPI_LEGACY_UPLOAD_ENABLED`; sem flag/token → `503` / feature disabled. A mesma sessão do ator cobre o ciclo H10 (aceite/recusa/satisfação) — ver §4.

**Autoria do upload — por construção**: a escrita roda sob sessão mintada do `api_token` do **próprio usuário** (`_user_legacy_session`), resolvido do `user_id` da sessão OAuth (`GET /session`) **antes** de qualquer escrita — sem identidade resolúvel → `502` pré-write e nada é criado (fail-closed). O `api_token` é provisionado uma única vez por principal dedicado (`PUT /User/{id} {api_token}` — GLPI cifra server-side) e fica guardado cifrado em `helpdesk.glpi_user_tokens` (V004); a sessão mintada é verificada via `getFullSession` — `glpiID` divergente aborta antes do primeiro write. Nenhum `users_id` é enviado no payload: o GLPI carimba o usuário da sessão na criação de `Document`/`Document_Item`/`ITILFollowup` — **autoria por construção, nunca reparo retroativo**. `author_state` ∈ `verified` | `mismatch` | `unverified` é **composto** (Document + Document_Item, lido pelo canal técnico de leitura — perfil requester não lê essas linhas via apirest): `verified` só quando todas as linhas comprovam o ator. `author_verified=false` = upload persistido com autoria não confirmada — visível no contrato e nos logs (`glpi_document_author`, `glpi_document_item_author`, `glpi_document_upload_author_partial`), nunca silenciado. A sessão técnica (`GLPI_LEGACY_USER_TOKEN`) só faz **leituras bounded**; um caminho de sessão técnica não realiza escrita humana.

**Governança do `api_token` (V005)**: o provisionador é identidade dedicada obrigatória — `GLPI_TOKEN_PROVISIONER_*` sem fallback para `GLPI_LEGACY_*`; ausente → falha **antes** de qualquer sessão de provisionamento. Ciclo de vida na store `helpdesk.glpi_user_tokens` (`source` ∈ `provisioned` | `rotated` | `adopted` | `revoked`, `revoked_at`): **provisionamento** só em identidade não-gerenciada **sem** chave preexistente detectável — `GET /User/{id}` no canal do provisionador lê `api_token_date` (carimbado quando a chave é gerada na UI GLPI; chaves gravadas por REST sem `_regenerate_api_token` não carimbam — limitação residual); marcador presente → bloqueio e revisão manual, nunca overwrite silencioso de chave de terceiro. **Adoção autorizada**: operador confirma a propriedade da chave e grava marcador `adopted` na store → a escrita seguinte rotaciona uma chave governada. **Rotação**: token armazenado rejeitado pelo `initSession` → re-provisionamento único, só para identidades gerenciadas. **Revogação**: `revoke_user_api_token` envia `api_token=""` ao GLPI e marca `revoked` → provisionamento e escritas bloqueiam até o operador liberar. **Concorrência**: `provision_lock` (advisory lock Postgres por `glpi_user_id`; lock por id no store em memória) serializa provisionamento — o perdedor relê a store e reutiliza o token do vencedor em vez de cunhar um concorrente. A sessão do provisionador é aberta apenas para o GET de preflight e o PUT de `api_token` (`finally: killSession`) — restrição de escopo por código do BFF; a identidade em si é Super-Admin porque `User::currentUserHaveMoreRightThan` exige direitos ⊇ do alvo e perfis de produção variam (evidência: perfil Technician teve `PUT api_token` negado).

Imagens no HTML de follow-up/descrição: `src` só no path `/apps/helpdesk-api/tickets/{id}/attachments/{document_id}`; `width`/`height` numéricos (≤4096) passam na allowlist. CSS `width`/`height` em `style` **não** entram na allowlist de estilo — o resize do editor persiste pelos atributos HTML. Ao persistir no GLPI, o BFF traduz o `src` BFF verificado para o formato canônico do GLPI `/front/document.send.php?docid={id}` — assim a imagem renderiza inline também na UI nativa do GLPI; na leitura, o sanitizador de entrada converte de volta para o path autenticado quando o `docid` pertence ao chamado.

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

`PATCH /tickets/{id}/description` — reescreve a descrição de abertura (campo `content` do Ticket no GLPI) via `PATCH /api.php/v2.2/Assistance/Ticket/{id}` sob o token OAuth do ator — `Ticket::canUpdate` no GLPI é a autoridade, e o BFF exige `requester_mine` (a descrição é atribuída ao solicitante).

```json
{ "content": "string | HTML" }
```

`Idempotency-Key` obrigatório. Resposta `200`: `{ "id", "description_html" }`. Referências inline seguem a mesma regra do follow-up (só `docid` pertencente ao chamado; outros são removidos pelo sanitizador). É o caminho que preserva a posição original de imagens inline na abertura: o compositor cria o chamado com placeholders removidos, sobe os anexos e depois grava a descrição completa já reescrita com os `document_id` reais. Read-back autoritativo é **estrutural**: a assinatura texto+`docid` do HTML persistido precisa reproduzir as mesmas imagens, na mesma quantidade, ordem e posição relativa ao texto — texto igual com `<img>` perdida/movida → `422 validation_error` (nunca falso 200).

### Ciclo do solicitante (H10 Branch B — legado)

HLAPI não fecha o ciclo; o BFF usa `apirest` após ACL OAuth (mesmo token técnico de H12). Só o solicitante (`requester_mine`). `Idempotency-Key` obrigatório nas escritas.

| Método | Path | Efeito |
|---|---|---|
| POST | `/tickets/{id}/solution/accept` | body opcional `{ "content": "…" }` → fecha (status 6) |
| POST | `/tickets/{id}/solution/reject` | body opcional `{ "content": "…" }` → reabre (status 1) |
| GET | `/tickets/{id}/satisfaction` | `{ "satisfaction": 1..5, "comment": "…" }` ou 404 |
| PUT | `/tickets/{id}/satisfaction` | `{ "satisfaction": 1..5, "comment": "…" }` → 201; duplicata → 422 |

Não solicitante → 403. Status incoerente → 422. Legado desligado → 503.
Identidade GLPI do ator não resolúvel (`GET /session` sem `user_id`) → 502 **antes** do write: nenhum followup é criado sob a identidade técnica (fail-closed).

**Resultado governado do accept/reject** (`200`, aditivo): `{ "id", "status_id", "followup_id", "author_verified", "status_verified", "outcome" }`.
`outcome` ∈ `verified` | `author_mismatch` | `author_unverified` | `status_unverified`.
A escrita legada roda sob **sessão do próprio ator** (`POST /apirest.php/ITILFollowup` com `add_close`/`add_reopen` na sessão mintada do `api_token` do usuário — mesmo mecanismo da UI GLPI); nenhum `users_id` é enviado no payload. O read-back do `ITILFollowup` e do estado do chamado roda no canal técnico bounded (perfil requester não lê essas linhas via apirest). `author_verified=false` ou `status_verified=false` significam **executado sem confirmação integral** — o consumidor não deve tratar como sucesso pleno nem incentivar retry automático (a transição de estado no GLPI já ocorreu; repetir a intenção retorna 422). A resposta governada é a que fica gravada na idempotência: retry com a mesma chave devolve o mesmo `outcome`.

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
