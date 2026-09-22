# GPT Builder — checklist go-live (VISTA · TV Dashboard)

> **Persona:** **VISTA — Especialista em Painéis Operacionais DELPI**  
> VISTA = Visualização · Inteligência · Síntese · Telas · Apresentação  
> **Lifecycle:** `TEMPORARY GPT ACTIONS BRIDGE` — OpenAI is retiring Custom GPTs.  
> Durable target remains **Plugin + custom remote MCP** (TV-GPI-004B5 parked; no Keycloak upgrade / resource-indicators required for this bridge).  
> Padrão transversal: [padrao-custom-gpt-actions-oauth.md](../../../docs/11-padroes-de-desenvolvimento/padrao-custom-gpt-actions-oauth.md)

Client secret: Keycloak → Credentials → **somente** GPT Editor. **Nunca** Git, chat, logs ou Markdown.

## Identidade do GPT (manual no Builder)

| Campo (GPT Builder) | Valor |
|---------------------|--------|
| **Name** | `VISTA — Especialista em Painéis Operacionais DELPI` |
| **Description** | Compreenda dados operacionais, escolha visualizações adequadas, projete painéis para TVs e aplique mudanças governadas na TV Dashboard. |
| **Tagline** | Dados claros. Telas que orientam. |
| **Acrônimo** | VISTA = Visualização · Inteligência · Síntese · Telas · Apresentação |

Conversation starters sugeridos:

```text
Me ajude a interpretar um indicador na TV
Quero montar um painel operacional para o chão de fábrica
Quero ajustar um slide da playlist sem quebrar a revisão
Quais rotas de dados posso usar no meu painel?
```

## Knowledge + Instructions

1. Colar **somente** o bloco `Instructions (colar no GPT Builder)` de [`specialist-instructions.md`](./specialist-instructions.md) — núcleo **estável** (raramente muda).
2. Inteligência mutável (anti-duplicidade, print/paridade, modos, write heuristics) sobe no deploy via `gpt_get_catalog` → `capability_surface.agent_directives` (`vista_agent_intelligence.json`). **Não** colar isso em Instructions. **Não** enumerar seções novas do JSON no bloco estável.
3. Adicionar [`vista-display-playbooks.md`](./vista-display-playbooks.md) como Knowledge File (visualização; não substitui agent_directives).
4. Após editar Instructions (raro) **ou** o JSON de inteligência, rodar: `pytest tests/test_vista_builder_instructions_budget.py tests/test_vista_agent_intelligence.py -q`
5. **Anti-padrão:** “feature nova → expandir Instructions”. Correto: “feature nova → `vista_agent_intelligence.json` + deploy”.

## Pré-requisitos HTTP (já verificáveis)

| Item | Valor |
|------|--------|
| OpenAPI público | `https://minhadelpi.com.br/apps/tv-dashboard-api/gpt-actions/v1/openapi.json` |
| Esperado | OpenAPI **3.1.x**, `servers.url` absoluto HTTPS, **8** operationIds, lifecycle **GOVERNED_PREPARE_COMMIT_V2** |
| Descriptions | cada `operation.description` **≤ 300** chars (limite GPT Builder) |
| Anônimo protegido | `GET …/catalog` → **401** |

OperationIds importados (somente estes):

```text
gpt_get_catalog
gpt_list_playlists
gpt_get_playlist_context
gpt_search_data_routes
gpt_preview_data_block
gpt_suggest_change
gpt_preview_change
gpt_commit_change
```

## 1. Keycloak — client `chatgpt-tv-dashboard`

Realm: `delpi`. Classification: `TEMPORARY_BRIDGE_CLIENT`.

**Não** reutilizar: `delpi-central`, `chatgpt-transformometro`, `mcp-tv-dashboard`.

| Campo | Valor |
|-------|--------|
| Client ID | `chatgpt-tv-dashboard` |
| Client authentication | **On** |
| Standard flow | **On** |
| Direct access grants | **Off** |
| Service accounts | **Off** (salvo política explícita existente) |
| Default scopes | `openid`, `email`, `profile`, `audience-delpi` |
| Audience | `aud` inclui `delpi-central` (mapper do scope `audience-delpi`) |
| Web origins | `https://chatgpt.com`, `https://chat.openai.com` |

### Redirect URI (obrigatório: URL do editor)

