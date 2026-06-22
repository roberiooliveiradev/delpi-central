Skill — Análise de Desenhos Técnicos DELPI:

Ative o pipeline PDF × API DELPI quando o usuário pedir análise ou validação de desenho técnico (skill `drawing-analysis-delpi` habilitada).

## Camadas (consuma o tool context)

1. **Visão / OCR** (`document-vision-delpi`): leitura do PDF — não invente códigos ausentes no OCR.
2. **API DELPI** (`get_product_analyser`): cadastro (SB1010), estrutura (SG1010), roteiro (SG2010), inspeções (QP6/QP7/QP8).
3. **Checklist canônico** (`drawingAnalysis`, `drawingAnalysisExport`): gerado pelo pipeline — **fonte única de status** por item.

Ordem de autoridade em divergência: **API DELPI → PDF/OCR → normas (RAG)**.

## Obrigações do assistente

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
