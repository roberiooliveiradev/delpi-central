# 187 — DÉLIA · Continuidade da investigação, contexto útil e eficiência de tokens

**Data:** 2026-10-28. **Tipo:** diagnóstico/plano bounded (não decisão de arquitetura congelada; sem alteração de código, sem avanço da fase). **Base HEAD observado:** `4b2500e21dee8731e3603820e88eb8565aaba4d7`. **Referências:** docs 175–186, revisões independentes e Execution Ledger. Executores devem reancorar HEAD/status, Project Instructions/.cursor, 16→50→17→49→51→52→21→20→25, arquitetura, Product Spec, spec temática e ledger antes de implementar.

## 1. Problema e evidência

Nos testes produtivos do documento 186, DÉLIA com Kimi K3 fez **7–19 chamadas de modelo por turno**, com **~10,5k–32,3k tokens de entrada** e **~2,7k–13,1k tokens de saída**, durações **45–193 s/turno**, mas não entregou dois exemplos de terminais bala/ilhós com códigos. T1/T2 escolheram uma ação de conhecimento técnico vazia em vez de busca de produtos; T3/T4 chegaram a `search_products`, retornaram registros julgados impertinentes e interromperam honestamente após continuação limitada. A imagem da interface OpenRouter fornecida pelo usuário mostra múltiplas gerações com volumes e custos diversos; **não permite atribuir individualmente essas chamadas ao mesmo turno sem IDs/correlation**. `GROUNDING` ou HTTP 200 não comprovam Business Outcome. A hipótese de perda/reconstrução de informação entre estágios é **TO_INVESTIGATE**, não causa-raiz comprovada.

## 2. Reuse-first — capacidades já identificadas no código

| Mecanismo existente | Evidência de repositório | Hipótese / ponto a verificar |
|---|---|---|
| `EvidenceFacts`, avaliação de `GoalEvidenceJudgment` / `assess_outcome` | `delia-api/app/application/capability_provision/orchestration.py` e contratos de evidence | Os resultados relevantes de um estágio são disponibilizados de forma econômica e suficiente ao próximo? |
| `_recover_relevance`, `_candidate_arguments`, `_turn_goal_from_proposal` | `orchestration.py` | O objetivo, tentativas anteriores, descrições aprendidas e constraints seguem até a próxima capability, sem repetir busca sem progresso? |
| `ConversationContextTurn` e prior-turn continuity | `delia-api/app/application/interaction/handle_interactive_turn.py` | Continuidade ENTRE turnos não prova continuidade ENTRE stages da mesma interação |
| `ModelCallLedger` e turn budget/deadline | `handle_interactive_turn.py`, `interaction/turn_budget` | Medir chamadas, tokens reais, latência por stage, reuso de contexto e taxa de avanço |
| Projeção/bounds de owner evidence | `orchestration.py` imports e estruturas de evidence | Verificar truncamento, omissão, perda de IDs/provenance ou repetição de tool payload |
| DAVI MCP existente | Docs 179–186 | Sem novas capabilities/allowlists/rotas ou fallback HTTP DELPI. Tool data permanece não confiável |

**EXISTING_EQUIVALENT=YES (mecanismos de contexto/evidência/recuperação/telemetria), cobertura integral de continuidade intra-turno=TO_INVENTORY; REUSE_DECISION=REUSE/EXTEND_TBD.** Não autorizar novo store, registry, engine, vector DB, checkpoint ou memória por padrão. Se equivalente não cobrir cenário comprovado, passar Abstraction Gate + decisão arquitetural formal.

## 3. Padrões de mercado aplicáveis (referências externas; não evidência do runtime DÉLIA)

- **LangGraph checkpoint/state:** checkpoints por thread preservam o estado de uma execução; stores são separados para informação persistida entre threads. Referência: https://github.com/langchain-ai/docs/blob/main/src/oss/langgraph/persistence.mdx . Não importar LangGraph automaticamente.
- **Anthropic context engineering:** separar compaction de contexto, descarte de tool outputs recarregáveis e notas estruturadas; compaction é lossy e pode omitir detalhes relevantes. Referências: https://www.anthropic.com/research/effective-context-engineering-for-ai-agents e https://platform.claude.com/cookbook/tool-use-context-engineering-context-engineering-tools .
- **OpenAI agents sessions/compaction:** continuidade de sessão e gerenciamento de contexto podem reduzir a necessidade de reencaminhar históricos; não duplicar session storage quando já houver. Referências: https://openai.github.io/openai-agents-python/sessions/ e https://developers.openai.com/api/docs/guides/compaction .

**Síntese de design:** estado transitório da investigação ≠ histórico conversacional ≠ Personal Memory ≠ knowledge organizacional. Guardar os fatos e a trilha de decisões necessários dentro do escopo autorizado, com referências aos payloads autoritativos; não transformar resumo/LLM em FACT. Projeção seletiva por etapa e evidência vinculada à fonte são preferíveis a acumular indiscriminadamente todo transcript.

