# Root cause — Kimi × Qwen: contexto, parâmetros e recuperação

TASK_ID: DELIA-C3-PYDANTIC-AI-KIMI-QWEN-CONTEXT-PARAMETER-ROOT-CAUSE-01

## Diferenças de config comprovadas (pydantic_ai.runtime.delpi.json)

| Campo | Qwen | Kimi | Efeito |
|---|---|---|---|
| retries (agent) | 2 | 1 | metade do orçamento de retry de validação |
| max_governed_attempts | 2 | 1 | metade das tentativas governadas |
| max_output_tokens | null | 2048 | cap duro de geração |
| effective_context_window | 16384 | null | sem ProcessHistory/gate local p/ Kimi |
| chat_template_kwargs | enable_thinking=False | idem | kwarg Qwen-template; OpenRouter ignora p/ Kimi |

## Experimento controlado (B1, perfil openrouter_kimi_parity:
retries=2, governed=2, output=8192 — revertido após o run)

Resultado: 5 calls, 2 fails ("Disallowed filters" — classe NOVA de
erro, não a anterior de filial/setor), limit atingido, sem answer
estruturada. O modelo mudou de estratégia (reads em vez de analyze)
mas MANTEVE o padrão de repetição de erro-classe em forma diferente.

## Conclusão causal

CONFIGURATION_ASYMMETRY: contribuinte real — Kimi corria com metade
do orçamento de recovery e cap de output (confundiu parte do gap
anterior). Não foi a única causa: sob paridade numérica o churn
persistiu numa classe diferente.
MODEL_BEHAVIOR: contribuinte persistente — mesmo com orçamento igual,
Kimi repete classe de erro sem resolver a condição bloqueante.
THINKING_KWARG: sem efeito observado (provider ignora/rejeita
silenciosamente — requests sucederam).
ProcessHistory ausente p/ Kimi: não provada como causa (contexto
não saturou em B1).

ROOT_CAUSE_STATUS: INCONCLUSIVE_PARCIAL — config confunde o gap
anterior; não elimina o padrão de retry cego do Kimi. Recomendação:
paridade de budgets entre perfis (decisão de config, fora desta
task) + comparação de modelos ampliada antes de atribuir a capacidade.
