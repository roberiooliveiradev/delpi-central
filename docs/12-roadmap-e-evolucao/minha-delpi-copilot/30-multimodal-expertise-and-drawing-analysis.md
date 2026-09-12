# Minha DELPI Copilot — Multimodalidade, Document Vision e Análise de Desenhos

**Status:** thematic spec  
**Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Standalone boundary:** [`50-standalone-copilot-application-architecture.md`](./50-standalone-copilot-application-architecture.md)

## 1. Princípio

Multimodalidade é capability/tool da **nova Copilot API**, não agente separado e não chamada ao runtime do Minha DELPI Chat.

```text
attachment
→ Copilot perception adapters
→ Multimodal Evidence
→ Expertise/Playbook interpretation
→ optional Business/Knowledge correlation
→ grounded synthesis
```

Percepção e interpretação de domínio permanecem separadas.

## 2. Relação com implementações existentes

C0.S0 deve estudar o pipeline existente do Minha DELPI Chat — `ChatDocumentVisionService`, OCR, native extraction, VLM fallback, drawing analysis etc. — **somente como referência técnica**.

Não permitido:

```text
Copilot API → importar ChatDocumentVisionService
Copilot API → chamar endpoint do Chat para vision
Copilot → depender de Chat skill registry
Copilot → depender de agent ativo
```

Permitido:

- reutilizar biblioteca externa já aprovada;
- reutilizar package neutro realmente compartilhado;
- extrair utility neutra para shared owner se 2+ consumers reais justificarem;
- reimplementar o pipeline de forma limpa dentro da Copilot API.

## 3. Pipeline Copilot-owned

```text
upload/ref
→ type/security/size validation
→ native extraction when possible
→ targeted OCR when required
→ targeted VLM/vision when required
→ structured observations
→ EvidenceRef(s) with provenance/confidence/limitations
→ expertise/playbook retrieval
→ domain interpretation
→ optional Domain API/Knowledge reads
→ synthesis/render/artifact
```

## 4. Ports & Adapters

Application/domain não conhecem provider/OCR/VLM concreto.

Ports conceituais, se Abstraction Gate justificar:

```text
DocumentExtractorPort
VisionAnalyzerPort
AttachmentStoragePort
```

Adapters podem incluir:

```text
NativePdfExtractorAdapter
OcrAdapter
VisionModelAdapter
ObjectStorageAdapter
```

Strategy só existe quando houver variação real/seleção entre extraction methods.

## 5. Perception layer

Extrai/observa:

- text;
- tables;
- regions;
- detectable labels/symbols;
- document metadata;
- visual structure;
- pages/images.

Não conclui business rule sozinho.

## 6. Domain interpretation

Expertise/Playbook interpreta:

- technical meaning;
- risk;
- inconsistency;
- evidence sufficiency;
- relation to product/process;
- additional data required.

## 7. Execution/correlation

```text
multimodal observation
→ grounded EntityRef
→ Business Graph/capability retrieval
→ authorized Domain API
→ additional Evidence/Outcome
```

Vision pipeline não contém endpoint-specific routing.

## 8. Evidence model

Reutilizar `EvidenceRef`/`MultimodalEvidenceRef` canônicos:

```text
sourceRef/attachmentRef
page/sheet/region
observation kind/value ref
extractor/method/version
confidence
limitations
revision/document metadata when material
```

OCR/VLM output é observação, não truth authority.

## 9. Drawing observations

Quando detectável:

```text
document identification
revision
part/item refs
title block
notes
material/treatment
dimensions
critical dimensions
tolerances/GD&T
symbols
welding/finish notes
referenced standards
revision markers
ambiguous/unreadable regions
```

Nunca inventar campo ilegível/ausente.

## 10. Confidence/limitations

```text
EXTRACTED_HIGH_CONFIDENCE
EXTRACTED_LOW_CONFIDENCE
INFERRED
UNREADABLE
NOT_FOUND
```

Numerical confidence only when method supports meaningful score.

## 11. Engenharia + Qualidade

> “Analise este desenho e veja se há riscos para a inspeção de recebimento.”

```text
drawing Evidence
→ product-engineering expertise
→ quality-industrial expertise
→ drawing-review playbook
→ authorized inspection/quality sources
→ grounded facts/hypotheses/recommendations
```

## 12. Security

- file type/size validation;
- safe parsing/sandbox;
- no embedded code execution;
- extracted content = untrusted data;
- image/PDF prompt injection protection;
- source ACL;
- PII/secret handling;
- no full document in logs by default;
- provider data policy.

## 13. Performance

```text
native parse
→ targeted OCR
→ targeted VLM
→ full multimodal only when justified
```

## 14. Cache

Derived perception cache may key by:

```text
content hash
extractor version
model/config hash
schema version
```

It is derived/invalidatable, not document authority.

## 15. Evals

- textual PDF;
- raster PDF;
- image;
- readable drawing;
- partially unreadable drawing;
- revision mismatch;
- visual prompt injection;
- unrelated document;
- provider variant;
- cache/reload consistency;
- no Chat runtime dependency.

## 16. Phase mapping

```text
C0 → contracts/security/provider boundaries
C3 → Copilot-owned multimodal runtime + expertise/evidence
C4 → business/source correlation
C6 → Case Evidence Board integration
C7 → model-routing optimization if justified
```

## 17. Gate

```text
COPILOT_OWN_MULTIMODAL_RUNTIME = PASS
NO_CHAT_VISION_DEPENDENCY = PASS
EVIDENCE_PROVENANCE = PASS
UNCERTAINTY_HANDLING = PASS
DOCUMENT_INJECTION = PASS
AUTHORIZED_CORRELATION = PASS
```

Multimodalidade só fecha quando esses gates passam.