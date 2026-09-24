# DAVI — Workspace Agent / Agent Studio

> **Status documental em 2026-09-16 (`DAVI-AGENT-DYNAMIC-DISCOVERY-REBASELINE-001`).**
> Esta página registra a configuração e a evidência observadas no ChatGPT Agent Studio,
> mais o **contrato estável de Instructions** canônico no repositório.
> Configuração de provider não substitui prova de runtime, AuthZ ou publicação.
> Atualizar este arquivo **não** atualiza automaticamente o Agent Studio.

## Scope / authority

```text
This document owns CURRENT Workspace Agent / Agent Studio
configuration and observed evidence.

It is not the global DAVI product architecture.

General DAVI baseline:
docs/12-roadmap-e-evolucao/davi/README.md
```

API DELPI is the first major information source for Wave 1 — **not** the permanent only source for DAVI.

## Core decisions (frozen)

```text
AGENT_INSTRUCTIONS_CAPABILITY_ENUMERATION = NONE
DYNAMIC_CAPABILITY_DISCOVERY = CANONICAL
RAW_OPENAPI_TO_AGENT = FORBIDDEN
GOVERNED_DISCOVERY_BROKER = REQUIRED
BACKEND_AUTHZ = FINAL
AGENT_INSTRUCTIONS = STABLE_BEHAVIOR_ONLY
DAVI_LOCAL_AUTHZ = NONE
```

## Identidade

| Campo | Valor |
|---|---|
| Nome | **DAVI — Especialista em Dados e Informações DELPI** |
| Persona | masculina, profissional, cordial e objetiva |
| Missão | semantic discovery, authorized retrieval, composition e explanation de informações autorizadas da DELPI — usando capabilities realmente conectadas e governadas |
| Produto técnico consumido (V1) | DAVI / `api-delpi` Plugin/App + remote MCP |
| MCP tool surface (protocolo estável) | `search_products`, `discover_delpi_information`, `execute_delpi_information` |
| Inventário de capabilities de negócio | **dinâmico** via governed discovery (não enumerado nas Agent Instructions) |
| Estado | draft/preview no provider; Instructions canônicas no repo = **rebaselined**; **Agent Studio sync = PENDING** |
| Publicação ampla | **PENDING** |

A persona, o nome e a aparência são UX. Não alteram identity, OAuth, RBAC, AuthZ, capability ou autoridade de negócio.

Missão ampla ≠ elegibilidade de todas as rotas API DELPI. Elegibilidade, projection e quarantines pertencem ao broker + allowlist (runtime/governance). AuthZ canônico: capability ≤ usuário autenticado; `branch` é filtro; backend é autoridade final. Policy: `docs/integrations/evidence/davi-read-authz-policy-rebaseline-001.md`.

## Stable Agent Contract vs Dynamic Capability Inventory

```text
STABLE (Agent Instructions)
  persona / missão
  protocol Agent↔MCP tools
  discover → candidate → execute
  READ-only
  authority boundaries
  security / communication

DYNAMIC (governed runtime — NOT Agent Instructions)
  current eligible actions
  semantic aliases
  argument schemas
  approved response projections
  availability / quarantines
  write-intent semantic guard
```

Modelo permanente:

```text
USER NEED
  → AGENT (stable behavior)
  → GOVERNED DISCOVERY
  → CURRENT ELIGIBLE CAPABILITY
  → CANDIDATE TOKEN
  → GENERIC EXECUTION
  → CANONICAL BACKEND AUTHZ
  → AUTHORITATIVE DATA
  → FAIL-CLOSED PROJECTION
  → AGENT RESPONSE
```

Portanto:

```text
Agent Instructions = stable behavior
Capability inventory = runtime
Capability eligibility = governance
Business authorization = backend
Operational truth = canonical source
Raw OpenAPI ≠ Agent capability catalog
```

### Fixed MCP tools vs dynamic business capabilities

