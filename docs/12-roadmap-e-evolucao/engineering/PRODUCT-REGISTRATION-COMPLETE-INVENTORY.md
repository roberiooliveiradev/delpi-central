# Product Registration — Inventário completo para o BFF

**Task:** `ENG-PRODUCT-REGISTRATION-COMPLETE-INVENTORY`  
**Status:** `INVENTORY_COMPLETE`  
**Data da evidência:** 2026-11-06  
**Implementação produtiva:** não executada  
**Deploy:** não executado

Este documento é a evidência de código para iniciar o contrato do BFF de **Controle e Cadastro de Produtos**. O plano de intenção continua no adendo de [ROADMAP.md](./ROADMAP.md). Onde o adendo dizia `AUTHZ_DELEGATION=TO_INVENTORY` ou `LEGACY_RUNTIME=PENDING_VERIFICATION`, o estado factual passa a ser o desta página.

SHAs examinados (working tree de código não foi alterado por esta task):

| Repositório | Path local | Branch | SHA |
|---|---|---|---|
| `roberiooliveiradev/controle_mp` | `/home/analistaptd/projetos/controle_mp` | `main` | `c96060f90be5c131fc17f21312dd3a33781b0cd2` |
| `roberiooliveiradev/delpi-central` | `/home/analistaptd/projetos/delpi-central` | `main` | `2cbd3e308d70f33a894b1e48d2b0d18214603b7b` |

Links de código usam esses SHAs. O `delpi-central` tinha alterações não commitadas de outra frente (percepção de desenho / OCR). Nenhum desses arquivos foi editado, formatado ou incluído no commit desta task.

---

## 1. Executive Summary

A fila operacional do Controle MP é uma fila de **itens**, não de solicitações com status único. O status vive em `request_items.request_status_id`. A autoridade que muda status, devolve, rejeita e finaliza é `RequestService` na API Flask. A finalização grava um produto local no Postgres do Controle MP depois de ler o Protheus; não grava no ERP.

O Portal Engenharia já tem o lugar certo para o BFF: `plugins/engineering` chama `engineering-api` em `/apps/engineering-api/v1/...`, e a `engineering-api` já delega o JWT do usuário para APIs irmãs por `DownstreamClient`. Esse padrão **não funciona** contra o Controle MP. `require_auth` só decodifica JWT local HS256 (`typ=access`, issuer/audience do próprio Controle MP). O Bearer do Portal é o JWT Keycloak RS256. Não há token exchange, on-behalf-of, nem aceitação do token de serviço na entrada da API.

Consequência: nenhuma leitura nem escrita do BFF em nome do analista está `READY_FOR_IMPLEMENTATION` até uma mudança aditiva na API do Controle MP. A menor mudança é estender `require_auth` para aceitar o JWT central já usado em `POST /api/auth/sso-login`, resolver `tbUsers` por `central_subject` e **recusar** quando o usuário local não existir. `sso-login` não serve como delegação: ele cria usuário, força papel default 3, emite refresh de 7 dias e audita `LOGIN`.

A primeira superfície do analista cabe no MFE existente, como irmã de `products` e `nonconformities`. A rota `/apps/engineering/product-registration` hoje cai em `not_found`. O prefixo público `/apps/engineering-api/v1/product-registration` segue o padrão real do gateway; o segmento ainda não existe.

`requests-api` tem motor de workflow e um stub `raw-material-creation` com três campos (`description`, `unit`, `notes`) e `adapter=none`. Não há `raw-material-update`. Esse stub não é a fonte da fase 1.

---

## 2. Repositórios e versões examinados

### 2.1 controle_mp

- HEAD `c96060f90be5c131fc17f21312dd3a33781b0cd2` em `main`, alinhado a `origin/main` no momento da leitura (`git status -sb` = `## main...origin/main`, working tree limpo).
- Remote: `git@github.com:roberiooliveiradev/controle_mp.git`.
- Worktree única: `/home/analistaptd/projetos/controle_mp`.
- Árvore usada: `api-cadastro-mp/app/`, `front-cadastro-mp/src/`, `docs/API_REFERENCE.md`, `docs/ARQUITETURA.md`, `README.md`.
- Últimos commits no topo: `c96060f` docs de evolução; `40a51b3` sync de IDs da Minha DELPI; `ca3c3bb` vínculo SSO ao `sub`; `d87490a` persistência de campos; `88db39d` correção de campos em item ALTERAR devolvido.

### 2.2 delpi-central

- HEAD `2cbd3e308d70f33a894b1e48d2b0d18214603b7b` em `main`, alinhado a `origin/main` no momento da leitura.
- Remote: `git@github.com:roberiooliveiradev/delpi-central.git`.
- Working tree **sujo por outra frente**, não por esta task:
  - `D` `docs/12-roadmap-e-evolucao/delia/corrections/.../286-gpu-wsl2-overlay-acceptance-structured-output-residual.md`
  - `M` `engineering-api/engineering_app/application/drawing/perception_contract.py`
  - `M` `engineering-api/engineering_app/application/drawing/understanding.py`
  - `M` `engineering-api/engineering_app/infrastructure/extraction/paddleocr_adapter.py`
  - `M` `engineering-api/engineering_app/interface/mcp/semantic_bridge.py`
  - `M` `engineering-api/tests/test_drawing_understanding_r8.py`
  - `M` `engineering-api/tests/test_table_perception_native.py`
  - `M` `infra/scripts/keycloak-dev-bootstrap.sh`
  - `M` `infra/scripts/up-dev-sequential.sh`
  - untracked: `delia-api/.battery/kimi-dev-eval/`, `plugins/tv-dashboard-presentation/artifacts/`, `plugins/tv-dashboard-presentation/e2e/specs/kpi-status-capture.spec.ts`
- Há dezenas de worktrees preexistentes (`git worktree list`). Nenhuma foi alterada. A worktree `eng-products-e2e` (`feat/engineering-products-e2e`) é de outro assunto (catálogo de produtos de engenharia), não deste vertical.
- Docs de intenção lidos: `engineering/ROADMAP.md` (adendo 2026-11-06), `engineering/ARCHITECTURE.md`, `engineering/API-ROUTES.md`, `engineering/INTEGRACOES.md`, `controle-mp/EVOLUCAO.md`, `my-requests/PLAYBOOK.md`, `AGENTS.md`.

`API-ROUTES.md` §10 e `INTEGRACOES.md` §7 ainda descrevem a decisão anterior (resumo + deep link para `my-requests`). O adendo do ROADMAP prevalece sobre a **superfície do analista**. Este inventário não reescreve essa decisão; confirma o que o código permite.

---

## 3. Authorities e decisões existentes

| ID | Decisão vigente | Onde | Efeito neste inventário |
|---|---|---|---|
| Adendo PRC 2026-11-06 | Analista no `plugins/engineering`; solicitante permanece no Controle MP; BFF = `engineering-api` → API Controle MP | `ROADMAP.md` adendo; `EVOLUCAO.md` §10 | Fonte da fase 1 é a API Flask |
| D-07 / E9 (histórico) | Deep link para `my-requests`, sem duplicar fila | `ROADMAP.md` antes do adendo; `API-ROUTES.md` §10 | Superfície inicial **não** segue mais isso. O path `GET /v1/integrations/raw-material-control/summary` **não existe** na `engineering-api` |
| Ownership de fase 1 | Controle MP é dono da solicitação, da transição e do produto materializado. `engineering-api` é façade | Adendo §2 | BFF não grava produto nem reimplementa a máquina de estados como autoridade |
| Proibições | Sem Postgres do Controle MP, sem import Flask, sem MFE→Flask/TOTVS, sem token admin no lugar do usuário, sem dual-write | Adendo §2 | Confirmadas como ausência no código da `engineering-api` (`tests/test_architecture.py` proíbe import Flask) |
| Delegação | Sem contrato de auth, leituras e escritas remotas ficam bloqueadas | Adendo §4 | **Confirmado no código.** Ver seção 6 |
| Stub MP | `raw-material-creation` não substitui o fluxo real | Adendo §3; seed `V007` | Confirmado. Ver seção 13 |
| Identificadores | Inglês no código; pt-BR na apresentação | Adendo §1; `.cursor/rules/english-code-identifiers.mdc` | Prefixo `product-registration` é compatível |
| Fronteira de apps | MFE com API própria não chama `api-delpi` direto; dado alheio só por HTTP | `.cursor/rules/mfe-own-api-no-direct-api-delpi.mdc`, `application-bounded-context-decoupling.mdc` | O plugin só fala com `engineering-api` |
| Resiliência | Timeout explícito; retry só em leitura idempotente | `.cursor/rules/http-integration-resilience.mdc` | `DownstreamClient` já não faz retry |
| Git | Commit direto em `main`; worktree/branch só com autorização explícita | `AGENTS.md` regras 1–10 | Esta task pediu worktree se o arquivo de destino estivesse em conflito. O destino estava limpo. O commit documental fica em `main`, sem stage dos arquivos da EVA. Deploy canônico do `AGENTS.md` **não** foi executado: a task proíbe deploy |

Decisões que o código **não** fecha e continuam `ARCHITECTURE_DECISION_REQUIRED`:

1. Aceitar o JWT central nas rotas de negócio do Controle MP (recomendação técnica na seção 6.4) e alinhar audience/issuer de runtime.
2. Aceitar, na fase 1, que ADMIN/ANALYST enxergam **toda** a fila, porque a API não filtra por `assigned_to` nem por “analista dono”.
3. Aceitar last-write-wins na mudança de status ou exigir versão otimista aditiva antes de PRC-3.
4. Semântica de `FRACASSADO` (id 4): existe no seed e na cópia de notificação; `change_item_status` recusa esse alvo.
5. Owner funcional do cadastro (o adendo cita TÉO `PROC-0078`; o processo não foi reaberto neste workspace).
6. Cutover futuro para `requests-api`.

---

## 4. Mapa de sistemas e owners

```text
Solicitante (fase 1)
  front-cadastro-mp  -->  api-cadastro-mp (Flask)  -->  Postgres do Controle MP
                     -->  SQL Server Protheus (somente leitura SB1010 / SA2010 / SA5010)
                     -->  Socket.IO + POST Core /integrations/notifications

Analista (fase 1, ainda não implementado)
  plugins/engineering
    --> engineering-api  /apps/engineering-api/v1/product-registration
        --> api-cadastro-mp          (fonte da solicitação e da finalização)
        --> Core GET /me             (permissão engineering.access, já existente)
        --> api-delpi /products/...  (catálogo ERP já usado pela ferramenta Produtos;
                                      NÃO é a autoridade que aprova a finalização)

Futuro, decisão separada
  requests-api / my-requests
```

| Sistema | Dono do dado na fase 1 | O que o BFF pode fazer |
|---|---|---|
| Solicitação, item, campos, conversa, anexo | API Controle MP | Consumir HTTP depois da delegação |
| Transição de status e materialização do produto local | `RequestService` + `ProductService` | Chamar o endpoint existente; não reproduzir a regra |
| Catálogo Protheus usado **na finalização** | `TotvsProductRepository` dentro do Controle MP | A finalização continua lá. Consulta de apoio pode usar o mesmo endpoint `/api/products/totvs/...` |
| Catálogo Protheus da ferramenta Produtos do Portal | `api-delpi` via `ApiDelpiDelegatedAuxiliary` | Já existe para outro caso de uso. Não substitui a checagem da finalização |
| Permissão de entrar no Portal Engenharia | Core, `engineering.access` | Já é o gate do MFE e da `engineering-api` |
| Papel ADMIN/ANALYST/USER do fluxo MP | `tbUsers.role_id` no Controle MP | Não está nas roles do Keycloak. SSO novo usuário nasce role 3 |
| Workflow futuro | `requests-api` | Fora da fase 1 |

---

## 5. Inventário REST completo do Controle MP

### 5.1 Bootstrap

`create_app` chama `register_routes` (`api-cadastro-mp/app/main.py`). O prefixo efetivo é o de `register_blueprint`, não o do construtor do Blueprint.

