# 70 — EVA — Drawing Intelligence E1–E3: Implementation, Grounding, Evaluation, Security & Production Evidence

**Status:** IMPLEMENTED + DEPLOYED (produção, engineering-api rebuild). **Data:** 2026-10-31.
**Baseline:** doc 69 (`e3bb05f444`) → **SHA final main:** `9397a35461` (code `a86c2b61f1`).

## 1. Decisão do Contract Gate (E1.0)

- **Owner do serviço neutro:** `engineering-api` — bounded context dono da EVA e da delegation oficial para api-delpi; nenhum novo microsserviço criado.
- **Sem dependência runtime do Chat IA legado:** conceitos (pipeline, evidência por página, honestidade de incerteza, modelo de relatório) extraídos para módulo neutro `engineering_app/{domain,application}/drawing/` — código próprio, nenhum import de `minha-delpi-ai-api`.
- **Entrada v1:** somente `product_code` — desenho oficial do acervo. Anexos do consumidor (ChatGPT MCP) **não têm transporte contratual comprovado** → não simulado; fluxo de upload via Portal = decisão de produto pendente (documentado como limitação, não feature).
- **OCR/VLM:** adapters explicitamente fora do v1 — extração determinística da camada de texto (pypdf). PDF escaneado → `INCONCLUSIVE`, nunca texto fabricado.

## 2. Implementado

| Componente | Arquivo | Conteúdo |
|---|---|---|
| Modelo canônico | `domain/drawing/models.py` | `DrawingEvidence`, `Finding`, `Verification`, `DrawingAnalysisReport` — dataclasses puros (domain sem pydantic — purity test), enums `OBSERVED/CALCULATED/INFERRED/UNKNOWN`, `PASS/FAIL/WARNING/INCONCLUSIVE/NOT_APPLICABLE/NOT_CHECKED`, `DRAFT/CANDIDATE` |
| Adapter extração | `application/drawing/pdf_text_extractor.py` | pypdf; caps 15MB/30págs/60k chars; assinatura `%PDF-`; criptografia rejeitada; scanned→limitation explícita |
| Evidências | `application/drawing/drawing_evidence_extractor.py` | regex determinística: códigos 8d, revisão, qty+UM, item-row candidates (INFERRED/low), notas, materiais — sempre por página |
| Regras MP/PI | `application/drawing/description_rules.py` | MP 1001–1025 (prefixo↔grupo, cores abreviadas) + PI 50xx (isolação CA–CV, cor 4L, comprimento) — estrutural apenas, sem norma inventada |
| Orquestração | `application/drawing/drawing_analysis_service.py` | detail+structure+drawing(+pdf) via gateway delegado → 11 verificações + achados + relatório DRAFT com hash SHA-256 e auditoria |
| EVA | `semantic_registry.py`, `semantic_bridge.py`, `server.py` | `analysis_type=product.drawing_analysis` na tool `analyze` — 6 tools preservadas |

## 3. Verificações implementadas (honestas)

legibility, product_identification, revision (desenho×cadastro), bom_comparison (presença textual — indício, nunca divergência comprovada), mp_description + pi_description (raiz), mp_items + pi_items (BOM), technical_notes, units_dimensions, material_hints; **NOT_CHECKED honesto:** routing (SG2 sem contrato), inspection (contrato não inventariado), pa_description (sem norma autorizada).

## 4. Segurança

Identidade delegada em todas as consultas (`access_token` do chamador via `_source_context`); sem SQL/URL/path arbitrário (só `product_code`); MIME real + caps; texto extraído é dado não confiável — pipeline determinístico sem LLM → prompt-injection-immune por construção; zero writes; relatório `DRAFT` com `human_review_required`.

## 5. Testes (SHA final)

`tests/test_drawing_analysis.py` — 16 testes: contrato de extração (vazio/oversize/não-PDF/PDF real parseado por pypdf), evidência por página+classificação, regras MP/PI, orquestração happy-path com source fake, erros `product_not_found`/`drawing_not_found`, paridade registry. **Suite completa: 507 passed, 0 failed** (inclui architecture purity e paridade semântica existentes).

## 6. Deploy e smoke produtivo

- Push `feat/engineering-products-e2e:main` (rebase ff) → `origin/main=9397a35461`.
- Prod `operador@192.168.1.237`: `git merge origin/main` (repo prod divergido — ff impossível, histórico conhecido) → `up-prod-sequential.sh --build engineering-api` → `delpi-engineering-api Up (healthy)`.
- Smoke verificado: `pypdf 5.9.0` no container; `product.drawing_analysis` presente em `SEMANTIC_ACTIONS` em produção; `/v1/health` 401 auth-gated.
- **Rollback:** checkout do SHA anterior + rebuild `engineering-api`.

## 7. Limitações e residuais

1. **E2E consumidor MCP/ChatGPT não executado** (exige sessão OAuth real do consumidor) — `TEST_NOT_RUN`, não simulado.
2. **Extração texto-only** — escaneados/OCR/VLM/coordenadas de região: FEATURE_GATED pending (adapter + provider + evals).
3. **Anexo via MCP** — transporte não comprovado; upload via Portal pendente de decisão de produto.
4. **SG2 roteiro / inspeção / norma PA** — OWNER_BLOCKED por contrato (doc 69 §17).
5. Ground truth ONDA14 existe no legado como scripts — portabilidade para corpus de evals EVA = próximo passo (métricas precision/FP/FN ainda não homologadas).

## 8. Matriz EVA-DRAW-01..32

- **PASS:** 01–05, 07, 09–12, 13–14 (parcial estrutural — honesto), 15 (normas referenciadas com fonte), 16–21, 24, 28–29, 31–32.
- **PENDING/FEATURE_GATED:** 06 (anexos sem contrato), 08 (OCR/VLM não provisionados), 26–27 (Portal/ChatGPT não integrados nesta entrega).
- **TEST_NOT_RUN:** 25 (E2E PDF real em sessão MCP), 22–23 (ground truth/metrics pendentes de corpus aprovado).
- **OWNER_BLOCKED:** roteiro/inspeção/PA (dentro de 15/16 como NOT_CHECKED).
- Nenhum critério declarado PASS sem evidência; análise produtiva qualificada como `CODE_READY` — homologação de qualidade depende do corpus E4.
