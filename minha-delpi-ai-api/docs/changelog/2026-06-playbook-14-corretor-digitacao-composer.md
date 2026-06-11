# Changelog — Playbook 14: corretor de digitação no composer (jun/2026)

## Contexto

O chat **já tolerava** typos operacionais na API via `ChatMessageNormalizationService` (matching silencioso), mas o usuário **não via** a correção antes do envio. O Playbook 14 fecha essa lacuna com sugestões **determinísticas**, **confirmadas pelo usuário**, reutilizando o vocabulário existente e a aprendizagem contínua.

**Distinto de:** habilidade «corrija este texto» (LLM, parágrafos inteiros) — ver [playbook_correcao_texto](../roadmap/melhorias/playbook_correcao_texto_minha_delpi_chat.md).

Relacionado: [playbook-14](../roadmap/playbook-14-corretor-digitacao-chat.md), [chat-intelligence-base § typos](../architecture/chat-intelligence-base.md), [smoke U2b](../testing/smoke-operacional-manual.md).

---

## Fluxo (API + MFE)

```text
Composer (draft)
  → debounce 500 ms
  → POST /chat/typing-suggestions { text }
       · ChatLearnedNormalizationService.ensure_loaded()
       · ChatTypingCorrectionService.suggest(text)
  → chip «Você quis dizer…» (textos message_composer.json)
       · Enviar corrigido → POST .../messages/stream + typingCorrection metadata
       · Manter original → dismiss (sessão); telemetria help-events
  → matching interno continua normalize_for_matching (idempotente se aceito)
```

Princípios: **sugerir, não impor**; spans protegidos (códigos `\d{5+}`, `@menções`, backticks, SQL); máx. **3** substituições; desligado após `corrija:`.

---

## API

| Item | Detalhe |
|------|---------|
| Serviço | `app/domain/services/chat_typing_correction_service.py` — `suggest()` |
| Fonte de regras | `ChatMessageNormalizationService.iter_typo_patterns()` (estáticas + aprendidas) |
| Endpoint | `POST /chat/typing-suggestions` — `chat.access` |
| Flag | `CHAT_TYPING_CORRECTION_ENABLED` (default `true`) |
| Capabilities | `GET /chat/capabilities` → `typingCorrectionEnabled` |
| Metadata turno | `typingCorrection` na mensagem user quando aceita (`SendChatMessageRequest`) |
| Telemetria | `POST /chat/assistant/help-events`: `typing_correction_offered` \| `accepted` \| `dismissed` |
| Métricas admin (P14-4) | Audit `chat.typing_correction.event`; `typingCorrectionMetrics` em turnos; `GET /admin/metrics/typing-correction/summary`; painel `AdminTypingCorrectionMetrics` |

### Contrato `POST /chat/typing-suggestions`

**Request:**

```json
{ "text": "estouque do produto 90262404", "locale": "pt-BR" }
```

**Response:**

```json
{
  "hasSuggestions": true,
  "original": "estouque do produto 90262404",
  "corrected": "estoque do produto 90262404",
  "changes": [
    { "offset": 0, "length": 8, "from": "estouque", "to": "estoque", "kind": "typo_rule" }
  ],
  "protectedSpans": [{ "start": 19, "end": 27, "reason": "product_code" }]
}
```

### Metadata no envio (aceite)

```json
{
  "message": "estoque do produto 90262404",
  "typingCorrection": {
    "original": "estouque do produto 90262404",
    "corrected": "estoque do produto 90262404",
    "accepted": true,
    "source": "domain_dictionary",
    "changes": [{ "from": "estouque", "to": "estoque", "kind": "typo_rule" }]
  }
}
```

---

## MFE (`plugins/minha-delpi-chat`)

| Arquivo | Papel |
|---------|--------|
| `src/state/hooks/useChatTypingCorrection.ts` | Debounce + estado da sugestão |
| `src/state/chatTypingCorrection.ts` | Dismiss por sessão, metadata, fetch API |
| `src/ui/components/ChatInput.tsx` | Chip + atalhos Tab (aceitar) / Esc (dispensar) |
| `src/ui/pages/ChatPage.tsx` | Wiring + envio com metadata |
| `src/ui/typingCorrectionTelemetry.ts` | help-events best-effort |
| `src/content/message_composer.json` | Rótulos PT (espelho da API) |
| `src/content/messageComposerContent.ts` | Loader local |

Sync de textos após editar JSON na API:

```bash
cd plugins/minha-delpi-chat
npm run sync:message-composer-content
```

---

## Conteúdo PT-BR

Bundle `app/content/pt-BR/assistant/message_composer.json`:

| Chave | Uso |
|-------|-----|
| `typingCorrection.hint` | «Você quis dizer:» |
| `typingCorrection.acceptLabel` | «Enviar corrigido» |
| `typingCorrection.dismissLabel` | «Manter original» |
| `typingCorrection.previewPrefix` | «Enviar:» |

Catálogo: [assistant-content-catalog.md](../architecture/assistant-content-catalog.md).

---

## Testes

| Suíte | Arquivo |
|-------|---------|
| API T1–T7 | `tests/fixtures/chat_typing_correction_cases.py` + `tests/unit/domain/services/test_chat_typing_correction_service.py` |
| Telemetria | `tests/unit/application/services/test_chat_help_self_help_telemetry.py` |
| MFE | `plugins/minha-delpi-chat/src/state/chatTypingCorrection.test.ts` |

Homologação manual: **U2b** e smoke operacional #2 em [smoke-operacional-manual.md](../testing/smoke-operacional-manual.md).

---

## Commits

| Hash | Descrição |
|------|-----------|
| `7d80d908` | Implementação P14-1 a P14-3 (serviço, endpoint, chip MFE) |
| `d302b8fb` | Telemetria, fixtures T1–T7, smoke U2b, sync script |

---

## Backlog

| Fase | Escopo |
|------|--------|
| P14-4 | ~~Dashboard admin de métricas~~ **Concluído** — `GET /admin/metrics/typing-correction/summary`, audit `chat.typing_correction.event`, `typingCorrectionMetrics` em turnos |
| P14-5 | Fuzzy léxico operacional (SymSpell) |

---

## P14-0 — Catálogo JSON (jun/2026)

Regras estáticas migradas de tupla Python para `app/content/pt-BR/assistant/typing_correction_rules.json` (159 entradas `{ pattern, replacement }`).

- Carregamento: `content_composer._configure_typo_correction_rules()` → `ChatMessageNormalizationService.configure_static_rules()`
- Validação CI/local: `python scripts/export_typing_correction_rules.py`
- Novos typos operacionais: editar o JSON (ordem importa — específicos primeiro)