```17:36:api-cadastro-mp/app/api/routes/__init__.py
def register_routes(app: Flask, *, api_prefix: str, app_prefix: str) -> None:
    app.register_blueprint(bp_health, url_prefix=f"{app_prefix}/health")
    app.register_blueprint(bp_users, url_prefix=f"{api_prefix}/users")
    app.register_blueprint(bp_auth, url_prefix=f"{api_prefix}/auth")
    app.register_blueprint(bp_conv, url_prefix=f"{api_prefix}/conversations")
    app.register_blueprint(
        bp_msg, url_prefix=f"{api_prefix}/conversations/<int:conversation_id>/messages"
    )
    app.register_blueprint(bp_files, url_prefix=f"{api_prefix}/files")
    app.register_blueprint(bp_req, url_prefix=f"{api_prefix}/requests")
    app.register_blueprint(bp_prod, url_prefix=f"{api_prefix}/products")
    app.register_blueprint(bp_audit, url_prefix=f"{api_prefix}/audit")
    app.register_blueprint(bp_test, url_prefix=f"{app_prefix}/test")
```

`API_PREFIX = f"{APP_PREFIX}/api"`. `APP_PREFIX` vem de env e é vazio por omissão. Paths abaixo assumem `APP_PREFIX=""`. Não há `add_url_rule` extra. Nenhuma rota foi classificada `DEPRECATED` ou `DEFINED_NOT_REGISTERED`.

**Total: 51 rotas HTTP, todas `REGISTERED`.** Duas delas (`/test/*`) estão registradas em qualquer ambiente, inclusive sem `DEBUG`.

Erros de domínio: `{"error": "<mensagem>"}` via `AppError` (`error_handler.py`). Códigos: 400, 401, 403, 404, 409, 500. `ValidationError` do Pydantic nas rotas de auth, requests, messages, conversations e products **não** vira 400: cai no handler genérico (500). Users captura validação e devolve 400.

`require_auth`: OPTIONS 204; Bearer; `JwtProvider.decode`; `typ=access`; `jti` obrigatório; `tbRevokedTokens`; claims em `g.auth`. `require_roles` compara `g.auth["role_id"]`.

Acesso à conversa (request, message, file, conversation): role 1 ou 2 passa; role 3 só se `conversation.created_by == user_id`. Função: `RequestService._ensure_access_by_conversation`.

Testes HTTP de rota: ausentes. `api-cadastro-mp/tests/` tem testes unitários de SSO, binding, permissão de campo e cliente de notificação.

### 5.2 Matriz REST

AuthN `local` = `require_auth` (JWT HS256 de access). AuthZ “conv” = acesso à conversa descrito acima. Efeito “audit” grava `tb` de auditoria na mesma sessão.

| Método | Endpoint | Handler | AuthN | AuthZ | Request | Response | Service | Efeito | Evidência |
|---|---|---|---|---|---|---|---|---|---|
| GET | `/health` | `health` | não | — | — | `{status:ok}` 200 | — | — | `health_routes.py` |
| GET | `/health/db` | `health_db` | não | — | — | `{db:ok}` 200 | sessão | `SELECT 1` | `health_routes.py` |
| POST | `/api/auth/login` | `login` | não | — | `email`, `password` | par de tokens 200; 401 | `UserService.authenticate` | `last_login`, refresh hash, audit LOGIN | `auth_routes.py` |
| POST | `/api/auth/sso-login` | `sso_login` | Bearer **Keycloak** | — | body vazio | par de tokens 200; 401; 409 e-mail ligado a outro `sub` | `CentralJwtValidator`, `get_or_create_from_sso` | cria usuário se não houver; audit LOGIN `sso=minhadelpi` | `auth_routes.py` |
| POST | `/api/auth/refresh` | `refresh` | refresh no body | — | `refresh_token` | par novo 200; 401 | `RefreshTokenService.rotate` | revoga refresh antigo | `auth_routes.py` |
| POST | `/api/auth/logout` | `logout` | local | — | `refresh_token` opcional | 204 | `AuthService.revoke_access_token` | revoga `jti`; refresh só se veio no body | `auth_routes.py` |
| POST | `/api/users` | `create_user` | **não** | força role 3 | nome, e-mail, senha | `UserResponse` 201; 409 | `UserService.create_user` | senha PBKDF2; audit CREATED | `user_routes.py` |
| GET | `/api/users` | `list_users` | **não** | — | `limit`, `offset` | lista com e-mail e `role_id` 200 | `list_users` | leitura de usuários ativos | `user_routes.py` L104 |
| PUT | `/api/users/<id>` | `update_user` | local | senha atual; **não** exige `sub==id` | `current_password` + campos; aceita `role_id` | 200; 401; 409 | `update_user` | pode trocar papel de outro id | `user_routes.py` L130 |
| DELETE | `/api/users/<id>` | `delete_user` | local | **sem** dono nem role | — | 204 | `delete_user` | soft delete de qualquer id | `user_routes.py` |
| GET | `/api/users/admin` | `admin_list_users` | local | role 1 | `limit`, `offset`, `include_deleted` | lista admin incl. `central_subject` | `admin_list_users` | leitura | `user_routes.py` |
| PUT | `/api/users/<id>/admin` | `admin_update_user` | local | role 1 | `role_id?`, `is_deleted?` | user admin 200 | `admin_update_user` | audit | `user_routes.py` |
| POST | `/api/users/admin/central-subjects/sync` | `admin_sync_central_subjects` | local | role 1 | — | contagens e conflitos 200; 503 se Core falhar | `DelpiDirectoryClient` | grava `central_subject` | `user_routes.py` L272 |
| GET | `/api/conversations` | `list_conversations` | local | USER só as que criou | `limit`, `offset`, `title` | lista | `ConversationService` | leitura | `conversation_routes.py` |
| GET | `/api/conversations/<id>` | `get_conversation` | local | conv | — | uma conversa; 403; 404 | idem | leitura | idem |
| GET | `/api/conversations/unread-summary` | `get_unread_summary` | local | USER filtrado | — | mapa id→não lidas | idem | leitura | idem |
| POST | `/api/conversations` | `create_conversation` | local | autenticado | `title`, `has_flag`, `assigned_to_id?` | 201 | idem | socket `conversation:new`; DELPI; audit | idem |
| PATCH | `/api/conversations/<id>` | `update_conversation` | local | conv; título só criador | campos opcionais | 200 | idem | audit; sem socket | idem |
| DELETE | `/api/conversations/<id>` | `delete_conversation` | local | **role 1** | — | 204 | idem | soft delete; audit | idem |
| GET | `/api/conversations/<id>/messages` | `list_messages` | local | conv | — | lista `MessageResponse` | `MessageService` | leitura | `message_routes.py` |
| GET | `.../messages/<message_id>` | `get_message` | local | conv | — | uma mensagem | idem | leitura | idem |
| POST | `.../messages/read` | `mark_read` | local | conv | `message_ids` | `{updated}` | idem | socket `message:read` | idem |
| POST | `.../messages` | `create_message` | local | conv | body, tipo, files, `create_request`, `request_items` | 201; 409 | `MessageService` → `RequestService.create_request` | mensagem + request; socket; DELPI; audit | `message_routes.py` L261 |
| DELETE | `.../messages/<message_id>` | `delete_message` | local | conv; USER só a própria | — | 204 | idem | soft delete; sem socket | idem |
| POST | `/api/files/upload` | `upload_files` | local | autenticado, sem conversa | multipart | metadados 201; 409 MIME/tamanho | `LocalFileStorage` | disco; **não** grava `tbMessageFiles`; audit | `file_routes.py` |
| GET | `/api/files/<id>/download` | `download_file` | local | arquivo de mensagem em conversa acessível | — | `send_file` | `FileService` | leitura | `file_routes.py` |
| POST | `/api/requests` | `create_request` | local | conv da mensagem | `message_id`, `items[]` | `RequestResponse` 201; 409 se a mensagem já tem request | `RequestService.create_request` | inserts; socket; DELPI; audit. Não valida enum de status | `request_routes.py` |
| GET | `/api/requests/<id>` | `get_request` | local | conv | — | request + items + fields. **Sem** `conversation_id` e sem nome do solicitante | `get_request` | leitura | `request_routes.py` |
| DELETE | `/api/requests/<id>` | `delete_request` | local | conv | — | 204 | `delete_request` | soft delete **mesmo** FINALIZADO/REJEITADO; sem socket | idem |
| POST | `/api/requests/<id>/items` | `add_item` | local | conv | item | `{id}` 201 | `add_item` | sem socket | idem |
| PATCH | `/api/requests/items/<id>` | `update_item` | local | criador + status DEVOLVIDO + não locked | tipo, status, `product_id` | 204 | `update_item` | pode gravar status fora da whitelist; sem socket | idem |
| DELETE | `/api/requests/items/<id>` | `delete_item` | local | conv, **sem** lock | — | 204 | `delete_item` | soft delete de item finalizado | idem |
| PATCH | `/api/requests/items/<id>/resubmit` | `resubmit_item` | local | **só criador**; status 5 | body ignorado | 204; 409 | `resubmit_returned_item` | status → 1; socket STATUS; DELPI; audit | `request_service.py` L552 |
| POST | `/api/requests/items/<id>/fields` | `add_field` | local | regra de campo §8 | tag, valor, tipo | `{id}` 201 | `add_field` | sem socket | `request_routes.py` |
| PATCH | `/api/requests/fields/<id>` | `update_field` | local | regra de campo; staff só manda `field_value` | parcial | 204 | `update_field` | socket FIELDS; DELPI; audit | `request_service.py` L342 |
| PATCH | `/api/requests/fields/<id>/flag` | `set_field_flag` | local | role 1 ou 2; item não 3/6 | `{field_flag}` | 204 | `set_field_flag` | socket FIELD_FLAG | `request_routes.py` |
| DELETE | `/api/requests/fields/<id>` | `delete_field` | local | regra de campo | — | 204 | `delete_field` | sem socket | idem |
| GET | `/api/requests/count` | `count_requests` | local | USER só os próprios | `status_id`, `type_id` | `{total}` | `count_items` | **não filtra `is_deleted`** | `request_item_repository.py` L91 |
| GET | `/api/requests/items` | `list_request_items` | local | USER forçado a `created_by=self` | ver §5.3 | página + `total` | `list_request_items` | `fields_count` sempre 0 | `request_item_repository.py` L239 |
| PATCH | `/api/requests/items/<id>/status` | `change_item_status` | local | role 1 ou 2; não locked; conv | `{request_status_id}` | 204; 400; 409 | `change_item_status` | ver §8. Audit de item e, se finalizou, de produto | `request_routes.py` L542 |
| GET | `/api/requests/meta` | `get_requests_meta` | local | qualquer autenticado | — | types + statuses ativos | repositórios de tipo/status | leitura | `request_routes.py` L594 |
| GET | `/api/products` | `list_products` | local | qualquer autenticado | `q`, `flag`, datas, página | lista local | `ProductQueryService` | Postgres; sem ERP | `product_routes.py` |
| GET | `/api/products/<id>` | `get_product` | local | autenticado | — | produto + fields | idem | Postgres | idem |
| PATCH | `/api/products/fields/<id>/flag` | `set_product_field_flag` | local | role 1 ou 2 | `{field_flag}` | 204 | `ProductService` | socket `product:flag_changed` | idem |
| GET | `/api/products/<id>/totvs` | `get_product_totvs` | local | autenticado | — | ficha ERP pelo `codigo_atual` local | `ProductQueryService` | leitura ERP; 409 se TOTVS off | idem |
| GET | `/api/products/totvs/suppliers` | `search_suppliers_totvs` | local | autenticado | `code`, `store`, `name`, `limit`≤50, `offset` | página | `TotvsProductRepository.search_suppliers` | `SA2010` | idem |
| GET | `/api/products/totvs/<code>` | `get_product_by_code_totvs` | local | autenticado | path | `{totvs}` ou 404 | `list_products(code=)` | `SB1010` | idem |
| GET | `/api/audit/logs` | `admin_list_audit_logs` | local | role 1 | filtros | página | `AuditReportService` | leitura | `audit_routes.py` |
| GET | `/api/audit/summary` | `admin_audit_summary` | local | role 1 | filtros | agregados | idem | leitura | idem |
| GET | `/test/protected` | `protected_route` | local | — | — | ecoa claims | — | vaza JWT decodificado | `test_routes.py` |
| GET | `/test/admin-only` | `admin_only_route` | local | role 1 | — | ecoa claims | — | idem | `test_routes.py` |

### 5.3 Query da fila (`GET /api/requests/items`)

Parâmetros reais: `limit`, `offset`, `status_id`, `created_by_name`, `type_id`, `type_q`, `item_id`, `date_mode` (`AUTO` \| `CREATED` \| `UPDATED`), `date_from`, `date_to` (`YYYY-MM-DD`).

