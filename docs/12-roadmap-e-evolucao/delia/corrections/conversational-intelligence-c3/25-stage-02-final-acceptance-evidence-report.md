# 25 — Stage 02 · Final Acceptance Evidence Report

**TASK:** `DELIA-C3-STAGE-02-FINAL-ACCEPTANCE-EVIDENCE-AND-REWORK-01`
**MODE:** `REANCHOR → INVENTORY → REUSE → INDEPENDENT REEXECUTION → CONSUMER/DEPLOYMENT VERIFICATION → SAFE EVALS → UX QA → RED/FIX/GREEN IF NEEDED → FULL REGRESSION → DOCUMENT → COMMIT → PUSH MAIN → VERIFY → REPORT`
**REFERENCE HEAD:** `34cc744f71b4bb9063c88ee7e302acf52cc5ea23` (= `origin/main` no reanchor; worktree limpo exceto 1 arquivo concorrente de `transformometro-api`, preservado — desde então commitado como `60a632699b`; `main` avançou a `4af3d656c6` sem nenhuma mudança em `delia-api`/`plugins/delia`, mantendo a evidência válida no HEAD final)
**CONTEXTO:** rework B2 revisado `ACCEPT_WITH_RESIDUAL` (doc [24](./24-stage-02-final-independent-review.md), §6.193). Esta task fecha as lacunas de evidência apontadas; não reimplementa RW-01/RW-02/UX-01.

---

## 1. Inventário e Reuse Gate (HEAD `34cc744f`)

Todos os mecanismos permanecem conforme revisados: `PendingWriteStore.take_if_current` (identity-CAS sob `RLock`), `_attempt_confirmation`/`_confirm_proposal`/`_execute_prepared_act`, `InteractiveTurnRequest.command_type`, `_validate_turn_command` no Application, `App.tsx` decisão-alvo, `interactionClient` tipado, `GovernedConfirmation` compartilhado.

`EXISTING_EQUIVALENT=YES` em todo o perímetro; `REUSE_DECISION=REUSE/EXTEND`. Nenhum planner/engine/registry/Policy novo.

## 2. Reexecução independente (executor local, SHA `34cc744f`)

| Suíte | Comando | Resultado |
|---|---|---|
| Concorrência B2 | `pytest tests/test_stage02_b2_concurrent_decisions.py` | **6/6 PASS** — Barrier(2)+ThreadPool real; APPLY×APPLY, APPLY×REJECT, REJECT×APPLY: ≤1 owner ACT, 1 vencedor; replay/stale/invalid/actor-mismatch não consomem pendência |
| Contrato HTTP/Application | `pytest tests/test_interaction_runtime.py tests/test_stage02r2_execution_bound_diagnosis.py` | **104/104 PASS** |
| Arquitetura do request | `pytest tests/test_interaction_runtime_architecture.py` | **PASS** (campo `command_type` no contrato fechado) |
| Backend completo | `pytest tests/` | **1137/1137 PASS** em 32.4s — inclui B1 (baseline, ceiling, provider-neutrality, orquestração) e casos positivos de execução autorizada (APPLY→ACT com fake provider) |
| Frontend | `vitest run` | **191/191 PASS**, 16 arquivos |
| `s2.shell.test.tsx` pós-fix | `vitest run src/s2.shell.test.tsx` | **21/21 PASS** |

Casos positivos comprovados: APPLY válido executa o ACT governado (fake `commit_record` invocado exatamente 1×), REJECT cancela sem owner call, proposta inválida nunca consome pendência legítima.

## 3. Deployment topology — agora PROVEN em runtime

Anteriormente só a imagem declarada era evidência. Nesta task:

- `docker ps`: `delpi-delia-api` (imagem `infra-delia-api`) em execução no stack local.
- `docker inspect delpi-delia-api`: `Cmd = gunicorn -b 0.0.0.0:8000 --workers 1 --threads 4 --timeout 60` — **o processo efetivamente implantado roda 1 worker**.
- Compose dev/prod: nenhum `replicas`/`deploy.scale` para `delia-api`.
- `curl /apps/delia-api/health` via gateway → **200** (serviço saudável atrás do gateway).

**Conclusão:** a topologia observada é single-process/multi-thread; o claim process-local (`RLock`+`take_if_current`) cobre exatamente esse threat model. Exatamente-uma-vez distribuído **não é alegado**; multi-worker futuro exige decisão arquitetural separada (`TO_INVENTORY`).

## 4. Consumers de `POST /interaction/turns` (HEAD `34cc744f`)

