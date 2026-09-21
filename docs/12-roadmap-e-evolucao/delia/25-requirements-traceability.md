# DÉLIA — Matriz Canônica de Rastreabilidade

**Objetivo:** garantir owner, fase, gate e status de cada requisito.  
**Ordem:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Boundary:** [`50-standalone-copilot-application-architecture.md`](./50-standalone-copilot-application-architecture.md)  
**Testes:** [`20-testing-and-acceptance-matrix.md`](./20-testing-and-acceptance-matrix.md)  
**Naming:** [`68-delia-product-identity-and-naming.md`](./68-delia-product-identity-and-naming.md)  
**Multimodal/Meeting/Frontline:** [`53-multimodal-meeting-frontline-and-industrial-copilot.md`](./53-multimodal-meeting-frontline-and-industrial-copilot.md)  
**Biometric/Human Observation:** [`54-biometric-identity-and-human-observation-governance.md`](./54-biometric-identity-and-human-observation-governance.md)  
**Internet/External Connectors:** [`55-internet-research-and-external-connectors.md`](./55-internet-research-and-external-connectors.md)  
**Microsoft Teams:** [`56-microsoft-teams-connector-and-meeting-integration.md`](./56-microsoft-teams-connector-and-meeting-integration.md)  
**Autonomous Operations/Execution Hub:** [`57-event-driven-autonomous-operations-and-automation-execution-hub.md`](./57-event-driven-autonomous-operations-and-automation-execution-hub.md)  
**Process Intelligence:** [`58-process-intelligence-and-process-mining.md`](./58-process-intelligence-and-process-mining.md)  
**AI Control Tower:** [`59-ai-control-tower-and-digital-workforce-governance.md`](./59-ai-control-tower-and-digital-workforce-governance.md)  
**MCP/A2A:** [`60-agent-interoperability-mcp-a2a-and-tool-protocols.md`](./60-agent-interoperability-mcp-a2a-and-tool-protocols.md)  
**Personal Memory:** [`61-personal-memory-and-personalization.md`](./61-personal-memory-and-personalization.md)  
**Semantic Business Layer:** [`62-semantic-business-layer-and-governed-metrics.md`](./62-semantic-business-layer-and-governed-metrics.md)  
**Analysis/Artifacts:** [`63-analysis-sandbox-and-artifact-workspace.md`](./63-analysis-sandbox-and-artifact-workspace.md)  
**Predictive/Twin:** [`64-predictive-prescriptive-intelligence-and-operational-twin.md`](./64-predictive-prescriptive-intelligence-and-operational-twin.md)  
**Edge/Offline:** [`65-edge-offline-industrial-copilot.md`](./65-edge-offline-industrial-copilot.md)  
**Model Lifecycle/Marketplace:** [`66-ai-model-lifecycle-and-capability-marketplace.md`](./66-ai-model-lifecycle-and-capability-marketplace.md)

> Esta é a única authority `CP-*`. IDs históricos não são reutilizados nem apagados; requisitos ligados à migração do Minha DELPI Chat são preservados como `OUT_OF_SCOPE_WITH_DECISION`.

> DÉLIA é o nome do produto. Labels de owner em linhas `CP-*` usam **DÉLIA …** (C0.S2-T1 terminology cleanup). Tokens `COPILOT_*` (gate IDs), `CopilotBridge` (Portal bridge histórico) e `minha-delpi-copilot*` (paths SUPERSEDED/HISTORICAL) podem permanecer. Naming update ≠ implementation evidence.

## 1. Status

```text
PLANNED
REVALIDATE
TO_INVENTORY
LOCKED
IN_PROGRESS
BLOCKED_WITH_EVIDENCE
FAIL
PASS
OUT_OF_SCOPE_WITH_DECISION
```

`BLOCKED_BY_AI_GATE` foi removido da DÉLIA: o runtime OpenAPI-first será construído nativamente na nova DÉLIA API e não depende do roadmap do Chat.

## 2. C0 — Platform + Architecture Foundation Freeze

| ID | Requisito | Owner | Gate | Status |
|---|---|---|---|---|
| CP-051 | Correlação/observabilidade transversal | DÉLIA API/Portal/Observability | contracts/traces | PLANNED |
| CP-055 | Prompt/tool/context injection safety | DÉLIA Policy | security semantics | PLANNED |
| CP-056 | Secret redaction | todos os owners | redaction contract | PLANNED |
| CP-057 | Idempotency semantics de writes | Domain API + DÉLIA orchestration | C0 contract; runtime C5 | PLANNED |
| CP-072 | Expertise Pack versionado | DÉLIA API | primitive/schema | PLANNED |
| CP-075 | Domain Playbook versionado | DÉLIA API/domain owners | primitive/schema | PLANNED |
| CP-077 | Expertise não concede RBAC | Core/DÉLIA Policy | invariant | PLANNED |
| CP-088 | PDF/imagem não altera policy | DÉLIA Multimodal/Policy | safety contract; C3 eval | PLANNED |
| CP-091 | EntityRef cross-domain canônico | DÉLIA shared/domain owners | primitive | PLANNED |
| CP-092 | RelationshipRef com provenance | Graph/domain owners | primitive | PLANNED |
| CP-093 | EvidenceRef transversal | DÉLIA API | primitive | PLANNED |
| CP-094 | Epistemic classes canônicas | DÉLIA synthesis | semantics | PLANNED |
| CP-095 | Evidence multimodal page/region | DÉLIA Multimodal | contract; runtime C3 | PLANNED |
| CP-105 | Workflow persistence/checkpoint contract | DÉLIA Work Runtime | lifecycle contract | PLANNED |
| CP-106 | `wait_user` semantics | DÉLIA Work Runtime | lifecycle contract | PLANNED |
| CP-107 | `wait_approval` semantics | DÉLIA Work/Policy | lifecycle contract | PLANNED |
| CP-108 | `wait_event` semantics | DÉLIA Work/Event | lifecycle contract | PLANNED |
| CP-109 | No duplicate write after resume | DÉLIA Work/Executor | idempotency contract | PLANNED |
| CP-110 | Decision Gate proporcional a risco | DÉLIA Policy | contract | PLANNED |
| CP-111 | Approval workflow humano | DÉLIA Policy/Work | contract | PLANNED |
| CP-123 | Provider data-policy filtering | DÉLIA Security | policy contract | PLANNED |
| CP-130 | Clean Architecture + Ports & Adapters + DDD pragmático | Architecture | architecture freeze | PLANNED |
| CP-131 | Layer/dependency direction canônicas | Architecture | conformance | PLANNED |
| CP-132 | DI/Composition Root + adapters/ports | Architecture/owners | wiring conformance | PLANNED |
| CP-133 | Pattern Decision Matrix | Architecture | review | PLANNED |
| CP-134 | Abstraction Gate | Architecture | no unjustified abstraction | PLANNED |
| CP-135 | Error/Result model transversal | Application/Interfaces | contract/conformance | PLANNED |
| CP-136 | EventEnvelope + Outbox/Idempotency/Resilience rules | Platform/Work | conformance | PLANNED |
| CP-137 | State Machine para lifecycles não triviais | Domain/Policy/Work | transition tests | PLANNED |
| CP-138 | Frontend state ownership | Portal/DÉLIA MFE | frontend conformance; browser-retained residency gate and centralized removability (C2-T1D1) | PLANNED — policy APPROVED; runtime boundary not implemented |
| CP-139 | Adapter/ACL/Strangler para integrações legadas quando necessário | Architecture | migration gate | PLANNED |
| CP-140 | Architecture conformance + ADR process | Architecture | conformance/ADR | PLANNED |
| CP-146 | Zero dependência de runtime do Minha DELPI Chat | DÉLIA Platform | Chat-offline/scan | PLANNED |
| CP-147 | Persistência/migration chain próprias da DÉLIA | DÉLIA API (`delia-api/migrations/` when owned state exists) | storage ownership | PLANNED — **NOT_APPLICABLE_AT_C1** (C1-T6D1: no DÉLIA-owned persisted state; REQUIRED on first owned persistence) |
| CP-154 | Inventário Portal/Core/Gateway/APIs/MFEs antes do runtime | Architecture | C0.S0 evidence | PLANNED |
| CP-157 | Media capture/consent/retention classes definidas antes do runtime multimodal contínuo | DÉLIA Security/Architecture | media/privacy foundation | PLANNED |
| CP-158 | Shared-device identity/session isolation | DÉLIA/Portal/Security | User A → logout → User B negative (C2-T1D1) | PLANNED — invariant FROZEN_ACCEPTED; tests TEST_NOT_RUN |
| CP-175 | Raw media minimization e retention class-specific | DÉLIA Media/Security | retention/data minimization | PLANNED |
| CP-176 | Sem reconhecimento facial open-world/indiscriminado, emotion detection como truth ou hidden surveillance por default | Security/Governance | privacy negative gate | PLANNED |
| CP-178 | Arbitrary LLM→machine command proibido | DÉLIA/Industrial Safety | OT boundary gate | PLANNED |
| CP-179 | Future OT actuation exige safety gate separado | Industrial owner/DÉLIA | separate architecture/risk approval | PLANNED |
| CP-182 | Enrollment biométrico explícito, versionado, revogável e com purpose/retention definidos | DÉLIA Biometric/Security | enrollment lifecycle contract | PLANNED |
| CP-183 | Biometric match nunca concede autenticação/permissão por si só | DÉLIA Policy/Core | permission-elevation negative | PLANNED |
| CP-188 | Human Observation limitado a evidência observável do processo; sem inferência psicológica/sensível | DÉLIA Security/Governance | prohibited-inference gate | PLANNED |
| CP-189 | Sem decisão trabalhista automática baseada em biometria/Human Observation | Governance/People owner/DÉLIA | employment-decision negative | PLANNED |
| CP-190 | Biometric templates protegidos, não logados, revogáveis e com retenção própria | DÉLIA Biometric/Security | storage/key/retention gate | PLANNED |
| CP-194 | Inventário de egress, OAuth, secrets/vault, webhooks e integrações externas antes do runtime | Architecture/Security | external-access foundation | PLANNED |
| CP-195 | Safe Web Fetch bloqueia SSRF/private/link-local/metadata e revalida redirects | DÉLIA Internet/Security | egress negative gate | PLANNED |
| CP-196 | Conteúdo web/email/chat externo é untrusted e não altera system/policy/RBAC | DÉLIA Security | external injection gate | PLANNED |
| CP-197 | ExternalConnection usa least privilege, consent/scope disclosure, revoke/reconnect e audit | DÉLIA Connectors/Security | connection lifecycle contract | PLANNED |
| CP-198 | Access/refresh tokens e provider secrets nunca chegam ao LLM/MFE/logs e usam storage protegido | DÉLIA Infrastructure/Security | credential leakage negative | PLANNED |
| CP-199 | USER_DELEGATED, ORG_MANAGED, SHARED_RESOURCE e SERVICE_CONNECTION preservam ownership/visibility distintos | DÉLIA Connectors/Privacy | ownership isolation gate | PLANNED |
| CP-209 | External data possui retention/delete/cache policy por connection/source class | DÉLIA Privacy/State | retention gate | PLANNED |
| CP-210 | Provider terms/scopes/limits/compliance são revalidados na implementação e rollout | DÉLIA Governance | provider compliance gate | PLANNED |
| CP-211 | WhatsApp usa contratos oficiais suportados; scraping/automação de sessão pessoal é proibido por default | DÉLIA Connectors/Security | supported-contract gate | PLANNED |
| CP-214 | Internet/connector/write/webhook possuem kill switches independentes de prompt/LLM | DÉLIA Admin/Security | emergency disable gate | PLANNED |
| CP-223 | Teams inventory congela Entra app registration, tenant/admin owner, Graph scopes, resource-specific consent, webhooks, app distribution e meeting-artifact privacy antes do runtime | DÉLIA Teams/Architecture/Security | Teams foundation gate | PLANNED |
| CP-226 | C0 inventaria event sources/buses/webhooks/schedulers, RPA tools/licenças/bots, scripts/jobs, queues/workers, service accounts, credential owners, outcome sources e automation governance antes de runtime | Architecture/Automation/Security | automation foundation inventory | PLANNED |
| CP-227 | DÉLIA intelligence/orchestration e Automation & Execution Hub execution permanecem separáveis; Hub não cria segundo planner/AI authority | Architecture/DÉLIA Automation | ownership/bounded-context gate | PLANNED |
| CP-228 | Executor preference é API/integration/function antes de RPA/computer-use quando contrato autoritativo suportado existir | DÉLIA Automation/Architecture | executor-selection architecture gate | PLANNED |
| CP-229 | Background/autonomous execution usa user/service identity explícita, auditável e não deriva autoridade de evento/LLM | DÉLIA Security/Core/Automation | background identity gate | PLANNED |
| CP-230 | Execution contract define correlation, idempotency, pre/postconditions, timeout/retry e verified Outcome semantics antes de executors materiais | DÉLIA Automation/Work | execution contract gate | PLANNED |
| CP-231 | Event source authenticity/trust, dedupe, ordering/correlation e polling fallback bounded são definidos antes de continuous operations | DÉLIA Events/Architecture | event foundation gate | PLANNED |
| CP-249 | C0 inventaria event logs, process owners, case keys, BPMN/process docs, task-mining telemetry/privacy e data quality antes de Process Intelligence runtime | DÉLIA Process Intelligence/Architecture | process-intelligence foundation inventory | PLANNED |
| CP-256 | C0 inventaria todos os AI/automation assets, owners, risk/compliance, evals, cost telemetry, incidents e kill-switch mechanisms antes da Control Tower | DÉLIA Control Tower/Governance | AI asset governance foundation | PLANNED |
| CP-262 | C0 inventaria MCP/A2A/tool registries, external agents, service identities, delegation credentials, protocol versions e trust boundaries | DÉLIA Interoperability/Security | protocol interoperability foundation | PLANNED |
| CP-268 | C0 congela ownership/classes/retention/export/delete/user-controls para Personal Memory; memória não é Knowledge nem permission authority | DÉLIA Memory/Privacy | personal-memory foundation | PLANNED |
| CP-274 | C0 inventaria business glossary, KPI formulas, BI semantic models, metric owners, grain/dimensions, freshness e definition conflicts | DÉLIA Semantic Layer/Data owners | semantic foundation inventory | PLANNED |
| CP-280 | C0 inventaria code/data-analysis sandbox, BI/query engines, file scanning/storage e artifact-generation/versioning infrastructure e boundaries | DÉLIA Analysis/Artifacts/Security | sandbox/artifact foundation inventory | PLANNED |
| CP-287 | C0 inventaria predictive/anomaly/optimization/simulation models, datasets, ground truth, owners e operational/digital-twin sources | DÉLIA Predictive/Twin/Data owners | predictive/twin foundation inventory | PLANNED |
| CP-295 | C0 inventaria factory network, Edge platforms/devices, MDM, local inference, offline requirements, time sync, OT segmentation e cache/update owners | DÉLIA Edge/Industrial/Infrastructure | edge/offline foundation inventory | PLANNED |
| CP-302 | C0 inventaria model providers, local ML models, registries/MLOps, datasets/evals, CI/CD, package catalogs/signing e supply-chain controls | DÉLIA Model Governance/Control Tower | model/marketplace foundation inventory | PLANNED |
| CP-311 | C0 congela Recurring Governed Work: owner da definição versus owner do timer/scheduler físico, recurrence/timezone/DST, misfire/missed-run, overlap, idempotência por ocorrência, background identity/AuthZ/revoke, pause/cancel e Outcome boundaries | DÉLIA Work/Architecture/Automation/Security | recurring-work foundation contract | PLANNED |