Role 3: o serviço zera `created_by_name` e fixa o criador no próprio usuário. Role 1 e 2: veem itens de todas as conversas acessíveis (na prática, todas). Não há filtro por responsável, por `assigned_to` da conversa, nem por descrição técnica.

A listagem filtra `is_deleted` de item, request e tipo (`request_item_repository.py` por volta da L166). O `GET /count` não filtra. O BFF de indicadores deve usar o `total` da listagem, não `/count`.

`fields_count` é constante `0` (`request_item_repository.py` L239). O objeto `request_created_by_user` inclui `email` no repositório; o schema Pydantic de request declara só `id` e `full_name`.

Se `limit`/`offset` forem omitidos, o schema de resposta declara `int` não opcional. O BFF deve sempre enviar os dois.

### 5.4 Diferenças contra `docs/API_REFERENCE.md`

No código e ausente no doc:

- `POST /api/users/admin/central-subjects/sync`
- socket `message:read`
- socket `conversation:joined` / `conversation:left`

No doc e ausente no código: nenhuma rota da tabela do doc. As rotas documentadas existem. A 51ª é o sync.

Contrato divergente:

- Doc trata `GET /api/users` como autenticado. O handler não tem `require_auth`.
- Doc trata `PUT /api/users/<id>` como “o próprio”. O handler não compara `sub` com `user_id` e o schema aceita `role_id`.
- `DELETE /api/users/<id>` apaga qualquer usuário autenticado, qualquer id.
- `/test/*` está no doc e no código, sempre registrado.

O BFF **não** deve proxificar users, audit, test, delete de request/item, `POST /api/users` nem `GET /api/users`.

---

## 6. Contratos de autenticação e autorização

### 6.1 Login local

`JwtProvider` (`infrastructure/security/jwt_provider.py`):

- HS256 com `JWT_SECRET` (default de código `dev-secret-change-me`, `settings.py`).
- `iss` default `cadastro-mp-api`. `aud` default `cadastro-mp-front`.
- Claims: `iss`, `aud`, `sub` (id local), `iat`, `exp`, `jti`, `typ` (`access` ou `refresh`). Access ainda leva `email`, `role_id`, `full_name`.
- Access nas rotas de login/refresh: 60 minutos explícitos (não o default `JWT_ACCESS_MINUTES`, que só vale se `minutes<=0`).
- Refresh de login/SSO: 7 dias. Rotação usa `JWT_REFRESH_MINUTES` (default 7 dias).
- Refresh persistido como SHA-256 + `jti` em `tbRefreshTokens`. Reuso do refresh antigo → 401.
- Logout insere `jti` em `tbRevokedTokens`. Sem refresh no body, o refresh continua válido.
- Senha local: PBKDF2-HMAC-SHA256, 600000 iterações.

### 6.2 SSO Minha DELPI

Único endpoint: `POST /api/auth/sso-login`.

`CentralJwtValidator` (`central_jwt_validator.py`):

- JWKS `CENTRAL_JWKS_URL` (obrigatório na chamada; timeout do client 10s).
- Issuer `CENTRAL_JWT_ISSUER` obrigatório.
- Audience default `delpi-central` (`CENTRAL_JWT_AUDIENCE`). Verificação ligada por default.
- RS256. Exige `exp`, `sub`, `iss` e e-mail.
- `central_subject` = `sub` do Keycloak, coluna `tbUsers.central_subject`.
- Roles do Keycloak são ignoradas. Usuário novo recebe `CENTRAL_DEFAULT_ROLE_ID` (default **3**). Usuário existente **mantém** o `role_id`.
- Resolução (`UserService.get_or_create_from_sso`): por `central_subject`; senão por e-mail (409 se o e-mail já tem outro `sub`); senão **cria** a conta. Não existe rejeição de “usuário sem vínculo” nesse endpoint.
- Sync admin `POST /api/users/admin/central-subjects/sync` só preenche `central_subject` a partir do diretório Core (`GET /integrations/directory/users/by-app?app=controle-mp`). Não emite sessão.

Testes: `tests/test_sso_central_subject.py`, `test_central_subject_binding.py`, `test_central_subject_sync.py`.

O frontend embute isso por `postMessage` (`DelpiSsoBridge.jsx`): o iframe manda o Bearer central para `sso-login`. Isso autentica o browser do Controle MP. Não entrega um token de serviço para a `engineering-api`.

### 6.3 Delegação backend-to-backend

`require_auth` (`auth_middleware.py` L15–48) lê `Authorization: Bearer` e chama `JwtProvider.decode`. Esse decode só aceita HS256 com o segredo, issuer e audience **locais**, e exige `typ=access`.

Busca no pacote por impersonação, on-behalf-of, `X-User`, token exchange e header de serviço na entrada: sem implementação de entrada. O header `X-Delpi-Service-Token` é **saída** do Controle MP para a Core (`delpi_notification_client.py`, `delpi_directory_client.py`). As rotas do Controle MP não o aceitam como ator.

A `engineering-api` já possui o padrão certo para APIs que entendem o JWT do Portal (`DownstreamClient`):

- `Authorization: Bearer <JWT do usuário>`
- `X-Delpi-Caller-App: engineering-api`
- `X-Request-Id`
- S2S opcional em `X-Delpi-Service-Authorization`, separado do Bearer humano
- sem retry; timeout no construtor

Esse Bearer é o que `delpi_auth` valida na `engineering-api` (JWKS, `KEYCLOAK_ISSUER`, `KEYCLOAK_AUDIENCE`). `KEYCLOAK_AUDIENCE` não tem default no código (`config.py`); é env obrigatório de boot. O audience default do Controle MP é a string `delpi-central`. **Igualdade entre os dois valores de runtime não está no repositório.** É bloqueio externo (seção 22).

Encaminhar o JWT do Portal para `sso-login` mintaria um access local, com estes efeitos colaterais reais: `last_login`, insert de refresh, audit de LOGIN e **criação de usuário role 3** se o `central_subject` ainda não existir. Um analista ainda não vinculado nasceria USER e não conseguiria mudar status. Isso não é delegação.

Socket.IO (`socket_handlers.py`) valida HS256/iss/aud no `connect`, aceita `?token=`, não exige `typ=access` e não consulta revogação. `conversation:join` não revalida o acesso à conversa. O BFF não deve abrir esse socket em nome do usuário.

### 6.4 Menor evolução na API proprietária

Estender `require_auth` (ou um decorator irmão usado pelas rotas de negócio), sem novo fluxo de refresh:

1. Tentar o JWT local HS256 como hoje.
2. Se falhar por algoritmo/issuer, validar com `CentralJwtValidator` (RS256, JWKS, issuer, audience).
3. Carregar `tbUsers` por `central_subject`.
4. Se não houver linha, responder 403. Não chamar `get_or_create_from_sso`.
5. Preencher `g.auth` com `sub` = id local, `role_id`, `email`, `full_name` já gravados. O papel continua sendo o do Controle MP (admin promove ANALYST em `/admin/users`).
6. Auditar o ator local nas operações que já auditam. Não emitir refresh.

Pré-condição de runtime: o access token que a `engineering-api` recebe precisa ser aceito por `CENTRAL_JWT_ISSUER` e `CENTRAL_JWT_AUDIENCE`. Se o audience do Portal for outro, a alternativa mínima passa a ser um endpoint de exchange que recebe o Bearer já validado pela malha **e** uma credencial de serviço, devolve access local curto, e também recusa usuário inexistente. Não aceitar `user_id` solto. Não usar token de admin.

Até uma dessas duas existir, a classe de delegação das operações de negócio é `BLOCKED_BY_SECURITY`.

### 6.5 Matriz de delegação

| Operação | AuthN atual | AuthZ real | Delegação suportada | Mudança necessária | Classe |
|---|---|---|---|---|---|
| Entrar no Portal Engenharia | JWT Keycloak na `engineering-api` + `GET Core /me` | `engineering.access` | já é o contrato do Portal | nenhuma para o gate do MFE | `READY` |
| Ler fila / detalhe / meta / mensagens / anexo / TOTVS do Controle MP | JWT local HS256 | role + conversa | ausente para o JWT do Portal | seção 6.4 | `BLOCKED_BY_SECURITY` |
| Mudar status, flag, `novo_codigo`, finalizar | JWT local | role 1 ou 2 + regras de campo | ausente | seção 6.4; writes só depois do contrato | `BLOCKED_BY_SECURITY` |
| Resubmit, editar campos devolvidos | JWT local | criador da request | ausente; e a fase 1 deixa o solicitante no legado | não expor no Portal na fase 1 | `NOT_APPLICABLE` |
| `sso-login` como sessão do BFF | JWT Keycloak | cria ou reusa usuário | efeito colateral de login, não delegação | não usar | `BLOCKED_BY_SECURITY` |
| Token de serviço / admin no lugar do usuário | não aceito na entrada | bypass | ausente de propósito | proibido pelo adendo | `BLOCKED_BY_SECURITY` |
| Diretório e notificação Controle MP → Core | service token de saída | app `controle-mp` | direção inversa | não inverte a identidade do analista | `NOT_APPLICABLE` |
| Catálogo ERP da ferramenta Produtos | JWT do Portal na `api-delpi` | permissão do owner da rota | `DownstreamClient` já delega | não usar isso para finalizar solicitação | `READY` para o catálogo; `NOT_APPLICABLE` como autoridade do workflow |

---

## 7. Modelo de domínio e persistência

Estado no **item**. Uma request (`tb` de requests, modelo `RequestModel`) tem `message_id` único, `created_by`, itens. Uma mensagem tem no máximo uma request (`create_request` devolve 409 se já existir).

| Conceito | Persistência | Evidência |
|---|---|---|
| Request | ligada a uma mensagem; `created_by` = `sub` do token, não um campo livre do body | `RequestService.create_request` |
| RequestItem | `request_type_id`, `request_status_id`, `product_id` opcional | `RequestItemModel` |
| RequestItemField | `field_type_id`, `field_tag` (1–255), `field_value`, `field_flag`. Unique parcial `(request_items_id, field_tag)` citado em `002_add_indexes.sql` | schema `CreateRequestItemFieldInput` |
| RequestType | seed id 1 `CRIAR`, id 2 `ALTERAR` | `RequestType` e `002_core_types.sql` |
| RequestStatus | 1 CRIADO, 2 EM PROCESSO, 3 FINALIZADO, 4 FRACASSADO, 5 DEVOLVIDO, 6 REJEITADO | `RequestStatus` L38–45 |
| Conversation | título, flag, `assigned_to`. `assigned_to` **não** entra na regra de status | `ConversationService` vs `change_item_status` |
| Message | texto, tipo (1 TEXT, 2 REQUEST, 3 SYSTEM), arquivos, request opcional | `MessageService.create_message` |
| Product | cabeçalho vazio + `tbProductFields` por tag. `codigo_atual` é a chave de busca | `ProductService.apply_request_item_finalized` |
| Comentário | não há entidade. Texto livre é `message.body` | ausência de modelo de comment |
| Anexo | binário no upload; metadado na mensagem. Sem FK no item | `file_routes.py`, `create_message` |
| Papel | `role_id` 1 ADMIN, 2 ANALYST, 3 USER. Coluna `permissions` do seed não é lida | `Role` em `request_service.py`; `require_roles` só é usado com `(1)` |

Field types de seed: 1 DEFAULT, 2 OBJECT. `fornecedores` vai como string JSON (`field_type_id` 2 no front).

Nascimento do fluxo usado pela UI (não o `POST /api/requests` solto, que o front não chama):

1. `POST /api/conversations/<id>/messages` com `message_type_id=2`, `create_request=true`, `request_items`.
2. `MessageService` grava a mensagem e os metadados de arquivo.
3. `RequestService.create_request` grava request, itens e campos na mesma sessão.
4. Socket `request:created` e `request:item_changed` (`change_kind=ITEM`) do primeiro item. O emit ocorre **antes** do `commit` do `db_session` (o serviço emite e o `with db_session()` só commita ao sair). Falha posterior de commit pode ter emitido evento de estado não persistido.
5. Notificação DELPI `request:created`, exceto quando a mensagem é do tipo REQUEST no canal de mensagem (`on_message_created` ignora tipo REQUEST para não duplicar).

---

## 8. Workflows e transições

