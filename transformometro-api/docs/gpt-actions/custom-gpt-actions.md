# Transformômetro — Custom GPT (OpenAI Actions) · persona TÉO

> **Lifecycle:** `GOVERNED_PREPARE_COMMIT_V2` — Builder-visible surface is prepare/commit.  
> **Legacy HTTP shims** (`gpt_create_record` / `gpt_update_record` / `gpt_delete_record` /
> `gpt_duplicate_record` / `gpt_commit_improvement_package`): **LEGACY_TRANSITIONAL**
> (`include_in_schema=False`) — not model guidance.  
> **Target Plugin/Agent:** MCP `CAPABILITY_GOVERNED_V2` (20 tools) — ver [`../integrations/openai-plugin-mcp.md`](../integrations/openai-plugin-mcp.md) (client `mcp-transformometro`).  
> **Padrão transversal:** [padrao-custom-gpt-actions-oauth.md](../../../docs/11-padroes-de-desenvolvimento/padrao-custom-gpt-actions-oauth.md)  
> Este arquivo é a **instância** Transformômetro (paths, client, operations). Para Action Plans e outros produtos, seguir o padrão geral e espelhar esta estrutura.  
> **Persona user-facing:** [TÉO — Especialista em Transformação Digital](./specialist-instructions.md) (produto = Transformômetro; TÉO ≠ novo serviço/bounded context).  
> **Capability matrix (canônica):** [`../integrations/teo-capability-matrix.md`](../integrations/teo-capability-matrix.md) — paridade Actions/MCP/DÉLIA + Action Surface Budget.

Superfície compacta para o **ChatGPT Custom GPT** (TÉO) analisar, cadastrar e editar o Transformômetro sem expor as ~150 rotas internas (budget ~30; atual **18** operations importáveis).

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
| Contexto pessoal (read-only) | `tm_app/application/gpt_actions/user_context_service.py` + `person_profile_reader_port.py` |
| Adapter Core PersonProfile | `tm_app/infrastructure/gateways/core_person_profile_gateway.py` (`GET /me/person-profile`, Bearer do usuário) |
| Instructions do especialista | [`specialist-instructions.md`](./specialist-instructions.md) (persona **TÉO**) |
| Method playbooks (Knowledge) | [`teo-method-playbooks.md`](./teo-method-playbooks.md) — editorial. Runtime: `query_methodology_guide`. Action: `gpt_get_methodology_guide`. Métodos não são entidades. Destino de negócio: [ciclo de inteligência](../../../docs/12-roadmap-e-evolucao/transformometro-app/CICLO-INTELIGENCIA-DE-PROCESSO.md). Experiência Portal Transforma+: [adendo](../../../docs/12-roadmap-e-evolucao/transformometro-app/PORTAL-TRANSFORMA-PLUS.md). Os dois são TARGET, sem Action por tela. |
| Rotas | `tm_app/interface/http/routes/gpt_actions_routes.py` |

Regenerar o JSON versionado:

```bash
cd transformometro-api
PYTHONPATH=.:../shared python scripts/sync_gpt_actions_openapi.py
```

## Operations (18 no schema importado — V2 prepare/commit)

| operationId | Método / path | Kind |
|-------------|----------------|------|
| `gpt_get_my_context` | `GET .../me` | READ / context (não AuthZ) |
| `gpt_get_catalog` | `GET .../catalog` | READ / discovery |
| `gpt_get_methodology_guide` | `GET .../methodology-guide` | READ / methodology |
| `gpt_get_process_context` | `GET .../process-context` | READ / composition |
| `gpt_analyze` | `GET .../analysis` | ANALYSIS |
| `gpt_search_records` | `GET .../records/{entity}` | ENTITY READ |
| `gpt_get_record` | `GET .../records/{entity}/{id}` | ENTITY READ |
| `gpt_prepare_record_change` | `POST .../records/prepare-change` | ENTITY PREPARE |
| `gpt_commit_proposal` | `POST .../proposals/commit` | COMMON COMMIT (ACT) |
| `gpt_activate_revision` | `POST .../revisions/{id}/activate` | WORKFLOW PREPARE |
| `gpt_recalculate_dashboard` | `POST .../dashboard/recalculate` | WORKFLOW PREPARE |
| `gpt_meeting_minute_workflow` | `POST .../meeting-minutes/{id}/workflow` | WORKFLOW PREPARE |
| `gpt_validate_improvement_package` | `POST .../improvement-packages/validate` | WORKFLOW PREPARE |
| `gpt_list_evidence` | `GET .../evidence` | READ |
| `gpt_manage_evidence` | `POST .../evidence/manage` | WORKFLOW PREPARE |
| `gpt_get_process_timeline` | `GET .../processes/{id}/timeline` | READ |
| `gpt_adjust_shared_resource_cost` | `POST .../shared-resources/adjust-cost` | WORKFLOW PREPARE |
| `gpt_meeting_minute_manage` | `POST .../meeting-minutes/manage` | WORKFLOW PREPARE |