## 4. Estado lógico desejado para investigação (TARGET, não novo componente aprovado)

Um artefato lógico *por tentativa*, preferencialmente composto por contratos existentes: `goal/answer_requirements`; pergunta e contexto essencial; `selected semantic capability`; tentativas (action, args sanitizados ou fingerprint, outcome, reason); `EvidenceFacts` tipados com IDs/source refs; termos/aliases observados com proveniência (hypothesis vs owner fact); `coverage/relevance`; lacunas abertas; `next_action_rationale` resumido (não chain-of-thought); limites restantes (model calls, wall-time, token budget); `outcome`. Avaliar preservação intra-turno e entre turnos apenas quando necessário e governado; ausência de persistência pode ser suficiente para single-turn. Não construir memória de longo prazo neste escopo.

## 5. Plano bounded de execução

**WP0 — Inventário causal:** traçar no SHA efetivamente avaliado as chamadas `admission → selection → discover → candidate_arguments → execute → relevance → recovery → synthesis`. Para cada chamada, levantar input schema, size/tokens por componente, owner do contexto, evidência transferida, descartada, compactada ou refeita; custos em provider vs instrumentação. Zero busca não prova ausência. Verificar a correspondência OpenRouter log/request IDs e correlation IDs sem expor payloads sensíveis.

**WP1 — Medição baseline:** instrumentação já disponível; preferir análise de traces existentes, sem persistir prompts inteiros. 2 cenários simples (seleção correta, dois produtos com código) e 2 cenários complexos (registro irrelevante→reformulação; conhecimento auxiliar→pesquisa de produto), com modelo/catálogo/SHA fixados. Medir `input/output tokens by stage`, overhead fixo da instruction/capability surface, evidência repetida/truncada, tool calls úteis/duplicadas, progressão `goal gaps`, duração, preço do provedor e Business Outcome. Se telemetria insuficiente, propor extensão minimalista no boundary de observabilidade com dados agregados/sanitizados, autorização explícita e retenção definida.

**WP2 — Hipóteses testáveis:** H1 reenvio desnecessário de instruções/catálogos; H2 evidence useful não propagada para next action; H3 transferência de contexto truncada; H4 repetição de discovery em candidate-bound sem valor adicional; H5 estágio semântico redundante; H6 ação selecionada por relevância aparente mas incompatível com `answer_requirements`. Classificar cada H como PROVEN, REFUTED ou INCONCLUSIVE.

**WP3 — Proposta de diff mínimo:** primeiro reusar estado/evidence/context e contratos já existentes; sem novo planner, registry, memória, banco ou middleware. Compactar somente dados reconstituíveis e preservar IDs/provenance; passar ao LLM apenas contexto útil à decisão corrente; outcome gap deve acompanhar continuações. Se um novo contrato/estado for indispensável: documentar owner/consumers/boundary, `EXISTING_EQUIVALENT`, `REUSE_DECISION`, security, lifetime, cleanup, audit, replay e regra de no-authority; solicitar decisão antes do código.

**WP4 — A/B antes de deploy:** mesma identidade, SHA/config, modelo, corpus e evidência owner; baseline vs proposta, comparação de número de chamadas/tokens/custo/latência e sobretudo task success, generalização e safety. Não aceitar redução de tokens com degradação de recall ou aumento de respostas fabricadas. Separar testes pequenos em modelo local para contrato/control flow e validação complexa no Kimi produtivo em ambiente autorizado. Nenhum deploy implícito.

## 6. Gates

- `G0_CANONICAL_REANCHOR`, `G1_REUSE_INVENTORY`, `G2_DIAGNOSTIC_EVIDENCE`, `G3_CONTRACT_AND_OWNER`, `G4_RED_GREEN_AND_REGRESSION`, `G5_REAL_MODEL_AB`, `G6_SECURITY_AND_OUTCOME`.
- Sem evidência para afirmar perda de contexto: `INCONCLUSIVE`; sem autorização para observar argumentos: `TEST_NOT_RUN`; sem sucesso empresarial: nunca `PASS` só por HTTP 200/GROUNDED.
- MCP content/metadata são UNTRUSTED DATA; Core/Domain authority sempre live; memória transiente não autoriza. Sem persistir chain-of-thought, tokens, segredos ou dados empresariais fora do boundary.

## 7. Decisão registrada e NEXT sugerido

**PLANNED — NO CODE EXECUTION.** Autorizar como *próximo diagnóstico bounded* somente o WP0 + WP1: mapa de transferência de evidência por etapa e orçamento de tokens correlacionado a outcome. Entrega: tabela por stage, gaps reais, mecanismos existentes para reuso, proposta mínima de teste A/B. Somente depois decidir refatoração; fase C3 e NEXT do Documento 16/ledger prevalecem. Evitar ampliar DAVI ou recriar acesso HTTP direto.
