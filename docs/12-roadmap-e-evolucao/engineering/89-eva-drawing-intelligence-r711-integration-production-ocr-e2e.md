# 89 — EVA Drawing Intelligence R7.1.1: Git Integration Recovery, Isolated OCR Production Deployment & Memory-Limit Correction

**Status:** INTEGRATED + DEPLOYED (código em prod com flag OCR off) — E2E autenticado `TEST_NOT_RUN` (sem sessão OAuth consumidora). **Data:** 2026-11-01. **SHAs:** `8147c89ec6` (R7.1 integrado por terceiro), `159d74b883` (correção de memória), merge prod `f044714fc3`, doc commit `ver abaixo`.

## 1. Reconciliação Git (I02/I03/I16)

- Os commits locais reportados na R7.1 (`f7817c33e7`, `5a1175d1e7`) não constam como SHAs em `origin/main`, porém o commit `8147c89ec6` (mesmo título/escopo) já integrou **conteúdo idêntico**: diff arquivo-a-arquivo local × remoto = vazio em `subprocess_executor.py`, `visual_worker.py`, `test_ocr_isolation_r71.py` e doc 88. **Nenhum trabalho legítimo perdido; nada a re-aplicar** — matriz de reconciliação = keep em todos os componentes.
- Workspace isolado utilizado: clone limpo `~/delpi-r711` (a árvore compartilhada permaneceu contaminada com dezenas de modificações não-commitadas de agentes concorrentes — stash/commit-alheio proibidos, não necessários).
- Push do clone: `159d74b883` em `origin/main` (fix de memória + compose).
- Deploy canônico: `git merge origin/main` no repo prod (padrão local-merge estabelecido) → `f044714fc3` → `./infra/scripts/up-prod-sequential.sh --build engineering-api` → `delpi-engineering-api Up (healthy)`.

## 2. Correção de memória — gate I06 (alta prioridade)

Medição real (venv py3.12, modelos provisionados, PDF oficial 90264302):

| Métrica | Valor |
|---|---|
| VmPeak (virtual) | **8,65 GB** (9 066 484 KB) |
| VmHWM (pico RSS) | **2,86 GB** (2 997 116 KB) |
| OCR | 92 tokens / 762 chars — igual à R7 |

`RLIMIT_AS=3072MB` **mataria a execução real** — o cap limita espaço de endereçamento virtual, não RSS. Correção: default `ENG_DRAWING_OCR_MAX_RSS_MB` 3072→**12288MB** (bounds 512–16384, medição + ~40% headroom) + compose prod. Prova real: `run_pipeline_isolated(pdfium_render_paddleocr)` sob cap 12GB → `status=ok`, `worker_rc=0`, `memory_peak_kb≈2 997 624`, 19,6s.

## 3. Isolamento e segurança revalidados

Timeout → SIGKILL no process group + reap verificado (PID morto), semáforo concorrência=1, `document_hash_mismatch` rejeitado, request sem JWT/URL/path de acervo/secrets, modelos somente via `ENG_DRAWING_OCR_MODEL_DIR` (vazio em prod → `model_not_provisioned` honesto), extras visuais fora da imagem prod (`INSTALL_VISION_EXTRAS=false`). Testes no clone: 9/9 isolation + 97 focused R7 — verde.

## 4. Runtime produtivo verificado

`delpi-engineering-api` `Up (healthy)`; módulo carrega `_limits()={max_rss_mb:12288, cpu_seconds:300, max_concurrency:1}`; `ENG_DRAWING_OCR_BENCHMARK_ENABLED=` (vazio — off, fail-closed); `ENG_DRAWING_BENCHMARK_ENABLED=true`; `ENG_DRAWING_OCR_ISOLATION=subprocess`; `ENG_DRAWING_OCR_MODEL_DIR=` (vazio); 6 tools MCP; `drawing_analysis` intocada. Kill switch: flag vazia = off; rollback = flag + rebuild SHA anterior.

## 5. E2E autenticado — estado honesto

`TEST_NOT_RUN`: o executor não possui JWT de usuário produtivo (realm prod exige credencial humana que não está disponível; realm dev "rober" existe, porém o acervo dev está vazio — seed controlado documentado como próximo passo). PaddleOCR não está instalado na imagem prod por decisão de isolamento (extras opt-in) — o perfil visual retornaria `feature_disabled`/`provider_unavailable` honesto até completar a cadeia de gates: imagem com extras + modelos provisionados + flag + sessão autorizada. Cadeia registrada aqui, não contornada.

## 6. Inventário do acervo

Contrato vigente confirmado: `GET /products/drawings` (api-delpi, RBAC `ENGINEERING_LMP_ACCESS`, paginação ≤500, filtros code/file_kind/revision/variant/size/datas). Acervo real medido offline: **4.833 PDFs** (mapeamento X: autorizado do operador). Corpus R7 (offline): 90264302 (vetorial+BOM+cotas), 10210267-2 (escaneado), 90263554 (18p), 90262471 Inspecao, ETIQUETA.

## 7. Residuais

1. E2E autenticado `approved_local_visual_ocr` — requer sessão OAuth + imagem com extras + modelos provisionados + flag (owner).
2. Corpus autenticado via API; seed de acervo em dev como alternativa de homologação.
3. Worker dedicado se volume justificar — `ARCHITECTURE_DECISION_REQUIRED`.
4. Permissão dedicada `engineering.drawing_benchmark` no Core — decisão owner pendente.
5. Avaliação ampliada do acervo = campanha governada separada (etapas A–D).
