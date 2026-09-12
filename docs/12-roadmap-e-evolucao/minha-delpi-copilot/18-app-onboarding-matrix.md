# Minha DELPI Copilot — Matriz de Onboarding dos Apps

**Status:** inventário inicial / `TO_INVENTORY`  
**Owner factual:** C0.S0 + future readiness scanner  
**Regra:** nenhum campo sem evidence vira comprovado por suposição.  
**Multimodal/Meeting/Frontline:** [`53-multimodal-meeting-frontline-and-industrial-copilot.md`](./53-multimodal-meeting-frontline-and-industrial-copilot.md)

## 1. Objetivo

Mapear como o **novo Copilot standalone** descobre e integra apps/APIs existentes sem hardcode central e sem depender do Minha DELPI Chat.

O onboarding de negócio e a prontidão Frontline/media são dimensões relacionadas, mas diferentes: um app pode estar `READ_READY` sem possuir qualquer suporte a device/câmera/voz.

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

## 4. Frontline/media readiness — dimensão complementar

Não alterar L1–L5 para representar hardware/modalidade.

Quando um app/domínio tiver relevância para chão de fábrica, C0 pode registrar separadamente:

```text
F0 NOT_APPLICABLE_OR_NOT_INVENTORIED
F1 OPERATIONAL_CONTEXT_READY
F2 DEVICE_UI_READY
F3 MEDIA_ASSIST_READY
F4 FRONTLINE_WORKFLOW_READY
```

Critérios conceituais:

- `F1`: IDs/owners para OP/máquina/produto/operação/posto + WorkspaceContext/EntityRef;
- `F2`: UX/device/browser/shared-session constraints conhecidas;
- `F3`: voz/câmera/media permitidos por policy/device + Evidence provenance;
- `F4`: escalation/action/workflow governados + training/procedure sources.

Esses níveis só recebem estado real após evidence. Até lá: `TO_INVENTORY`.

## 5. Campos obrigatórios por app/domain

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

Quando Frontline/media for aplicável, adicionar sem inventar:

```text
operational entity types/IDs
productionOrder/operation/machine/workstation source owners
procedure/work-instruction source
revision/freshness source
training/qualification owner
shared-device pattern
browser/device capabilities
mic/camera/media relevance
media/consent/retention owner
network constraints
OT telemetry relevance
industrial safety owner
frontline readiness class
```

Além disso:

```text
COPILOT_INTEGRATION = API_CONTRACT | PLATFORM_CONTEXT | IFRAME_BRIDGE | NONE
CHAT_DEPENDENCY_FOR_COPILOT = MUST_BE_NONE
```

## 6. Inventário inicial — candidatos

A lista é ponto de partida, não prova.

