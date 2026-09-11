# Ledger de execução — llm-json-decoupling

**Fonte:** markdowns desta pasta (não `.cursor/plans`).  
**Atualizado:** 2026-09-11 — auditoria pós-fechamento da Onda J  
**Baseline histórico:** [`onda-a-baseline/manifest.json`](./onda-a-baseline/manifest.json) (`runId=0249db78-d6fd-45b3-84bf-d11abcd17a6a`)  
**Plano ativo:** [`../planos/11-corrective-cutover-generalization-cleanup.md`](../planos/11-corrective-cutover-generalization-cleanup.md)  
**Auditoria vigente:** [`e11-post-close-audit-2026-09-11.md`](./e11-post-close-audit-2026-09-11.md)

> O histórico detalhado das subetapas permanece preservado nos arquivos de evidência e no Git. Este ledger registra o estado canônico vigente e os marcos necessários para continuar a execução sem confundir PASS histórico com release atual.

## 1. Ondas

| Onda | Escopo | Estado vigente | Observação |
|---|---|---|---|
| A | baseline/contratos | **HISTÓRICO / BASELINE** | evidence preservada |
| B | routing universal | **HISTÓRICO** | avanços incorporados; revalidados na J |
| C | entendimento | **HISTÓRICO** | semantic ownership ainda reaberto na J |
| D | multi-turn/args | **HISTÓRICO** | structured continuity/schema-first preservados |
| E | capabilities/composition | **HISTÓRICO** | capability metadata válida; composition preservada |
| F | UX/recommendations | **HISTÓRICO / DÍVIDA REABERTA** | `recommendationQueries` ainda material |
| G | presentation/skills | **HISTÓRICO** | presentation improvements preservadas |
| H | cutover/evals | **PASS HISTÓRICO; NÃO RELEASE VIGENTE** | evidence anterior não fecha estado atual |
| I | zero mapa lateral | **ACEITE HISTÓRICO INVALIDADO** | substitutos semânticos encontrados depois |
| J | correção arquitetural | **REABERTO / P0** | primeiro fechamento invalidado pela auditoria pós-E11.S10 |

## 2. Candidate histórico da Onda J

O candidate:

```text
782a49721319571f0fe4733d59b8a5cc65ac4c04
```

foi inicialmente registrado como:

```text
R1..R11 = PASS
VERIFY_FINAL = PASS
FINAL_RESULT = PASS
```

Após auditoria pós-fechamento:

```text
CURRENT_RELEASE_EVIDENCE_STATUS = INVALIDATED
R8 = FAIL
R1_R11_REQUIRED_DIMENSIONS = FAIL
EVIDENCE_REPRODUCIBLE = FAIL
UNKNOWN_EXTERNAL_FULL_CHAIN = INCONCLUSIVE
METAMORPHIC_RENAME = INCONCLUSIVE
COMPLETE_GATE = FAIL
VERIFY_FINAL = FAIL
FINAL_RESULT = VERIFY_FINAL_FAILED
```

Referências:

- [`e11-s9-final-candidate.md`](./e11-s9-final-candidate.md)
- [`e11-s10-residual-scan-verify-final.md`](./e11-s10-residual-scan-verify-final.md)
- [`e11-post-close-audit-2026-09-11.md`](./e11-post-close-audit-2026-09-11.md)

## 3. Estado revisado E11.S0–S10

| Etapa | Estado vigente | Próximo tratamento |
|---|---|---|
| E11.S0 | PASS histórico | nenhum; usar como baseline histórico |
| E11.S1 | **FAIL / REABERTO** | J-R6 Architecture Enforcement independente |
| E11.S2 | PASS pendente final reverify | J-R12 |
| E11.S3 | PASS/PARTIAL | J-R8 + J-R12 |
| E11.S4 | PASS/PARTIAL | J-R5 + J-R12 |
| E11.S5 | **FAIL / REABERTO** | J-R7/J-R8 |
| E11.S6 | **PARTIAL/FAIL / REABERTO** | J-R9 |
| E11.S7 capability | PASS | revalidate J-R12 |
| E11.S7 recommendations | **FAIL / REABERTO** | J-R10 |
| E11.S8 credentials | PASS | revalidate J-R12 |
| E11.S8 Clean Architecture | **PARTIAL/FAIL / REABERTO** | J-R11 |
| E11.S9 | **INVALIDADO** | J-R1/J-R2/J-R3/J-R4/J-R5/J-R12 |
| E11.S10 | **INVALIDADO** | novo residual scan somente em J-R12 |

