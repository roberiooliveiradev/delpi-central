# Minha DELPI Copilot — Evidence, Provenance e Epistemic UX

**Status:** thematic spec  
**Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Standalone boundary:** [`50-standalone-copilot-application-architecture.md`](./50-standalone-copilot-application-architecture.md)  
**Foundation:** `SourceRef`, `EvidenceRef`, `OutcomeRef` e epistemic classes em C0; runtime base em C3.

## 1. Regra central

Toda análise/conclusão material deve, quando a fonte permitir, apontar para evidência verificável.

```text
source
→ EvidenceRef
→ synthesis classification
→ conclusion/recommendation
```

## 2. Epistemic classes

```text
FACT           → observado em fonte autorizada
CALCULATION    → derivado por método identificável
HYPOTHESIS     → explicação possível não confirmada
CONCLUSION     → inferência sustentada por evidence suficiente
RECOMMENDATION → ação sugerida a partir de facts/conclusions/policy
```

Nunca apresentar hipótese como fato.

## 3. EvidenceRef

Usar primitive compartilhado C0. Campos conceituais incluem evidenceId, sourceRef, kind, entityRefs, observedAt, freshness, confidence quando metodologicamente válida e limitations.

Não criar EvidenceRef diferente para Case, Workflow, Graph, API ou multimodal.

## 4. Synthesis claim

Afirmação de resposta pode referenciar EvidenceRefs e classificação epistemic sem exigir durable `ClaimV1` próprio. Persistir claim somente se C0/C6 provar lifecycle/owner real.

## 5. SourceRef / Freshness

SourceRef representa API/result, domain entity, document, knowledge record, event ou calculation inputs.

Freshness conceitual:

```text
current/live
snapshot
cached-valid
stale
unknown
```

Stale/unknown exige limitação coerente quando atualidade importa.

## 6. Multimodal Evidence — C3

Documento/desenho/imagem pode carregar:

- file/source ref;
- page/sheet/region;
- observation/extracted text;
- method/extractor/model version;
- confidence;
- limitations;
- document revision.

Finding importante sem localização/provenance é incompleto quando a tool pode fornecer isso.

## 7. Business/API Evidence — C4/C5

Normalized read/write outcomes podem produzir source/evidence refs com entity/action result, timestamps/version, filters/query context material e outcome status.

Não copiar payload sensível inteiro apenas para provenance.

## 8. Graph Evidence — C4

RelationshipRef possui provenance própria. Relação inferida permanece explicitamente inferred e não vira FACT automaticamente.

## 9. Evidence Board — C6

Case organiza os mesmos EvidenceRefs:

```text
accepted
contested
missing
superseded
```

Board state não altera source/provenance original.

## 10. Artifacts / conflicting sources / RBAC

Artifacts podem preservar refs/footnotes permitidos sem copiar PII/secrets desnecessários.

Quando fontes confiáveis divergem, mostrar conflito/recency/authority e manter limitation até resolução.

EvidenceRef não concede source access:

```text
EvidenceRef → SourceRef → current permission check → source fetch
```

## 11. Observabilidade

Sem CoT, deve ser possível responder quais sources sustentaram outcome/conclusion, freshness, conflicts, extractor/version, hypotheses não validadas e quais evidence refs suportaram uma ação.

## 12. Phase mapping

```text
C0 → Source/Evidence/Outcome contracts + freshness semantics
C3 → Copilot-owned multimodal Evidence + epistemic synthesis foundation
C4 → Business read/Graph outcome/evidence normalization
C5 → governed-write outcomes/evidence
C6 → Case Evidence Board + Experience/Knowledge promotion
C7 → Simulation outputs separados de facts
```

## 13. Independence

Evidence runtime e storage pertencem à Copilot API. Não usar evidence/session/output models do Minha DELPI Chat como authority.

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

Análise avançada não é madura se não diferencia fato/hipótese, perde provenance ou depende do Chat para recuperar/armazenar Evidence.