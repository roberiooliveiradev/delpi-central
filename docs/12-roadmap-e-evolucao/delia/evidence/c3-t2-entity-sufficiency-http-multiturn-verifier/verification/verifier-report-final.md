# Relatório do delpi-verifier

veredito: ACCEPT_WITH_RESIDUAL
rodada: 1
escalar: NAO
escopo: working tree @ e38940c0c6
contrato: PRESENTE
independencia: OK (verificador: SWE-2 High/Devin; executor: Composer)
registro: OK

## Resumo

A entrega implementa (1) gate de congruência de entidade empresarial no caminho de apresentação sob `aggregation` em `semantic_capability_support.py` — fail-closed quando `entity=`/`entity_kind=` ausente do `required_scope`; (2) contrato E2E HTTP de dois turnos via `POST /interaction/turns` + `context` canônico, com evidência live real (correlação `http-mt-42e226d1432a`, TURN2 GROUNDED via `davi.get_product_structure` 90260921) e suíte de boundary em pytest; (3) pacote de evidência autocontido + request integral RQ-1..14/AC-1..22. O restauro de V024 confere byte-a-byte com o checksum aplicado (sha256 do arquivo = `8f9c97…` = checksum em `schema_migrations`), remediação canônica da regra de imutabilidade. Não consegui reexecutar os pytest (hook bloqueia `docker exec`; host sem `flask`/`pydantic_ai`), mas fiz desk-check mecânico de cada teste novo contra o código de produção — todos consistentes. Commit/push/CI são PENDING por sequência (verificação é pré-commit por contrato). Nenhum achado ≥80 de confiança introduzido pelo escopo.

## Expectativas (escritas antes de ler o diff)

| AC | Comportamento que prova | Evidência buscada | Irmão | Negativo |
|---|---|---|---|---|
| AC-3 | Métrica de entidade A não satisfaz obrigação de entidade B sob aggregation/presentation | gate mecânico no owner + teste negativo | S3 product≠process | obrigação sem `entity=` declarado não pode SATISFY |
| AC-4 | Obrigação process+ativo satisfeita por teo.read com total | teste S1 + trace live G2 | live eval real | total sem filtro `status=ativo` → não SATISFIED |
| AC-9..13 | Dois POST reais; turn-2 re-posta `context` derivado da resposta do turn-1 | artefatos live + teste de boundary + contrato da rota | M5 código do usuário autoriza | DELIA_RESULT nunca autoriza identificador inventado; AuthZ revalidado |
| AC-17 | pytest verde no container com comandos/exit codes | logs + reexecução | regression 4 arquivos | teste enfraquecido/skip/shortcut |
| AC-19 | request file com 14 RQ + 22 AC integrais | `.git/delpi-verifier/requests/` | — | resumos/intervalos |

## Critérios de aceite × evidência

| AC | Status | Evidência |
|---|---|---|
| AC-1 | PASS | HEAD e38940c0c6 == origin/main (rev-list 0/0); WIP inventariado em `scope-reconciliation.md` |
| AC-2 | PASS | `entity-sufficiency/contract-analysis.md`: EXISTING_EQUIVALENT + REUSE_DECISION + owners/consumers |
| AC-3 | PASS | `_attempt_business_entity_congruent` em `semantic_capability_support.py:3394-3411` + gates em `:3484` e `:3650`; testes S2/S3 (`tests/test_c3_t2_final_gates_sufficiency_collection_multiturn.py:110-156`) |
| AC-4 | PASS | `positive.sanitized.json`: or-qwen14b-aca443baae46 SATISFIED, entity=process, teo.read, 109, scope `params.status=ativo` |
| AC-5 | PASS | `_SCOPE_CONTAINER_ALIASES`/`_material_required_scope`/`_consultation_operations_compatible` intactos; `test_s2_params_vs_arguments` e `test_s3_capability_read_satisfies_analysis` preservados |
| AC-6 | PASS | S2,S3,S2b,S4,S5,S6,S7,S8,S9,S10 presentes e fail-closed por desk-check (UNSATISFIED/INCONCLUSIVE conforme contrato) |
| AC-7 | PASS | `test_s10` → INCONCLUSIVE (bound ≠ demonstrated); grounding nunca promove |
| AC-8 | PASS | resposta publicada "109 processos" == métrica autoritativa SATISFIED |
| AC-9 | PASS | 2 POSTs reais `POST /interaction/turns` (`turn1/turn2-response.sanitized.json`, request_ids distintos) + `test_http_m_positive_two_turn_clarification_and_recovery` |
| AC-10 | PASS | turn-2 `context` construído do corpo da resposta do turn-1 (`c3_t2_http_multiturn_live_eval.py:140-155`); rota `_parse_context` valida (`interaction_routes.py:467-546`) |
| AC-11 | PASS | turn-1 NON_GROUNDED, sem provenance, pede só o identificador; consulta indevida ausente |
| AC-12 | PASS | turn-2 preserva objetivo, usa 90260921 informado, provenance `get_product_structure` READ completo |
| AC-13 | PASS | GROUNDED + conteúdo real DAVI (CHICOTE 90260921 + componente 10020003) |
| AC-14 | PASS | M1: `HandleInteractiveConversationTurn` real → `_require_access` fail-closed → 403/`forbidden` (`handle_interactive_turn.py:858-863`); M4: `invented_record_tokens` bloqueia código só citado em DELIA_RESULT |
| AC-15 | PASS | M1/M2/M4/M5/M10 pytest; M3/M6–M9 PENDING declarado — condizente com "disponibilidade de identidades autorizadas" do próprio AC |
| AC-16 | PASS | gate é token-interseção mecânica (sem hardcode de produto/owner); casos S cobrem entidades/owners irmãos |
| AC-17 | TEST_NOT_RUN | `docker exec` bloqueado pelo hook do verificador; host sem flask/pydantic_ai. Logs `directed-pytest.log` (29) e `regression-pytest.log` (119) íntegros e consistentes; desk-check mecânico aprova todos os testes novos |
| AC-18 | PASS | eval-only two-agent em container isolado (`run_c3_t2_http_multiturn_live.sh` prova separação do prod), modelo qwen3-14b + fingerprint e4a5b706 gravados |
| AC-19 | PASS | `.git/delpi-verifier/requests/2026-11-16-c3t2-entity-http-verifier-r1.md` contém 36 blocos RQ/AC integrais (grep 36/36) |
| AC-20 | PASS | verificação executada por motor independente; sem residual crítico nem omissão de RQ/AC |
| AC-21 | PENDING | escopo working tree pré-commit por contrato — URLs GitHub só existem após push |
| AC-22 | PENDING | idem: commit/push/CI ocorrem após este veredito (sequência autorizada) |

