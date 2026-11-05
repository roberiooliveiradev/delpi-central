# 286 — Review DÉLIA GPU WSL2: infraestrutura aceita, resultado funcional permanece FAIL

**DATA:** 2026-11-05  
**TASK_ID:** `DELIA-INFRA-NVIDIA-GPU-DOCKER-OLLAMA-ENABLEMENT-01`  
**BASE/FINAL REPORTED:** `d8c3a4f680516d61d76b20a2ae714dbb5009809c` — zero diff  
**VERDICT:** `ACCEPT_WITH_RESIDUAL` para a entrega infra/reuso WSL2 conforme evidências do executor; `FAIL` para resposta empresarial correta; `PRODUCTION_DEPLOY=BLOCKED`.

## Evidence/ownership

- GitHub confirma `infra/docker-compose.ollama-gpu.yml` no SHA-base, com `/dev/dxg`, mount `/usr/lib/wsl:ro` e `LD_LIBRARY_PATH=/usr/lib/wsl/lib`, overlay explicitamente restrito a WSL2. `EXISTING_EQUIVALENT=YES`, `REUSE_DECISION=REUSE`. Sem necessidade de NVIDIA Container Toolkit ou alteração do daemon nesta topologia **reportada**.
- Host WSL2, RTX3050 6GB, driver 610.47.03, CUDA no container, offload 79% GPU/21% CPU, 4602MiB VRAM, tokens/s warm 13.61 CPU vs 29.46 GPU e latência de geração warm 14.62s CPU vs 6.79s GPU são **medidos conforme relatório do executor**; review não acessou host, benchmark ou logs para reproduzir. Aceite infra condicionado à fidelidade das evidências reportadas.
- A DÉLIA recebeu HTTP200 em 39.4s e 45.7s, mas retornou `NON_GROUNDED/owner_path_unbound`; no primeiro turno catálogo foi 0 devido a Keycloak/MCP auth startup, no segundo 10 capabilities apareceram; Discovery DAVI retornou `CAPABILITY_NOT_MATCHED eligible=97`, sem prova da resposta final grounded. `DELIA_REAL_QUESTION=FAIL`, `ANSWER_DELIVERED=YES` apenas para fallback honesto.
- Residual observado `UnexpectedModelBehavior/ToolRetryError` em structured output. Não presumir que a GPU resolve formato JSON, nem que todo erro estrutural tem a mesma causa. Schema pass isolado anteriormente, porém falha com toolset/catálogo completo. Confirmar o estágio exato de `ToolRetryError`: pode ser validação do output, erro de ferramenta ou falta de correspondence/argumentos. É necessário diferenciar Pydantic AI native tool-output schema, model tool arguments, retries e final output.
- Executor reporta `pytest=1377 passed`, sem execução independente do reviewer. `DELIA_RUNTIME_SHA` env baked ainda stale, marcar `EXECUTION_DRIFT`, não confundir com volume montado. `PRODUCTION_DEPLOY=NOT_AUTHORIZED`.

## Próxima ação bounded

**TASK_ID:** `DELIA-C3-P0-GPU-ENABLED-STRUCTURED-OUTPUT-AND-REAL-READ-CLOSURE-01`

1. Reancorar HEAD/status, Project Instructions/.cursor, authorities 16→50→17→49→51→52→21→20→25, architecture/product/thematic specs/ledger and docs256/283–286. Confirm model/runtime active, GPU overlay, Pydantic AI 2.50.0. Keep GPU infra frozen unless failure demonstrated.
2. Use current GPU-backed Ollama and exact real user question for code 50220013, **after** Keycloak and MCP catalog health confirmed (10 caps). Select a known-present owner READ independently; compare owner data and full DÉLIA response.
3. Collect Pydantic AI **typed, sanitized diagnostics**, no exception bodies/messages/prompt/response payloads in common logs: classify `ToolRetryError` vs output validator retries vs malformed function arguments vs provider/tool schema rejection, and whether error originates from selection, discovery, execute or `InvestigationAnswer` finalization. Assert effective native tool definitions and output schema. Do not conflate `UnexpectedModelBehavior` with proven `output_retries_exhausted` subtype without native signal.
4. Try no more than one **authorized, existing** alternative model/provider or SDK-supported structured-output mode, using same prompt, tool catalog, owner data, gates and output contract; compare exact client delivered answer, source refs, model calls, retries, token timing and errors. Do not disable validation or use raw-text fallback. No unapproved business-data egress.
5. If code/config defect identified: minimal RED→GREEN fix, mandatory same-delivery legacy retirement, consumers, security/backend regressions, residual search. If no solution within available approved environment, `BLOCKED` with precise evidence/operator action, not another generic infrastructure loop.
6. Acceptance must include `HTTP_RESPONSE_RECEIVED`, `STRUCTURED_OUTPUT_VALID`, `OWNER_DATA_MATCH`, `GROUNDED_SOURCE_REFS`, `NO_FALSE_AUTHORITY`, and latency in budget. HTTP200 NON_GROUNDED is **not** product PASS.
7. Production stays blocked pending true P0 READ PASS, production release/config/security/rollback gates. Update doc256 and ledger factual outcomes.

**STOP condition:** no further GPU-specific task unless GPU use or memory behavior regresses. Focus on app-level structured output and end-to-end grounded answer.