Não existe ação “assumir”. `EM PROCESSO` é `PATCH /api/requests/items/<id>/status` com `request_status_id=2`. Dois analistas podem chamar o mesmo item: não há versão, `SELECT FOR UPDATE` nem dono. O último `UPDATE` prevalece. Cada chamada grava audit `STATUS_CHANGED` e emite socket, mesmo se o status numérico não mudar (a whitelist não compara com o status atual).

Alvos de `change_item_status` (`request_service.py` L504–511): **somente 2, 3, 5, 6**. Ids 1 e 4 → 409 `Status inválido para esta operação.` `FRACASSADO` não é alcançável por esta rota. O criador, em item DEVOLVIDO, pode `PATCH /items/<id>` com `request_status_id` arbitrário, **sem** a whitelist e **sem** socket. A UI não chama esse PATCH.

Lock `_ensure_not_locked`: status 3 ou 6 bloqueia novo status, edição de campo e flag. Não bloqueia `delete_item` nem `delete_request`.

| SOURCE_STATUS | ACTION | TARGET_STATUS | ACTOR | REQUIRED_PERMISSION | PRECONDITIONS | VALIDATIONS | SIDE_EFFECTS | AUDIT_EVENT | POSTCONDITION |
|---|---|---|---|---|---|---|---|---|---|
| qualquer exceto 3 e 6 | `PATCH .../status` body 2 | 2 EM PROCESSO | role 1 ou 2 | conv | item existe | whitelist | socket+DELPI `STATUS` | `STATUS_CHANGED` | item editável pelas regras de campo |
| idem | body 5 | 5 DEVOLVIDO | role 1 ou 2 | conv | idem | whitelist | cópia DELPI “devolvida para correção” | `STATUS_CHANGED` | criador pode editar e resubmeter |
| idem | body 6 | 6 REJEITADO | role 1 ou 2 | conv | idem | whitelist | socket+DELPI | `STATUS_CHANGED` | lock de status e campos; produto não é criado |
| idem | body 3 | 3 FINALIZADO | role 1 ou 2 | conv | regras de código + linha no TOTVS | ver abaixo | materializa produto local; `item.product_id`; audit de produto. Socket de produto **não** dispara: `ProductService` é construído sem notifier (`request_service.py` L520–525) | item `STATUS_CHANGED` + product `CREATED` ou `UPDATED` | item locked; Postgres local atualizado; ERP intocado |
| 5 | `PATCH .../resubmit` | 1 CRIADO | criador da request | conv | status atual 5 | senão 409 | socket STATUS; DELPI | `STATUS_CHANGED` | volta para a fila |
| 5 | `PATCH /items/<id>` com status | o id enviado | criador | não locked | status atual 5 | sem whitelist | sem socket | `UPDATED` | pode gravar 3 ou 4 sem TOTVS. Fora da UI |
| na criação | client envia `request_status_id` | o que vier | quem acessa a conversa | — | nenhuma checagem de enum | — | socket do primeiro item | `CREATED` | item pode nascer já em 3, 4 ou 6 se o client mandar |

### Finalização (autoridade)

Ordem dentro da mesma `db_session` (commit só no sucesso; exceção faz rollback — `session.py` L32–40):

1. `RequestService._validate_finalize_rules`: CRIAR exige `novo_codigo`. ALTERAR passa se houver `novo_codigo` **ou** `codigo_atual`.
2. `ProductService.apply_request_item_finalized` revalida: CRIAR exige `novo_codigo`. ALTERAR **exige `codigo_atual`** mesmo quando há `novo_codigo` (`product_service.py` L138–142). A regra efetiva de ALTERAR é a do `ProductService`.
3. `lookup_code` = `novo_codigo` (CRIAR) ou `codigo_atual` (ALTERAR). `effective_code` no ALTERAR = `novo_codigo` se preenchido, senão `codigo_atual`.
4. Acha produto local por tag `codigo_atual` = `lookup_code`. Se não há, cria `ProductModel` vazio.
5. `TotvsProductRepository.list_products(code=lookup_code)`. Zero linhas → 409 e rollback. Sem `INSERT` no Protheus.
6. Para cada campo do item exceto `novo_codigo` e `codigo_atual`: grava no produto o valor TOTVS mapeado, senão o valor da request. Mapa: `descricao`, `unidade`, `grupo`, `tipo`, `armazem_padrao`, `produto_terceiro`, `ref_cliente`, `fornecedores`. **`cta_contabil` não está no mapa**; permanece o valor da request.
7. Upsert `codigo_atual` = `effective_code`. `novo_codigo` não vira campo do produto.

Quem aprova a ficha técnica, no código, é o analista ou admin que envia status 3, sob essas regras. O BFF não pode “aprovar” por conta própria nem gravar `tbProducts`.

### Edição de campos (`_ensure_user_can_edit_field`)

Item não pode estar 3 ou 6.

- **CRIAR:** role 1 ou 2 editam só a tag `novo_codigo` (em qualquer status não locked). Se o analista também é o criador e o status é 5, edita as outras tags. Role 3 criador em DEVOLVIDO edita tudo **exceto** `novo_codigo`.
- **ALTERAR:** só o criador, e só em DEVOLVIDO, qualquer tag inclusive `novo_codigo`. Analista que não é o criador recebe 403.
- Flag de campo de request: role 1 ou 2, item não locked, qualquer tag.

Teste: `tests/test_request_field_edit_permissions.py` (não cobre `tipo`, `armazem_padrao`, `produto_terceiro`, `ref_cliente`; a API também não rejeita essas tags).

Imutabilidade pós-finalização/rejeição: status, campos e flags. Deletes continuam permitidos a quem acessa a conversa. O BFF não expõe delete.

---

## 9. Catálogo de campos CRIAR / ALTERAR

A API não tem enum de tags. `CreateRequestItemFieldInput` aceita qualquer `field_tag` de 1 a 255, `field_type_id` int, `field_value` opcional, `field_flag` opcional. Obrigatoriedade de negócio na API existe **só na finalização** (seção 8). O restante da obrigatoriedade abaixo é do validador de UI `validateStructuredItem` (`front-cadastro-mp/src/app/ui/requests/requestItemFields.logic.js`). Não há yup/zod nem `required` HTML. Campos de texto em branco não vão no POST (`pushTextField`); `fornecedores` sempre vai, como JSON string. O front aplica `trim` + `toUpperCase` antes de enviar. A API não normaliza.

Defaults de UI (`productFields.js` `DEFAULT_VALUES`): `tipo=MP`, `cta_contabil=11401002`, `armazem_padrao=01`, `produto_terceiro=1`. `YES_NO_OPTIONS`: valor `1` rótulo “NÃO”, valor `2` rótulo “SIM”. Portanto o default de produto de terceiros é “NÃO”.

| Campo técnico | Label pt-BR | Tipo | Obrigatório na API ao criar | Obrigatório na UI ao enviar | Criar | Alterar | Editável por | Origem na finalização | Validação |
|---|---|---|---|---|---|---|---|---|---|
| `codigo_atual` | Código atual | texto, field type 1 | não | só ALTERAR | a UI de CRIAR não envia | envia | criador em DEVOLVIDO no ALTERAR; analista não edita | vira `effective_code` no produto, não o texto cru do ERP | UI não vazia em ALTERAR. API exige na finalização de ALTERAR |
| `novo_codigo` | Novo código | texto | não na criação; sim para finalizar CRIAR | não no composer; sim na UI ao finalizar CRIAR | envia se preenchido | envia se preenchido | role 1 ou 2 em CRIAR não locked; criador USER em CRIAR devolvido **não** pode | não persiste no produto; em ALTERAR substitui o código gravado | UI: `requireNovoCodigoForCreateFinalization` em `RequestsPage.jsx`. API: `_validate_finalize_rules` + `ProductService` |
| `grupo` | Grupo | texto; UI é select | não | sim | sim | sim | criador em DEVOLVIDO; analista só se também for o criador em CRIAR devolvido | TOTVS `B1_GRUPO`, senão request | UI: lista `PRODUCT_GROUP_OPTIONS` (códigos 1001–1055 com furos, `productFields.js`). API aceita qualquer string |
| `descricao` | Descrição | texto | não | sim | sim | sim | idem | TOTVS `B1_DESC` | UI não vazia |
| `tipo` | Tipo | texto | não | sim | sim | sim | idem | TOTVS `B1_TIPO` | UI não vazia; default `MP` |
| `armazem_padrao` | Armazém padrão | texto; UI select `01` Almoxarifado, `99` Fábrica | não | sim | sim | sim | idem | TOTVS `B1_LOCPAD` | UI não vazia; default `01` |
| `unidade` | Unidade | texto; UI select PC, UN, MM, MT, L, G, KG, MI (duas vezes no array), CX, FD, GL, JG, P, RL, RS | não | sim | sim | sim | idem | TOTVS `B1_UM` | UI não vazia |
| `produto_terceiro` | Produto terceiro | texto; UI select 1/2 | não | sim | sim | sim | idem | TOTVS `B1_TPMAT` | UI não vazia; default `1` |
| `cta_contabil` | CTA contábil | texto | não | sim | sim | sim | idem | **não vem do mapa TOTVS**; fica o valor da request. A coluna `B1_CONTA` é lida na query e devolvida nas rotas `/totvs`, mas `apply_request_item_finalized` não a copia | UI não vazia; default `11401002` |
| `ref_cliente` | Ref. cliente | texto | não | sim | sim | sim | idem | TOTVS `B1_REFEREN` | UI não vazia |
| `fornecedores` | Fornecedores | JSON string, field type 2 | não | UI exige linhas completas; a API guarda a string | sempre, mesmo `[]` | sempre | idem | TOTVS `SA5010` via `FOR JSON PATH`, senão a string da request | UI: cada linha exige `supplier_code`, `store`, `supplier_name`, `part_number`. `catalog_number` não é validado. `SUPPLIER_COLUMNS.required` do schema **não** é lido pelo validador |

Subcampos do JSON, alinhados ao SELECT (`totvs_product_repository.py`): `supplier_code` (`A5_FORNECE`), `store` (`A5_LOJA`), `supplier_name` (`A5_NOMEFOR`), `part_number` (`A5_CODPRF`), `catalog_number` (`A5_CODPRCA`). A busca `SA2010` devolve só código, loja e nome.

Autofill de ALTERAR no front: ao digitar `codigo_atual`, `GET /api/products/totvs/<code>` preenche grupo, tipo, descrição, armazém, unidade, produto terceiro, CTA, ref. cliente e fornecedores se o usuário ainda não sujou o campo. O objeto TOTVS traz `codigo` (`B1_COD`), e o form não copia essa chave para `codigo_atual`.

Não há outros tags no composer. Tags extras que um client mandar são persistidas e, na finalização, caem no fallback “valor da request” porque não estão no mapa.

---

## 10. Inventário frontend legado

Stack: React + Vite, CSS próprio (`cmp-*`), `lucide-react`, `react-hot-toast`. Sem MUI, Ant, yup ou zod. Base HTTP: `${VITE_API_BASE_URL}${VITE_API_PREFIX || "/api"}`, header `Authorization: Bearer`. 401 tenta `POST /auth/refresh`.

Router (`AppRouter.jsx`): guard único `ProtectedRoute` (só sessão). Papel é da tela.

| Path | Página | Papel na rota |
|---|---|---|
| `/login`, `/register`, `/sso/logout-from-parent` | públicas | — |
| `/conversations`, `/conversations/:id` | `ConversationsPage` | autenticado |
| `/requests` | `RequestsPage` | autenticado |
| `/products` | `ProductsPage` | autenticado |
| `/account` | `AccountPage` | autenticado |
| `/admin/users` | `AdminUsersPage` | página manda não-admin para `/` |
| `/audit` | `AuditPage` | página mostra erro se não for admin |
| `*` | redirect `/` → `/conversations` | — |

`ConversationDetailPage` não está no router. `deleteMessageApi`, `createRequestApi`, `deleteRequestApi`, `updateRequestItemApi` existem no client e a UI não os chama. A criação real é `POST .../messages`.

### Jornadas

**USER (3).** Login local ou SSO → conversas. Cria conversa, mensagem, anexo (MIME whitelist, 20 MB) e solicitação CRIAR/ALTERAR no `RequestComposerModal` (status enviado = 1). Em `/requests` vê só as próprias (recorte da API). Edita item próprio em DEVOLVIDO e reenvia (`PATCH .../resubmit`). Em CRIAR devolvido a UI não envia `novo_codigo`. Não muda status, não põe flag, não abre auditoria. Produtos em leitura.

