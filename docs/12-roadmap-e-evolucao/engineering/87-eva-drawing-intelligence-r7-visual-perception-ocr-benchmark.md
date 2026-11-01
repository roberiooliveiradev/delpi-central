# 87 — EVA Drawing Intelligence R7: Visual Perception, PDFium Rendering, OpenCV/PaddleOCR & Real Technical Drawing Benchmark

**Status:** IMPLEMENTED + REAL-PDF BENCHMARKED (local, bytes oficiais verificados) — deploy prod experimental OWNER_BLOCKED (sem sessão SSH/OAuth no executor). **Data:** 2026-11-01. **SHA base:** `d9282bd48a` (main).

## 1. Abstraction Gate (R7-02/03)

Contratos neutros **já existiam** em `application/drawing/extraction_ports.py` — reutilizados, nenhuma arquitetura paralela criada:

- `PdfRenderingPort` → `PdfiumExtractionAdapter.render_page` (existente; endurecido R7-04: rotação, dimensão em pontos, `scale=dpi/72`, `coordinate_system`).
- `OcrExtractionPort` → **novo** `PaddleOcrAdapter` (infrastructure/extraction).
- `ImagePreprocessingPort` → **novo** `OpencvPreprocessingAdapter`; port refinado para retornar `PreprocessResult` (profile + `ops_applied` + dims — rastreabilidade, nunca op-chain livre). Não havia implementação prévia → refinamento seguro.
- `OcrResult.metadata` (aditivo): engine/versões/model_source/device/lang/coordinate_system/timeout.
- Modelo `VisualEvidence` conceitual mapeado no `spatial_evidence.token_sample[]`: page, raw/normalized_text, confidence, `bounding_box_px`, `bounding_box_normalized`, `bounding_box_pdf_points` + `pdf_transform`, provider+versão+extraction_method.
- Invariante reforçada em `test_architecture.py`: `cv2|paddleocr|paddle|numpy` proibidos fora de `infrastructure/extraction`.

## 2. Adapters & governança (R7-05/06/07)

| Adapter | Versão | Licença | Governança |
|---|---|---|---|
| `opencv-python-headless` | 4.10.0.84 | Apache-2.0 | profiles fechados `raw_render`/`grayscale`/`adaptive_threshold`; limites 40MB/40MPx |
| `paddlepaddle` | 3.2.2 | Apache-2.0 | CPU-only; `DISABLE_MODEL_SOURCE_CHECK`; timeout 120s (piso 5/teto 600) |
| `paddleocr` | 3.3.0 | Apache-2.0 | `ENG_DRAWING_OCR_MODEL_DIR` (provisionado) **ou** `ENG_DRAWING_OCR_ALLOW_MODEL_DOWNLOAD=true` (só dev); ausente → `model_not_provisioned`, **nunca download implícito** |

Modelos usados no benchmark (paddlex official, cache local): `PP-OCRv5_server_det` (sha256 `183146fe…24d2d`) + `en_PP-OCRv5_mobile_rec` (sha256 `3ec8a97e…f66b`), 93MB — prod exige provisionamento via `ENG_DRAWING_OCR_MODEL_DIR` com processo aprovado/checksum.

**Isolamento (R7-07):** OCR ~9–97s/documento e pico RSS ~3.7GB observados — **~1000× mais caro que extração textual**. Profile `approved_local_visual_ocr` exige `ENG_DRAWING_BENCHMARK_ENABLED` **+** `ENG_DRAWING_OCR_BENCHMARK_ENABLED` (default OFF em dev e prod); extras fora do requirements principal → `requirements-vision.txt` + `Dockerfile ARG INSTALL_VISION_EXTRAS` (default false). ARCHITECTURE_DECISION_REQUIRED: worker/subprocess dedicado se o perfil for promovido.

## 3. Residual R6-D.2 corrigido (R7-16)

Mensagem fixa `"providers experimentais não executam"` removida → `_benchmark_limitations(runs)` deriva limitações do status real (erro → motivo; parcial → cobertura; ok+limitações → por provider). Teste de regressão impede contradição `status=ok` × `não executou`.

## 4. Benchmark real — `90264302.pdf` (bytes oficiais)

- Fonte: acervo oficial FILESERVER `X:\DESENHOS DELPI EM PDF` via mapeamento autorizado do operador (mesma identidade/escopo que a api-delpi serve). SHA-256 `f33447b2…f0ef`, 103498 B, 1 página — **idêntico ao baseline R6-D.2**.
- Mesmos bytes para os 6 motores; documento não versionado no repo.

| Provider | status | chars | tokens | ms | cobertura campos (9) |
|---|---|---|---|---|---|
| pypdf | ok | 234 | – | 16 | 4/9 |
| pdfplumber | ok | 255 | – | 36 | 4/9 |
| PDFium text | ok | 263 | – | 2 | 4/9 |
| PDFium→PaddleOCR | ok | 762 | 92 | 31.246 | **9/9** |
| PDFium→OpenCV(adaptive)→OCR | ok | 753 | 90 | 29.923 | **9/9** |
| PDFium→OpenCV(gray)→OCR | ok | 764 | 94 | 19.155 | **9/9** |

**Campos recuperados SOMENTE por OCR:** `663` (cota 663±2), `50226113`, `50226114`, `10020033`, `10080106` — presentes na tabela BOM/cotas do desenho mas **invisíveis à camada de texto** (texto vetorial/CAD não exposto aos extratores). Dedup conservador (página+texto normalizado exato): 70 textos únicos, 56 duplicados entre pipelines.

## 5. Ground truth visual (R7-11) — inspeção autorizada do render

