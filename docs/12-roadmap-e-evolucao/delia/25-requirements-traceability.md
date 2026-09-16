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

> DÉLIA é o nome do produto. `Copilot` / `COPILOT_*` / `minha-delpi-copilot*` neste arquivo são `LEGACY_TOKEN`/`HISTORICAL`/`SUPERSEDED` quando ainda presentes; paths/owners ativos preferem `delia-api` / `plugins/delia` / DÉLIA API|MFE (`FROZEN_ACCEPTED` C0.S1). Naming update ≠ implementation evidence. Labels semânticos residuais “Copilot” permanecem `DOCUMENTATION_TERMINOLOGY_RESIDUAL` não bloqueante.

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
| CP-051 | Correlação/observabilidade transversal | Copilot API/Portal/Observability | contracts/traces | PLANNED |
| CP-055 | Prompt/tool/context injection safety | Copilot Policy | security semantics | PLANNED |
| CP-056 | Secret redaction | todos os owners | redaction contract | PLANNED |
| CP-057 | Idempotency semantics de writes | Domain API + Copilot orchestration | C0 contract; runtime C5 | PLANNED |
| CP-072 | Expertise Pack versionado | Copilot API | primitive/schema | PLANNED |
| CP-075 | Domain Playbook versionado | Copilot API/domain owners | primitive/schema | PLANNED |
| CP-077 | Expertise não concede RBAC | Core/Copilot Policy | invariant | PLANNED |
| CP-088 | PDF/imagem não altera policy | Copilot Multimodal/Policy | safety contract; C3 eval | PLANNED |
| CP-091 | EntityRef cross-domain canônico | Copilot shared/domain owners | primitive | PLANNED |
| CP-092 | RelationshipRef com provenance | Graph/domain owners | primitive | PLANNED |
| CP-093 | EvidenceRef transversal | Copilot API | primitive | PLANNED |
| CP-094 | Epistemic classes canônicas | Copilot synthesis | semantics | PLANNED |
| CP-095 | Evidence multimodal page/region | Copilot Multimodal | contract; runtime C3 | PLANNED |
| CP-105 | Workflow persistence/checkpoint contract | Copilot Work Runtime | lifecycle contract | PLANNED |
| CP-106 | `wait_user` semantics | Copilot Work Runtime | lifecycle contract | PLANNED |
| CP-107 | `wait_approval` semantics | Copilot Work/Policy | lifecycle contract | PLANNED |
| CP-108 | `wait_event` semantics | Copilot Work/Event | lifecycle contract | PLANNED |
| CP-109 | No duplicate write after resume | Copilot Work/Executor | idempotency contract | PLANNED |
| CP-110 | Decision Gate proporcional a risco | Copilot Policy | contract | PLANNED |
| CP-111 | Approval workflow humano | Copilot Policy/Work | contract | PLANNED |
| CP-123 | Provider data-policy filtering | Copilot Security | policy contract | PLANNED |
| CP-130 | Clean Architecture + Ports & Adapters + DDD pragmático | Architecture | architecture freeze | PLANNED |
| CP-131 | Layer/dependency direction canônicas | Architecture | conformance | PLANNED |
| CP-132 | DI/Composition Root + adapters/ports | Architecture/owners | wiring conformance | PLANNED |
| CP-133 | Pattern Decision Matrix | Architecture | review | PLANNED |
| CP-134 | Abstraction Gate | Architecture | no unjustified abstraction | PLANNED |
| CP-135 | Error/Result model transversal | Application/Interfaces | contract/conformance | PLANNED |
| CP-136 | EventEnvelope + Outbox/Idempotency/Resilience rules | Platform/Work | conformance | PLANNED |
| CP-137 | State Machine para lifecycles não triviais | Domain/Policy/Work | transition tests | PLANNED |
| CP-138 | Frontend state ownership | Portal/DÉLIA MFE | frontend conformance | PLANNED |
| CP-139 | Adapter/ACL/Strangler para integrações legadas quando necessário | Architecture | migration gate | PLANNED |
| CP-140 | Architecture conformance + ADR process | Architecture | conformance/ADR | PLANNED |
| CP-146 | Zero dependência de runtime do Minha DELPI Chat | DÉLIA Platform | Chat-offline/scan | PLANNED |
| CP-147 | Persistência/migration chain próprias da DÉLIA | DÉLIA API (`delia-api/migrations/`) | storage ownership | PLANNED |
| CP-154 | Inventário Portal/Core/Gateway/APIs/MFEs antes do runtime | Architecture | C0.S0 evidence | PLANNED |
| CP-157 | Media capture/consent/retention classes definidas antes do runtime multimodal contínuo | Copilot Security/Architecture | media/privacy foundation | PLANNED |
| CP-158 | Shared-device identity/session isolation | Copilot/Portal/Security | device session negative tests | PLANNED |
| CP-175 | Raw media minimization e retention class-specific | Copilot Media/Security | retention/data minimization | PLANNED |
| CP-176 | Sem reconhecimento facial open-world/indiscriminado, emotion detection como truth ou hidden surveillance por default | Security/Governance | privacy negative gate | PLANNED |
| CP-178 | Arbitrary LLM→machine command proibido | Copilot/Industrial Safety | OT boundary gate | PLANNED |
| CP-179 | Future OT actuation exige safety gate separado | Industrial owner/Copilot | separate architecture/risk approval | PLANNED |
| CP-182 | Enrollment biométrico explícito, versionado, revogável e com purpose/retention definidos | Copilot Biometric/Security | enrollment lifecycle contract | PLANNED |
| CP-183 | Biometric match nunca concede autenticação/permissão por si só | Copilot Policy/Core | permission-elevation negative | PLANNED |
| CP-188 | Human Observation limitado a evidência observável do processo; sem inferência psicológica/sensível | Copilot Security/Governance | prohibited-inference gate | PLANNED |
| CP-189 | Sem decisão trabalhista automática baseada em biometria/Human Observation | Governance/People owner/Copilot | employment-decision negative | PLANNED |
| CP-190 | Biometric templates protegidos, não logados, revogáveis e com retenção própria | Copilot Biometric/Security | storage/key/retention gate | PLANNED |
| CP-194 | Inventário de egress, OAuth, secrets/vault, webhooks e integrações externas antes do runtime | Architecture/Security | external-access foundation | PLANNED |
| CP-195 | Safe Web Fetch bloqueia SSRF/private/link-local/metadata e revalida redirects | Copilot Internet/Security | egress negative gate | PLANNED |
| CP-196 | Conteúdo web/email/chat externo é untrusted e não altera system/policy/RBAC | Copilot Security | external injection gate | PLANNED |
| CP-197 | ExternalConnection usa least privilege, consent/scope disclosure, revoke/reconnect e audit | Copilot Connectors/Security | connection lifecycle contract | PLANNED |
| CP-198 | Access/refresh tokens e provider secrets nunca chegam ao LLM/MFE/logs e usam storage protegido | Copilot Infrastructure/Security | credential leakage negative | PLANNED |
| CP-199 | USER_DELEGATED, ORG_MANAGED, SHARED_RESOURCE e SERVICE_CONNECTION preservam ownership/visibility distintos | Copilot Connectors/Privacy | ownership isolation gate | PLANNED |
| CP-209 | External data possui retention/delete/cache policy por connection/source class | Copilot Privacy/State | retention gate | PLANNED |
| CP-210 | Provider terms/scopes/limits/compliance são revalidados na implementação e rollout | Copilot Governance | provider compliance gate | PLANNED |
| CP-211 | WhatsApp usa contratos oficiais suportados; scraping/automação de sessão pessoal é proibido por default | Copilot Connectors/Security | supported-contract gate | PLANNED |
| CP-214 | Internet/connector/write/webhook possuem kill switches independentes de prompt/LLM | Copilot Admin/Security | emergency disable gate | PLANNED |
| CP-223 | Teams inventory congela Entra app registration, tenant/admin owner, Graph scopes, resource-specific consent, webhooks, app distribution e meeting-artifact privacy antes do runtime | Copilot Teams/Architecture/Security | Teams foundation gate | PLANNED |
| CP-226 | C0 inventaria event sources/buses/webhooks/schedulers, RPA tools/licenças/bots, scripts/jobs, queues/workers, service accounts, credential owners, outcome sources e automation governance antes de runtime | Architecture/Automation/Security | automation foundation inventory | PLANNED |
| CP-227 | DÉLIA intelligence/orchestration e Automation & Execution Hub execution permanecem separáveis; Hub não cria segundo planner/AI authority | Architecture/DÉLIA Automation | ownership/bounded-context gate | PLANNED |
| CP-228 | Executor preference é API/integration/function antes de RPA/computer-use quando contrato autoritativo suportado existir | Copilot Automation/Architecture | executor-selection architecture gate | PLANNED |
| CP-229 | Background/autonomous execution usa user/service identity explícita, auditável e não deriva autoridade de evento/LLM | Copilot Security/Core/Automation | background identity gate | PLANNED |
| CP-230 | Execution contract define correlation, idempotency, pre/postconditions, timeout/retry e verified Outcome semantics antes de executors materiais | Copilot Automation/Work | execution contract gate | PLANNED |
| CP-231 | Event source authenticity/trust, dedupe, ordering/correlation e polling fallback bounded são definidos antes de continuous operations | Copilot Events/Architecture | event foundation gate | PLANNED |
| CP-249 | C0 inventaria event logs, process owners, case keys, BPMN/process docs, task-mining telemetry/privacy e data quality antes de Process Intelligence runtime | DÉLIA Process Intelligence/Architecture | process-intelligence foundation inventory | PLANNED |
| CP-256 | C0 inventaria todos os AI/automation assets, owners, risk/compliance, evals, cost telemetry, incidents e kill-switch mechanisms antes da Control Tower | DÉLIA Control Tower/Governance | AI asset governance foundation | PLANNED |
| CP-262 | C0 inventaria MCP/A2A/tool registries, external agents, service identities, delegation credentials, protocol versions e trust boundaries | Copilot Interoperability/Security | protocol interoperability foundation | PLANNED |
| CP-268 | C0 congela ownership/classes/retention/export/delete/user-controls para Personal Memory; memória não é Knowledge nem permission authority | Copilot Memory/Privacy | personal-memory foundation | PLANNED |
| CP-274 | C0 inventaria business glossary, KPI formulas, BI semantic models, metric owners, grain/dimensions, freshness e definition conflicts | DÉLIA Semantic Layer/Data owners | semantic foundation inventory | PLANNED |
| CP-280 | C0 inventaria code/data-analysis sandbox, BI/query engines, file scanning/storage e artifact-generation/versioning infrastructure e boundaries | DÉLIA Analysis/Artifacts/Security | sandbox/artifact foundation inventory | PLANNED |
| CP-287 | C0 inventaria predictive/anomaly/optimization/simulation models, datasets, ground truth, owners e operational/digital-twin sources | Copilot Predictive/Twin/Data owners | predictive/twin foundation inventory | PLANNED |
| CP-295 | C0 inventaria factory network, Edge platforms/devices, MDM, local inference, offline requirements, time sync, OT segmentation e cache/update owners | DÉLIA Edge/Industrial/Infrastructure | edge/offline foundation inventory | PLANNED |
| CP-302 | C0 inventaria model providers, local ML models, registries/MLOps, datasets/evals, CI/CD, package catalogs/signing e supply-chain controls | Copilot Model Governance/Control Tower | model/marketplace foundation inventory | PLANNED |
| CP-311 | C0 congela Recurring Governed Work: owner da definição versus owner do timer/scheduler físico, recurrence/timezone/DST, misfire/missed-run, overlap, idempotência por ocorrência, background identity/AuthZ/revoke, pause/cancel e Outcome boundaries | DÉLIA Work/Architecture/Automation/Security | recurring-work foundation contract | PLANNED |

