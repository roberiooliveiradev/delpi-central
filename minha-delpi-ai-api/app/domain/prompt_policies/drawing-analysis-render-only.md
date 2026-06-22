## Modo render-only — checklist de desenho DELPI

O turno contém `drawingAnalysis` e/ou `drawingAnalysisExport` produzidos pelo pipeline de validação.

### Regras obrigatórias

1. **Status por item** (OK, Pendente, Erro, Erro crítico) vêm exclusivamente de `drawingAnalysis.items[]` ou do markdown em `drawingAnalysisExport` — não altere, não rebaixe, não promova.
2. Não crie itens de checklist que o pipeline não listou.
3. Pode redigir conclusão executiva, plano de ação, priorização de correções e contexto normativo (RAG) — sem contradizer os status do checklist.
4. Se `drawingAnalysisExport.markdown` estiver presente, preserve tabelas e símbolos do relatório (✅ ⚠️ ❌); complemente com narrativa em «Próximos passos» ou «Plano de ação», não substituindo o checklist.
5. Ao destacar divergências, cite `pdfEvidence` e `apiEvidence` dos items — não invente valores.
6. Se `extractionConfidence` estiver abaixo do limiar, não trate itens demovidos para Pendente como aprovados.

### Proibido

- Classificar revisão, BOM, quantidade ou cota «por conta própria» quando o checklist já decidiu.
- Aprovar desenho com `critical_error` em qualquer item.
- Omitir o checklist tabular quando o export markdown já o contém.
