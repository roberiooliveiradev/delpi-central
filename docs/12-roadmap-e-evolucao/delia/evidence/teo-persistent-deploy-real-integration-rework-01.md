# DÉLIA + TÉO — REWORK: deploy persistente + MCP live + outcome real

TASK_ID: `DELIA-C3-TEO-PERSISTENT-DEPLOY-AND-REAL-INTEGRATION-REWORK-01`
EXECUTION_DATE: 2026-11-08 | EXECUTOR: Devin
BASE_HEAD: `e18695d593de5a3e6e14e1e58a929ccc2a2d2586` (origin/main)
FINAL_HEAD: `4f9cafb51d841f50063c8867df1d014cc8518a45` (pushed)

## Parte A — Código

| Campo | Valor |
|---|---|
| Base SHA | `e18695d5` |
| Final SHA | `4f9cafb5` (main, push verificado) |
| Arquivos alterados | `transformometro-api/tm_app/interface/mcp/server.py` (3 linhas, description-only) |
| Diff | `view=departamento requires filial_id AND setor_id` → `view=department (alias: departamento) requires filial_id AND setor_id` (canonical enum + alias, §2.3) |
| Contrato | `DashboardView` canonical: consolidated/filial/department; `_VIEW_ALIASES` aceita departamento/setor/branch/consolidado (`dashboard_view_scope_service.py:20-34`) |
| Owner approval | Tarefa anterior (074470d2) já aprovava a correção de descrição; esta etapa só declara o identificador canônico |
| Trabalho concorrente | Worktree tinha diffs não relacionados (engineering PRC); commit limitado a server.py |

## Parte B — Testes

| Comando | Exit | Resultado |
|---|---|---|
| `PYTHONPATH=.:../shared .venv/bin/pytest tests/test_teo_mcp_contract.py tests/test_teo_mcp_write_governance.py -q` (em `transformometro-api/`) | 0 | **39 passed** |
| `pytest tests/test_dashboard_view_scope_service.py` | 0 | **13 passed** |
| `pytest` MCP surface/metadata (5 arquivos) | 0 | **101 passed** |
| `bash scripts/ci-transformometro-api.sh` (suite completa) | 1 | **2040 passed, 56 skipped, 10 failed** |

Os 10 fails são **pré-existentes e não relacionados** — comprovado via `git stash` do diff e re-execução dos mesmos arquivos (10 failed idênticos sem a mudança): bootstrap_filiais (2, fixture), dashboard_live_service (4), gpt_validation_error_context (1), process_instance_repository (1), shared_resource_scope (1), sign_invite_mail_trace (1). Nenhum toca `server.py` ou a descrição MCP.

## Parte C — Deploy (srv-api `operador@192.168.1.237`)

| Campo | Valor |
|---|---|
| Procedimento | `git pull --ff-only` (ec67d8ca00→4f9cafb51d) + `./infra/scripts/up-prod-sequential.sh --fase api --build transformometro-api` |
| SOURCE_SHA | `4f9cafb51d841f50063c8867df1d014cc8518a45` |
| PREVIOUS_IMAGE_ID | `sha256:c2fdb9ed8f35` (retida no host → rollback disponível) |
| DEPLOYED_IMAGE_ID | `sha256:76b063de974b6a8ad5b1ab767efb30ed6bd48784283567bd8fa3395b73e733a8` |
| CONTAINER_ID | `96fecb4bbddef9401bece4cc59cd61ac71b5a8c88366964a07d13ae42cb7ddcf` |
| CONTAINER_CREATED_AT | `2026-11-08T15:28:43Z` |
| SERVICE_STATUS | Up (container recriado pelo compose, não docker cp) |
| HEALTH | `GET /health` → 200 |
| Persistência | `docker run --rm infra-transformometro-api grep "view=department" /app/tm_app/interface/mcp/server.py` → texto presente **na imagem** (container descartável, sem tocar produção/migrations) |
| Migrations startup | `tm_migrations_startup_begin/done` → "Nenhuma migration pendente" (V027–V056 já aplicadas; zero executada) |
| DÉLIA | não reconstruída, não reiniciada (Up 2 days) |

## Parte D — MCP

| Item | Resultado |
|---|---|
| Endpoint DÉLIA→TÉO | `http://transformometro-api:8000/mcp` (rede interna), Host header `minhadelpi.com.br` (prod) / `localhost:8000` (dev), audience `mcp-transformometro`, token exchange via `DELIA_TOKEN_EXCHANGE_URL` (gateway) |
| tools/list autenticado (wire real, dev stack) | initialize 200 → tools/list 200 → 6 tools (analyze, get_context, read, knowledge, execute, delete) |
| Descrição `analyze` publicada | contém: consolidated sem ids; `view=filial requires filial_id and rejects setor_id`; `view=department (alias: departamento) requires filial_id AND setor_id`; `get both via read entity=department first` — 7/7 checks |
| Contract hash | `ANALYZE_DESC_SHA256=a5ed4ec6846c810b` |
| Segurança | unauth tools/list → **401** (prod e dev); `delia-api` client sem service-account (`unauthorized_client`) — fail-closed preservado |
| Prod authenticated tools/list | **TEST_NOT_RUN** — credencial sancionada `user` (prod realm) é fornecida pelo owner por sessão e não está provisionada ao executor; `rober` do env.local válido só no realm dev (`invalid_grant` no prod). Compensação: descrição verificada **dentro da imagem publicada** + wire idêntico no dev + 401 não autenticado |
| Snapshot catálogo prod (residual) | `DELIA_MCP_CATALOG_MODE=snapshot_experiment` (EVAL_ONLY); snapshot `teo` ACTIVE v1 capturado 2026-11-02 carrega descrição ANTIGA — afeta apenas `discover_delpi_information`; invoke/registro de tools segue live (código `snapshot_interop.py`). Refresh do catálogo = config/dado DÉLIA → NÃO autorizado nesta task |
| Caminho de consumo do modelo | `_build_native_mcp_toolset` → MCPToolset faz tools/list LIVE no owner → modelo recebe a descrição publicada (provado comportamentalmente: C1 Kimi usou filial_id+setor_id corretos) |

