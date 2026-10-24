# 138 — Release readiness integrado DÉLIA + DAVI: fechamento G3/G5 e candidatos de release

**TASK_ID:** `DELIA-C3-DELIA-DAVI-INTEGRATED-RELEASE-READINESS-AND-HOMOLOGATION-01`
**PLAN_ID:** `DELIA-ORCHESTRATION-RESPONSIBILITY-REFACTOR-FINITE-01`
**REFERENCE_REVIEW:** `cd5f349f7148bfc6ee059f37980b08216a0fc05a` (revisão independente do doc 137)
**Data:** 2026-10-24
**Natureza:** fechamento operacional dos resíduos G3/G5, regressão completa, prova integrada em dev, preparação de artefatos de release para `delia-api` e `api-delpi`. **Sem deploy** — gate de autorização operacional específica pendente.

---

## 1. Reancoragem e autoridade

| Item | Valor verificado |
|---|---|
| BASE_SHA | `cd5f349f71` (`origin/main` no início da task — revisão independente do 137) |
| EVALUATED_SHA | `efedddfe39` + 1 arquivo de teste alterado nesta task (ver §2.4). `origin/main` avançou durante a execução: `3c89d222b5` (spec 127 — **plugin-UI apenas**), `8856245205`, `7dd897f530`, `efedddfe39` (docs). Verificado por `git diff --quiet`: árvores `api-delpi/` e `delia-api/` **byte-idênticas** entre `cd5f349f71` e `efedddfe39` — suites e probes executados permanecem válidos no SHA avaliado |
| Worktree isolada | `/home/analistaptd/delia-release-wt` — checkout principal e trabalho concorrente preservados |
| Autorização | prompt PO desta task: testes, correções G3/G5 estritamente necessárias, preparação de artefatos e verificação de readiness. Deploy produtivo **não** autorizado por este prompt nem pela revisão `cd5f349f` (`DEPLOY_AUTHORIZED_BY_THIS_REVIEW=NO`) |
| Authorities lidas | `.cursor` always-on + `delia-execution-protocol`; reancoragem 16 → 50 → 17 → 49 → 51 → 52 → 21 → 20 → 25; specs 03/60; ADR 58; roadmap 59; S4/117; docs 125/129/130/133–137; parecer `cd5f349f`; ledger vigente |

## 2. G3 — ambiente de testes (`CLOSED_PROVEN`)

### 2.1 Causa-raiz e mecanismo canônico

Os 3 testes geradores (`test_davi_capability_wave_002_freeze`, `test_davi_capability_wave_003a_freeze`, `test_davi_governed_knowledge_bundle`) chamam `git rev-parse` via as bibliotecas canônicas (`davi_governed_knowledge_bundle_lib`, `davi_wave_002_economic_freeze_lib`) para pinar `source_git_sha`/`freeze_sha` no manifesto. O runner sancionado é **GitHub Actions** (`.github/workflows/api-delpi-console.yml`): `actions/checkout@v4` com `fetch-depth: 0` sobre `ubuntu-latest` — isto é, o contrato do ambiente de testes é **git executável + gitdir real**, não a imagem de produção. A imagem `infra-api-delpi` corretamente não contém git (Dockerfile produtivo minimal).

### 2.2 Correção aplicada (somente configuração de teste)

- Imagem de teste derivada `infra-api-delpi-test:local` = `infra-api-delpi:latest` + camada única `apt-get install git` (sem tocar o Dockerfile de produção, sem dependência produtiva nova).
- Execução sob o ambiente oficial: rede `infra_delpi-network`, `--env-file infra/.env`, worktree e repositório principal montados nos caminhos reais (`/home/analistaptd/delia-release-wt` e `/home/analistaptd/projetos/delpi-central`) → `.git` da worktree resolve o gitdir naturalmente; `git rev-parse HEAD` = `cd5f349f71` confirmado dentro do container.
- Nenhum teste gerador alterado para ignorar git; nenhum mecanismo paralelo criado — é a execução local equivalente ao contrato do runner CI.

### 2.3 Comando e resultado

```
docker run --rm --network infra_delpi-network \
  --env-file infra/.env \
  -v <worktree>:/home/analistaptd/delia-release-wt \
  -v <main-repo>:/home/analistaptd/projetos/delpi-central \
  -w <worktree>/api-delpi infra-api-delpi-test:local \
  bash -c 'git config --global --add safe.directory "*" && python -m pytest tests -q'
```

**Resultado: `6034 passed, 10 skipped, exit=0`** em `cd5f349f71` + delta desta task (árvore `api-delpi/` idêntica em `efedddfe39`). `API_DELPI_FULL_SUITE=PASS`.

