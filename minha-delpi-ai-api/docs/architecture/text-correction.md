# Correção de texto (chat base)

Habilidade nativa do Minha DELPI Chat para revisar ortografia, gramática e clareza **sem** consultar ERP.

## Pipeline

```
Mensagem
  → ChatTextTaskIntentService (categoria correct / rewrite)
  → ChatTextCorrectionIntentService (subtipo, não compete com e-mail)
  → estágio text_task + text_correction (sem tools/RAG)
  → policies administrative-writing.md + text-correction.md
  → LLM
  → ChatTextCorrectionAnswerGuardService
  → metadata textTask + textCorrectionFollowUpSuggestions
```

## Serviços

| Serviço | Papel |
|---------|--------|
| `ChatTextCorrectionIntentService` | Subtipos, extração do texto, códigos a preservar |
| `ChatTextCorrectionPromptSupplementService` | Instruções por modo no prompt |
| `ChatTextCorrectionQualityValidator` | Checklist pós-resposta |
| `ChatTextCorrectionAnswerGuardService` | Trim «só versão final» |
| `ChatTextCorrectionFollowUpService` | Chips do `personality_playbook.json` |
| `ChatTextCorrectionTurnService` | Orquestração no turno (send/stream) |
| `ChatTextCorrectionPreferenceService` | Preferências de sessão (`textCorrection`, `textCorrectionPreferences`) |

## Metadata

- `textTask.type`: `"correction"`
- `textTask.subtype`: ex. `text_correct_basic`
- `textCorrectionFollowUpSuggestions`: chips de refinamento
- `textCorrectionQuality`: falhas do validador (opcional)

## Validação

```bash
cd minha-delpi-ai-api && ./scripts/run_text_correction_validation.sh
```

Playbook: [`../roadmap/melhorias/playbook_correcao_texto_minha_delpi_chat.md`](../roadmap/melhorias/playbook_correcao_texto_minha_delpi_chat.md).
