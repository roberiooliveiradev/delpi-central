Skill — Análise de Desenhos Técnicos DELPI:

Ative o pipeline PDF × API DELPI quando o usuário pedir análise ou validação de desenho técnico (skill `drawing-analysis-delpi` habilitada).

## Camadas (consuma o tool context)

1. **Visão / OCR** (`document-vision-delpi`): leitura do PDF — não invente códigos ausentes no OCR.
2. **API DELPI** (`get_product_analyser`): cadastro (SB1010), estrutura (SG1010), roteiro (SG2010), inspeções (QP6/QP7/QP8).
3. **Checklist canônico** (`drawingAnalysis`, `drawingAnalysisExport`): gerado pelo pipeline — **fonte única de status** por item.

Ordem de autoridade em divergência: **API DELPI → PDF/OCR → normas (RAG)**.

## Falsos positivos / negativos conhecidos (não reclassifique)

O pipeline já trata estes padrões — **não** eleve Pendente a OK nem converta Erro em «provavelmente certo»:

| Padrão | Comportamento esperado |
|--------|------------------------|
| **N VIAS** na descrição (ex.: «4 VIAS») | QTD extraída igual a N → **Pendente** (`quantity_from_description`), não crítico |
| **Refinamento OCR de coluna** (`refined_column`) | Confia na célula só após cruzar ruído de descrição e SG1010 — sem descrição no PDF usa cadastro |
| **Intermediário 50xx** fantasma em `full_text` | Ignorado quando BOM estruturada já lista CB/CT — não reportar `intermediate_extra` |
| **Revisão sem carimbo legível** | Não bloqueia por revisão Delpi — B1_REVATU não vem do PDF |
| **REF. do cliente no PDF ≠ B1_REFEREN** | **Erro crítico** (`customer_reference_mismatch`) quando ambos existem e divergem; pendente se só um lado tiver valor |
| **QTD 0 / coluna vazia** | **Pendente** ou ignorado na comparação — não crítico automático |

Se `drawingAnalysis` marcar **Pendente**, diga que a leitura foi incerta e sugira reextração ou conferência manual — **não** trate como aprovado.

## Severidade e checklist

1. Não invente dados ausentes no PDF nem no cadastro.
2. Quando `drawingAnalysisExport.markdown` existir, use-o como base do relatório — **não reclassifique** itens do checklist.
3. Respeite Pendente do pipeline quando a leitura for incerta; não converta em OK por inferência.
4. Se o produto não existir na API, prevalece o erro crítico do pipeline.
5. Normas (RAG) explicam requisitos; **status** (OK / Pendente / Erro) vêm só do checklist.
6. Sugira ação corretiva para erros; não use «provavelmente», «parece», «talvez».

## PDF anexado

- O PDF já está na conversa quando o usuário pediu análise — não solicite print, zoom ou novo arquivo só para ler BOM, QTD ou cotas.
- Chip «Reextrair BOM do PDF» = nova extração com o **mesmo** anexo.

## Sem PDF

- Informe que é necessário anexar o PDF ou informar código DELPI para busca na biblioteca.
- Com código apenas, pode pré-validar cadastro, roteiro e inspeção na API.

Regras técnicas de validação (tolerâncias, severidade, padrões OCR) vivem no pipeline (`ChatDrawingValidationOrchestrationService`, `drawing_validation.json`) — **não duplique nesta skill**.

Conversão de unidades Protheus (MI, `B1_CONV`, SG1010): pipeline `ChatDrawingProductUnitConversionService` decide; consulte limitações em `docs/architecture/chat-drawing-skill-limitations.md`.
