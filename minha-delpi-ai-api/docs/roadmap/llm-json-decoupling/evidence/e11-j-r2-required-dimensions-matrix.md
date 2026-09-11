# J-R2 — requiredDimensions × matriz canônica

**Status:** COMPLETE_GATE = PASS (`REQUIRED_DIMENSIONS_MATRIX`)  
**HEAD_BEFORE:** `a3c683f064e174c256c57b724409cb84b29837c4`  
**Bloqueio:** A11-02  
**Authority:** `docs/testing/chat-ai-flow-families.md` §4

## Problema

O corpus `r1_r11_corpus_v1` declarava dimensões incompletas (ex.: args só R5; security só R11; compound só R1/R7). A matriz canônica exige conjuntos mínimos por classe de risco.

## Correção

| Artefato | Papel |
|---|---|
| `ChatRequiredDimensionsMatrixService` | authority §4 + validação |
| `r1_r11_corpus_v2.json` | corpus vigente (`sha256=1147e05d…`) |
| `r1_r11_corpus_v1.json` | histórico imutável (`371f0cfa…`); **falha** o gate |
| `scripts/assert_corpus_required_dimensions.py` | gate CLI |
| `run_e11_s9_final_candidate_offline.py` | bloqueia se matriz FAIL; usa v2 |

Regra: `declared requiredDimensions ⊇ minimum(matrixClass)`.

## Testes

| Caso | Esperado |
|---|---|
| v2 completo | PASS |
| sibling args/unknown com R3/R8/R9 | PASS |
| v1 histórico | FAIL (20 casos) |
| write só com R11 | FAIL (falta R10/R3/…) |

```bash
PYTHONPATH=. python3 -m unittest tests.unit.domain.services.test_j_r2_required_dimensions_matrix -v
PYTHONPATH=. python3 scripts/assert_corpus_required_dimensions.py
```

## Gate

```text
REQUIRED_DIMENSIONS_MATRIX = PASS
COMPLETE_GATE (J-R2) = PASS
NEXT = J-R3
```