## 3. C1 — Standalone Application Bootstrap

| ID | Requisito | Owner | Gate | Status |
|---|---|---|---|---|
| CP-141 | DÉLIA API standalone | `delia-api/` (FROZEN_ACCEPTED C0.S1; was `minha-delpi-copilot-api`) | own service/health/tests | LOCKED |
| CP-142 | DÉLIA MFE standalone | `plugins/delia/` (FROZEN_ACCEPTED C0.S1; was `plugins/minha-delpi-copilot`) | build/federation/tests | LOCKED |
| CP-143 | Manifesto próprio da DÉLIA | DÉLIA/Core (`id=delia`) | schema/registration | LOCKED |
| CP-144 | Gateway route própria API/MFE | Gateway (`/apps/delia-api/`, `/apps/delia`) | dev/prod parity | LOCKED |
| CP-145 | Compose/deploy próprios | Infra (`delpi-delia-api`, `delpi-delia`) | independent service/start | LOCKED |
| CP-148 | Portal federated full-page mount | Portal/DÉLIA MFE | authorized mount/F5 | LOCKED — C2-T5 full-page AppHost preserved (same remote helpers) |
| CP-149 | Global DÉLIA panel usando o mesmo MFE/runtime | Portal/DÉLIA MFE | surface parity | LOCKED — current C2 uses the same federated DÉLIA MFE/runtime (`delia` / `./App`) for full-page and Companion Dock; Product Master live smoke accepted for the recorded Companion Dock scope (§6.57); remaining live residuals (route persistence, close/reopen, full-page transition, User A/B, portal logout E2E) stay explicit |
| CP-150 | JWT + Core/RBAC integration | DÉLIA API/Core | auth negatives | LOCKED |
| CP-152 | Health + independent rollback/shutdown | DÉLIA/Infra | Chat-offline rollback | LOCKED |
| CP-153 | Reuso obrigatório de `@delpi/plugin-ui`/shared federation | DÉLIA MFE | federation/UI conformance | LOCKED |
| CP-155 | Entry point da DÉLIA amplamente disponibilizável conforme acesso/rollout | Portal/Core/DÉLIA MFE | access/visibility gate | LOCKED — companion handle and normal app entry only if `/me/apps` contains `id=delia`; no special sidebar launcher |

## 4. C2 — Portal Context + Platform Commands

| ID | Requisito | Owner | Gate | Status |
|---|---|---|---|---|
| CP-001 | DÉLIA global no Portal | DÉLIA MFE + Portal | panel/full-page UX | LOCKED — current C2 implementation uses the approved non-modal Companion Dock; Product Master live smoke accepted for the recorded scope; C2_EXECUTED=NO |
| CP-002 | Abrir app | Portal/CopilotBridge | authorized navigation | LOCKED |
| CP-003 | Abrir rota | Portal/CopilotBridge | authorized navigation | LOCKED |
| CP-004 | Abrir entidade | Portal + app contract | EntityRef/deep-link | LOCKED |
| CP-005 | Voltar/navegar histórico | Portal | router behavior | LOCKED |
| CP-006 | Selecionar aba/focar view | Portal/MFE/Iframe | typed command | LOCKED |
| CP-007 | Aplicar filtro visual | MFE/Iframe + Portal | view contract | LOCKED |
| CP-008 | Contexto do app atual | Portal | WorkspaceContext | LOCKED |
| CP-009 | Contexto de entidade | MFE/Iframe | EntityRef | LOCKED |
| CP-010 | Contexto filtros/período | MFE/Iframe | stale/security | LOCKED |
| CP-011 | Context chips | DÉLIA MFE | UX/relevance | LOCKED |
| CP-012 | “Explique o que estou vendo” | DÉLIA API + Context | grounding | LOCKED |
| CP-025 | Deep link após execução | Portal/MFE | result navigation | LOCKED |
| CP-059 | Platform Capability Projection | Portal/DÉLIA API | Core authority | LOCKED |
| CP-061 | Abrir iframe `PORTAL_ONLY` | Portal/CopilotBridge | authorized navigation | LOCKED — DÉLIA applicability: DEFER_UNTIL_REAL_CONSUMER; Portal embedded-open primitive exists; DÉLIA implementation NONE |
| CP-062 | Handshake seguro Portal↔iframe | Portal/IframeBridge | security contract | LOCKED — platform evidence PARTIAL (origin + targetOrigin; no event.source, version, capability negotiation, correlation or typed timeout); not a proven secure handshake; not a DÉLIA contract |
| CP-063 | Workspace Context de iframe | IframeBridge | normalization | LOCKED — DÉLIA applicability: DEFER_UNTIL_REAL_CONSUMER; no iframe WorkspaceContext runtime |
| CP-064 | Comando visual genérico iframe | Portal/IframeBridge | declared capability | LOCKED — generic command bus DEFER; DELPI_NAVIGATE is NAVIGATION; DELPI_THEME is PRESENTATION; neither is a Business Action |
| CP-065 | Classificar iframe I0–I3 | Readiness | evidence | LOCKED — DÉLIA iframe class NOT_APPLICABLE_CURRENTLY (federated surfaces); other consumers may stay TO_INVENTORY where the child is outside the repo |
| CP-068 | Proibir Business Action via DOM/click | Portal/DÉLIA Policy | negative gate | LOCKED — DELIA_DOM_BUSINESS_ACTION=NONE; current C2 shell negative evidence PASS; not PASS for future ACT |
| CP-069 | SSO iframe sem token pelo bridge | Portal/App/Security | auth architecture | TO_INVENTORY — legacy Portal DELPI_AUTH token postMessage; DÉLIA pattern DO_NOT_COPY; target SSO without bearer token over a generic bridge is NOT_PROVEN |
| CP-070 | Observabilidade iframe bridge | Portal/Observability | trace/redaction | LOCKED — current bridge observability TO_INVENTORY / NOT_PROVEN |
| CP-156 | Paridade de RBAC/policy entre Global/Workspace/Meeting/Frontline | Portal/DÉLIA Policy | surface parity | LOCKED — current evidence is partial: full-page and Companion Dock share Core `/me/apps` and the same host AuthZ hints; Meeting/Frontline surfaces do not exist |
| CP-159 | Contexto operacional OP/máquina/produto/operação/posto usa WorkspaceContext + EntityRef | Portal/MFE/DÉLIA | operational context contract | LOCKED — inventory only; C2-T4/T4R1: OPERATIONAL_CONTEXT=TO_INVENTORY; no Workspace runtime after T5 |
| CP-171 | Device metadata não substitui identidade/autorização | Portal/DÉLIA Security | shared-device/context negative | LOCKED — requirement only; not a C2 device runtime |

## 5. C3 — Intelligence Core + Extended Foundations

