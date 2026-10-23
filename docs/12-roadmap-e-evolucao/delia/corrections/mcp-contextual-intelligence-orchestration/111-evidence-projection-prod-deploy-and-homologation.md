# 111 — Deploy produtivo + homologação RC1/RC2 (srv-api)

`DELIA-C3-EVIDENCE-PROJECTION-PROD-DEPLOY-AND-HOMOLOGATION-01` · 2026-10-23 · executor: Devin · HEAD `287f94a2aad` (worktree `delia-budget-contract-wt`)

Implantação e homologação da remediação RC1+RC2 (commit `86294797d1`) em produção. Resultado principal: **o fix já estava implantado e comprovado em runtime** — a task concorrente de fechamento residual G4 havia integrado e deployado `caac5f5452` (que carrega `86294797d1` por rebase) poucos minutos antes. Esta task re-verificou a cadeia completa de evidência e mapeou o único bloqueio restante: ausência de credencial de teste governada em prod.

## 1. Verificação de implementação e deploy

| item | evidência |
|---|---|
| Remediação ancestral do HEAD deployado | `86294797d1` ∈ ancestors de `caac5f5452` (integrada por rebase na task G4) |
| Checkout prod | `srv-api:~/projetos/delpi-central` em `caac5f5452` → sincronizado ff-only para `287f94a2a` (delta docs-only — zero efeito runtime) |
| Código no runtime | `delpi-delia-api` (imagem `cf66b56c6022`, built 14:32 UTC — após o commit do fix 14:26 UTC): `_without_control_plane` ×5, `_is_capability_descriptor` ×2, `_CAPABILITY_VOCABULARY_KEYS` ×4 presentes no `orchestration.py` em execução |
| Regime 60/3/300 | `LLM_TIMEOUT=60`, `MODEL_STAGE=60`, `TURN=300`, `TOTAL=300`, `CALL_MAX_ATTEMPTS=3` — preservados |
| Governed resume | `DELIA_MAX_GOVERNED_ATTEMPTS` inalterado (gate próprio) |
| LLM produtivo | `DELIA_LLM_MODEL=moonshotai/kimi-k3` (OpenRouter — identificador real observado) |
| CRI | `DELIA_RESPONSE_INTELLIGENCE_ENABLED=true` |
| Saúde | `delpi-delia-api` healthy; `/health` 200 via gateway; `/interaction/turns` 401 sem credencial (AuthN fail-closed); zero erros nos logs do container; zero 502/504 no gateway |
| Migrations | zero |
| AuthZ/Core/Domain/policy/writes | inalterados |

`DEPLOY_STATUS=ALREADY_DEPLOYED_VERIFIED` — nenhuma recriação necessária; o runtime correto estava ativo antes desta task executar o passo de build (evidência: marcadores de código presentes no arquivo em execução, timestamp da imagem posterior ao merge, container healthy).

## 2. Pre-deploy gates (registrados como pós-verificação de deploy já-executado)

`EXISTING_EQUIVALENT=YES` · `REUSE_DECISION=EXTEND` · owner canônico preservado · contratos preservados · 6 testes RED originais GREEN em HEAD · suíte backend completa GREEN no SHA implantado · zero migrations · AuthZ/policy/writes inalterados · correção na fronteira canônica de projeção — todos confirmados no código efetivamente em execução.

## 3. Testes produtivos autenticados (D4/D5/D8)

**TEST_NOT_RUN — bloqueio de credencial governada.**

A task exige "identidade de teste legitimamente autorizada, Core AuthZ ativo e MCPs reais". Estado real em prod:

- Realm `delpi` (prod) contém apenas usuários reais (`rober`, `michael`, `dennis`, `jose`, `fabiano`, `max`, `admin`) — **nenhuma identidade de teste/homologação existe** (`user_entity` consultado read-only).
- O client `delpi-central` suporta password grant (`direct_access_grants_enabled=true`), mas não existe senha de usuário de teste — e usar/resetar credenciais de usuários reais é proibido (AuthZ boundary; §10/§13 da task).
- `KEYCLOAK_ADMIN` existe no host, mas criar usuário ou alterar credenciais modifica estado de identidade — fora da autorização desta task ("não modificar secrets ou credentials", "não alterar o fluxo de autorização").
- Service-account/client_credentials não produz subject token de usuário (Core `/me` + delegated exchange exigem identidade de pessoa).
- Residual documentado idêntico em docs 95/106 e ledger §6.388/G4: "smoke real aguarda sessão de usuário legítimo — não se cunhou credencial de teste em prod."

