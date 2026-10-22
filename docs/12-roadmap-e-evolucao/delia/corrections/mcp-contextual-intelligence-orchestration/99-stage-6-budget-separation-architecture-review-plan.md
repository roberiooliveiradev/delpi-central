# DÉLIA — Etapa 6: revisão dos orçamentos por responsabilidade (adendo de homologação)

**Decisão de produto — 22/10/2026:** a homologação integrada da etapa 6 deve incluir uma revisão explícita da distribuição de tempo entre **decisões semânticas do LLM**, **execução operacional MCP/Domain APIs/AuthZ** e **composição/entrega**, antes de decidir ativação produtiva de retry. Esta decisão NÃO aprova novos valores de deadline, nem a retirada do limite global de segurança.

**Status:** PLANNED — investigation + architecture decision gate. **Next:** etapa 5.1 GPU Ollama em execução, então etapa 6. Não mudar arquitetura, flags ou limites durante esta anotação.

## Evidência factual e hipótese

- Browser prod pós-etapa 5, caso `qual o ultimo produto cadastrado no transforma+?`: painel por turno mostrou total de 30,0s, `select_capability` ~17,8s, `native_assessment` ~3,9s até timeout, TÉO selecionado e nenhuma consulta operacional comprovada. Isso demonstra consumo de tempo significativo em seleção semântica e estágio posterior sem orçamento suficiente. **Não prova** regressão da etapa 5 nem latência MCP/Domain; confirmar com traces correlacionados.
- O mecanismo de recuperação dev tem limites aprovados 2 tentativas / 60s total / 30s por tentativa, com `TurnDeadline.started_at` ancorado no início da interação. A última configuração produtiva reportada permanece 1 tentativa / recuperação OFF por gate de revogação de token; não confundir esses ambientes.
- Etapa 5 produziu dados reais por chamada de modelo (`duration_ms`, usage, attempt, stage) em ledger limitado por request. Reutilizá-los. Latência de MCP/Domain/Policy/CRI deve ser inventariada antes de assumir cobertura.

## Princípios e decisões que continuam congelados

1. Planner e LLM fazem interpretação de intenção, contexto, descoberta/seleção semântica e propostas tipadas; nada de regex, tabelas lexicais, aliases e branches por provider para acelerar decisão.
2. Core/Domain mantêm autoridade. MCP/A2A metadata não concede autorização. Writes seguem PREPARE/ACT, idempotência, audit e postcondition. O tempo das etapas não reduz segurança.
3. **Separate logical budgets != unlimited latency**: fases têm métricas, grants e reservas distintas sob um limite end-to-end governado; nunca transportar um timeout LLM como se fosse falha da API ou vice-versa.
4. O total 60s e a tentativa 30s são **decisões existentes**. Qualquer mudança em seu significado, valores, retry policy ou contratos de cancelamento/release exige `ARCHITECTURE_DECISION_REQUIRED` e aprovação explícita, não ajuste oportunista.
5. Testes locais com LLM real: apenas Ollama. GPU 5.1 deve produzir medições CPU/GPU, não consertar semântica por heurística. LLM externo somente usuário real em produção.

## Investigação bounded obrigatória na Etapa 6

### A. Inventário de ownership e contratos
Reancorar HEAD, Project Instructions/.cursor, authorities 16→50→17→49→51→52→21→20→25, arquitetura técnica, product spec, thematic specs, ledger, docs 88–99 e relatório 5.1. Rastrear `TurnDeadline`, Model Invocation, orchestration, Admission/Goal/Group/Capability/Arguments/Assessment/Synthesis, `ActivityEvent`, `turn_observability`, MCP adapter, Domain API, CRI e streaming. Por responsabilidade registrar `EXISTING_EQUIVALENT=YES|NO|TO_INVENTORY` e `REUSE_DECISION=REUSE|EXTEND|NEW`.

### B. Medir sem fabricar telemetria
Medir separadamente `model_call_duration` por estágio/modelo/attempt, `semantic_decision_elapsed` acumulado, `discovery`, `core_authz`, `domain_api/mcp_invoke_elapsed`, `composition_elapsed` (CRI deterministic e model synthesis distinguíveis), `transport_elapsed` e `total_turn_elapsed`. Instrumentar somente gaps observados no owner já existente, com proteção contra dados sensíveis, sem segundo ledger ou duplicação de telemetry. Registar `budget_allocated`, `budget_consumed`, `budget_remaining_at_stage_start/end`, timeout source e cancellation reason. As métricas técnicas exatas devem ser versionadas e seus consumers/contratos definidos.

