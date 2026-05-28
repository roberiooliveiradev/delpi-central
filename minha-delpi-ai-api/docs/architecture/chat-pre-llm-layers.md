# Camadas de preparação antes do LLM

**Status:** proposta de arquitetura (maio/2026)  
**Público:** `minha-delpi-ai-api`, plugin `minha-delpi-chat`  
**Relacionado:** [`chat-intelligence-base.md`](./chat-intelligence-base.md)

---

## Por que camadas?

Chats de IA maduros **não** mandam a pergunta crua direto ao modelo. Antes do LLM entram etapas determinísticas (regras, classificadores leves, APIs, RAG) que:

- **Reduzem custo e latência** — resposta direta sem tokens quando a intenção é clara.
- **Aumentam confiabilidade** — roteamento para a API certa (ex.: `group_code` vs `/analyser`).
- **Protegem o sistema** — sanitização, permissões, limites de contexto.
- **Enriquecem o prompt** — só o que o turno precisa (histórico resumido, tool results, chunks RAG).

No Minha DELPI isso já acontece, mas está **espalhado** no `StreamChatMessageUseCase` / `SendChatMessageUseCase`. O objetivo é tornar o fluxo **explícito, ordenado e extensível**.

---

## Modelo mental: três fases

```text
┌─────────────────────────────────────────────────────────────────┐
│  FASE A — Ingresso (por turno, uma vez)                         │
│  segurança → workspace → normalização → classificação de intenção │
└───────────────────────────────┬─────────────────────────────────┘
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  FASE B — Resolução (pode encurtar o turno)                     │
│  atalhos → tools/actions → resposta direta → identidade/capac.  │
└───────────────────────────────┬─────────────────────────────────┘
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  FASE C — Montagem do prompt (só se ainda precisa do LLM)      │
│  RAG → anexos → policies/skills → histórico → mensagens LLM     │
└───────────────────────────────┬─────────────────────────────────┘
                                ▼
                          LLM (stream/send)
```

**Regra de ouro:** cada camada retorna um de três resultados:

| Resultado | Significado |
|-----------|-------------|
| `Continue` | Segue para a próxima camada; pode alterar `ChatTurnContext`. |
| `Answer(text)` | **Short-circuit** — resposta final sem LLM (ou com playback só da string). |
| `Abort(error)` | Erro controlado (segurança, permissão, validação). |

---

## Mapeamento: o que o projeto já tem hoje

| Camada (conceitual) | Implementação atual | Onde |
|---------------------|---------------------|------|
| Segurança de entrada | `ChatMessageSecurityService.secure_message` | use cases (início) |
| Workspace (agente, projeto, actions) | `ChatWorkspaceContextService` | use cases |
| Normalização / typos | `ChatMessageNormalizationService` | seleção de rotas, intents |
| Classificação operacional vs análise | `ChatIntelligencePipelineService.resolve_pre_tool_decisions` | `operational_optimize`, `analysis_mode` |
| Fast path (mensagem curta) | `ChatFastPathService` | use cases |
| Pergunta de capacidade | `ChatCapabilitiesService.resolve_capability_answer` | use cases (antes de tools) |
| Canvas / lousa | `ChatCanvasContentService` | use cases |
| Tools + OpenAPI | `ChatToolContextService` + `ExternalActionSelectionService` | tools |
| Pós-tools / modo análise | `ChatIntelligencePipelineService.finalize_after_tools` | use cases |
| Resposta direta API | `ChatExternalActionDirectResponseService` | pipeline |
| Comparação estruturas | `ChatStructureComparisonService` | pipeline |
| Identidade usuário/assistente | `ChatUserContextService`, `ChatAssistantIdentityService` | use cases |
| RAG | `RagContextService` + `KnowledgeScopeService` | use cases |
| Prompt | `ChatPromptBuilderService` + `PromptPolicyService` | use cases |
| LLM | gateway Ollama/vLLM | use cases |

Ou seja: **as camadas existem**; falta **contrato único** (`ChatTurnContext`) e **pipeline registrável** para novas camadas sem inflar o use case.

---

## Proposta: `ChatTurnPreparationPipeline`

### 1. Contexto único do turno

Objeto imutável (ou copy-on-write) criado no início do turno e passado a todas as camadas:

```python
@dataclass
class ChatTurnContext:
    # Entrada
    message: str
    normalized_message: str
    session_id: str
    user_id: str
    attachment_ids: list[str]
    previous_messages: list
    workspace_context: dict
    allowed_action_ids: list[str]

    # Decisões (preenchidas pelas camadas)
    operational_optimize: bool = False
    analysis_mode: bool = False
    fast_path: bool = False
    skip_rag: bool = False
    direct_answer: str | None = None
    tool_context: dict | None = None
    rag_context: dict | None = None

    # Telemetria
    stages_run: list[str] = field(default_factory=list)
    timings_ms: dict[str, float] = field(default_factory=dict)
```

Os use cases deixam de espalhar 15 variáveis locais; leem/escrevem o contexto.

### 2. Interface de estágio

```python
class ChatTurnStage(Protocol):
    name: str

    def run(self, ctx: ChatTurnContext) -> StageResult: ...
```

`StageResult`:

- `continue_()` — próximo estágio
- `answer(text, *, skip_llm=True, skip_rag=True)` — short-circuit
- `abort(code, detail)` — erro HTTP

### 3. Ordem recomendada de estágios (registro)

Ordem fixa no **chat base**; agentes só alteram *dados* (skills, actions), não a ordem.

