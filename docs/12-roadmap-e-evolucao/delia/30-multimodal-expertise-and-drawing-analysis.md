# DÉLIA — Multimodalidade, Document Vision e Análise de Desenhos

**Status:** `TARGET` — thematic spec  
**Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Standalone boundary:** [`50-standalone-copilot-application-architecture.md`](./50-standalone-copilot-application-architecture.md)

## 1. Princípio

Multimodalidade é capability target da DÉLIA, não agente separado e não chamada ao runtime do Minha DELPI Chat.

```text
attachment/source
→ provider-neutral perception adapter
→ Multimodal Evidence
→ Expertise/Playbook interpretation
→ optional Business/Knowledge correlation
→ grounded synthesis
```

Percepção e interpretação de domínio permanecem separadas.

Nenhum extractor, OCR, VLM, storage port ou provider é considerado implementado apenas por aparecer neste documento.

## 2. Relação com implementações existentes

C0.S0 pode estudar pipeline existente do Minha DELPI Chat — vision, OCR, native extraction, drawing analysis etc. — **somente como inventário/reference-only**.

Não permitido:

```text
DÉLIA → importar ChatDocumentVisionService
DÉLIA → chamar endpoint do Chat para vision
DÉLIA → depender de Chat skill registry
DÉLIA → depender de agent ativo
```

Reuse só é válido quando C0 provar componente neutro, owner, contrato, consumers e lifecycle adequados.

## 3. Pipeline target

```text
upload/ref
→ type/security/size validation
→ native extraction when possible
→ targeted OCR when required
→ targeted VLM/vision when required
→ structured observations
→ Evidence refs with provenance/confidence/limitations
→ expertise/playbook retrieval
→ domain interpretation
→ optional authorized Domain API/Knowledge reads
→ synthesis/render/artifact
```

O pipeline final depende de C0 inventory, data policy, provider contracts e Abstraction Gate.

## 4. Ports & Adapters

Domain/Application não conhecem provider/OCR/VLM concreto.

Ports só podem existir quando variação/consumer/test-double/boundary real justificar. Exemplos conceituais, não prescrição:

```text
DocumentExtractorPort?
VisionAnalyzerPort?
AttachmentStoragePort?
```

Strategy só existe quando houver seleção real entre métodos.

## 5. Perception layer

Pode extrair/observar:

- text;
- tables;
- regions;
- detectable labels/symbols;
- document metadata;
- visual structure;
- pages/images.

Não conclui business rule, safety state ou authorization sozinha.

## 6. Domain interpretation

Expertise/Playbook pode interpretar:

- technical meaning;
- risk;
- inconsistency;
- evidence sufficiency;
- relation to product/process;
- additional data required.

Material conclusion continua dependente de Evidence adequada e source/domain authority.

## 7. Execution/correlation

```text
multimodal observation
→ grounded EntityRef/SourceRef
→ authorized relationship/capability retrieval
→ authorized Domain API
→ additional Evidence/Outcome
```

Vision pipeline não contém endpoint-specific routing e nunca concede write authority.

## 8. Evidence model

Reutilizar contratos canônicos de Evidence quando C0 os congelar. Candidate fields:

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

Semântica de confidence precisa vir do método real. Não inventar score numérico quando o extractor/modelo não sustenta significado calibrado.

## 11. Engenharia + Qualidade

Cenário target:

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
- provider data policy;
- media retention and deletion owner explicit.

## 13. Performance

Preferir custo mínimo suficiente:

```text
native parse
→ targeted OCR
→ targeted VLM
→ broader multimodal only when justified
```

## 14. Cache

Derived perception cache, se existir, é invalidável e não authority. Key/version/freshness dependem do contrato real aprovado.

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
- cache/reload consistency quando cache existir;
- no Chat runtime dependency.

AI change exige generalization, safety e task outcome para o SHA/config avaliado.

## 16. Phase mapping

```text
C0 → inventory/contracts/security/provider/media boundaries
C3 → capability foundation only when dependencies are proven
C4 → authorized business/source correlation
C6 → product/Case integration when prioritized
C7 → routing/performance optimization only if evidence justifies
```

## 17. Gate

Sem runtime/evals reais, status permanece `PLANNED/TARGET`, nunca PASS documental.