## 4. Regras de fechamento

Não marcar `ATENDIDO/COMPLETED/100%` se item material permanecer em:

```text
PARTIAL
ATENDIDO_PARCIAL
LEGACY_FALLBACK
SHADOW_ONLY
INCONCLUSIVE
PENDING
DEFERRED sem justificativa
TODO/FIXME/HACK/TEMPORARY
flag/fallback sem exit criteria
evidence stale ou não reproduzível
gate enfraquecido ou dependente de self-attestation
```

Qualquer mudança material posterior ao candidate invalida as dimensões afetadas até rerun no novo HEAD.

## 5. Protocolo por subetapa

```text
abrir Plano 11
→ revalidar HEAD + git status
→ READY_TO_EXECUTE?
→ confirmar owner/producer/consumer
→ implementar menor escopo coerente
→ wiring real
→ unit/contract
→ positive + sibling + negative
→ generalization/metamorphic/unknown quando aplicável
→ adversarial diff review
→ semantic residual search
→ evidence reproduzível
→ postconditions
→ COMPLETE_GATE
→ só então liberar dependente
```

## 6. Fila vigente

```text
J-R1  corrigir evaluator R8
J-R2  alinhar requiredDimensions
J-R3  tornar evidence reproduzível
J-R4  unknown external full chain
J-R5  metamorphic provider/path/operationId rename verdadeiro
J-R6  Architecture Enforcement independente
J-R7  remover path/operationId semantic affinity
J-R8  cleanup registry/content técnico
J-R9  consolidar semantic single owner
J-R10 remover recommendationQueries como LEGACY_FALLBACK material
J-R11 corrigir Clean Architecture residual
J-R12 novo candidate final + R1–R11 + residual + COMPLETE_GATE
```

## 7. Marcos históricos relevantes

| Data | Evento |
|---|---|
| 2026-09-10 | Ondas A–G executaram inventário, OpenAPI-first, Turn Understanding, schema-driven args/presentation, capabilities e recommendations iniciais |
| 2026-09-10/11 | Onda H consolidou evals, live gates e primeiro release histórico |
| 2026-09-11 | Onda I tentou fechar zero mapa lateral; auditoria posterior encontrou substitutos semânticos |
| 2026-09-11 | Onda J criada para corrigir path-domain/strategy/continuity/registry/NLU/recommendations/security/evidence |
| 2026-09-11 | E11.S2–S4 corrigiram `_DOMAIN_RULES`, schema binding e structured continuity no caminho principal |
| 2026-09-11 | E11.S7 corrigiu capability contract; credenciais de smoke foram removidas de defaults em E11.S8 |
| 2026-09-11 | Candidate `782a4972…` foi registrado como PASS e programa arquivado |
| 2026-09-11 | Auditoria pós-fechamento encontrou A11-01…A11-12 e invalidou E11.S9/E11.S10 como release evidence |
| 2026-09-11 | Onda J / Plano 11 **REABERTOS**; fila J-R1…J-R12 passa a ser o estado canônico |

## 8. Proibições vigentes

- não criar `.plan.md` paralelo para o mesmo objetivo;
- não mover catálogo/heurística de JSON para Python/TS ou vice-versa para fazer o gate passar;
- não usar `cleanupMeta`/flag declarativa como prova suficiente de ausência de authority;
- não chamar sinônimo/paráfrase de metamorphic provider/path/operationId rename;
- não contar unknown API como PASS full chain se o executor HTTP/outcome não foi provado;
- não aumentar threshold de latency ou reduzir requiredDimensions para acomodar candidate;
- não editar manifest de resultado para contradizer o runner;
- não declarar `FINAL_RESULT=PASS` com `LEGACY_FALLBACK`, `PARTIAL`, `INCONCLUSIVE` ou dívida material do objetivo original.

## 9. Próximo desbloqueio

A próxima execução deve começar por **J-R1/J-R2/J-R3**, pois os avaliadores e evidence chain precisam estar corretos antes de um novo candidate poder ser confiavelmente medido.

`J-R4…J-R11` podem ser planejados em dependências coerentes, mas `J-R12` fica bloqueado até todos os gates anteriores estarem PASS.