**ANALYST (2).** Tudo do USER, mais filtro “Criado por”, botões Em andamento / Devolver / Rejeitar / Finalizar, edição de `novo_codigo` em CRIAR, flag de campo da solicitação e flag de produto. Não exclui conversa e não administra usuários. Não há botão para FRACASSADO nem para voltar a CRIADO (isso é o Reenviar, só do dono).

**ADMIN (1).** Tudo do analista, mais excluir conversa, `/audit` e `/admin/users` (papel, soft delete, sync de `central_subject`).

Deep link: `/conversations/:id?messageId=`. “Ir para conversa” na solicitação monta isso. SSO: `DELPI_NAVIGATE` guarda path pendente; depois do login vai para ele ou para `/conversations`. O sync com o pai manda só `pathname`.

Realtime: Socket.IO com token na query e em `auth`. Eventos consumidos: `message:new`, `conversation:new`, `request:created`, `request:item_changed`, `product:created`, `product:updated`, `product:flag_changed`. Toasts de status em `toastForRequestStatus` **não** usam os mesmos rótulos de `requestStatus.js` (o toast trata 1 como “retornada para análise” e 4 como “reprovada”). O badge do Topbar conta `GET /requests/count?status_id=1`.

Padrões reutilizáveis como referência, não como cópia: lista desktop em tabela e mobile em cards; filtros com debounce; detalhe em modal; ficha única para composer, solicitação e produto; estados “Carregando...”, banner `error` e vazio. O Portal deve usar `@delpi/plugin-ui`, não este CSS.

---

## 11. Inventário Engineering API

Boot: `engineering-api/engineering_app/main.py`, FastAPI, `root_path` default `/apps/engineering-api` (`config.py` L21–24). Rotas internas são `/v1/...`. Nginx (`gateway/nginx.conf`) publica `/apps/engineering-api/` e reescreve o prefixo. O MFE já chama, por exemplo, `/apps/engineering-api/v1/products` (`plugins/engineering/src/features/products/api/productApi.ts`).

O prefixo candidato `/apps/engineering-api/v1/product-registration` **respeita o padrão real**. O módulo ainda não existe (`product-registration` / `product_registration` ausentes em `engineering-api` e `plugins/engineering`).

AuthN: `jwt_middleware` + `delpi_auth`. AuthZ das rotas de negócio: `@require_any_permission(["engineering.access"])` e principal humano. Permissões efetivas: `GET {CORE_API_URL}/me` com o Bearer. Não há cliente da API Flask do Controle MP nem DSN desse Postgres. Postgres da engineering-api é o de não conformidade (`ENG_NC_DB_*`).

Padrão de saída a copiar: `infrastructure/gateways/downstream_client.py` (seção 6.3). Exemplos vivos:

- Home → `requests_api_gateway.py` (`GET /requests/work-queue`, `GET /requests/mine`) e `api_delpi_gateway.py`. Timeout default de home 5s. 401/403 → forbidden; resto → unavailable.
- Produtos → `delegated_auxiliary.py`: Bearer humano, sem S2S, para `/products/search`, detalhe, fornecedores, estrutura, desenho, PDF, histórico de preço.
- Facts LMP → Bearer humano **mais** client-credentials. Fail-closed sem credencial.

Composição por composer (`home_composer.py`, `lmp_composer.py`, `nc_composer.py`, `overview_composer.py`, `drawing_composer.py`). Um módulo novo entra como router incluído em `main.py`, composer próprio e gateway próprio. Não reutilizar `product_routes.py`: ele é o catálogo/desenho e já contém a frente de PDF. Há marcadores de conflito git em arquivos de produtos do plugin (`productRoutes.ts`, `ProductsListPage.tsx`, `ProductDetailPage.tsx`).

Testes: pytest + `TestClient`, permissão, 401, principal humano, port stub (`tests/test_lmp_routes.py`). `tests/test_architecture.py` proíbe import de `flask`, `requests_app` e do pacote da api-delpi.

Não há segundo gateway para inventar. O BFF é a própria `engineering-api`.

---

## 12. Inventário Portal Engenharia

Router: `plugins/engineering/src/app/engineeringRoutes.ts`. Base `/apps/engineering`. Views: `home`, `overview`, `lmps`, `nonconformities`, `products`, `help`. Qualquer outro relative path, inclusive `product-registration`, retorna `not_found` (L64–71 e o fallback L71).

```64:71:plugins/engineering/src/app/engineeringRoutes.ts
  if (relativePath === "products" || relativePath.startsWith("products/")) {
    return { view: "products", pathname: path, relativePath };
  }
  if (relativePath === "help") {
    return { view: "help", pathname: path, relativePath };
  }
  return { view: "not_found", pathname: path, relativePath };
```

A convenção para a rota passar a existir é um ramo irmão de `products` / `nonconformities` (`/apps/engineering/nonconformities` e `.../:id`). O host resolve o MFE pelo prefixo `/apps/engineering`. O manifest `engineering.manifest.json` (v0.2.0) declara a entrada do app e não uma linha por subpágina de produtos ou NC. **Não é obrigatório** criar outra entrada de manifest só para a subrota, desde que o host continue montando o MFE em `/apps/engineering`. Confirmar o host no momento da implementação; o router do plugin, hoje, rejeita o path.

Shell: `EngineeringPluginShell.tsx`. TopBar: Início, Visão geral, Ajuda. Produtos e NC entram pelo catálogo `engineeringRouteCatalog.ts` e pelo switch de `App.tsx`, não pela TopBar. O módulo novo segue esse encaixe. Nome de apresentação no catálogo: `Controle e Cadastro de Produtos`. Id técnico: `product-registration`.

Cliente: `src/api/httpClient.ts`. `fetch` same-origin, Bearer do host, `X-Delpi-Caller-App: engineering`, timeout 15s. Erros nomeados: `unauthorized`, `forbidden`, `rate_limited`, `unavailable`, `timeout`, `network_error`. Envelope `data`.

UI: `@delpi/plugin-ui`, prefixo BEM `engineering`, façade `src/ui/engineeringUi.ts`. Deep link interno por `history.pushState` + `popstate`. Link externo só sob `/apps/...`. Ajuda in-app é exigida por `feature-help-sync` (`HelpPage.tsx` hoje cita NC de forma hardcoded).

Arquivos que a implementação futura cria:

- `plugins/engineering/src/features/product-registration/` (routes, pages, api, copy pt-BR, types, teste)
- `engineering-api/engineering_app/interface/http/routes/product_registration_routes.py`
- `engineering-api/engineering_app/composition/product_registration_composer.py`
- `engineering-api/engineering_app/infrastructure/gateways/controle_mp_gateway.py` (nome indicativo)
- DTOs em `application/` do mesmo contexto
- `engineering-api/tests/test_product_registration_routes.py`

Arquivos existentes que a implementação futura precisa tocar (gate compartilhado, um integrador por vez):

- `plugins/engineering/src/app/engineeringRoutes.ts` e o teste
- `plugins/engineering/src/App.tsx`
- `plugins/engineering/src/content/engineeringRouteCatalog.ts`
- `plugins/engineering/src/features/help/HelpPage.tsx`
- `engineering-api/engineering_app/main.py` (`include_router`)
- `engineering-api/engineering_app/config.py` (URL base da API Controle MP; hoje ausente)

`EngineeringPluginShell.tsx` fica de fora se o módulo não entrar na TopBar. O manifest só muda se o menu do host precisar de uma entrada nova.

---

## 13. Inventário Requests API / My Requests

Motor: `requests-api`, schema `my_requests`, workflow JSON por tipo, sem `if request_type` no engine (`workflow_engine.py`). `Request` tem `payload` JSONB, `status`, `version`, `return_reason`, `correction_targets`. Não há tabela `request_items` nas migrations.

Seed `migrations/V007__seed_raw_material_creation_request_type.sql` e `requests_app/content/pt-BR/workflows/raw_material_creation.json`:

- `presentation_mode=schema_driven`
- campos `description`, `unit` (UN/KG/M), `notes`
- `destination_config.adapter=none`
- `submitted` → `in_progress` (`start` + `assignSelf`) → `completed` \| `rejected`
- `cancel` do dono em `submitted`
- permissões `my-requests.raw-material-creation` + `.create` / `.process`
- UI: `plugins/my-requests/src/features/raw-material-creation/`, label `Criação de matéria-prima`

`raw-material-update`: ausente em `requests-api` e `plugins/my-requests`.

A transição `return` / `needs_information` existe no workflow de emissão de NF e no motor, e **não** está no JSON de matéria-prima. Lookups TOTVS do adapter `api_delpi` são de NF (`/request-lookups`), não deste tipo.

| Capacidade | Controle MP | Requests API | Gap de paridade | Impacto futuro |
|---|---|---|---|---|
| Identidade | usuário local + `central_subject` | `sub` Keycloak no `created_by_user_id` | papéis locais 1/2/3 não são as permissões `my-requests.*` | mapa de identidade no cutover |
| Fila | `GET /api/requests/items`, staff vê tudo | `GET /requests/work-queue` e `/mine`, escopo por permissão | semântica de escopo diferente | não copiar a fila global sem decisão |
| Filtros | status, tipo, nome do criador, item, datas | `type_code`, `status`, `branch`, `q`, página | sem ficha MP | filtros novos no tipo, não no motor |
| Contagem | `/count` (sem `is_deleted`) e `total` da lista | `total` paginado; sem endpoint por status | — | usar `total` |
| Detalhe | request + items + fields | `GET /requests/{id}` com `allowed_actions` | legado não devolve `allowed_actions` | o motor já tem o campo que o legado não tem |
| Itens | entidade | ausente; payload JSON | modelo diferente | um request do motor ≠ N itens legados sem desenho de payload |
| Campos dinâmicos | tags livres | `form_schema` | stub tem 3 campos; legado tem a ficha da seção 9 | schema do tipo precisa nascer da ficha real |
| Produto / fornecedor | TOTVS na finalização e busca SA2 | ausente para este tipo | sem código, sem fornecedor | adapter próprio; não reusar o de NF sem contrato |
| Comentários | mensagens da conversa | `GET/POST /requests/{id}/comments` | modelos diferentes | não há thread Socket.IO no motor |
| Anexos | arquivo da mensagem | `request_attachments` e artifacts | sem vínculo ao item | migração de binário é decisão de cutover |
| Histórico | audit admin; analista não lê audit | `request_status_history` + `GET /events` | analista do legado não tem timeline | motor é mais completo |
| Responsável | não há dono do item; `assigned_to` da conversa é decorativo no workflow | `assignSelf` grava `request_assignments`; o JSON de detalhe não expõe assignee | legado não atribui | não inventar assignee na fase 1 |
| Máquina | 1–6 no item; 4 inalcançável pela rota oficial | `start`, `complete`, `reject`, `cancel` no stub | sem DEVOLVIDO, sem FRACASSADO, sem resubmit no tipo MP | `return` teria de entrar no JSON do tipo |
| Iniciar análise | status 2 | `start` | nomes diferentes; legado não atribui | mapa de status |
| Devolver | status 5 | ausente no tipo MP | gap funcional | bloqueia cutover do fluxo de correção |
| Rejeitar | status 6 | `reject` | ok no motor | falta motivo estruturado no legado |
| Finalizar | status 3 + TOTVS + produto local | `complete` com `adapter=none` | sem invariante de código | não apontar o destino para `none` e chamar de paridade |
| Validar código | `list_products(code=)` dentro da finalização | ausente no tipo | gap | a autoridade da fase 1 continua no Flask |
| Atualizar campo | PATCH de field com regra por tag | `PATCH /requests/{id}` exige ação `edit` + `version` | `edit` ausente no workflow MP; legado não tem versão | OCC do motor é melhor que o legado |
| Notificação | socket + Core com service token do Controle MP | outbox na mesma transação → Core | canais diferentes | cutover troca o produtor |
| TOTVS | leitura direta pyodbc no Flask | adapter `none` neste tipo | fontes diferentes | BFF da fase 1 não unifica |

A `engineering-api` já lê a work queue desse motor na Home, com deep link `/apps/my-requests`, sem filtro `raw-material-creation`. Isso permanece. A fase 1 não passa a fila de matéria-prima por esse motor.

---

## 14. Integrações TOTVS, Core e notificações

### TOTVS dentro do Controle MP