### Legacy (NOT Builder-visible)

| Legacy | Replacement | Public? |
|---|---|---|
| `gpt_create_record` / `gpt_update_record` / `gpt_delete_record` / `gpt_duplicate_record` | `gpt_prepare_record_change` + `gpt_commit_proposal` | No |
| `gpt_commit_improvement_package` | `gpt_validate_improvement_package` + `gpt_commit_proposal` | No |

### Capacidade × superfície (TM-GPI-006)

| Capacidade | Classificação |
|---|---|
| Contexto pessoal (nome/e-mail/cargo) | **SUPPORTED_BY_TÉO** (`gpt_get_my_context`) — perfil ≠ autorização |
| Link/metadata de evidência (processo/revisão) | **SUPPORTED_BY_TÉO** (`gpt_list_evidence` / `gpt_manage_evidence` → `gpt_commit_proposal`) |
| Upload/download binário de evidência | **BLOCKED_BY_PLATFORM** / **SUPPORTED_BY_UI_ONLY** |
| Timeline de auditoria do processo | **SUPPORTED_BY_TÉO** (`gpt_get_process_timeline`) |
| Reajuste semântico de custo de recurso compartilhado | **SUPPORTED_BY_TÉO** (`gpt_adjust_shared_resource_cost` → commit) |
| Ata: send/finalize/cancel | **SUPPORTED_BY_TÉO** (`gpt_meeting_minute_workflow` → commit) |
| Ata: pending/audit/versions/participants/signers/resend/create_version/generate_from_transcript | **SUPPORTED_BY_TÉO** (`gpt_meeting_minute_manage` → commit) |
| Assinatura PNG / PDF / magic-link público | **NOT_EXPOSED_BY_DESIGN** / **SUPPORTED_BY_UI_ONLY** |
| Proxy HTTP genérico, locks, websocket, backup JSON, S2S | **NOT_EXPOSED_BY_DESIGN** |
| Tasks / Interaction Room | **DOMAIN_ONLY_BY_DESIGN** |

Proveniência: ata = registro formal; áudio/vídeo = evidência original quando governada; transcript = representação derivada; resumo TÉO = conteúdo derivado. Não converter derivado em evidência autoritativa.

`gpt_get_process_context` monta o Process Business Graph / Process Intelligence Context a partir dos records e services canônicos. Sem persistência de grafo. Comparativo/composição/stats ficam restritos ao escopo de filial visível. Distinga `as_is` (AS_IS), `current_composed` (CURRENT_COMPOSED) e `to_be` (TO_BE). `surface_supports` ≠ autorização de write. Na facade GPT, `setor_id` aceita UUID **ou** `codigo_setor` (ex. `comercial`); `gpt_analyze(view=instances)` honra `processo_id`.

**Governed user-parity (TM-GPI-002):** ENTITY writes usam `gpt_prepare_record_change` → `gpt_commit_proposal`. WORKFLOW writes usam specialized PREPARE → o mesmo `gpt_commit_proposal`. Diagramas/WBS usam `DiagramWriteService` / `DecompositionWriteService` (validators da UI). Mermaid é derivado no servidor. Confirmação conversacional ≠ AuthZ. Sucesso = verified + authoritative read-back. Draft Mermaid no chat = PROPOSED / NOT SAVED.

**Diagram catalog (TM-GPI-009):** TÉO **deve** descobrir tipos de nó/aresta de `flowchart_v1` em `gpt_get_catalog.diagram_catalog` (`build_bpmn_catalog_for_api()` — mesma fonte de `GET /diagrama/catalogo`). Não inferir tipos só de exemplos; exemplos não são exaustivos. Não inventar tipos fora do catálogo. Não restringir a `start`/`process`/`end` quando o catálogo lista `decision`, gateways, tasks, etc.

