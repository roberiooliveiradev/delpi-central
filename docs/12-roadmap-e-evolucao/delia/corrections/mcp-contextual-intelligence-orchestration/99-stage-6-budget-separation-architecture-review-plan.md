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