`TotvsProductRepository` + `totvs_connection.py`. URL `mssql+pyodbc`, ODBC Driver 17, host/porta/db/user/password (`settings.py`). Porta default 1433. Sem os quatro envs, a API sobe e o primeiro uso responde 409. `pool_pre_ping=True`. Timeout de connect/query: ausente no código. Cache de resultado: ausente (`lru_cache` só no sessionmaker).

- `list_products(code)`: `SB1010`, `D_E_L_E_T_=''`, `B1_COD = :code` (igualdade). Sem `code`, devolve todas as linhas. Colunas: código, grupo, tipo, descrição, armazém, unidade, terceiro, `B1_CONTA`, referência, fornecedores JSON de `SA5010`.
- `search_suppliers`: `SA2010`, LIKE em código, loja e nome, `OFFSET/FETCH`, limit 1–50.
- Erro ODBC não tratado vira 500.

Operacional do Controle MP (Postgres): usuários, conversas, mensagens, arquivos, requests, itens, campos, produtos materializados, audit, tokens. Fonte ERP (leitura): existência do código na finalização e as rotas `/totvs`. A finalização não grava no Protheus.

### api-delpi

A `engineering-api` já lê produto e fornecedor pela api-delpi (`delegated_auxiliary.py`), com o JWT do usuário. Essa leitura serve a ferramenta Produtos. A finalização do Controle MP **não** passa por ela. Mostrar no detalhe um snapshot da api-delpi ao lado da ficha pode divergir do que `ProductService` vai aceitar (mapa de colunas e o momento da leitura). Para o analista deste módulo, a consulta de apoio ao código usa os endpoints `/api/products/totvs/...` do Controle MP, depois da delegação. A ferramenta Produtos existente não muda de fonte.

### Core

- AuthZ do Portal: `GET /me` já usado por `delpi_auth`.
- Notificação do Controle MP: `POST {DELPI_CORE_API_URL}/integrations/notifications`, header `X-Delpi-Service-Token`, timeout 15s. Desliga se `DELPI_NOTIFICATIONS_ENABLED` não for true. Falha é logada e engolida.
- Diretório: `GET /integrations/directory/users/by-app?app=controle-mp` no sync admin.

Eventos socket servidor→cliente relevantes: `request:created`, `request:item_changed` (`STATUS`, `FIELDS`, `FIELD_FLAG`, `ITEM`), `message:new`, `message:read`, `conversation:new`, `product:flag_changed`. `product:created` / `product:updated` só se o `ProductService` receber notifier; a finalização atual não passa notifier. O Portal da fase 1 pode recarregar por polling/refetch. Abrir o socket do Controle MP a partir da `engineering-api` não está autorizado pelo contrato atual (seção 6.3).

Cópias DELPI (`_status_notification_copy`): 1 “retornada para análise”, 2 “em análise”, 3 “aprovada”, 4 “reprovada”, 5 “devolvida para correção”, 6 “rejeitada”. O id 4 é “reprovada” na notificação e `FRACASSADO` no seed. O id 1 é CRIADO no seed e “retornada para análise” na notificação (é o texto do resubmit). A UI do Portal deve usar os nomes do seed (CRIADO, EM PROCESSO, FINALIZADO, FRACASSADO, DEVOLVIDO, REJEITADO), não essas cópias.

---

## 15. Matriz completa de contratos BFF

Prefixo público, alinhado ao gateway: `/apps/engineering-api/v1/product-registration`. Router interno: `/v1/product-registration`. Nomes em inglês. O consumer é o plugin `engineering`. O owner dos dados continua a API Controle MP. AuthN do BFF: JWT do Portal já validado pela `engineering-api`. AuthZ do BFF: `engineering.access` **e** a autorização da fonte (role local + conversa). Sem a seção 6.4, a fonte responde 401 e o BFF devolve 403 fail-closed, sem fallback admin.

Timeout sugerido, no mesmo espírito do home gateway: 5s para meta e listagens; 15s para detalhe composto e para TOTVS. Retry: no máximo uma repetição em GET idempotente com falha de transporte/timeout; zero retry em PATCH/POST. Idempotency-Key: a fonte não honra. O BFF não finge idempotência.

Erros da fonte → BFF: 401 da fonte após delegação válida vira 502 com corpo opaco (token local inesperado); 403 → 403; 404 → 404; 409 de regra → 409 com `code` estável (`finalize_code_required`, `totvs_not_found`, `item_locked`, `invalid_status`); timeout/transporte → 504/503; 500 da fonte → 502. Não repassar `str(err)` de debug.

DTOs neutros carregam `source: "controle-mp"` e os ids numéricos da fonte em `sourceIds`. Status e tipo ganham `code` inglês (`created`, `in_progress`, `finalized`, `failed`, `returned`, `rejected`, `create`, `update`) **além** do id e do label pt-BR. Isso evita amarrar a UI ao inteiro do legado e deixa o cutover trocar o provider sem renomear a tela. A tradução fica no gateway, não no React.

| OPERATION_ID | HTTP | PATH | SOURCE_ENDPOINT | Classe |
|---|---|---|---|---|
| `listProductRegistrationItems` | GET | `/requests` | `GET /api/requests/items` | `REQUIRES_AUTHZ_DECISION` |
| `getProductRegistrationRequest` | GET | `/requests/{requestId}` | `GET /api/requests/{id}` | `REQUIRES_AUTHZ_DECISION` |
| `listProductRegistrationMessages` | GET | `/requests/{requestId}/messages` | `GET /api/conversations/{conversationId}/messages` | `REQUIRES_SOURCE_API_CHANGE` |
| `downloadProductRegistrationAttachment` | GET | `/attachments/{fileId}` | `GET /api/files/{id}/download` | `REQUIRES_AUTHZ_DECISION` |
| `getProductRegistrationMeta` | GET | `/reference-data` | `GET /api/requests/meta` | `REQUIRES_AUTHZ_DECISION` |
| `getProductRegistrationErpProduct` | GET | `/erp-products/{code}` | `GET /api/products/totvs/{code}` | `REQUIRES_AUTHZ_DECISION` |
| `searchProductRegistrationSuppliers` | GET | `/suppliers` | `GET /api/products/totvs/suppliers` | `REQUIRES_AUTHZ_DECISION` |
| `getProductRegistrationLocalProduct` | GET | `/local-products/{productId}` | `GET /api/products/{id}` | `REQUIRES_AUTHZ_DECISION` |
| `startProductRegistrationAnalysis` | POST | `/items/{itemId}/actions/start` | `PATCH /api/requests/items/{id}/status` body `2` | `REQUIRES_AUTHZ_DECISION` |
| `returnProductRegistrationItem` | POST | `/items/{itemId}/actions/return` | body `5` | `REQUIRES_AUTHZ_DECISION` |
| `rejectProductRegistrationItem` | POST | `/items/{itemId}/actions/reject` | body `6` | `REQUIRES_AUTHZ_DECISION` |
| `finalizeProductRegistrationItem` | POST | `/items/{itemId}/actions/finalize` | body `3` | `REQUIRES_AUTHZ_DECISION` |
| `updateProductRegistrationNewCode` | PATCH | `/items/{itemId}/fields/new-code` | `PATCH /api/requests/fields/{fieldId}` ou `POST .../fields` se a tag não existir | `REQUIRES_AUTHZ_DECISION` |
| `setProductRegistrationFieldFlag` | PATCH | `/fields/{fieldId}/flag` | `PATCH /api/requests/fields/{id}/flag` | `REQUIRES_AUTHZ_DECISION` |
| `projectAllowedActions` | — (campo do detalhe) | — | a fonte não devolve `allowed_actions` | `REQUIRES_SOURCE_API_CHANGE` |
| `compareAndSetItemStatus` | — | — | sem coluna de versão | `REQUIRES_SOURCE_API_CHANGE` |
| `resubmitProductRegistrationItem` | — | — | `PATCH .../resubmit` existe | `FUTURE_ONLY` na superfície do analista |
| `searchItemsByTechnicalDescription` | — | — | ausente | `FUTURE_ONLY` até a fonte ganhar o filtro |

Nenhum contrato está `READY_FOR_IMPLEMENTATION`: os que chamam a API de negócio dependem da delegação. `projectAllowedActions` e `compareAndSetItemStatus` continuam incompletos mesmo depois da delegação. `listProductRegistrationMessages` depende de `conversation_id`, que a listagem de itens já traz e o `GET /api/requests/{id}` não traz. Deep link só com `requestId` não alcança a conversa. Menor correção na fonte: incluir `conversation_id` e o mini do solicitante em `GET /api/requests/{id}`. Até lá, o detalhe aberto a partir da fila usa o `conversationId` que a listagem já devolveu; o deep link canônico deve carregar os dois ids (`/requests/{requestId}/items/{itemId}`) e o BFF, se não tiver `conversation_id`, omite a thread em vez de adivinhar.

### Contratos que a fase de leitura usa

`listProductRegistrationItems`  
Request query: `page`, `pageSize` (o gateway traduz para `limit`/`offset` e sempre os envia), `status`, `type`, `createdByName`, `itemId`, `dateMode`, `dateFrom`, `dateTo`. Sem `q` de descrição.  
Response: `{ items: QueueItem[], page, pageSize, total }`. `QueueItem`: `requestId`, `itemId`, `conversationId`, `messageId`, `type`, `status`, `createdBy {id, fullName}`, `itemCreatedAt`, `itemUpdatedAt`, `productId`, `source`, `sourceIds`. Não incluir `fieldsCount`. Não chamar `/api/requests/count`.  
Escopo: o da fonte (staff vê a fila inteira). O BFF não restringe por assignee.  
Audit: nenhum na fonte para GET. O BFF loga `request_id` de correlação, não a ficha.

`getProductRegistrationRequest`  
Response: request, itens, fields (tag, value, flag, field id), `productId`. `allowedActions` fica ausente até a fonte calcular. O plugin da fase de leitura não renderiza botões de decisão.  
Postcondition: nenhuma escrita.

`getProductRegistrationMeta`  
Response: tipos e status com id, code e label. Listas fechadas de grupo/unidade/armazém/terceiro são conteúdo de apresentação do plugin, copiadas como rótulo a partir de `productFields.js`, não como segunda autoridade de validação. A API não as publica.

`downloadProductRegistrationAttachment`  
O id opaco do BFF é o `file_id` da fonte. A fonte já exige que o arquivo pertença a uma mensagem de conversa acessível. O BFF transmite o stream e não grava cópia. Fase de leitura pode incluir o download: é GET autorizado, não decisão de cadastro. Audit na fonte: ausente nesse GET.

### Contratos de decisão (só depois da delegação e de aceite explícito)

Cada POST de ação lê o item de novo, chama o PATCH de status e devolve o detalhe relido (read-back). Body vazio exceto `finalize` / `return` / `reject`, que não precisam de motivo: a fonte não tem campo de motivo. Não enviar `request_status_id` bruto ao browser como contrato; o path da ação é que fixa o alvo.

`finalizeProductRegistrationItem` é o único que materializa produto. Pré-condição que o BFF pode checar para falhar cedo, sem substituir a fonte: CRIAR com `novo_codigo` vazio. A fonte continua sendo quem consulta o TOTVS e quem grava. Resposta 409 `totvs_not_found` quando a mensagem da fonte for a de produto inexistente. Não há rollback de negócio depois do commit: o ERP não foi escrito; o Postgres local só commita junto com o status. Repetir a ação com item já 3 ou 6 → 409 `item_locked`. Repetir com o mesmo status ainda não terminal **não** é no-op: gera outro audit e outro socket.

`updateProductRegistrationNewCode` só para item CRIAR, ator staff, tag `novo_codigo`. O gateway procura o field na leitura imediatamente anterior. Se não existir, `POST /api/requests/items/{id}/fields` e em seguida o PATCH, na ordem que a UI legada usa. Não atualizar outras tags pelo Portal na fase do analista: a fonte recusa, e o solicitante corrige no legado.

`setProductRegistrationFieldFlag` existe na fonte e na UI do analista. Entra no mesmo gate de escrita. Não é necessária para a fila read-only.

`projectAllowedActions` (mudança aditiva preferida na fonte, calculada dentro de `RequestService`, para o BFF não reimplementar a matriz): para staff, item não locked: `start`, `return`, `reject`, `finalize`, `set_flag`; em CRIAR também `edit_new_code`. Para o criador em DEVOLVIDO: `resubmit` e edição de campos (exceto `novo_codigo` em CRIAR). Item 3 ou 6: lista vazia. Até esse campo existir, o Portal de leitura não mostra ações; o Portal de escrita que duplicasse a matriz passaria a ser uma segunda autoridade. Isso fica fora do desenho.

