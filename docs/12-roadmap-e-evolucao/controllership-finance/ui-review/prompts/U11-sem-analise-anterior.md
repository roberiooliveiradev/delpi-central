# Prompt para o Cursor — UI review, U11 («sem análise anterior» não é zero)

> **Incluída na U12 (15/11/2026).** Não executar sozinha: o conteúdo é o item W1a de [U12-cursor.md](./U12-cursor.md).

```text
PROMPT CURSOR — UI REVIEW · U11 — comparação com período anterior inexistente aparece como zero

CONTEXTO
Revisão do Claude sobre U10 (15/11/2026): ACCEPT_WITH_RESIDUAL. Desempenho aceito (teste de orçamento
de consultas presente; PROD pela CLARA: summary da análise 07–13/11, filiais 01+02, em ≈2 s com o
overhead do conector). Residual achado pela CLARA em PROD:

  read entry_audit.summary (análise 07/11–13/11, 197 notas) → "previous": todos os campos 0.
  Não existe análise do período anterior. A tela mostra «anterior: 0» e a variação parece real.

Causa: application/entry_audit/service.py `_previous_kpis()` devolve um dicionário de zeros quando
`_previous_analysis()` é None. Viola a regra do produto «indisponível ≠ zero».

MISSÃO
1. BFF: sem análise anterior → `"previous": null` em summary (e `daily.previous: []` já é vazio —
   manter). Documentar no contrato (backend §6) que previous é opcional. Teste.
2. MFE: com `previous` null, KPIs sem TrendDelta e sem «anterior: …»; ajuda do KPI diz «Sem análise
   do período anterior para comparar». Teste de render.
3. CLARA: a skill/diretiva já trata ausência; conferir que `analyze entry_audit_findings` não
   compara com zeros (FACT entry_audit.compare só quando há análise anterior). Teste.
4. Conferir a regra de `_previous_analysis()`: mesmo tamanho de período, imediatamente anterior,
   mesmas filiais e tipos; registrar no contrato.
5. HML → PROD (tag rollback-ui-review-u11-controllership-finance-api e -controllership-finance).

REGRAS
As da trilha. git add só com caminhos explícitos. Parar ao concluir e reportar.
```