## 3. C1 — Standalone Application Bootstrap

| ID | Requisito | Owner | Gate | Status |
|---|---|---|---|---|
| CP-141 | DÉLIA API standalone | `delia-api/` (FROZEN_ACCEPTED C0.S1; was `minha-delpi-copilot-api`) | own service/health/tests | LOCKED |
| CP-142 | DÉLIA MFE standalone | `plugins/delia/` (FROZEN_ACCEPTED C0.S1; was `plugins/minha-delpi-copilot`) | build/federation/tests | LOCKED |
| CP-143 | Manifesto próprio da DÉLIA | DÉLIA/Core (`id=delia`) | schema/registration | LOCKED |
| CP-144 | Gateway route própria API/MFE | Gateway (`/apps/delia-api/`, `/apps/delia`) | dev/prod parity | LOCKED |
| CP-145 | Compose/deploy próprios | Infra (`delpi-delia-api`, `delpi-delia`) | independent service/start | LOCKED |
| CP-148 | Portal federated full-page mount | Portal/DÉLIA MFE | authorized mount/F5 | LOCKED |
| CP-149 | Global DÉLIA panel usando o mesmo MFE/runtime | Portal/DÉLIA MFE | surface parity | LOCKED |
| CP-150 | JWT + Core/RBAC integration | DÉLIA API/Core | auth negatives | LOCKED |
| CP-152 | Health + independent rollback/shutdown | DÉLIA/Infra | Chat-offline rollback | LOCKED |
| CP-153 | Reuso obrigatório de `@delpi/plugin-ui`/shared federation | DÉLIA MFE | federation/UI conformance | LOCKED |
| CP-155 | Entry point da DÉLIA amplamente disponibilizável conforme acesso/rollout | Portal/Core/DÉLIA MFE | access/visibility gate | LOCKED |