Inspeção visual do render 150dpi por este executor: **todos os 9 campos são `VISIBLE_CONFIRMED`** — `90264302`/`18702881`/`10013396831` (carimbo), `643`/`663` (cotas ±2 em vermelho), `50226113`/`50226114`/`10020033`/`10080106` (tabela BOM embutida). O alerta R6-D.2 ("PI/MP podem estar só na BOM") está **refutado para este desenho**: os códigos estão no desenho — a falha era da camada textual, não do documento. `OCR_TEXT_FOUND ≠ DIMENSION_ASSOCIATION_VERIFIED`.

## 6. Corpus adicional autorizado (R7-10)

| Documento | sha256[:16] | bytes | pág. | tipo (evidência) | texto (chars) | OCR (chars) |
|---|---|---|---|---|---|---|
| `10210267-2.pdf` | 43b2cd6f | 51.944 | 1 | **escaneado** (text layer vazia) | 0/0/0 | **463/453** |
| `90262471 Inspecao.pdf` | a884243c | 3.283 | 1 | vetorial esparso | 87/90/91 | 87/89 |
| `90263554.pdf` | 89f9b4d5 | 6.202.644 | **18** | vetorial multipágina | 8296/9773/9777 | 4282/8675 (partial: limite 5p) |
| `ETIQUETA.pdf` | 5c77141c | 2.003 | 1 | quase sem texto | 19/21/22 | 22/21 |

OCR em documento escaneado foi o **único** método a produzir conteúdo. `partial` honesto no multipágina (limite governado de 5 renders).

## 7. Segurança / fail-closed (R7-18)

Coberto por testes: flag-off → `feature_disabled`; perfil desconhecido → `provider_profile_not_allowed`; perfil OCR exige flag própria; providers experimentais exigem `allow_experimental`; `unknown_pipeline|kind|provider` tipados; `empty/oversize/unreadable` input; `model_not_provisioned`; `page_out_of_bounds`/`dpi_limit`; timeout bounded (5–600s); sem path/URL externos (só bytes); sem JWT fabricado; `_tokens_sample`/`_text_blob` stripped no JSONL; sem imagem integral na resposta.
**Residual honesto:** paddlex emite probe de conectividade aos hosters de modelo no init (sem conteúdo do documento) — em prod recomenda-se egress deny + `ENG_DRAWING_OCR_MODEL_DIR` provisionado.

## 8. Qualidade / métricas

Cobertura medida acima; precision/recall/CER/WER permanecem `metric_not_available` (sem ground truth aprovado por Engenharia). `memory_peak_kb` reportado como pico RSS best-effort. Confiança OCR não é confiança técnica.

## 9. Recomendação fundamentada (R7-23)

**Mecanismo híbrido governado**: (a) manter extração textual como camada primária (ms, gratuita); (b) OCR local como **fallback condicional** quando `text_chars` baixo/escaneado OU para regiões BOM/cotas quando field-coverage divergir — evidência em 90264302 (5/9 campos só-OCR) e 10210267-2 (única via); (c) preprocess `adaptive_threshold` teve ganho real no multipágina (8675 vs 4282 chars) mas neutro no desenho simples — manter profile duplo só se corpus ampliado confirmar; (d) associação número↔geometria/cota exige etapa posterior (layout/multimodal) — não implementada aqui. **Custo:** ~20–90s/doc CPU + ~1GB+ imagem + ~3.7GB pico RAM + modelos provisionados → worker isolado + flag, nunca hot-path produtivo.

## 10. Testes / deploy

- Suite engineering-api: **579→601 passed / 0 failed** (28 testes R7 novos + regressões). Dockerfile build verificado (`INSTALL_VISION_EXTRAS=false` default).
- E2E autenticado via MCP: `TEST_NOT_RUN` — executor sem sessão OAuth consumidora.
- Deploy prod: `OWNER_BLOCKED` — SSH operator indisponível neste executor; além disso extras/flag/modelos exigem decisão de infraestrutura (imagem ~+1GB). Kill switch pronto: `ENG_DRAWING_OCR_BENCHMARK_ENABLED` ausente/vazio = off.

## 11. Matriz R7-01..32

PASS: 01–12, 14–20, 22–26, 31, 32 (authorities, abstraction, contratos, render, OpenCV, PaddleOCR, versões rastreáveis, isolamento desenhado, limites, perfil governado, PDF oficial legítimo, mesmo documento, benchmark real, matriz real, visibilidade classificada, coordenadas, dedup, residual corrigido, regressão drawing_analysis, 6 tools MCP, zero legadas, fail-closed, zero escrita, testes no SHA, nenhuma precisão inventada, recomendação fundamentada).
TEST_NOT_RUN: 28 (E2E autenticado — sem sessão). OWNER_BLOCKED: 27 (deploy experimental — SSH + decisão infra/owner). PENDING com honestidade: 13 parcial (PDF oficial acessado via acervo autorizado, não via MCP delegado), 21 parcial (smoke MCP idem), 29 (kill switch documentado, rollback = flag off; rebuild prod não executado), 30 doc publicado neste commit. 09: probe de conectividade paddlex no init (dev) — sem egress de conteúdo; mitigação registrada.

## 12. Residuais / próxima etapa

1. E2E autenticado `analyze(product.drawing_benchmark)` perfil `approved_local_visual_ocr` por consumidor autorizado.
2. Decisão owner: build com extras + volume de modelos provisionados + worker isolado antes de qualquer uso produtivo.
3. Associação geométrica cota↔elemento (DIMENSION_ASSOCIATION_VERIFIED) — etapa de inteligência separada.
4. Corpus ampliado + ground truth por Engenharia → métricas de qualidade reais.
5. Timeout OCR: thread não é matável — para hard-isolation avaliar subprocess/executor dedicado.
