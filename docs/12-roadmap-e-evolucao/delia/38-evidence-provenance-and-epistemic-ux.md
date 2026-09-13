# DÉLIA — Evidence, Provenance e Epistemic UX

**Status:** `TARGET` — thematic spec  
**Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Standalone boundary:** [`50-standalone-copilot-application-architecture.md`](./50-standalone-copilot-application-architecture.md)  
**Evidence rule:** `SourceRef`, `EvidenceRef`, `OutcomeRef`, storage e runtime só são implementados quando C0/C3 provar owner, contract, consumers e lifecycle.

## 1. Regra central

Toda análise/conclusão material deve, quando a fonte permitir, apontar para evidência verificável.

```text
source
→ Evidence
→ epistemic classification
→ conclusion/recommendation
```

## 2. Epistemic classes

```text
FACT           → observado em fonte autorizada
CALCULATION    → derivado por método identificável
HYPOTHESIS     → explicação possível não confirmada
CONCLUSION     → inferência sustentada por evidence suficiente
RECOMMENDATION → ação sugerida, nunca autorização
```

Prediction/simulation permanecem classes próprias quando aplicáveis e não viram FACT.

## 3. Evidence contract

Se C0 congelar um `EvidenceRef` compartilhado, reutilizá-lo. Candidate fields podem incluir evidenceId, sourceRef, kind, entityRefs, observedAt, freshness, confidence quando metodologicamente válida e limitations.

Não criar EvidenceRef diferente por Case, Workflow, Graph, API, multimodal ou provider.

## 4. Synthesis claim

Afirmação pode referenciar Evidence refs e classificação epistemic sem exigir durable `ClaimV1` próprio. Persistir claim somente se owner/lifecycle/consumer real justificar.

## 5. Source / Freshness

SourceRef representa origem identificável, não authority inventada. Freshness precisa refletir o contrato real da fonte.

Candidate semantics:

```text
current/live
snapshot
cached-valid
stale
unknown
```

Stale/unknown exige limitation quando atualidade importa.

## 6. Multimodal Evidence

Documento/desenho/imagem pode carregar source/file ref, page/sheet/region, observation, method/version, confidence, limitations e revision quando material. Output de OCR/VLM é observação não confiável até contextualização/validação apropriada.

## 7. Business/API Evidence

Reads/writes podem produzir refs normalizadas para source/result/outcome sem copiar payload sensível inteiro. Domain API continua authority dos dados/regras; technical execution result não é business outcome.

## 8. Graph Evidence

Relationship provenance permanece separada. Relação inferida continua `inferred` e não vira FACT automaticamente.

## 9. Evidence Board

Case pode organizar refs como:

```text
accepted
contested
missing
superseded
```

Board state não altera source/provenance original.

## 10. Artifacts / conflicting sources / RBAC

Artifacts podem preservar refs/footnotes permitidos sem copiar PII/secrets desnecessários.

Quando fontes divergem, mostrar conflict/recency/authority/limitations.

Evidence nunca concede source access:

```text
Evidence ref
→ Source ref
→ current permission check
→ source fetch
```

## 11. Observabilidade

Sem CoT, deve ser possível responder quais sources sustentaram outcome/conclusion, freshness, conflicts, versions, hypotheses não validadas e Evidence refs relevantes.

## 12. Phase mapping

```text
C0 → owner/source/consumer/contracts/freshness semantics
C3 → minimal Evidence/epistemic foundation when unlocked
C4 → business-read/Graph normalization
C5 → governed-ACT outcome/evidence correlation
C6 → Case/Evidence Board + governed knowledge promotion
C7 → advanced scale/optimization only; simulation is not restricted to C7 by this document
```

## 13. Ownership

DÉLIA é owner da coordenação/intelligence Evidence que C0 atribuir a ela. A fonte autoritativa continua com Domain API/provider/document owner/etc. Storage físico não é assumido por este documento.

## 14. Tests

- FACT com source;
- calculation com inputs/method;
- hypothesis label;
- stale/conflicting source;
- RBAC revoked source;
- multimodal page/region;
- superseded revision;
- artifact refs;
- no invented evidence/source IDs;
- data injection não altera policy;
- Chat-offline independence.

## 15. Gate

Sem prova no SHA/config avaliado, o status é `PENDING/INCONCLUSIVE`, nunca PASS documental.