### 2.4 Correção de teste descoberta na execução completa

`test_supplies_negotiation_savings_summary_route` (`test_google_sheets_routes_live.py`) invocava a rota live incondicionalmente e falhava com sheet não configurada (env `SUPPLIES_IDD_SHEET_ID`/`SUPPLIES_NEGOTIATION_SAVINGS_SHEET_GID` vazias no ambiente dev — integração opcional). O irmão parametrizado do mesmo arquivo já skipa nessa condição. Fix mínimo: mesmo guard `pytest.skip` no teste de rota — não oculta defeito (a rota informa corretamente "planilha não configurada"), apenas alinha a semântica de "executável somente quando a integração opcional está configurada". Arquivo verde: `5 passed, 4 skipped`.

## 3. G5 — budget de diretivas DAVI (`CLOSED_PROVEN` com residual sinalizado)

### 3.1 Medidas reais (SHA avaliado)

| Métrica | Valor |
|---|---|
| `directives_serialized_size()` | **17.151 B** (16,75 KiB) |
| `DAVI_AGENT_DIRECTIVES_MAX_BYTES` | 20.480 B — utilização **83,75%** |
| Teto de transporte canônico (`execute_max_response_bytes`) | 65.536 B — diretivas = **26,2%** |
| Envelope `gpt_get_catalog` completo | 18.626 B (28,4% do teto) |
| Envelope `discover_delpi_information` real | 18.142 B — `capability_surface` = 17.173 B (94,7%) |
| **Wire real** (MCP live, token delegado) | resposta discover **17.553 B**, `capability_surface` intacto 17.173 B — zero truncamento |
| Latência de projeção (100 chamadas) | **0,167 ms/chamada** (doc `lru_cache`) — desprezível |
| Tokens estimados | ~4,3K (estimativa; ~4 bytes/token pt/en) — um fetch de catálogo, não custo por turno |

### 3.2 Cadeia de consumo verificada

1. `davi_agent_intelligence.json` → `agent_directives()` → `capability_surface` em `gpt_get_catalog` (ação OpenAPI do GPT externo) e `discover_delpi_information` (tool MCP).
2. Na DÉLIA, `agent_directives`/`capability_surface` são **control-plane** (`_CONTROL_PLANE_KEYS`, `_without_control_plane` em `outcome_assessment.py`): nunca projetados como conteúdo renderizável nem injetados no contexto do modelo como fato — fora do budget de prompt do orquestrador.
3. Consumidor efetivo: GPT externo (uma leitura de catálogo por descoberta) ou cliente MCP. Nenhum limite intermediário identificado no provider/api-delpi abaixo do teto de transporte; envelopes medidos cabem com folga ~3,5×.

### 3.3 Truncamento e fail-closed

- **Sem truncamento silencioso**: a projeção aplica caps determinísticos de lista (12 itens, 32 anti-patterns — testados); `bound_response_payload` marca `truncated` explicitamente e só se aplica a resultados `execute`. O envelope `discover` não é byte-bounded em runtime — o payload sai íntegro (provado na wire: 17.553 B completos).
- **Fail-closed comprovado na fronteira de governança**: o conteúdo governado só muda via commit; 3 testes pinam `directives_serialized_size() <= DAVI_AGENT_DIRECTIVES_MAX_BYTES` (`test_davi_agent_intelligence`, `test_davi_knowledge_orchestration`, `test_davi_enterprise_intelligence_acceptance_v1`). Injeção de +25 KiB (42.172 B projetados) → gate rejeita (`oversized > cap`). Oversize não alcança runtime sem um commit que passaria CI.
- **Residual sinalizado (não normalizado silenciosamente):** não existe bound de runtime no envelope `discover` — a única linha de defesa é o gate CI. Se a coordenação exigir defesa-em-profundidade runtime (fail-closed ou bound com flag), é decisão de arquitetura — `ARCHITECTURE_DECISION` registrada para avaliação, sem mudança nesta task.
- O budget canônico 16 KiB não está fixado por autoridade superior (o próprio comentário do owner o descreve como soft budget autoescolhido sob o teto de transporte 64 KiB); a restauração sancionada das diretivas SQL (v23) precisa de ~0,8 KiB sobre um corpus já no limite → 20 KiB tecnicamente justificado com folga (16,3% headroom) e dentro de todos os bounds efetivos medidos.

## 4. Regressão completa no SHA avaliado