## Parte E — Modelo (runtime real: pydantic_ai, v41, política unificada, MCP TÉO novo; identidade `rober` password grant + token exchange; stack dev completo)

### Kimi K3 (`openrouter_kimi`, moonshotai/kimi-k3)

| Cenário | Calls | Fails | Outcome |
|---|---|---|---|
| B1 r1 `analise departamento engenharia` | 7 | 2 (analyze sem filial_id → 400 scope ×2) | GROUNDED — recuperou via consolidated + reads; honest limitations |
| B1 r2 | 6 | **0** | GROUNDED — declarou "Filial não especificada — análise para filial 01" |
| B1 r3 | 7 | 1 (read branch `page/page_size` INVALID_FIELD) | GROUNDED; tool_calls_limit residual |
| C1 `processos na engenharia` | 7 | 1 (read department filtro `q` INVALID_FIELD) | GROUNDED partial — **read department → filial_id 01 + setor_id engenharia → 3× analyze com escopo correto, todos SUCCESS**; dados reais (10 soluções, R$ 37.037,87) |

Baseline documentado: B1 Kimi original **8/5**, unificado **6/3**. Agora: **7/2, 6/0, 7/1** — melhoria consistente, sem repetição cega 5× do mesmo erro.
C1 baseline **8/3**→**7/1** com o comportamento-alvo do contrato (resolve ids via read department).

### Qwen local (`local_ollama`, qwen3:4b-instruct-2507-q4_K_M)

| Cenário | Calls | Fails | Outcome |
|---|---|---|---|
| B1 r1 | 6 | 2 (read `get` sem id ×2, mesma classe) | GROUNDED partial — ids reais do departamento, unmet honesto |
| B1 r2 | 3 | 1 (read get sem id) | GROUNDED — dept real + dashboard live |
| B1 r3 | 5 | 1 (read get sem id) | GROUNDED |
| C1 r1 | 0 | 0 | NON_GROUNDED — resposta conceitual HYPOTHESIS (sem ferramentas) |
| C1 r2 | 0 | 0 | NON_GROUNDED — idem (consistente) |

Baseline Qwen B1: 6/1 → agora 6/2, 3/1, 5/1 — comparável; **zero erros de escopo** (a classe "exige filial_id e setor_id" desapareceu). C1 Qwen: respondeu conceitualmente sem tools (variância do modelo pequeno; honesto, não fabricou).

### Agregados

| Métrica | Valor |
|---|---|
| Total real model calls | 16 (Kimi 6, Qwen 10) |
| Total MCP invokes | 41 |
| Total erros (400/exception) | 8 |
| Error-class "exige filial_id+setor_id" | baseline B1 5× → **2× total em 3 runs** (só r1) |
| HTTP 400 antes→depois (B1) | 5 → 2/0/1 por run |
| Tokens | usage() provider-reported 0 (não medido por run); custo OpenRouter API |
| Latência total | Kimi 79.4s (B1×3) + 19.1s (C1); Qwen 306.7s (B1×3) + 100.4s (C1×2) |
| Custo | $0.035026 OpenRouter (Kimi); Qwen local ~0 |

### Erros residuais (classificação)

| Erro | Owner | Causa | Repro |
|---|---|---|---|
| analyze 400 scope (filial_id ausente) | MODEL_BEHAVIOR | modelo chamou analyze antes de obter filial_id; contrato agora declara o requisito | 2× (B1 r1 só) |
| read INVALID_FIELD (`q`, `page`, `page_size`) | MODEL_BEHAVIOR + possível gap de contrato (vocabulário de filtros por entidade não publicado por completo) | modelo inventou filtros não aceitos | 2× |
| read `get` sem id | MODEL_BEHAVIOR | arg-shape; descrição já diz "get uses id" | 3× Qwen |
| C1 Qwen 0-invoke | MODEL_BEHAVIOR | pequeno modelo responde conceitualmente; honest NON_GROUNDED | 2× |

Nenhum erro atribuível ao contrato novo, à DÉLIA ou ao transporte. `tool_calls_limit` (8) cortou investigações legítimas em B1 r1/r3 — chamadas produtivas (read department/branch) competiram com retries; não alterado (fora de escopo).

## Parte F — Decisão

- **PROVEN**: contrato corrigido publicado na imagem prod; wire real serve a nova descrição; modelo consumiu a metadata (args corretos em C1); erro-classe alvo (scope-400) 5→≤2; outcomes GROUNDED com dados reais.
- **Residuais**: (a) retry de error-class em variantes (read arg-shape) — limitação do modelo, já documentada; (b) snapshot catálogo prod stale (EVAL_ONLY mode; refresh não autorizado); (c) tools/list autenticado prod — TEST_NOT_RUN por credencial sancionada ausente (bloqueio comprovado); (d) tool_calls_limit ocasional.
- **Não provado como defeito**: DÉLIA código/config (intocado, DELIA_CODE_CHANGED=NO).
- **Next action**: provisionar credencial `user` sancionada ao executor para tools/list autenticado em prod (gate de encerramento administrativo); decidir refresh/aposentadoria do snapshot catalog com o owner DÉLIA.