## 4. C2 — Portal Context + Platform Commands

| ID | Requisito | Owner | Gate | Status |
|---|---|---|---|---|
| CP-001 | DÉLIA global no Portal | DÉLIA MFE + Portal | panel/full-page UX | LOCKED |
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
| CP-061 | Abrir iframe `PORTAL_ONLY` | Portal/CopilotBridge | authorized navigation | LOCKED |
| CP-062 | Handshake seguro Portal↔iframe | Portal/IframeBridge | security contract | LOCKED |
| CP-063 | Workspace Context de iframe | IframeBridge | normalization | LOCKED |
| CP-064 | Comando visual genérico iframe | Portal/IframeBridge | declared capability | LOCKED |
| CP-065 | Classificar iframe I0–I3 | Readiness | evidence | LOCKED |
| CP-068 | Proibir Business Action via DOM/click | Portal/DÉLIA Policy | negative gate | LOCKED |
| CP-069 | SSO iframe sem token pelo bridge | Portal/App/Security | auth architecture | TO_INVENTORY |
| CP-070 | Observabilidade iframe bridge | Portal/Observability | trace/redaction | LOCKED |
| CP-156 | Paridade de RBAC/policy entre Global/Workspace/Meeting/Frontline | Portal/DÉLIA Policy | surface parity | LOCKED |
| CP-159 | Contexto operacional OP/máquina/produto/operação/posto usa WorkspaceContext + EntityRef | Portal/MFE/DÉLIA | operational context contract | LOCKED |
| CP-171 | Device metadata não substitui identidade/autorização | Portal/DÉLIA Security | shared-device/context negative | LOCKED |

## 5. C3 — Intelligence Core + Extended Foundations

| ID | Requisito | Owner | Gate | Status |
|---|---|---|---|---|
| CP-026 | RAG de procedimentos/documentos | Copilot Knowledge | grounding/security | LOCKED |
| CP-028 | Redigir e-mail/texto | Copilot capability | faithfulness | LOCKED |
| CP-053 | Send/stream parity | Copilot API/MFE | transport parity | LOCKED |
| CP-071 | Uma única DÉLIA sem seleção de agente | DÉLIA API/MFE | no agent runtime | LOCKED |
| CP-073 | Recuperação semântica de expertise | Copilot API | positive/sibling/negative | LOCKED |
| CP-074 | Composição multi-expertise | Copilot Planner | cross-domain | LOCKED |
| CP-078 | Multimodalidade sem agent dependency | Copilot Multimodal | attachment eval | LOCKED |
| CP-079 | Análise de desenho com provenance/confidence | Copilot + Engineering | multimodal eval | LOCKED |
| CP-083 | Projects/preferred expertise sem outro runtime | Copilot API | permission negative | TO_INVENTORY |
| CP-086 | Unknown Expertise Pack sem planner patch | Copilot API | generalization | LOCKED |
| CP-087 | Metamorphic rename de Expertise Pack | Copilot Evals | equivalence | LOCKED |
| CP-089 | Packs referência Qualidade + Engenharia | Copilot/domain owners | pilot evals | LOCKED |
| CP-151 | OpenAPI ingestion + Action Catalog próprios da DÉLIA | DÉLIA API | independent catalog/importer | LOCKED |
| CP-160 | Speech-to-text/text-to-speech baseline por ports/adapters quando priorizado | Copilot Media | voice eval/provider abstraction | LOCKED |
| CP-161 | Voice command preserva mesma RBAC/policy/Decision semantics do texto | Copilot Policy/Planner | modality parity | LOCKED |
| CP-162 | Camera/image Evidence com frame/region/confidence/limitations | Copilot Multimodal | visual evidence eval | LOCKED |
| CP-163 | Short-video ingestion com time-range provenance e bounded processing | Copilot Media | video eval/budget | LOCKED |
| CP-164 | Screen share bounded/consented sem virar DOM automation | Copilot MFE/Media/Security | screen-share safety | LOCKED |
| CP-177 | Visual finding não vira decisão oficial de qualidade por default | Copilot/Quality Policy | epistemic/quality negative | LOCKED |
| CP-184 | Face recognition/verification closed-set apenas para usuários enrolled e policy-approved | Copilot Biometric | positive/unknown/look-alike eval | LOCKED |
| CP-185 | Speaker recognition/diarization separado de STT e de autorização | Copilot Biometric/Media | speaker identity eval | LOCKED |
| CP-186 | Unknown/low-confidence permanece desconhecido ou requer confirmação; associação é corrigível | Copilot Biometric/MFE | confidence/correction gate | LOCKED |
| CP-187 | Liveness/anti-spoof obrigatório quando a finalidade exigir confiança adicional | Copilot Biometric/Security | replay/photo/deepfake eval | LOCKED |
| CP-200 | Internet Research usa search + safe fetch + SourceRef/EvidenceRef + freshness/provenance | Copilot Internet Research | grounded research eval | LOCKED |
| CP-201 | Connector runtime é provider-neutral; planner não contém branches Gmail/Outlook/WhatsApp | Copilot Connectors/Planner | provider generalization | LOCKED |
| CP-205 | Connector capabilities são semânticas/contract-driven e separadas de endpoints específicos | Copilot Capability/Connectors | capability contract gate | LOCKED |
| CP-215 | Teams é capability family do Microsoft 365 connector; planner não depende de Graph paths nem cria runtime Teams separado | Copilot Teams/Connectors/Planner | Teams provider-neutral architecture | LOCKED |
| CP-232 | DÉLIA suporta decision-path routing `FAST | OPERATIONAL | REASONING`; nem todo evento chama LLM | DÉLIA Intelligence/Policy | decision-path routing eval | LOCKED |
| CP-233 | Business readiness/anomaly material usa deterministic Policy/Specification sobre fatos autoritativos; LLM não é única autoridade da decisão | Copilot Policy/Domain owners | deterministic-decision gate | LOCKED |
| CP-250 | Process Intelligence usa EventLog/ProcessTrace contracts com case/activity/time/source/provenance e não inventa eventos ausentes | Copilot Process Intelligence | process-contract/conformance gate | LOCKED |
| CP-257 | AI Control Tower possui AI Asset Registry/projection com owner/version/risk/data scope/eval/status/dependencies/kill-switch refs sem duplicar owner truth | Copilot Control Tower | asset-registry contract gate | LOCKED |
| CP-263 | MCP/A2A entram por adapters/allowlists provider-neutral; discovery de server/agent nunca equivale a aprovação/permission | Copilot Interoperability/Security | tool-agent trust gate | LOCKED |
| CP-269 | Personal Memory possui classes/provenance/version/retention e write policy; conversation não cria memória material silenciosamente | Copilot Memory/Privacy | memory lifecycle gate | LOCKED |
| CP-275 | Semantic Business Layer possui MetricDefinition/Glossary versionados com formula/grain/dimensions/unit/owner/source/freshness/security | Copilot Semantic Layer | metric-definition contract gate | LOCKED |
| CP-281 | Analysis Sandbox é isolado, quota-bounded, sem host/network/secret access irrestrito, e recebe dados apenas via reads autorizados | Copilot Analysis/Security | sandbox isolation gate | LOCKED |
| CP-288 | Prediction/Prescription contracts preservam model/version/horizon/confidence/inputs/limitations e não promovem previsão a FACT | Copilot Predictive/Evidence | prediction semantics gate | LOCKED |
| CP-296 | Edge runtime usa device/package/model/cache contracts versionados; device identity nunca substitui user identity | Copilot Edge/Architecture | edge contract gate | LOCKED |
| CP-303 | Model Registry/projection cobre LLM/embedding/vision/speech/classifier/forecast/anomaly/optimization com owner/version/eval/risk/deployment/rollback metadata | Copilot Model Governance | model registry gate | LOCKED |

