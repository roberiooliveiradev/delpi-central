# Avaliação de agnosticismo — Kimi K3 (OpenRouter) vs Qwen local (Ollama)

TASK_ID: DELIA-C3-PYDANTIC-AI-KIMI-QWEN-MODEL-AGNOSTICISM-EVALUATION-01
Kimi: moonshotai/kimi-k3 via openrouter_kimi | Qwen: qwen3:4b-instruct-2507-q4_K_M via local_ollama (default) | v41 | pydantic_ai 2.50.0

## Paridade arquitetural (comprovada)
Mesmo Agent, MCPToolset, governed hook→gates→projection, typed args
(params=object em todas as chamadas Qwen), structured output
(declared_answer presente), AuthZ/governança, Evidence/limitations.
Zero branches por modelo na aplicação. AGNOSTICISM: PASS.

## Comparativo real (mesmos cenários, typed records)

| Cen | Kimi calls/fails | Qwen calls/fails | Qwen outcome |
|---|---|---|---|
| A1 | 1/0 | 2/0 | GROUNDED partial (latency 203s local) |
| B1 | 8/5 (mesmo erro 5x) | 6/1 | GROUNDED — sem retry mesma-classe |
| C1 | 8/3 | 3/0 | GROUNDED |
| E1 | 8/1 | 4/0 | GROUNDED |

## Leitura causal
B1: Qwen não repetiu erro-classe — variou view/params e recuperou com
analyzes válidos; 1 fail isolado de read. O "retry cego" era
comportamento do KIMI, não defeito de arquitetura nem instrução —
a mesma v41 produziu estratégia superior em Qwen.
Eficiência: Qwen menos calls (17 vs 33) mas latência maior
(inferência local); custo monetário ~0 (local) vs ~$0.15 remoto.
Qualidade: Qwen declarou `partial` + limitações honestas em todos —
Outcome conservador e correto; Kimi declarou `complete` mais vezes
(declared_status_overridden observado nas duas).

## Veredictos
ARCHITECTURAL_CONFORMANCE: PASS (ambos)
PROVIDER_COMPATIBILITY: PASS (ambos; tool calling + structured output OK)
MODEL_LIMITATION: Kimi — repetição de error-class (provado, B1);
  Qwen — nenhuma limitação comportamental provada nestes cenários,
  latência maior é característica local, não defeito.
DELIA_DEFECTS_PROVEN: nenhum.
