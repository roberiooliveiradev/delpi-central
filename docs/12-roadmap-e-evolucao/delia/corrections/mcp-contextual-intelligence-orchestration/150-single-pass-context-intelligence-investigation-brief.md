# 150 — DÉLIA: investigação única e conclusiva de Context Intelligence

**TASK_ID:** `DELIA-CONTEXT-INTELLIGENCE-SINGLE-PASS-CANONICAL-INVESTIGATION-01`  
**MODE:** READ-ONLY INVENTORY → END-TO-END TRACE → THREE-WAY COMPARISON → GAP ANALYSIS → IMPLEMENTATION DECISION PACKAGE → ONE FINAL REPORT.  
**Baseline HEAD na emissão:** `c70f9ed9598cdb106ee88dd4693b7b626d4cc1d0`. Reancorar no HEAD real no início e ao concluir; não congelar falsa versão se main avançar.  
**ESCOPO:** somente investigação; sem alterar código, contrato, instruction resources, modelo, runtime, infraestrutura ou deploy. Entregar uma investigação completa, não uma sequência de diagnósticos/iterações. Respeitar trabalho concorrente no Plano 148.

## Objetivo e obrigação de resposta única

Em uma só execução, provar **como o contexto é composto, validado, selecionado, transportado, reduzido, consumido, preservado, recuperado e descartado** desde o Frontend MFE até o LLM e entre estágios de uma mesma interação. Comparar (A) documentação canônica, (B) implementação/testes no HEAD e (C) práticas atuais do mercado, para entregar **um pacote de decisões de implementação** à coordenação. Não implementar nem fazer rework nesta task. Não encerrar após descobrir uma lacuna isolada. Quando acesso, contrato ou ambiente não permitir uma verificação, registrar `TO_INVENTORY` com prova de tentativa e impacto, não presumir ausência. **A investigação só está completa se cobrir todos os itens seguintes numa única resposta.**

## 0 — Reancoragem e inventário de autoridade

HEAD, origin/main, status, worktrees, autor/commit, concorrência; Project Instructions, `.cursor`, `AGENTS.md`; fontes 16 → 50 → 17 → 49 → 51 → 52 → 21 → 20 → 25; arquitetura técnica; product spec; specs temáticas de Session/Conversation/Context/Model Invocation/CRI/Evidence/Personal Memory; ADRs, CP/RQ, Ledger; planos 125, 129, 130, 146, 147, 148, 149 e reports aplicáveis. Registrar localização, prioridade, SHA, cláusula e diferença prevista/implementada. Não usar chat como autoridade.

## 1 — Jornada completa do histórico conversacional (por código e contrato)

Rastrear **Frontend DÉLIA e Portal** → transport (HTTP/NDJSON) → endpoint API → identidade/sessão → conversa e mensagens armazenadas, se houver → carregamento de históricos → validação e limites → use-case → orchestrator `attempt(prior_turns)` → `ModelInvocationRequest.prior_context` → model adapter → serialização final de roles/user/system/tool para Ollama local → resposta/persistência. Identificar **quem produz e é owner do histórico** (frontend cliente ou backend; nunca presumir), como troca de `conversation_id`, `session_id`, usuário, tenant e autorização protege fronteira. Demonstrar o que ocorre em refresh/reconnect/new conversation, multi-tab, sessão expirada, cancelamento, streaming, memória e mensagens de falha.

Evidência obrigatória: request/response schemas, funções + arquivos + linhas, limites `max_turns/max_chars/max_tokens`, truncação (prioridade do que cai), ordering, roles, epistemic classes, se assistant/result entram, persistência real, e prova do payload **efetivamente enviado** ao LLM (probe local sanitizado ou testes do adapter). Não inferir transmissão final só por `prior_context` no DTO.

## 2 — Contexto dentro de uma única interação (stage-by-stage)