## 6. C4 — Business + External Reads + Graph + Intelligence Reads

| ID | Requisito | Owner | Gate | Status |
|---|---|---|---|---|
| CP-013 | Consultar Business Action | Copilot Action Runtime | read/RBAC/outcome | LOCKED |
| CP-014 | Consultar múltiplas APIs | Copilot Planner | multi-provider | LOCKED |
| CP-015 | Analisar/comparar dados | Copilot synthesis | grounded evidence | LOCKED |
| CP-027 | Gerar resumo/relatório grounded | Copilot Artifact | evidence/faithfulness | LOCKED |
| CP-029 | Recomendar próximos passos | Copilot synthesis | contextual/allowed | LOCKED |
| CP-043 | Unknown OpenAPI provider | Copilot API | full-chain unknown | LOCKED |
| CP-044 | Metamorphic provider/path/opId | Copilot Evals | metamorphic | LOCKED |
| CP-058 | Business Capability Projection | Copilot API | no duplicate authority | LOCKED |
| CP-090 | DELPI Business Graph mínimo | Copilot Graph/domain owners | permission traversal | LOCKED |
| CP-128 | Business Graph sibling onboarding | Copilot Graph | no planner hardcode | LOCKED |
| CP-202 | External reads suportam fontes conectadas autorizadas sem vazar dados entre usuários/conexões | Copilot Connectors/Privacy | read isolation gate | LOCKED |
| CP-206 | Todo external read material gera SourceRef/EvidenceRef com provider/resource/scope/freshness | Copilot Evidence/Connectors | provenance gate | LOCKED |
| CP-216 | Teams reads suportam teams/channels/chats/messages/replies e meeting metadata somente dentro dos scopes/resources autorizados | Copilot Teams/Privacy | Teams read isolation gate | LOCKED |
| CP-219 | Transcript/recording/meeting artifact do Teams preserva SourceRef/EvidenceRef, meeting resource, provenance, permission scope, freshness/version e retention policy | Copilot Teams/Meeting/Evidence | Teams meeting provenance gate | LOCKED |
| CP-225 | Identidade de participante resolvida pelo Teams/tenant é primária quando authoritative; biometria é somente evidência suplementar governada | Copilot Teams/Biometric/Identity | participant identity precedence gate | LOCKED |
| CP-234 | Operational readiness/anomaly evaluation correlaciona Domain reads/Graph/Evidence e produz resultado read-only antes de qualquer side effect | Copilot Operational Intelligence/Domain owners | read-only decision evidence gate | LOCKED |
| CP-251 | Process Mining reconstrói variants/bottlenecks/conformance somente de event logs autorizados; ausência/incompletude permanece explícita | Copilot Process Intelligence | read-only process mining eval | LOCKED |
| CP-264 | MCP/A2A read-only tools/agents preservam tool/agent provenance, data minimization, timeout/cancellation e não recebem contexto irrestrito | Copilot Interoperability | read-only delegation gate | LOCKED |
| CP-270 | Personalization prioriza conteúdo/formatos usando memória, mas live domain/source facts continuam authority e stale memory não os substitui | Copilot Memory/Planner | personalization authority gate | LOCKED |
| CP-276 | Semantic Query resolve métrica governada e calcula por definição estruturada/reprodutível; LLM não inventa fórmula empresarial material | Copilot Semantic Layer/Analytics | governed metric query gate | LOCKED |
| CP-282 | Sandbox executa análise read-only reproduzível com SourceRefs/runtime/code hash/parameters e não permite DDL/DML por connector analítico read-only | Copilot Analysis | reproducible analysis gate | LOCKED |
| CP-289 | Predictive reads mostram model/version/horizon/freshness/calibration/limitations e degradam explicitamente em stale/OOD/unavailable | Copilot Predictive | predictive read eval | LOCKED |
| CP-297 | Edge read-only/offline cache preserva source revision/syncedAt/freshness e sinaliza ou bloqueia conteúdo stale conforme criticidade | Copilot Edge/Frontline | offline freshness gate | LOCKED |
| CP-304 | Uso de modelo material gera lineage suficiente para ligar prediction/result ao model/version/eval/deployment ref sem expor segredo | Copilot Model Governance/Evidence | model lineage gate | LOCKED |

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
| CP-016 | Criar registro | Domain API + Copilot executor | Decision/RBAC/outcome | LOCKED |
| CP-017 | Editar registro | Domain API + Copilot executor | write parity | LOCKED |
| CP-018 | Aprovar/rejeitar | Domain API/Copilot Policy | approval/safety | LOCKED |
| CP-019 | Cancelar/arquivar | Domain API/Copilot Policy | destructive gate | LOCKED |
| CP-020 | Adicionar comentário | Domain API | write parity | LOCKED |
| CP-021 | Atribuir responsável | Domain API | permission/gate | LOCKED |
| CP-022 | Preview de write | Copilot API/MFE | argsHash/impact | LOCKED |
| CP-023 | Decision/confirmation UI | Copilot MFE/API | Decision Gate | LOCKED |
| CP-024 | Revalidar após decisão | Copilot Policy/Executor | TOCTOU | LOCKED |
| CP-030 | Plano operacional visível | Copilot API/MFE | no CoT/activity | LOCKED |
| CP-031 | Workflow multi-app | Copilot Work Runtime | compound outcome | LOCKED |
| CP-032 | Parallel safe reads | Copilot Work Runtime | safety | LOCKED |
| CP-033 | Dependências entre steps | Copilot Work Runtime | DAG | LOCKED |
| CP-034 | Partial failure truthful | Copilot Work Runtime | outcome | LOCKED |
| CP-035 | Retry seguro | Copilot Work Runtime | idempotency | LOCKED |
| CP-036 | Pause por decisão | Copilot Work/Decision | persistence | LOCKED |
| CP-037 | Reload/resume | Copilot Work Persistence | no duplicate write | LOCKED |
| CP-038 | Audit trail workflow | Copilot Observability | coverage | LOCKED |
| CP-045 | Autonomia L0–L2 | Copilot Policy | safe reads/navigation/prepare | LOCKED |
| CP-046 | Autonomia L3 prepare | Copilot Policy/Work | PREPARE no-side-effect semantics | LOCKED |
| CP-047 | Autonomia L4 governed execute | Copilot Policy/Work | live AuthZ + Decision Gate + idempotency/audit + verified Outcome | LOCKED |
| CP-054 | Simulate/admin preview de action | Copilot Admin | parity | LOCKED |
| CP-076 | Playbook→WorkflowPlan sem endpoint hardcoded | Copilot Planner | authority separation | LOCKED |
| CP-168 | Candidate action de voz/reunião/frontline exige transition governada antes de write | Copilot Policy/Work | Decision/idempotency | LOCKED |
| CP-203 | External write/send/create/update é capability distinta de read e exige policy/Decision/outcome verification | Copilot External Actions | external write gate | LOCKED |
| CP-204 | Draft/preview é separado de send; mensagem sugerida nunca é enviada implicitamente | Copilot Communication/MFE | draft-send separation | LOCKED |
| CP-217 | Teams reply/send são capabilities governadas distintas de read/draft, com target preview, policy/Decision Gate e verified outcome | Copilot Teams/External Actions | Teams write gate | LOCKED |
| CP-235 | Automation Capability Registry/Projection mapeia capability semântica a executor versionado sem expor clicks/seletores/provider UI ao planner | Copilot Automation/Capability | executor abstraction gate | LOCKED |
| CP-236 | API/Function/RPA/Computer-Use executors implementam Port+Adapter substituível; RPA não é authority de business rule | Copilot Automation/Architecture | executor substitution gate | LOCKED |
| CP-237 | AutomationExecution possui lifecycle/correlation/inputHash/attempt/idempotency/timeout/error/outcome refs e impede dupla execução após retry/resume | Copilot Automation/Work | execution lifecycle gate | LOCKED |
| CP-238 | RPA worker/queue execution, quando priorizada, possui worker health/lease/concurrency/environment/package-version/credential isolation/audit | Copilot RPA/Infrastructure/Security | RPA execution reliability gate | LOCKED |
| CP-239 | Sucesso técnico do executor não equivale a sucesso de negócio; ação material exige postcondition/Outcome verification quando aplicável | Copilot Automation/Domain owners | verified business outcome gate | LOCKED |
| CP-240 | Notification/escalation deriva de estado/outcome verdadeiro e não é usada como prova de sucesso da execução | Copilot Notifications/Automation | truthful notification gate | LOCKED |
| CP-252 | Oportunidade descoberta por Process Intelligence vira candidate/Task/PREPARE com Evidence; nunca cria RPA/automation ativa automaticamente | Copilot Process Intelligence/Automation | opportunity governance gate | LOCKED |
| CP-265 | MCP/A2A tool/agent com write capability passa pela mesma Policy/Decision/idempotency/Outcome verification das Business/External Actions | Copilot Interoperability/Policy | delegated write gate | LOCKED |
| CP-277 | Métrica/semantic rule usada em Decision/Write é versionada e revalidada; mudança material invalida decisão anterior quando aplicável | Copilot Semantic Layer/Decision | semantic TOCTOU gate | LOCKED |
| CP-283 | Artifact Workspace possui artifact version/lifecycle/provenance/ACL e external share/send continua ação governada separada | Copilot Artifacts/Work | artifact lifecycle/share gate | LOCKED |
| CP-290 | Prescriptive output gera alternatives/trade-offs/PREPARE; `recommendation != authorization` e `simulate != apply` | Copilot Prescriptive/Decision | prescriptive action separation gate | LOCKED |
| CP-312 | Usuário/owner autorizado pode criar, inspecionar/listar, pausar, retomar e cancelar Recurring Governed Work persistente com recurrence versionada, timezone IANA, start/end bounds e refs bounded para Work/capabilities/scope/targets | DÉLIA Work/API | recurring-work lifecycle gate | LOCKED |
| CP-313 | Cada ocorrência agendada é determinística, correlacionada e idempotente; duplicate tick/retry/restart/reconciliation não duplica side effect e misfire/overlap semantics são explícitas | DÉLIA Work/Events/Automation | scheduled-occurrence reliability gate | LOCKED |
| CP-314 | Cada ocorrência material revalida identity, live Core/domain AuthZ, current Policy/Decision, connection/provider state e source permissions; `schedule != permission` e stored intent nunca vira autorização eterna | DÉLIA Work/Policy/Core/Domain owners | scheduled live-authorization gate | LOCKED |
| CP-315 | Anchor recurring report→send executa sem sessão de chat aberta: trigger determinístico → reads atuais → relatório grounded/versionado → `communication.email.send` governado → Outcome/Evidence/Audit, sem confundir report generated, provider accepted e verified outcome | DÉLIA Work/Artifacts/External Actions | recurring report-email end-to-end gate | LOCKED |