`compareAndSetItemStatus`: coluna `version` no item, `PATCH` condicional, 409 `stale_version`. Ausente. PRC-3 ou aceita last-write-wins com essa frase no contrato, ou espera a coluna. As duas opções são decisão, não detalhe de implementação.

---

## 16. Modelo de páginas e navegação

Uma área, duas rotas. Seções da hipótese (ficha, fornecedor, conversa, produto, histórico) são blocos da página de detalhe, não páginas soltas. O solicitante não ganha jornada neste MFE na fase 1.

### Fila — `Requests Queue`

- Persona: analista ou admin com `engineering.access` e, depois da delegação, role local 1 ou 2. Usuário só com `engineering.access` e role local 3 vê a própria fila, porque a fonte filtra assim; a fase 1 não depende disso.
- Objetivo: achar itens e abrir o detalhe.
- Dados: `listProductRegistrationItems`, `getProductRegistrationMeta`.
- Kit: página de lista do `@delpi/plugin-ui`, filtros, tabela/cards, badge de status.
- Vazio: “Nenhuma solicitação encontrada.”
- Carregamento, erro e forbidden: estados já usados nas outras ferramentas do plugin.
- Ações da fase de leitura: Abrir, e link para o legado `/controle-mp` quando o deep link do produto legado estiver publicado. Sem botões de status.
- Deep link: `/apps/engineering/product-registration` e a mesma rota com query de filtro (F5 preserva a query).
- Responsivo: tabela no desktop, cards no estreito, como o restante do plugin.
- Aceite: AC-PRC-02, 03, 04, 05.

### Detalhe — `Request Details`

- Rota: `/apps/engineering/product-registration/requests/{requestId}/items/{itemId}`.
- Objetivo: ler a ficha do item, os irmãos da mesma request, fornecedores parseados do JSON, mensagens quando `conversationId` for conhecido, produto local se houver `productId`, e consulta ERP sob demanda pelo código.
- Endpoints: `getProductRegistrationRequest`, `listProductRegistrationMessages` (quando houver conversation id), `downloadProductRegistrationAttachment`, `getProductRegistrationLocalProduct`, `getProductRegistrationErpProduct`.
- Histórico de audit: a fonte só entrega para role 1 em `/api/audit/*`. O bloco do analista mostra `itemCreatedAt`, `itemUpdatedAt` e o status. Não promete trilha de audit. Timeline rica fica `FUTURE_ONLY` (ou admin, se um dia o papel local 1 for reconhecido e o endpoint for delegado de propósito).
- Ações de leitura: baixar anexo, abrir conversa no legado (`/conversations/{id}?messageId=`).
- Ações de escrita (gate posterior): Iniciar análise, Devolver, Rejeitar, Finalizar, editar Novo código em CRIAR, flag. Cada uma desabilitada quando o contrato de ação não estiver ligado. Forbidden da fonte aparece como 403, sem otimismo.
- Aceite: AC-PRC-04, 05, 06, 07.

Não criar página separada de “Technical Review”, “Supplier Information” ou “History”. Não criar tela de nova solicitação: o solicitante continua no Controle MP.

---

## 17. Paridade e evolução futura

O frontend fala com DTOs da seção 15 (`source`, `sourceIds`, `status.code`, fields como lista de tag/value). Trocar o provider é trocar o gateway, não as páginas, **quando** um segundo provider real existir. Até lá não há interface `RegistrationProvider`, não há feature flag de dual-read e não há dual-write.

Diferenças que o cutover terá de resolver antes de desligar o Flask:

- Ids numéricos locais versus id do `requests-api`.
- Status por item versus status único do request, e o mapa 2→`in_progress`, 3→`completed`, 6→`rejected`. DEVOLVIDO e FRACASSADO não têm alvo no stub.
- N campos tag/valor versus `form_schema` de três campos.
- Papel local versus permissão `my-requests.raw-material-creation.process`.
- Conversa Socket.IO versus comments + events.
- Anexo da mensagem versus attachment do request.
- Produto materializado no Postgres do Controle MP versus `adapter=none`.
- `central_subject` já gravado versus `sub` nativo do motor.
- TOTVS pyodbc na finalização versus lookup do adapter de NF.
- Notificação engolida no client do Controle MP versus outbox do motor.
- Finalização com prova de código no ERP versus `complete` sem invariante.

A abstração mínima da fase 1 é um gateway com os métodos de leitura (e, no gate seguinte, as cinco ações). O nome do tipo no DTO já é `create` / `update`, não um enum fechado só de matéria-prima, mas o catálogo de tags da seção 9 é o único caso com consumidor.

---

## 18. Mapa de arquivos afetados

Nenhum arquivo desta tabela foi modificado agora, exceto este documento e o link no ROADMAP.

| Repositório | Arquivo ou módulo | Mudança necessária | Motivo | Owner | Risco de conflito |
|---|---|---|---|---|---|
| delpi-central | `plugins/engineering/src/features/product-registration/**` | NEW_FILES | UI | PRC | baixo, diretório novo |
| delpi-central | `engineering_app/interface/http/routes/product_registration_routes.py` | NEW_FILES | rotas BFF | PRC | baixo |
| delpi-central | `engineering_app/composition/product_registration_composer.py` | NEW_FILES | wiring | PRC | baixo |
| delpi-central | `engineering_app/infrastructure/gateways/controle_mp_gateway.py` | NEW_FILES | HTTP fonte | PRC | baixo |
| delpi-central | `engineering-api/tests/test_product_registration_routes.py` | TESTS | contrato | PRC | baixo |
| delpi-central | `plugins/engineering/src/app/engineeringRoutes.ts` | EXISTING_FILES_TO_CHANGE / SHARED_FILES | ramo de rota | PRC, serializado | médio (router único) |
| delpi-central | `plugins/engineering/src/App.tsx` | SHARED_FILES | switch de view | PRC | médio |
| delpi-central | `plugins/engineering/src/content/engineeringRouteCatalog.ts` | SHARED_FILES | entrada do catálogo | PRC | médio |
| delpi-central | `plugins/engineering/src/features/help/HelpPage.tsx` | SHARED_FILES | ajuda | PRC | médio |
| delpi-central | `engineering_app/main.py` | SHARED_FILES | `include_router` | PRC | alto enquanto a EVA também sobe rotas/MCP |
| delpi-central | `engineering_app/config.py` | SHARED_FILES | URL da fonte | PRC | médio |
| delpi-central | `engineering.manifest.json` | MANIFEST_CHANGES | só se o host exigir item de menu | Portal | baixo se a subrota não precisar |
| controle_mp | `app/api/middlewares/auth_middleware.py` | SECURITY_CHANGES | delegação §6.4 | owner Controle MP | fora da EVA; é outro repositório |
| controle_mp | `app/api/schemas/request_schema.py` + `get_request` | SECURITY_CHANGES aditivas | `conversation_id`, solicitante, `allowed_actions` | owner Controle MP | baixo |
| controle_mp | item `version` | MIGRATIONS | só se OCC for exigido | owner Controle MP | médio |
| delpi-central | `docs/.../engineering/ROADMAP.md` | DOCUMENTATION | link | esta task | baixo; não estava sujo |
| delpi-central | este arquivo | DOCUMENTATION | inventário | esta task | baixo |

### FORBIDDEN_FILES para a frente PRC

Não editar, nem formatar:

- `engineering-api/engineering_app/application/drawing/` (`understanding.py`, `perception_contract.py`, comparadores, contratos, jobs)
- `engineering-api/engineering_app/domain/drawing/`
- `engineering-api/engineering_app/infrastructure/extraction/` (`paddleocr_adapter.py` e vizinhos)
- `engineering-api/engineering_app/composition/drawing_composer.py`
- `engineering-api/engineering_app/interface/mcp/semantic_bridge.py` enquanto a outra frente o tiver sujo
- testes `test_drawing_*.py`, `test_table_perception_native.py`, `test_ocr_isolation_r71.py`, `test_visual_perception_r7.py`, `test_analysis_jobs.py`, `test_bom_structure_comparator*.py`
- `infra/scripts/keycloak-dev-bootstrap.sh` e `up-dev-sequential.sh` (sujos na leitura; não são desta task)

`product_routes.py` e o feature `plugins/engineering/src/features/products/` ficam fora: são a ferramenta Produtos/desenho, com marcadores de merge abertos.

---

## 19. Estratégia de trabalho paralelo

Estado observado em 2026-11-06: a frente de percepção documental está com diff não commitado no checkout principal de `delpi-central` (arquivos da seção 2.2). O destino deste inventário não estava nesse diff.

Esta task **não** criou worktree nem branch. `AGENTS.md` regra 10 pede autorização explícita para isso, e o arquivo de destino não estava em conflito. O commit documental entra em `main` com `git add` só dos dois arquivos de docs. Os arquivos da outra frente permanecem unstaged.

Para o código futuro (PRC-1 em diante), o checkout principal continua inadequado enquanto o diff da EVA existir:

1. Autorização explícita do usuário para uma worktree e uma branch só de PRC (a regra 10 não permite criá-las em silêncio).
2. Base = `origin/main` no momento dessa autorização, não um SHA com commit alheio não revisado.
3. Commits só dos paths da seção 18 marcados NEW_FILES e, no fim, um commit curto e serializado para os SHARED_FILES (`engineeringRoutes.ts`, `App.tsx`, catálogo, `HelpPage.tsx`, `main.py`, `config.py`).
4. Quem integrar os SHARED_FILES reexecuta os testes da `engineering-api` e do plugin no SHA já reunido, incluindo a suíte de desenho que a outra frente possuir.
5. Merge fast-forward em `main`. Sem rebase publicado por cima de commit da EVA, sem force push.
6. Deploy continua proibido até um owner de operação autorizar um SHA único, com rollback da versão anterior. Esta task não despliega.

---

## 20. Requisitos RQ-PRC e critérios AC-PRC

Os IDs são os do adendo. O estado abaixo é o que o código sustenta hoje.

| ID | Requisito | Estado após o inventário |
|---|---|---|
| RQ-PRC-01 | Área no Portal Engenharia | Path compatível com o host; o router do plugin ainda devolve `not_found`. Implementação não começou |
| RQ-PRC-02 | Leitura das solicitações legadas via BFF | Endpoints de leitura existem. Delegação bloqueia |
| RQ-PRC-03 | UI neutra por tipo | DTO com `type.code`; único caso com campos reais é matéria-prima |
| RQ-PRC-04 | Não duplicar owner | Fonte e transições permanecem no Flask. `allowed_actions` deve nascer lá |
| RQ-PRC-05 | Decisões governadas | Regras da seção 8 estão provadas. Escrita do BFF espera delegação e aceite de concorrência |
| RQ-PRC-06 | Coexistência e cutover | Matriz da seção 13. Sem dual-write |
| RQ-PRC-07 | Isolamento paralelo | Seção 19. Diff da EVA preservado |

| ID | Critério | Como provar quando implementar |
|---|---|---|
| AC-PRC-01 | Sem permissão → 403 no backend | teste da rota sem `engineering.access` e, com a delegação, role local insuficiente |
| AC-PRC-02 | Analista vê o escopo autorizado e o detalhe bate com a fonte | o escopo real do staff é a fila inteira, não “os seus”. O teste trava esse comportamento |
| AC-PRC-03 | UI não chama Flask, TOTVS nem api-delpi | teste de arquitetura / ausência de URL no bundle do plugin |
| AC-PRC-04 | Filtros, página, erro, deep link | teste de componente + rota `requests/{id}/items/{itemId}` |
| AC-PRC-05 | Leitura inicial sem write | fase de leitura não registra as rotas POST/PATCH |
| AC-PRC-06 | Ids e provenance | `source` + `sourceIds` no DTO |
| AC-PRC-07 | Ação sem delegação fail-closed | enquanto a seção 6.4 não existir, as rotas de ação nem são montadas |
| AC-PRC-08 | Testes no mesmo SHA | pytest do BFF + teste do router do plugin |
| AC-PRC-09 | Sem regressão EVA | não tocar os FORBIDDEN_FILES; suíte de desenho no SHA integrado |
| AC-PRC-10 | Rollback e aceite do owner | fora desta task; depende de deploy autorizado e do owner funcional |

