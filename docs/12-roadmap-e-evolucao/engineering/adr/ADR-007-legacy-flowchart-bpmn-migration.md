# ADR-007 — Migração governada de `flowchart_v1` legado → BPMN nativo do Transformômetro (G8)

- **Status:** Accepted (G8 — LOCAL INTEGRATION RUNTIME)
- **Data:** 2026-10-09
- **Estende:** ADR-006 (BPMN nativo TM + editor compartilhado), ADR-005
  (referência externa G5 / XOR dual-mode).

## Contexto

O mapeamento vigente dos processos do Transformômetro vive em `flowchart_v1`
(`transformometro.processo_diagramas` + `instancia_diagrama_escopo` +
`revisao_diagrama_overlays`). Com o BPMN nativo TM do G7, o legado precisa de
um caminho de saída **sem overwrite, sem delete e sem equivalência silenciosa**
— e sem apresentar duas autoridades "vigentes" na UI.

## Decisão

```text
LEGACY → READ → MAP → REPORT → PREVIEW → CONFIRM → CREATE NEW BPMN

Nunca: LEGACY → OVERWRITE
Nunca: AI GUESS → CANONICAL WRITE
Nunca: MIGRATION → DELETE HISTORY
```

- **Source de migração:** `DiagramaCompositionService.compose_for_processo`
  — macro `flowchart_v1` + overlays das revisões vigentes em ordem
  cronológica (a "visão composta" já derivada server-side). Cliente nunca
  fornece o diagrama-fonte; sem overlay vigente, source = macro base
  (reportado em `source_summary.applied_revisoes`).
- **Mapper puro:** `tm_app/domain/diagram/legacy_bpmn_migration.py` — sem
  DB/HTTP/TÉO/frontend. Entrada = flowchart_v1 composto normalizado; saída =
  `MigrationCandidate` (BPMN 2.0 XML + BPMN-DI, ID map estável, relatório
  por objeto, perdas, ambiguidades, warnings, estatísticas, SHA-256, status
  `READY | AMBIGUOUS | BLOCKED`).
- **Classificação por objeto:** `EXACT | HEURISTIC | AMBIGUOUS |
  UNMAPPABLE | IGNORED_METADATA`. O catálogo `bpmn_node_catalog.py` torna a
  maioria dos nós EXACT por construção (tipo legado já carrega `bpmn_tag` +
  event definition). Metadata legada (highlight, meta) vira
  `IGNORED_METADATA` — nunca entra no XML canônico nem em vendor extensions.
- **Ambiguidades:** decisões multi-saída sem condição, `kind=message_flow`
  sem participants, `boundary_*` sem `attachedToRef` → `AMBIGUOUS` com
  `ambiguity_id`, opções explícitas e opção recomendada; resolução é externa
  (`resolutions` no PREPARE seguinte) — o mapper nunca adivinha semântica.
- **Capability TÉO:** `migrate_legacy_diagram_to_native_bpmn` via
  `governed-operations/prepare` + `commit_proposal` (choke point único).
  PREPARE = read-only, sela XML + checksum + `legacy_source_fingerprint` +
  relatório; `execution_policy = confirm_before_act`. ACT revalida AuthZ,
  fingerprint (stale → `proposal_stale`), XOR dual-mode e checksum; cria
  documento nativo + revisão 1 `origin='migration'` + linha em
  `transformometro.processo_bpmn_migrations` (V054); read-back autoritativo;
  compensação fail-closed (soft-delete do documento novo) se persistência
  falhar — legado nunca é mutado.
- **Bloqueios PREPARE/ACT:** `NATIVE_BPMN_ALREADY_EXISTS`,
  `dual_mode_forbidden` (referência G5 ativa), `LEGACY_DIAGRAM_EMPTY`,
  candidato `BLOCKED`/`AMBIGUOUS` não resolvido, BPMN inválido
  (`shared/bpmn_validation` — intake safety + XML + XSD + estrutura +
  semântica + BPMN-DI + product rules).
- **Atomicidade:** commits sequenciais + compensação documentada (a
  assinatura do repo G7 é auto-commit por statement; transação única é
  follow-up registrado).
- **UI:** card "Modelo BPMN" exibe CTA "Migrar legado para BPMN nativo" só
  quando `legacy && !native && !external`; wizard read-only (não reutiliza o
  editor — preview é somente leitura, nunca autosave); após sucesso o BPMN
  nativo é a seção vigente e o legado passa a seção colapsada
  "Mapeamento legado" — nunca rotulado "visão vigente".
- **READ surface:** `record_read(entity=process_bpmn_document, id=processo)`
  retorna doc + revisions + `migration` (metadados da última migração).
- **`import_diagram_bpmn_xml`:** NÃO reutilizado — continua escrevendo só no
  legado macro (contrato antigo preservado); a capability nova é a única
  via TÉO para criar BPMN nativo a partir do legado.

## Invariantes

- `flowchart_v1` mutado pela migração: 0. Deletes de histórico: 0.
- Resolução silenciosa de ambiguidade: 0. Writes em `bpmn_modeler.*`: 0.
- Chamadas de escrita à `bpmn-modeler-api` durante commit: 0.
- Duas autoridades "vigentes" na UI pós-migração: 0.
- Writes de BPMN nativo fora de `commit_proposal`: 0 (preview/preview-edit
  nunca tocam tabelas canônicas).

## Evidência runtime (LOCAL INTEGRATION RUNTIME, 2026-10-09)

PREPARE real (PROC-0034, legado composto 8→4 nós + 1 overlay):
`READY`, 9×EXACT + 6×IGNORED_METADATA, `confirm_before_act`,
candidate sha256 selado. COMMIT via `commit_proposal`: documento
`03b4c6e9…` v1 + revisão 1 `origin='migration'` + linha
`processo_bpmn_migrations` (fingerprint + checksum + ator) + read-back
verificado. Negativos provados em runtime: `NATIVE_BPMN_ALREADY_EXISTS`,
`LEGACY_DIAGRAM_EMPTY`, `dual_mode_forbidden` (ref G5 ativa),
`proposal_stale` (legado mutado pós-PREPARE; fingerprints divergentes no
response). `bpmn_modeler.models/revisions`: 0 rows criadas.
`record_read(process_bpmn_document)` expõe `revisions[].origin=migration` +
`migration{}`.

## Residuals aceitos

- View vs manage por processo compartilham `transformometro.access`
  (gate vigente de todo o Transformômetro — não é regressão do G8;
  separação dedicada é follow-up já registrado em ADR-005/006).
- `migration` de documentos criados fora da migração é `null`.
- Transação única doc+rev+migration: compensação atual é fail-closed;
  transação atômica real é follow-up.

## Follow-ups explícitos (não iniciados)

- Merge/re-migração de processo que já possui BPMN nativo.
- Resolução de ambiguidade assistida com UI dedicada por `ambiguity_id`.
- Transação atômica única para doc+revision+migration.