### C. Caracterização e comparação
Usar casos `ola`, `qual o ultimo processo cadastrado?`, `qual o primeiro processo cadastrado no Transformômetro?`, `qual o ultimo produto cadastrado no transforma+?`, `qual a descrição 10080043?` e sequência `terminal bala → use o davi → o mcp davi`, em sessões limpas e multiturno conforme caso. Comparar modelos locais permitidos e resultados CPU/GPU da etapa 5.1; registrar p50/p95 somente se amostra suficiente, contagem de chamadas/tokens, stage-level and API-level latencies, erro de JSON, business outcome e segurança. Classificar backend full workflow em dev vs evidência produtiva real sem rodar bateria de chamadas pagas.

### D. Proposta de budgets por responsabilidade
Projetar **opções**, não alterar automaticamente: política de grants/reserva pré e pós-LLM, orçamento de raciocínio/seleção, timeout da invocação API, tempo de CRI/stream e limite global protetor. Especificar tradeoffs, fairness entre modelos, picos de carga, cancelamento/desconexão, custo, timeouts de proxy e relação com 2/60/30. Contrato antes de implementação: owner/consumer, boundaries, request/response/errors, backward compatibility, telemetry, release gate. Exigir evidência de que API válida não é privada de tempo por seletor lento e que timeout de API não é rotulado como LLM. **Se opções exigirem modificar contrato/limites congelados, STOP → ARCHITECTURE_DECISION_REQUIRED; registrar ADR e solicitar decisão da coordenação antes de implementar.**

### E. Segurança e ativação
Gate de revogação de credencial delegada intra-turno permanece OPEN (doc 94). Não habilitar `DELIA_MAX_GOVERNED_ATTEMPTS=2` em produção sem decisão de revogação e negativos reais. Homologar painel Contexto (abertura, seleção alternada e indicador azul sutil), eventos/Outcome consistentes, CRI por turno, DAVI e casos Ori/timeout como resíduos documentados. Não fazer deploy automático por ser etapa 6.

## Critérios de aceite da investigação

- Latências do LLM, da autoridade/execução MCP/Domain e da composição podem ser atribuídas sem mistura ou alegação causal sem trace.
- Capacidade efetiva e gaps dos mecanismos existentes inventariados, com propostas de mínimo diff e nenhuma duplicação.
- Matriz CPU/GPU, modelos, latência/tokens/outcome e cenários reproduzíveis com SHA/config.
- Diagnóstico claro para falta de orçamento após `select_capability` lento, com pelo menos testes determinísticos de orçamento e cenários de integração reais no dev.
- Recomendação explícita e governada sobre segregação de budgets, preservando 2/60/30 até aprovação formal de mudanças.
- Itens sem evidência ficam `PENDING/INCONCLUSIVE/TEST_NOT_RUN`, nunca `PASS`.

**Roadmap:** 1 Ollama → 2 R4 → 3 CRI prod → 4 contexto DAVI → 5 painel Contexto → 5.1 GPU local → **6 homologação integrada + decisão de budgets separados**. `I04_ACCEPTED` e avanço de fase só pelo processo canônico.

---
## Resultado da execução — Etapa 6 (SHA avaliado: f250d778e84943a9fc555548869324eb2b73113b)

### Matriz de homologação 1–5.1

| Etapa | Status | Evidência |
|---|---|---|
| 1 Ollama-only local | PASS | Todos os evals com DELIA_LLM_BASE_URL=http://ollama:11434/v1; 0 chamadas externas; egress guard intacto |
| 2 MCP auth + retomada governada | PASS (com gate R4 aberto) | Token exchange + resume autenticado verificados nas Etapas 2/4; revogação intra-turno segue OPEN |
| 3 CRI efetivo | PASS | response_mode=cri, composition_mode=model no wire serializado (p5 live eval, GPU) |
| 4 Inteligência contextual | PASS-WITH-RESIDUAL | Multiturn `terminal bala → use o davi → o mcp davi` com seleção semântica e invokes reais; residual: invalid_structured_output e miss-seleção ocasional do 3B (list_playlists p/ consulta de processo → NON_GROUNDED honesto) |
| 5 Painel Contexto | PASS backend+frontend; browser QA TEST_NOT_RUN (portal serve build MFE anterior) | 14/14 testes vitest + tsc limpo no worktree |
| 5.1 GPU Ollama | PASS-WITH-EVIDENCE | doc 97: offload 100%, 16.6→47.4 tok/s, timeouts de estágio 11→0 |

