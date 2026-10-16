# BPMN MODELER — V1 STABLE PRODUCT BASELINE

> **Release:** V1 stable product baseline (G10 — Final Closure)
> **Baseline SHA:** `4ad30b5f21aebb85aee7df1122f17ba130cedf3f` (`main`)
> **Data:** 2026-10-16
> **Status:** `IMPLEMENTATION: PASS / CLOSED` — `FUNCTIONAL BLOCKERS: 0` — `ACTIVE IMPLEMENTATION GAPS: 0`

## Propósito do produto

**Meu Modelador de Processos** — produto autônomo de modelagem BPMN governada: criar, importar, editar, validar, versionar e exportar processos em **BPMN 2.0 XML + BPMN-DI** como artefato canônico único. O Transformômetro consome a mesma superfície de edição compartilhada, mas possui seus próprios artefatos, persistência e autorização — `EDITOR É COMPARTILHADO. ARTEFATO NÃO.`

## Artefato canônico

```text
BPMN 2.0 XML + BPMN-DI no mesmo documento
  Meu Modelador     → bpmn_modeler.models / working copies / revisions
  Transformômetro   → transformometro.processo_bpmn_documents / _revisions
  Validação única   → shared/bpmn_validation (intake → lxml → XSD vendored → regras)
```

Nenhuma autoridade paralela (JSON visual, DI separado, proxy XML/FK, bypass de persistência) existe ou é permitida.

## Capacidades entregues (complete para o escopo V1 governado)

| Área | Estado |
|---|---|
| Model CRUD + working copy + autosave com read-back autoritativo | PASS/CLOSED |
| Revisões imutáveis append-only + restore com `origin=restore` | PASS/CLOSED |
| Ownership pessoal fail-closed (`Model.created_by`; foreign → 404; superadmin não atravessa) | PASS/CLOSED |
| Editing profile governance (CREATE_EDIT allowlist fail-closed em palette/context-pad/replace/panel) | PASS/CLOSED |
| CREATE_EDIT breadth (activities, gateways, events, collaboration, artifacts) | PROVEN — E2E por família |
| Properties breadth (BpmnCorePropsProvider: calledElement/conditionExpression/defaultFlow + doc/event-refs) | PROVEN — WAVE E |
| Preserve-only + extensões desconhecidas (fail-closed `UNSUPPORTED_EXTENSION_SERIALIZATION`) | PASS/CLOSED |
| Round-trip/interoperabilidade (import→RB→edit→export→compare→reimport) | PASS/CLOSED — 16 E2E + 21 unit |
| Produtividade (clipboard, multi-select, lasso, search, palette search semântica, resize, shortcuts, grid/snap, pan, global-connect) | PASS/CLOSED |
| Auto-layout ELK worker-only + preview Accept/Cancel | PASS/CLOSED |
| Live preview readonly viewer, pan/zoom/fit, timeout/retry, terminal error UI | PASS/CLOSED — G9 |
| Watermark bpmn.io bottom-left padronizado (licença, sem overlap) | PASS/CLOSED — G9-BRAND-1/2 |
| Runtime provenance (OCI revision + build-info.json + /health) | PASS/CLOSED — LOCAL INTEGRATION RUNTIME |
| TM external immutable revision reference (G5/ADR-005) | PASS/CLOSED |
| TM-native BPMN document (G7) | PASS/CLOSED |
| Migração flowchart_v1 → BPMN nativo via TÉO PREPARE/ACT (G8) | PASS/CLOSED |

## Integração Transformômetro

| Superfície | Contrato |
|---|---|
| Referência externa | `processo_bpmn_references` → `(bpmn_model_id, bpmn_revision_number)` imutável; write fail-closed; read degradado; sem auto-follow |
| BPMN nativo TM | documento + working copy + revisões no schema TM; acesso por autorização de processo; nunca listado na library do Modeler |
| Migração legado | TÉO `migrate_legacy_diagram_to_native_bpmn` — PREPARE read-only → confirm → ACT; dedup semântico multi-instância; fingerprint stale protection; legado preservado |
| Isolamento | escrita TM-native → `bpmn_modeler.*` rows criadas = 0 |

