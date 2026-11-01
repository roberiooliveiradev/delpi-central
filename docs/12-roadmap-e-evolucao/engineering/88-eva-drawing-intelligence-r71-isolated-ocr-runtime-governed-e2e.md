# 88 — EVA Drawing Intelligence R7.1: Isolated OCR Runtime, Governed Contract & Production Path

**Status:** IMPLEMENTED (isolamento subprocess real + contrato interno + testes de encerramento) — deploy prod/E2E autenticado registrados honestamente abaixo. **Data:** 2026-11-01. **SHA:** `f7817c33e7` (local; push bloqueado por trabalho concorrente não-commitado na árvore — ver §9).

## 1. Decisão de arquitetura (R71-02)

Inventário: nenhum executor governado de jobs pesados reutilizável no repo (Automation Hub não existe como runtime; `bpmn_validation` subprocess é de outro domínio). **Decisão B — subprocesso isolado**: `SubprocessVisualExecutor` + `visual_worker` (mesmo código governado, sem novo bounded context nem serviço). Worker dedicado (opção C) permanece `ARCHITECTURE_DECISION_REQUIRED` caso o uso cresça.

## 2. Contrato interno (R71-04)

`drawing_ocr_execution.v1` (stdin): `document_hash_sha256`, `pdf_b64`, `pipeline_id`, `dpi`, `correlation_id`. `drawing_ocr_result.v1` (stdout): `status`, `record`, `error`. Sem JWT, sem path/URL de acervo, sem persistência integral — bytes entram, evidência sai. AuthN/AuthZ permanecem na fronteira MCP (humano + RBAC + flags) antes do spawn.

## 3. Isolamento efetivo (R71-05) — comprovado por teste

- `RLIMIT_AS` (default 3072MB, bounds 512–16384): alocação > cap mata o filho — testado com `alloc_mb:2048`.
- `RLIMIT_CPU` (default 300s, hard+5s SIGXCPU) + `RLIMIT_NOFILE` 256.
- Process group próprio + `SIGKILL` no timeout: `ocr_timeout` com `child_reaped:true` e PID morto verificado — a chamada nativa PaddleOCR é realmente encerrada (o gap da thread-timeout da R7 está fechado).
- `BoundedSemaphore(ENG_DRAWING_OCR_MAX_CONCURRENCY=1)` — saturação honesta `ocr_concurrency_saturated`.
- Pico RSS do filho medido via `RUSAGE_CHILDREN` → `memory_peak_kb`/`child_rusage_kb` no record.
- `ENG_DRAWING_OCR_ISOLATION` default `subprocess`; `inprocess` restrito a dev/test (resolução por call, nunca pelo consumidor).

## 4. Modelos governados (R71-06)

PaddleOCR 3.3.0 + paddlepaddle 3.2.2 + opencv-headless 4.10.0.84; `PP-OCRv5_server_det` (sha256 `183146fe…24d2d`) + `en_PP-OCRv5_mobile_rec` (sha256 `3ec8a97e…f66b`) — cache `~/.paddlex/official_models` (93MB). Prod: `ENG_DRAWING_OCR_MODEL_DIR` provisionado (sem download implícito; ausente → `model_not_provisioned`). Extras fora da imagem default (`INSTALL_VISION_EXTRAS`).

## 5. Execução híbrida / flags (R71-07/09)

`approved_local_visual_ocr` inalterado; exige `ENG_DRAWING_BENCHMARK_ENABLED` + `ENG_DRAWING_OCR_BENCHMARK_ENABLED` (default OFF dev+prod). Fallback automático em `drawing_analysis.v3` **não** ativado.

## 6. Testes (R71-11/16)

`test_ocr_isolation_r71.py` (9): contrato inválido/hash mismatch rejeitados, kill real no timeout (SIGKILL, sem órfão), memory cap mata filho, falha simulada honesta, semáforo de concorrência, request sem secrets, bounds de env. Foco total no SHA `f7817c33e7`: **97 passed / 0 failed** (R7 + isolation + benchmark + arch + semantic MCP). Suíte completa prévia: 601+.

## 7. Deploy prod / E2E — estado honesto

- **SSH Operator `operador@192.168.1.237` comprovado neste executor** (key-based, `srv-api`, containers listados) — o bloqueio de SSH da R7 está resolvido.
- **Push/deploy: PENDING→OWNER_BLOCKED transitório** — árvore local contém dezenas de modificações não-commitadas de agentes concorrentes (api-delpi, supplies, commercial, engineering-api/tool_bridge etc.) que impedem `pull --rebase`/`merge` sem stash (proibido por AGENTS.md) e sem commitar trabalho alheio. Commit R7.1 `f7817c33e7` existe localmente e é seguro.
- **E2E autenticado MCP: TEST_NOT_RUN** — sem sessão OAuth de consumidor (dev realm "rober" existe; acervo dev está vazio — seed controlado documentado como próximo passo). Prod idem.
- Deploy planejado (quando push liberar): `git pull --ff-only` + `--build engineering-api` imagem padrão (extras OFF, flag OFF → `provider_unavailable`/`feature_disabled` honestos) — deploy de código seguro sem custo operacional.

## 8. Inventário do acervo (R71-13/14)

Contrato de listagem existe: `GET /products/drawings` (api-delpi, `require_any_permission(ENGINEERING_LMP_ACCESS)`, paginação ≤500, filtros code/file_kind/revision/variant/size/datas). Catálogo real medido: **4.833 PDFs** no FILESERVER autorizado (via mapeamento X: do operador — evidência offline; a listagem autenticada via API segue pendente de sessão). Corpus R7 já cobriu: vetorial+BOM+cotas (90264302), escaneado (10210267-2), multipágina 18p (90263554), esparso (90262471 Inspecao), etiqueta (ETIQUETA).

## 9. Matriz R71-01..32 (resumo)

PASS: 01–08, 10–16, 29–30, 31 (parcial — kill switch = flag off default + rollback trivial; deploy não executado). OWNER_BLOCKED: 17–18 (push/deploy — concorrência na árvore compartilhada). TEST_NOT_RUN: 19–21 (sem sessão OAuth). PENDING: 22–28 dependentes do E2E/corpus autenticado (corpus offline já evidenciado na R7/doc 87). 09: probe paddlex no init documentado (sem egress de conteúdo).

## 10. Residuais

1. Push `f7817c33e7` quando a árvore compartilhada estabilizar → deploy canônico.
2. E2E autenticado (dev: acervo seed + token dev + MCP call; prod: sessão consumidora).
3. Worker dedicado se volume justificar (ARCHITECTURE_DECISION_REQUIRED).
4. Permissão dedicada `engineering.drawing_benchmark` no Core — decisão owner pendente.
5. Avaliação ampliada do acervo = campanha governada separada (etapas A–D do plano R71-16).
