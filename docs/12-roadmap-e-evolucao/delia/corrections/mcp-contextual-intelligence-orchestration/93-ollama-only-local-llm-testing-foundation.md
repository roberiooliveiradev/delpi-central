# 93 — Ollama-only local LLM testing foundation

**TASK_ID:** `DELIA-C3-OLLAMA-ONLY-LOCAL-LLM-TESTING-01`
**Data:** 2026-10-22
**Autoridade primária:** [local-llm-testing-policy-ollama-2026-10-22.md](./local-llm-testing-policy-ollama-2026-10-22.md) (decisão de produto aprovada)
**Status:** `EXECUTED` — política implementada em código + configuração dev; seleção de modelo baseada em medição real.

## 1. Objetivo executado

Tornar Ollama o único provider de LLM real permitido nos testes locais da DÉLIA. O LLM externo permanece reservado a tráfego real de usuários em produção. Testes determinísticos continuam em fixtures/fakes. Nenhum runtime, serviço de modelos ou infraestrutura paralela foi criado.

## 2. Inventário medido no ambiente autorizado

- **Container:** `delpi-ollama` (compose `infra/docker-compose.dev.yml`, profile `optional-heavy`), volume persistente `infra_ollama_data`.
- **Ollama:** versão `0.40.8`, runner `llamacpp`, keep-alive efetivo ~29min.
- **Hardware host:** 16 logical CPUs; WSL ~7GiB RAM total (~4GiB livres no inventário); NVIDIA RTX 3050 Laptop 6GiB presente **mas não passada ao container** — inferência medida 100% CPU (`ollama ps` → `PROCESSOR 100% CPU`).
- **Limites:** container com cap de memória ~4500MiB; disco Docker `/dev/sdd` ~853GiB livres.
- **Modelos instalados no volume (durante a task):**
  - `qwen2.5:1.5b` — 3.1B→1.5B class, Q4_K_M, ~986MiB disco, ~1.2GiB residente.
  - `qwen2.5:3b` — 3.1B parâmetros, Q4_K_M, ~1.9GiB disco, ~2.2GiB residente, contexto 4096.
- **Endpoint efetivo:** `http://ollama:11434/v1` (OpenAI-compatible `/v1/chat/completions`), alcançável do container `delia-api` na rede `infra_delpi-network`.
- **Compatibilidade API:** `OpenAICompatibleModelInvocationAdapter` funcionou sem alteração contratual — mesma estrutura chat/completions, usage tokens reportados, timeouts e classificação de erro preservados.

## 3. Reuse gate (registro obrigatório)

| Responsabilidade | EXISTING_EQUIVALENT | REUSE_DECISION | OWNER | EVIDENCE |
|---|---|---|---|---|
| Serviço Ollama dev | YES | REUSE | `infra/docker-compose.dev.yml` (`ollama`) | container + volume persistente já declarados |
| Adapter real de modelo | YES | REUSE | `OpenAICompatibleModelInvocationAdapter` | `/v1` Ollama compatível; zero mudança no adapter |
| Config provider-neutral | YES | REUSE | `settings.py` (`DELIA_LLM_*`) | mesmas chaves, sem forks por provider |
| Gate de ambiente local | NO | NEW (mínimo) | `root_composer.py` + `settings.py` | composer anteriormente aceitava qualquer `openai_compatible` completo em dev |
| Bloqueio de egress em testes | NO | NEW | `tests/conftest.py` | nenhuma proteção de socket existia |
| Avaliação local Ollama | PARTIAL | EXTEND | `scripts/*_eval.py` | scripts existiam mas resolviam fallback KIMI |

`REUSE_DECISION` global: **REUSE** do adapter e da infra Ollama; **EXTEND** apenas em (a) policy local fail-closed no composer/settings, (b) guard de rede na camada de testes, (c) evals passando a exigir `DELIA_LLM_*` explícito.

## 4. Implementação