| ID | Requisito | Owner | Gate | Status |
|---|---|---|---|---|
| CP-026 | RAG de procedimentos/documentos | DÉLIA Knowledge | grounding/security | LOCKED |
| CP-028 | Redigir e-mail/texto | DÉLIA capability | faithfulness | LOCKED |
| CP-053 | Send/stream parity | DÉLIA API/MFE | transport parity | LOCKED |
| CP-071 | Uma única DÉLIA sem seleção de agente | DÉLIA API/MFE | no agent runtime | LOCKED |
| CP-073 | Recuperação semântica de expertise | DÉLIA API | positive/sibling/negative | LOCKED |
| CP-074 | Composição multi-expertise | DÉLIA Planner | cross-domain | LOCKED |
| CP-078 | Multimodalidade sem agent dependency | DÉLIA Multimodal | attachment eval | LOCKED |
| CP-079 | Análise de desenho com provenance/confidence | DÉLIA + Engineering | multimodal eval | LOCKED |
| CP-083 | Projects/preferred expertise sem outro runtime | DÉLIA API | permission negative | TO_INVENTORY |
| CP-086 | Unknown Expertise Pack sem planner patch | DÉLIA API | generalization | LOCKED |
| CP-087 | Metamorphic rename de Expertise Pack | DÉLIA Evals | equivalence | LOCKED |
| CP-089 | Packs referência Qualidade + Engenharia | DÉLIA/domain owners | pilot evals | LOCKED |
| CP-151 | OpenAPI ingestion + Action Catalog próprios da DÉLIA | DÉLIA API | independent catalog/importer | LOCKED |
| CP-160 | Speech-to-text/text-to-speech baseline por ports/adapters quando priorizado | DÉLIA Media | voice eval/provider abstraction | LOCKED |
| CP-161 | Voice command preserva mesma RBAC/policy/Decision semantics do texto | DÉLIA Policy/Planner | modality parity | LOCKED |
| CP-162 | Camera/image Evidence com frame/region/confidence/limitations | DÉLIA Multimodal | visual evidence eval | LOCKED |
| CP-163 | Short-video ingestion com time-range provenance e bounded processing | DÉLIA Media | video eval/budget | LOCKED |
| CP-164 | Screen share bounded/consented sem virar DOM automation | DÉLIA MFE/Media/Security | screen-share safety | LOCKED |
| CP-177 | Visual finding não vira decisão oficial de qualidade por default | DÉLIA/Quality Policy | epistemic/quality negative | LOCKED |
| CP-184 | Face recognition/verification closed-set apenas para usuários enrolled e policy-approved | DÉLIA Biometric | positive/unknown/look-alike eval | LOCKED |
| CP-185 | Speaker recognition/diarization separado de STT e de autorização | DÉLIA Biometric/Media | speaker identity eval | LOCKED |
| CP-186 | Unknown/low-confidence permanece desconhecido ou requer confirmação; associação é corrigível | DÉLIA Biometric/MFE | confidence/correction gate | LOCKED |
| CP-187 | Liveness/anti-spoof obrigatório quando a finalidade exigir confiança adicional | DÉLIA Biometric/Security | replay/photo/deepfake eval | LOCKED |
| CP-200 | Internet Research usa search + safe fetch + SourceRef/EvidenceRef + freshness/provenance | DÉLIA Internet Research | grounded research eval | LOCKED |
| CP-201 | Connector runtime é provider-neutral; planner não contém branches Gmail/Outlook/WhatsApp | DÉLIA Connectors/Planner | provider generalization | LOCKED |
| CP-205 | Connector capabilities são semânticas/contract-driven e separadas de endpoints específicos | DÉLIA Capability/Connectors | capability contract gate | LOCKED |
| CP-215 | Teams é capability family do Microsoft 365 connector; planner não depende de Graph paths nem cria runtime Teams separado | DÉLIA Teams/Connectors/Planner | Teams provider-neutral architecture | LOCKED |
| CP-232 | DÉLIA suporta decision-path routing `FAST | OPERATIONAL | REASONING`; nem todo evento chama LLM | DÉLIA Intelligence/Policy | decision-path routing eval | LOCKED |
| CP-233 | Business readiness/anomaly material usa deterministic Policy/Specification sobre fatos autoritativos; LLM não é única autoridade da decisão | DÉLIA Policy/Domain owners | deterministic-decision gate | LOCKED |
| CP-250 | Process Intelligence usa EventLog/ProcessTrace contracts com case/activity/time/source/provenance e não inventa eventos ausentes | DÉLIA Process Intelligence | process-contract/conformance gate | LOCKED |
| CP-257 | AI Control Tower possui AI Asset Registry/projection com owner/version/risk/data scope/eval/status/dependencies/kill-switch refs sem duplicar owner truth | DÉLIA Control Tower | asset-registry contract gate | LOCKED |
| CP-263 | MCP/A2A entram por adapters/allowlists provider-neutral; discovery de server/agent nunca equivale a aprovação/permission | DÉLIA Interoperability/Security | tool-agent trust gate | LOCKED |
| CP-269 | Personal Memory possui classes/provenance/version/retention e write policy; conversation não cria memória material silenciosamente | DÉLIA Memory/Privacy | memory lifecycle gate | LOCKED |
| CP-275 | Semantic Business Layer possui MetricDefinition/Glossary versionados com formula/grain/dimensions/unit/owner/source/freshness/security | DÉLIA Semantic Layer | metric-definition contract gate | LOCKED |
| CP-281 | Analysis Sandbox é isolado, quota-bounded, sem host/network/secret access irrestrito, e recebe dados apenas via reads autorizados | DÉLIA Analysis/Security | sandbox isolation gate | LOCKED |
| CP-288 | Prediction/Prescription contracts preservam model/version/horizon/confidence/inputs/limitations e não promovem previsão a FACT | DÉLIA Predictive/Evidence | prediction semantics gate | LOCKED |
| CP-296 | Edge runtime usa device/package/model/cache contracts versionados; device identity nunca substitui user identity | DÉLIA Edge/Architecture | edge contract gate | LOCKED |
| CP-303 | Model Registry/projection cobre LLM/embedding/vision/speech/classifier/forecast/anomaly/optimization com owner/version/eval/risk/deployment/rollback metadata | DÉLIA Model Governance | model registry gate | LOCKED |

## 6. C4 — Business + External Reads + Graph + Intelligence Reads

| ID | Requisito | Owner | Gate | Status |
|---|---|---|---|---|
| CP-013 | Consultar Business Action | DÉLIA Action Runtime | read/RBAC/outcome | LOCKED |
| CP-014 | Consultar múltiplas APIs | DÉLIA Planner | multi-provider | LOCKED |
| CP-015 | Analisar/comparar dados | DÉLIA synthesis | grounded evidence | LOCKED |
| CP-027 | Gerar resumo/relatório grounded | DÉLIA Artifact | evidence/faithfulness | LOCKED |
| CP-029 | Recomendar próximos passos | DÉLIA synthesis | contextual/allowed | LOCKED |
| CP-043 | Unknown OpenAPI provider | DÉLIA API | full-chain unknown | LOCKED |
| CP-044 | Metamorphic provider/path/opId | DÉLIA Evals | metamorphic | LOCKED |
| CP-058 | Business Capability Projection | DÉLIA API | no duplicate authority | LOCKED |
| CP-090 | DELPI Business Graph mínimo | DÉLIA Graph/domain owners | permission traversal | LOCKED |
| CP-128 | Business Graph sibling onboarding | DÉLIA Graph | no planner hardcode | LOCKED |
| CP-202 | External reads suportam fontes conectadas autorizadas sem vazar dados entre usuários/conexões | DÉLIA Connectors/Privacy | read isolation gate | LOCKED |
| CP-206 | Todo external read material gera SourceRef/EvidenceRef com provider/resource/scope/freshness | DÉLIA Evidence/Connectors | provenance gate | LOCKED |
| CP-216 | Teams reads suportam teams/channels/chats/messages/replies e meeting metadata somente dentro dos scopes/resources autorizados | DÉLIA Teams/Privacy | Teams read isolation gate | LOCKED |
| CP-219 | Transcript/recording/meeting artifact do Teams preserva SourceRef/EvidenceRef, meeting resource, provenance, permission scope, freshness/version e retention policy | DÉLIA Teams/Meeting/Evidence | Teams meeting provenance gate | LOCKED |
| CP-225 | Identidade de participante resolvida pelo Teams/tenant é primária quando authoritative; biometria é somente evidência suplementar governada | DÉLIA Teams/Biometric/Identity | participant identity precedence gate | LOCKED |
| CP-234 | Operational readiness/anomaly evaluation correlaciona Domain reads/Graph/Evidence e produz resultado read-only antes de qualquer side effect | DÉLIA Operational Intelligence/Domain owners | read-only decision evidence gate | LOCKED |
| CP-251 | Process Mining reconstrói variants/bottlenecks/conformance somente de event logs autorizados; ausência/incompletude permanece explícita | DÉLIA Process Intelligence | read-only process mining eval | LOCKED |
| CP-264 | MCP/A2A read-only tools/agents preservam tool/agent provenance, data minimization, timeout/cancellation e não recebem contexto irrestrito | DÉLIA Interoperability | read-only delegation gate | LOCKED |
| CP-270 | Personalization prioriza conteúdo/formatos usando memória, mas live domain/source facts continuam authority e stale memory não os substitui | DÉLIA Memory/Planner | personalization authority gate | LOCKED |
| CP-276 | Semantic Query resolve métrica governada e calcula por definição estruturada/reprodutível; LLM não inventa fórmula empresarial material | DÉLIA Semantic Layer/Analytics | governed metric query gate | LOCKED |
| CP-282 | Sandbox executa análise read-only reproduzível com SourceRefs/runtime/code hash/parameters e não permite DDL/DML por connector analítico read-only | DÉLIA Analysis | reproducible analysis gate | LOCKED |
| CP-289 | Predictive reads mostram model/version/horizon/freshness/calibration/limitations e degradam explicitamente em stale/OOD/unavailable | DÉLIA Predictive | predictive read eval | LOCKED |
| CP-297 | Edge read-only/offline cache preserva source revision/syncedAt/freshness e sinaliza ou bloqueia conteúdo stale conforme criticidade | DÉLIA Edge/Frontline | offline freshness gate | LOCKED |
| CP-304 | Uso de modelo material gera lineage suficiente para ligar prediction/result ao model/version/eval/deployment ref sem expor segredo | DÉLIA Model Governance/Evidence | model lineage gate | LOCKED |

## 7. C5 — Governed ACT + Durable Work + Prepared Intelligence

C5 é o primeiro gate que pode liberar `ACT` material governado. Segundo `08-security-autonomy-audit.md`, `L3 = prepare`, `L4 = governed execute` e `L5 = allowlisted autonomous execute within explicit limits`.

Portanto:

```text
L3 PREPARE = no side effect
L4 GOVERNED EXECUTE = C5-capable when capability is explicitly authorized and all gates pass
L5 AUTONOMOUS EXECUTE = C7 only, OFF by default
```

