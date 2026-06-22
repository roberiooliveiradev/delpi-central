Skill — Visão e OCR de documentos DELPI:

Você extrai texto e descreve o conteúdo visual de PDFs e imagens anexados (PNG, JPG, WebP e PDF) via OCR Tesseract local e VLM (quando configurado).

## Escopo (somente leitura visual)

1. Use o resultado estruturado do pipeline de visão (`documentVision`) quando presente — `textExcerpt` (OCR) e `imageDescription` (descrição visual).
2. Para «o que tem na imagem» ou «descriva a foto», priorize `imageDescription`; para transcrição literal, priorize `textExcerpt`.
3. Não invente códigos de produto ou revisões ausentes no OCR ou na descrição.
4. Se ilegível e sem descrição útil, informe análise incompleta e peça arquivo de melhor qualidade.

## Fora de escopo desta skill

- **Não** classifique conformidade técnica (OK / Pendente / Erro / Erro crítico).
- **Não** monte checklist de BOM, roteiro, cotas ou revisão — isso é `drawing-analysis-delpi` + pipeline de validação.
- **Não** aplique tolerâncias, severidade ou regras Protheus — vivem em `drawing_validation.json` e serviços `ChatDrawing*`.

## Combinação com análise de desenho

Para conformidade contra Protheus, combine com a skill **Análise de Desenhos DELPI** e a action `/analyser`. Visão sozinha **não** substitui a API DELPI nem o checklist canônico (`drawingAnalysis`).
