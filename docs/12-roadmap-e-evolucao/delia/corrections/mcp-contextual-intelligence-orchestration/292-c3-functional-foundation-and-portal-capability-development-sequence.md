# 292 — DÉLIA · sequência de estabilização funcional C3 → primeira capability Portal

**Data:** 2026-11-05  
**Tipo:** `COORDINATION_ROADMAP / DOCUMENTATION_ONLY / NO_CANONICAL_PHASE_ADVANCE`  
**GitHub HEAD examinado:** `44dd236a2ead61a00d8c66339df3735f03972716` (docs após CP-071). **Último código de execução MCP avaliado:** `545775a821f488d7a2614d8451ec2be930001f97`.  
**Autoridades:** Project Instructions/.cursor → 16 → 50 → 17 → 49 → 51 → 52 → 21 → 20 → 25 → arquitetura técnica → 24 → 60/61/66 → ledger. Refs docs 116/121, 283/286–291. Este roteiro **não substitui NEXT/phase do 16**, não autoriza deploy ou C4/C5/C6, e não declara testes próprios.

## 1. Diagnóstico factual, sem extrapolação

- `PROVEN_BY_CODE_REVIEW`: `delia-api/app/infrastructure/orchestration/pydantic_ai_investigation.py` ainda contém `_capability_tool_signature`, `_safe_tool_name` e montagem manual de ferramentas Python MCP; migração `MCPToolset` não está implementada no HEAD examinado.
- `EXECUTOR_REPORTED_PASS`: DAVI produto 50220013 e 99999999 com GROUNDED/provenance, VISTA playlist READ grounded; correções no adapter de erro e renderer no commit `545775a821`. `VISTA_ANALYZE=PARTIAL` (schema/operation owner residual).
- `PROVEN_BY_CODE_REVIEW`: `plugins/delia/src/App.tsx` envia `buildInteractionContext(turnsRef.current)` por request; `handle_interactive_turn.py` cria request-scoped sessions segundo auditoria doc121. Cross-app/multi-agent durable thread não comprovada.
- `PLATFORM_FOUNDATION`: Core /me/apps e Portal host/federation/Companion Dock com ownership documentado 17/50/51; app navigation commands CP-002..012 and WorkspaceContext semantics target, implementation must inventory at CURRENT HEAD.
- `CANONICAL_PHASE`: doc16 preserva `C3_EXECUTED=NO` em seu snapshot e I04 residual; doc16 `NEXT=AWAIT_PRODUCT_MASTER_COMMAND` no último snapshot de coordenação específico, sem evidência de aceite integral posterior. Ledger registra progressos bounded. Não inferir C3 complete.
- `PRODUCT_DIRECTION`: 24 §5/CP-071 atualizado permite especialistas selecionáveis e participantes, mas não constitui runtime/contract authorized; MCP != Agent.

## 2. Quatro gates funcionais em ordem de dependência (não fases canônicas)

### F0 — Interoperabilidade MCP nativa e governada (bloqueador imediato)

**OWNER:** DÉLIA Infrastructure Pydantic AI + Application governance; owner MCP continua autoritativo por schema/capabilities/dados. **REUSE:** existing Pydantic AI runtime + native MCPToolset when supported by installed version, Core AuthZ + owner fresh tools/list + Evidence/Policy/Decision.
- Verificar versão instalada e APIs reais de `MCPToolset` e hooks antes de migrar; decidir boundary de execução governada pre-call. Não conectar toolset cru ao Agent se bypassar gates.
- Red→green, migrar tools/schemas/transporte e remover geração manual/deprecated consumers em **mesma entrega** (sem dual-mode permanente); proteger owner token exchange, live capability class, PREPARE/ACT, deadlines/cancellation, untrusted data and provenance.
- Provar end-to-end com **DAVI** (product detail/search/structure), **TÉO** (context real), **VISTA** (read real). `analyze` apenas PASS quando própria análise retorna resultado válido; schema gap corrigido no owner após confirmação. Negativos: unauthorized, missing schema, tool poisoning, revoked/UNKNOWN, id unknown, timeout.
- Acceptance = three owners with grounded client answer; clean legacy residual; full test/eval security; actual SHA/model/config. Without this **NO F1 promotion**.
- **Status:** `IN_PROGRESS_BY_EXTERNAL_EXECUTOR / EVIDENCE_PENDING` (user reports migration assigned; no commit observed yet).

### F1 — Inteligência e interação confiáveis