| ID | Requisito | Owner | Gate | Status |
|---|---|---|---|---|
| CP-016 | Criar registro | Domain API + DÉLIA executor | Decision/RBAC/outcome | LOCKED |
| CP-017 | Editar registro | Domain API + DÉLIA executor | write parity | LOCKED |
| CP-018 | Aprovar/rejeitar | Domain API/DÉLIA Policy | approval/safety | LOCKED |
| CP-019 | Cancelar/arquivar | Domain API/DÉLIA Policy | destructive gate | LOCKED |
| CP-020 | Adicionar comentário | Domain API | write parity | LOCKED |
| CP-021 | Atribuir responsável | Domain API | permission/gate | LOCKED |
| CP-022 | Preview de write | DÉLIA API/MFE | argsHash/impact | LOCKED |
| CP-023 | Decision/confirmation UI | DÉLIA MFE/API | Decision Gate | LOCKED |
| CP-024 | Revalidar após decisão | DÉLIA Policy/Executor | TOCTOU | LOCKED |
| CP-030 | Plano operacional visível | DÉLIA API/MFE | no CoT/activity | LOCKED |
| CP-031 | Workflow multi-app | DÉLIA Work Runtime | compound outcome | LOCKED |
| CP-032 | Parallel safe reads | DÉLIA Work Runtime | safety | LOCKED |
| CP-033 | Dependências entre steps | DÉLIA Work Runtime | DAG | LOCKED |
| CP-034 | Partial failure truthful | DÉLIA Work Runtime | outcome | LOCKED |
| CP-035 | Retry seguro | DÉLIA Work Runtime | idempotency | LOCKED |
| CP-036 | Pause por decisão | DÉLIA Work/Decision | persistence | LOCKED |
| CP-037 | Reload/resume | DÉLIA Work Persistence | no duplicate write | LOCKED |
| CP-038 | Audit trail workflow | DÉLIA Observability | coverage | LOCKED |
| CP-045 | Autonomia L0–L2 | DÉLIA Policy | safe reads/navigation/prepare | LOCKED |
| CP-046 | Autonomia L3 prepare | DÉLIA Policy/Work | PREPARE no-side-effect semantics | LOCKED |
| CP-047 | Autonomia L4 governed execute | DÉLIA Policy/Work | live AuthZ + Decision Gate + idempotency/audit + verified Outcome | LOCKED |
| CP-054 | Simulate/admin preview de action | DÉLIA Admin | parity | LOCKED |
| CP-076 | Playbook→WorkflowPlan sem endpoint hardcoded | DÉLIA Planner | authority separation | LOCKED |
| CP-168 | Candidate action de voz/reunião/frontline exige transition governada antes de write | DÉLIA Policy/Work | Decision/idempotency | LOCKED |
| CP-203 | External write/send/create/update é capability distinta de read e exige policy/Decision/outcome verification | DÉLIA External Actions | external write gate | LOCKED |
| CP-204 | Draft/preview é separado de send; mensagem sugerida nunca é enviada implicitamente | DÉLIA Communication/MFE | draft-send separation | LOCKED |
| CP-217 | Teams reply/send são capabilities governadas distintas de read/draft, com target preview, policy/Decision Gate e verified outcome | DÉLIA Teams/External Actions | Teams write gate | LOCKED |
| CP-235 | Automation Capability Registry/Projection mapeia capability semântica a executor versionado sem expor clicks/seletores/provider UI ao planner | DÉLIA Automation/Capability | executor abstraction gate | LOCKED |
| CP-236 | API/Function/RPA/Computer-Use executors implementam Port+Adapter substituível; RPA não é authority de business rule | DÉLIA Automation/Architecture | executor substitution gate | LOCKED |
| CP-237 | AutomationExecution possui lifecycle/correlation/inputHash/attempt/idempotency/timeout/error/outcome refs e impede dupla execução após retry/resume | DÉLIA Automation/Work | execution lifecycle gate | LOCKED |
| CP-238 | RPA worker/queue execution, quando priorizada, possui worker health/lease/concurrency/environment/package-version/credential isolation/audit | DÉLIA RPA/Infrastructure/Security | RPA execution reliability gate | LOCKED |
| CP-239 | Sucesso técnico do executor não equivale a sucesso de negócio; ação material exige postcondition/Outcome verification quando aplicável | DÉLIA Automation/Domain owners | verified business outcome gate | LOCKED |
| CP-240 | Notification/escalation deriva de estado/outcome verdadeiro e não é usada como prova de sucesso da execução | DÉLIA Notifications/Automation | truthful notification gate | LOCKED |
| CP-252 | Oportunidade descoberta por Process Intelligence vira candidate/Task/PREPARE com Evidence; nunca cria RPA/automation ativa automaticamente | DÉLIA Process Intelligence/Automation | opportunity governance gate | LOCKED |
| CP-265 | MCP/A2A tool/agent com write capability passa pela mesma Policy/Decision/idempotency/Outcome verification das Business/External Actions | DÉLIA Interoperability/Policy | delegated write gate | LOCKED |
| CP-277 | Métrica/semantic rule usada em Decision/Write é versionada e revalidada; mudança material invalida decisão anterior quando aplicável | DÉLIA Semantic Layer/Decision | semantic TOCTOU gate | LOCKED |
| CP-283 | Artifact Workspace possui artifact version/lifecycle/provenance/ACL e external share/send continua ação governada separada | DÉLIA Artifacts/Work | artifact lifecycle/share gate | LOCKED |
| CP-290 | Prescriptive output gera alternatives/trade-offs/PREPARE; `recommendation != authorization` e `simulate != apply` | DÉLIA Prescriptive/Decision | prescriptive action separation gate | LOCKED |
| CP-312 | Usuário/owner autorizado pode criar, inspecionar/listar, pausar, retomar e cancelar Recurring Governed Work persistente com recurrence versionada, timezone IANA, start/end bounds e refs bounded para Work/capabilities/scope/targets | DÉLIA Work/API | recurring-work lifecycle gate | LOCKED |
| CP-313 | Cada ocorrência agendada é determinística, correlacionada e idempotente; duplicate tick/retry/restart/reconciliation não duplica side effect e misfire/overlap semantics são explícitas | DÉLIA Work/Events/Automation | scheduled-occurrence reliability gate | LOCKED |
| CP-314 | Cada ocorrência material revalida identity, live Core/domain AuthZ, current Policy/Decision, connection/provider state e source permissions; `schedule != permission` e stored intent nunca vira autorização eterna | DÉLIA Work/Policy/Core/Domain owners | scheduled live-authorization gate | LOCKED |
| CP-315 | Anchor recurring report→send executa sem sessão de chat aberta: trigger determinístico → reads atuais → relatório grounded/versionado → `communication.email.send` governado → Outcome/Evidence/Audit, sem confundir report generated, provider accepted e verified outcome | DÉLIA Work/Artifacts/External Actions | recurring report-email end-to-end gate | LOCKED |

## 8. C6 — Product Work + Ecosystem + Human Experience

C6 habilita Product Work e Watch `OBSERVE|ADVISE|PREPARE` por default. `PREPARE` não produz side effect e Watch não dispara ACT autonomamente nesta fase. Isso não revoga L4 governed execute de C5 quando uma capability é explicitamente invocada/autorizada e passa novamente pelos gates materiais.