| Consumidor | Estado |
|---|---|
| `plugins/delia` (MFE) | Migrado — comandos tipados, sem texto em decisões |
| `real_provider_neutral_eval.py` | Migrado — `command` tipado, fluxo two-turn |
| `real_governed_read_eval.py` | Compatível — `{"input"}` resolve como MESSAGE por forma |
| `real_multistep_orchestration_eval.py` | Compatível — idem |
| `real_model_eval*.py` (in-process) | Sem `confirmation` — comportamento inalterado |
| Testes backend/frontend | Atualizados e verdes |
| OpenAPI | `delia-api` não publica spec para a rota interna — contrato = testes de fronteira + docs 18/19/23 |
| Não-MFE externos | `TO_INVENTORY` — nenhum localizado no repo; ausência externa não provada |

## 5. Typecheck — classificação e correção

`tsc -p tsconfig.app.json` antes do fix: 4 erros.

| Erro | Owner | Ação |
|---|---|---|
| `s2.shell.test.tsx(238)` indexing `unknown` | `plugins/delia` | **CORRIGIDO** — helper `deliaApiCalls` agora retorna `[string, RequestInit][]` (mesmo cast aplicado a `interaction.test.tsx` no rework); sem `@ts-ignore`, sem `any`, sem relaxar config |
| `plugin-ui` `InitialsAvatar.tsx(198)` | `plugins/plugin-ui` | **Outro owner** — não alterado lateralmente; registrado como bloqueio de full-repo typecheck; task bounded separada recomendada |
| `plugin-ui` `layout/index.ts(274)` export ausente | `plugins/plugin-ui` | idem |
| `plugin-ui` `TaskDetailCard.tsx(136)` ReactNode type | `plugins/plugin-ui` | idem |

Estado pós-fix: **somente os 3 erros de `plugin-ui`** permanecem — pré-existentes (últimos commits que tocam esses arquivos são anteriores a B2: `b607e604c2`, `843ee2423a`, `3e669015f3`, `737eef150a`), fora do diff e do ownership da Etapa 02. **Sem silenciamento.**

## 6. Browser QA

- Stack local vivo: gateway `http://localhost/` → 200; `delia-api/health` → 200.
- Browser preview aberto no gateway para verificação autenticada pelo usuário (login Keycloak exigido — executor não possui credenciais interativas nesta sessão).
- Vite standalone do MFE não renderiza fielmente sem o host Portal (federation remote + `lucide-react` shared-scope não resolvido fora do monorepo host) — inspeção visual standalone **não é evidência válida**.
- **BROWSER_QA=TEST_NOT_RUN** pelo executor; cobertura funcional dos cenários UX-01 A–E via Vitest (191 testes, incluindo cartão preservado após MESSAGE e resolução alvo-específica).

## 7. Generalization / real-model evals

Sem credenciais `DEV_PORTAL_USERNAME`/`DEV_PORTAL_PASSWORD` ou `DELIA_EVAL_BEARER` no ambiente, e a eval contém writes reais (D1–D3) proibidos nesta task:

`REAL_MODEL_EVAL=TEST_NOT_RUN` · `LIVE_PROVIDER_EVAL=TEST_NOT_RUN` · `TASK_OUTCOME_REAL=NOT_PROVEN`.

A cobertura adversarial scripted (formulações variadas, bound ausente/inválido/unrestricted, provider renomeado, ceiling, owner true/false) está verde na suíte.

## 8. Defeitos novos encontrados

**Apenas o débito de typecheck delia-side** (`s2.shell.test.tsx`), corrigido com cast mínimo. Nenhum defeito de produção encontrado; nenhum diff funcional adicional.

## 9. Segurança e concorrência — reconfirmado

Gates §9 do brief anterior re-verificados no HEAD atual: single-winner atômico, invalid não consome, replay rejeitado, ceiling reduction-only, `execution_bound` inerte para grant, ACT-only fail-closed, digests-only no wire, audit por decisão real. Residual search: sem `get`→ACT sem claim, sem claim ignorado, `take` legado sem callers.

## 10. Arquivos alterados

- `plugins/delia/src/s2.shell.test.tsx` — cast do helper (débito de typecheck do próprio pacote).
- `docs/.../25-stage-02-final-acceptance-evidence-report.md` (novo), `README.md`, `03-evals-and-handoff.md`, `evidence/execution-ledger.md`.

## 11. Estado

`B2_REWORK=ACCEPT_WITH_RESIDUAL` (§6.193) + `B2_EVIDENCE=EXECUTED_ON_CURRENT_HEAD`; `STAGE_02_ACCEPTED=NO`; `STAGE_03_AUTHORIZED=NO`; `PRODUCTION_READINESS=NOT_PROVEN`.

**Veredito do executor:** `READY_FOR_INDEPENDENT_ACCEPTANCE_REVIEW` — não é auto-aceite; decisão de `STAGE_02_ACCEPTED` pertence à coordenação/revisor independente.
