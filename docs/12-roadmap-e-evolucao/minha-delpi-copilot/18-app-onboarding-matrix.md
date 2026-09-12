# Minha DELPI Copilot — Matriz de Onboarding dos Apps

**Status:** inventário inicial / `TO_INVENTORY`  
**Owner factual:** C0.S0 + future readiness scanner  
**Regra:** nenhum campo sem evidence vira comprovado por suposição.

## 1. Objetivo

Mapear como o **novo Copilot standalone** descobre e integra apps/APIs existentes sem hardcode central e sem depender do Minha DELPI Chat.

## 2. Níveis AI-ready

| Nível | Nome | Critério mínimo |
|---|---|---|
| L0 | NOT_INVENTORIED | não auditado |
| L1 | DISCOVERABLE | app/rotas/permissions discoverable |
| L2 | CONTEXT_READY | EntityRef/deep link + WorkspaceContext quando material |
| L3 | READ_READY | business reads via Domain API/OpenAPI + RBAC + evidence |
| L4 | WRITE_READY | writes + Decision Gate + idempotency/audit |
| L5 | WORKFLOW_READY | safe durable workflow/events when required |

## 3. Iframe class

```text
I0 PORTAL_ONLY
I1 CONTEXTUAL
I2 INTERACTIVE
I3 AI_READY
```

I3 exige Business Actions por API/OpenAPI.

## 4. Campos obrigatórios por app

C0 deve registrar:

```text
appId/name
manifest path/version
renderMode/MFE path
backend/domain API owner
Core registration
routes/permissions
canonical entity IDs
entity deep links
WorkspaceContext support
OpenAPI location/version/quality
business reads/writes
risk/sensitivity owner
Decision Gate readiness
idempotency/concurrency
outcome/evidence/freshness
events/workflow relevance
iframe class/origin/SSO/bridge if applicable
knowledge/help sources
owner/team
candidate wave
blockers
evidence paths/hashes/timestamp
```

Além disso:

```text
COPILOT_INTEGRATION = API_CONTRACT | PLATFORM_CONTEXT | IFRAME_BRIDGE | NONE
CHAT_DEPENDENCY_FOR_COPILOT = MUST_BE_NONE
```

## 5. Inventário inicial — candidatos

A lista é ponto de partida, não prova.

| Área/app | Referência | Nível | Wave candidata | Estado |
|---|---|---:|---|---|
| Minha DELPI Chat | sistema vizinho/reference-only | N/A | nenhuma | OUT_OF_SCOPE para onboarding Copilot |
| Portal Comercial | commercial | L0 | Wave 1 candidata | TO_INVENTORY |
| Portal Suprimentos | supplies | L0 | Wave 1 candidata | TO_INVENTORY |
| Minhas Solicitações | my-requests | L0 | Wave 1 candidata | TO_INVENTORY |
| Portal Engenharia | engineering | L0 | Wave 2 | TO_INVENTORY |
| Portal Financeiro | financial | L0 | Wave 2 | TO_INVENTORY |
| Production Control | production-control | L0 | Wave 2 | TO_INVENTORY |
| Production Pulse | production-pulse | L0 | Wave 2 | TO_INVENTORY |
| Apontamento Produção | production-appointments | L0 | Wave 2 | TO_INVENTORY |
| Eficiência Fabril | eficiencia-fabril | L0 | Wave 2 | TO_INVENTORY |
| Acompanhamento Refugos | scrap-monitoring | L0 | Wave 2 | TO_INVENTORY |
| Indicadores Estratégicos | strategic indicators | L0 | Wave 2 | TO_INVENTORY |
| Manutenção | maintenance | L0 | Wave 2 | TO_INVENTORY |
| Customer Experience | customer-experience | L0 | Wave 2 | TO_INVENTORY |
| Planos de Ação Qualidade | quality-action-plans | L0 | Wave 2 | TO_INVENTORY |
| Inspeções Entrada | inspecoes-entrada | L0 | Wave 2 | TO_INVENTORY |
| Inspeções Processo | inspecoes-processo | L0 | Wave 3 | TO_INVENTORY |
| Solicitações Compras | purchase requests | L0 | Wave 2 | TO_INVENTORY |
| Controle MP | controle-mp | L0 | Wave 3 | TO_INVENTORY |
| Emissão/Lançamento NF | invoice apps | L0 | Wave 3 | TO_INVENTORY |
| Despesas Viagem | travel expenses | L0 | Wave 3 | TO_INVENTORY |
| CIPA | cipa | L0 | Wave 3 | TO_INVENTORY |
| Comitê Ética/Conduta | ethics | L0 | Wave 3 | TO_INVENTORY |
| Auditoria 5S | auditoria-5s | L0 | Wave 3 | TO_INVENTORY |
| Central Agendamento | central-agendamento | L0 | Wave 3 | TO_INVENTORY |
| Delpi Reports | delpi-reports | L0 | Wave 3 | TO_INVENTORY |
| TV Dashboard | tv-dashboard | L0 | Wave 3 | TO_INVENTORY |
| Transformômetro | transformometro | L0 | Wave 3 | TO_INVENTORY |

C0 deve reconciliar esta lista com `plugins/`, Core registrations e APIs reais.

## 6. API inventory é parte do onboarding

Para cada app/domain mapear também:

```text
API service
Gateway base path
OpenAPI source
JWT/auth model
permission headers/scopes
error envelope
pagination
entity IDs
read operations
write operations
idempotency support
events/websockets
health
```

O Copilot integra a API owner diretamente; não passa pelo Chat.

## 7. Wave 1

Priorizar apps com:

- Core registration/permissions estáveis;
- owner disponível;
- EntityRef/deep-link claro;
- OpenAPI real;
- useful reads;
- contextual value;
- lower pilot risk;
- future governed write path;
- observability/tests.

Comercial, Suprimentos e Minhas Solicitações permanecem candidatos até C0.S0.

## 8. Readiness evidence

```text
gitSha
manifest path
Core registration evidence
route/permission source
OpenAPI source/hash
entity/deep-link contract
WorkspaceContext contract/test
Decision/idempotency contract
event source if applicable
iframe origin/protocol if applicable
smoke/eval
lastVerifiedAt
```

No evidence → `TO_INVENTORY`.

## 9. Promotion

```text
L1 → L2: context/entity foundations
L2 → L3: generic read + RBAC + outcome/evidence
L3 → L4: write + Decision Gate + idempotency/audit
L4 → L5: workflow safety + resume/events when required
```

Iframe:

```text
I0 → I1 context handshake
I1 → I2 declared visual commands
I2 → I3 Business Actions via API/OpenAPI
```

## 10. Foundation rule

App onboarding não cria new primitives or product-specific planner branches. Se um app revelar gap de Entity/Evidence/Decision/Workspace/Event, voltar à foundation/versioned contract antes de implementar.