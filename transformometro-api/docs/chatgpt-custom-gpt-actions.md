# Transformômetro — Custom GPT (OpenAI Actions)

Superfície compacta para o **ChatGPT Custom GPT** analisar, cadastrar e editar o Transformômetro sem expor as ~150 rotas internas (limite ~30 operations por schema da OpenAI).

## Arquivos

| Artefato | Caminho |
|----------|---------|
| OpenAPI para importar no GPT Builder | [`docs/openapi-gpt-actions.json`](./openapi-gpt-actions.json) |
| Endpoint público do schema | `GET /apps/transformometro-api/transformometro/gpt-actions/v1/openapi.json` |
| Builder canônico | `tm_app/application/gpt_actions/openapi_builder.py` |
| Dispatcher | `tm_app/application/gpt_actions/dispatch_service.py` |
| Rotas | `tm_app/interface/http/routes/gpt_actions_routes.py` |

Regenerar o JSON versionado:

```bash
cd transformometro-api
PYTHONPATH=.:../shared python scripts/sync_gpt_actions_openapi.py
```

## Operations (11 no schema importado)

| operationId | Método / path |
|-------------|----------------|
| `gpt_get_catalog` | `GET .../catalog` |
| `gpt_analyze` | `GET .../analysis?view=meta\|summary\|processes\|instances\|rows` |
| `gpt_search_records` | `GET .../records/{entity}` |
| `gpt_get_record` | `GET .../records/{entity}/{id}` |
| `gpt_create_record` | `POST .../records/{entity}` |
| `gpt_update_record` | `PUT .../records/{entity}/{id}` |
| `gpt_delete_record` | `DELETE .../records/{entity}/{id}` |
| `gpt_duplicate_record` | `POST .../records/{entity}/{id}/duplicate` |
| `gpt_activate_revision` | `POST .../revisions/{id}/activate` |
| `gpt_recalculate_dashboard` | `POST .../dashboard/recalculate` |
| `gpt_meeting_minute_workflow` | `POST .../meeting-minutes/{id}/workflow` |

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

Checklist operacional com valores para colar: [`chatgpt-gpt-builder-go-live.md`](./chatgpt-gpt-builder-go-live.md).

1. Create GPT → Actions → Import from URL  
   `https://<host>/apps/transformometro-api/transformometro/gpt-actions/v1/openapi.json`  
   ou cole o conteúdo de `docs/openapi-gpt-actions.json`.
2. Authentication → OAuth (valores da tabela acima).
3. Instructions (resumo):

```text
Você é o assistente do Transformômetro DELPI.
Antes de cadastrar, chame gpt_get_catalog.
Para KPIs use gpt_analyze (view=summary|processes|instances|rows).
Cadastro segue: unidade/departamento → processo → melhoria (instance) → revisão → medição/investimento.
Confirme writes destrutivos (delete, activate, cancel ata) com o usuário.
Não invente UUIDs: busque com gpt_search_records / gpt_get_record.
Assinatura manuscrita de atas e uploads binários ficam na UI Minha DELPI.
```

## Fora desta superfície

- Locks de colaboração / realtime
- Backup JSON / export CSV binário
- Uploads (arquivos, evidências, PNG de assinatura, PDF)
- Assinatura pública magic-link
- Integrações S2S engineering

## Relação com o Chat da Minha DELPI

O agente interno continua no schema **somente leitura** [`openapi-snapshot-chat.json`](./openapi-snapshot-chat.json) com `allowWrite: false`.  
Esta superfície GPT **não** altera esse provider.

## Sync pós-mudança

```bash
PYTHONPATH=.:../shared python scripts/sync_gpt_actions_openapi.py
PYTHONPATH=.:../shared python scripts/sync_openapi_baseline.py --write
PYTHONPATH=.:../shared python scripts/audit_route_test_coverage.py --write
```