## 8. C6 — Product Work + Ecosystem + Human Experience

C6 habilita Product Work e Watch `OBSERVE|ADVISE|PREPARE` por default. `PREPARE` não produz side effect e Watch não dispara ACT autonomamente nesta fase. Isso não revoga L4 governed execute de C5 quando uma capability é explicitamente invocada/autorizada e passa novamente pelos gates materiais.

| ID | Requisito | Owner | Gate | Status |
|---|---|---|---|---|
| CP-039 | AI-ready SDK/templates | Shared/Portal/Copilot | contracts | LOCKED |
| CP-040 | Readiness scanner | Copilot Tooling | factual inventory | LOCKED |
| CP-041 | Coverage dashboard | Copilot Admin/Observability | metrics | LOCKED |
| CP-042 | Unknown app onboarding | Core/Portal/Copilot | no hardcode | LOCKED |
| CP-060 | Admin de capabilities/coverage | Copilot Admin | admin RBAC | LOCKED |
| CP-066 | Iframe Copilot Bridge SDK | Shared/Portal | contract/lifecycle | LOCKED |
| CP-067 | Unknown iframe onboarding | Portal/IframeBridge | generalization | LOCKED |
| CP-084 | Admin/observability packs/playbooks | Copilot Admin | version/eval/audit | LOCKED |
| CP-096 | Copilot Task persistente | Copilot Work | restart/resume | LOCKED |
| CP-097 | Copilot Case | Copilot Work/Product | lifecycle/evidence | LOCKED |
| CP-098 | Evidence Board | Copilot Case | same EvidenceRef | LOCKED |
| CP-099 | Interaction Room ligada a Case | Copilot + room owner | RBAC/context | TO_INVENTORY |
| CP-100 | Copilot Inbox | Copilot Work/MFE | lifecycle | LOCKED |
| CP-101 | Watch por condição/evento | Copilot Work/Events | dedupe/RBAC | LOCKED |
| CP-102 | Watch OBSERVE | Copilot Work | audit | LOCKED |
| CP-103 | Watch ADVISE | Copilot Work/AI | grounded alert | LOCKED |
| CP-114 | Reference Knowledge lifecycle | Copilot Knowledge | owner/version/scope | LOCKED |
| CP-115 | Decision Knowledge | Copilot Case/Knowledge | provenance/no-CoT | LOCKED |
| CP-116 | Experience Knowledge | Copilot Case/Knowledge | governed promotion | LOCKED |
| CP-117 | Solution Pattern lifecycle | Copilot Knowledge/Expertise | review/eval/version | LOCKED |
| CP-118 | Governed Learning Loop | Copilot Admin | no auto-publish | LOCKED |
| CP-119 | Expertise Studio lifecycle | Copilot Admin | draft→publish | LOCKED |
| CP-120 | Expertise/Playbook rollback | Copilot Admin | version/eval | LOCKED |
| CP-124 | Task Completion metric | Copilot Observability | metric validity | LOCKED |
| CP-125 | Case resolution learning candidate | Copilot Case/Knowledge | candidate only | LOCKED |
| CP-126 | Inbox decision→workflow resume | Copilot MFE/Work | correlation | LOCKED |
| CP-127 | Room summary grounded em Case | Copilot/Room | evidence/RBAC | TO_INVENTORY |
| CP-165 | Meeting Mode com lifecycle explícito de captura | Copilot MFE/API | explicit start/stop/indicators | LOCKED |
| CP-166 | Meeting consulta dados reais com permissões do usuário | Copilot API/Domain APIs | meeting read parity | LOCKED |
| CP-167 | Ata viva distingue transcript/resumo/decisão/action/outcome | Copilot Meeting/Artifact | semantic/evidence gate | LOCKED |
| CP-169 | Frontline Mode no mesmo MFE/API | Copilot MFE/API | frontline surface parity | LOCKED |
| CP-170 | Hands-free voice com fallback touch/text | Copilot Frontline | noisy/permission/accessibility tests | LOCKED |
| CP-172 | Training assistance referencia procedimento/desenho/revisão vigente | Copilot Knowledge/Domain owners | source freshness | LOCKED |
| CP-173 | Observação de processo gera somente Knowledge/Experience candidate | Copilot Knowledge | candidate provenance | LOCKED |
| CP-174 | Meeting/frontline candidate exige review/eval antes de virar conhecimento publicado | Copilot Knowledge/Expertise | governed learning | LOCKED |
| CP-181 | Meeting/Frontline accessibility e large-touch/shared-device UX | Copilot MFE | accessibility/frontline gate | LOCKED |
| CP-191 | Meeting pode associar face/voz enrolled a participante com confidence/correção | Copilot Meeting/Biometric | participant identity gate | LOCKED |
| CP-192 | Frontline pode usar biometria para identity assistance sem substituir sessão/RBAC | Copilot Frontline/Biometric | shared-device identity gate | LOCKED |
| CP-193 | Human Observation analisa somente padrões operacionais observáveis com Evidence/provenance | Copilot Frontline/Knowledge | process observation gate | LOCKED |
| CP-207 | Provider push/webhook/subscription normaliza para EventEnvelope com authenticity/dedupe/reconciliation | Copilot Connectors/Events | webhook lifecycle gate | LOCKED |
| CP-208 | External source só vira user/org Knowledge por candidate→review/eval/publish; nunca auto-truth | Copilot Knowledge/Governance | external learning gate | LOCKED |
| CP-212 | Personal connection data não vira shared Knowledge/Case/Room sem sharing/promotion explícito | Copilot Privacy/Knowledge | personal-data isolation gate | LOCKED |
| CP-213 | Subscription expiry/missed events/revocation exigem renewal/reconciliation/degraded state truthful | Copilot Connectors/Work | external event reliability gate | LOCKED |
| CP-218 | Teams change notifications de mensagens/canais/reuniões/transcrições/gravações, quando suportadas, entram por autenticidade→EventEnvelope→dedupe/reconciliation | Copilot Teams/Events | Teams event lifecycle gate | LOCKED |
| CP-220 | Teams meeting artifacts podem alimentar ata viva, Evidence, Task, Case, Room e Watch sem transformar transcript em decisão/ação automática | Copilot Teams/Meeting/Work | Teams meeting-to-work gate | LOCKED |
| CP-221 | App/tab/bot da DÉLIA no Teams, quando implementado, usa a mesma DÉLIA API, Core/RBAC, Policy, Evidence e Work runtime; nenhum `teams-copilot-api` paralelo | DÉLIA Teams/MFE/Platform | same-runtime surface gate | LOCKED |
| CP-224 | Chat privado, canal restrito, transcript e recording do Teams preservam source ACL; não viram shared Knowledge/Case/Room sem autorização/promotion explícita | Copilot Teams/Privacy/Knowledge | Teams private-resource isolation gate | LOCKED |
| CP-241 | Watch suporta `PREPARE` como estado/mode distinto de `ACT`, permitindo preparar ação sem side effect | Copilot Watch/Work/Policy | prepare-vs-act gate | LOCKED |
| CP-242 | Automation Hub Admin expõe automations/executions/workers/exceptions, owner/version/executor/status/outcome/evidence sem virar segundo workflow engine | Copilot Automation Admin/MFE/API | admin ownership/observability gate | LOCKED |
| CP-243 | Event-driven notification/escalation usa recipients/severity/dedupe/SLA/channel policy e pode combinar Minha DELPI/email/Teams/WhatsApp Business | Copilot Notifications/Watch | notification orchestration gate | LOCKED |
| CP-244 | Manual exception/human-in-the-loop pausa e retoma o mesmo Durable Workflow; não cria processo paralelo sem correlation | Copilot Work/Inbox/Decision | HITL resume gate | LOCKED |
| CP-253 | Process Intelligence UX expõe process map/variants/bottlenecks/conformance/automation backlog e before-after metrics com Evidence | Copilot Process Intelligence/MFE | process product gate | LOCKED |
| CP-258 | AI Control Tower oferece inventory/ownership/risk/health/eval/cost/value/incidents/dependencies/kill-switch UX sem conceder business permission | Copilot Control Tower/Admin | control-tower governance gate | LOCKED |
| CP-266 | MCP/A2A servers/agents possuem lifecycle `DISCOVERED→REVIEWED→APPROVED→ACTIVE→DISABLED/REVOKED` e health/usage no Control Tower | Copilot Interoperability/Control Tower | agent-tool lifecycle gate | LOCKED |
| CP-271 | Usuário possui controles para inspecionar/corrigir/apagar/desabilitar Personal Memory e recebe briefing personalizado grounded em authorities live | Copilot Memory/MFE | user memory control gate | LOCKED |
| CP-278 | Semantic Layer possui catalog/admin/lineage/conflict UX; mesma label com definições distintas não é fundida silenciosamente | Copilot Semantic Layer/Admin | semantic governance UX gate | LOCKED |
| CP-284 | Artifact Workspace suporta draft/review/version/collaboration/attach/export sem sobrescrever silenciosamente edição humana | Copilot Artifacts/MFE/Work | artifact collaboration gate | LOCKED |
| CP-291 | Operational Twin/Scenario Workspace mantém simulated state separado de production state e permite comparar alternativas com assumptions/Evidence | Copilot Twin/MFE | scenario isolation gate | LOCKED |
| CP-298 | Frontline Edge suporta modos `ONLINE/DEGRADED/OFFLINE_READ_ONLY/SYNCING`, event buffering idempotente e device/cache admin quando priorizado | Copilot Edge/Frontline | edge offline product gate | LOCKED |
| CP-305 | Capability Marketplace oferece lifecycle draft/review/approved/published/deprecated/revoked para packs/playbooks/Watches/automations/connectors/MCP/A2A/templates/models | Copilot Marketplace/Admin | marketplace lifecycle gate | LOCKED |
| CP-306 | Model lifecycle monitora quality/input/calibration drift, latency, availability, cost e correction/outcome metrics conforme model type | Copilot Model Governance/Observability | model drift gate | LOCKED |
| CP-316 | Product UX permite inspecionar Recurring Governed Work com status, recurrence/timezone, next scheduled occurrence quando derivável, last occurrence/outcome e ações governadas pause/resume/cancel, sem transformar schedule admin em permission authority | DÉLIA Work/MFE/Admin | recurring-work product UX gate | LOCKED |