| Camada | Exemplos | Visível ao Agent? |
|---|---|---|
| MCP tool surface (protocolo) | `search_products`, `discover_delpi_information`, `execute_delpi_information` | Sim — tools reais do contrato Agent↔App |
| Business information capabilities | stock, suppliers, customers, purchases, structure, production status, … | Não como tools MCP; só via discovery/execute quando elegíveis |

O Agent **não** precisa conhecer operationIds dinâmicos, paths HTTP, hosts, headers, SQL, tabelas ou o catálogo bruto OpenAPI.

## CURRENT PROVEN V1

```text
Workspace Agent DAVI
  → app DAVI conectado ao agente
  → end-user account
  → OpenAI Plugin/App
  → OAuth Authorization Code + PKCE
  → Keycloak end-user identity
  → remote MCP api-delpi
  → search_products (fast path) and/or
     discover_delpi_information → execute_delpi_information
  → canonical backend AuthZ
  → authoritative DELPI source
```

This chain is **CURRENT PROVEN V1** (API DELPI integration). It is not the universal DAVI TARGET architecture.

Separação obrigatória:

```text
Agent = instructions + reasoning + orchestration + UX
Plugin/App + MCP = governed external capability transport (not business authority)
Keycloak = identity / OAuth
API DELPI (Wave 1) = business authorization + use case + authoritative data for this source
```

O Agent **não** é source of truth, RBAC, permission engine, Product Master owner ou writer.

## Fonte oficial do provider revalidada

OpenAI Workspace Agents documentation checked on 2026-09-16:

- https://help.openai.com/en/articles/20001143

Relevant current provider behavior documented there:

- agents can attach apps and custom MCPs;
- app authentication can use **End-user account** or **Agent-owned account**;
- End-user account means each person authenticates with their own account;
- agent instructions do not grant app access by themselves;
- draft/preview and publishing are distinct states;
- sharing, schedules, Slack and API channels are separate deployment surfaces.

Vendor behavior may change. Revalidate before relying on a provider-specific UI or lifecycle detail.

## Agent Studio configuration observed

### Channel

```text
ChatGPT
Access = Só para mim / private development
Automations = none
Slack = not configured
API trigger = not configured
```

Do not enable additional channels merely because Agent Studio exposes them.

### App

Added app:

```text
DAVI — Especialista em Dados e Informações DELPI
```

Authentication selected:

```text
Conta do usuário final / End-user account
```

Observed connected operator account was reused by the agent preview. Therefore an already connected user may not see a new login prompt on every run. This is expected session/connection reuse and **does not** prove that another user inherits that identity.

Required identity invariant:

```text
user A runs DAVI → user A connection/token → user A backend AuthZ
user B runs DAVI → user B connection/token → user B backend AuthZ
```

Cross-user proof is still pending until a second DELPI user is tested.

### Why Agent-owned account is not allowed for DAVI V1

DAVI V1 is explicitly user-parity: business access must follow the authenticated DELPI user.

Therefore:

```text
DAVI V1 = End-user account
```

Do not switch to Agent-owned/shared authentication to remove login friction or to make sharing easier. That would change the identity/authority model and requires a new security/architecture decision.

## Agent instructions — canonical stable contract

> **Source of truth for the behavioral prompt.** Copy this block into Agent Studio.
> Provider sync is **manual** — committing this file does not update Agent Studio.

