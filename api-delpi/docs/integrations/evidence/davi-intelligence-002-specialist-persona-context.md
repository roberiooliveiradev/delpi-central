# DAVI-INTELLIGENCE-002 — Specialist persona, knowledge e context delivery

> **Status:** implementação bounded concluída; Agent Studio sync = PENDING_MANUAL.
> Owner: `api-delpi` (`davi_agent_intelligence.json` + `branding.py` +
> `openai-workspace-agent-davi.md` paste canônico). Zero ops novas, zero MCP
> tools novas, zero mudança de AuthZ.

## 1. Escopo executado (Grupo A — autorizado)

| Item | Decisão | Evidência |
|---|---|---|
| Persona estável | Fonte canônica: paste Agent Studio (`openai-workspace-agent-davi.md`) + `DAVI_MCP_INSTRUCTIONS` (initialize instructions). Eco operacional via `agent_directives.persona` | `test_davi_intelligence_002_specialist_context.py` |
| Conhecimento especialista | Novas seções em `davi_agent_intelligence.json` projetadas em `capability_surface.agent_directives`: `persona`, `data_specialist`, `protheus`, `tsql`, `table_discovery`, `proactive` | testes Grupo B |
| Entrega de contexto MCP | `instructions` do initialize (estável) + `agent_directives` em cada discover (dinâmico). MCP prompts/resources **não** adicionados — mecanismo mínimo compatível | `branding.py` |
| Aliases de movimentação | `get_product_internal_movements` +17 frases de negócio; `execute_readonly_sql` +9 frases de varredura agregada | allowlist v30 |
| Orçamento | Diretivas 26→32 KiB re-baselined (29897B usados; transport bound 64KiB) | `DAVI_AGENT_DIRECTIVES_MAX_BYTES` |

## 2. Persona canônica

Garoto curioso, inteligente, prestativo, bem-humorado e ocasionalmente
travesso — especialista em dados na competência. Humor leve e contextual;
nunca infantilizar assuntos sérios. Atender primeiro; sugerir 1–2
aprofundamentos compatíveis com capabilities autorizadas. Persona = UX,
nunca autoridade (registrado em `persona_bridge.authority`).

## 3. MCP context delivery — inventário de mecanismos

| Mecanismo | Status | Uso |
|---|---|---|
| `initialize` server `instructions` | PROVEN (emitido) / TO_INVENTORY (consumo pelo host) | persona + postura estável |
| `capability_surface.agent_directives` | PROVEN | contexto dinâmico completo em cada discover |
| Tool descriptions | PROVEN | contrato das 2 tools |
| Tool response metadata | PROVEN | `structuredContent` com candidates + surface |
| MCP prompts / resources | NÃO ADOTADO | superfície extra sem necessidade comprovada |
| Agent Studio Files | PROVEN (corpus) | conhecimento governado documental |

Honestidade AC-13: o MCP `instructions` é emitido no `initialize`, mas o
consumo/aplicação pelo host (ChatGPT em chat comum) não é observável neste
repositório — `PROVIDER_HOST_INSTRUCTIONS_CONSUMPTION = TO_INVENTORY`.

## 4. Validação

```text
UNIT/CONTRACT  = PASS — 16 testes novos (persona, seções, aliases, budget,
                 paste parity, authority boundary)
FOCUSED SUITES = PASS — 521 testes das suítes DAVI governadas
BENCHMARK 264  = top-1 0.9619 · required 0.9914 · top-5 1.0 · misses 0 ·
                 leaks 0 · canonical_sql family 1.0
NEW CASES      = 10 (DQ-SUP-045..047, DQ-SQL-109..110, DQ-MET-011,
                 DQ-AMB-011, DQ-COM-037..038, DQ-PRD-035) — todos roteiam
                 corretamente, incl. varredura agregada sem nomear SQL
```

## 5. Roteamento empírico (live-seeded `app.openapi()`)

| Query | Top-1 | Score |
|---|---|---|
| movimentos de materiais | `get_product_internal_movements` | 0.9225 |
| registros de entrada de materiais | `get_product_internal_movements` | 0.9425 |
| produtos com movimentação este mês | `execute_readonly_sql` | 0.9425 |
| qual tabela guarda as estruturas | `search_tables_by_description` | 0.905 |
| componentes de um produto | `get_product_structure` | 0.915 |
| pedidos de compra em aberto | `get_product_purchases` | 0.9025 |

## 6. Pendências (Grupo B — dependentes de aprovação/provider)

```text
AGENT_STUDIO_SYNC        = PENDING_MANUAL — colar bloco canônico atualizado
CHATGPT_PLUGIN_LIVE      = TEST_NOT_RUN — validação em chat comum requer
                           provider autenticado
SECOND_USER_AUTHZ        = PENDING — gate independente preexistente
HOST_INSTRUCTION_CONSUME = TO_INVENTORY — não simulável; documentado
```
