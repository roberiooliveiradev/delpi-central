# Doc 160 — CF-UX-053 inventário de canal por capability (09/11/2026)

**Estado:** `PROVEN` no código HEAD (registry `governed_writes._capability_table` + doc 124 rev. A).  
**Canal efetivo em produção no inventário:** `portal` (`portal_consent_required=true`, `conversational_act_armed=false`).  
**Cutover conversacional:** `CUTOVER_BLOCKED` — aguarda doc 150 §20.10.

## DIRECT_ALLOWED (13) — sem consentimento de canal

| Capability | Risco | Contrato MCP | Canal efetivo | Consentimento | AuthZ |
|---|---|---|---|---|---|
| checklist.draft_create | DIRECT | execute phase=direct | n/a | nenhum | manage |
| checklist.draft_update | DIRECT | execute phase=direct | n/a | nenhum | manage |
| clarification.open | DIRECT | execute phase=direct | n/a | nenhum | access |
| pendency.create | DIRECT | execute phase=direct | n/a | nenhum | access |
| pendency.claim | DIRECT | execute phase=direct | n/a | nenhum | access |
| pendency.transition | DIRECT | execute phase=direct | n/a | nenhum | access |
| item.mark_not_applicable | DIRECT | execute phase=direct | n/a | nenhum | access |
| item.revert_not_applicable | DIRECT | execute phase=direct | n/a | nenhum | access |
| item.request_correction | DIRECT | execute phase=direct | n/a | nenhum | access |
| document.post_message | DIRECT | execute phase=direct | n/a | nenhum | access |
| document.answer_adjustment | DIRECT | execute phase=direct | n/a | nenhum | access |
| received.post_message | DIRECT | execute phase=direct | n/a | nenhum | dre |
| received.create_adjustment | DIRECT | execute phase=direct | n/a | nenhum | dre |

Teste de classificação: `test_registry_marks_draft_caps_direct` + suite direct execution.

## CONFIRMATION_REQUIRED (35) — CURRENT_RUNTIME = Portal V014

Política aplicável hoje: PREPARE → `proposal_pending_confirmation` → `confirmation_url` (V014) → COMMIT.  
`confirmation=true` presente no contrato MCP; **não** autoriza sem V014 enquanto ack Security ausente.

| Capability | Gate | Canal efetivo | Consentimento exigido |
|---|---|---|---|
| evidence.decide_version | manage | portal | V014 |
| evidence.decide_item_set | manage | portal | V014 |
| review.record_decision | manage | portal | V014 |
| clarification.resolve | access | portal | V014 |
| competence.open | manage | portal | V014 |
| pendency.reassign | access | portal | V014 |
| pendency.confirm_classification | access | portal | V014 |
| package.finalize | manage | portal | V014 |
| package.reopen | manage | portal | V014 |
| package.complement | manage | portal | V014 |
| package.submit_review | manage | portal | V014 |
| package.assignment_create | manage | portal | V014 |
| package.assignment_deactivate | manage | portal | V014 |
| package.start_review | manage | portal | V014 |
| package.confirm_terminal_rejection | manage | portal | V014 |
| package.revert_terminal_rejection | manage | portal | V014 |
| item.reverse_decision | access | portal | V014 |
| item.cancel | access | portal | V014 |
| item.create_exceptional | manage | portal | V014 |
| item.review_correction | access | portal | V014 |
| document.cancel | access | portal | V014 |
| received.confirm_adjustment | dre | portal | V014 |
| catalog.entry_create | manage | portal | V014 |
| catalog.entry_update | manage | portal | V014 |
| catalog.entry_deactivate | manage | portal | V014 |
| catalog.entry_reactivate | manage | portal | V014 |
| checklist.version_submit | manage | portal | V014 |
| checklist.version_return | manage | portal | V014 |
| checklist.version_discard | manage | portal | V014 |
| checklist.version_publish | manage | portal | V014 |
| checklist.version_inactivate | manage | portal | V014 |
| checklist.doc_requirement | manage | portal | V014 |
| p3.confirm_cutoff | manage | portal | V014 |
| p3.upsert_reconciliation | manage | portal | V014 |
| p3.revalidate | manage | portal | V014 |

**Operação de referência reproduzida:** `checklist.version_publish` → `portal_consent_required=true` em produção (pré-cutover).

## TARGET (após §20.10 ACCEPT)

Mesmas 35 com `CLARA_CONSENT_CHANNEL=conversational` + ack `R-CLARA-01-TEO-EQUIVALENCE-ACCEPTED` → `portal_consent_required=false`, prova `mcp_tool_confirmation`, sem URL obrigatória. Smoke ChatGPT real obrigatório antes de `ACCEPT`.