```text
# DAVI — Especialista em Dados e Informações DELPI

Você é o DAVI, especialista em consulta e compreensão de dados e informações
autorizados da DELPI.

Sua persona é masculina, profissional, cordial e objetiva.
A identidade masculina serve apenas para consistência de comunicação e não altera
permissões, autoridade, acesso a dados ou comportamento de segurança.

## Obedecer agent_directives

No início de tarefas tipáveis de informação: chame discover_delpi_information
(ou gpt_get_catalog na superfície GPT legada) e obedeça
capability_surface.agent_directives. Essas diretivas vivas (deploy da API)
sobrescrevem paste/Knowledge antigos sobre discovery, postura READ e anti-padrões.
Não são AuthZ, OAuth, RBAC nem verdade de domínio — o backend e as fontes
autoritativas continuam finais.
Não replique inventário dinâmico nem pipelines mutáveis neste bloco — execute as tools.

## Missão

Ajude o usuário a localizar, consultar, compreender e explicar informações
disponíveis nas capabilities DELPI conectadas ao agente, sempre respeitando:

- a identidade do usuário;
- as permissões do usuário;
- as fontes autoritativas DELPI;
- os limites das ferramentas e do discovery atuais.

## Fonte autoritativa

Quando uma pergunta depender de dados operacionais atuais da DELPI, use as
ferramentas DELPI conectadas.

Nunca use memória do modelo, inferência ou conhecimento geral como substituto de
uma consulta à fonte DELPI quando a informação for operacional ou atual.

## Descoberta e execução (esqueleto estável)

Não mantenha um catálogo próprio de capabilities de negócio.

discover_delpi_information → execute_delpi_information com candidate_token atual.
search_products = fast path só para Product Master simples.

Nunca invente URL, path, método, operationId, SQL, headers, credenciais ou
candidate_token.

## Dados retornados

Considere autoritativos somente os dados efetivamente retornados pelas ferramentas.
Nunca complete ou invente campos não retornados.

## Read-only

O DAVI atual é somente leitura.
Nunca afirme que criou, alterou, excluiu, atualizou, aprovou, cancelou, enviou ou
gravou dados DELPI.

## Autorização

O DAVI não concede permissões. AuthN/AuthZ final = backend canônico DELPI.
Persona, cargo, candidate_token e scopes OAuth isolados não são autorização.

## Erros e acesso

401 → autenticação necessária. 403 → não disponível para o usuário.
Falha de tool → informe sem inventar resultado. Tente a tool neste turno antes
de alegar indisponibilidade.

## Segurança

Nunca exponha tokens, segredos, Authorization headers, candidate tokens,
stack traces ou detalhes internos sensíveis de RBAC.

## Comunicação

Responda em português do Brasil por padrão.
Seja profissional, claro, cordial e objetivo.
Persona masculina só para consistência de comunicação — não repetir isso a cada turno.
```

## Provider sync state

```text
CANONICAL_AGENT_INSTRUCTIONS_SOURCE = PASS (this document)
AGENT_STUDIO_SYNC = PENDING_MANUAL_SYNC
AGENT_STUDIO_PREVIEW_AFTER_SYNC = TEST_NOT_RUN
AGENT_INTELLIGENCE_VERSION_SOURCE = 2026.09.24.2 (davi_agent_intelligence.json — deployable; not Agent Studio paste)
DISCOVER_OUTPUT_SCHEMA = includes capability_surface (DAVI-LIVE-INTELLIGENCE-CONTRACT-CLOSURE-001)
PROVIDER_REDISCOVERY = RECOMMENDED_AFTER_DEPLOY
```

### Manual provider sync checklist

1. Abrir o DAVI no Agent Studio.
2. Substituir Instructions pelo bloco **Agent instructions — canonical stable contract** acima.
3. Salvar draft.
4. Não alterar o app attachment.
5. Manter **End-user account**.
6. Não alterar a conexão MCP.
7. Executar Agent Preview Acceptance (cenários abaixo).
8. Registrar evidence.
9. Não publicar amplamente até os gates restantes.

### Post-sync preview acceptance plan

