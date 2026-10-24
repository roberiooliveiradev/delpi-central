# DAVI — Contextual Discovery & Knowledge Selection Generalization

**TASK_ID:** `DAVI-CONTEXTUAL-DISCOVERY-KNOWLEDGE-SELECTION-GENERALIZATION-01`
**Scope:** `api-delpi` discovery path only — no new MCP tools, no planner, no
registry, no RAG, no domain/product/topic hardcoding.

## 1. Symptom

Semantically equivalent documentary questions selected different
capabilities:

| Query | Selected |
|---|---|
| `Quais são as normas técnicas completas de descrição de matérias-primas da DELPI, incluindo a nomenclatura TERM. BALA?` | `read_governed_technical_knowledge` (correct) |
| `Normas completas descrição matérias primas e TERM. BALA` | `search_products` (wrong) |
| `normas de codificação de produtos intermediários` | **empty result** (wrong) |

Compound queries lost their documentary half entirely:
`Explique as normas de terminais e encontre dois exemplos reais` minted only
`search_products`; `regras de PI e itens cadastrados são PI` minted nothing.

## 2. Causal diagnosis (measured, not assumed)

Path inspected: query → `is_pure_concept_intent` →
`retrieve_eligible_actions` → `score_action` → ranking → candidate mint.

Root cause — **two-layer lexical coverage gap**, not a ranking bug:

1. `is_pure_concept_intent` only recognised *question-shaped* syntax
   (`quais são as normas`, `como funciona`, `existe uma norma`). Telegraphic
   document-seeking phrasing (`normas completas …`, `regras de PI …`,
   `padrão de descrição …`) fell through to generic lexical ranking.
2. The `read_governed_technical_knowledge` allowlist entry carried only
   generic aliases (`guia técnico`, `documentação técnica`, `technical
   guidance`, `governed knowledge`). Document-seeking vocabulary —
   `normas`, `regras`, `padrão`, `nomenclatura`, `codificação`, `manual`,
   `diretrizes`, `convenções` — scored **0.0** on the guidance capability,
   so it vanished from the candidate set while operational actions minted
   via entity-domain markers (`search_products` 0.9125 on `matérias
   primas`).

## 3. Minimal causal fix (declarative + generic)

Two changes, both language-level with **zero domain terms**:

1. `concept_intent_guard.py`
   - `_CONCEPT_ONLY_START` gained a telegraphic document-seeking pattern:
     optional consult verb (`consultar|buscar|leia|localize|procure|
     verifique`) + optional article/preposition + document vocabulary
     (`normas|regras|padrão|diretrizes|convenções|nomenclatura|documentação|
     manual|guia|codificação|descrição técnica|instruções técnicas`) at
     query start; plus EN equivalents. `quais são …` list extended with
     `documentação|manuais|codificação`.
   - `_MIXED_REQUEST` gained request verbs (`encontre|localize|procure|
     obtenha|retorne|exiba|apresente|find`) so compound questions stay
     eligible for both capability kinds instead of collapsing to one.
2. `davi_external_read_allowlist.json` — `read_governed_technical_knowledge`
   `semanticAliases` and `entityDomainMarkers` extended with the same
   document-seeking vocabulary (PT + EN). This is the capability's
   *declarative semantic description* — the legitimate channel for how the
   action presents itself to retrieval. No topic names, product terms or
   operationIds added.

No changes to ranking maths, thresholds, token minting, authorization,
corpus, or the MCP surface.

## 4. Results

### Discovery matrix (new test file `test_davi_discovery_knowledge_selection.py`, 27 cases)

- **D-family (15 documentary forms)** — all mint
  `read_governed_technical_knowledge` as the sole capability, including the
  two reported failures and telegraphic/verb-prefixed variants.
- **O-family** — `Me dê dois exemplos de terminal bala` top-1
  `search_products`; `Localize o produto de código 10080092`, `estoque
  disponível`, `O que é a SB1?` → operational top-1; guidance never forced.
- **C-family (4 compound forms)** — documentary capability minted alongside
  operational candidates within `top_k`.
- **N-family** — write intent and unsupported text still mint nothing.

### Baseline vs candidate benchmark (`davi-mcp-discovery-quality-001.json`, 230 cases)

| Metric | Baseline (pre-change) | Candidate |
|---|---|---|
| `top1_accuracy` | 0.9608 | 0.9608 |
| `top1_required_accuracy` | 0.9901 | 0.9901 |
| `top3_recall` | 0.9951 | 0.9951 |
| `top5_recall` | 1.0 | 1.0 |
| `hard_negative_leaks` | 0 | 0 |
| `known_failures` | 8 | 8 (same IDs) |

The 230-case quality corpus is **regression-free**: identical metrics and
the same 8 pre-existing known failures (alias collisions/quarantine
artifacts unrelated to this change). The documentary-selection improvement
is additive — the failure modes it fixes were not covered by that fixture
and are now covered by the 27-case selection matrix above.

### Suites

- New selection matrix: **27 passed**
- Focused (concept guard, command context, quality benchmark, inventory
  adjustment, read-only guard, real-user retrieval, V1/V2 knowledge,
  selection matrix): **224 passed**
- Broad DAVI selection (`-k 'davi or discovery or governed or allowlist or
  openapi'`): **1476 passed, 0 failed**

## 5. Preserved

- 2 MCP tools / 0 resources (unchanged); candidate-token flow untouched.
- Corpus V1/V2 integrity — no corpus, manifest, topic or content changes.
- `GUIDANCE != AUTHORIZATION`; backend AuthZ authoritative; guidance is
  untrusted document content.
- No domain/product/topic/provider hardcoding; no mandatory LLM; discovery
  stays deterministic and efficient.
