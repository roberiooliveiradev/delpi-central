# VISTA Semantic Tools Refactoring — Phase 1 (Discovery)

**Escopo:** inventário técnico, benchmark e preparação arquitetural para uma
futura convergência da superfície VISTA ao padrão semântico dos especialistas
(SURI/CAIO/EVA/CLARA). **Nenhuma refatoração foi implementada nesta fase.**

| Campo | Valor |
|---|---|
| Base HEAD | `5adbed8737` (`origin/main`, 2026-10-30) |
| Data do inventário | 2026-10-30 |
| Status | `PROVEN` onde há evidência de código/teste/runtime; `TO_INVENTORY`/`INCONCLUSIVE` marcado explicitamente |
| Owner | `tv-dashboard-api` (domínio TV Dashboard / especialista VISTA) |
| Autoridade arquitetural atual | `tv-dashboard-api/docs/architecture/adr-vista-specialist-capability-surfaces.md` + `vista-capability-matrix.md` |

## Documentos

1. [01 — Current State Inventory](01-current-state-inventory.md) — tools,
   superfícies, dispatch, contratos e runtime atuais.
2. [02 — Specialist Benchmark](02-specialist-benchmark.md) — VISTA vs SURI /
   CAIO / EVA / CLARA / TÉO / DAVI, com evidência de código real.
3. [03 — Capability Mapping](03-capability-mapping.md) — matriz de
   capabilities do domínio TV Dashboard vs exposição VISTA.
4. [04 — Semantic Tools Target Assessment](04-semantic-tools-target-assessment.md)
   — avaliação do catálogo-alvo de 6 verbos, equivalências e riscos.
5. [05 — Orchestration and Security](05-orchestration-and-security.md) —
   operações compostas, confirmações, autorização e falhas.
6. [06 — Refactoring Gap Analysis](06-refactoring-gap-analysis.md) —
   sintoma → evidência → causa → owner → contrato → reuse decision.
7. [07 — Phase 2 Planning Input](07-phase-2-planning-input.md) — base
   objetiva para o plano de implementação.

## Limitações desta fase

- Nenhum write/exclusão real foi executado; evidência de runtime vem de
  leituras (health, catalog, smoke já existentes).
- Validação conversacional no host ChatGPT permanece `TEST_NOT_RUN`
  (sem acesso ao host nesta sessão).
- Inventário REST backend coberto por rotas registradas em
  `tv_app/interface/http/routes/` — endpoints internos não-roteados não
  foram contados.
- O inventário de código foi executado sobre HEAD `28943d4d9b`; a branch
  documental foi rebaseada sobre `origin/main` `5adbed8737` (avanços
  upstream: docs commercial/transformometro — sem impacto nos arquivos
  inspecionados).