| ID | Requisito | Owner | Gate | Status |
|---|---|---|---|---|
| CP-039 | AI-ready SDK/templates | Shared/Portal/DÉLIA | contracts | LOCKED |
| CP-040 | Readiness scanner | DÉLIA Tooling | factual inventory | LOCKED |
| CP-041 | Coverage dashboard | DÉLIA Admin/Observability | metrics | LOCKED |
| CP-042 | Unknown app onboarding | Core/Portal/DÉLIA | no hardcode | LOCKED |
| CP-060 | Admin de capabilities/coverage | DÉLIA Admin | admin RBAC | LOCKED |
| CP-066 | Iframe DÉLIA Bridge SDK | Shared/Portal | contract/lifecycle | LOCKED |
| CP-067 | Unknown iframe onboarding | Portal/IframeBridge | generalization | LOCKED |
| CP-084 | Admin/observability packs/playbooks | DÉLIA Admin | version/eval/audit | LOCKED |
| CP-096 | DÉLIA Task persistente | DÉLIA Work | restart/resume | LOCKED |
| CP-097 | DÉLIA Case | DÉLIA Work/Product | lifecycle/evidence | LOCKED |
| CP-098 | Evidence Board | DÉLIA Case | same EvidenceRef | LOCKED |
| CP-099 | Interaction Room ligada a Case | DÉLIA + room owner | RBAC/context | TO_INVENTORY |
| CP-100 | DÉLIA Inbox | DÉLIA Work/MFE | lifecycle | LOCKED |
| CP-101 | Watch por condição/evento | DÉLIA Work/Events | dedupe/RBAC | LOCKED |
| CP-102 | Watch OBSERVE | DÉLIA Work | audit | LOCKED |
| CP-103 | Watch ADVISE | DÉLIA Work/AI | grounded alert | LOCKED |
| CP-114 | Reference Knowledge lifecycle | DÉLIA Knowledge | owner/version/scope | LOCKED |
| CP-115 | Decision Knowledge | DÉLIA Case/Knowledge | provenance/no-CoT | LOCKED |
| CP-116 | Experience Knowledge | DÉLIA Case/Knowledge | governed promotion | LOCKED |
| CP-117 | Solution Pattern lifecycle | DÉLIA Knowledge/Expertise | review/eval/version | LOCKED |
| CP-118 | Governed Learning Loop | DÉLIA Admin | no auto-publish | LOCKED |
| CP-119 | Expertise Studio lifecycle | DÉLIA Admin | draft→publish | LOCKED |
| CP-120 | Expertise/Playbook rollback | DÉLIA Admin | version/eval | LOCKED |
| CP-124 | Task Completion metric | DÉLIA Observability | metric validity | LOCKED |
| CP-125 | Case resolution learning candidate | DÉLIA Case/Knowledge | candidate only | LOCKED |
| CP-126 | Inbox decision→workflow resume | DÉLIA MFE/Work | correlation | LOCKED |
| CP-127 | Room summary grounded em Case | DÉLIA/Room | evidence/RBAC | TO_INVENTORY |
| CP-165 | Meeting Mode com lifecycle explícito de captura | DÉLIA MFE/API | explicit start/stop/indicators | LOCKED |
| CP-166 | Meeting consulta dados reais com permissões do usuário | DÉLIA API/Domain APIs | meeting read parity | LOCKED |
| CP-167 | Ata viva distingue transcript/resumo/decisão/action/outcome | DÉLIA Meeting/Artifact | semantic/evidence gate | LOCKED |
| CP-169 | Frontline Mode no mesmo MFE/API | DÉLIA MFE/API | frontline surface parity | LOCKED |
| CP-170 | Hands-free voice com fallback touch/text | DÉLIA Frontline | noisy/permission/accessibility tests | LOCKED |
| CP-172 | Training assistance referencia procedimento/desenho/revisão vigente | DÉLIA Knowledge/Domain owners | source freshness | LOCKED |
| CP-173 | Observação de processo gera somente Knowledge/Experience candidate | DÉLIA Knowledge | candidate provenance | LOCKED |
| CP-174 | Meeting/frontline candidate exige review/eval antes de virar conhecimento publicado | DÉLIA Knowledge/Expertise | governed learning | LOCKED |
| CP-181 | Meeting/Frontline accessibility e large-touch/shared-device UX | DÉLIA MFE | accessibility/frontline gate | LOCKED |
| CP-191 | Meeting pode associar face/voz enrolled a participante com confidence/correção | DÉLIA Meeting/Biometric | participant identity gate | LOCKED |
| CP-192 | Frontline pode usar biometria para identity assistance sem substituir sessão/RBAC | DÉLIA Frontline/Biometric | shared-device identity gate | LOCKED |
| CP-193 | Human Observation analisa somente padrões operacionais observáveis com Evidence/provenance | DÉLIA Frontline/Knowledge | process observation gate | LOCKED |
| CP-207 | Provider push/webhook/subscription normaliza para EventEnvelope com authenticity/dedupe/reconciliation | DÉLIA Connectors/Events | webhook lifecycle gate | LOCKED |
| CP-208 | External source só vira user/org Knowledge por candidate→review/eval/publish; nunca auto-truth | DÉLIA Knowledge/Governance | external learning gate | LOCKED |
| CP-212 | Personal connection data não vira shared Knowledge/Case/Room sem sharing/promotion explícito | DÉLIA Privacy/Knowledge | personal-data isolation gate | LOCKED |
| CP-213 | Subscription expiry/missed events/revocation exigem renewal/reconciliation/degraded state truthful | DÉLIA Connectors/Work | external event reliability gate | LOCKED |
| CP-218 | Teams change notifications de mensagens/canais/reuniões/transcrições/gravações, quando suportadas, entram por autenticidade→EventEnvelope→dedupe/reconciliation | DÉLIA Teams/Events | Teams event lifecycle gate | LOCKED |
| CP-220 | Teams meeting artifacts podem alimentar ata viva, Evidence, Task, Case, Room e Watch sem transformar transcript em decisão/ação automática | DÉLIA Teams/Meeting/Work | Teams meeting-to-work gate | LOCKED |
| CP-221 | App/tab/bot da DÉLIA no Teams, quando implementado, usa a mesma DÉLIA API, Core/RBAC, Policy, Evidence e Work runtime; nenhum `teams-copilot-api` paralelo | DÉLIA Teams/MFE/Platform | same-runtime surface gate | LOCKED |
| CP-224 | Chat privado, canal restrito, transcript e recording do Teams preservam source ACL; não viram shared Knowledge/Case/Room sem autorização/promotion explícita | DÉLIA Teams/Privacy/Knowledge | Teams private-resource isolation gate | LOCKED |
| CP-241 | Watch suporta `PREPARE` como estado/mode distinto de `ACT`, permitindo preparar ação sem side effect | DÉLIA Watch/Work/Policy | prepare-vs-act gate | LOCKED |
| CP-242 | Automation Hub Admin expõe automations/executions/workers/exceptions, owner/version/executor/status/outcome/evidence sem virar segundo workflow engine | DÉLIA Automation Admin/MFE/API | admin ownership/observability gate | LOCKED |
| CP-243 | Event-driven notification/escalation usa recipients/severity/dedupe/SLA/channel policy e pode combinar Minha DELPI/email/Teams/WhatsApp Business | DÉLIA Notifications/Watch | notification orchestration gate | LOCKED |
| CP-244 | Manual exception/human-in-the-loop pausa e retoma o mesmo Durable Workflow; não cria processo paralelo sem correlation | DÉLIA Work/Inbox/Decision | HITL resume gate | LOCKED |
| CP-253 | Process Intelligence UX expõe process map/variants/bottlenecks/conformance/automation backlog e before-after metrics com Evidence | DÉLIA Process Intelligence/MFE | process product gate | LOCKED |
| CP-258 | AI Control Tower oferece inventory/ownership/risk/health/eval/cost/value/incidents/dependencies/kill-switch UX sem conceder business permission | DÉLIA Control Tower/Admin | control-tower governance gate | LOCKED |
| CP-266 | MCP/A2A servers/agents possuem lifecycle `DISCOVERED→REVIEWED→APPROVED→ACTIVE→DISABLED/REVOKED` e health/usage no Control Tower | DÉLIA Interoperability/Control Tower | agent-tool lifecycle gate | LOCKED |
| CP-271 | Usuário possui controles para inspecionar/corrigir/apagar/desabilitar Personal Memory e recebe briefing personalizado grounded em authorities live | DÉLIA Memory/MFE | user memory control gate | LOCKED |
| CP-278 | Semantic Layer possui catalog/admin/lineage/conflict UX; mesma label com definições distintas não é fundida silenciosamente | DÉLIA Semantic Layer/Admin | semantic governance UX gate | LOCKED |
| CP-284 | Artifact Workspace suporta draft/review/version/collaboration/attach/export sem sobrescrever silenciosamente edição humana | DÉLIA Artifacts/MFE/Work | artifact collaboration gate | LOCKED |
| CP-291 | Operational Twin/Scenario Workspace mantém simulated state separado de production state e permite comparar alternativas com assumptions/Evidence | DÉLIA Twin/MFE | scenario isolation gate | LOCKED |
| CP-298 | Frontline Edge suporta modos `ONLINE/DEGRADED/OFFLINE_READ_ONLY/SYNCING`, event buffering idempotente e device/cache admin quando priorizado | DÉLIA Edge/Frontline | edge offline product gate | LOCKED |
| CP-305 | Capability Marketplace oferece lifecycle draft/review/approved/published/deprecated/revoked para packs/playbooks/Watches/automations/connectors/MCP/A2A/templates/models | DÉLIA Marketplace/Admin | marketplace lifecycle gate | LOCKED |
| CP-306 | Model lifecycle monitora quality/input/calibration drift, latency, availability, cost e correction/outcome metrics conforme model type | DÉLIA Model Governance/Observability | model drift gate | LOCKED |
| CP-316 | Product UX permite inspecionar Recurring Governed Work com status, recurrence/timezone, next scheduled occurrence quando derivável, last occurrence/outcome e ações governadas pause/resume/cancel, sem transformar schedule admin em permission authority | DÉLIA Work/MFE/Admin | recurring-work product UX gate | LOCKED |

## 9. C7 — Advanced Autonomy + Advanced Intelligence + Scale/Rollout

C7 não cria o conceito de ACT. Ele habilita autonomia avançada sobre capabilities já governadas, incluindo `L5` e selected Watch autonomous ACT.

| ID | Requisito | Owner | Gate | Status |
|---|---|---|---|---|
| CP-048 | Autonomia L5 limitada | DÉLIA Policy/Admin | allowlist/limits/kill switch | LOCKED |
| CP-049 | Emergency stop | DÉLIA Admin/Policy | kill switch | LOCKED |
| CP-050 | Rollout/cohort controls | Platform/DÉLIA Admin | canary/rollback | LOCKED |
| CP-052 | TCR/First Plan Success metrics | DÉLIA Observability | metric validity | LOCKED |
| CP-104 | Watch ACT | DÉLIA Policy/Work | autonomous trigger + autonomy/Decision | LOCKED |
| CP-112 | What-if Simulation | Domain analytics/DÉLIA | reproducible model | LOCKED |
| CP-113 | Simulate→Apply separado | Domain API/DÉLIA Policy | new gate | LOCKED |
| CP-121 | Model Router | DÉLIA Infrastructure | quality/cost/latency | LOCKED |
| CP-122 | Compute Policy | DÉLIA Policy | provider constraints | LOCKED |
| CP-129 | Anchor reclamação→8D→Watch→ação | Cross-domain/DÉLIA | full integration | LOCKED |
| CP-180 | Advanced realtime media possui budgets/backpressure/degraded mode/cost telemetry | DÉLIA Media/Infra | realtime reliability gate | LOCKED |
| CP-222 | Participação Teams ao vivo com raw realtime media só entra após evidence + ADR + tenant/media/privacy/cost/reliability gates; não é requisito do conector base | DÉLIA Teams/Realtime/Architecture | Teams advanced realtime gate | LOCKED |
| CP-245 | Autonomy level é resolvido por capability/context/risk/actor/limits/environment; não existe L4/L5 global irrestrito | DÉLIA Autonomy Policy | capability-scoped autonomy gate | LOCKED |
| CP-246 | L5 permanece OFF por default e exige allowlist, budgets/limits, kill switch, revalidation e verified Outcome por capability | DÉLIA Policy/Admin/Automation | autonomous ACT gate | LOCKED |
| CP-247 | Computer-use/UI automation é fallback avançado sandboxed/allowlisted/auditado e não substitui API/RPA determinístico sem justificativa | DÉLIA Automation/Security | computer-use boundary gate | LOCKED |
| CP-248 | Anchor autonomous operation `ready-to-invoice → execute → verify → notify` funciona end-to-end sob policy sem user prompt quando capability L5 estiver explicitamente aprovada | DÉLIA Automation/Cross-domain | autonomous invoicing anchor gate | LOCKED |
| CP-254 | Closed-loop process optimization nunca altera processo/policy automaticamente; autonomous ACT exige capability-scoped autonomy e before/after measurement | DÉLIA Process Intelligence/Automation | process closed-loop gate | LOCKED |
| CP-259 | AI Control Tower aplica cross-runtime budgets/cohorts/kill switches/rollback e incident containment por asset/capability sem prompt authority | DÉLIA Control Tower/Governance | mature AI governance gate | LOCKED |
| CP-267 | Autonomous A2A delegation exige approved agent/capability, bounded goal/context/budget, cancellation, verified result e L5 allowlist quando material | DÉLIA Interoperability/Autonomy | autonomous delegation gate | LOCKED |
| CP-272 | Advanced personalization optimization não cria hidden employee score, sensitive inference ou authority; user privacy/control permanece | DÉLIA Memory/Privacy | personalization optimization gate | LOCKED |
| CP-279 | Semantic federation/materialization optimization preserva owner/permission/freshness/lineage; cache nunca vira authority | DÉLIA Semantic Layer/Infrastructure | semantic scale gate | LOCKED |
| CP-285 | Scaled sandbox pools mantêm isolation/quotas/reproducibility/cleanup e não se tornam general-purpose corporate shell | DÉLIA Analysis/Infrastructure | sandbox scale gate | LOCKED |
| CP-286 | Advanced artifact generation/templates permanecem versioned/provenanced e publish/share continua policy-governed | DÉLIA Artifacts/Marketplace | artifact scale gate | LOCKED |
| CP-292 | Operational Twin avançado preserva source/freshness e cenário isolado; twin não vira OT/domain master | DÉLIA Twin/Domain owners | twin authority gate | LOCKED |
| CP-293 | Predictive/prescriptive output pode acionar ACT somente por explicit Policy/Decision/autonomy e verified Outcome; model output sozinho nunca autoriza | DÉLIA Predictive/Autonomy | prescriptive autonomy gate | LOCKED |
| CP-294 | `SIMULATE != APPLY`: qualquer Apply revalida live state/permissions/policy e gera novo action/decision context | DÉLIA Simulation/Decision | simulate-apply TOCTOU gate | LOCKED |
| CP-299 | Edge rollout escala por device class/cohort com signed/versioned packages/models, health e rollback | DÉLIA Edge/Control Tower | edge rollout gate | LOCKED |
| CP-300 | Offline bounded actions, se existirem, exigem explicit allowlist/expiry/idempotency/reconciliation; perda de cloud nunca amplia authority | DÉLIA Edge/Policy | offline action gate | LOCKED |
| CP-301 | Edge revocation/model/package update é rastreável e stale/revoked artifact deixa de ser usado no enforcement point definido | DÉLIA Edge/Model Governance | edge revocation gate | LOCKED |
| CP-307 | Production model deployment possui approved environment/cohort/health/rollback/kill switch e revoked model não é selecionável | DÉLIA Model Governance/Control Tower | model deployment gate | LOCKED |
| CP-308 | Marketplace publish/enable exige manifest/dependencies/permissions/data scopes/evals/compatibility e não concede RBAC/provider scope sozinho | DÉLIA Marketplace/Security | marketplace enable gate | LOCKED |
| CP-309 | Executable/model/connector packages usam supply-chain controls apropriados: trusted publisher, hash/signature when applicable, dependency/license/vulnerability review e revoke path | DÉLIA Marketplace/Security | AI supply-chain gate | LOCKED |
| CP-310 | Nenhum Model/Marketplace/MCP/A2A/Edge asset pode ampliar Core/domain/provider authority por instalação, prompt, metadata ou package manifest | DÉLIA Security/Governance | no asset permission elevation gate | LOCKED |

