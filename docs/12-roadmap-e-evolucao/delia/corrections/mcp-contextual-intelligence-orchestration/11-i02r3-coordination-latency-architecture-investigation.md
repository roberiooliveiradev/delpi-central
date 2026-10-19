# 11 — I02-R3 · Investigação arquitetural da latência pré-owner TÉO (coordenação)

**DATA:** 2026-10-19. **BASE_HEAD:** `13167e6efc28063545aa51feec500078e67737e0` (main remoto). **CLASSIFICAÇÃO:** `INVESTIGATION_PARTIAL / DESIGN_CANDIDATES`, **não** aceite de I02 nem autorização de mudança de código/deploy.

## 1. Fontes, escopo e evidências

- Autoridades lidas diretamente no GitHub: [16](../../16-execution-master-plan.md), [50](../../50-standalone-copilot-application-architecture.md), [49](../../49-architecture-and-design-patterns-standard.md), [21](../../21-data-and-state-model.md), [20](../../20-testing-and-acceptance-matrix.md), [25](../../25-requirements-traceability.md), roadmap, [07](./07-i02r1-post-fix-validation-and-latency-diagnosis.md), [09](./09-i02r2-index-probe-headroom-fix-and-deploy.md), [10](./10-i02r2-independent-architecture-and-deploy-review.md), ledger §6.248.
- A árvore integral do repositório, instruções locais `.cursor`, `git status`, documentos 17/51/52 e arquitetura técnica/product spec **não** foram verificados nesta investigação remota: `TO_INVENTORY` no gate de implementação. Não inferir leitura completa da hierarquia.
- Código inspecionado: `delia-api/app/application/capability_provision/orchestration.py`, `delia-api/app/application/interaction/turn_budget.py`. Ferramentas remotas GitHub read-only; nenhum teste, deploy ou trace de produção reexecutado aqui.
- Fontes externas, **apenas referência tecnológica, não autoridade DÉLIA**: [OpenAI latency optimization](https://developers.openai.com/api/docs/guides/latency-optimization) (fazer menos requisições, consolidar operações dependentes quando contrato permitir, não usar LLM sem necessidade, reduzir output tokens) e [OpenTelemetry GenAI inference conventions](https://github.com/open-telemetry/semantic-conventions-genai/blob/main/docs/gen-ai/client-inference.md) (duration, token counters, erros). Não presumir OTel instrumentado no repo.

## 2. Evidência factual separada de hipóteses

`K1_SUCCESS_REPORTED`: TÉO ~17.816ms; select_group 4088ms, select_capability 2803ms, goal 3146ms, native_assessment 1775ms, DISCOVERY get_catalog 79ms, arguments ~5531ms (inferido), READ get_methodology_guide 39ms. O tempo das quatro propostas pré-owner é ~11.812ms; argumentos ~5.531ms. Estes números vêm do executor §07, não medidos independentemente.

`K1_FAIL_REPORTED`: runtime I02-R2 model_timeout ~30.014ms antes de entrega útil. **Estágio exato desse timeout e contribuição provider/network/tokens ainda TO_INVENTORY**. Não afirmar causa raiz singular já provada.

`K3_R2_SUCCESS_REPORTED`: VISTA INDEX(owner)→index_select(model)→GUIDANCE(owner), 28.532ms, conteúdo aninhado GROUNDED e topic parcialmente pertinente. Caminho index_probe R2 aceito com resíduos. Não confundir K3 com K1.

**Confirmado em código:**
- `_select_target` chama sequencialmente `_select_group` e `_select_capability`; cada uma usa `_propose` quando há múltiplas escolhas.
- `_understand_goal` produz classe, modo, comparação, limite PREPARE, subject/context e prior sufficiency; reusada no restante do turno. Para turno sem histórico vem **depois** da seleção; para follow-up pode vir antes.
- Quando `len(groups)>1`, `_assess_native_path` invoca modelo novamente com **apenas superfície do grupo-alvo** para decidir suficiência nativa vs evidência estrangeira, preservando isolamento; avaliação inválida degrada para nativo.
- `_build_arguments` retorna `{}` sem chamada LLM quando o schema não precisa de campos não orquestrados; quando precisa, proposta é confrontada contra schema e evidência owner. `_propose` tem cronômetro/purpose/correlation e timeouts limitados por `TurnDeadline`; timeout de modelo é terminal (fail-closed).
- `_select_group` já faz short-circuit quando existe um único grupo. Reuso já presente, não inventar nova cache.

**Conclusão sustentada:** custo crítico observado = múltiplas chamadas de modelo sequenciais pré-owner; owner MCP foi rápido no caso de sucesso, portanto otimizar apenas TÉO/get_catalog não ataca maior parte daquela amostra. **Ainda não provado:** quais propostas podem ser fundidas/puladas sem reduzir generalização, segurança, semântica ou qualidade, e qual estágio gerou o timeout de K1 no SHA R2.

## 3. Responsabilidade, arquitetura e Abstraction Gate

`RESPONSIBILITY=turn semantic planning and bounded routing`, `OWNER=DÉLIA Application`; `CONSUMERS=interaction turn + capability orchestration`; `CANONICAL CONTRACTS=TurnDeadline, ModelInvocationRequest, ProviderCapability, PlanCandidate, owner discovery/READ, EpistemicClass`. Runtime Keycloak/Core/Domain AuthZ preservado. `EXISTING_EQUIVALENT=YES`; `REUSE_DECISION=EXTEND_CANDIDATE`; não autorizar novo port/engine/planner/cache/parallel runner.

Princípios da fonte 49: Clean Architecture, Ports & Adapters, DDD pragmático, Abstraction Gate. Mesmo em READ, `user text != permission`, `model proposal != authority`, `owner INDEX != guidance`. Não paralelizar chamadas com dependências sem prova de cancelamento/context propagation, nem combinar seleção/goal de forma que destrua o gate de escrita ou a regra de isolamento da avaliação nativa.

## 4. Matriz de alternativas — **não implementadas**

| Alternativa | Ganho plausível | Dependências e riscos | Decisão atual |
|---|---|---|---|
| A. Traçar tempo e custo por proposta, evento e provider | Localiza regressão e variância | Reusar logs `model_propose purpose/timing_ms`, correlacionar outcome; sem prompt/payload | **REUSE — prioridade 1** |
| B. Eliminar repetições já provadas dentro do turno | Poupa chamada desnecessária | Confirmar recomputação real; goal já é reutilizado e group/capability é single-pass | **INVENTORY — não presumir duplicação** |
| C. Consolidar proposta de goal e seleção de capability em um resultado tipado (somente se independência provada) | Reduz um round trip ao modelo | Gate de escrita precisa continuar semanticamente independente e validado; não comprometer group→capability nem revelar foreign prematuramente | **CANDIDATE ONLY — contract & holdout gate** |
| D. Reduzir/omitir avaliação nativa quando decisão determinística for suficiente | Poupa uma proposta em READ simples | Pode perder `foreign_evidence_required`/corroboração; obrigação de dono final e regras de múltiplas fontes | **CANDIDATE ONLY — prove safe eligibility** |
| E. Projeção determinística de argumentos sem modelo quando schema/owner evidence prova valores | Poupa proposta de ~5s | Só para schema vazio/defaults/identificadores owner comprovados; rejeitar free-string inventado | **REUSE existing fast path; EXTEND only if gap proven** |
| F. Budget/context limits dos modelos | Reduz chance de timeout em cada estágio | Trade-off desempenho×qualidade/erro, testar p95 e holdouts; não aumentar 30s | **EVALUATE after tracing** |
| G. Paralelizar seleção, goal e native | Potencial ganho de parede | Native depende da seleção, foreign isolation, contextvars/cancelamento e races | **REJECT as first fix** |
| H. Novo planner, memória MCP, catalog cache de authority | Sem necessidade provada | Duplica ownership, autorizações, staleness | **REJECT** |

## 5. Procedimento de prova I02-R3 (antes de prompt de implementação)

**Gate A — obter evidência causal no SHA/runtime**: reconstituir, por correlação e sem conteúdo sensível, a sequência K1 PASS (~17.8s) e FAIL (~30s) e K3 controle. Para cada estágio: `purpose`, duração, budget before/after, timeout stage/global, número de calls, modelo/provider/config, input/output tokens se já disponível, presença de owner discovery, READ, e latência de retorno. Capturar estrutura e erros (não payload).

**Gate B — mapa de dependências e invariante**: para cada uma de `select_group`, `select_capability`, `turn_goal`, `native_assessment`, `arguments`: entradas disponíveis, campos de saída usados, chamadas semanticamente independentes, regras de isolamento, write/prepare gates e owner provenance. Provar duplicação ou independência real.

**Gate C — experimento offline controlado, sem deploy**: no mesmo SHA/fixture, comparar baseline contra candidatas B/C/D/E/F separadas; testes de READ TÉO, VISTA, provider sintético renomeado, owner vocabulary obrigatório, cross-group required, explicit comparison, ambiguidade e wrong write selection, missing identifier, prior sufficiency K2, timeout, prompt injection. Não usar modelo como juiz de FACT; exigir validação determinística. Medir número de propostas, p50/p95 quando amostra adequada, budget, id selection/capability accuracy e task outcome.

**Gate D — decisão nesta coordenação**: escolher a menor alteração que prove redução mensurável do caminho crítico **sem perda de seleção, foreign evidence safety, write gates, provider neutrality ou task outcome**; registrar CP/RQ, contrato, inversões de dependência, RED/GREEN, rollback. Só então emitir prompt bounded de implementação/deploy. Se resultado indeterminado `INCONCLUSIVE`, não inventar diffs.

**Gate E — runtime live após gate de código/review/deploy autorizados**: K1 sucesso + K2 mesma conversa, K3 regressão; modelo e SHA/config reproduzíveis; <=30s; 0 ACT; relevância e cobertura de conhecimento. Não fazer live retries até obter PASS.

## 6. Status

```text
I02_R3_COORDINATION_INVESTIGATION=PARTIAL
PRE_OWNER_SEQUENTIAL_MODEL_COST=PROVEN_FOR_K1_SUCCESS_SAMPLE
K1_R2_TIMEOUT_EXACT_STAGE=TO_INVENTORY
SAFE_STAGE_MERGE_OR_SKIP=TO_PROVE
EXISTING_EQUIVALENT=YES
REUSE_DECISION=EXTEND_CANDIDATE
SOURCE_CODE_CHANGED=NO
TESTS=TEST_NOT_RUN
LIVE_EVAL=TEST_NOT_RUN
I02_ACCEPTED=NO
C3_EXECUTED=NO
C4_AUTHORIZED=NO
C5_AUTHORIZED=NO
NEXT=I02_R3_EVIDENCE_AND_DEPENDENCY_GATE_BEFORE_IMPLEMENTATION
```