### Diagnóstico de orçamento — evidência de causalidade

A extensão de atribuição (instrumentação bounded nos owners canônicos turn_observability, orchestration, handle_interactive_turn) tornou mensurável a separação A/B/C exigida. Wire real (GPU, qwen2.5:3b):

- `qual o último processo cadastrado?`: elapsed_ms = model 7124 / operational 198 / composition 0 / other 913 — **o LLM consumiu ~86% do turno; a execução operacional real consumiu 198 ms** (list_playlists, completed). Isso confirma com trace a hipótese do problema observado em produção: o orçamento é consumido pelas decisões semânticas, não pela capability nem pela API.
- budget_remaining_ms por estágio (escada observada): 29999 → 28263 (admission) → 27576 (select_group) → 25192 (select_capability) → 24116 (native_assessment) → 23757 (arguments) → 22686 (arguments 2). Cada estágio registra o remanescente real do deadline — starvation agora é diretamente visível sem telemetria nova.
- Em CPU (5.1) a mesma forma escalava: select_capability ~17.8 s + native_assessment ~3.9 s ⇒ tentativa de 30 s expirava antes da invocação — API_EXECUTION_STARVATION=CONFIRMED com evidência.

### Campos aditivos no contrato de observabilidade

Aditivos, bounded, presentation-only (parser frontend allowlisted, descarta desconhecidos):

- calls[].budget_remaining_ms — remanescente do deadline no fim de cada estágio de modelo.
- operational_calls[] — {capability, duration_ms, finish_status} por invocação de capability (≤8).
- elapsed_ms = {model, operational, composition, other} — decomposição das responsabilidades A/B/C.
- timeout_source = model|provider|budget|null — classifica o encerramento sem confundir LLM com Domain API.
- Teste determinístico novo: deadline esgotado por estágio lento ⇒ timeout_source=budget, sem atribuir à fonte.

### Alternativas arquiteturais (§D) — comparação

| Opção | Descrição | Benefício | Risco | Compat. | Decisão |
|---|---|---|---|---|---|
| A. Budgets lógicos separados sob deadline global | sub-limits A/B/C dentro dos 60 s | previsibilidade | cortes prematuros em modelos lentos; dois regimes p/ manter | quebra semântica do deadline | REQUIRED |
| B. Reserva explícita p/ execução operacional | garantir X ms p/ invoke+pós-condição após seleção | elimina starvation | precisa estimar reserva; estágio lento vira falha honesta mais cedo | muda comportamento de timeout | REQUIRED |
| C. Grant por estágio | cada estágio recebe teto | controle fino | complexidade de tuning; unidades artificiais | alto churn | REQUIRED |
| D. Degradação honesta quando seleção excede | seleção lenta ⇒ terminal budget honesto em vez de invocar sem folga | simples, já evidenciado | UX de timeout permanece | compatível | REQUIRED (compõe B) |
| E. Status quo + observabilidade (implementado) | só medir | zero risco | não resolve starvation | total | DONE — instrumentação apenas |

Recomendação da investigação: **B+D** — reserva operacional mínima após seleção + encerramento honesto quando a reserva não pode ser garantida. Qualquer mudança em valores/significado de 2/60/30, retry policy ou cancelamento ⇒ ARCHITECTURE_DECISION_REQUIRED — nenhuma alterada nesta etapa.

### Gates e estado de release

- RECOVERY_PRODUCTION=OFF — inalterado; gate de revogação R4 segue OPEN ⇒ RECOVERY_PRODUCTION_ACTIVATION=BLOCKED.
- Limites 2/60/30 preservados; nenhum contrato de cancelamento/deadline alterado.
- Segurança: nenhum campo novo expõe prompt, payload, token ou chain-of-thought; wire forbidden-scan limpo nos evals.
- Frontend: READY_WITH_RESIDUAL (QA browser pendente de build do portal).
- Backend: READY_WITH_RESIDUAL (miss-seleção semântica do 3B documentada; não autoriza heurística).

### Resíduos materiais

- invalid_structured_output do modelo ≤3B persiste (GPU não corrige — medido).
- Seleção semântica imperfeita observada (list_playlists para consulta de processo) — NON_GROUNDED honesto, sem fabricação.
- Browser QA do painel: TEST_NOT_RUN até portal servir build atual do MFE.
- WSL dropa intermitentemente sob saturação (self-healing).