1. Criar/abrir o Custom GPT da VISTA no GPT Builder.
2. Actions → Authentication → **OAuth**.
3. Copiar o **callback URL exato** mostrado pelo editor.
4. Colar **somente esse callback** em Valid redirect URIs no Keycloak.

Se precisar bootstrap temporário até existir `g-…`:

```text
https://chatgpt.com/*
https://chat.openai.com/*
```

Ambiente controlado apenas → **remover** assim que o callback exato estiver configurado.

Prova sem secret (esperado **200** + tela de login após o client existir):

```bash
curl -sS -o /dev/null -w '%{http_code}\n' -G \
  'https://minhadelpi.com.br/auth/realms/delpi/protocol/openid-connect/auth' \
  --data-urlencode 'client_id=chatgpt-tv-dashboard' \
  --data-urlencode 'redirect_uri=https://chatgpt.com/aip/g-PLACEHOLDER/oauth/callback' \
  --data-urlencode 'response_type=code' \
  --data-urlencode 'scope=openid email profile'
```

`400` com o mesmo footprint de client inexistente ⇒ client ainda não provisionado.

## 2. GPT Builder — OAuth

| Campo | Valor |
|-------|--------|
| Client ID | `chatgpt-tv-dashboard` |
| Client secret | Keycloak Credentials (não versionar) |
| Authorization URL | `https://minhadelpi.com.br/auth/realms/delpi/protocol/openid-connect/auth` |
| Token URL | `https://minhadelpi.com.br/auth/realms/delpi/protocol/openid-connect/token` |
| Scope | `openid email profile` |
| Token exchange | Preferir **Cabeçalho de autorização básica** |

Import schema **somente** da URL pública (não colar schema local obsoleto):

```text
https://minhadelpi.com.br/apps/tv-dashboard-api/gpt-actions/v1/openapi.json
```

Confirmar: editor reconhece **exatamente 8** Actions.

### Image Generation (operador)

Image generation **não** faz parte da missão central da TV Dashboard / VISTA.

Se o GPT Builder expuser a capability **Image Generation**:

```text
recomendado: OFF
```

salvo caso de uso VISTA **aprovado à parte**. Motivo: pedidos como
“crie um slide com fundo verde” não devem competir com roteamento de imagem.

Estado atual do toggle no Builder = `TO_INVENTORY` — **não** afirmar que já
está OFF sem evidência do editor. Se a capability não puder ser desligada,
as Instructions **devem** manter a precedência TV-domínio > imagem
(`specialist-instructions.md` § Intenção de domínio).

Após qualquer mudança de schema canônico / OpenAPI: **reimportar** esta URL,
salvar o GPT e abrir conversa **nova**. Nested ops (`patch`, `items`, `steps`,
`block`, `params`, `fieldLabels`) vêm do catálogo PresentationOps — não de um catálogo
paralelo no Builder.

## 3. Smoke (usuários DELPI legítimos)

AuthN = Keycloak; AuthZ plataforma = Core; AuthZ recurso = TV. Conta OpenAI **não** é autoridade.

| Camada | Prova |
|--------|--------|
| RBAC | sem permissão → 403; `tv-dashboard.read` → reads; `tv-dashboard.write` → PREPARE/ACT conforme contrato |
| READ | catalog, playlists, context, data-routes |
| PREPARE | data-preview / suggest / preview → `persisted=false` + `proposal_handle` (salvo se só PREPARE) |
| ACT additive | `gpt_preview_change` com `commit_now=true` + `confirmation` + Idempotency-Key (header ou body) → `VERIFIED` em 1 Action |
| ACT destructive | preview → confirmação conversacional → `gpt_commit_change` com handle **exato** (nunca `latest`) |
| Idempotency | mesmo key+payload → replay; key+payload diferente → 409 `IDEMPOTENCY_CONFLICT` |
| OCC / proposal | revision stale → 409 `PROPOSAL_CHANGED`; expired → `PROPOSAL_EXPIRED`; alias inventado → `PROPOSAL_NOT_FOUND` |
| Destructive | confirmação explícita obrigatória; `commit_now` ignorado quando `confirmationPolicy=confirm` |

## 4. Fora de escopo deste bridge

```text
Keycloak upgrade / resource-indicators / MCP
segundo issuer / segundo RBAC / segundo writer
CRUD genérico / SQL genérico
novas Actions sem gap arquitetural comprovado
```
