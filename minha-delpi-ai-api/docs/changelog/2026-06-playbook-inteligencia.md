# Changelog — Playbook inteligência do chat

**Data:** 03/06/2026
**Escopo:** [`docs/roadmap/playbook-inteligencia.md`](../roadmap/playbook-inteligencia.md) — entender perguntas simples, typos, preferências, erros e UX de streaming.
**Arquitetura:** detalhes em [`docs/architecture/chat-intelligence-base.md`](../architecture/chat-intelligence-base.md).

Princípio: *pergunta simples → resposta simples*; usar ferramenta só quando necessário; admitir quando não entendeu; avisar e **contornar** erros.

---

## Fase 1 — Normalização de typos

Entradas como «oq vc faz», «cmo», «cm», «qm», «qual eh», «seu nom», «vc s chama», «naum/num entendi» passam a normalizar para a forma canônica antes do roteamento, evitando que pequenos erros de digitação caiam em ferramenta ou LLM desnecessários.

**UI (jun/2026):** [Playbook 14](../roadmap/playbook-14-corretor-digitacao-chat.md) — chip pré-envio no composer (`POST /chat/typing-suggestions`); [changelog](../changelog/2026-06-playbook-14-corretor-digitacao-composer.md).

---

## Fase 2 — Gate de turno simples

- **`ChatSimpleTurnGateService`** — decide, **antes** de qualquer atividade técnica, que o turno é simples (identidade, saudação, agradecimento, hora/data, capacidades, «não entendi»).
- Integrado ao `StreamChatMessageUseCase`: em turno simples, `_on_stream_activity` é suprimido (nenhuma etapa técnica no painel) e a resposta direta segue pelos serviços existentes.

---

## Fase 3 — Fallback honesto (não entendi)

- Conteúdo **`assistant/unclear_requests.json`** + **`ChatUnclearRequestService`**: quando o pedido é vago/ininteligível, o chat admite que não entendeu e oferece opções de esclarecimento, em vez de inventar.
- Integrado ao `ChatTurnPreparationService` (após small talk/utility, antes do LLM) e ao estágio de intent router.

---

## Fase 4 — Preferências de sessão

- **`ChatBehaviorInstructionService`** detecta novas preferências persistentes:
  - `responseFormat: text` — «sempre em txt», respostas em texto puro sem tabelas.
  - `toolsPolicy: on_request` — «não use ferramentas sem eu pedir».
- **`ChatUserPreferenceManagerService`** reconhece, rotula e confirma as preferências; revogação ampliada para «esqueça essa preferência» e «volte ao normal» (com ACK explícito de retorno ao padrão).
- ACK consistente em `ChatSessionMemoryDirectAnswerService`.

---

## Fase 8 — Métricas de eficiência (§30) e feedback (§31)

**Métricas (§30):**
- Flags de eficiência por turno em `ChatFeedbackContextService` espelhadas em `responseQuality` (`ChatResponseMetadataService`): `directAnswer`, `fallback`, `toolSkipped`, `ragSkipped`, `llmSkipped`, `simpleTurn`.
- `ChatIntentRouterMetricsService`: `requiresLlm` no snapshot, helper único `is_simple_turn_snapshot`, e agregados `simpleTurnCount`, `fallbackCount`, `directAnswerCount`.
- **Tempo médio de perguntas simples**: `PostgresAdminMetricsRepository` calcula `simpleTurnLatencyAvgMs` + `simpleTurnCount` a partir dos logs de auditoria; exposto em `ChatQualityUnifiedMetricsService` (seção `efficiency`).

**Feedback (§31):** novos motivos em `personality_playbook.json` — `simple_question_missed`, `unnecessary_tool`, `too_slow`, `technical_diagnostic_shown`, `unclear_not_admitted` — e correção de `chip_irrelevant` (referenciado mas ausente do array). Regenerar MFE: `python scripts/generate_chat_feedback_reasons_ts.py --write`.

---

## §25 — Starters do chat comum

`assistant/onboarding.json` (`starterCards`) abre amplo: capacidades, corrigir texto, escrever e-mail, consultar dados, analisar documento, pesquisar na web — não começa por «Ver estoque». Welcome e tour atualizados. `profilePresets` e icebreakers de agente seguem operacionais.

---

## §24 — Streaming humanizado

As etapas continuam **visíveis** (o usuário precisa saber que o chat está trabalhando e que a resposta evolui), mas o headline (`message`) de cada activity é natural e tranquilizador — sem jargão («rota OpenAPI», «API DELPI», «RAG», caminhos crus). O técnico fica no `detail` (painel expandido / admin). Ex.: «Entendendo o seu pedido...», «Vendo a melhor forma de te ajudar...», «Buscando as informações que você pediu...», «Procurando nas informações de apoio...».

Pontos de edição: `ChatStreamActivityService`, `ChatTurnPreparationService`, `StreamChatMessageUseCase`, `chat_external_action_orchestration_service.py`, `assistant/stream.json`.

---

## Avisar e contornar erros (§26/§27)

**Avisar** — falhas no meio do caminho deixam de ser silenciosas:
- Loop agentic emite `tool_finished` para sucesso **e** falha de cada ferramenta.
- Falha na preparação do turno emite uma activity de erro («Tive um problema ao preparar a sua resposta.») antes de propagar.

**Contornar** — `ChatAgenticToolLoopService`:
- Detecta falha por exceção **ou** metadata (`ok=False` / HTTP não-2xx) via `_looks_like_failure`; resume em `_summarize_failure`.
- O planejador (`_plan_tools`) recebe as falhas e é instruído a **não repetir** a consulta que falhou e tentar uma **abordagem alternativa** (outra action, outros parâmetros, busca por descrição, ampliar filtros). Payload de erro não vira «resultado autorizado» para o LLM.
- Sem contexto novo mas com falhas, as `toolCalls` falhas são propagadas para a camada §27 (`ChatErrorHandlingService`) enriquecer com motivos + chips de recuperação.
- `error_handling.json` → `chipQueries`: rótulos antes sem ação agora têm query útil («Buscar por descrição», «Mostrar SQL», «Executar consulta», «Interpretar resultado», «Corrigir consulta», «Ver schema», «Ver schema completo»).

Camadas pré-existentes mantidas: recuperação de coluna SQL inválida (`ChatSqlRecoveryService`), reexecução sob demanda (`fetch_error_recovery_from_history`), plano `errorAutoRecovery`.

---

## Validação

```bash
.venv/bin/python -m pytest tests/unit -k "preference or feedback_efficiency or agentic or error_handling or stream_activity or simple_turn or unclear" -q --continue-on-collection-errors
python scripts/generate_chat_feedback_reasons_ts.py --write
```

> Ambiente local sem `sqlalchemy`/`flask` gera erros de coleta em alguns módulos (pré-existente); a suíte completa roda em CI.

## Pendência conhecida

Falha **total** da preparação do turno ainda propaga erro técnico (SSE/HTTP 500) sem cair num card §27. Degradação graciosa completa (persistir mensagem assistente com `errorHandling`) fica como próximo passo.
