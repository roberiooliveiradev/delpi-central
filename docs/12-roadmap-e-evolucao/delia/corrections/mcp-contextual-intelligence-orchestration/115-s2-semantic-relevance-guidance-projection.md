# 115 — S2 Relevância semântica — projeção de guidance no terminal de descoberta

**Track:** `DELIA-C3-SELF-AWARENESS-FINITE-DELIVERY-01` / STEP=S2
**Plano:** [112](./112-self-awareness-finite-delivery-plan.md) ·
**Matriz:** [113](./113-s0-contract-freeze-and-responsibility-matrix.md)
**Autorização PO:** `f7b6a601cb3770a2e592989d0a83371b95bbfaf0`
**Diretriz vinculante:** doc 112 §9 (`645684d24b`)
**Status:** `IMPLEMENTED` — `INDEPENDENT_REVIEW_PENDING`

---

## 1. Escopo

Implementa **RQ-SA04** (relevância semântica D5) preservando
RQ-SA06/08/09. Gap tipado na S0: `SELECTION_EVIDENCE_CLASSIFICATION` —
a resposta correta ao pedido do usuário já era publicada pela
capability legítima (`get_catalog` carrega `displayFormatCatalog` +
`productGuide`), mas o payload chegava ao terminal zero-candidate e
rendia "não encontrei".

## 2. Achado factual (evidência de produção)

- `get_catalog` (VISTA, classe DISCOVERY) publica
  `displayFormatCatalog` + `productGuide` (índice de tópicos) +
  metadados de capability — sem chave `candidates`.
- O fluxo DISCOVERY sem `candidates` caía em
  `_render_zero_candidate_discovery` → declara miss, ignorando o
  conteúdo-guia presente no mesmo payload.
- `get_product_guide` (READ) já entrega documentação específica por
  tópico (`display_formats`, `block_types`), projetada
  nativamente pelas famílias de guidance existentes
  (`use_when`→when, `how_to_use`→steps, `summary`→objective).

## 3. Decisão (reuse gate)

**EXISTING_EQUIVALENT=YES · REUSE_DECISION=EXTEND.** Nenhum engine,
catálogo paralelo ou branch por provider.

| Peça | Decisão |
|---|---|
| Famílias `_GUIDANCE_SECTION_FAMILIES` | EXTEND — `productguide`/`guideindex`→objective; `displayformat`/`formats`→criteria (vocabulário já previa `displayformats`/`formatos`) |
| Terminal zero-candidate em `attempt()` | EXTEND — antes de declarar miss, projeta seções de guidance do payload via `_deterministic_guidance_content`/`_select_guidance_records` existentes |
| Instruções de seleção (2×) | EXTEND — pedido de documentação owner (formatos/guias) prefere capability não-mutante que anuncia documentação ao invés do catálogo de operações |

## 4. Contrato preservado

- `_CAPABILITY_VOCABULARY_KEYS` segue excluindo
  `displayformatcatalog`/`productguide` dos **records de negócio**
  (RC1/RC2 intacto) — eles só aparecem via projeção de guidance,
  que é o seu papel declarado pelo owner.
- Sem projeção de guidance ⇒ o terminal miss permanece honesto
  (comportamento anterior preservado).
- `selection-only`, `MODEL_AUTHORED_FACTUAL_PROSE=NONE`,
  PREPARE/ACT, AuthZ, 60/3/300 — inalterados.
- Nenhum vocabulário por especialista; as chaves novas são nomes
  publicados pelo payload owner (contrato observado, não inventado).

## 5. Evidência

- **RED**: `tests/test_c3_self_awareness_relevance.py` — 6 testes
  reproduziam a mensagem D5 de produção ("não encontrei ... catálogo")
  para payload com `displayFormatCatalog`/`productGuide`.
- **GREEN**: 6/6 após a projeção; conteúdo renderizado contém os
  formatos reais e o índice de tópicos do owner (verificado por
  inspeção do texto, não apenas status).
- Negativos: payload sem guidance ⇒ miss declarada; descrições de
  capability seguem fora dos records; nenhum candidato inventado.
- **Regressão**: suíte backend completa verde no HEAD com S1+S2+S3.

## 6. Resíduos

- Seleção entre `get_catalog` e `get_product_guide` depende da
  descrição owner — VISTA anuncia formatos em ambas; a projeção
  funciona em qualquer dos dois caminhos (idempotente por desenho).
- `INDEPENDENT_REVIEW_PENDING`.
