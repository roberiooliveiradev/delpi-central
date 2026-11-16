# C3/T2 — Pacote de evidências (grounding / multipágina / multi-turno)

**TASK:** `DELIA-C3-T2-TWO-AGENT-FINAL-EVIDENCE-CI-NEGATIVE-AND-VERIFIER-CLOSURE-01`

Pacote sanitizado para revisão GPT independente no GitHub. Artefatos brutos em
`delia-api/.battery/` permanecem gitignored; este diretório é a superfície
publicável.

## Manifesto

Ver `manifest.yaml`.

## Commits de referência

| Papel | SHA |
|---|---|
| Implementação funcional | `c0891eb1a5b18443a4e7d3da6ce831a24b61b3da` |
| Correção OC-1 | `550eae558ddfe61bac546d98a862f8e8c2e52eac` |

Commits intercalados **fora** do escopo DÉLIA entre os dois:

- `e327b08e5a` — docs ui-review
- `9488209013` — my-requests E2E

## Artefatos

| Arquivo | Conteúdo |
|---|---|
| `scope-reconciliation.md` | Matriz arquivo × commit × ownership × verificação |
| `g2.md` + `g2.sanitized.json` | Caso G2 (agregação ativa) |
| `r5.md` + `r5.sanitized.json` | Multipágina 40+40+29 / total 109 |
| `r6.md` + `r6_*.sanitized.json` | Clarificação + recovery multi-turno |
| `negatives-matrix.md` | Negativos G2 / REF05 / R5-N* / R6 |
| `tests-and-ci.md` | Comandos, exit codes, CI |

## Segurança

Tokens, bearers, cookies e secrets foram removidos ou substituídos por
`[REDACTED]`. Respostas longas do owner foram truncadas com marcador
`…[truncated]` quando necessário para revisão.