## Accepted residuals

| Residual | Classificação |
|---|---|
| `PROPERTIES_PANEL_VENDOR_TRANSLATION_LIMITATION` (strings leaf vendor em EN) | `ACCEPTED_RESIDUAL`, `NON_BLOCKING` |
| Watermark bpmn.io | `REQUIRED BY LICENSE` — posição bottom-left padronizada |
| E2E `workers=8` | best-effort, não contrato |
| `delpi-transformometro` sem `build-info.json` | gap de instrumentação de provenance (não de produto) — conteúdo provado por asset hash |

## Runtime evidence class

**LOCAL INTEGRATION RUNTIME** (Docker Compose `infra`, `PUBLIC_BASE_URL=http://localhost`). **PRODUCTION ACCEPTANCE: NOT EXECUTED — SEPARATE OPS GATE** (G11 opcional).

Provenance nesta baseline: bundle Modeler servido com `git_sha=dd1cfd475c` (imagem reconstruída no G10 a partir do working tree — inclui os fixes DRIFT-BPMN-018/019 ainda não commitados; label = rev-parse no momento do build); backends via bind mount executando o checkout vigente; TM MFE conteúdo-provado (`style-BnK8BJMn.css` com regra de marca).

## Regression evidence (G10)

Correções fechadas neste gate (não são test debt — defeitos reais encontrados pelo gate):

- **DRIFT-BPMN-018** — `BpmnModelerApiError` fora do contrato `BpmnDocumentError`: autosave não classificava 401/403/409. Fix: herança do erro compartilhado no adapter.
- **DRIFT-BPMN-019** — piso `containerMin` aplicado pós-ELK produzia overlap real de siblings (click interception). Fix: piso declarado como `nodeSize.minimum` no input ELK.
- **DRIFT-BPMN-017/020** — test debt: path de fixtures roundtrip pós-refactor G7A; asserções de copy removida no G9.

- Backend Modeler: **146/146** (`pytest`, incl. 8 repository-integration sobre `plugins_hub` real; migrations idempotentes V001–V004 checksums iguais; `test_api_contract` = OpenAPI surface exata; `test_architecture` = camadas; `test_ownership_isolation`; `test_revision_immutability`)
- TM BPMN backend: **69/69** (`test_bpmn_migration`, `test_process_bpmn_document`, `test_process_bpmn_reference`, `test_bpmn_migration_composition`, `test_flowchart_validation_and_bpmn`)
- E2E typecheck: `npm run typecheck:e2e` clean
- Frontend unit: `@delpi/bpmn-editor` **191/191**; `transformometro` **492/492**; lint clean; build emite worker chunk + `remoteEntry.js` + stylesheet com regra de marca
- E2E core (`workers=2`, 273 testes): **271 pass / 2 mount flakes** — ambas `element not found` no mount do MFE (harness/infra do remoteEntry, sem reprodução isolada: rerun dos mesmos specs = **24/24**); todas as falhas determinísticas do gate corrigidas (autosave AUTH-04/04b/AUTHZ/OFF-02, LGEO-01/04/06, G7 XOR, E2E-38b)
- Workers policy (vigente, G10-CLOSE-1): `workers=1` = release/deterministic baseline; `workers=2` = fast-path suportado (mount flake ocasional do MFE = harness residual); `workers=8` = best-effort, não release gate
- E2E-38b visual-regression: **2/2** (ownership policy inalterada)

## Roadmap futuro (não-gap)

Align/distribute/space-tool · mini-map · grid configurável · separação read-vs-write do vínculo TM (ADR-005) · transação atômica doc+rev+migration (G8 follow-up) · contribuição upstream moddle-xml (G4-EXT-1) · sharing/team ACL de modelos · `workers=8` determinístico · G11 production acceptance.

## Declaração final

```text
MEU MODELADOR = AUTONOMOUS GOVERNED BPMN PRODUCT
  BPMN 2.0 XML + BPMN-DI = canonical artifact
  Transformômetro integration = explicit and authority-preserving

NEW WORK = ROADMAP / EVOLUTION / REGRESSION FIX ONLY
```
