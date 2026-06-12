# Configuração de plataforma do chat (admin prevalece)

Documentação dos **bundles de runtime** gravados em `ai_admin_runtime_settings`, editáveis no painel admin do plugin **minha-delpi-chat**.

Relacionado: [`chat-intelligence-settings-profiles.md`](chat-intelligence-settings-profiles.md), [`../architecture/chat-intelligence-base.md`](../architecture/chat-intelligence-base.md).

---

## Princípio

| Camada | Papel |
|--------|--------|
| **Docker / `.env`** | Defaults iniciais apenas — **não** sobrescreve admin a cada boot |
| **Admin (UI)** | Fonte de verdade em runtime após primeiro save |
| **Seed no boot** | `flask seed-chat-platform-settings` — grava **só se a chave do bundle estiver vazia** |

```
.env → build_defaults_payload() → seed (1× se DB vazio)
Admin PUT → ai_admin_runtime_settings → resolve() / read_*_settings() → pipeline
```

---

## Bundles e rotas admin

| Chave no DB | Painel admin | GET/PUT |
|-------------|--------------|---------|
| `chat_intelligence_settings` | Plataforma → Inteligência | `/admin/chat/intelligence-settings` |
| `chat_response_mode_settings` | Plataforma → Modos de resposta | `/admin/chat/response-mode-settings` |
| `chat_vision_settings` | Plataforma → Visão e anexos | `/admin/chat/vision-settings` |
| `chat_learning_pipeline_settings` | Conhecimento → Aprendizagem → Pipeline | `/admin/chat/learning-pipeline-settings` |

Código canônico:

- Specs: `app/infrastructure/config/chat_admin_settings_bundles.py`
- Serviço: `app/application/services/chat_admin_settings_bundle_service.py`
- Leitura runtime: `app/infrastructure/config/chat_admin_settings_runtime_reader.py`
- Acesso pipeline: `app/application/services/chat_platform_runtime_access.py`

---

## O que permanece só no Docker

Não migrado para admin (infra, segredos, modelos):

- URLs de APIs, Postgres, Redis, Ollama/vLLM
- API keys e credenciais
- `CHAT_DOCUMENT_VISION_BACKEND`, `CHAT_DOCUMENT_VISION_OLLAMA_*`, DPI, timeouts
- Fine-tuning webhook, modelos base e `OLLAMA_CREATE`
- Limites fixos de vocabulário (`CHAT_LEARNING_VOCABULARY_MAX_RULES`, `CHAT_LEARNING_GLOSSARY_MAX_TERMS`, etc.)

---

## Campos por bundle (resumo)

### Modos de resposta

- `responseModesEnabled` — seletor Texto / Painel / Automático na sessão

### Visão e anexos

- `documentVisionEnabled`, `documentVisionAutoWithDrawing`, `documentVisionAutoVlmFallback`
- `attachmentImageOcrEnabled`, `documentVisionStampCropEnabled`, `documentVisionImageDescribeEnabled`
- `documentVisionMaxPages`, `documentVisionMaxChars`

### Pipeline de aprendizagem

- `learningEnabled` (master)
- `typingCorrectionEnabled`, `typingCorrectionFuzzyEnabled`
- `learningApplyVocabulary`, `learningCaptureFromFeedback`, `learningCaptureFromTurn`
- `learningAutoApproveEnabled`, `learningAutoApproveMinConfidence`
- `learningGlossaryRetrieval`, `learningGlossaryCapture`, `learningTermConfirmationEnabled`
- `learningGlossaryWebMeaning`, `learningGlossaryRagIndex`
- `learningEvaluationEnabled`, `learningEvaluationBlockPromotion`, `learningEvaluationCaptureFromFeedback`
- `learningFineTuningEnabled`, `learningFineTuningCapturePositiveFeedback`

---

## Operação

```bash
# Seed manual (idempotente — não sobrescreve admin)
docker compose -f infra/docker-compose.dev.yml exec minha-delpi-ai-api \
  flask --app app.main:app seed-chat-platform-settings
```

No boot do container, `docker-entrypoint.sh` chama o mesmo comando quando `RUN_MIGRATIONS=true`.

---

## Smoke rápido

1. Abrir **Plataforma → Modos de resposta** e alternar `responseModesEnabled`; salvar — recarregar deve mostrar origem **admin**.
2. Enviar mensagem com typo com **Correção de digitação** ligada/desligada em **Aprendizagem → Pipeline**.
3. Anexar PDF com **Visão** ligada — verificar extração sem alterar `CHAT_DOCUMENT_VISION_ENABLED` no `.env` após save na admin.
