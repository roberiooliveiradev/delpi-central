# 149 — Contexto conversacional e operacional: inventário tridimensional

**2026-10-25 | CLASSIFICAÇÃO: DISCOVERY / TO_INVENTORY (não é decisão de implementação).**
**HEAD auditado:** `1be870c5e9d6a8b389b71e77a7dd1aa4e0eb7e13`.
**Escopo:** somente READ, sem mudança em runtime e sem interferência na execução do Plano 148.

## Método obrigatório — três verificações por claim

1. **Documentação/autoridade DÉLIA:** plano 147, plano 148, contrato de `ModelInvocationRequest`; reancorar 16→50→17→49→51→52→21→20→25 + spec/ledger antes de propor qualquer implementação. Estes docs de plano não substituem a leitura integral da autoridade vigente no HEAD.
2. **Código atual:** `delia-api/app/application/capability_provision/orchestration.py`; `delia-api/app/application/model_invocation/contracts.py`. A montagem upstream da API/frontend e o adapter de transporte LLM ainda são `TO_INVENTORY`.
3. **Prática de mercado:** sessões e histórico gerenciado, compaction/summarization, trimming/relevance budgets e checkpointing (fontes oficiais nas seções abaixo). Referência de padrão, **não** aprovação para adicionar dependência/framework.

## O que está PROVEN no código

- `OperationalCapabilityOrchestrator.attempt(... prior_turns: tuple[ConversationContextTurn,...]=())` recebe turnos anteriores opcionalmente.
- `_model_stage_proposal` forma cada `ModelInvocationRequest` com `prior_context=prior_turns`, `input_text` com `<user_message>` + `workspace_context` opcional + bloco específico do stage, e `instruction_content` versionada. Portanto o **contrato** transporta histórico para invocação. **Ainda não foi comprovado** como adapter/provider serializa roles e quantos tokens foram enviados na rede.
- `ConversationContextTurn` possui `kind`, `content`, `epistemic_class`; por contrato é UNTRUSTED CONTEXT, não FACT, AuthZ, EvidenceRef ou Personal Memory.
- `_understand_goal` recebe `prior_turns`; `_prior_result_turn` busca resultado `DELIA_RESULT` mais recente; `_prior_continuation_attempt` pode tentar transformação bounded de resultado anterior em certas condições, sem substituir fresh owner fact.
- `_context_folded_discovery_query` usa no máximo `MAX_DISCOVERY_CONTEXT_TURNS=4` turnos anteriores para elaborar consulta de discovery com limites adicionais de chars. **Não** é o cap global de `prior_context`.
- `_unproven_identifier_inputs` explicitamente não aceita `prior_turns` como provenance de identificador para invocação; exige validação live. Boa separação entre conversa e autoridade.
- `_admit_conversational_turn` recebe `prior_turns`; sua decisão pode reduzir acesso a owner; a qualidade da projeção de contexto e seus efeitos no routing exigem rastreamento.

## Documentação versus implementação (ainda não reconciliar lacunas por suposição)

| Tema | Previsto/documentado | Evidência de código | Status |
| --- | --- | --- | --- |
| Conversa mult turno | Planos 147/148 preservam continuidade governada e contexto sem authority | `prior_turns` em `attempt` e `ModelInvocationRequest` | PROVEN contract, E2E TO_INVENTORY |
| Reaproveitar observação anterior | 147: read != fact; fresh domain authority quando necessário | `_prior_result_turn`, `_prior_continuation_attempt` | PROVEN bounded mechanism |
| Contexto por estágio | 148: proposta deve receber objetivo/capability/evidence suficiente sem duplicar planner | `block_payload` específico e `instruction_content` mais histórico | PROVEN assembly, completeness TO_INVENTORY |
| Histórico completo de sessão | Nenhuma obrigação de full transcript sem bounds encontrada nestes dois planos | `prior_turns` já vem montado; source/truncation não auditados | TO_INVENTORY |
| Context window real e compactação | Sem decisão de novo context/memory engine nesses planos | nenhuma implementação específica confirmada nesta inspeção | TO_INVENTORY |
| Persistência/auth da sessão | Core/Keycloak/Domain ownership não deve ser contornado | front/API/storage/history ownership ainda não auditados | TO_INVENTORY |

## Mercado — padrões e tradeoffs

- **OpenAI Agents SDK Sessions**: histórico associado a session id é carregado automaticamente a cada turno; o armazenamento e trust boundary são responsabilidade do backend. https://openai.github.io/openai-agents-python/sessions/
- **OpenAI Agents API**: sessão preserva conversa e trabalho entre turnos; trabalho concluído exige observar status/outcome, não apenas session idle. https://developers.openai.com/api/docs/guides/agents-api/sessions
- **Anthropic Context Editing/Compaction**: preservar intenção, decisões relevantes e observações ao compactar contexto longo; remover resultados antigos que se tornaram ruído. https://platform.claude.com/docs/en/build-with-claude/context-editing e https://platform.claude.com/docs/en/build-with-claude/compaction
- **LangGraph short-term memory**: trim por tokens, sumarizar histórico e checkpoints persistentes; práticas de referência, **sem** importar LangGraph. https://github.com/langchain-ai/docs/blob/main/src/oss/langgraph/add-memory.mdx

**Interpretação proposta, não aprovada:** o alvo não é transmitir todas as mensagens a todos os estágios. É entregar *contexto mínimo suficiente* com identidade de sessão legitimamente autorizada, pedido atual, referência conversacional relevante, objetivo corrente, estado de execução, evidência tipada e restrições por stage, mantendo auditáveis os pontos em que houve perda/compactação. Preservar `transient research != session evidence != personal memory != organizational knowledge`. `cached history != source of truth`.

## Inventário residual necessário antes de qualquer design

A. Rastrear frontend MFE → request HTTP → autenticação/sessão → validação de `prior_turns` → origem (frontend, backend storage, ambos?) → truncation/ordering → `attempt`. Verificar caso troca de conversation id, subject e tenant; negar cross-session/cross-user leaks.

B. Localizar concrete adapter `ModelInvocationRequest.prior_context` → mensagens efetivas para Ollama/OpenAI-compatible, roles, limites, truncação, orçamento tokens, recusa a conteúdos maliciosos. Capturar probe sanitizado da montagem, nunca segredos ou conteúdo sensível.

C. Produzir **matriz real por estágio**: goal, admission, select_group, select_capability, native_assessment, foreign_selection, candidate_arguments, arguments, relevance, synthesis, recovery: `current_user_goal`, `prior_turns_count`, `prior_observation`, `business_subject`, `owner_catalog`, `owner_evidence`, `prior_failures`, `time/token_budget`, lineage/source-role. Identificar perdas por consumer, não por opinião.

D. Testes de pares de follow-ups (“desses, mostre outros três”, “qual foi o segundo?”, mudança de tópico, user sem autorização), conversa longa e interrupção; distinguir continuação por texto e fresh verification em Domain API.

E. Medir token/context window **real** por chamada, latência, truncation e sucessos/erros com o modelo local no SHA/config. Contexto maior sem seleção tende a aumentar custo, latência e ruído; a hipótese de enriquecimento precisa de eval controlada A/B **somente local**, com negatives e generalização.

**GATES:** `EXISTING_EQUIVALENT=TO_INVENTORY`, `REUSE_DECISION=TO_INVENTORY`; nenhuma nova engine, memória, store, planner, componente ou prompt de implementação antes de verificar as fontes superiores e os consumers efetivos. Plano 148 segue em execução independente; não mudar code no mesmo worktree.
