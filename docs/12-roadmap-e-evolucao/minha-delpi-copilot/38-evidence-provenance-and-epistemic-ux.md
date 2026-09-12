# Minha DELPI Copilot — Evidence, Provenance e Epistemic UX

**Status:** thematic spec  
**Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Foundation:** `SourceRef`, `EvidenceRef`, `OutcomeRef` e epistemic classes são compartilhados em C0.

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
FACT
→ observado em fonte autorizada

CALCULATION
→ derivado de fatos por método identificável

HYPOTHESIS
→ explicação possível ainda não confirmada

CONCLUSION
→ inferência sustentada por evidence suficiente

RECOMMENDATION
→ ação sugerida a partir de facts/conclusions/policy
```

Nunca apresentar hipótese como fato.

## 3. EvidenceRef

Usar o primitive compartilhado. Exemplo conceitual:

```json
{
  "evidenceId":"uuid",
  "sourceRef":"source-ref-id",
  "kind":"api_fact",
  "entityRefs":[],
  "observedAt":"ISO-8601",
  "freshness":"current",
  "confidence":1.0,
  "limitations":[]
}
```

Campos finais dependem do C0 contract.

Não criar EvidenceRef diferente para Case, Workflow, Graph ou multimodal.

## 4. Synthesis claim

Uma afirmação de resposta pode referenciar EvidenceRefs e possuir classificação epistemic, confidence/limitations quando metodologicamente válidos.

Isso **não exige um novo durable `ClaimV1`** por padrão. Use DTO/presentation structure do pipeline existente, a menos que C0 prove necessidade de persistência/owner próprio.

Exemplo conceitual de apresentação:

```json
{
  "type":"HYPOTHESIS",
  "statement":"A troca de lote pode estar associada ao aumento de refugo",
  "evidenceRefs":["e1","e2"],
  "confidence":0.68,
  "limitations":["certificado do lote anterior ainda não comparado"]
}
```

Não criar falsa precisão de confidence sem método.

## 5. SourceRef

SourceRef representa origem verificável, como:

- API/result ref;
- domain entity;
- document/attachment;
- knowledge record;
- event;
- calculation inputs.

Evidence refere SourceRef; não repetir metadata de source em formatos incompatíveis.

## 6. Freshness

Semântica conceitual:

```text
current/live
snapshot
cached-valid
stale
unknown
```

Fonte stale/unknown pode ser usada somente com limitação coerente quando o objetivo exigir atualidade.

## 7. Multimodal Evidence

Para documento/desenho/imagem:

- file/source ref;
- page/sheet;
- region;
- observation/extracted text;
- extraction method;
- extractor/model version;
- confidence;
- limitations;
- revision quando relevante.

Finding importante sem localização/provenance é incompleto quando a tool consegue fornecer essa informação.

## 8. Business/API Evidence

Normalized read/write outcome pode gerar evidence/source refs contendo:

- entity/action result;
- timestamps/version;
- filters/query context quando material;
- outcome status;
- freshness.

Não copiar payload sensível inteiro só para provenance.

## 9. Graph Evidence

RelationshipRef possui provenance própria. Traversal pode produzir evidence sobre relações/fatos, mas relação inferida continua rotulada como inferred.

## 10. Evidence Board

Case organiza os mesmos EvidenceRefs:

```text
accepted
contested
missing
superseded
```

Board state não altera source/provenance original.

## 11. Artifacts

Relatório/artefato pode preservar refs/footnotes/source metadata permitidos, sem copiar secrets/PII desnecessários.

## 12. Conflicting evidence

Quando fontes confiáveis divergem:

- não escolher silenciosamente;
- mostrar conflito/recency/authority;
- buscar source owner atual quando possível;
- manter limitation até resolução.

## 13. RBAC

Evidence reference não concede acesso ao source.

Ao abrir/reconsultar source:

```text
EvidenceRef
→ SourceRef
→ current permission check
→ source fetch
```

Revogação precisa ser respeitada.

## 14. Observabilidade

Sem CoT, deve ser possível responder:

- quais sources sustentaram outcome/conclusion?;
- freshness?;
- evidence conflicts?;
- qual extractor/version?;
- hypothesis permaneceu não validada?;
- qual action usou quais evidence refs?.

## 15. Implementation mapping

```text
C0 → Source/Evidence/Outcome contracts + freshness semantics
C2 → multimodal evidence + epistemic synthesis
C3 → API/Graph outcome/evidence normalization
C5 → Case Evidence Board sobre o mesmo model
C6 → Experience/Knowledge promotion com provenance
C7 → Simulation results também separados de facts
```

## 16. Tests

- FACT com source;
- calculation com inputs/method;
- hypothesis label;
- stale source;
- conflicting sources;
- RBAC revoked source;
- multimodal page/region;
- superseded revision;
- artifact refs;
- no invented evidence/source IDs;
- data injection não altera policy.

## 17. Gate

Análise avançada não é madura se não diferencia fato/hipótese ou perde provenance de evidence material.