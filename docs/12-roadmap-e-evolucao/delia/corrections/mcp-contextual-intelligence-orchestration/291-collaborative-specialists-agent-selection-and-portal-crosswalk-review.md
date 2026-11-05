# 291 — Crosswalk: DÉLIA central, especialistas participantes, catálogo de agentes e Portal

**DATA:** 2026-11-05  
**NATUREZA:** `DOCUMENTATION_REVIEW_ONLY` / `NO_CANONICAL_CHANGE` / `NO_RUNTIME_CHANGE`  
**OBJETIVO:** confrontar discussão de produto (DÉLIA central, TÉO/CAIO como participantes visíveis ou especialistas selecionáveis, MCP tools/resources/prompts, delegação A2A, navegação Portal, continuidade e aprendizado) com autoridades e estado documental.  
**DECISION STATUS:** `ARCHITECTURE_DECISION_REQUIRED` para seleção user-facing de agentes e a nova semântica de participante/handoff; demais capacidades em grande parte `ALIGNED_WITH_EXISTING_TARGET`.  
**EVIDENCE LIMIT:** revisão documental via GitHub, não reexecução de ambiente/runtime; linhas de documentos históricos podem estar defasadas. Fase/NEXT somente no 16 e ledger atualizados.

## 1. Authorities and source hierarchy

Order: Project Instructions/.cursor → 16 → 50 → 17 → 49 → 51 → 52 → 21 → 20 → 25 → technical architecture → 24 → thematic 53–66 → execution ledger. Supporting: docs 116 (frontend), 121 (conversation queue), personality/README, 60, 61, 66, 290. This report is not authority over frozen specs.

## 2. Alignment matrix

| Desired product behavior | Canonical support | Assessment / status |
|---|---|---|
| Single central DÉLIA coordinator spanning apps/domains | 24 §1–6, 50 §5–8, 17/25 | `ALIGNED / TARGET` |
| Contextual expertise via TÉO/CAIO/DAVI/VISTA knowledge | 24 §5, CP-072/073/074/075/077/083/086/087, expertise/knowledge 17 §3 C3-T6 | `ALIGNED`; Packs/Playbooks foundation ≠ Studio/runtime or specialist-owned MCP Resources automatically proven |
| MCP tools, knowledge resources, prompts; live owner capability catalog | 60 §1–5 and 24 §19 | `ALIGNED`; tools/list current bounded live MCP, Resources/Prompts consumption capabilities contract/runtime `TO_INVENTORY` |
| DÉLIA uses multiple independent MCPs and delegates bounded tasks to approved A2A agents | 60 §3, §9, §12–13, CP-263–267 | `ALIGNED / TARGET`; delegated agents never own permissions, no unrestricted conversation |
| Human can choose named TÉO/CAIO as a standalone agent in UI | 24 §5 explicitly single DÉLIA with no departmental runtimes; **CP-071 'Uma única DÉLIA sem seleção de agente' LOCKED**; 50 §22 forbids Chat agent-id runtime migration | `DIRECT_PRODUCT_REQUIREMENT_CONFLICT`; `ARCHITECTURE_DECISION_REQUIRED` before enabling selectable user-facing specialist |
| Specialist visually joins the same conversation, distinct identified participant, user can address specialist | 24 conversation, 60 A2A delegation, 36 Room target, 116 conversation UI | `PRODUCT_GAP`: no inspected frozen contract for multi-speaker participant role, invite/leave, message attribution, routing or shared thread; do not assume Agent/MCP result == independent speaking actor |
| A delegated agent takes conversation or task over and then returns to central DÉLIA | 60 §9 bounded delegation, A2A, single DÉLIA constraint | `PARTIAL_TARGET`; delegation contract exists, user-visible handoff/thread ownership contract not confirmed |
| Plugin-like catalog/enable/disable/specialist configuration | 66 §§8–10, CP-119 Expertise Studio, CP-305/308/309, 59 AI Control Tower | `ALIGNED_TARGET`; C6 catalog/draft UX and C7 publish/enable, owner-controlled assets, no install=RBAC; not a currently proven specialized-agent UI |
| Agents/plugins navigation components | 116 §2.1, §2.2: AgentNavigation/PluginNavigation in plugin-ui and DÉLIA rail, disabled catalog_unavailable/contract_unavailable | `UI_REUSE_PROVEN_AT_116_SHA`; active catalog, agent selection and participant runtime `NOT_PROVEN` |
| "DÉLIA, open Commercial Portal and connect CAIO" / reverse from Transforma Mais | CP-002..012, 17 §22.3 DELIA.PORTAL.HOST, 50 §8, CP-148/149 | `PARTIAL`: Portal=host/navigation, Core=/me/apps app access, Companion Dock same MFE; route actions and WorkspaceContext are planned/contracted, agent-binding cross-app is not a frozen implemented contract |
| Same persistent conversation switching apps and specialist without losing history | 24 §6, 21 §8, 61; 121 §1–4: request-scoped InteractionSession and client-carried untrusted context at audited SHA | `ARCHITECTURAL_GAP`: durable conversation/thread/participant history and cross-app routing/continuity not proved; no automatic global context persistence; do not substitute Personal Memory or knowledge |
| Personal and organizational learning across specialists | 24, 61 §§1–14, 40 target, 66 marketplace | `ALIGNED_TARGET`; Evidence→candidate→owner/review→eval→version→publish; Personal Memory never AuthZ or business fact |
| Email/Teams/Microsoft 365/Google/WhatsApp/Slack/GitHub and more | 24 §8, 55, 56, CP-200/201/215 etc | `ALIGNED_TARGET`; OAuth/consent/scopes/data privacy, draft!=send, provider source ownership; not proven live for all providers |