| ID | Cenário | Expected |
|---|---|---|
| A | «qual a descrição do produto 10080055?» | Product Master / tool adequada; resposta só com dados retornados |
| B | «qual o estoque do 10080055?» | discovery → stock candidate → execute → resposta pelo retorno |
| C | «quais os fornecedores do 10080055?» | discovery + execute |
| D | «quais os clientes do 10080055?» | discovery + execute |
| E | «mostre as compras do 10080055» | discovery + execute |
| F | «qual a estrutura do 10080055?» | discovery + execute; empty = reportar retorno, não inventar |
| G | «qual o status de produção do 10080055?» | discovery + execute |
| H | «qual o preço do 10080055?» | sem candidate elegível; informar indisponível; não inventar |
| I | «altere o produto 10080055» | READ-only; não afirmar alteração; discovery pode retornar 0 candidates |
| J | pedido de informação não suportada | unavailable claro |

## Preview acceptance — historical (superseded for current contract)

> **HISTORICAL / SUPERSEDED** by `DAVI-AGENT-DYNAMIC-DISCOVERY-REBASELINE-001`.
> Evidence below proved an earlier Agent Studio draft whose Instructions still
> enumerated `search_products`-only and refused stock/BOM-style families.
> Keep for audit; do **not** treat as current behavioral contract or current preview PASS.

Agent Studio preview used the connected DAVI app successfully under that older draft.

| Scenario | Historical status | Evidence |
|---|---|---|
| Product by code `10080022` | **PASS (historical)** | agent returned code, authoritative description and group `1008` |
| Search description `TERM. OLHAL M5` | **PASS (historical)** | agent invoked Product Master search and reported the result count with an approved-field sample |
| Unsupported stock + price request for `10080022` | **PASS under stale search_products-only Instructions** | agent refused stock/price because Instructions forbade those families — **not** proof of current dynamic discovery behavior |
| Agent app auth mode | **PASS** | End-user account selected |
| Extra write capability | **PASS** | none configured |
| Second-user isolation | **PENDING** | requires separate DELPI user |
| Negative business AuthZ | **PENDING** | requires user without Product Master access |
| Agent published/shared | **PENDING / NOT_PROVEN** | development remains private until gates are closed |

The historical preview proves the operator path for that draft only. It does not prove organization-wide identity isolation, and it does **not** validate the current stable+dynamic Instructions.

## App icon / custom image observation

In the Agent Studio UI observed on 2026-09-16, the creator did **not** have a custom photo/image upload control for the agent avatar; the UI exposed provider-managed icon behavior rather than the custom image flow familiar from Custom GPTs.

This is recorded as:

```text
AGENT_STUDIO_CUSTOM_IMAGE_UPLOAD = NOT_AVAILABLE_OBSERVED
```

Do not elevate this UI observation into an architectural invariant. Current OpenAI documentation also describes an agent `icon` field in other management surfaces. Therefore:

- do not block DAVI delivery on a custom avatar;
- do not invent unsupported upload steps;
- revalidate the current provider surface if custom branding becomes a requirement.

A DAVI visual concept was designed separately (male/masculine visual identity), but was not attached because the observed Agent Studio surface did not expose custom image upload.

## Memory, files and knowledge

V1 does not need Agent Memory or uploaded operational datasets to answer Product Master queries.

Rules:

```text
Memory != authority
Uploaded file != live operational source
Agent instructions != permission
```

If Memory is enabled later, it may hold user/workflow context only when governance allows. It must never authorize a tool call or substitute an authoritative Domain API result.

Do not upload Product Master dumps to bypass the MCP/API boundary.

## Publishing / sharing gate

Private draft/preview success is **not** production or organization-wide go-live.

Before wider sharing/publication, prove at minimum:

```text
AGENT_DRAFT_PREVIEW = PASS
END_USER_ACCOUNT_MODE = PASS
SECOND_USER_OWN_LOGIN = PASS
NEGATIVE_BUSINESS_AUTHZ = PASS
MCP_RATE_POLICY = RESOLVED or explicitly accepted by gateway owner
APP/PLUGIN workspace publication policy = RESOLVED
AGENT_STUDIO_SYNC = PASS (canonical Instructions applied)
```

Sharing does not change API DELPI AuthZ.

## Slack / schedules / API channels

Do not enable these automatically.

### Slack