Mapear TODAS as decisões/LLM calls reais e variantes: `interaction_admission`, `turn_goal`, `select_group`, `select_capability`, `native_assessment`, `foreign_selection`, discovery→execute, `candidate_arguments`, `arguments`, `goal_evidence_relevance`, `clarification`, `grounded_synthesis`, recovery, timeout/resume e CRI-on/off. Para cada stage registrar: owner/função, source of truth, instruction id/version, payload atual, `current_user_goal`, `prior_turns`, `prior_observation`, `workspace_context`, `business_subject`, catálogo (live? selected? dynamic?), schema, prior attempts/feedback, owner evidence e source roles, cardinalidade, budgets, projected bytes/tokens, truncamento, status e consumers. Registrar quando `goal` é calculado, quando é recalculado, onde se perde/é contradito e se o modelo vê **por que o último resultado falhou**.

Distinguir: (a) entre turnos da mesma conversa, (b) entre estágios dentro do mesmo turno, (c) entre reexecuções por timeout, (d) sessão, (e) Personal Memory e organizational knowledge. Não misturar essas responsabilidades nem tratar história de chat como FACT/AuthZ.

## 3 — Validade de contexto e proveniência (security-first)

Classificar cada campo `trusted/UNTRUSTED`, authority owner, freshness, provenance/source_role, privacy/tenant, AuthZ, capability constraints, token/id protections, user-controlled fields, workspace context, MCP tool metadata/tool results, prompt injection e candidate-token. Verificar se histórico transcrito pode vazar secrets ou ser usado para fabricar fact, permissões ou identificadores; preservar `prior_turns NOT provenance`, `read != write`, `simulate != apply`, `PREPARE != ACT`, `MCP result != FACT`.

Verificar separação **business evidence vs. control-plane metadata** e casos de falsa pertinência (VISTA routes/operationId como produtos) como input contextual do stage, sem corrigir nesta task.

## 4 — Conteúdo, seleção e orçamento

Inventariar context-window real configurada (Ollama model + server `num_ctx`, GPU offload, quantização), instruction bytes/tokens, conversation excerpt, catalog, evidence, structured schemas, retry payloads, model response format, stage caps, global turn budget. Comparar **estimativa vs uso real** e distinguir duração prefill/generation, truncamento no adapter/provedor, `invalid_structured_output`, timeout, fallbacks, input-too-long. Confirmar o comportamento com modelo local autorizado, sem instalar modelo e sem usar modelos externos; se ambiente não estiver acessível, documentar `TEST_NOT_RUN`.

Mapear `MAX_DISCOVERY_CONTEXT_TURNS=4`, `MAX_PRIOR_EXCERPTS`, limites da invocação, memória/summarization se existente. Inventariar política de relevância/recência/compaction; ver se é real e testes; nunca assumir que janela grande equivale a contexto útil.

## 5 — Testes de continuidade e generalização

Apenas READ/probes não invasivos e testes existentes; quando viável, testes locais de caracterização **sem editar código**. Casos: “desses, mostre outros três”, “qual foi o segundo?”, “esse material”, mudança de assunto, follow-up após erro MCP, conversa longa e resumo/compactação, duas sessões em paralelo, usuário diferente, troca tenant, histórico adulterado, prompt injection, referência a id vindo apenas de resposta anterior, pending write, cancel/resume; múltiplas fontes e modelos local-only. Diferenciar factual prior answer e verificação live. Guardar resultados sanitizados + SHA/config/correlation. Não executar ACT nem alterações de negócio.

## 6 — Mercado: pesquisa externa atual e comparação

Pesquisar documentação oficial com links e data de consulta — OpenAI (sessions, conversation state, tool orchestration, compaction), Anthropic (context engineering, context editing/compaction, tool usage), LangGraph (short-term memory, trim/summarize/checkpoint), Microsoft (agent memory, evals, grounding), MCP specification (tool and trust boundaries). Analisar **padrão/problema/benefício/custo/limites/security e adequação DÉLIA**; não propor instalar SDK/framework por moda; identificar equivalentes já implementados, contratos faltantes e boas práticas transferíveis. Separar padrões documentados de opinião e do runtime do próprio ChatGPT.

