# Set/2026 — Desacoplamento JSON + generalização LLM/OpenAPI

**Roadmap:** [llm-json-decoupling](../roadmap/llm-json-decoupling/README.md) (`ARQUIVADO`)  
**Ledger:** [execution-ledger.md](../roadmap/llm-json-decoupling/evidence/execution-ledger.md)  
**Release:** `globalReleasePass=true` (E9.S8 / E9.S15)

---

## Resumo

A Minha DELPI AI deixou de depender de catálogos técnicos / markers / heuristics por rota como **autoridade** de routing, follow-up, binding e apresentação. A autoridade canônica passou a:

```text
OpenAPI + Action Catalog
→ Turn Understanding + retrieval/planner
→ schema-driven presentation
→ recommendations grounded
```

Policies determinísticas (RBAC, required args, confirmation, timeouts) permaneceram fora do LLM.

## Ondas (A–H)

| Onda | Entrega |
|------|---------|
| A | Inventário + baseline freeze |
| B | Registry OpenAPI-first + DELETE markers (E9.S12) |
| C | Turn Understanding cutover (heuristics KEEP_APPROVED) |
| D | Multi-turn/args + Postgres `lastAction` overlay (E3.S8) |
| E | Capabilities / composition |
| F | Recommendations contextual grounded |
| G | Presentation schema-first + skills/help residual |
| H | Evals R1–R11, live gates, DELETE autorizado, release pass |

## Evidências-chave de release

- E9.S13–S15 live (compound, multi-turn, unknown API, safety, recommendations, send/stream/simulate)
- E9.S11 efficiency (p50/p95 + tokens metadata)
- E9.S16 F5/session reload via API
- E9.S6 `deleteAuthorized=true`

## Residuais justificados (não são débito aberto)

- Heuristics TU `KEEP_APPROVED` (fast paths)
- `api_route_domains.pathMarkers` JUSTIFIED_POLICY
- Pasta roadmap mantida como arquivo histórico