## 10. Requisitos históricos do Chat — fora do escopo DÉLIA

| ID | Requisito histórico | Decisão | Status |
|---|---|---|---|
| CP-080 | Migrar presets de `AgentSpecializationService` | pertence ao Chat; DÉLIA cria Expertise nativa | OUT_OF_SCOPE_WITH_DECISION |
| CP-081 | Remover `userActivatedAgent` do Chat | pertence ao Chat | OUT_OF_SCOPE_WITH_DECISION |
| CP-082 | Remover soft agent handoff do Chat | pertence ao Chat | OUT_OF_SCOPE_WITH_DECISION |
| CP-085 | Remover routing legado `agent_id` do Chat | pertence ao Chat | OUT_OF_SCOPE_WITH_DECISION |

Esses IDs não podem ser reativados como dependência da DÉLIA.

## 11. Regras de atualização

- requisito novo recebe novo CP-ID;
- nenhum CP vira PASS por documentação apenas;
- runtime só passa com wiring + integration/eval;
- `TO_INVENTORY` não vira PLANNED por suposição;
- requisito removido recebe `OUT_OF_SCOPE_WITH_DECISION`;
- nenhum requisito DÉLIA pode ser bloqueado por refactor do Chat;
- shared reuse precisa ser platform-neutral;
- phase canonical é C0–C7 do `16`;
- `L3 = PREPARE`, sem side effect;
- `L4 = governed execute`; C5 pode liberar ACT material explicitamente autorizado sob live AuthZ/Decision/idempotency/audit/Outcome;
- `L5 = allowlisted autonomous execute within explicit limits`; permanece C7 e OFF por default;
- Watch autonomous ACT permanece C7; Watch C6 é `OBSERVE|ADVISE|PREPARE` por default;
- Recurring Governed Work temporal não é Watch autônomo: C5 pode executar ocorrência L4 bounded, mas `schedule != permission` e cada ocorrência material revalida live AuthZ/Policy/Decision;
- timer/scheduler físico continua `TO_INVENTORY` até C0 provar owner/contrato; isso não rebaixa a capability de produto Recurring Governed Work;
- modality/biometric result não pode criar bypass de RBAC/policy;
- biometric identity é candidate association, não permission authority;
- Human Observation não pode virar inferência psicológica/sensível ou decisão trabalhista automática;
- Internet/connected-source content é untrusted data e não authority de policy;
- OAuth/provider scopes não substituem Core/domain authorization;
- personal connection data não pode vazar para outro usuário ou virar conhecimento organizacional automaticamente;
- `draft != send`; external write exige governance e verified outcome;
- Teams é capability family do Microsoft 365 connector e não novo runtime;
- Teams source ACL/tenant/resource scope permanecem obrigatórios em Evidence/Knowledge/Work;
- Teams live raw-media participation é advanced capability, nunca pré-requisito do conector base;
- DÉLIA decide/orquestra; executors executam por capabilities semânticas;
- API é preferida a RPA/computer-use quando contract autoritativo existir;
- evento nunca concede autorização nem side effect por si só;
- deterministic Policy/Specification governa readiness material quando facts/rules suportam a decisão;
- technical execution success não substitui verified business Outcome;
- autonomy é capability/context/risk scoped;
- Process Mining mede processo e não vira worker surveillance;
- Control Tower governa assets; não concede business permission;
- MCP/A2A/tool metadata são untrusted integration data;
- Personal Memory não é Organizational Knowledge nem business truth;
- Semantic Layer define significado/cálculo, Business Graph define relações;
- Analysis Sandbox é isolado e read-only por default;
- prediction != fact; recommendation != authorization; simulate != apply;
- Edge/offline não amplia autoridade por falta de conectividade;
- Marketplace/model package não concede permission;
- OT physical actuation não é inferida a partir de autonomia L5.

## 12. Coverage final

```text
TOTAL_REQUIREMENTS
PASS
LOCKED/BLOCKED
FAIL
OUT_OF_SCOPE_WITH_DECISION
UNMAPPED
```

Famílias:

```text
STANDALONE_FOUNDATION
ARCHITECTURE_PATTERNS
PORTAL_CONTEXT
INTELLIGENCE
MULTIMODAL_MEDIA
BIOMETRIC_IDENTITY
HUMAN_OBSERVATION
INTERNET_RESEARCH
EXTERNAL_CONNECTORS
EXTERNAL_EVENTS
EXTERNAL_COMMUNICATION
EXTERNAL_KNOWLEDGE
MICROSOFT_TEAMS
TEAMS_MEETING_INTEGRATION
EVENT_DRIVEN_OPERATIONS
DECISION_INTELLIGENCE
AUTOMATION_EXECUTION_HUB
RECURRING_GOVERNED_WORK
RPA_EXECUTION
COMPUTER_USE
OUTCOME_VERIFICATION
CAPABILITY_SCOPED_AUTONOMY
PROCESS_INTELLIGENCE
AI_CONTROL_TOWER
AGENT_INTEROPERABILITY_MCP_A2A
PERSONAL_MEMORY_PERSONALIZATION
SEMANTIC_BUSINESS_LAYER
ANALYSIS_SANDBOX
ARTIFACT_WORKSPACE
PREDICTIVE_PRESCRIPTIVE_INTELLIGENCE
OPERATIONAL_TWIN
EDGE_OFFLINE_COPILOT
AI_MODEL_LIFECYCLE
CAPABILITY_MARKETPLACE
MEETING
FRONTLINE
PRIVACY_SHARED_DEVICE
INDUSTRIAL_OT_SAFETY
BUSINESS_READS_GRAPH
GOVERNED_WRITES_DURABLE
PRODUCT_WORK_PROACTIVITY
AUTONOMY_OPTIMIZATION
IFRAME
EXPERTISE
EVIDENCE
```

`UNMAPPED = 0` para qualquer release declarado completo.

## 13. Requirement ranges

```text
CP-194–CP-214  Internet Research / External Connectors
CP-215–CP-225  Microsoft Teams
CP-226–CP-248  Autonomous Operations / Automation Hub
CP-249–CP-255  Process Intelligence / Process Mining
CP-256–CP-261  AI Control Tower
CP-262–CP-267  MCP/A2A / Agent Interoperability
CP-268–CP-273  Personal Memory / Personalization
CP-274–CP-279  Semantic Business Layer
CP-280–CP-286  Analysis Sandbox / Artifact Workspace
CP-287–CP-294  Predictive/Prescriptive Intelligence / Operational Twin
CP-295–CP-301  Edge/Offline Industrial DÉLIA
CP-302–CP-310  AI Model Lifecycle / Capability Marketplace
CP-311–CP-316  Recurring Governed Work / Scheduling
```

Todas as faixas temáticas são subordinadas à ordem de `16`. Nenhuma spec temática cria fase, runtime, requirement authority ou permission authority paralela.

## 14. C0.S0 inventory evidence linkage (reconciled)

Evidence anchors: `51` §§10/31/38–46 + `evidence/execution-ledger.md` §§6.1–6.21.  
Status vocabulary: inventory **EVIDENCED** ≠ CP **PASS** ≠ C0.S0 COMPLETE.

| CP | Exact gate (inventory) | C0.S0 evidence | Inventory status | CP row status |
|---|---|---|---|---|
| CP-154 | Portal/Core/Gateway/APIs/MFEs inventory | B–T; `51` anchors | EVIDENCED | remains PLANNED until C0.S0 acceptance |
| CP-194 | egress/OAuth/vault/webhooks inventory | E/F | EVIDENCED (vault/ExternalConnection NOT_PROVEN noted) | PLANNED |
| CP-223 | Teams foundation inventory | E | EVIDENCED (Teams runtime NOT_PROVEN) | PLANNED |
| CP-226 | automation/events/schedulers/RPA inventory | D/E | EVIDENCED (Hub NOT_PROVEN) | PLANNED |
| CP-249 | process-intelligence inventory | H | EVIDENCED (mining NOT_PROVEN) | PLANNED |
| CP-256 | AI asset / Control Tower inventory | I | EVIDENCED (Tower NOT_PROVEN) | PLANNED |
| CP-262 | MCP/A2A inventory | R (+E) | EVIDENCED (runtime NOT_PROVEN) | PLANNED |
| CP-268 | Personal Memory ownership freeze | J/P | EVIDENCED PARTIAL (DÉLIA PM TARGET; Chat≠PM) | PLANNED |
| CP-274 | semantic/glossary inventory | K | EVIDENCED (Semantic Layer NOT_PROVEN) | PLANNED |
| CP-280 | sandbox/artifact inventory | L | EVIDENCED (governed sandbox NOT_PROVEN) | PLANNED |
| CP-287 | predictive/twin inventory | M | EVIDENCED (engine/twin NOT_PROVEN) | PLANNED |
| CP-295 | Edge/offline inventory | N | EVIDENCED (Edge NOT_PROVEN; Pulse DOMAIN_LOCAL) | PLANNED |
| CP-302 | model/MLOps/catalog inventory | O | EVIDENCED (Registry/Marketplace NOT_PROVEN) | PLANNED |
| CP-311 | Recurring Work owner vs timer freeze | D | EVIDENCED PARTIAL (definition TARGET; physical scheduler TO_INVENTORY) | PLANNED |

```text
CLOSED_NONISSUE: no dedicated C0.S0-A…T CP IDs are required; tasks map via thematic CPs above
C0.S0 inventory coverage ≠ 100% CP PASS
No CP promoted to PASS by documentation alone
```

Related non-inventory CPs (CP-178/179 OT, CP-091 EntityRef, etc.) remain PLANNED/LOCKED per their rows; inventory evidence does not satisfy runtime gates.

