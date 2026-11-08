# R01 — Decisão arquitetural: estratégia nativa de structured output (Pydantic AI 2.50.0)

TASK_ID: `DELIA-C3-R01-PYDANTIC-AI-NATIVE-STRUCTURED-OUTPUT-ARCHITECTURE-DECISION-01`
Data: 2026-11-08 | Executor: Devin | Status: DECISÃO para implementação na task seguinte

## 1. Problema comprovado (resumo causal)

C1 Qwen falha **antes** do `output_validator`: o modelo emite prosa simples em vez de `InvestigationAnswer`/tool calls — `declared_answer=null`, validator nunca acionado, NON_GROUNDED honesto. A fronteira real é a produção/decodificação de saída estruturada.

## 2. Inventário nativo — pydantic_ai 2.50.0 (verificado no container)

`pydantic_ai.output` expõe: `ToolOutput`, `NativeOutput`, `PromptedOutput`, `TextOutput`.

- **Atual**: `output_type=InvestigationAnswer` → **ToolOutput implícito** (result-tool call). Quando o modelo emite prosa sem chamar o result-tool, parse falha → retry nativo → prosa de novo → fallback honesto. O gap: nada obriga structured output e nenhuma fronteira tipada captura prosa-operacional.
- **ToolOutput**: disponível; é o modo atual (falha provada em C1).
- **NativeOutput**: disponível — schema via `response_format` do provider.
- **PromptedOutput**: disponível — schema injetado em instrução + validação pydantic; não depende de feature do provider.

## 3. Experimentos executados (spike isolado, container dev, não commitado)

Patch temporário: `output_type` selecionável por env `DELIA_OUTPUT_STRATEGY`. Mesma pergunta canônica, mesmo model/profile/identidade/MCP real.

| Estratégia | C1 Qwen resultado | structured output | validator | tool calls | grounding |
|---|---|---|---|---|---|
| tool (baseline) | prosa pura | **inválido/ausente** | NÃO entra | 0 | NON_GROUNDED |
| prompted | `InvestigationAnswer` tipado `insufficient` + unmet_obligations | **válido** | entra (retry dispara) | 0 | NON_GROUNDED honesto |
| native | `InvestigationAnswer` tipado `insufficient` + clarification | **válido** | entra | 0 | NON_GROUNDED honesto |

Observações:
- Ambas as alternativas eliminam o vazamento de prosa: a declaração agora é **tipada, validada e governada** (`insufficient` + obrigações não atendidas declaradas honestamente em vez de narrativa livre).
- `native` em Ollama local: C1 completou, mas B1 ficou >15 min sem concluir — latência/risco real com `response_format=json_schema` em modelo local (registrado como constraint técnico).
- `prompted` completou C1 em ~126s.
- B1 Qwen (baseline tool) funciona — 3 invokes GROUNDED; coexistência tool-use×alternativas fica para a task de implementação (TEST_NOT_RUN, não presumir incompatibilidade — `PromptedOutput` não altera tool calling, só o canal do resultado final).
- Qwen C1 continua sem chamar tools, mas agora **declara `insufficient`/clarification tipada** — improvement real de contrato; Outcome C1 continua NOT_ACHIEVED (limitação do modelo 4b persistida, honestamente).

## 4. Comparação nos critérios

| Critério | tool (atual) | prompted | native |
|---|---|---|---|
| pydantic_ai 2.50.0 | ✓ | ✓ | ✓ |
| MCPToolset coexist | provada (B1) | não altera o canal de tools | provada em outros providers; Ollama local lento |
| Preserva InvestigationAnswer | sim, quando o modelo coopera | **sempre tipado** | sempre tipado |
| Recupera gap C1 (prosa→tipado) | não | **sim** | sim |
| Neutralidade de provider | sim | **sim (não depende de feature do provider)** | depende de response_format do provider |
| Latência local | ok | ok (~126s) | **degradada em Ollama (B1 >15min)** |
| Novo componente | nenhum | nenhum (1 linha no Agent) | nenhum |

## 5. DECISÃO: `ACCEPT_WITH_TECHNICAL_CONSTRAINTS` — PromptedOutput

Estratégia selecionada: **`output_type=PromptedOutput(InvestigationAnswer)`** no Agent de investigação.

Justificativa:
- Resolve comprovadamente o vazamento de prosa (C1 passa a produzir declaração tipada validada).
- Provider-neutral por construção (não depende de `response_format`; funciona igual em Ollama/OpenRouter) — nenhum branch por modelo.
- Uma linha no Agent existente; zero novos componentes, zero planner novo, zero parser paralelo.
- Constraints documentados: (a) `NativeOutput` é tecnicamente viável em providers com structured-outputs mas degradou latência em Ollama local — pode ser candidato futuro por provider adapter se medido; (b) coexistência tools×prompted a validar na implementação (B1 Qwen real); (c) C1 Outcome permanece NOT_ACHIEVED — limitação do modelo local, honesta, não mascarada.

Alternativas rejeitadas:
- ToolOutput (atual): falha provada no gap de prosa.
- NativeOutput como padrão único: constraint de latência Ollama não resolvido.
- TextOutput/engine custom: PROIBIDO/REJECT_CUSTOM_ENGINE.

## 6. Revisão do validator anterior

O branch `insufficiency_retry` para COMPLETE/PARTIAL+zero-evidence: **manter** — com PromptedOutput toda saída vira tipada, então o validator passa a ser sempre alcançável (antes era pulado na prosa). O retry bounded permanece útil e agora efetivamente cobre TODAS as respostas — recomendação: manter como está na implementação seguinte, observando em testes que conceptual questions podem declarar `partial`/limitations (o retry permite re-declaração, não força tools).

## 7. Implementation-ready next step

- **Owner**: DÉLIA — orchestration/pydantic_ai_investigation.py (mesmo boundary do spike).
- **Diff esperado**: no bloco `agent = Agent(...)`: `output_type=InvestigationAnswer` → `output_type=PromptedOutput(InvestigationAnswer)` + import `from pydantic_ai.output import PromptedOutput`. ~2 linhas.
- **Testes RED/GREEN**: teste comportamental do validator agora cobrindo saída tipada sempre; teste de regressão dos 70 focused; behavioral T01–T04 do rework anterior.
- **Real eval obrigatório pós-implementação**: C1 Qwen ×3, B1 Qwen ×2, C1/B1 Kimi controle, controle conceitual ×1 cada — verificar coexistência tools×prompted (B1) e não-regressão Kimi.
- **Rollback**: revert de 1 parâmetro.
- **Gates**: Outcome C1 pode permanecer honestamente NOT_ACHIEVED (limitação do modelo) — o gate de sucesso da implementação é saída tipada sempre + tools quando o modelo decide + nenhuma regressão.
