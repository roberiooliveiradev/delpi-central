# Set/2026 — Desacoplamento JSON + generalização LLM/OpenAPI

**Roadmap:** [llm-json-decoupling](../roadmap/llm-json-decoupling/README.md)  
**Ledger:** [execution-ledger.md](../roadmap/llm-json-decoupling/evidence/execution-ledger.md)  
**Release (Ondas A–H):** `globalReleasePass=true` (E9.S8 / E9.S15)  
**Reabertura:** Onda I — [plano 10 zero mapa lateral](../roadmap/llm-json-decoupling/planos/10-zero-lateral-path-maps.md)

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

### Correção de política (2026-09-11)

**Nenhum mapa lateral deve existir.**  
A disposição `JUSTIFIED_POLICY` para `api_route_domains.pathMarkers` (e mapas irmãos por path) foi **revogada**. Domínio/label/classificação operacional devem vir do OpenAPI indexado / Action Catalog — não de JSON paralelo no assistente.

Débito Onda I: **ATENDIDO** (E10.S1–S5) — content sem chaves laterais; domínio via catalog/inference.

## Ondas

| Onda | Entrega | Status |
|------|---------|--------|
| A | Inventário + baseline freeze | ATENDIDO |
| B | Registry OpenAPI-first + DELETE markers (E9.S12) | ATENDIDO |
| C | Turn Understanding cutover (heuristics KEEP_APPROVED) | ATENDIDO |
| D | Multi-turn/args + Postgres `lastAction` overlay (E3.S8) | ATENDIDO |
| E | Capabilities / composition | ATENDIDO |
| F | Recommendations contextual grounded | ATENDIDO |
| G | Presentation schema-first + skills/help residual | ATENDIDO |
| H | Evals R1–R11, live gates, DELETE autorizado, release pass | ATENDIDO |
| I | Zero mapa lateral (`pathMarkers` / pathToken laterais) | **ATENDIDO** |

## Evidências-chave de release (H)

- E9.S13–S15 live (compound, multi-turn, unknown API, safety, recommendations, send/stream/simulate)
- E9.S11 efficiency (p50/p95 + tokens metadata)
- E9.S16 F5/session reload via API
- E9.S6 `deleteAuthorized=true`

## Residuais

| Item | Disposição atual |
|------|------------------|
| Heuristics TU fast paths | KEEP_APPROVED (não é mapa de rota) |
| Mapas `pathMarkers` laterais | **REMOVED** (E10) |
| `pathToken` KPI → `catalogToken` | **REMOVED** chave pathToken (E10.S4) |
| `presentation_profiles.pathRules` | **REMOVED** (E10.S4; entityProfiles + OpenAPI deriver) |
| Pasta roadmap | arquivado A–I |
