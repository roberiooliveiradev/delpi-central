# Minha DELPI Copilot — Multimodalidade, Document Vision e Análise de Desenhos

**Status:** thematic spec  
**Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Foundation:** multimodal perception produz `EvidenceRef`/`MultimodalEvidenceRef` compartilhado em C0; runtime de integração em C2.

## 1. Princípio

Multimodalidade é capability/tool do mesmo Copilot, não agente separado.

```text
attachment
→ extraction/perception
→ Multimodal Evidence
→ expertise/playbook interpretation
→ optional business/knowledge correlation
→ grounded synthesis
```

Percepção e interpretação de domínio são responsabilidades separadas.

## 2. Runtime existente a reaproveitar

C0.S0 deve revalidar e preservar quando vigente:

- `ChatDocumentVisionService`;
- `chat_document_vision/*`;
- native extraction;
- OCR;
- VLM fallback;
- drawing merge;
- `drawing-analysis-delpi`;
- `document-vision-delpi`;
- `technical-description-delpi`.

Objetivo de migração: remover dependência de agent ativo quando não houver requisito real de segurança/capability.

## 3. Pipeline

```text
upload/ref
→ type/security/size validation
→ native extraction quando possível
→ targeted OCR quando necessário
→ targeted VLM/vision quando necessário
→ structured observations
→ EvidenceRef(s) com provenance/confidence/limitations
→ expertise/playbook retrieval
→ domain interpretation
→ optional API/Knowledge reads
→ synthesis/render/artifact
```

## 4. Layers

### Perception

Extrai/observa:

- texto;
- tables;
- regions;
- labels/symbols detectáveis;
- metadata;
- visual structure;
- pages/images.

Não conclui business rule sozinho.

### Domain interpretation

Usa expertise/playbook para interpretar:

- significado técnico;
- risco;
- inconsistência;
- evidence sufficiency;
- relation com produto/processo;
- necessidade de dados adicionais.

### Execution/correlation

EntityRef extraído/grounded pode acionar Business/Knowledge capabilities autorizadas.

## 5. Evidence model

Não criar um evidence schema exclusivo de vision.

Usar foundation compartilhada com extensões multimodais como:

```text
sourceRef/attachmentRef
page/sheet/region
observation kind/value ref
extractor/method/version
confidence
limitations
revision/document metadata quando material
```

OCR/VLM output é observação, não verdade absoluta.

## 6. Drawing observations

Quando tecnicamente viável:

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

Ausência de campo não deve ser inventada.

## 7. Confidence/limitations

Estados conceituais úteis:

```text
EXTRACTED_HIGH_CONFIDENCE
EXTRACTED_LOW_CONFIDENCE
INFERRED
UNREADABLE
NOT_FOUND
```

Confidence numérica só quando o extractor/method suporta significado real.

## 8. Engenharia + Qualidade

Exemplo:

> “Analise este desenho e veja se há riscos para a inspeção de recebimento.”

```text
drawing evidence
→ product-engineering expertise
→ quality-industrial expertise
→ drawing-review playbook
→ authorized quality/inspection knowledge/actions
→ facts/hypotheses/recommendations grounded
```

## 9. Entity correlation

```text
vision observation
→ grounded EntityRef
→ Business Graph/capability retrieval
→ source APIs
→ Evidence/Outcome
```

Vision pipeline não recebe endpoints específicos para buscar produto/fornecedor/inspeção.

## 10. Security

- file type/size validation;
- safe parsing/sandbox;
- no embedded code execution;
- extracted text is untrusted data;
- image/PDF prompt injection protection;
- document ACL;
- PII/secret handling;
- no full document in logs by default;
- model/provider data policy.

## 11. Performance

Preferir custo incremental:

```text
native parse
→ targeted OCR
→ targeted VLM
→ full multimodal only if justified
```

Não rasterizar tudo por padrão.

## 12. Cache

Cache de percepção pode usar:

```text
attachment/content hash
extractor version
model/config hash
schema version
```

Mudança material invalida evidence/eval afetada.

## 13. Evals

- textual PDF;
- raster PDF;
- image;
- readable drawing;
- partially unreadable drawing;
- revision mismatch;
- visual prompt injection;
- unrelated document;
- model/provider variant;
- cache/reload consistency;
- session without agent.

## 14. Implementation mapping

```text
C0 → evidence contract + runtime inventory/security semantics
C2 → multimodal adapter producing shared Evidence + expertise integration
C3 → optional business/source correlation through generic reads/Graph
C5 → Case Evidence Board reuses same refs
```

## 15. Gate

Multimodal feature só é madura se:

- observations são rastreáveis;
- unreadable/uncertain content é explicitado;
- document injection não altera policy;
- source correlation usa authorized capabilities;
- evidence model não é paralelo;
- no-agent usage funciona quando autorizado.
