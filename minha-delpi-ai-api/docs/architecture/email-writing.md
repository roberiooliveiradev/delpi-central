# Arquitetura — Escrita de e-mails no chat base

**Status:** vigente (maio/2026)  
**Playbook:** [`../roadmap/melhorias/playbook_escrita_emails_minha_delpi_chat.md`](../roadmap/melhorias/playbook_escrita_emails_minha_delpi_chat.md)

---

## Princípio

E-mails corporativos são **inteligência transversal do chat**, não skill isolada de agente. Agentes herdam policies, validação, chips e memória de preferências.

---

## Pipeline

```text
Mensagem
  → ChatTextTaskIntentService (text_task puro vs misto operacional)
  → ChatEmailIntentService (subtipo email_*)
  → estágio email_writing no turn prep
  → PromptPolicyService (administrative-writing + email-writing)
  → ChatEmailPromptSupplementService (destinatário, tom, DELPI/IA, preferências)
  → LLM ou resposta direta (operacional)
  → ChatEmailAnswerGuardService (sanitize)
  → ChatEmailQualityValidator
  → ChatEmailFollowUpService (chips + metadata)
```

### Turno misto / follow-up operacional

```text
Consulta ERP → humanizedSummary
  → ChatEmailOperationalComposerService
  → estágios text_task_mixed + email_operational
  → metadata emailDataSource + textTask.source = operational_data
```

---

## Serviços

| Serviço | Papel |
|---------|--------|
| `ChatEmailIntentService` | Subintenções e extração de contexto |
| `ChatEmailPreferenceService` | Preferências «sempre curtos/formais» + persistência `emailWriting` |
| `ChatEmailOperationalComposerService` | Rascunho só com dados autorizados + rodapé de fonte |
| `ChatEmailQualityValidator` | Checklist pós-geração |
| `ChatEmailAnswerGuardService` | Remove assinatura inventada / frases artificiais |
| `ChatEmailTurnService` | Orquestra prompt, guard e metadata |
| `ChatEmailFollowUpService` | `emailFollowUpSuggestions`, `textTask`, `emailPreferences` |

---

## Metadata do assistente (referência)

| Campo | Uso |
|-------|-----|
| `textTask` | tipo, subtipo, destinatário, tom, assunto |
| `emailFollowUpSuggestions` | chips de refinamento |
| `emailQuality` | resultado do validador |
| `emailGuard` | sanitização aplicada |
| `emailDataSource` | consulta operacional usada no rascunho |
| `emailPreferences` | preferências ativas da sessão |

---

## Validação

```bash
cd minha-delpi-ai-api
./scripts/run_email_writing_validation.sh
```

Container:

```bash
docker compose -f infra/docker-compose.dev.yml exec -T minha-delpi-ai-api \
  bash -c 'SMOKE_BASE_URL=http://delpi-gateway ./scripts/run_email_writing_validation.sh'
```

Regressão: `tests/fixtures/chat_intelligence_regression_cases.py` → `EMAIL_*_CASES` e `test_chat_email_intelligence_regression.py`.

---

## MFE (`minha-delpi-chat`)

- Chips «Refinar e-mail» (`emailFollowUpSuggestions`)
- Botão «Copiar e-mail» quando `textTask.type === email`
- Tipos em `chatTypes.ts`: `emailDataSource`, `emailPreferences`
