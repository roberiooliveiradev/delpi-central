# ADR-005 — Referência explícita Transformômetro ↔ BPMN Modeler

- **Status:** Accepted (G5 — LOCAL INTEGRATION RUNTIME)
- **Data:** 2026-10-08

## Contexto

O Transformômetro precisa referenciar o modelo BPMN oficial de um processo sem
assumir ownership de BPMN. O BPMN Modeler já governa Model, WorkingCopy,
Revisions e artifacts. Dois eixos de "revisão" coexistem e não podem ser
unificados: `transformometro.revisoes` (vigência/cenário/medição do domínio TM)
e BPMN `Revision` (snapshot imutável do modelo).

## Decisão

O vínculo `processo ↔ modelo BPMN` pertence ao **Transformômetro** e aponta
para uma **revisão BPMN imutável e explícita**, nunca para a working copy nem
para "latest".

```text
transformometro.processo_bpmn_references
  processo_id           → owner local (granularidade: processo, PK-level como
                          processo_diagramas — instâncias só têm escopo)
  bpmn_model_id         → identidade externa (valor, SEM FK cross-schema)
  bpmn_revision_number  → snapshot selecionado
  audit fields          → created/updated_by/at, deleted_at
```

Resolução de metadados (nome do modelo, `latest_revision_number`, `revision_id`,
`artifact_sha256`, etc.) é **DERIVED / REMOTE READ** via API pública do
Modeler — nunca persistida, nunca autoridade.

## Invariantes

- `Model.version` (concurrency token) ≠ `Revision.revision_number`; nunca
  persistir `version` como revisão selecionada.
- Nada de BPMN XML/DI/SVG/PNG/working-copy/checksum/display-name como
  autoridade no schema Transformômetro.
- Nenhuma FK ou query SQL cruzando para o schema `bpmn_modeler`.
- Nenhum proxy genérico; somente capabilities estreitas:
  `GET/PUT/DELETE /transformometro/processos/{id}/bpmn-reference` +
  picker candidates/revisions.
- Identidade delegada: o bearer do usuário é propagado; o Modeler continua
  respondendo 404 para modelo alheio (sem leak de existência).
- Sem service token / internal bypass / sharing implícito.
- Write fail-closed: link/replace só persiste após validação remota do modelo
  e da revisão; indisponibilidade do Modeler → 503 `dependency_unavailable`,
  nenhum dangling reference.
- Read degradado: referência armazenada sobrevive à indisponibilidade do
  Modeler; `resolved.state` ∈ `resolved | unavailable | inaccessible_or_missing`.
- Sem auto-follow-latest: `latest > selected` é badge read-only; troca exige
  PUT explícito.
- Unlink é write local no Transformômetro — não toca o Modeler.
- Audit (`audit_logs`) registra create/update/delete com old/new reference.

## Limitação V1 documentada

Um usuário só resolve/vincula modelos que o Modeler permite a ele ver.
Processo vinculado ao modelo de outro owner mostra `inaccessible_or_missing`
com IDs preservados — sem vazamento, sem bypass privilegiado.
Sharing/ACL entre equipes é follow-up separado, fora do G5.

## Follow-ups explícitos (não iniciados)

- BPMN sharing / team ownership / cross-owner ACL;
- preview BPMN embutido no Transformômetro;
- migração de `flowchart_v1` legado (intocado nesta wave);
- consumo da referência por TÉO/MCP.