`GET .../openapi.json` continua público só para o botão **Importar de URL**. Não entra no schema: o GPT Builder trata esse path como OpenAPI 3.1 e rejeita o documento.

`entity` enum: inclui `process_document` e demais entidades CRUD do catalog. **Nova ENTITY CRUD ≠ nova Action** — usa prepare/commit genéricos.

Bodies ENTITY V2 usam `gpt_prepare_record_change` com `{ entity, operation, record_id?, changes: { ... } }` (campos canônicos da UI sob `changes`). Não empacotar em `conteudo`/`payload`/`attributes`/`metadata`, exceto entities de documento (diagram/decomposition) onde o contrato exige `changes.conteudo`.

Antes de qualquer gravação: `gpt_get_catalog` → `registration_guide.entity_schemas.<entity>` + `capability_surface`. Schema canônico da entidade prevalece. Após erro: não repetir; reler catálogo; read-back. Sucesso só com read-back autoritativo + verify.

Fluxo canônico:

```text
UNDERSTAND → READ CURRENT STATE → PREPARE EXACT CHANGE → VALIDATE
→ SHOW USER → EXPLICIT CONFIRMATION → COMMIT → AUTHORITATIVE READ-BACK
→ VERIFY → REPORT OUTCOME
```

Exemplos:

```json
{
  "entity": "shared_resource",
  "operation": "create",
  "changes": {
    "nome_recurso": "Embaixador Robério",
    "tipo_custo": "mao_obra",
    "recorrencia": "mensal",
    "escopo_recurso": "empresa",
    "status_recurso": "ativo"
  }
}
```

Errado (não fazer): colocar `nome_recurso` / `tipo_custo` / `recorrencia` dentro de `changes.conteudo` para `shared_resource`.

`resource_link` deve usar `revisao_id` e `recurso_compartilhado_id` obtidos por read-back, nunca IDs inventados.

### Erros para o Custom GPT

Envelope de falha: `{ "success": false, "message": "...", "data": { "error_kind": "...", "errors": [...], "error_count": N } }`.

| `error_kind` | Origem típica |
|---|---|
| `validation` | Pydantic / campos ausentes ou inválidos |
| `domain` | `GptActionsError` (negócio/not found/etc.) |
| `authn` / `authz` | JWT/RBAC (também normaliza `{detail}` legado) |
| `persistence` | falha de banco/repositório (HTTP 503) |
| `internal` | bug inesperado (HTTP 500; inclui `error_type`) |

O TÉO deve **sempre** ler `message`/`data` — nunca reportar só o código HTTP.

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
   ou cole o conteúdo de `docs/gpt-actions/openapi-gpt-actions.json` (esperar **18** actions importáveis — V2).
2. Authentication → OAuth (valores da tabela acima).
3. Colar o bloco Instructions de [`specialist-instructions.md`](./specialist-instructions.md) (**REPLACE INSTRUCTIONS**).
4. Adicionar [`teo-method-playbooks.md`](./teo-method-playbooks.md) como Knowledge do GPT (metodologia; não authority de dados).
5. OpenAPI: reimportar **somente** quando o schema mudar. Contrato importável = **18** operationIds (`GOVERNED_PREPARE_COMMIT_V2`). Inventários 20/21 = HISTORICAL.

Fluxo guiado preferido: `gpt_get_catalog` → `registration_guide.package_hints` → entrevista → `gpt_validate_improvement_package` (`ready=true`) → SHOW → EXPLICIT CONFIRMATION → `gpt_commit_proposal`.

### Envelope canônico do improvement package

```text
process + instance + baseline? + scenario?
  baseline → { revision, measurement? }
  scenario → { revision, measurement?, investments? }
```

- Reuso: `process.processo_id` / `instance.instancia_id`.
- Cenário: campos de revisão **somente** em `scenario.revision` (nunca flat em `scenario`).
- Validar com `gpt_validate_improvement_package` (PREPARE; nunca escreve).
- Commit via `gpt_commit_proposal` (opaque `proposal_handle`). `gpt_commit_improvement_package` = LEGACY_TRANSITIONAL off-schema.
- Pacote incompleto → proposal com `ready=false` / `act_allowed=false`, sem escrita.
- Não há dialeto flat→nested; um único contrato.
Method playbooks (SIPOC, Lean, Ishikawa, CTP, TDR, KPI, SWOT…) são reasoning/conversa via Instructions+Knowledge; **não** geram novas Actions.

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
