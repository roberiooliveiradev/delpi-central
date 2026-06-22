## RAG normativo — análise de desenho DELPI

Trechos documentais (normas técnicas, procedimentos, GPTs de engenharia) **complementam** a resposta — **não substituem** o checklist do pipeline.

### O que o RAG pode fazer

1. Explicar **por que** um requisito existe (ex.: decape, revisão, inspeção QP).
2. Sugerir **como corrigir** no desenho ou no cadastro, alinhado ao item do checklist.
3. Citar norma/procedimento como referência educativa — sem alterar status.

### O que o RAG **não** pode fazer

1. Definir ou alterar status **OK**, **Pendente**, **Erro** ou **Erro crítico** — só `drawingAnalysis.items[]` / `drawingAnalysisExport`.
2. Aprovar desenho quando o checklist tem `critical_error`.
3. Promover item **Pendente** (leitura incerta) para **OK** porque a norma «parece» atendida.
4. Inventar códigos, quantidades, revisões ou cotas ausentes no PDF/OCR ou na API.

### Ordem de autoridade (reforço)

**API DELPI → PDF/OCR → normas (RAG).** Em conflito, prevalece o checklist; use o RAG para contextualizar, não para reclassificar.
