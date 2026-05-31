# Playbook 03 — Especialista em Textos

**Status (30/05/2026):** Implementado (Fases 1–3; 4–6 parciais)  
**Código:** `ChatTextTaskService`, `ChatTextQualityValidator`, `text-specialist.md`  
**Validação:** `scripts/run_text_specialist_validation.sh`

## Núcleo

| Componente | Função |
|------------|--------|
| `ChatTextTaskIntentService` | Detecção `text_task` pura vs mista |
| `ChatTextTaskService` | Classificação, prompt supplement, metadata `textTask` |
| `ChatTextQualityValidator` | Checklist de qualidade pós-resposta |
| `ChatTextTaskFollowUpService` | Chips `textTaskFollowUpSuggestions` |
| Policies | `administrative-writing.md`, `text-specialist.md`, `text-correction.md`, `email-writing.md` |

## Regra central

Tarefa textual explícita → **sem** API/SQL/RAG/web no mesmo turno (roteamento Playbook 02 + estágio `text_task`).

## Subtipos (exemplos)

`text_correct`, `text_rewrite`, `text_email_create`, `text_minutes`, `text_checklist`, `text_summarize`, `text_translate`, `text_announcement`, `text_compare`, …

## Metadata

```json
{
  "textTask": { "type": "correction", "subtype": "text_correct", "tone": "formal" },
  "textTaskFollowUpSuggestions": [{ "label": "Deixar mais formal", "query": "..." }],
  "textTaskMetrics": { "subtype": "text_correct" }
}
```

## Regressão T1–T15

Ver `tests/fixtures/text_specialist_regression_cases.py`.

## Roadmap restante

- Orquestração automática de mixed turn (dados reais + e-mail)
- Dashboard admin de uso textual
- Versionamento de alterações na lousa
