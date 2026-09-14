# Transformômetro — Custom GPT (OpenAI Actions) · persona TÉO

> **Padrão transversal:** [padrao-custom-gpt-actions-oauth.md](../../../docs/11-padroes-de-desenvolvimento/padrao-custom-gpt-actions-oauth.md)  
> Este arquivo é a **instância** Transformômetro (paths, client, operations). Para Action Plans e outros produtos, seguir o padrão geral e espelhar esta estrutura.  
> **Persona user-facing:** [TÉO — Especialista em Transformação Digital](./specialist-instructions.md) (produto = Transformômetro; TÉO ≠ novo serviço/bounded context).

Superfície compacta para o **ChatGPT Custom GPT** (TÉO) analisar, cadastrar e editar o Transformômetro sem expor as ~150 rotas internas (limite ~30 operations por schema da OpenAI).

## Arquivos

| Artefato | Caminho |
|----------|---------|
| OpenAPI para importar no GPT Builder | [`openapi-gpt-actions.json`](./openapi-gpt-actions.json) |
| Endpoint público do schema | `GET /apps/transformometro-api/transformometro/gpt-actions/v1/openapi.json` |
| Builder canônico | `tm_app/application/gpt_actions/openapi_builder.py` |
| Dispatcher | `tm_app/application/gpt_actions/dispatch_service.py` |
| Guia de cadastro (catalog) | `tm_app/application/gpt_actions/registration_guide.py` |
| Pacote guiado | `tm_app/application/gpt_actions/improvement_package_service.py` |
| Contexto de inteligência (read-only) | `tm_app/application/gpt_actions/process_context_service.py` |
| Instructions do especialista | [`specialist-instructions.md`](./specialist-instructions.md) (persona **TÉO**) |
| Rotas | `tm_app/interface/http/routes/gpt_actions_routes.py` |

Regenerar o JSON versionado:

```bash
cd transformometro-api
PYTHONPATH=.:../shared python scripts/sync_gpt_actions_openapi.py
```

## Operations (13 no schema importado)

| operationId | Método / path |
|-------------|----------------|
| `gpt_get_catalog` | `GET .../catalog` (inclui `registration_guide` + enums `fase_melhoria` / `prioridade_melhoria`) |
| `gpt_get_process_context` | `GET .../process-context?process_id=&instance_id=&revision_id=` (projeção efêmera read-only) |
| `gpt_analyze` | `GET .../analysis?view=meta\|summary\|processes\|instances\|rows` |
| `gpt_search_records` | `GET .../records/{entity}` (`instance_id` para revisões de uma melhoria) |
| `gpt_get_record` | `GET .../records/{entity}/{id}` |
| `gpt_create_record` | `POST .../records/{entity}` |
| `gpt_update_record` | `PUT .../records/{entity}/{id}` |
| `gpt_delete_record` | `DELETE .../records/{entity}/{id}` |
| `gpt_duplicate_record` | `POST .../records/{entity}/{id}/duplicate` |
| `gpt_activate_revision` | `POST .../revisions/{id}/activate` |
| `gpt_recalculate_dashboard` | `POST .../dashboard/recalculate` |
| `gpt_meeting_minute_workflow` | `POST .../meeting-minutes/{id}/workflow` |
| `gpt_commit_improvement_package` | `POST .../improvement-packages` (`dry_run` → commit orquestrado) |

`gpt_get_process_context` monta o Process Business Graph / Process Intelligence Context a partir dos records e services canônicos. Sem persistência de grafo. Comparativo/composição/stats ficam restritos ao escopo de filial visível. Distinga `as_is` (AS_IS), `current_composed` (CURRENT_COMPOSED) e `to_be` (TO_BE). `surface_supports` ≠ autorização de write. Na facade GPT, `setor_id` aceita UUID **ou** `codigo_setor` (ex. `comercial`); `gpt_analyze(view=instances)` honra `processo_id`. Diagramas/WBS: rascunho Mermaid na conversa; persistência validada via GPT ainda não — use a UI.

`GET .../openapi.json` continua público só para o botão **Importar de URL**. Não entra no schema: o GPT Builder trata esse path como OpenAPI 3.1 e rejeita o documento.

