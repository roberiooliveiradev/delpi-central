# Playbook 14 — Corretor de digitação no chat (typos operacionais)

**Projeto:** Minha DELPI Chat IA  
**Escopo:** reduzir erros de digitação em **perguntas operacionais** antes e no envio — sem confundir com a habilidade «corrija este texto».  
**Status:** **Implementado (jun/2026)** — P14-1 a P14-3 + telemetria parcial  
**Changelog:** [2026-06-playbook-14-corretor-digitacao-composer.md](../changelog/2026-06-playbook-14-corretor-digitacao-composer.md)  
**Relacionado:** [playbook-inteligencia.md](./playbook-inteligencia.md), [playbook-aprendizagem-continua.md](./playbook-aprendizagem-continua.md), [playbook_correcao_texto (melhorias)](./melhorias/playbook_correcao_texto_minha_delpi_chat.md), [chat-intelligence-base.md](../architecture/chat-intelligence-base.md)

---

## 1. Objetivo

Quando o usuário digita «estouque do produto 90262404» ou «status fabril filial 01», o chat deve:

1. **Entender** a intenção (já ocorre em parte via normalização silenciosa na API).
2. **Opcionalmente mostrar** sugestões de correção **antes do envio**, para o usuário confirmar ou ignorar.
3. **Nunca** alterar silenciosamente códigos de produto, filiais, valores ou termos técnicos Protheus.

**Meta de produto:** menos falhas de roteamento, menos «não entendi», menos reenvios — com transparência (o usuário vê o que foi sugerido).

---

## 2. O que **não** é este playbook

| Tema | Playbook / módulo | Diferença |
|------|-------------------|-----------|
| «Corrija este e-mail» | [playbook_correcao_texto](./melhorias/playbook_correcao_texto_minha_delpi_chat.md) | Tarefa textual com LLM; revisão de parágrafos inteiros |
| Normalização silenciosa (hoje) | `ChatMessageNormalizationService` | Só para **matching** interno; usuário não vê a correção |
| Aprendizagem de vocabulário | `ChatVocabularyLearningService` + `ChatLearnedNormalizationService` | Alimenta regras aprovadas no normalizador — **sem UI** hoje |

Este playbook cobre **UX + contrato** de sugestão de typos no composer do chat.

---

## 3. Baseline atual (jun/2026)

### 3.1 API — normalização determinística

`ChatMessageNormalizationService.normalize_for_matching()` aplica:

- ~180 regras regex estáticas (`estouque`→`estoque`, `filail`→`filial`, `bo dia`→`bom dia`, …).
- Regras **aprendidas** via `set_learned_rules()` (termos aprovados no admin de aprendizagem).

Usado por: roteamento de intenção, seleção de action, SQL, web search, utilitários, etc.

**Limitação:** o texto exibido na UI e persistido no histórico permanece **com typo**; só a camada interna vê a forma normalizada.

### 3.2 MFE — sem corretor no composer

`ChatInput.tsx` — `<textarea>` sem `spellCheck`, sem diff pré-envio, sem chip «Você quis dizer…?».

### 3.3 Smoke documentado

[`smoke-operacional-manual.md`](../testing/smoke-operacional-manual.md) — caso «estouque do produto» espera comportamento correto **via API**, não via feedback visual.

---

## 4. Pesquisa — opções de implementação

### 4.1 Comparativo de abordagens

| Abordagem | Prós | Contras | Recomendação DELPI |
|-----------|------|---------|-------------------|
| **`spellcheck` nativo do browser** (`lang="pt-BR"`) | Zero backend; acessível | Ruim com jargão ERP (BOM, CPV, códigos); pt-BR com acentos inconsistente em sugestões | **Camada 0 opcional** — ligar só em modo «Texto livre», desligado em consultas operacionais |
| **Dicionário de domínio + diff** (mesmas regras do normalizador) | Determinístico, testável, alinhado ao roteamento; offline | Não corrige frases novas fora do vocabulário | **Camada 1 — preferida (MVP)** |
| **Fuzzy match (Levenshtein / SymSpell)** sobre vocabulário operacional | Cobre typos não listados | Falsos positivos em códigos numéricos; custo de manutenção do léxico | **Camada 2** — só tokens ≥4 chars e fora de `\d{5,}` |
| **Endpoint API `/spell-suggest`** | Uma fonte de verdade API+MFE; regras aprendidas centralizadas | Latência no blur/envio | **Camada 1b** se bundle MFE ficar grande |
| **LLM por keystroke ou por envio** | Flexível | Latência, custo, alucinação em códigos; viola princípio «pergunta simples → resposta simples» | **Não** para typos operacionais |
| **Chrome Proofreader API / Gemini Nano on-device** | Privacidade local | Disponibilidade heterogênea; difícil restringir domínio ERP | **Backlog exploratório** — não dependência |