| Área/app | Referência | Nível | Frontline | Wave candidata | Estado |
|---|---|---:|---|---|---|
| Minha DELPI Chat | sistema vizinho/reference-only | N/A | N/A | nenhuma | OUT_OF_SCOPE para onboarding Copilot |
| Portal Comercial | commercial | L0 | F0 | Wave 1 candidata | TO_INVENTORY |
| Portal Suprimentos | supplies | L0 | F0 | Wave 1 candidata | TO_INVENTORY |
| Minhas Solicitações | my-requests | L0 | F0 | Wave 1 candidata | TO_INVENTORY |
| Portal Engenharia | engineering | L0 | F0 | Wave 2 | TO_INVENTORY |
| Portal Financeiro | financial | L0 | F0 | Wave 2 | TO_INVENTORY |
| Production Control | production-control | L0 | F0 | Wave 2 | TO_INVENTORY |
| Production Pulse | production-pulse | L0 | F0 | Wave 2 | TO_INVENTORY |
| Apontamento Produção | production-appointments | L0 | F0 | Wave 2 | TO_INVENTORY |
| Eficiência Fabril | eficiencia-fabril | L0 | F0 | Wave 2 | TO_INVENTORY |
| Acompanhamento Refugos | scrap-monitoring | L0 | F0 | Wave 2 | TO_INVENTORY |
| Indicadores Estratégicos | strategic indicators | L0 | F0 | Wave 2 | TO_INVENTORY |
| Manutenção | maintenance | L0 | F0 | Wave 2 | TO_INVENTORY |
| Customer Experience | customer-experience | L0 | F0 | Wave 2 | TO_INVENTORY |
| Planos de Ação Qualidade | quality-action-plans | L0 | F0 | Wave 2 | TO_INVENTORY |
| Inspeções Entrada | inspecoes-entrada | L0 | F0 | Wave 2 | TO_INVENTORY |
| Inspeções Processo | inspecoes-processo | L0 | F0 | Wave 3 | TO_INVENTORY |
| Solicitações Compras | purchase requests | L0 | F0 | Wave 2 | TO_INVENTORY |
| Controle MP | controle-mp | L0 | F0 | Wave 3 | TO_INVENTORY |
| Emissão/Lançamento NF | invoice apps | L0 | F0 | Wave 3 | TO_INVENTORY |
| Despesas Viagem | travel expenses | L0 | F0 | Wave 3 | TO_INVENTORY |
| CIPA | cipa | L0 | F0 | Wave 3 | TO_INVENTORY |
| Comitê Ética/Conduta | ethics | L0 | F0 | Wave 3 | TO_INVENTORY |
| Auditoria 5S | auditoria-5s | L0 | F0 | Wave 3 | TO_INVENTORY |
| Central Agendamento | central-agendamento | L0 | F0 | Wave 3 | TO_INVENTORY |
| Delpi Reports | delpi-reports | L0 | F0 | Wave 3 | TO_INVENTORY |
| TV Dashboard | tv-dashboard | L0 | F0 | Wave 3 | TO_INVENTORY |
| Transformômetro | transformometro | L0 | F0 | Wave 3 | TO_INVENTORY |

`F0` nesta tabela significa **não inventariado**, não “sem relevância Frontline”.

C0 deve reconciliar a lista com `plugins/`, Core registrations, APIs reais e realidade operacional.

## 7. API inventory é parte do onboarding

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

## 8. Operational-context inventory

Para domínios industriais, provar relações/IDs reais, por exemplo quando existirem:

```text
productionOrder
operation
machine
workstation
product/revision
lot
material
tool
maintenance event
quality inspection/nonconformity
```

Não inventar source system ou relationship apenas porque faz sentido conceitualmente.

## 9. Frontline onboarding rules

Frontline-ready exige mais do que “ter uma API”.

Verificar:

- device/browser disponível;
- user/shared-session model;
- context source;
- procedure/revision source;
- accessibility/touch/noise;
- media permissions/policy;
- offline/degraded behavior;
- escalation/action contract;
- training qualification owner;
- industrial safety boundary.

A falta de câmera/microfone não impede L1–L5 de negócio; apenas limita a experiência Frontline/media.

## 10. Meeting onboarding

Meeting Mode não exige que cada domínio implemente um “meeting endpoint”.

Para responder durante reunião, o domínio precisa apenas das capabilities normais:

```text
OpenAPI/readiness
RBAC
EntityRef/Evidence
freshness
```

A sessão/ata pertence ao Copilot.

## 11. Wave 1

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

**Não assumir** que Wave 1 administrativa deve ser também o primeiro piloto Frontline. O piloto Frontline depende do inventário de produção/device/processo e deve ser selecionado por evidence.

## 12. Readiness evidence

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
frontline/device/media evidence if applicable
procedure/revision owner if applicable
industrial safety owner if applicable
smoke/eval
lastVerifiedAt
```

No evidence → `TO_INVENTORY`.

## 13. Promotion

Business:

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

Frontline:

```text
F1 → source IDs/context proven
F2 → device/session/UX proven
F3 → media/policy/evidence proven
F4 → governed work/escalation/training proven
```

Uma promoção Frontline nunca amplia RBAC do app.

## 14. Foundation rule

App onboarding não cria new primitives or product-specific planner branches.

Se um app revelar gap de Entity/Evidence/Decision/Workspace/Event/Media, voltar à foundation/versioned contract antes de implementar.

Nunca criar contexto/action executor separado só para Frontline ou Meeting.