## 7 — Cruzamento triplo para CADA capability de contexto

Tabela obrigatória: `DIMENSION | AUTHORITY + CLAUSE | DOCUMENTED TARGET (PLANNED/TARGET) | HEAD CODE FILE:LINE | RUNTIME TEST SHA/CONFIG | MARKET PATTERN + URL | CURRENT STATUS PROVEN/TO_INVENTORY | GAP/RISK | EXISTING_EQUIVALENT | REUSE_DECISION | MINIMAL PROPOSED CHANGE | OWNER | CP/RQ | ACCEPTANCE TEST`.

Dimensões mínimas: session identity, authenticated history loading, message order, roles, serialization, conversation boundary, summary/compaction, relevant excerpt selection, schema/source projection, stage context, goal persistence, business subject, failed-attempt feedback, live capability catalog, evidence lineage, context budget and token accounting, timeout resume/cancel, cross-model parity, provider neutrality, privacy, prompt injection, AuthZ and safe re-query.

**Não reconciliar silentemente documentação × código.** Divergência documental é `DRIFT` a classificar, não permissão de redesenho.

## 8 — Entregas finais numa única resposta

1. **Executive factual diagnosis:** resposta inequívoca para “o modelo recebe toda a conversa, parte ou só turno atual?”, em quais stages e sob quais limites, separando contrato de transporte e payload comprovado.
2. **Mapas de sequência** Frontend→API→storage→orchestrator→adapter→LLM e dentro do turno, com links de código.
3. **Matriz 3-way completa** e lacunas ordenadas por causa/risco, sem confundir ausência de evidência com ausência de funcionalidade.
4. **Inventário reuse-before-design** por owner/boundary/consumer, incluindo `EXISTING_EQUIVALENT` e `REUSE_DECISION`.
5. **Matriz de mercado** com URLs, diferenças de tradeoff; não instalar frameworks.
6. **Plano fechado para próxima interação**, em work packages **ordenados**: contexto de sessão/serialização; contexto de objetivo e evidências por stage; seleção/compaction/budgets; segurança; generalização/medição. Para cada WP: arquivos, contrato, diff estimado por fronteira (não código), RED tests, pass/fail, dependências, riscos, critérios release e `NEXT`.
7. **Decision register**: o que pode ser aprovado agora, o que depende de contrato/authority/infra, o que é inadmissível e o que já é implementado.
8. **Exatamente um report final** com `BASE_SHA`, `FINAL_HEAD`, `AUTHORITIES`, `FILES_INSPECTED`, `STAGES_MAPPED`, `CONTEXT_ORIGIN`, `SESSION_BOUNDARY`, `MODEL_WIRE_PAYLOAD`, `TRUNCATION`, `TOKEN_USE`, `TESTS`, `MARKET_SOURCES`, `GAPS`, `REUSE_DECISION`, `DECISIONS_REQUIRED`, `NEXT_WP`, `EXECUTION_DRIFT`. Não pedir repetidos prompts de diagnóstico. Persistir documento de evidências e plano da próxima fase no GitHub + Ledger com commit/push ff-only, se autorizado pelas regras canônicas, sem código.

## Normas de execução

Esta task é **single-pass investigation**, não implementação: proibir editar `.py`, `.ts`, instruction resources, adapters, migrations, envs, prompt templates e deploy; não trocar modelos; não usar LLM externo; não modificar schema/routing. Não fazer redesign silencioso, não criar abstrações nem contratos especulativos; quando uma fonte não existir, tentar os caminhos legítimos, registrar e seguir ao próximo item. Prova documental não é runtime. `0 search results != absence`. Execução sem credenciais ou ambiente = `TEST_NOT_RUN`, não `PASS`. Não devolver report parcial; uma única entrega completa, com limitações explícitas, é obrigatória.

**Resultado esperado:** coordenação recebe uma investigação completa e um plano de implementação suficientemente preciso para emitir o próximo prompt diretamente, sem pedir outra rodada genérica de inventário.
