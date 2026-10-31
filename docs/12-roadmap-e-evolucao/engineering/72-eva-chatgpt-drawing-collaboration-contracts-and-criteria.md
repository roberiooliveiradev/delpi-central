# 72 — EVA — Collaborative Drawing Analysis: Contracts & Criteria (doc 71 G1)

**Status:** CONTRACTS PUBLISHED. **Data:** 2026-10-31. **Autoridade:** doc 71 (master). **Baseline:** `00fc7d8d0b`.

## 1. `DrawingVisualObservation` (entrada NÃO confiável)

Fonte: percepção visual do ChatGPT sobre o desenho na conversa. Schema estrito — campos fora do contrato são rejeitados (`invalid_visual_observation`).

| Campo | Tipo | Limite | Notas |
|---|---|---|---|
| `observation_id` | string | 80c | gerado `VO-###` se ausente; unicidade forçada |
| `kind` | enum | — | `text|dimension|material|note|bom_item|symbol|legibility|revision|identification|other` |
| `raw_observation` | string (req) | 500c | texto observado (untrusted) |
| `normalized_value` | string | 500c | valor normalizado pelo consumidor |
| `unit` | string | 12c | PC/UN/MM/… |
| `page` | int 1–999 | — | página da evidência |
| `view_or_region` | string | 120c | vista/região textual |
| `confidence` | enum | — | `low|medium|high` (inválido→`low`) |
| `uncertainty_reason` | string | 500c | motivo da incerteza |
| `is_hypothesis` | bool | — | hipótese explícita |
| `document_identity` | obj | — | `{source, document_ref, document_hash, revision, product_code}` |

`capture_method` é sempre `chatgpt_visual` (servidor fixa). Limites: `MAX_OBSERVATIONS=50`, `MAX_TEXT_LEN=500`. Campos desconhecidos → erro.

## 2. Comparabilidade de fontes (`SourceMatch`)

`same_document_verified` — hash idêntico OU (product_code + revision + document_ref iguais).
`possible_match` — product_code igual e sem evidência de revisão distinta.
`different_document` — revisão explícita divergente OU hash divergente OU código divergente.
`unknown` — dados insuficientes.
Regra: código de produto sozinho nunca verifica identidade; revisão distinta nunca é mesma fonte.

## 3. `analyze(product.drawing_analysis)` — entrada evoluída (v2, backward-compatible)

`product_code` (obrigatório, mantido) + `visual_observations[]` (opcional, schema §1) + `scope[]` (opcional, ≤20 labels). Proibido: SQL, URL, path, anexo cru. Produto/desenhos/BOM só por contrato oficial com identidade delegada.

## 4. `DrawingComparisonReport` (resposta)

`contract_version="drawing_analysis.v2"`, `identification`, `executive_summary`, `verifications[]`, `findings[]`, `visual_observations[]` (normalizadas), `comparison_results[]` (`vs_text_layer`, `vs_official` por observação), `source_match`, `audit` (sha256, fontes, writes=0), `status=DRAFT`, `human_review_required`.

Erros tipados: `invalid_visual_observation`, `product_not_found`, `drawing_not_found`, `drawing_pdf_unavailable`, `pdf_extraction_failed`, `not_implemented`, `validation`.

## 5. Conhecimento (`knowledge` topic `product.drawing_criteria` v1.1)

7 regras tipadas (`rule_id/owner/source/version/applicability/criterion/evidence_required/severity/limitations`): MP-GROUP-STRUCTURE, MP-COLOR-ABBREV, PI-50XX-SEGMENTS, PI-ISOLATION-CODES, DRAW-EVIDENCE-NOT-FACT, DRAW-REV-MATCH, DRAW-NO-PA-NORM. Sem norma PA, roteiro SG2 ou inspeção — `NOT_CHECKED/OWNER_BLOCKED` explícito.