- `settings.py`: validação de política local — em `DELIA_ENV` não-produtivo, provider real só é admitido quando `DELIA_LLM_BASE_URL` aponta para endpoint Ollama local (host `ollama`/`localhost`/`127.0.0.1` na porta 11434) e `DELIA_LLM_MODEL` está presente; helper expõe a razão de bloqueio para testes/evals.
- `root_composer.py`: gate environment-aware — desenvolvimento com config externa ou incompleta retorna handler ausente (fail-closed, sem fallback); produção mantém o caminho externo aprovado **inalterado**.
- `tests/conftest.py`: neutralização de env ambiente (já existente) + bloqueio estrutural de socket para hosts públicos/externos de LLM — nenhum teste consegue egresso externo mesmo construindo o adapter diretamente.
- `tests/test_local_llm_egress_guard.py` (novo): suíte RED→GREEN cobrindo os 7 cenários exigidos — provider externo no perfil local, Ollama indisponível, modelo ausente, endpoint inválido, resposta incompatível com schema, tentativa de fallback externo e ausência de configuração.
- `tests/test_real_provider_adapter.py`: testes que exigem wiring real externo agora declaram `DELIA_ENV=production` explicitamente (externo só é legal em produção); modo testing continua determinístico.
- `tests/test_i04_provider_neutral_generalization.py`: asserts hardcoded de modelo Kimi substituídos por modelo configurado — provider-neutral de verdade.
- `scripts/real_model_eval.py`, `real_model_continuity_eval.py`, `cp4_governed_resume_eval.py`, `cp5_incident_repro_eval.py`: removida resolução por variáveis `KIMI_*`; exigem `DELIA_LLM_*` explícito e validam a política local antes de construir o adapter.
- `scripts/ollama_local_llm_eval.py` (novo): eval real via `HandleInteractiveConversationTurn`/orquestrador compostos, registrando por chamada: purpose, latência, tokens in/out, finish status, decisão estruturada e fases da atividade.
- `infra/.env.dev.example`: bloco `DELIA_LLM_*` documentado para Ollama local; nenhum segredo pago adicionado; variáveis produtivas intactas.

## 5. Avaliação real de modelos (hardware efetivo, CPU-only)

### qwen2.5:1.5b (Q4_K_M)

- Admission: 535–882ms warm — cabe no grant de ~6s.
- Answer stage: ~50% das chamadas retornaram saída não-JSON → `invalid_model_output` → FAILED honesto.
- **Fabricação factual:** para "qual o ultimo processo cadastrado?" o modelo inventou um número de processo ("processo 123456789012345678") sem evidência owner — a arquitetura classificou corretamente `NON_GROUNDED`, mas o modelo é **inseguro** para contratos DÉLIA.
- Veredito: inadequado — flake de JSON + alucinação operacional.

### qwen2.5:3b (Q4_K_M) — **modelo selecionado**

- Admission correto semanticamente: `o mcp davi` e controle CRI OFF classificados `requires_owner_surface=True / interaction_class=operational` (1.4–1.9s warm).
- `use o davi`: resposta honesta sem fabricação ("Davi is an unverified name..."), `NON_GROUNDED` correto.
- Latência: 2/5 chamadas de admission excederam o grant de ~6s sob CPU-only → `PROCESSING_TIMEOUT`/`BLOCKED` honestos (bounded, sem fallback externo).
- Continuidade multi-turn (`real_model_continuity_eval.py`, 5 casos×2 turnos): 1/5 PASS completo — o caso de segurança (injection resistance, secret/fact/authority boundaries todos PASS); 3 casos FAIL por `invalid_model_output`; 1 por `model_timeout`.
- Veredito: **selecionado com limitações classificadas** — semanticamente superior e sem fabricação observada; aderência JSON do estágio de resposta (~40% de falha em multi-turn) e latência de admission sob CPU-only são os gargalos medidos.

### Limitações registradas (não compensadas por arquitetura)

1. CPU-only nesta máquina torna chamadas frias proibitivas (3b: ~92s cold load) e admissions quentes ocasionalmente >6s. GPU pass-through do RTX 3050 é decisão de host/compose fora do escopo.
2. `OLLAMA_NUM_CTX=4096` efetivo no runner é menor que o contexto nominal 32k do modelo — prompts de estágio grandes devem permanecer compactos.
3. Nenhum modelo ≤3B medido aqui atinge 100% de aderência JSON no estágio `interaction.turn`; falhas terminam honestamente (`invalid_model_output`), nunca promovem conteúdo não estruturado.
4. Memória: manter os dois modelos residentes (~3.4GiB) pressiona o cap de ~4.4GiB; apenas o modelo selecionado deve permanecer quente.

## 6. Evidência de custo e egresso