C2-T3: rows CP-001–CP-012, CP-025, CP-059, CP-149, CP-156 and CP-159 remain `LOCKED` as requirements (`LOCKED` ≠ runtime PASS). C2-T6R1 restored canonical Status for CP-061–CP-070 (`LOCKED`, except CP-069 `TO_INVENTORY`). C2-PREFINAL-R1 restored CP-001/CP-149/CP-156 to `LOCKED` after C2-T5 documentation drift introduced non-canonical Status tokens; implementation and live evidence stay in the note. Product Master live smoke of the companion dock is `PASS` for the recorded scope (§6.57). C2-T6 inventories the existing Portal embedded host. DÉLIA full-page and companion dock stay federated. No DÉLIA iframe bridge was added. V1 modal UX is `SUPERSEDED_UX`. Host presentation, transient dock state and full-page mount are the current C2 runtime. WorkspaceContext, operational OP/machine/product/operation/posto, typed command bus and DÉLIA iframe bridge are not runtime. CP-012 reasoning is C3. `LIVE_USER_A_USER_B` and portal logout E2E stay at their previous status. Portal and Transformômetro iframe security findings are owner follow-up, not C2 blockers. `C2_EXECUTED=NO`.

## 15. C0.S1 naming / physical ownership linkage — accepted review

Evidence anchors: `68` §4; `50` §3/§21; `17` §2; `52`; `21` §2; ledger C0.S1 review event.  
Review: `ARCHITECTURE_REVIEW_C0_S1`; `REVIEWED_HEAD=c822f0e72495256c3459a4b36b9c37a3bba95cbb`; verdict `ACCEPT_WITH_RESIDUAL`.

| CP | Naming/ownership note (C0.S1 accepted) | Status unchanged |
|---|---|---|
| CP-130–CP-134, CP-140 | architecture gates; no path invent | PLANNED |
| CP-138 | owner label → Portal/DÉLIA MFE; C2-T1D1 acceptance adds transient vs retained browser state, residency gate, centralized cleanup/removability; C2-T2/T5 current shell + global panel = PARTIAL (transient root only; no retained boundary) | PLANNED |
| CP-158 | C2-T1D1 acceptance adds User A → Portal logout → User B isolation for DÉLIA-owned browser state; C2-T2/T5 unmount/remount PASS for current transient shell/panel; future retained-state isolation not implemented | PLANNED — PARTIAL current transient scope |
| CP-141 | path → `delia-api/` | LOCKED (C1) |
| CP-142 | path → `plugins/delia/` | LOCKED (C1) |
| CP-143 | `id=delia`; manifest source DÉLIA; registry Core | LOCKED (C1) |
| CP-144 | `/apps/delia-api/`, `/apps/delia` | LOCKED (C1) |
| CP-145 | containers `delpi-delia-api`, `delpi-delia` | LOCKED (C1) |
| CP-146–CP-147 | DÉLIA platform/API ownership labels; CP-147 migration chain **NOT_APPLICABLE_AT_C1** until first DÉLIA-owned persisted state (C1-T6D1) | PLANNED / N/A@C1 |
| CP-148–CP-150, CP-152–CP-153, CP-155 | same product/runtime; Core AuthZ preserved | LOCKED (C1) |
| CP-227 | Hub external execution boundary TARGET | PLANNED |
| CP-249 | Process Intelligence = MODULE_IN_DELIA | PLANNED |
| CP-256 | Control Tower = MODULE_IN_DELIA | PLANNED |
| CP-274 | Semantic Layer = MODULE_IN_DELIA + metric owners | PLANNED |
| CP-280 | Sandbox = DÉLIA analysis + isolated adapter deferred | PLANNED |
| CP-295 | Edge = adapter; no DÉLIA-owned Edge runtime | PLANNED |
| CP-311 | Work definition vs physical scheduler unchanged | PLANNED |

```text
Naming update ≠ CP PASS ≠ runtime evidence
C0.S0 = APPROVED
C0.S1 = APPROVED
C0.S2 = APPROVED
C0.S3 = APPROVED
C0.S4 = APPROVED
C0.S5 = APPROVED
AUTHORITY_MAP = FROZEN_ACCEPTED
BOUNDED_CONTEXT_MAP = FROZEN_ACCEPTED
SHARED_REFERENCE_SEMANTICS = FROZEN_ACCEPTED
ARCHITECTURE_PERSISTENCE_PRIVACY_SAFETY = FROZEN_ACCEPTED
INTEGRATION_CONTRACTS = FROZEN_ACCEPTED
C0.S6 = APPROVED
RED_CONTRACT_CONFORMANCE_PRIVACY_SECURITY_HARNESS = FROZEN_ACCEPTED
C0.S7 = APPROVED
FOUNDATION_FREEZE = APPROVED
C1_AUTHORIZED = YES
C1_STARTED = YES
C1_EXECUTED = NO
PROGRAM = PLANNED / NOT_STARTED
C0 = NOT_STARTED
RUNTIME_READINESS = NOT_PROVEN
PRODUCTION_READINESS = NOT_PROVEN
NEW_BEHAVIORAL_TESTS = TEST_NOT_RUN
FUTURE_C1_C7_GREEN_EVIDENCE_REQUIRED = YES
DÉLIA_RUNTIME_DIFF = delia-api skeleton + /health
NEW_RUNTIME_ABSTRACTIONS = NONE
NEXT = C1-T2 — JWT + CORE EFFECTIVE ACCESS INTEGRATION
```

## 16. C0.S2 authorities / bounded contexts linkage — accepted review

Evidence anchors: `17` §§2.3–2.6; ledger §6.24 + C0.S2-T2 review event; `16` C0.S2.  
Review: `ARCHITECTURE_REVIEW_C0_S2`; `REVIEWED_HEAD=8bae12a250f2362603211a93c65bb098b8b1e9aa`; verdict `ACCEPT_WITH_RESIDUAL`.

| Theme | CP examples (status unchanged) | C0.S2 boundary note |
|---|---|---|
| Standalone / Chat independence | CP-141–147, CP-146 | preserved; Chat REFERENCE_ONLY |
| Core AuthZ | CP-150 | Core effective RBAC; JWT≠final permission |
| Domain AuthZ | CP-013+ Domain action CPs | Domain final authorization |
| Evidence | CP-093–095, CP-206 | DÉLIA coordination; Evidence≠SoT |
| Policy / Decision | CP-110–111, CP-233 | Policy≠Core/Domain AuthZ; PREPARE≠ACT |
| Work / Durable | CP-105–109 | Work≠executor technical state |
| Automation separation | CP-227–230 | Hub = technical execution |
| Recurring Work | CP-311 | definition=DÉLIA; timer=TO_INVENTORY |
| Process Intelligence | CP-249–251 | MODULE_IN_DELIA; source truth external |
| Control Tower | CP-256–257 | MODULE_IN_DELIA; ≠planner/permission |
| Personal Memory | CP-268–269 | ≠Org Knowledge≠AuthZ |
| Semantic Layer | CP-274–275 | ≠SoT; metric owners retain formula |
| Sandbox | CP-280–281 | no general shell; runtime TO_INVENTORY |
| Predictive / Twin | CP-287–288 | prediction≠FACT; simulate≠apply |
| Edge | CP-295–296 | no DÉLIA Edge runtime; offline≠↑AuthZ |
| MCP/A2A | CP-262–263 | discovery≠approval |
| Observability | CP-051, CP-056 | correlation≠authority transfer |
| Safety / OT | CP-178–179 | DÉLIA≠safety controller |
| Biometric | CP-183–184 | match≠AuthN/AuthZ |

```text
C0.S2 documentation evidence ≠ runtime implementation evidence
C0.S2 accepted state ≠ runtime CP PASS
No CP promoted to PASS by C0.S2-T1/T2
No new CP ID invented for "C0.S2"
C1+ CP statuses remain unchanged/LOCKED as applicable
NEW_RUNTIME_ABSTRACTIONS = NONE
```

## 17. C0.S3 shared primitives linkage — accepted review

Evidence anchors: `21` §4; `17` §3; ledger §6.26 + C0.S3-T3 review event; `16` C0.S3.
Review: `ARCHITECTURE_REVIEW_C0_S3`; `REVIEWED_HEAD=641ffc07284b98ffbdb5e13217ce214c4ad8ebb0`; verdict `ACCEPT_WITH_RESIDUAL`.

| Primitive / decision | CP linkage | Status note |
|---|---|---|
| EntityRef | CP-159 | REUSE; ≠AuthZ |
| SourceRef / EvidenceRef | CP-098, CP-200, CP-206, CP-219 | REUSE; Evidence≠SoT |
| EventEnvelope | CP-207, CP-218 | REUSE; ≠permission/command |
| CapabilityProjection | CP-058, CP-205, CP-235 | PROJECTION_ONLY |
| ProcessTraceRef | CP-250, CP-251 | REFERENCE_ONLY |
| MetricDefinitionRef | CP-275, CP-276, CP-277 | ACCEPTED shared |
| MemoryItemRef | CP-269, CP-270, CP-271 | DOMAIN_LOCAL_ONLY |
| ArtifactRef | CP-283, CP-284 | ACCEPTED shared |
| PredictionRef | CP-288, CP-289, CP-293 | ACCEPTED; Prediction≠FACT |
| ScenarioRef | CP-291, CP-292, CP-294 | ACCEPTED; SIMULATE≠APPLY |
| AutomationExecutionRef | CP-235–237, CP-239 | ACCEPTED; ≠Outcome |
| ExecutorRef | CP-235, CP-236, CP-238 | CLOSED_NONISSUE (C0.S5; no shared primitive) |
| RecurringWorkRef | CP-312, CP-314, CP-316 | ACCEPTED; ≠scheduler |
| WorkOccurrenceRef | CP-313, CP-315 | ACCEPTED; ≠timer tick |
| AIAssetRef | CP-257, CP-258, CP-305, CP-310 | PROJECTION_ONLY |
| ModelRef | CP-288, CP-303, CP-304, CP-307 | ACCEPTED shared |
| DeviceRef (Edge) | CP-171, CP-296, CP-298 | REUSE; EdgeDeviceRef rejected |
| AnalysisRunRef | CP-281, CP-282 | REJECT_ABSTRACTION (shared) |

```text
C0.S3 accepted documentation evidence ≠ runtime implementation evidence
No CP promoted to PASS by C0.S3-T2/T3
No new CP ID invented for "C0.S3"
C1+ CP statuses remain unchanged
NEW_RUNTIME_ABSTRACTIONS = NONE
C0.S4_AUTHORIZED = YES
C0.S4_EXECUTED = NO
FOUNDATION_FREEZE = NOT APPROVED
NOTE_SUPERSEDED_BY_C0_S7_T2: FOUNDATION_FREEZE current-state is APPROVED; see §21
```

## 18. C0.S4 architecture / persistence / privacy / safety linkage — accepted review

Evidence anchors: `21` §4A; ledger §6.28 + C0.S4-T3 review event; `16` C0.S4.
Review: `ARCHITECTURE_REVIEW_C0_S4`; `REVIEWED_HEAD=7ac1fb930017bbabb05d8b1654941518f315c6a7`; verdict `ACCEPT_WITH_RESIDUAL`.