## 9. C7 — Advanced Autonomy + Advanced Intelligence + Scale/Rollout

C7 não cria o conceito de ACT. Ele habilita autonomia avançada sobre capabilities já governadas, incluindo `L5` e selected Watch autonomous ACT.

| ID | Requisito | Owner | Gate | Status |
|---|---|---|---|---|
| CP-048 | Autonomia L5 limitada | Copilot Policy/Admin | allowlist/limits/kill switch | LOCKED |
| CP-049 | Emergency stop | Copilot Admin/Policy | kill switch | LOCKED |
| CP-050 | Rollout/cohort controls | Platform/Copilot Admin | canary/rollback | LOCKED |
| CP-052 | TCR/First Plan Success metrics | Copilot Observability | metric validity | LOCKED |
| CP-104 | Watch ACT | Copilot Policy/Work | autonomous trigger + autonomy/Decision | LOCKED |
| CP-112 | What-if Simulation | Domain analytics/Copilot | reproducible model | LOCKED |
| CP-113 | Simulate→Apply separado | Domain API/Copilot Policy | new gate | LOCKED |
| CP-121 | Model Router | Copilot Infrastructure | quality/cost/latency | LOCKED |
| CP-122 | Compute Policy | Copilot Policy | provider constraints | LOCKED |
| CP-129 | Anchor reclamação→8D→Watch→ação | Cross-domain/Copilot | full integration | LOCKED |
| CP-180 | Advanced realtime media possui budgets/backpressure/degraded mode/cost telemetry | Copilot Media/Infra | realtime reliability gate | LOCKED |
| CP-222 | Participação Teams ao vivo com raw realtime media só entra após evidence + ADR + tenant/media/privacy/cost/reliability gates; não é requisito do conector base | Copilot Teams/Realtime/Architecture | Teams advanced realtime gate | LOCKED |
| CP-245 | Autonomy level é resolvido por capability/context/risk/actor/limits/environment; não existe L4/L5 global irrestrito | Copilot Autonomy Policy | capability-scoped autonomy gate | LOCKED |
| CP-246 | L5 permanece OFF por default e exige allowlist, budgets/limits, kill switch, revalidation e verified Outcome por capability | Copilot Policy/Admin/Automation | autonomous ACT gate | LOCKED |
| CP-247 | Computer-use/UI automation é fallback avançado sandboxed/allowlisted/auditado e não substitui API/RPA determinístico sem justificativa | Copilot Automation/Security | computer-use boundary gate | LOCKED |
| CP-248 | Anchor autonomous operation `ready-to-invoice → execute → verify → notify` funciona end-to-end sob policy sem user prompt quando capability L5 estiver explicitamente aprovada | Copilot Automation/Cross-domain | autonomous invoicing anchor gate | LOCKED |
| CP-254 | Closed-loop process optimization nunca altera processo/policy automaticamente; autonomous ACT exige capability-scoped autonomy e before/after measurement | Copilot Process Intelligence/Automation | process closed-loop gate | LOCKED |
| CP-259 | AI Control Tower aplica cross-runtime budgets/cohorts/kill switches/rollback e incident containment por asset/capability sem prompt authority | Copilot Control Tower/Governance | mature AI governance gate | LOCKED |
| CP-267 | Autonomous A2A delegation exige approved agent/capability, bounded goal/context/budget, cancellation, verified result e L5 allowlist quando material | Copilot Interoperability/Autonomy | autonomous delegation gate | LOCKED |
| CP-272 | Advanced personalization optimization não cria hidden employee score, sensitive inference ou authority; user privacy/control permanece | Copilot Memory/Privacy | personalization optimization gate | LOCKED |
| CP-279 | Semantic federation/materialization optimization preserva owner/permission/freshness/lineage; cache nunca vira authority | Copilot Semantic Layer/Infrastructure | semantic scale gate | LOCKED |
| CP-285 | Scaled sandbox pools mantêm isolation/quotas/reproducibility/cleanup e não se tornam general-purpose corporate shell | Copilot Analysis/Infrastructure | sandbox scale gate | LOCKED |
| CP-286 | Advanced artifact generation/templates permanecem versioned/provenanced e publish/share continua policy-governed | Copilot Artifacts/Marketplace | artifact scale gate | LOCKED |
| CP-292 | Operational Twin avançado preserva source/freshness e cenário isolado; twin não vira OT/domain master | Copilot Twin/Domain owners | twin authority gate | LOCKED |
| CP-293 | Predictive/prescriptive output pode acionar ACT somente por explicit Policy/Decision/autonomy e verified Outcome; model output sozinho nunca autoriza | Copilot Predictive/Autonomy | prescriptive autonomy gate | LOCKED |
| CP-294 | `SIMULATE != APPLY`: qualquer Apply revalida live state/permissions/policy e gera novo action/decision context | Copilot Simulation/Decision | simulate-apply TOCTOU gate | LOCKED |
| CP-299 | Edge rollout escala por device class/cohort com signed/versioned packages/models, health e rollback | Copilot Edge/Control Tower | edge rollout gate | LOCKED |
| CP-300 | Offline bounded actions, se existirem, exigem explicit allowlist/expiry/idempotency/reconciliation; perda de cloud nunca amplia authority | Copilot Edge/Policy | offline action gate | LOCKED |
| CP-301 | Edge revocation/model/package update é rastreável e stale/revoked artifact deixa de ser usado no enforcement point definido | Copilot Edge/Model Governance | edge revocation gate | LOCKED |
| CP-307 | Production model deployment possui approved environment/cohort/health/rollback/kill switch e revoked model não é selecionável | Copilot Model Governance/Control Tower | model deployment gate | LOCKED |
| CP-308 | Marketplace publish/enable exige manifest/dependencies/permissions/data scopes/evals/compatibility e não concede RBAC/provider scope sozinho | Copilot Marketplace/Security | marketplace enable gate | LOCKED |
| CP-309 | Executable/model/connector packages usam supply-chain controls apropriados: trusted publisher, hash/signature when applicable, dependency/license/vulnerability review e revoke path | Copilot Marketplace/Security | AI supply-chain gate | LOCKED |
| CP-310 | Nenhum Model/Marketplace/MCP/A2A/Edge asset pode ampliar Core/domain/provider authority por instalação, prompt, metadata ou package manifest | Copilot Security/Governance | no asset permission elevation gate | LOCKED |

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