| Suíte | Resultado | Ambiente |
|---|---|---|
| `api-delpi` completa | **6034 passed / 10 skipped / exit=0** | `infra-api-delpi-test:local` + rede/env oficiais + git/gitdir |
| `delia-api` completa | **2205 collected, exit=0** (perfil 2202 passed / 3 skipped — idêntico ao pós-F01–F06) | `infra-delia-api` + monorepo montado |
| DAVI/retrieval, allowlist, route contracts, SQL validator, governed knowledge, pagination | verde dentro da suíte completa | idem |
| F01–F06 | preservados (sem regressão — árvore `delia-api/` idêntica ao SHA já caracterizado) | idem |
| Import DAG | acíclico (sem novas edges) | — |

## 5. Prova integrada em desenvolvimento (providers reais)

Container `delia-eval` (código `efedddfe39` montado) + `davi-candidate` (código `api-delpi` do SHA avaliado, comando produtivo `--root-path /apps/api-delpi`) na rede dev real, Keycloak real.

### 5.1 Eval HTTP integrado (`r1r2_integrated_eval.py`) — `verdict=PASS`, `blocking_failures=[]`

| Cenário | Resultado |
|---|---|
| NEG-AUTH | 401 sem bearer |
| D4 discovery | 200, superfícies reais TEO/VISTA listadas |
| D5 / D5-R | 200, surface listing (variância 3B documentada — modelo dev não alcança grupos MCP por seleção) |
| D5-schema | pedido de esclarecimento honesto |
| **D8 material** | **GROUNDED**, `OBSERVATION`, provider `openapi`, `delpi.get_product_summary` → produto real 10080043 |
| D8-R continuity | surface listing (variância 3B documentada) |
| N1 | resposta conversacional no retry (`HYPOTHESIS`, NON_GROUNDED declarado) |
| NEG-INJ | 502 `invalid_model_output` — modelo recusou instrução-injeção (falha honesta, não compliance) |
| NEG-UNK provider | 200, resposta bounded honesta, `owner_path_unbound`, zero dado inventado |

### 5.2 Probe live MCP (determinístico — token delegado real RFC 8693, wire real)

| Cenário | Resultado |
|---|---|
| S0 tools/list | exatamente `discover_delpi_information` + `execute_delpi_information` (invariante 2 tools) |
| **S1 D8-R DAVI (F06)** | `"descricao do material 10080043"` → `search_products` @ **0,9125** → execute `{code:"10080043"}` → produto real `TERM. OLHAL M6 …` (`projection=approved_fields`, `is_complete`, `truncated=false`) |
| S2 required args | execute sem `code` → `VALIDATION_ERROR "Missing required argument: code"` (fail-closed, sem invoke) |
| S3 sem token | 401 |
| S4 write intent `"atualizar o preço do produto"` | zero candidatos — superfície READ-only |
| Wire G5 | discover 17.553 B íntegro; `capability_surface` 17.173 B sem truncamento |

Nota de evidência: o probe injeta goal/argumentos deterministicamente — prova integração/contrato, não seleção autônoma do LLM (essa fica com o eval HTTP + homologação `kimi-k3` pendente de gate).

## 6. Gates de segurança revalidados

- `execute_readonly_sql`: candidato canônico bounded (`requestBody` obrigatório); SQL genérico segue FORBIDDEN; bypass do validator default-ON **auditado** mantendo AST/safeguards (`dacf4fa7ca`); fixtures de enforcement explícitas.
- READ ≠ PREPARE ≠ ACT mantido; zero candidato WRITE na superfície MCP (probe S4).
- `candidate_token` nunca projetado ao usuário; `api-delpi.access` fora da projeção externa (reword governado).
- AuthZ: token delegado exigido (401 sem bearer); exchange devolve `aud` = client-id + canonical URL; `scope mcp:tools` exigido pelo realm.
- DISCOVERY ≠ APPROVAL; metadata ≠ FACT; secrets fora de logs/evidência.
- AP-01…AP-20 reconciliados: DAG acíclico, owner único de projeção, zero duplicação de contrato.

## 7. Candidatos de release (dois serviços, controle independente)