Consequência: a homologação autenticada D4/D5/D8 em prod é **TEST_NOT_RUN** — requer sessão manual do PO no Portal ou uma identidade de teste governada criada por decisão do owner de identidade. O código remediado está ativo; a evidência de não-vazamento em runtime de prod só pode ser capturada por essa sessão.

### Evidência substituta (não substitui a homologação)

- Prova determinística em HEAD: 30 testes na suíte de discovery incluindo envelopes reais DAVI/VISTA capturados — zero projeção de control-plane, catálogo nunca promovido a business record.
- Live Ollama dev (20 turnos, cadeia real idêntica): zero leak em qualquer campo do output.
- A lógica remediada é independente do modelo: o vazamento era determinístico na projeção, não uma decisão do LLM — portanto o comportamento de prod com Kimi está coberto pela mesma fronteira de projeção (a seleção do modelo pode variar, mas os campos de controle nunca alcançam a projeção user-facing).

## 4. Campos de homologação (TEST_NOT_RUN — sem execução paga)

| campo | D4 | D5 | D8 |
|---|---|---|---|
| OWNER/CAPABILITY/GROUNDING/OUTCOME/LATENCY/TOKENS | TEST_NOT_RUN | TEST_NOT_RUN | TEST_NOT_RUN |
| RC1_RC2_RESULT | CODE_DEPLOYED+TEST_NOT_RUN | CODE_DEPLOYED+TEST_NOT_RUN | CODE_DEPLOYED+TEST_NOT_RUN |

`EXTERNAL_LLM_CALLS=0` nesta task — nenhuma chamada paga executada; `TOKEN_USAGE_SOURCE=provider (não exercitado)`.

## 5. Segurança

- AuthN fail-closed verificado (401 sem credencial); AuthZ/audit/gates inalterados.
- Nenhum metadado de control-plane executado como instrução — a superfície provada determinística cobre todas as vias de saída (`contract_facts`, CRI, conteúdo determinístico).
- Observabilidade/telemetria podem legitimamente mencionar nomes técnicos — distinção preservada.
- Nenhum secret/credencial alterado; nenhum usuário criado/modificado.
- Imunidade universal a prompt injection NÃO é reivindicada — a remediação cobre as vias de projeção conhecidas.

## 6. Resultado separado por camada

- **TECHNICAL DEPLOYMENT**: PASS — runtime correto (`caac5f5452` ⊃ `86294797d1`), healthy, zero erros, regime 60/3/300 preservado.
- **RC1/RC2 CORRECTION**: CODE_DEPLOYED_VERIFIED — control-plane não projetável, catálogos não promovíveis, records legítimos preservados (determinístico em HEAD + live dev). Runtime-prod outcome = TEST_NOT_RUN (credencial).
- **SEMANTIC QUALITY**: TEST_NOT_RUN (não avaliável sem turnos autenticados; modelo Kimi distinto do 3B local).
- **USER OUTCOME**: TEST_NOT_RUN.
- **BUSINESS OUTCOME**: TEST_NOT_RUN.
- **ROLLBACK**: disponível — imagem anterior `eec7be0f913c`/`b05a0f35b52c` no host + checkout anterior; não executado (nenhuma regressão).

## 7. Resíduos

1. Homologação autenticada D4/D5/D8 em prod: **PENDENTE** — requer identidade de teste governada (decisão do owner de identidade/PO) ou sessão manual do PO.
2. RC3–RC7 permanecem fora de escopo conforme autorização.
3. Delta `caac5f5452 → 287f94a2a` no checkout prod = docs-only (controllership/supplies); imagem runtime intocada.
4. `EXECUTION_DRIFT=NONE` — a descoberta de deploy-concorrente foi verificada e absorvida (mesma mudança, nenhum conflito).

## 8. Veredicto d'executor

`DEPLOY_VERIFIED_HOMOLOGATION_BLOCKED_BY_CREDENTIAL` — a versão produtiva contém a remediação RC1+RC2 provada por marcadores de código em execução, imagem pós-merge e suíte green no SHA; a comprovação de não-vazamento no usuário real exige a sessão autenticada que só uma credencial governada (PO) pode fornecer. Recomendação: PO executa as 3 perguntas no Portal (mesma bateria D4/D5/D8) ou autoriza criação de identidade de homologação no realm prod.
