# Diagnóstico causal — eficiência multi-step MCP (B2, C1, C2, D5)

TASK_ID: DELIA-C3-PYDANTIC-AI-MCP-MULTISTEP-EFFICIENCY-CAUSAL-DIAGNOSTIC-01
EVALUATED_SHA: 164746162e7aa07616d34479dde342e5871bd6fc
CURRENT_HEAD: 1672b07f9067aad9985ab9c485e689c2cb620a28
MODEL: moonshotai/kimi-k3 | PYDANTIC_AI: 2.50.0 | INSTRUCTION: v41
EVIDENCE: /tmp/delia_kimi_gen/*.json (traces reais com mcp_invoke_records)

## Matriz causal

### B2 — "Quais indicadores são acompanhados na área de engenharia?"
Sequência: teo.get_context → davi.discover (0 cand) → davi.discover REDUNDANTE (0 cand)
→ teo.read(department, params=STRING) → teo.read(measurement, params=STRING → INVALID_FIELD)
→ teo.analyze(sem filial_id → 400) → teo.analyze(params=STRING → 400)
Primeira fronteira divergente: **TYPED TOOL ARGUMENTS** — `params` enviado 3× como
string Python-dict. Secundário: discover duplicado + campos obrigatórios adivinhados.
Causa-raiz: PROVEN — args inválidos atravessam o boundary sem rejeição/retry.

### C1 — "Compare as economias de novembro e dezembro"
Sequência: get_context → analyze(summary) → read(measurement, params=STRING → 82 itens
sem filtro) → analyze(evolution) → analyze(ranking Nov-Dez) → analyze(ranking só Nov,
redundante) → analyze(by_family → vazio, desperdiçada)
Primeira fronteira: TYPED TOOL ARGUMENTS + tool_calls_limit antes da composição.
Causa-raiz: PROVEN — idem + churn de 2 chamadas marginais.

### C2 — "O produto 50220013 aparece em algum processo monitorada?"
Sequência: davi.discover → davi.execute (produto OK) → teo.read(process,
params=STRING "{'filter':{'q':'50220013'}}" → 109 itens SEM FILTRO) → read idem+pagination
(109) → discover redundante → 2× process_context get (owner 500 TypeError)
→ read 'CB18BRAN' (109)
Primeira fronteira: TYPED TOOL ARGUMENTS — o filtro NUNCA foi aplicado porque params
chegou como string; owner ignorou silenciosamente → re-tentativas → limit.
Secundário: owner process_context retorna 500 (defeito do owner TÉO, fora de escopo).
Causa-raiz: PROVEN.

### D5 — "Liste as revisões de engenharia publicadas ontem às 14h"
Sequência: discover → get_context(catalog) → read(revision, params=STRING, 94 itens)
→ 2× discover redundantes → read(revision, filtro temporal EM STRING → 94 itens sem
filtro) → get_context(self)
Primeira fronteira: TYPED TOOL ARGUMENTS — o filtro temporal existia e foi
serializado como string → ignorado → dados corretos nunca recuperados com filtro.
Causa-raiz: PROVEN.

## Hipóteses

- H1 (limite insuficiente): REJEITADA como primária — churn precedeu o limit em
  todos os casos; chamadas legítimas teriam bastado.
- H2 (churn do modelo): CONFIRMADA contribuinte — discovers redundantes (B2:2×0,
  D5:3×), reads idênticos sem filtro (C2:3×109), ranking duplicado (C1).
- H3 (contrato/projeção de argumentos): **PROVEN — causa-raiz primária**.
  `_governed_mcp_hook` repassa args ao owner sem validar tipos contra o
  inputSchema publicado; o owner ignora string-serialized `params` → filtros
  nunca aplicados → dumps gigantes → re-tentativas → tool_calls_limit → dump
  final. O hint v41 informa, mas não rejeita — insuficiente contra Kimi.
- H4 (contrato/outcome): contribuinte — budget esgotado antes de declared_answer
  → join/dump apresentado; acceptor honesto (result_truncated, limit_reached).

## Análise de framework

Mecanismo necessário já existe: `process_tool_call` intercepta ANTES do wire;
`ModelRetry` devolve erro recuperável ao modelo. O que falta é a VERIFICAÇÃO de
tipo contra o inputSchema — hoje só há hint textual (v41).

## Correção bounded proposta (não implementada)

No `_governed_mcp_hook`/`_governed_invoke`: antes de invocar o owner, validar
cada argumento de nível superior contra o `type` declarado no inputSchema
publicado — `object` recebendo string → `ModelRetry`("argument X must be a
JSON object, not a serialized string"). Recuperável, sem parser manual, sem
coerção semântica. EXISTING_EQUIVALENT=YES | REUSE_DECISION=EXTEND.
Arquivos: pydantic_ai_investigation.py (+schema lookup via catalog).
RED test: tool call com params-string → ModelRetry, nunca atinge _governed invoke.
Ajuste de tool_calls_limit: NÃO recomendado — churn é a causa, não o budget.