- `EXTERNAL_LLM_LOCAL_EGRESS=NONE` — bloqueio em três camadas: composer fail-closed, conftest socket guard, eval scripts sem fallback.
- `LOCAL_MODEL_CALLS`: eval funcional 3b = 6 chamadas (admission×4 + turn×1 + 1 timeout), continuity = 10 chamadas; tokens locais reportados via `usage` (ex.: 598–621 in / 15–55 out por chamada).
- `EXTERNAL_MODEL_CALLS=0`; `COST_EXTERNAL=0` — nenhuma chamada paga; falhas não consomem tokens externos.

## 7. Verificação

- Guard suite: `test_local_llm_egress_guard.py` + adapter/I04 realinhados = **72 testes focados PASS**.
- Regressão backend completa: **~1190 testes PASS** no worktree avaliado.
- CRI ON/OFF: preservado — controle OFF exerce admission legado; CRI ON usa o caminho composto; ambos falham fechado e honesto sob indisponibilidade de modelo.
- Governed resume: timeouts de admission mapeiam para `PROCESSING_TIMEOUT` terminal (provider-level TIMEOUT não dispara re-tentativa de estágio — comportamento existente preservado, não alterado por esta task).

## 8. Configuração dev resultante

```text
DELIA_LLM_PROVIDER=openai_compatible
DELIA_LLM_BASE_URL=http://ollama:11434/v1
DELIA_LLM_MODEL=qwen2.5:3b
DELIA_LLM_API_KEY=ollama-local        # placeholder local, sem custo
DELIA_LLM_TIMEOUT_SECONDS=30
DELIA_MODEL_STAGE_TIMEOUT_SECONDS=30  # budgets internos intactos
```

## 9. Resultado

```text
TASK_ID=DELIA-C3-OLLAMA-ONLY-LOCAL-LLM-TESTING-01
OLLAMA_CONTAINER=delpi-ollama (infra_ollama_data persistente)
OLLAMA_VERSION=0.40.8
LOCAL_MODEL=qwen2.5:3b
MODEL_QUANTIZATION=Q4_K_M (3.1B, ctx efetivo 4096)
HARDWARE=16 CPU threads, RTX 3050 6GB não passada, CPU-only
MEMORY=container ~4.4GiB cap; modelo residente ~2.2GiB
MODEL_API_COMPATIBILITY=OpenAI-compatible /v1 via adapter existente

EXISTING_EQUIVALENT=YES (compose ollama + OpenAICompatibleModelInvocationAdapter)
REUSE_DECISION=REUSE adapter/infra; EXTEND policy local + test socket guard
ADAPTER_REUSED=OpenAICompatibleModelInvocationAdapter (sem alteração)

EXTERNAL_LLM_LOCAL_EGRESS=BLOCKED (composer + socket guard + scripts)
EXTERNAL_FALLBACK=NONE (KIMI_* removido dos evals; produção inalterada)
LOCAL_MODEL_CALLS=16 (funcional 6 + continuity 10)
EXTERNAL_MODEL_CALLS=0
COST_EXTERNAL=0

STRUCTURED_OUTPUT=PARTIAL (admission confiável; answer-stage ~40% non-JSON em 3b)
SEMANTIC_EVAL=PASS_WITH_LIMITS (classificação operacional correta; zero fabricação em 3b)
MULTITURN_EVAL=1/5 PASS (segurança boundaries PASS; restante invalid_output/timeout)
RECOVERY_EVAL=PASS (timeouts → PROCESSING_TIMEOUT/BLOCKED honestos, bounded)
CRI_EVAL=PASS (ON/OFF exercitados; OFF parity preservada)

RED_TESTS=7 cenários exigidos cobertos no guard suite
GREEN_TESTS=72 focados PASS
REGRESSION=~1190 backend PASS
EVALUATED_CONFIG=DELIA_ENV=development + Ollama /v1 + qwen2.5:3b

PRODUCTION_LLM_CONFIGURATION=UNCHANGED
I04_ACCEPTED=NO
C3_EXECUTED=YES
NEXT=COORDINATION_REVIEW
```

## 10. Resíduos

- `REAL_MCP_EVALUATION` permanece dependente de credencial delegada dev (`DEV_PORTAL_*` ausente) — herdado do CP5, não agravado por esta task.
- Aderência JSON do answer-stage em modelos ≤3B CPU-only é o principal limitador medido; mitigações futuras possíveis (GPU pass-through, `response_format` json_schema, modelo maior) exigem decisão separada.
- `TEST_NOT_RUN` legítimo quando Ollama estiver indisponível — nunca migração paga.