Referências externas: [Chrome Proofreader API](https://developer.chrome.com/docs/ai/proofreader-api?hl=pt-br); boas práticas de validação inline — *late-fail, early-success* (validar após pausa/blur, não a cada tecla).

### 4.2 Princípios UX (obrigatórios)

1. **Sugerir, não impor** — chip ou banner «Enviar corrigido» / «Manter como digitou»; nunca autocorrect silencioso em códigos.
2. **Late-fail** — avaliar após ~400–800 ms de pausa ou no blur do textarea, não a cada caractere.
3. **Preservar tokens protegidos** — regex para códigos de produto (`\b\d{5,}\b`), filiais (`\b\d{2}\b` em contexto), `@menções`, paths SQL, números decimais.
4. **Transparência** — se a API normalizou internamente, metadata opcional `typingCorrection: { applied: false, suggested: "…" }` para debug/admin.
5. **Acessibilidade** — `aria-live="polite"` no chip de sugestão; atalho Tab para aceitar, Esc para dispensar.

---

## 5. Arquitetura recomendada

### 5.1 Camadas

```text
┌─────────────────────────────────────────────────────────────┐
│ MFE (ChatInput)                                              │
│  • spellCheck opcional (modo texto)                          │
│  • debounce → suggestTypingCorrections(draft)                │
│  • chip «Enviar: estoque do produto…» | «Manter original»   │
└───────────────────────────┬─────────────────────────────────┘
                            │ (fase 1: bundle TS espelhado)
                            │ (fase 1b: GET/POST spell-suggest)
┌───────────────────────────▼─────────────────────────────────┐
│ API — módulo canônico NOVO                                   │
│  ChatTypingCorrectionService                                 │
│    • reutiliza regras de ChatMessageNormalizationService     │
│    • diff token a token → TypingCorrectionSuggestion[]       │
│    • respect protected spans (product codes, mentions)       │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│ ChatLearnedNormalizationService (existente)                  │
│  • termos aprovados → mesmas regras para suggest + matching  │
└─────────────────────────────────────────────────────────────┘
```

**Regra clean architecture:** extrair lista de substituições para **fonte única** (JSON em `assistant/` ou gerador a partir do serviço Python) — evitar duplicar regex em TS e Python.

### 5.2 Contrato metadata (turno)

Quando o usuário **aceita** a sugestão antes do envio:

```json
{
  "typingCorrection": {
    "original": "estouque do produto 90262404",
    "corrected": "estoque do produto 90262404",
    "accepted": true,
    "source": "domain_dictionary",
    "changes": [
      { "from": "estouque", "to": "estoque", "kind": "typo_rule" }
    ]
  }
}
```

Persistir em `userMessage` o texto **corrigido**; manter `original` só em metadata do turno (auditoria, métricas).

### 5.3 Endpoint opcional (fase 1b)

```http
POST /v1/chat/typing-suggestions
Content-Type: application/json

{ "text": "estouque do produto 90262404 na fabrica", "locale": "pt-BR" }
```

```json
{
  "hasSuggestions": true,
  "corrected": "estoque do produto 90262404 na fabrica",
  "changes": [
    { "offset": 0, "length": 8, "replacement": "estoque", "kind": "typo_rule" }
  ],
  "protectedSpans": [{ "start": 19, "end": 27, "reason": "product_code" }]
}
```

Handler fino em `interfaces/http`; lógica em `ChatTypingCorrectionService` (domain).

---

## 6. Integração com aprendizagem contínua

Fluxo existente (não duplicar):

```text
Usuário define typo → candidato ChatVocabularyLearningService
  → admin aprova → ChatLearnedNormalizationService.refresh()
    → ChatMessageNormalizationService.set_learned_rules()
```

**Extensão P14:** mesmas regras alimentam `ChatTypingCorrectionService` automaticamente — sugestão na UI e matching interno **sempre alinhados**.

Gate admin: rejeitar regras que alterem códigos ou siglas de uma letra (`LMP`, `CPV`, `BOM`).

---

## 7. Onde encaixar no pipeline do chat

| Momento | Comportamento |
|---------|---------------|
| **Composer (pré-envio)** | Sugestão visual; usuário escolhe |
| **Send / Stream use case** | Recebe texto já escolhido pelo usuário; **não** re-normalizar silenciosamente o conteúdo persistido |
| **Matching interno** | Continua `normalize_for_matching` para intenção — deve ser **idempotente** com texto já corrigido |
| **Turno misto** | Se mensagem contém bloco «corrija: …», desligar sugestor de typo no trecho após `:` (delegar ao playbook de correção textual) |

Serviços a **não** patchar: `SendChatMessageUseCase`, `StreamChatMessageUseCase` — orquestração fina; regra no serviço de domínio.

---

## 8. MFE — pontos de implementação

| Arquivo | Mudança |
|---------|---------|
| `ChatInput.tsx` | Debounce, chip de sugestão, props `typingSuggestion` |
| `useChatSession.ts` / `ChatPage.tsx` | Aceitar envio com `correctedText`; metadata no payload |
| `chatTypingCorrection.ts` (novo) | `buildTypingSuggestions`, `applyAcceptedCorrection`, tokens protegidos |
| `assistant/*.json` (sync opcional) | Rótulos: «Enviar corrigido», «Manter original», «Você quis dizer…» |

**Feature flag:** `CHAT_TYPING_CORRECTION_ENABLED` (API + MFE) — default `true` em dev, rollout gradual em prod.

Conteúdo PT: `message_composer.json` ou seção em `onboarding.json` — seguir [assistant-content-json](../../.cursor/rules/assistant-content-json.mdc).

---

## 9. Regras de segurança (não negociáveis)

| Regra | Motivo |
|-------|--------|
| Não sugerir correção dentro de `\d{5,}` | Código de produto |
| Não sugerir em `@agente` / `@projeto` | Menções |
| Não sugerir em strings entre backticks | SQL / paths |
| Não expandir abreviações ambíguas (`num`→`numero`) sem contexto | Quebra «num entendi» vs «numero da OP» |
| Máximo 3 substituições por sugestão | Evitar reescrita agressiva |
| Dispensar sugestão → não repetir na mesma sessão para o mesmo par | Evitar irritação |

---

## 10. Roadmap de implementação

| Fase | Escopo | Entregáveis | Status |
|------|--------|-------------|--------|
| **P14-0 — Inventário** | Extrair regras estáticas para JSON/catálogo; documentar gaps | `typing_correction_rules.json` ou export do serviço; diff estático vs learned | Parcial (`iter_typo_patterns`) |
| **P14-1 — Serviço + diff** | `ChatTypingCorrectionService.suggest()`; testes espelhando `test_chat_message_normalization_service.py` | API pura; sem UI | **Concluído** |
| **P14-2 — UX composer** | Chip pré-envio no MFE; flag; textos JSON | Vitest `chatTypingCorrection.test.ts`; homologação manual U2 smoke | **Concluído** |
| **P14-3 — Endpoint** | `POST typing-suggestions` se bundle duplicado for inviável | Contrato OpenAPI; paridade MFE | **Concluído** |
| **P14-4 — Métricas** | `typingCorrectionMetrics`: offered / accepted / dismissed | Admin debug + dashboard aprendizagem | Parcial (`help-events`: `typing_correction_*`) |
| **P14-5 — Fuzzy léxico** | SymSpell só vocabulário operacional (rotas, KPIs) | Gate falsos positivos | Backlog |

**Ordem sugerida:** P14-0 → P14-1 → P14-2 → métricas.

---

## 11. Testes de regressão

| ID | Entrada | Esperado |
|----|---------|----------|
| T1 | `estouque do produto 90262404` | Sugestão `estoque`; código intacto |
| T2 | `qual o status fabril filial 01` | Sem sugestão ou só typos lexicais; `01` intacto |
| T3 | `corrija: estouque baixo` | Sem sugestor no trecho após `corrija:` |
| T4 | `@Agente estouque` | `@Agente` intacto |
| T5 | Regra aprendida aprovada | Sugestão MFE = normalize API |
| T6 | Usuário dispensa chip | Reenvio igual não reabre chip (sessão) |
| T7 | `SELECT * FROM` | Sem sugestão no SQL |

Arquivos alvo:

- `tests/unit/domain/services/test_chat_typing_correction_service.py`
- `tests/fixtures/chat_typing_correction_cases.py`
- `plugins/minha-delpi-chat/src/state/chatTypingCorrection.test.ts`
- Estender smoke U2b em [`smoke-operacional-manual.md`](../testing/smoke-operacional-manual.md)

---

## 12. Métricas de sucesso

| Métrica | Meta inicial |
|---------|--------------|
| Taxa de aceitação de sugestão | ≥ 40% quando exibida |
| Redução de `ambiguous_request` / roteamento errado pós-typo | −15% em casos T1–T2 |
| Falsos positivos reportados | < 2% dos turnos com sugestão |
| Latência p95 suggest (local ou API) | < 50 ms |

---

## 13. Critérios de aceite (release)

- [x] Usuário vê sugestão antes do envio em typo conhecido (`estouque`).
- [x] Códigos de produto nunca alterados na sugestão.
- [x] Texto enviado = texto aceito; histórico coerente.
- [x] Matching interno idempotente com texto corrigido.
- [x] Regras aprendidas refletidas na UI sem redeploy do MFE (via API ou sync documentado).
- [x] Nenhum texto PT hardcoded fora de `assistant/*.json`.
- [x] Testes T1–T7 verdes.

---

## 14. Referências internas

- Normalizador: `app/domain/services/chat_message_normalization_service.py`
- Aprendizado: `app/application/services/chat_learned_normalization_service.py`
- Correção textual (LLM): `app/domain/services/chat_text_correction_*`
- Capabilities: `typingCorrectionEnabled` em `GET /chat/capabilities`
- Changelog: [2026-06-playbook-14-corretor-digitacao-composer.md](../changelog/2026-06-playbook-14-corretor-digitacao-composer.md)
- Playbook inteligência § typos: [2026-06-playbook-inteligencia.md](../changelog/2026-06-playbook-inteligencia.md)

---

## 15. Resumo executivo

Hoje o chat **já tolera** typos operacionais na API, mas **esconde** a correção do usuário. O Playbook 14 fecha essa lacuna com sugestões **determinísticas**, **confirmadas pelo usuário**, reutilizando o vocabulário existente e a aprendizagem contínua — sem misturar com a habilidade de revisão textual por LLM e sem autocorrect agressivo em códigos ERP.

Próximo passo de engenharia: **P14-0** (extrair regras estáticas para catálogo JSON) e **P14-4** (dashboard admin de métricas).

---

## 16. Implementação entregue (jun/2026)

Changelog detalhado: [2026-06-playbook-14-corretor-digitacao-composer.md](../changelog/2026-06-playbook-14-corretor-digitacao-composer.md).

### Módulos

| Camada | Arquivo |
|--------|---------|
| Domain | `app/domain/services/chat_typing_correction_service.py` |
| Normalizador (fonte única) | `app/domain/services/chat_message_normalization_service.py` → `iter_typo_patterns()` |
| HTTP | `app/interfaces/http/routes/chat/meta_routes.py` → `POST /typing-suggestions` |
| Config | `CHAT_TYPING_CORRECTION_ENABLED` em `settings.py` |
| Conteúdo | `app/content/pt-BR/assistant/message_composer.json` |
| MFE hook | `plugins/minha-delpi-chat/src/state/hooks/useChatTypingCorrection.ts` |
| MFE UI | `ChatInput.tsx` (chip), `ChatPage.tsx` (envio) |
| Telemetria | `typing_correction_*` em `ChatHelpAdoptionService` |

### Variáveis de ambiente

| Variável | Default | Efeito |
|----------|---------|--------|
| `CHAT_TYPING_CORRECTION_ENABLED` | `true` | Desliga endpoint e flag `typingCorrectionEnabled` em capabilities |

Aprendizado de vocabulário (regras dinâmicas) continua gated por `CHAT_LEARNING_ENABLED` + `CHAT_LEARNING_APPLY_VOCABULARY` — mesmas regras do normalizador.

### Homologação

| ID | Passo | Esperado |
|----|-------|----------|
| U2b | Digitar `estouque do produto 90262404`, pausar ~1 s | Chip com `estoque`; código intacto |
| T6 | **Manter original** → reenviar igual | Chip não reaparece na sessão |
| Aceite | **Enviar corrigido** | Histórico com texto corrigido; metadata `typingCorrection.accepted: true` |

Ver também smoke operacional #2 em [smoke-operacional-manual.md](../testing/smoke-operacional-manual.md).