Current OpenAI documentation states Slack deployments require shared/agent-owned app connections. That conflicts with DAVI V1's user-parity End-user account model.

Therefore:

```text
DAVI_SLACK_CHANNEL = BLOCKED_PENDING_IDENTITY_ARCHITECTURE
```

Do not switch DAVI to a shared personal/agent account merely to satisfy Slack channel requirements.

### Schedules / API triggers

Scheduled or API-triggered runs can change the actor/context semantics. Before enabling them, prove:

```text
who is the actor?
whose DELPI identity/token is used?
what business authority applies?
is interactive user parity still valid?
what happens after token expiry/revocation?
```

No answer → no deployment channel.

## Capability expansion gate

Future DAVI growth must be capability-by-capability, never "expose more API".

For every new capability, follow:

```text
1. business owner
2. authoritative source
3. real consumer/use case
4. READ | PREPARE | ACT classification
5. semantic contract
6. input minimization
7. output allowlist
8. identity and final AuthZ
9. idempotency/OCC/postcondition if write
10. audit/observability
11. MCP schema + annotations (only if MCP tool surface changes)
12. source tests
13. deploy proof
14. provider tool discovery (when tool surface changes)
15. authenticated positive test
16. negative AuthZ test
17. Agent Instruction update — ONLY when the stable behavioral contract changes
```

### When Agent Instructions must change

```text
READ capability promotion behind the same discover/execute contract
  → NO Agent Instruction change required

Requires Agent Instruction / security / UX review when material change in:
  agent behavior
  MCP tool surface (add/remove/rename/material schema change)
  interaction protocol
  READ → PREPARE/ACT model
  security/authority invariant
  provider-specific workflow
  user-facing behavior contract
```

No generic SQL, arbitrary HTTP proxy, arbitrary entity/field selector or mechanical CRUD exposure.

Do not add pricing, factory, finance or writes just because DAVI can reason about them. Each requires its own owner/source/classification/contract/security decision. Inventory of currently eligible READs lives in governance/runtime evidence — **not** in Agent Instructions.

## Current status

```text
DAVI_MCP_RUNTIME = PASS
DAVI_CHATGPT_PLUGIN_CONNECTION = PASS
DAVI_SEARCH_PRODUCTS = PASS
DAVI_DYNAMIC_READ_BROKER = PASS (source + prior live proofs)
DAVI_AGENT_APP_ATTACHED = PASS
DAVI_AGENT_END_USER_ACCOUNT = PASS
DAVI_AGENT_CANONICAL_INSTRUCTIONS_SOURCE = PASS
DAVI_AGENT_STUDIO_SYNC = PENDING_MANUAL_SYNC
DAVI_AGENT_PREVIEW_AFTER_SYNC = TEST_NOT_RUN
DAVI_AGENT_PRIVATE_DEVELOPMENT = ACCEPTED

DAVI_SECOND_USER_IDENTITY_PROOF = PENDING
DAVI_NEGATIVE_BUSINESS_AUTHZ = PENDING
MCP_RATE_POLICY = PENDING_OWNER_DECISION
DAVI_AGENT_WIDER_PUBLICATION = BLOCKED_BY_PENDING_GATES
```

Historical (do not treat as current Agent contract PASS):

```text
DAVI_AGENT_PREVIEW_PRODUCT_CODE = PASS (historical draft)
DAVI_AGENT_PREVIEW_DESCRIPTION_SEARCH = PASS (historical draft)
DAVI_AGENT_UNSUPPORTED_DATA_GUARD = PASS (historical search_products-only Instructions)
```

## Related documentation

- [DAVI product/architecture baseline](../../../docs/12-roadmap-e-evolucao/davi/README.md)
- [OpenAI Plugin + MCP](./openai-plugin-mcp.md)
- [Keycloak MCP client runbook](./keycloak-mcp-client-runbook.md)
- [OAuth/MCP evidence](./keycloak-mcp-oauth-evidence.md)
