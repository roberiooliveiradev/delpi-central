# 21 — VISTA/TV RESIDUAL CLOSURE — D-8 + A5 + B3 + Contratos

**Data:** 2026-10-31
**Mandato:** fechamento técnico dos resíduos pós-B1/B2/B3 —
política D-8 regularizada, canal humano de consentimento A5,
revisão dos workflows B3, superfície six-tools, drift documental
e readiness B4/B5.

## DECISÃO CANÔNICA — D-8 (SUPERSEDE política condicional)

| Campo | Valor |
|---|---|
| Decisão | `DELETE_DATA_MODEL_CONFIRMATION = ALWAYS` |
| Owner | Product/Architecture (solicitante) |
| Data | 2026-10-31 |
| Justificativa | destrutiva em domínio de apresentação exige consentimento humano verificável independentemente de consumidores detectados |
| Regra anterior | `direct` sem consumidores / `confirm` com consumidores — **supersedida** (mantida como histórico no doc 20) |
| Contrato efetivo | `operations.delete_data_model.confirmationPolicy = "confirm"`, `risk = "destructive"` |
| Descoberta | `CONSUMER_DISCOVERY = REQUIRED_FOR_IMPACT` — `collect_source_consumer_field_refs` (canônica, cobre modelId) |
| Fail-closed | `INCOMPLETE_DISCOVERY = DEPENDENCY_UNRESOLVED` (409) — cfg de slide inspecionável é requisito |
| Zero consumidores | aceito apenas após consulta conclusiva (`verificationStatus: "CONCLUSIVE"`) |
| Consent/echo | `consent_artifact` + `target_echo` obrigatórios no COMMIT |
| Preview de impacto | `dependencyImpact[]` no PREPARE: modelId, consumerBlocks, consumerFieldRefs, consumers[{blockId,fields}], policy, status |

## R1 — D-8 → CLOSED

Implementado em `dispatch_service.preview_change` (seção D-8 após
`orderedOps`): para cada op `delete_data_model` no plano selado,
anexa `dependencyImpact` calculado sobre o `nativeConfig`
resolvido pelo patch service; cfg ausente → `DEPENDENCY_UNRESOLVED`.
Em uso → `_op_delete_data_model` falha com `MODEL_IN_USE` (owner
bloqueia — sem cascata sem contrato). Testes:
`test_d8_prepare_shows_conclusive_impact`,
`test_d8_prepare_failclosed_when_discovery_inconclusive`.

## R2 — Consentimento humano A5 → CLOSED (backend) / EXTERNAL_CHANNEL_UNVERIFIED (GPT Builder)

- Canal confiável EXISTE: `vista_consent_routes.py` —
  `GET /consent/proposals/{id}` (view selada) +
  `POST /consent/challenges/{id}/approve` com `step_up` claims
  (token fresco, actor binding).
- `VistaConsentService` cobre: proposal/plan-hash/target binding,
  TTL, single-use (`consume_for_commit`), replay protection,
  `verify_for_commit` no COMMIT — testado por
  `test_vista_consent_foundation.py`.
- Artefacto não pode ser fabricado pelo modelo (challenge_id minted
  pelo backend; `confirmation=true` inexistente).
- Lacuna externa: aprovação humana via GPT Builder/Portal depende
  do canal do host — registrada `EXTERNAL_CHANNEL_UNVERIFIED`.

## R3 — Revisão B3 → NO_PATCH_REQUIRED (com D-8 reforçada)

| Workflow | Owner | AuthN/AuthZ | CAS | Consent | Read-back | Defeito |
|---|---|---|---|---|---|---|
| `delete.playlist` | `playlist_lifecycle_service` | `TV_WRITE`+governed | proposal hash | A5 always | VERIFIED + consume | nenhum |
| `delete.data_model` | sealed pipeline + `_op_delete_data_model` | `TV_WRITE`+governed | content_hash | A5 always (D-8) | `_verify_postcondition` | nenhum |
| `execute.playlist_history.restore` | `playlist_lifecycle_service` | `TV_WRITE`+governed | `expectedRevision` CAS → 409 | contrato REST não exige | playlist retornada | nenhum |

Restore não recebeu confirmação adicional: contrato canônico
(`restore_playlist_history`) exige `need="edit"` + `expectedRevision`
CAS — não é destrutivo na política do owner; `NO_PATCH_REQUIRED`.

## R4 — Superfície six-tools → CLOSED

`MCP_TOOL_COUNT = 6`, `VISTA_GPT_ACTION_COUNT = 6` — verificado no
OpenAPI regen e em produção (digests B1–B3). Novas capacidades B3/D-8
entraram como entidades/ops dos verbos existentes; sem aliases
legados, sem endpoints de bypass.

## R5 — ChatGPT/consumidores externos → OBSERVED

Seis tools expostas ao ChatGPT (evidência do operador) —
registrada como observação de consumidor, **não** como
certificação universal; re-import do OpenAPI no GPT Builder
permanece follow-up operacional (doc 17).

## R6 — Drift documental

| SOURCE_A | SOURCE_B | DRIFT | DECISION |
|---|---|---|---|
| doc 20 (D-8 condicional) | este doc | DOCUMENTATION_DRIFT | doc 20 permanece como histórico; D-8=ALWAYS vigora |
| `delete_data_model.direct` (catalog pre-B3) | `confirm` atual | CONTRACT_DRIFT resolvido | catálogo atualizado + destructive |
| teste anti-restore (attr scan) | restore via execute | CONTRACT_DRIFT resolvido | teste reescrito para propriedade real (viewer→403) |

## B4/B5 — Readiness matrix

| Onda | Gate | Owner | Status |
|---|---|---|---|
| B4 export | `export_mdd` existente (template_routes) | `SlideTemplateLibraryService` | contrato existe — pronto p/ inventário |
| B4 import | `import_preview`/`import_apply` existem | idem | handoff binário — contrato a validar |
| B4 playlist MDD | workflow MDD de playlist | a inventariar | `TO_INVENTORY` |
| B5 shares | `playlist_routes` share/delete-share | `require_playlist_access` manage | inventário ok — ACL Core boundary pendente |
| B5 permissions | RBAC global | **Core owner** | `BLOCKED_BY_OWNER_CONTRACT` até decisão Core |

## Verificação

- Suite: **2331/2331 PASS** (inclui 2 novos testes D-8).
- Deploy: apenas se houver diff publicado (há — D-8 impact).

## Classificação

`R1=CLOSED` `R2=CLOSED+EXTERNAL_CHANNEL_UNVERIFIED`
`R3=NO_PATCH_REQUIRED` `R4=CLOSED` `R5=OBSERVED` `R6=CLOSED`
**Execução: PASS**
