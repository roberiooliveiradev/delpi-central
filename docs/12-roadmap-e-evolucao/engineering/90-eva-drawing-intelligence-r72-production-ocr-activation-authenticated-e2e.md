# 90 — EVA Drawing Intelligence R7.2: Governed Production OCR Activation, Model Provisioning & Real Runtime Evidence

**Status:** OCR ATIVO em produção (flag + imagem extras + modelos provisionados) + **execução real comprovada no runtime produtivo** — E2E via MCP ainda `TEST_NOT_RUN` (sem sessão OAuth consumidora). **Data:** 2026-11-01.

## 1. Reanchor / runtime truth (A01/A02)

Clone isolado `~/delpi-r711`; SHAs: compose opt-in `08f5537a68`, fix imagem `53a1f69d85`→push `2f135255c3`, merge prod `598eb5223d`+posteriores. Host srv-api: 23GB RAM (~4GB disponível — headroom justo; semaphore=1 protege), 16 CPU, disco 28G livre.

## 2. Imagem & modelos (A04/A05/A07)

- `engineering-api` build `INSTALL_VISION_EXTRAS=true` (opt-in via .env). Fix aplicado: `libgomp1+libglib2.0-0` + `--force-reinstall --no-deps opencv-python-headless==4.10.0.84` (deps do paddle arrastavam `opencv-python` → `libGL.so.1` break; headless reimposto).
- Modelos provisionados em `~/ocr-models` → montado `:ro` em `/opt/ocr-models` (novo volume); `ENG_DRAWING_OCR_MODEL_DIR=/opt/ocr-models`. SHA-256 verificados: det `183146fe…24d2d`, rec `3ec8a97e…f66b`. Sem download implícito; sem modelos no Git.
- Verificado no container: `cv2 4.10.0`, `paddle 3.2.2` importam; env correto.

## 3. Autorização experimental (A03)

Não existe permissão dedicada `engineering.drawing_benchmark` no Core (confirmado; não inventada). Mecanismo aprovado e restritivo vigente = `ENG_DRAWING_OCR_BENCHMARK_ENABLED` (flag própria, além do master) **+** requisitos existentes no bridge: principal humano + `engineering.access` + identidade delegada ao acervo. Flag ligada somente após deps/modelos/isolamento/rollback verificados.

## 4. Execução real no runtime produtivo (evidência central)

`docker exec delpi-engineering-api` → `run_pipeline_isolated` (mesmo path do MCP):

| Documento | sha | pipeline | status | tokens | chars | ms | mem_peak |
|---|---|---|---|---|---|---|---|
| `90264302.pdf` oficial | f33447b2…f0ef ✓ 103498B | pdfium_render_paddleocr | **ok** | 92 | 762 | 21.203 | 2.806.044 KB |
| `10210267-2.pdf` escaneado | 43b2cd6f… 51944B | pdfium_render_paddleocr | **ok** | 58 | 463 | 10.977 | — |
| idem | | pdfium_render_opencv_paddleocr | **ok** | 68 | 453 | 10.947 | — |

Resultados idênticos ao baseline offline R7 — sem divergência. Isolamento `subprocess`, `worker_rc=0`, RLIMIT_AS=12288MB, semáforo=1.

## 5. E2E MCP — estado honesto

`TEST_NOT_RUN`: chamada MCP exige JWT de usuário produtivo com `engineering.access` — o executor não possui sessão OAuth. Com flag ON + modelos + isolamento + deps comprovados, a cadeia está pronta: qualquer identidade autorizada que chamar `analyze(product.drawing_benchmark)` com `approved_local_visual_ocr` executará o mesmo `run_pipeline_isolated` comprovado acima. Não contornei AuthZ nem fabriquei JWT.

## 6. Segurança / rollback (A17/A19)

Sem JWT no worker, sem URL/path de acervo no request, hash validado, sem persistência integral, sem SaaS egress (modelos provisionados, `DISABLE_MODEL_SOURCE_CHECK`), sem writes. Kill switch: remover/`ENG_DRAWING_OCR_BENCHMARK_ENABLED=` + `up -d` → `feature_disabled` imediato; rollback de imagem = rebuild com `INSTALL_VISION_EXTRAS=false`. Recursos: semáforo=1 + cap 12GB virtual + SIGKILL timeout já testados.

## 7. Residuais

1. E2E autenticado (sessão OAuth) — único passo restante para PASS completo.
2. RAM disponível ~4GB vs pico ~2,8GB — headroom justo; monitorar; worker dedicado se uso crescer (`ARCHITECTURE_DECISION_REQUIRED`).
3. Corpus ampliado via `/products/drawings` (contrato existe; campanha separada).
4. Permissão dedicada `engineering.drawing_benchmark` no Core — decisão owner pendente.