| # | Estágio | Short-circuit? |
|---|---------|----------------|
| 1 | `SecurityStage` | abort |
| 2 | `WorkspaceStage` | — |
| 3 | `NormalizeStage` | preenche `normalized_message` |
| 4 | `PreToolDecisionStage` | flags operacional/análise |
| 5 | `CanvasStage` | answer |
| 6 | `CapabilityStage` | answer («consegue…?») |
| 7 | `ToolExecutionStage` | tool_context |
| 8 | `PostToolStage` | analysis_mode, direct_answer |
| 9 | `IdentityStage` | answer (quem é você / usuário) |
| 10 | `RagStage` | só se `direct_answer` vazio e não `skip_rag` |
| 11 | `PromptAssemblyStage` | mensagens para LLM |

Estágios 5–9 são os que mais evitam chamadas erradas à api-delpi **antes** do modelo “inventar” rota.

### 4. Onde colocar regras novas

| Tipo de regra | Onde implementar | Exemplo |
|---------------|------------------|---------|
| Sinônimo / typo | `NormalizeStage` ou serviço chamado por ele | ebita → ebitda |
| Intenção → rota API | `ToolExecutionStage` → `ExternalActionSelectionService` | grupo 1008 → search |
| Pergunta meta | `CapabilityStage` | buscar por grupo? |
| Formato da resposta | `PostToolStage` → presenter | tabela vs markdown |
| Comportamento do LLM | `prompt_policies/*.md` | tom, SQL, análise |

**Não** colocar regra de rota no `system_prompt` do agente se ela deve valer para todos.

---

## Fluxo de decisão (exemplo real)

Pergunta: *«busque 3 produtos do grupo 1008»*

```text
SecurityStage          → Continue
WorkspaceStage         → allowedActionIds inclui search
NormalizeStage         → texto normalizado
PreToolDecisionStage   → operational_optimize=true
CapabilityStage        → Continue (não é pergunta de capacidade)
ToolExecutionStage     → select_action → GET /products/search
                         group_code=1008, page_size=3
PostToolStage          → direct_answer com lista humanizada
RagStage               → skip (operational + direct_answer)
PromptAssemblyStage    → não chama LLM se direct_answer preenchido
```

Pergunta: *«compare as duas estruturas e traga insights»*

```text
PreToolDecisionStage   → analysis_mode=true, operational=false
ToolExecutionStage     → plan_structure_fetches (multi action)
PostToolStage          → comparison markdown OU contexto para LLM
RagStage               → pode rodar com policy chat-analysis-insights
LLM                    → só síntese; não re-executa APIs sem necessidade
```

---

## Implementação por fases (baixo risco)

### Fase 1 — Documentação + telemetria (sem refactor grande)

- [x] Este documento.
- [ ] Garantir `metadata.pipeline.stages` no assistant (lista de estágios executados).
- [ ] Expandir `ChatPipelineTimings` com chaves por estágio.

### Fase 2 — Extrair estágios do use case

- [ ] Criar `app/application/services/chat_turn/` com `context.py`, `pipeline.py`, `stages/*.py`.
- [ ] `StreamChatMessageUseCase` chama `ChatTurnPreparationPipeline.run(ctx)` e só depois monta LLM.
- [ ] `SendChatMessageUseCase` usa o **mesmo** pipeline (paridade stream/send).
- [ ] Testes: um teste por estágio + testes de integração do pipeline com fixtures.

### Fase 3 — Registro e extensão

- [ ] `Settings.CHAT_EXTRA_STAGES` ou registro por skill (`metadata.preLlmStages`) para experimentos admin.
- [ ] Simulação de agente (`AdminAgentSimulateUseCase`) usa o mesmo pipeline.

### Fase 4 — Classificador leve opcional

- [ ] Antes do LLM, classificador barato (regex + embeddings pequenos) só quando heurística e ranker empatarem.
- [ ] Nunca substituir regras críticas (grupo vs produto, estoque empresa vs item).

---

## Anti-padrões a evitar

1. **Lógica de rota só no prompt** — o modelo erra; use `ExternalActionSelectionService`.
2. **Duplicar pipeline em stream e send** — um único `ChatTurnPreparationPipeline`.
3. **LLM escolher action sem allow-list** — sempre filtrar por `allowedActionIds` do agente.
4. **Pular normalização** — typos quebram regex de grupo/código.
5. **RAG sempre ligado** — resposta operacional direta deve `skip_rag` quando já há `humanizedSummary`.

---

## Configuração (env sugeridas)

| Variável | Efeito |
|----------|--------|
| `CHAT_OPERATIONAL_FAST_PATH_ENABLED` | Ativa seleção determinística de actions |
| `CHAT_FAST_PATH_ENABLED` | Mensagens curtas → menos RAG/tools |
| `CHAT_MULTI_ACTION_ENABLED` | Várias actions no mesmo turno |
| `CHAT_HISTORY_MAX_MESSAGES` | Histórico enxuto no fast path operacional |
| `RAG_CONTEXT_MIN_SCORE` | Corte de ruído no contexto documental |

---

## Referências no repositório

- Pipeline vigente: [`chat-intelligence-base.md`](./chat-intelligence-base.md)
- Use cases: `stream_chat_message_use_case.py`, `send_chat_message_use_case.py`
- Orquestração inteligência: `chat_intelligence_pipeline_service.py`
- Policies LLM: `app/domain/prompt_policies/`
- Roadmap onda 1: [`../roadmap/inteligencia-chat-onda-1.md`](../roadmap/inteligencia-chat-onda-1.md)
