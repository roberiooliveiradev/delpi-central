# DÉLIA — Checkpoint de coordenação F1 / Qualidade da Compreensão (2026-11-18)

**Natureza:** DOCUMENTATION_ONLY / IMPLEMENTATION_BRIEF_PREPARED / NOT_EXECUTED.
**TASK candidata:** `COORDINATION_C3_T2_COMPREHENSION_OPERATION_ANCHOR_AND_HANDOFF_RELIABILITY_GATE`.
**Fase documental no momento da revisão:** C3/T2. Revalidar Doc 16 e Execution Ledger no HEAD antes de executar.
**Escopo:** F1 do roadmap PO F1→F5 registrado em 2026-11-18 no Doc 16 e no ledger; não altera NEXT formal sem gate.

## Decisão de coordenação

Consolidar prompt bounded para Cursor/Devin, com invocação do especialista `.devin/skills/delia-development/SKILL.md`; aplicar Skill ChatGPT `delia-development` para arquitetura, revisão e handoff.

Prioridades F1:
1. Distinguir `MaterialObligation.operation` explicitamente solicitada da estratégia de investigação escolhida pelo modelo, sem relaxar o matching de Suficiência.
2. Verificar integridade da transição INT-2 Compreensão → Application plan acceptance → INT-1 Investigação: goal, filtros, identities, obligations, clarificação residual e budget.
3. Investigar `T2-B-COMPREHENSION-AGENT-ERROR` sem presumir causa; RED antes de fix, menor mudança, GREEN, regressão, A/B real e safety.
4. Preservar `required_scope`, owners, provenance, filtros, controle de AuthZ e gates nativos Pydantic AI. Nenhum terceiro/quarto Agent, engine, registry ou planner.

**Status de execução:** `TEST_NOT_RUN` nesta atividade de coordenação; nenhuma alteração de código; verificação e eval F1 pendentes. O prompt completo já foi entregue no chat de coordenação; este checkpoint não o substitui nem declara aceite funcional.

## Normas: fonte e enforcement

| Diretriz | Skill ChatGPT | Especialista Cursor/Devin | Fonte revalidável |
|---|---|---|---|
| Clean Architecture, Ports & Adapters, DDD pragmático | Explícita | Explícita | Docs 49/50 e `.cursor/rules/` |
| Framework-first / Pydantic AI nativo | Reuse-before-design e contratos | Explícita: usar runtime nativo; proibir engines/parsers/planners semânticos paralelos | Doc 291, Doc 49, `.cursor/rules/delia-execution-protocol.mdc` |
| Não criar arquitetura/capability/authority paralela | Explícita | Explícita, Abstraction Gate | Docs 17/49/50 e rules |
| Clean code / menor diff / sem duplicações | Menor diff, remoção de substituto comprovado | Menor diff, consumers, regressão e residual search | `AGENTS.md`, `.cursor/rules/`, política de eliminação de legado |
| Contrato, owner e reutilização antes de design | `EXISTING_EQUIVALENT` / `REUSE_DECISION` | Mesmos gates | Docs 16/17/25 |
| Segurança, limites de autonomia, READ/PREPARE/ACT | Explícita | Explícita | Docs 17/20/21, `AGENTS.md`, rules |
| RED/GREEN, CI, outcome e delpi-verifier | Brief/review | Execução SHA-bound e relatório | `AGENTS.md`, `agent-kit/verifier/project-contract.md` |
| Fonte de verdade e fase atual | GitHub/ledger sempre antes do prompt | Reancoragem antes do diff | Doc 16 + ledger |
 
**Nota:** orientação resumida da Skill não substitui leitura efetiva dos padrões oficiais; regras transversais vivem em `.cursor/rules/` e `AGENTS.md`. A expressão “clean code” corresponde aqui a menor diff correto, responsabilidade única, legibilidade, não duplicação, teste e revisão; não é autorização para refatorar fora do escopo.

## Preconditions obrigatórias ao executor

- Revalidar HEAD, branch, WIP, worktrees, origin/main, authorities, Doc 16, ledger, CP/RQ e residual register.
- Classificar `EXISTING_EQUIVALENT=YES|NO|TO_INVENTORY` e `REUSE_DECISION=REUSE|EXTEND|NEW`.
- Produzir RQ/AC numerados, relatório por requisito, eval real no SHA/config avaliado, delpi-verifier independente (até 3 rodadas), CI e outcome.
- Não declarar PASS onde houver `TEST_NOT_RUN`, `STALE_EVIDENCE` ou `INCONCLUSIVE`.
- Se aparecer conflito entre regra geral de deploy de `AGENTS.md` e gate de produto C3/T2, não executar deploy: identificar precedência e escalar `ARCHITECTURE_DECISION_REQUIRED` quando necessário.
- `PRODUCTION_DEPLOY=NOT_AUTHORIZED`; `TWO_AGENT_PROMOTION=NOT_AUTHORIZED`; `INT3_INT4_AGENT_IMPLEMENTATION=NOT_AUTHORIZED`; `PHASE_ADVANCEMENT=NO`.

**NEXT:** executor Cursor/Devin recebe o brief F1 completo, reancora no HEAD e devolve `DÉLIA EXECUTION REPORT` com verificação independente para review de coordenação. F2 somente após gate próprio.