## 15. C0.S1 naming / physical ownership linkage — accepted review

Evidence anchors: `68` §4; `50` §3/§21; `17` §2; `52`; `21` §2; ledger C0.S1 review event.  
Review: `ARCHITECTURE_REVIEW_C0_S1`; `REVIEWED_HEAD=c822f0e72495256c3459a4b36b9c37a3bba95cbb`; verdict `ACCEPT_WITH_RESIDUAL`.

| CP | Naming/ownership note (C0.S1 accepted) | Status unchanged |
|---|---|---|
| CP-130–CP-134, CP-140 | architecture gates; no path invent | PLANNED |
| CP-138 | owner label → Portal/DÉLIA MFE | PLANNED |
| CP-141 | path → `delia-api/` | LOCKED (C1) |
| CP-142 | path → `plugins/delia/` | LOCKED (C1) |
| CP-143 | `id=delia`; manifest source DÉLIA; registry Core | LOCKED (C1) |
| CP-144 | `/apps/delia-api/`, `/apps/delia` | LOCKED (C1) |
| CP-145 | containers `delpi-delia-api`, `delpi-delia` | LOCKED (C1) |
| CP-146–CP-147 | DÉLIA platform/API ownership labels | PLANNED |
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
C0.S2_AUTHORIZED = YES
FOUNDATION_FREEZE = NOT APPROVED
PROGRAM = PLANNED / NOT_STARTED
C0 = NOT_STARTED
DÉLIA_RUNTIME_DIFF = NONE
NEXT = C0.S2 — Authorities / bounded contexts
```
