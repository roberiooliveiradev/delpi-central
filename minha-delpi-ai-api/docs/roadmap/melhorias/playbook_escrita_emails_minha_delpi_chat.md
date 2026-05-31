# Playbook — Melhoria da Escrita de E-mails no Minha DELPI Chat IA

**Projeto:** Minha DELPI Chat IA  
**Status implementação:** Fases 1–2 concluídas; Fase 3 parcial (preferências); Fase 4 parcial (copiar e-mail no MFE) — maio/2026  
**Código:** `ChatEmailIntentService`, `ChatEmailQualityValidator`, `ChatEmailAnswerGuardService`, `ChatEmailPromptSupplementService`, `ChatEmailPreferenceService`, `ChatEmailTurnService`, policy `email-writing.md`

---

## 1. Objetivo

Camada especializada para escrever, revisar e adaptar e-mails corporativos com linguagem natural, profissional e segura — sem textos genéricos, frases artificiais, assinatura inventada ou dados fictícios.

**Regra central:** e-mail bom = objetivo claro + tom adequado + assunto forte + sem dados inventados + opções de ajuste.

---

## 2. Problemas observados (baseline)

| Problema | Exemplo ruim | Direção |
|----------|--------------|---------|
| Frase artificial | «Estou em consideração…» | «Gostaria de solicitar sua avaliação…» |
| Assunto rígido | «Solicitação de Criação de IA…» | «Proposta de Implementação de IA no Minha DELPI» |
| Conteúdo genérico | IA abstrata | Conectar com agentes, consultas, lousa, anexos, gráficos, dados internos |
| Assinatura inventada | Roberto Silva / Superadministrador | `[Seu nome]` ou dado explícito do usuário |
| Sem refinamento | — | Chips pós-resposta |

---

## 3. Quando ativar

Termos: *escreva um e-mail*, *redija*, *responda este e-mail*, *melhore este e-mail*, *deixe mais formal/cordial/firme*, *comunicado por e-mail*, *e-mail para fornecedor/cliente*, refinamentos sobre *e-mail anterior*.

Pipeline: mensagem → `ChatTextTaskIntentService` (text_task puro) → `ChatEmailIntentService` (subtipo) → policy `email-writing.md` → LLM → `ChatEmailQualityValidator` → chips `emailFollowUpSuggestions`.

---

## 4. Subintenções (`ChatEmailIntentService`)

| Subtipo | Uso |
|---------|-----|
| `email_create` | Criar do zero |
| `email_reply` | Responder e-mail recebido |
| `email_rewrite` | Melhorar existente |
| `email_correct` | Gramática/clareza |
| `email_shorten` | Mais curto |
| `email_formalize` | Mais formal |
| `email_soften` | Mais cordial |
| `email_firm` | Mais firme |
| `email_subjects` | Opções de assunto |
| `email_translate` | Tradução |

---

## 5. Assinatura (obrigatório)

- **Nunca** inventar nome, cargo ou área.
- Informado pelo usuário → usar exatamente.
- Não informado → `Atenciosamente,\n\n[Seu nome]`.

---

## 6. Metadata na resposta

```json
{
  "textTask": {
    "type": "email",
    "subtype": "email_create",
    "recipient": "…",
    "tone": "formal",
    "missingFields": ["senderName"],
    "inventedFieldsPrevented": true
  },
  "emailFollowUpSuggestions": [{ "label": "…", "query": "…" }],
  "emailQuality": { "passed": true, "checks": [] }
}
```

---

## 7. Chips pós-resposta

Deixar mais formal · mais curto · tom executivo/cordial/firme · assunto alternativo · WhatsApp · traduzir · lousa — ver `personality_playbook.json` → `emailFollowUpChips`.

---

## 8. Validador (`ChatEmailQualityValidator`)

Assunto, objetivo no início, linguagem natural, assinatura segura, prazos não inventados, pedido explícito.

---

## 9. Exemplo ideal (IA Minha DELPI)

**Pedido:** «escreva um e-mail formal para Robério sobre criar uma IA para Minha DELPI»

**Assunto:** Proposta de Implementação de IA no Minha DELPI

Corpo com proposta, capacidades reais da plataforma, perguntas numeradas para avaliação, fechamento cordial e `[Seu nome]`.

---

## 10. Roadmap

| Fase | Escopo | Status |
|------|--------|--------|
| 1 | Policy, subintent, validador, chips, placeholders | **Concluída** |
| 2 | Validador ampliado, guard/sanitize, suplemento de prompt | **Concluída** |
| 3 | Memória de preferências (`ChatEmailPreferenceService`) | **Parcial** |
| 4 | Botão «Copiar e-mail» no MFE | **Concluída** |
| 5 | E-mail com contexto operacional (dados autorizados) | Pendente (`ChatTextTaskComposerService`) |

---

## 11. Testes

`tests/unit/test_email_writing_skill.py` — casos E1–E15 (subset automatizado).  
`tests/unit/domain/services/test_chat_email_*.py` — intent e qualidade.  
`scripts/run_email_writing_validation.sh` — suite unit + `scripts/smoke_email_writing.py`.

---

## 12. Feedback

Motivos em `personality_playbook.json`: `email_wrong_tone`, `email_artificial`, `email_invented_signature`, `email_invented_info`, `email_weak_subject`, `email_too_generic`.

---

## Referência arquitetural

[`docs/architecture/chat-intelligence-base.md`](../../architecture/chat-intelligence-base.md) — inteligência no chat base, não só no prompt do agente.