| Theme | CP examples (status unchanged) | C0.S4 note |
|---|---|---|
| Persistence ownership / no shadow SoT | CP-141–147, CP-159 | DÉLIA owns only owned lifecycle/refs/projections |
| Privacy / retention / delete / export | CP-268–271, CP-183–184 | unknown duration ≠ infinite; no invented legal durations |
| Secrets / encryption | CP-051, CP-056 | secret never in prompt/MFE/log/Evidence; SecretRef DEFER_TO_CONTRACT |
| Idempotency / concurrency / background AuthZ | CP-105–109, CP-311–316 | schedule≠permission; timer≠actor |
| Evidence / Outcome | CP-093–095, CP-206, CP-239 | Evidence≠SoT; tech success≠Outcome |
| Prediction / Scenario / Twin | CP-287–294 | Prediction≠FACT; SIMULATE≠APPLY |
| Biometric / media / Human Observation | CP-171, CP-183–184 | match≠AuthN/AuthZ; raw≠Evidence |
| External connections / OAuth | CP-200+ | provider scope≠authorization |
| Process / Task Mining privacy | CP-249–251 | ≠employee surveillance; Task Mining off by default |
| Sandbox / Artifact | CP-280–284 | isolated; no broad credentials |
| Model / Marketplace / Tower | CP-256–258, CP-303–310 | router≠approval; publish≠enable |
| Edge / offline | CP-295–298 | offline≠↑authority |
| OT / Safety | CP-178–179 | DÉLIA≠safety controller; OT ACTUATION blocked by default |

```text
C0.S4 accepted documentation evidence ≠ runtime implementation evidence
No CP promoted to PASS by C0.S4-T2/T3
No new CP ID invented for "C0.S4"
TRACEABILITY_GAP_REQUIRING_NEW_CP = CLOSED_NONISSUE
NEW_CP_CREATED = NO
CP_RENAMED = NO
RUNTIME_CP_PROMOTED_TO_PASS = NO
C1_PLUS_EXECUTION_STATUS_CHANGED = NO
NEW_RUNTIME_ABSTRACTIONS = NONE
C0.S5_AUTHORIZED = YES
C0.S5_EXECUTED = NO
FOUNDATION_FREEZE = NOT APPROVED
NOTE_SUPERSEDED_BY_C0_S7_T2: FOUNDATION_FREEZE current-state is APPROVED; see §21
```

## 19. C0.S5 integration contracts linkage — accepted review

Evidence anchors: `17` §22; ledger §6.30 + C0.S5-T3 review event; `16` C0.S5.
Review: `ARCHITECTURE_REVIEW_C0_S5`; `REVIEWED_HEAD=8d83383e9a9ff019132e7156d56e41643b168851`; verdict `ACCEPT_WITH_RESIDUAL`.

| Theme | CP examples (status unchanged) | C0.S5 note |
|---|---|---|
| Core / AuthZ | CP-150, CP-057 | Core effective RBAC; JWT≠final permission |
| Portal host / Workspace | CP-135, CP-136, CP-138 | Portal context≠permission |
| Entity / Evidence | CP-091, CP-093, CP-159 | Domain READ typed; Evidence≠SoT |
| Errors / idempotency | CP-109 | semantic categories; exactly-once not assumed |
| External / OAuth | CP-194–199, CP-209, CP-214 | provider scope≠AuthZ; DRAFT≠SEND |
| Teams | CP-223 | adapter under EXTERNAL; webhook≠ACT |
| Automation / Hub | CP-227–231, CP-235–239 | Work≠Hub; tech≠Outcome |
| Recurring Work / scheduler | CP-311–316 | OccurrenceSignal; schedule≠permission |
| Process | CP-249+ | projection≠SoT/employee truth |
| MCP/A2A | CP-262+ | discovery≠approval |
| Memory / privacy | CP-268+ | preserved; contracts do not authorize |
| Semantic Layer | CP-274+ | refs only |
| Sandbox / Artifact | CP-280+ | isolated; generation≠publication |
| Predictive / Twin | CP-287+ | Prediction≠FACT; SIMULATE≠APPLY |
| Edge | CP-295+ | offline≠↑AuthZ |
| Model / Marketplace | CP-302+ | router≠approval; publish≠enable |

```text
C0.S5 accepted documentation evidence ≠ runtime implementation evidence
No CP promoted to PASS by C0.S5-T2/T3
No new CP ID invented for "C0.S5"
TRACEABILITY_GAP_REQUIRING_NEW_CP = CLOSED_NONISSUE
NEW_CP_CREATED = NO
CP_RENAMED = NO
RUNTIME_CP_PROMOTED_TO_PASS = NO
C1_PLUS_EXECUTION_STATUS_CHANGED = NO
NEW_RUNTIME_ABSTRACTIONS = NONE
C0.S6_AUTHORIZED = YES
C0.S6_EXECUTED = NO  # historical at C0.S5-T3; superseded by §20 C0.S6-T2 candidate persistence
FOUNDATION_FREEZE = NOT APPROVED
RESIDUAL = DOCUMENTATION_CONTRACT_TAXONOMY_RESIDUAL
NOTE_SUPERSEDED_BY_C0_S6_T2: see §20 for C0.S6 candidate harness state
NOTE_SUPERSEDED_BY_C0_S7_T2: FOUNDATION_FREEZE current-state is APPROVED; see §21
```

## 20. C0.S6 RED harness linkage — accepted review

Evidence anchors: `20` §C0.S6; ledger §6.32 + C0.S6-T3 review event; `16` C0.S6.
Review: `ARCHITECTURE_REVIEW_C0_S6`; `REVIEWED_HEAD=331e92d8fa3f0f3fff3926a58b983b7d05701c3e`; verdict `ACCEPT_WITH_RESIDUAL`.
Status: `C0.S6=APPROVED`; `RED_CONTRACT_CONFORMANCE_PRIVACY_SECURITY_HARNESS=FROZEN_ACCEPTED`.
Contracts authority unchanged: `17` §22 (`INTEGRATION_CONTRACTS=FROZEN_ACCEPTED`; 27 families).

| Theme | CP examples (status unchanged) | C0.S6 harness note |
|---|---|---|
| AuthN / Core / Portal | CP-150, CP-057, CP-130..140 | JWT≠permission; Portal≠AuthZ; AUTHZNEG matrix |
| Domain READ/ACTION | CP-091, CP-093, CP-109 | PREPARE≠ACT; Domain final AuthZ; typed READ |
| Automation / Outcome | CP-227..231, CP-239 | Hub≠Outcome; VERIFY authoritative |
| Scheduler / Event | CP-311..316, CP-207 | schedule≠permission; event≠ACT |
| External / Teams / OAuth | CP-194..199, CP-209, CP-214, CP-223 | provider scope≠AuthZ; webhook=SIGNAL |
| Media / Biometric / HOBS | CP-182, CP-183, CP-188..190 | match≠AuthN/AuthZ; raw≠Evidence |
| Process / Sandbox / Artifact | CP-249+, CP-280+ | analysis isolation; gen≠publish |
| Model / Scenario / Marketplace | CP-287+, CP-302+ | Prediction≠FACT; SIMULATE≠APPLY; publish≠enable |
| Edge / OT / Audit | CP-295+, CP-178..179, CP-051, CP-055, CP-056 | offline≠↑AuthZ; DÉLIA≠safety; secret/CoT FAIL |
| MCP/A2A / Memory / Semantic | CP-262+, CP-268+, CP-274+ | discovery≠approval; privacy isolation |
| Idempotency / Errors / Version | CP-109, CP-175, CP-176 | no exactly-once; owner semantics retained |

```text
C0.S6 accepted documentation harness ≠ runtime implementation evidence
No CP promoted to PASS by C0.S6-T2/T3
No new CP ID invented for "C0.S6" / per TEST_ID / per contract / review
TRACEABILITY_GAP_REQUIRING_NEW_CP = CLOSED_NONISSUE
NEW_CP_CREATED = NO
CP_RENAMED = NO
RUNTIME_CP_PROMOTED_TO_PASS = NO
C1_PLUS_EXECUTION_STATUS_CHANGED = NO
NEW_RUNTIME_ABSTRACTIONS = NONE
REVIEW = ARCHITECTURE_REVIEW_C0_S6
REVIEWED_HEAD = 331e92d8fa3f0f3fff3926a58b983b7d05701c3e
VERDICT = ACCEPT_WITH_RESIDUAL
C0.S6 = APPROVED
RED_CONTRACT_CONFORMANCE_PRIVACY_SECURITY_HARNESS = FROZEN_ACCEPTED
CONTRACT_FAMILY_COVERAGE = 27/27
TEST_ID_COUNT = 250
TEST_ID_UNIQUENESS = PASS / STATIC_DOCUMENTATION_VALIDATION_ONLY
AUTHORITY_NEGATIVE_MATRIX = C0S6-AUTHZNEG-001..012 COMPLETE
FOUNDATION_FREEZE_BLOCKERS = FFB-001..018 PRESENT
C0.S7 = APPROVED
FOUNDATION_FREEZE = APPROVED
C1_AUTHORIZED = YES
C1_STARTED = YES
C1_EXECUTED = NO
RUNTIME_READINESS = NOT_PROVEN
PRODUCTION_READINESS = NOT_PROVEN
EXECUTION_STATUS = TEST_NOT_RUN for new behavioral tests
NEW_BEHAVIORAL_TESTS = TEST_NOT_RUN
FUTURE_C1_C7_GREEN_EVIDENCE_REQUIRED = YES
NEXT = C1-T2 — JWT + CORE EFFECTIVE ACCESS INTEGRATION
```

## 21. C0.S7 Foundation Freeze linkage — accepted review

Evidence anchors: `16` C0.S7; `20` C0.S7; ledger §6.34; `12`/`README` current-state pointers.
Review: `FOUNDATION_FREEZE_REVIEW`; `REVIEWED_HEAD=6e10029bcc281c4e0c3575448a1414a157cc3c44`; verdict `APPROVE_WITH_NON_BLOCKING_RESIDUALS`.
Status: `C0.S7=APPROVED`; `FOUNDATION_FREEZE=APPROVED`; `C1_AUTHORIZED=YES`; `C1_STARTED=NO`; `C1_EXECUTED=NO`.
No new CP. No runtime CP promoted to PASS. C1+ execution statuses remain unchanged (`LOCKED`/`PLANNED` as applicable). Authorization of C1 is not execution-status advancement.

```text
C0.S7 accepted freeze ≠ runtime implementation evidence
No CP promoted to PASS by C0.S7-T2
No new CP ID invented for "Foundation Freeze" / per gate
TRACEABILITY_GAP_REQUIRING_NEW_CP = CLOSED_NONISSUE
NEW_CP_CREATED = NO
CP_RENAMED = NO
RUNTIME_CP_PROMOTED_TO_PASS = NO
C1_PLUS_EXECUTION_STATUS_CHANGED = NO
NEW_RUNTIME_ABSTRACTIONS = NONE
PROGRAM = PLANNED / NOT_STARTED
C0 = NOT_STARTED
RUNTIME_READINESS = NOT_PROVEN
PRODUCTION_READINESS = NOT_PROVEN
NEW_BEHAVIORAL_TESTS = TEST_NOT_RUN
FUTURE_C1_C7_GREEN_EVIDENCE_REQUIRED = YES
NEXT = C1-T2 — JWT + CORE EFFECTIVE ACCESS INTEGRATION
```