`entity` enum: `branch`, `department`, `process`, `instance`, `revision`, `measurement`, `investment`, `shared_resource`, `resource_cost`, `resource_link`, `meeting_minute`, `decomposition_tree`, `instance_decomposition_scope`, `revision_decomposition_overlay`, `process_diagram`, `instance_diagram_scope`, `revision_diagram_overlay`, `impact_effort_matrix`.

Bodies de write usam `{ "data": { ... } }` com os mesmos campos do CRUD da UI.

## Auth (obrigatório)

- **Não** use API Key para writes.
- Custom GPT → Authentication → **OAuth**.
- Client Keycloak confidencial: `chatgpt-transformometro` (ver procedimento abaixo).
- ChatGPT envia `Authorization: Bearer <access_token>`.
- A API valida JWT (issuer/audience/JWKS) e RBAC via Core API — mesmas permissões da tela.

### Keycloak — client OAuth para o Custom GPT

1. Realm `delpi` (ou o de `KEYCLOAK_REALM`).
2. Clients → Create:
   - Client ID: `chatgpt-transformometro`
   - Client authentication: **On** (confidential)
   - Standard flow: **On**
   - Direct access grants: **Off**
3. Valid redirect URIs (após salvar o GPT e copiar o `g-...` da URL):
   - `https://chatgpt.com/aip/g-YOUR-GPT-ID/oauth/callback`
   - `https://chat.openai.com/aip/g-YOUR-GPT-ID/oauth/callback`
4. Web origins: `https://chatgpt.com` e `https://chat.openai.com`
5. Client scopes: `openid`, `email`, `profile`
6. Audience mapper (igual ao Portal): claim `aud` deve incluir `delpi-central` (`KEYCLOAK_AUDIENCE`).
7. Copiar **Client secret** só para o GPT Editor — **nunca** versionar no Git.

URLs OAuth (substituir host público):

| Campo GPT | Valor |
|-----------|--------|
| Client ID | `chatgpt-transformometro` |
| Client secret | *(Keycloak → Credentials)* |
| Authorization URL | `https://<host>/auth/realms/delpi/protocol/openid-connect/auth` |
| Token URL | `https://<host>/auth/realms/delpi/protocol/openid-connect/token` |
| Scope | `openid email profile` |

## GPT Builder — Actions

Checklist operacional: [`gpt-builder-go-live.md`](./gpt-builder-go-live.md).

**Instructions completas do TÉO (colar no Builder):** [`specialist-instructions.md`](./specialist-instructions.md). Name do GPT no Builder: `TÉO — Especialista em Transformação Digital` (`MANUAL_CONFIGURATION_REQUIRED`).

1. Create GPT → Actions → Import from URL  
   `https://<host>/apps/transformometro-api/transformometro/gpt-actions/v1/openapi.json`  
   ou cole o conteúdo de `docs/gpt-actions/openapi-gpt-actions.json` (esperar **13** actions).
2. Authentication → OAuth (valores da tabela acima).
3. Colar o playbook de [`specialist-instructions.md`](./specialist-instructions.md).

Fluxo guiado preferido: `gpt_get_catalog` → entrevista → `gpt_commit_improvement_package` (`dry_run=true` → confirmar → commit).

## Fora desta superfície

- Locks de colaboração / realtime
- Backup JSON / export CSV binário
- Uploads (arquivos, evidências, PNG de assinatura, PDF)
- Assinatura pública magic-link
- Integrações S2S engineering

## Relação com o Chat da Minha DELPI

O agente interno continua no schema **somente leitura** [`../chat/openapi-snapshot-chat.json`](../chat/openapi-snapshot-chat.json) com `allowWrite: false`.  
Esta superfície GPT **não** altera esse provider.

## Sync pós-mudança

```bash
PYTHONPATH=.:../shared python scripts/sync_gpt_actions_openapi.py
PYTHONPATH=.:../shared python scripts/sync_openapi_baseline.py --write
PYTHONPATH=.:../shared python scripts/audit_route_test_coverage.py --write
```