---

## 21. Testes necessários

Já existem e foram considerados evidência, não suíte HTTP:

- `api-cadastro-mp/tests/test_request_field_edit_permissions.py`
- `api-cadastro-mp/tests/test_sso_central_subject.py`
- `api-cadastro-mp/tests/test_central_subject_binding.py`
- `api-cadastro-mp/tests/test_central_subject_sync.py`
- `api-cadastro-mp/tests/test_delpi_notification_client.py`
- `front-cadastro-mp/src/app/ui/requests/requestItemFieldPersistence.test.js`

Ausentes e necessários na implementação, não agora:

- Controle MP: `require_auth` aceita JWT central de usuário já vinculado; recusa `sub` desconhecido; não cria usuário; não emite refresh. Mais `conversation_id` no GET da request, se essa extensão for feita.
- `engineering-api`: 401 sem Bearer; 403 sem `engineering.access`; 403 quando a fonte recusa; mapeamento 409 de finalização; timeout vira 504; listagem sempre manda `limit` e `offset`; DTO não contém segredo nem refresh; principal de serviço rejeitado.
- Plugin: `product-registration` deixa de ser `not_found`; F5 no detalhe; estado vazio e forbidden.
- Não há teste de rota Flask hoje. Não dá para tratar `docs/API_REFERENCE.md` como prova de registro; a prova é `register_routes`.

---

## 22. Riscos, decisões e dependências externas

| Bloqueio | Por que é externo | Procedimento | Owner | Impacto | Desbloqueio |
|---|---|---|---|---|---|
| Audience/issuer do JWT de runtime | `KEYCLOAK_AUDIENCE` da engineering-api não tem default; `CENTRAL_JWT_AUDIENCE` default é `delpi-central`; os valores deployados não estão neste workspace | No ambiente alvo, comparar `KEYCLOAK_ISSUER` + `KEYCLOAK_AUDIENCE` do serviço `engineering-api` com `CENTRAL_JWT_ISSUER` + `CENTRAL_JWT_AUDIENCE` + `CENTRAL_JWKS_URL` do Controle MP. Um access token real do Portal precisa passar em `CentralJwtValidator` | identidade da plataforma + owner do Controle MP | escolhe entre estender `require_auth` ou criar exchange | os dois pares coincidem, ou o exchange é aceito por escrito |
| Papel ANALYST do usuário do Portal | SSO cria role 3 e não lê groups do Keycloak | Listar, no admin do Controle MP, os analistas que já têm `central_subject` e `role_id=2` | admin do Controle MP | analista com role 3 não muda status mesmo depois da delegação | contas promovidas antes do piloto |
| Owner funcional | citado no adendo como TÉO PROC-0078, não reaberto aqui | Aceite escrito da fila global (staff vê tudo) e do fato de que quem finaliza é o analista na API legada | Engenharia / PO | PRC-3 não começa sem isso | aceite registrado |
| Concorrência | não está no código | Decidir last-write-wins documentado ou coluna `version` | PO + owner da API | writes | decisão registrada |
| `FRACASSADO` | id 4 no seed, inalcançável pela rota oficial, texto de notificação diferente | Decidir se o Portal omite o status como ação (recomendado: omitir, porque a rota recusa) | PO | rótulo e filtro | filtro pode exibir itens já gravados nesse status; sem botão |
| API Controle MP alcançável pela engineering-api | URL interna não existe em `config.py` | Definir env de base URL na rede dos serviços, timeout, e proibir exposição no browser | operação | o gateway não tem alvo | env no compose, sem secret no front |

Riscos de código já provados, para o owner do Controle MP corrigir no próprio serviço (o BFF não os reproduz):

- `GET /api/users` sem autenticação.
- `PUT` e `DELETE /api/users/<id>` sem vínculo com o ator.
- `GET /count` inclui itens apagados.
- `fields_count` fixo em 0.
- Delete de request/item ignora o lock de finalizado.
- `PATCH` de item pelo criador pode gravar status 3 sem TOTVS.
- Rotas `/test/*` sempre registradas e ecoam claims.
- Socket aceita token sem checar revogação.
- Emit de socket antes do commit.

---

## 23. Sequência executável da implementação

1. **PRC-1a — decisão de identidade.** Executar o procedimento de audience da seção 22. Implementar a seção 6.4 no Controle MP, com testes, sem auto-create. Publicar essa API antes do BFF.
2. **PRC-1b — contrato de leitura.** Fechar os DTOs `list` e `get` da seção 15. Incluir `conversation_id` no GET da request se o deep link precisar da thread sem depender da fila.
3. **PRC-2 — BFF read-only + página.** Novos arquivos da seção 18, mais o toque serializado em router, `App.tsx`, catálogo, ajuda, `main.py` e `config.py`. Sem rotas POST/PATCH. Link para o legado nas ações que ainda só existem lá.
4. **PRC-3 — ações.** Só com delegação em produção, analistas já role 2, e decisão de concorrência. Ordem: `novo_codigo`, iniciar, devolver, rejeitar, finalizar. Read-back obrigatório. `allowed_actions` calculado na fonte antes dos botões.
5. **PRC-4.** Outro tipo de cadastro só com owner, campos e RQ próprios.
6. **PRC-5.** Cutover para `requests-api` é outro projeto. O stub V007 não é o destino.

Não começar pelo UI enquanto PRC-1a não tiver SHA no Controle MP. Um BFF que só devolve 401 da fonte não cumpre AC-PRC-02.

---

## 24. Evidências e referências de código

Controle MP em `c96060f90be5c131fc17f21312dd3a33781b0cd2`:

- Registro das rotas: [api/routes/__init__.py](https://github.com/roberiooliveiradev/controle_mp/blob/c96060f90be5c131fc17f21312dd3a33781b0cd2/api-cadastro-mp/app/api/routes/__init__.py)
- AuthN: [auth_middleware.py](https://github.com/roberiooliveiradev/controle_mp/blob/c96060f90be5c131fc17f21312dd3a33781b0cd2/api-cadastro-mp/app/api/middlewares/auth_middleware.py)
- SSO: [auth_routes.py](https://github.com/roberiooliveiradev/controle_mp/blob/c96060f90be5c131fc17f21312dd3a33781b0cd2/api-cadastro-mp/app/api/routes/auth_routes.py), [central_jwt_validator.py](https://github.com/roberiooliveiradev/controle_mp/blob/c96060f90be5c131fc17f21312dd3a33781b0cd2/api-cadastro-mp/app/infrastructure/security/central_jwt_validator.py)
- Workflow: [request_service.py](https://github.com/roberiooliveiradev/controle_mp/blob/c96060f90be5c131fc17f21312dd3a33781b0cd2/api-cadastro-mp/app/services/request_service.py) (`change_item_status` L487, permissão de campo L342, finalização L396)
- Produto: [product_service.py](https://github.com/roberiooliveiradev/controle_mp/blob/c96060f90be5c131fc17f21312dd3a33781b0cd2/api-cadastro-mp/app/services/product_service.py) L114–192
- TOTVS: [totvs_product_repository.py](https://github.com/roberiooliveiradev/controle_mp/blob/c96060f90be5c131fc17f21312dd3a33781b0cd2/api-cadastro-mp/app/repositories/totvs_product_repository.py)
- Fila: [request_item_repository.py](https://github.com/roberiooliveiradev/controle_mp/blob/c96060f90be5c131fc17f21312dd3a33781b0cd2/api-cadastro-mp/app/repositories/request_item_repository.py) L91 e L239
- Campos de UI: [productFields.js](https://github.com/roberiooliveiradev/controle_mp/blob/c96060f90be5c131fc17f21312dd3a33781b0cd2/front-cadastro-mp/src/app/constants/productFields.js), [requestItemFields.logic.js](https://github.com/roberiooliveiradev/controle_mp/blob/c96060f90be5c131fc17f21312dd3a33781b0cd2/front-cadastro-mp/src/app/ui/requests/requestItemFields.logic.js)
- Router legado: [AppRouter.jsx](https://github.com/roberiooliveiradev/controle_mp/blob/c96060f90be5c131fc17f21312dd3a33781b0cd2/front-cadastro-mp/src/app/routes/AppRouter.jsx)

delpi-central em `2cbd3e308d70f33a894b1e48d2b0d18214603b7b`:

- Delegação de saída: [downstream_client.py](https://github.com/roberiooliveiradev/delpi-central/blob/2cbd3e308d70f33a894b1e48d2b0d18214603b7b/engineering-api/engineering_app/infrastructure/gateways/downstream_client.py)
- Root path: [config.py](https://github.com/roberiooliveiradev/delpi-central/blob/2cbd3e308d70f33a894b1e48d2b0d18214603b7b/engineering-api/engineering_app/config.py)
- Router do MFE: [engineeringRoutes.ts](https://github.com/roberiooliveiradev/delpi-central/blob/2cbd3e308d70f33a894b1e48d2b0d18214603b7b/plugins/engineering/src/app/engineeringRoutes.ts)
- Stub: `requests-api/migrations/V007__seed_raw_material_creation_request_type.sql` e `requests_app/content/pt-BR/workflows/raw_material_creation.json`
- Plano: [ROADMAP.md](./ROADMAP.md) adendo, [EVOLUCAO.md](../controle-mp/EVOLUCAO.md) §10

---

## 25. Veredicto de prontidão

| Pergunta | Veredicto |
|---|---|
| Inventário das 51 rotas, workflow, campos, auth, front, engineering-api, portal, requests-api e TOTVS | **Completo** sobre o código dos dois SHAs. Nada ficou como `TO_INVENTORY` |
| BFF de leitura pode ser codado hoje | **Não.** Falta a delegação da seção 6.4 e a conferência de audience |
| BFF de decisão pode ser codado hoje | **Não.** Além da delegação, falta aceite de concorrência e `allowed_actions` na fonte se os botões forem ligados |
| requests-api pode substituir a fonte | **Não.** Stub de três campos, sem devolução, sem código, sem fornecedor |
| EVA / VAL-01 foi alterada | **Não** |
| Deploy | **Não executado** |
| Próximo passo bounded | PRC-1a: provar audience/issuer no ambiente e implementar, no Controle MP, a aceitação do JWT central só para usuário já vinculado |

`INVENTORY_COMPLETENESS = COMPLETE`  
`AUTHZ_DELEGATION_STATUS = BLOCKED_BY_SECURITY`  
`CODE_CHANGES = NONE` (somente este documento e o link no plano mestre)  
`ARCHITECTURE_DECISION_REQUIRED = identity delegation contract; global analyst queue; optimistic concurrency vs last-write-wins; FRACASSADO; functional owner sign-off`

### Auditoria de cobertura

- Blueprints em `register_routes`: 10, todos enumerados.
- Decorators HTTP em `app/api/routes`: 51, todos na matriz.
- Services das rotas de solicitação, produto, auth, mensagem, conversa, arquivo, audit e usuário: lidos até a regra citada.
- Schemas de request, user, product, message: regras de entrada citadas onde mudam o contrato.
- Status e transições de `change_item_status` e `resubmit_returned_item`: tabela da seção 8.
- Campos do composer e da finalização: seção 9, com UI separada da API.
- Endpoints externos: Protheus (SQL), Core notificações, Core diretório, JWKS. api-delpi citada só como vizinha já integrada.
- Permissões: `role_id` 1/2/3 e `engineering.access`.
- Contratos BFF: cada um aponta endpoint de origem existente ou a ausência provada.
- Front: rotas, clientes e jornadas das três personas.
- Diferenças doc×código: seção 5.4.
- Arquivos futuros: seção 18, com FORBIDDEN explícito.


## D16 — Legado de flags como referência, sem dependência runtime

O inventário deste documento registra `field_flag` e operações legadas `PATCH /api/requests/fields/<id>/flag` e `PATCH /api/products/fields/<id>/flag`, além de flags de conversa. Para o Portal Engenharia, o PO aprovou uma **nova bandeira textual de acompanhamento do atendimento**, **não** uma cópia de `field_flag` booleano nem a adoção de auth/socket/DB do legado. Ownership: Engineering API; consumidores Portal e EVA. Ver [plano D16](./PRODUCT-REGISTRATION-D16-ATTENDANCE-FLAGS-CRUD-EVA-UX-PLAN.md) para contratos, UI, auditoria e aceites. Esta inclusão não autoriza integração runtime com o Controle MP legado.