## 3. Fundamental conflict, no silent reconciliation

- 24 §5: **'Uma DÉLIA dinamicamente especializada por Expertise Packs, Playbooks, Knowledge, Personal Memory, contexto atual e capabilities autorizadas. Sem runtime de agentes departamentais.'** It also says **external A2A agents are integrations, not user-facing alternatives**.
- 25, **CP-071 LOCKED**: **'Uma única DÉLIA sem seleção de agente'**.
- New proposal wants an explicit specialist selector, a selected TÉO/CAIO identity in chat, inviteable participant and possibly truly delegated separate agent. That is **not merely a UI implementation detail**; it changes the product contract and may conflict with CP-071 even if runtime is shared.
- Distinguish possible concepts before changing authority: **MCP tool** (no speaker identity), **contextual specialist profile** (same DÉLIA execution, separate presentation label only if contract approved), **visible participant** (multi-speaker thread contract), **delegated agent** (separate bounded Agent run/A2A task, not necessarily a user-facing product), **external agent** (provider/A2A governed).
- Product Master must decide whether CP-071 remains strictly binding or gets formally superseded with traceability, compat/security/phase implications. Do not silently treat selectable profiles as a workaround. Preserve DÉLIA single product identity, no Chat runtime reuse, no user-granted permissions.

## 4. Product decisions needed (not implementation approval)

1. `DECISION_AGENT_SELECTION`: permit user-facing switch/invite of specialist profiles? Difference between selected profile and independent agent? What is source of expert names/profile catalog and Core permissions?
2. `DECISION_PARTICIPANT_PROTOCOL`: same conversation multi-participant semantics, message speaker/ref, who authored content, control of responses, invitation, direct address, handoff, return, visibility and user attribution; distinguish representative UI from actual delegated run.
3. `DECISION_CONTEXT_HANDOFF`: session/thread identity across page/dock/app contexts; bounded transfer under Core/Domain/AuthZ, revocation, privacy, persistence/retention; avoid passing all history or raw private content to another provider.
4. `DECISION_NAVIGATION`: Portal command contract vs DÉLIA plan; Core `/me/apps`, published route, Portal executes, not LLM selectors/clicks; 'open Comercial then connect CAIO' as composed legitimate capabilities only after contract approval.
5. `DECISION_MCP_KNOWLEDGE`: Tools/Resources/Prompts actual inventory per owner; knowledge asset governance vs untrusted MCP metadata/instructions; no agent instruction override.
6. `DECISION_ADMIN_CATALOG`: reuse Core app/approval projection, Expertise Studio, Capability Marketplace and plugin-ui AgentNavigation/PluginNavigation; publish/enable not permission; no second registry/workflow/permission authority.

## 5. Evidence and implementation boundaries

- `EXISTING_EQUIVALENT=YES` for central DÉLIA, Portal host, Core access, MCP owner tools/list, expertise foundations, plugin-ui navigation primitives.
- `EXISTING_EQUIVALENT=TO_INVENTORY` for actual selected-specialist participant protocol, durable cross-app thread, UI asset catalog/approval and MCP resource/prompt materialization; `REUSE_DECISION=REUSE|EXTEND` favored, but no NEW approval without ownership proof.
- `RUNTIME_IMPLEMENTED` must be checked by current HEAD and evaluated config; a spec or a previously exported UI component is not runtime or authorized launch.
- Proposed path: Product Master explicit reconcile/ADR first → map CP-071 and related CPs and doc24/60/66 → contract-first prototype using existing UI and Pydantic AI runtime, bounded security/eval, no new planner nor duplicate agent runtime → acceptance by real thread and owner results. Freeze decisions maintained pending authority review.

**VERDICT:** discussion aligns with North Star and most capability families, but selectable specialist agents and visible co-participants require formal product/contract decision and cross-app persistence is a genuine gap; do not silently overwrite `CP-071`.