## Alegações do executor × realidade

| Alegação | Resultado | Evidência |
|---|---|---|
| WS-1 gate + S2/S3 fail-closed | CONFIRMADA | código `:3394-3411,:3484,:3650`; testes novos corretos por desk-check |
| G2 live GROUNDED+SATISFIED entity=process 109 | CONFIRMADA | `positive.sanitized.json` + `.battery/…/INT2_G2_aggregation_active_scope.jsonl` |
| WS-2 dois POSTs + context canônico + TURN2_GROUNDED | CONFIRMADA | `http-multiturn-live.json` + artefatos sanitizados consistentes |
| M1/M2/M4/M5/M10 pytest PASS | NAO_VERIFICAVEL | testes existem e são logicamente corretos; execução bloqueada pelo hook |
| directed 29 / regression 119 PASS | NAO_VERIFICAVEL | logs completos e internamente consistentes; não reproduzível (hook) |
| V024 restaurado ao checksum aplicado 8f9c97 | CONFIRMADA | `sha256sum` do arquivo = `8f9c97…` = checksum live documentado; == `git show e94e3f9989:…` |
| Escopo de stage + WIP preservado | CONFIRMADA | apenas V024 staged; demais WIP (api-delpi/plugins/shared/docs davi) intocado no stage |

## Comandos executados

| Comando | Saída (exit) | Trecho relevante |
|---|---|---|
| `git rev-parse HEAD; git rev-list --left-right --count origin/main...HEAD` | 0 | `e38940c0c6` == origin/main, `0 0` |
| `git diff delia-api/…/semantic_capability_support.py` | 0 | +`_obligation_declared_entity_tokens`, +`_attempt_business_entity_congruent`, gates nas duas funções |
| `git diff HEAD -- api-delpi/…/V024__prc_record_flags.sql` | 0 | CHECK `flag.*` → `created|updated|resolved|removed` |
| `git show e94e3f9989:…/V024…sql | md5sum` vs `md5sum` do arquivo | 0 | ambos `55ceca082dab06a03f3a3c0eb91dad94` |
| `sha256sum api-delpi/…/V024…sql` | 0 | `8f9c9753…cf73e` = checksum live `schema_migrations` documentado |
| `sha256sum delia-api/app/…/semantic_capability_support.py` | 0 | `e4a53b22…` == hash em `manifest.json` (evidência não-stale) |
| `docker exec delpi-delia-api python -m pytest …` | BLOQUEADO | hook delpi-verifier: docker exec altera estado → TEST_NOT_RUN |
| `pytest --noconftest` (venv do repo, host) | exit 4 | `ModuleNotFoundError: pydantic_ai` — host sem deps do serviço |
| `ast.parse` nos 4 arquivos novos/alterados delia-api | 0 | SYNTAX_OK em todos |
| `git status --porcelain --ignored=matching delia-api/` | 0 | `,str(p.get(proposal))[:150])\n` é tracked pré-existente (commit be614649b7) |
| `grep -c '^## RQ-\|^## AC-'` no request canônico | 0 | 36 blocos (14 RQ + 22 AC) integrais |
| `git log --oneline --all -- …/V024…sql` | 0 | `3a95d6a3e7` regravou divergente; `e94e3f9989` tem o conteúdo aplicado |

