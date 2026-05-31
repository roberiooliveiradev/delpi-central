# Especialista em textos (Playbook 03)

## Princípio

**Texto bom = sentido preservado + clareza + tom adequado + zero invenção.**

Tarefa textual pura não aciona API, SQL, RAG ou web (ver também [intent-routing.md](./intent-routing.md)).

## Serviços

| Serviço | Papel |
|---------|--------|
| `ChatTextTaskIntentService` | Detecção e categoria (`correct`, `email`, `minutes`, …) |
| `ChatTextTaskService` | Subtipos Playbook 03, supplement de prompt, `textTask` metadata |
| `ChatTextQualityValidator` | Validação pós-resposta |
| `ChatTextTaskFollowUpService` | Chips `textTaskFollowUpSuggestions` |
| `ChatTextTaskPreferenceService` | Preferências de sessão («só versão final», tom formal, …) |

## Policies

- `administrative-writing.md` — regras gerais
- `text-specialist.md` — templates (e-mail, ata, checklist, comunicado)
- `text-correction.md` / `email-writing.md` — quando aplicável

## Testes

`tests/fixtures/text_specialist_regression_cases.py` (T1–T15), `scripts/run_text_specialist_validation.sh`