**OWNER:** DÉLIA Application/Domain + infrastructure Agent, MFE consumes.
- Reuse native Agent multi-tool sequential/parallel when independent; no second planner. Test straightforward question, discovery→execute, multiple related reads, cross-owner comparison with nonfabricated evidence, unsupported/not-found, clarification→follow-up→answer, first/second turn continuity and truthful limitation.
- Keep `InvestigationAnswer` structured outputs; ensure source provenance from owner evidence and actual delivered content, not mere HTTP200 or MCP protocol success.
- Audit current conversation persistence vs client-carried context. Implement only justified typed continuity contract after architecture decision; no hidden personal memory or unauthorized cross-user data.
- Capture actual latency, model stage duration/token count where provider offers, timeout, concurrency and user-visible failure feedback.
- **Acceptance:** repeatable fixed real task battery across paraphrase/renaming, two-turn follow-up and multi-MCP query, with real outcome and no repeated manual patches per owner. **Status:** `PARTIAL`.

### F2 — User-facing DÉLIA experience fit (page + Companion Dock)

**OWNER:** plugin-ui presentation, DÉLIA MFE composition, Portal host chrome; use existing ConversationWorkspace, ActivityViewer/EvidenceDetails, MessageComposer, status, navigation.
- Prove send/stream/stop, spinner/activity, structured response, source disclosure, errors, clarification, conversation context, route transitions, page/dock parity, logout identity switch. Do not enable fake AgentNavigation/catalog ahead of contract.
- **Acceptance:** an authenticated human can execute F1 tasks through real Portal page and dock without raw technical envelopes or state leakage. **Status:** `PARTIAL/TO_VERIFY_ON_CURRENT_HEAD`.

### F3 — First DÉLIA-native Portal capability (after F0–F2 acceptance)

**OWNER:** Core app visibility/AuthZ and authorized routes; Portal navigation; DÉLIA semantic proposal/governed coordination and MFE user-facing context. **EXISTING_EQUIVALENT:** Core /me/apps, Portal host/navigate, CP-002..012, WorkspaceContext; **REUSE_DECISION:** REUSE|EXTEND contracts after HEAD inventory, never duplicate app registry.
- First read: **'Quais aplicativos posso acessar?'** → current Core-authoritative app list via existing contract and access; no JWT frontend roles.
- First navigation: **'Abra o Portal Comercial'** → resolve only Core-published eligible app/route, typed PlatformCommand/Portal navigation, no LLM-supplied URL/selectors/clicks. Observe actual route change as postcondition, not model reply alone.
- First context: **'O que estou vendo aqui?'** → published bounded WorkspaceContext/route/EntityRefs (where available), with optional verified domain read; host context is not permission nor factual business truth.
- Add specialist/CAIO selection **only later** after CP-071 participant/speaker/context contract + Core approval/profile catalog and cross-app continuity; no need to create agent runtime for this first Portal capability.
- **Acceptance:** allow/deny apps; forbidden route fail closed; navigation actual; context accurate; page/dock consistent; user switch isolation. **Status:** `PLANNED / NOT_AUTHORIZED_BY_THIS_DOC`.

## 3. Next-phase expansions (not current blocker)

After four gates: provider-neutral external connectors email/Teams (55/56), Expertise Studio/Marketplace (41/66), agent profiles and chat participants (CP-071; 24 §5), durable Work/Room and personal/org knowledge. Distinguish `MCP != Agent`; no new runtime solely for visual persona.

## 4. Operational gate and reporting

Before code: reanchor HEAD/status + authority sequence; identify CP/RQ, owner, contract, consumers; `EXISTING_EQUIVALENT=YES|NO|TO_INVENTORY`, `REUSE_DECISION=REUSE|EXTEND|NEW`; smallest legitimate diff; prove task outcome on real authorized data. Tests and production release status separate:
`SOURCE_REVIEW=PROVEN`, `LOCAL_TESTS=TEST_NOT_RUN_BY_COORDINATION`, `MCPTOOLSET_MIGRATION=EVIDENCE_PENDING`, `PRODUCTION_RELEASE=NOT_AUTHORIZED`. If native toolset cannot enforce pre-execution governance, `ARCHITECTURE_DECISION_REQUIRED` rather than bypass. If new code reveals incompatible frozen contract, `EXECUTION_DRIFT` rather than silent redesign.

**Priority recommendation:** finish externally assigned F0, review independent code/real matrix, then F1+F2 measured as one functional acceptance battery, then F3 limited Portal navigation. The order is a coordination proposal and may only affect authoritative phase/NEXT through separate authorized decision.