| Campo | `delia-api` | `api-delpi` |
|---|---|---|
| Deployed runtime (srv-api) | imagem `ee155bf5a325` (R1+R2 — **sem** `0b9220fa64` D5-R/D5-schema, **sem** `1f3bc4a640` F01–F06, **sem** spec-127) | imagem `edc5f2886e9f` (build ~3h atrás — allowlist v23/95 presente, **sem** aliases F06, **sem** remediação 137 — `DAVI_AGENT_DIRECTIVES_MAX_BYTES=16384` medido no runtime) |
| SHA candidato | `efedddfe39` (+ commit desta doc) | `efedddfe39` (+ commit desta doc + guard de teste §2.4) |
| Diff vs runtime | `0b9220fa64` + `1f3bc4a640` (+docs) — exatamente o escopo D5/F01–F06 | `1f3bc4a640` + `3b17610ddf` — aliases material + remediação 137; demais commits `api-delpi/` já anteriores e deployados |
| Mudanças concorrentes no artefato | nenhuma dentro de `delia-api/` entre prod e candidato além do escopo | nenhuma nova — prod já carrega supplies/pcp anteriores; spec-127 é plugin-UI (fora destes serviços) |
| Build | `Dockerfile.prod`/compose canônico (`up-prod-sequential.sh --build delia-api`) | `Dockerfile` canônico (`up-prod-sequential.sh --build api-delpi`) |
| Migrações | nenhuma | nenhuma nova |
| Rollback | `git revert` + rebuild; imagem anterior `ee155bf5a325` (e refs documentadas `536b621a6d81`/`1b21ce948e`) | `git revert` + rebuild; imagem anterior `edc5f2886e9f` (tag `incident-15b7f3ec200e` disponível) |
| Dependências reais | Keycloak, providers MCP DAVI/VISTA/TÉO, LLM provider | Keycloak, Protheus/REST, Postgres plugins, Google Sheets |

## 8. Estado de readiness e gates

- `RELEASE_READINESS=READY_FOR_INDEPENDENT_REVIEW` — sem regressão nova, G3/G5 fechados com evidência, segurança preservada, artefatos e rollback identificados, riscos residuais explicitados (bound runtime discover; variância de seleção do modelo dev 3B — já documentada como não-regressão).
- `INDEPENDENT_REVIEW_STATUS=PENDING` — este relatório não preenche parecer da coordenação.
- `DEPLOY_AUTHORIZATION=NOT_GRANTED` — prompt e revisão `cd5f349f` não autorizam deploy; exigido aceite independente de readiness + autorização operacional PO específica para os dois serviços/artefatos.
- `DEPLOY_STATUS=BLOCKED_PENDING_AUTHORIZATION`.
- `PROD_HOMOLOGATION=NOT_EXECUTED` — matriz produtiva com `moonshotai/kimi-k3` + DAVI real permanece gated; outcomes de negócio só serão declaráveis após homologação produtiva.
- `R3_AUTHORIZED=NO`. `PLAN_COMPLETE=NO`. `EXECUTION_DRIFT=NONE`.


## 9. Parecer independente de readiness — Coordenação (2026-10-23)

**REVIEWED_SHA:** `fd0f9ae28862f8df61eb91c0a37fef5b16a791ee`  
**VERDICT:** `ACCEPT_WITH_RESIDUAL` para **readiness técnico**, não para homologação produtiva.  
**DEPLOY_AUTHORIZATION:** `NOT_GRANTED` nesta revisão; depende de autorização explícita PO para este release e ambos os serviços.  
**R3_AUTHORIZED:** `NO`.

**Revisão GitHub:** commit e doc 138 examinados: houve apenas ajuste de guarda de teste `api-delpi/tests/test_google_sheets_routes_live.py`, indexação README e ledger, sem diff produtivo de `delia-api` ou `api-delpi` nesta task. As suítes `6034 passed/10 skipped/exit 0` e `2202 passed/3 skipped/exit 0`, além dos probes dev, foram executadas e **reportadas pelo executor**, não repetidas independentemente por esta coordenação. O skip da integração Google Sheets opcional não comprova seu outcome quando configurada.

**G3:** aceite técnico do harness derivado para testes, com git+gitdir e rede/env corretos, sem inflar a imagem produtiva. **G5:** aceite condicionado da elevação documentada do soft budget para 20 KiB, frente a `17151 B` medidos e envelopes wire intactos no ambiente de desenvolvimento. Sem bound de runtime em `discover` continua como **residual de defesa em profundidade**, proprietário DAVI/api-delpi; CI gate e corpus governado pinado reduzem o risco presente, mas não tornam payload arbitrário seguro nem dispensam reavaliação de alteração futura. Não afirmar runtime-fail-closed para esse envelope.

**Readiness:** `READY_FOR_PO_OPERATIONAL_AUTHORIZATION` com ressalvas — congelar SHA e verificar novamente o diff por serviço imediatamente antes do deploy (main é concorrente), imagem/digest/rollback, escopo e autorização para ambos `delia-api` e `api-delpi`. Sem consentimento específico, `DEPLOY_STATUS=BLOCKED_PENDING_AUTHORIZATION`. Após consentimento, implantar exclusivamente via procedimento autorizado e homologar com `kimi-k3`, DAVI real, D5-R/D5-schema/D8-R, negativos/AuthZ e outcomes; rollback se regressão material. O aceite da prontidão não prova resultados produtivos e não autoriza R3.
