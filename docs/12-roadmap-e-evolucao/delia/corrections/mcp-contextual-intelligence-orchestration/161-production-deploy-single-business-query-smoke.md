# 161 — DÉLIA Production Deploy & Single Real Business Query Smoke

TASK_ID: `DELIA-C3-PRODUCTION-DEPLOY-SINGLE-BUSINESS-QUERY-SMOKE-01`
Tipo: smoke de produção — **uma única** consulta empresarial real,
read-only, pela via conversacional normal. Nenhum fix implementado.

## Reancoragem

- BASE_HEAD consultado: `00a79c26530bf36cbf9a222779a30d9a223961c7`
  (ancestor de origin/main).
- ORIGIN_MAIN no início: `7daaf99364`; evoluiu para `b2c5bac902`
  durante a execução (commits cf/proc-0076 concorrentes, fora do
  escopo — preservados).
- DEPLOY_CANDIDATE / APPROVED_PRODUCTION_SHA: `b2c5bac902` —
  **`git diff` de `delia-api/` entre `00a79c26` e HEAD = 0 linhas**;
  o código produtivo já era o baseline aprovado.
- WORKTREE: `delia-semrel-wt` limpo para o escopo.

## Gates de baseline produtivo (verificados no runtime, não na doc)

- `delpi-delia-api`: `orchestration_instructions.delpi.json` =
  **v23, sha `fcdbd185527595b9`** — idêntico à instrução A (baseline).
- `orchestration.py` sha256 `8513a5d6…` **idêntico ao HEAD do repo** —
  EXPERIMENTAL_INSTRUCTION_B_ACTIVE=NO, EVAL_OVERRIDES_ACTIVE=NO.
- MODEL_ID de produção: **`moonshotai/kimi-k3`** via OpenRouter
  (`DELIA_LLM_PROVIDER=openai_compatible`, timeout 60s) — configuração
  produtiva aprovada, distinta do `delia-json` usado nos evals locais.
- Sem variáveis `DELIA_EVAL_*`, sem override de ordem/catálogo/routing.
- Providers: MCP davi/teo/vista e OpenAPI delpi alcançáveis
  (401 auth-required nos MCP = endpoints vivos); core/health 200.

## Deploy

DEPLOY_REQUIRED=**NO** — imagem `infra-delia-api` já continha o código
aprovado; `git pull --ff-only` em srv-api apenas sincronizou docs.
Nenhum rebuild, nenhum serviço não relacionado tocado.
Exceção operacional necessária para o teste: provisionamento da
identidade de teste (abaixo) exigiu `docker restart delpi-core-api`
(2×, ~10s) para limpar o cache RBAC em memória — serviço voltou
healthy em ambas.

## Identidade de teste

`devin-smoke-r4` (identidade dedicada de smoke, já existente).
Provisionamento necessário e registrado:
1. `Delia Acesso` role via `AddRoleToUserUseCase` canônico —
   primeiro POST retornou `403 missing required permission
   'delia.access'` **antes** de entrar no pipeline de turno (falha de
   provisionamento, não turno semântico).
2. `API DELPI Acesso` role — necessário para a verificação de cobertura
   do owner (read autorizado, fora da via conversacional).

## A única consulta

- `X-Request-Id: delia-smoke-2cfac0c60deb`, correlation
  `ceccfc0c-7c41-47e3-87bb-cb3b56525f28`.
- `POST /apps/delia-api/interaction/turns` → **HTTP 200, 16.819 ms**.
- Pergunta: «Busque três produtos que correspondam à descrição
  terminal bala.» Sem injeções: sem grupo/capability/argumentos
  forçados, sem retry.

## Trace de produção (logs do runtime)

| estágio | decisão |
|---|---|
| interaction_admission | `owner_surface`, class=operational |
| select_group | `openapi:delpi` |
| select_capability | `delpi.search_products` (READ) |
| goal_understanding | interpreted, class=read, subject=yes |
| plan / decision_path | `self_index_candidate` → **OPERATIONAL** |
| index_probe | model call 3.0s |
| arguments | built, missing=0 — `description`, `page_size` |
| provider_invoke | **error — `mcp_authorization_denied`, status 403** |
| execute | `source denied the delegated call` |
| síntese | `NON_GROUNDED` + `delpi_source_unverified` |

Resposta: «O acesso à fonte autoritativa necessária para esta
solicitação foi negado. Nenhum dado operacional foi verificado.» —
recusa honesta, zero fabricação.

**Observação arquitetural:** `native_assessment` e `foreign_selection`
**não foram alcançados** — a meta entrou no plano direto OPERATIONAL
(`self_index`), que não atravessa o estágio de assessment
(`len(groups)>1` gate + plano direto). A instrução v23 avaliada nos
docs 159/160 não foi exercitada neste turno.

## Verificação de cobertura do owner (read autorizado direto)

Com a identidade pós-grant de `API DELPI Acesso` (mesmo subject do
teste — leitura direta ao owner, **não** uma segunda consulta
conversacional):

- `GET /gpt-actions/v1/products/search?description=terminal bala` →
  200, `total: 77` candidatos.
- Varredura das 8 páginas: **65 registros `TERM…/TERMINAL…`** —
  incluindo `10080092 TERM. BALA 0,50-2,27MM2 ESTANHADO…` e
  `10081004 TERM. BALA 1,00-2,50MM2 NIQUELADO…` (verificados por
  código) — a fonte tem cobertura real e abundante para "três
  produtos terminal bala".
- A denúncia do owner foi **AuthZ correta**: `search_products`
  exige `api-delpi.access`/`dashboard-engineering.view`/
  `dashboard-lmps.view` (`ENGINEERING_LMP_ACCESS`) — fail-closed
  correto sobre a identidade de teste pré-grant.

## Business Outcome

**FAIL (first divergent stage = OWNER_INVOCATION, domain AuthZ).**
A cadeia semântica foi integralmente correta — grupo, capability
(READ), argumentos (`description`, `page_size`) e resposta honesta
sem fabricação. O objetivo empresarial não foi atendido porque o
subject delegado não possuía permissão de domínio naquele momento.
Com permissão de domínio, o mesmo owner retorna ≥3 registros
correspondentes reais.

## Métricas

- Model calls: 5 (admission, select_group, select_capability,
  index_probe, arguments) — todos `completed`.
- Tokens: in ≈ 7.256, out ≈ 985. Latência total 16.819 ms.
- AuthZ bypasses: 0. ACT/WRITE/PREPARE: 0. Registros fabricados: 0.

## Derivações e limitações

- Dois POSTs preliminares retornaram 403 no gate `delia.access` durante
  o provisionamento da identidade — registrados como falha de setup,
  não como turnos semânticos (nenhum model call ocorreu).
- O resultado mede o comportamento de produção sob `kimi-k3` e plano
  OPERATIONAL direto — não é comparável 1:1 aos evals locais
  (`delia-json`, caminho de enrichment com assessment).
- Restart do `delpi-core-api` foi necessário somente para limpar o
  cache RBAC em memória após grants — sem impacto em dados.

## Veredito

`FINAL_VERDICT=FAIL` (objetivo empresarial não entregue —
autorização de domínio do subject). Comportamento orquestrado:
correto e fail-closed em todos os estágios alcançados.

DEPLOY=EXECUTED-SKIP (baseline já deployed) ·
INDEPENDENT_REVIEW=PENDING