## Ordens de correção

nenhum

## Decisões necessárias (DECISION_REQUIRED)

| Id | Decisão | Opções | Impacto de cada opção |
|---|---|---|---|
| — | nenhum | — | — |

## Ordens anteriores (rodadas 2 e 3)

| Ordem | Situação | Evidência |
|---|---|---|
| — | nenhum (rodada 1) | — |

## Observações (não bloqueiam)

- **`{REQ}` na raiz do working tree** (untracked, 8 KB, mesmo timestamp do request canônico): rascunho duplicado do pedido de verificação. O contrato (`AGENTS.md` §A) prevê requests só em `<git-dir>/delpi-verifier/requests/` — a cópia canônica existe e está correta; o arquivo solto é resíduo de geração. Não está no stage nem no escopo declarado; deve ser removido antes do commit para não entrar acidentalmente. Confiança 75 (higiene, não defeito).
- **Bypass teórico via `source in tokens`**: `_attempt_demonstrates_anchored` só exige congruência quando `source not in tokens`. Se um owner ecoar token de apresentação (`view`/`shape="summary"`) no vocabulário, o caminho strict-anchor satisfaz sem checagem de entidade. É semântica pré-existente do sistema de âncoras (o eco é a própria prova de tipo), não introduzida pelo diff. Confiança 50.
- **Turn-1 via fallback**: a clarificação live ocorreu após `comprehension_handoff=comprehension_agent_error` — declarado em `scope-reconciliation.md`. AC-11 satisfeito em substância (pediu só o identificador, nenhuma consulta), mas não pelo fluxo primário.
- **M3/M6/M7/M8/M9 live PENDING**: declarado e condizente com o texto do AC-15; os mecanismos estão cobertos por fixture de contrato (M1 com handler real, `invented_record_tokens`).
- **Evidência live gerada em DEV com WIP concorrente no api-delpi**: `get_product_structure` existe no HEAD commitado (verificado na allowlist em HEAD), então a capability não depende do WIP; mas o ambiente continha trabalho de outra task. Risco baixo.
- **Arquivo tracked de 0 bytes `delia-api/,str(p.get(proposal))[:150])\n`** (nome com newline): pré-existente, commitado em `be614649b7` (14/nov), fora do escopo. Resíduo de redirect quebrado de sessão anterior — sugestão de higiene ao owner, não bloqueia.
- **Dirs de artefato untracked** (`plugins/controllership-finance/e2e/artifacts/`, `engineering/e2e/artifacts-d16/`, `tv-dashboard-presentation/artifacts/`, `tv-dashboard-api/data/`): de tasks concorrentes; preservação correta, mas merecem limpeza pelos próprios donos.
- **`_agg_ob` fixture alterado** (adição de `entity: "process"`): justificado por AC-3 — o contrato agora exige entidade declarada; os testes existentes (S1,S4,S5,S6,S6b,S7,S9) mantêm os mesmos desfechos por desk-check (S7 vira UNSATISFIED por contradição de `entity=` antes mesmo do anchor; resultado idêntico).

## Não verificado

- **Execução dos pytest direcionado/regressão** (comandos `docker exec delpi-delia-api python -m pytest …`): bloqueados pelo hook do verificador (`docker exec` classificado como alteração de estado). Tentativa legítima no host falhou por ausência de `flask`/`pydantic_ai` no `.venv` do repo — instalação de dependências é proibida ao verificador. Mitigação: desk-check mecânico linha-a-linha dos 4 testes novos contra `semantic_capability_support.py`, `interaction_routes.py` e `handle_interactive_turn.py`; logs do executor íntegros e consistentes com os arquivos.
- **AC-21/AC-22** (pacote GitHub, commit/push, CI): estruturalmente impossíveis em escopo `working tree` — verificação precede publicação por desenho do contrato.
- **Estado real do `schema_migrations` no banco DEV**: checksum `8f9c97…` vem da evidência documentada (`env-davi-unblock.md`); não consultei o banco diretamente — mas o hash do arquivo confere exatamente com o valor alegado, o que torna a alegação altamente provável.
- **Sanidade da suíte DÉLIA completa** além dos 4 arquivos do comando de regressão: grep indica que nenhum outro teste usa `evidence_source` de classe apresentação sob `delivery="aggregation"`, limitando a superfície de regressão ao escopo executado.
- `git fetch` para confirmar `origin/main` remoto real (hook bloqueia fetch; usei refs locais — `origin/main` pode estar stale em relação ao remoto, risco baixo dado HEAD curto recente).
