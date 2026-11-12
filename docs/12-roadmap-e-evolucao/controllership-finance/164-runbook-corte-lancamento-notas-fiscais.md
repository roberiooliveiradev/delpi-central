# 164 — Runbook do corte F5 · Lançamento de Notas Fiscais (api-delpi → BFF)

> Status: **F5a DONE** — dark PROD BFF+MFE+api-delpi; **F5b** pendente de janela  
> Owner de execução: operador de plataforma + PO (janela combinada)  
> Schema: **imutável** no corte (V001–V014; sem apply)  
> Princípio: o corte é **troca de configuração** (flags). Defaults = comportamento atual.  
> HEAD prep: `fdc31ad48e` + imagens dark 2026-11-12

---

## 0. Flags de corte (default = AS-IS)

| Flag | Onde | Default | Corte | Rollback |
|---|---|---|---|---|
| `LNF_HOSTED_ENABLED` | BFF (`controllership-finance-api`) | `false` | `true` (+ `LNF_MIGRATIONS_MODE=verify`) | `false` |
| `LNF_MODULE_ENABLED` | api-delpi | `true` | `false` (router não monta; runner ignora schema LNF) | `true` |
| `VITE_LNF_API_BASE` | build MFE `lancamento-notas-fiscais` | `/apps/api-delpi/lancamento-notas-fiscais` | `/apps/controllership-finance-api/lancamento-notas-fiscais` | default |
| `LNF_NOTIFICATIONS_ENABLED` | BFF | `false` em HML example | `true` no ensaio para smoke de inbox | valor AS-IS do ambiente |

Com defaults, qualquer deploy futuro de PROD **não muda** o comportamento.

---

## 1. Pré-requisitos (checklist)

| # | Item | Critério | Estado F4b |
|---|---|---|---|
| P1 | Ledger PROD | 14/14 = SHA256SUMS | OK (F4) |
| P2 | Ensaio HML completo | before/after golden + rollback | **PASS** (D8 único; rollback OK) |
| P3 | Imagem BFF com `invoice_posting` | presente no artefato | HML OK; **PROD ainda sem** (deploy dark pendente) |
| P4 | Envs LNF na BFF | nomes em `.env` | HML OK; **PROD nomes adicionados F5a** |
| P5 | Mount DANFE na BFF | volume host | HML OK; host PROD dir existe; compose volume versionado F5a |
| P6 | Rede BFF→SQL/financial/Core | TCP/health | preflight DEV 5/5; HML 4/5 (sem financial-api) |
| P7 | D9 Chat/TV | risco aceito owner | **ACEITO 2026-11-12** |
| P8 | Logs 7d callers (F4 2e) | risco aceito owner | **ACEITO 2026-11-12** |
| P9 | Janela + RACI | combinados | — |
| P10 | Gate commits PROD→HEAD | só LNF ou owner aceita | **ACEITO owner** (pacote api-delpi main + F5a.4-API) |

---

## 1b. Riscos aceitos pelo owner (2026-11-12)

- **D9 Chat/TV** — seguir sem inventário prévio de usage em PROD.
- **Logs 7 dias** — seguir sem análise de callers.

Ver ADR-001 adendo F5a.

---

## 1c. Preparação dark F5a (estado)

| Item | Estado |
|---|---|
| Smoke MFE HML federado | PASS (artefatos em `tests/contracts/.../playwright-artifacts/f5a-smoke/`) + HML ROLLED BACK |
| Preflight CLI | `python -m controllership_finance_app.interface.cli.lnf_preflight` · DEV **5/5 PASS** · HML **4/5** (financial FAIL esperado) |
| `docker-compose.yml` BFF | `LNF_HOSTED_ENABLED=false` explícito, verify, TOTVS/FINANCIAL/CORE/token, volume DANFE |
| `docker-compose.yml` api-delpi | `LNF_MODULE_ENABLED=true` explícito |
| MFE | default `VITE_LNF_API_BASE` = api-delpi (sem build-arg) |
| `infra/.env` PROD | nomes `LNF_HOSTED_ENABLED=false`, `LNF_MIGRATIONS_MODE=verify`, `LNF_MODULE_ENABLED=true` adicionados |
| Deploy dark PROD | **EXECUTADO 2026-11-12** — BFF + MFE + api-delpi (exceção R4 + F5a.4-API); preflight 5/5; obs. 15 min OK |

### Baseline PROD (antes do dark, 2026-11-12)

| Superfície | Medida |
|---|---|
| BFF OpenAPI | **112** paths · **0** LNF |
| BFF LNF requests | N/A (módulo ausente na imagem) |
| api-delpi OpenAPI LNF | **22** paths |
| MFE bundle | `/apps/api-delpi/lancamento-notas-fiscais` (imagem de **2026-10-29**) |

---

## 1d. Gate de commits (F5a Passo 3) — DECISION_REQUIRED

| Serviço | Imagem PROD (aprox.) | → `origin/main` | Só LNF? |
|---|---|---|---|
| `controllership-finance-api` | sem `invoice_posting`; competences = `6c84b5939f` | `7403fcc527`…`496644bbb7` (F3+F5a) | **SIM** |
| `lancamento-notas-fiscais` | 2026-10-29 | `00b6704d8f` (CT-e) + `04ddc620bc` (flag MFE) | **SIM** (domínio LNF) |
| `api-delpi` | `main.py` = `3fe374279f` | **dezenas** de commits (supplies, quality, PRC, PCP, INT-1, LNF flag `04ddc620bc`, …) | **NÃO** |

**Pare e reporte:** rebuild de `api-delpi` na preparação dark **não é limpo**. Owner deve decidir se sobe o pacote inteiro ou se isola cherry-pick/`LNF_MODULE_ENABLED` de outro modo.

Até decisão: **não executar Passo 4** (deploy dark).

---

## 2. Sequência do CORTE (após dark em PROD)

Ordem fixa. Sem `apply`. Já com imagens dark:

1. BFF: `LNF_HOSTED_ENABLED=true` + restart/`up-prod-sequential.sh --build controllership-finance-api`  
2. api-delpi: `LNF_MODULE_ENABLED=false` + restart  
3. MFE: build com `VITE_LNF_API_BASE=/apps/controllership-finance-api/lancamento-notas-fiscais` + deploy  
4. Regenerar catálogos chat/TV (`sync-api-delpi-openapi*.sh`)  
5. Verificações: BFF LNF 200; api-delpi LNF 404; Network MFE só BFF; preflight PASS; smoke fila  

Rollback = ordem inversa das flags + rebuilds.

---

## 3. Rollback (ensaio HML = mesma ordem inversa)

1. MFE: `VITE_LNF_API_BASE=/apps/api-delpi/lancamento-notas-fiscais` + rebuild  
2. api-delpi: `LNF_MODULE_ENABLED=true` + rebuild  
3. BFF: `LNF_HOSTED_ENABLED=false` + rebuild  

Schema único → dados criados na janela BFF continuam visíveis via api-delpi.

**F4b prova:** após rollback, api-delpi list **200** com registros `cancelled`/`posted` da janela; BFF LNF **404**; MFE bundle de volta a `/apps/api-delpi/lancamento-notas-fiscais`; AuthZ **314/314**.

---

## 4. Tempos medidos (HML F4b)

| Etapa | Comando | Tempo | Resultado |
|---|---|---|---|
| Build+up BFF (flag off, Passo 1) | `up-hml-sequential.sh --build controllership-finance-api` | ~28 s / ~14 s | healthy; LNF **404** |
| Gateway HML | `up-hml-sequential.sh --build gateway` | ~20 s | location CF ativa |
| Provision usuários contrato | `provision_dev_users.py` + `LNF_PROVISION_ENV=…/.env.hml` | ~13 s | P0–P12 OK |
| AuthZ baseline (api-delpi) | `pytest test_authz.py` + pacing 0,12 s | **44,8 s** | **314/314** |
| Suíte baseline (golden-hml-before) | authz+contract+combined+notify | **51 s** | 328 passed / 3 skipped; files=28 |
| Corte BFF on | rebuild CF | **11,4 s** | verify V001–V014 OK; LNF **401→200** c/ JWT |
| Corte api-delpi off | rebuild api-delpi | **17,6 s** | LNF **404** c/ JWT |
| Corte MFE BFF base | rebuild MFE | **20,8 s** | dist contém BFF base |
| Suíte pós-corte (BFF) | mesma suíte | **50 s** | 328 passed; compare **files=28 diffs=1 (D8)** |
| Notify P6→P6B (BFF, notif on) | `test_notifications_cross_user.py` | ~1,3 s | **PASS** |
| Rollback MFE / api / BFF | 3 rebuilds | **15,9 + 16,3 + 11,3 s** | estado AS-IS |
| AuthZ pós-rollback | `pytest test_authz.py` | **44,7 s** | **314/314** |

### Contagens (schema `lancamento_notas_fiscais`)

| Momento | requests | por status (resumo) |
|---|---|---|
| Pré-suíte baseline | 0 | — |
| Pós-suíte before (baseline) | 6 | cancelled=5, posted=1 |
| Pós-rollback (dados da janela BFF visíveis) | 21 | cancelled=18, posted=3 |

### Golden compare

```text
python compare_golden.py golden-hml-before-clean golden-hml-after-clean
→ files=28 diffs=1
DIFF list_lancamento_notas_fiscais_requests/success-envelope.json
  (D8: data_types.items len 0 → 1 — envelope de lista com dados vs vazio)
```

### Smoke MFE / Network

- Bundle corte: `/apps/controllership-finance-api/lancamento-notas-fiscais`  
- Bundle rollback: `/apps/api-delpi/lancamento-notas-fiscais`  
- Playwright (Chromium headless no host HML): login portal + harness fetch → BFF caminho de negócio ativo; api-delpi **404** no corte. Screenshots em `/tmp/lnf-hml-playwright/` no srv.  
- Shell Portal MFE federado completo (fila UI P11/P6/P2 com Network DevTools) **parcial**: deep-link do plugin no shell HML não estabilizou no ensaio; prova de base e AuthZ/suíte cobrem o contrato.

### Catálogos

HML sem `delpi-hml` chat/TV → **N/A** (PENDING_OWNER 2d em PROD).

---

## 5. Go / no-go

**GO dark (F5a Passo 4)** somente se:

- Ensaio HML before/after `diffs=0` (exceto D8) + rollback PASS → **atendido em F4b**  
- Smoke MFE HML federado PASS + HML ROLLED BACK → **atendido em F5a**  
- Compose/env PROD dark versionados → **atendido em F5a**  
- Gate commits PROD→HEAD só LNF (ou owner aceita pacote) → **ACEITO** (api-delpi pacote main + F5a.4-API)  
- D9 / logs 7d → **risco aceito owner 2026-11-12**  
- Dark PROD BFF/MFE/api-delpi + preflight 5/5 + obs. 15 min → **DONE 2026-11-12**

**GO corte (F5b)** somente com janela combinada + preflight PROD PASS ≤1 h antes.

**NO-GO** se verify do ledger falhar, dual-write, ou consumers não mapeados com uso > 0 (D9 aceito = risco consciente).

---

## 5b. Smoke MFE HML federado (F5a Passo 0)

Artefatos: `tests/contracts/lancamento-notas-fiscais/playwright-artifacts/f5a-smoke/` · Network: **to_bff=19 · to_api_delpi=0**.

| Perfil | Ações | Resultado |
|---|---|---|
| P11 | fila filial-01, filtros, criar, filial-02 bloqueada | PASS |
| P2 | fila filial-01; não vê filial-02 | PASS |
| P6 | shell sem `process` → **P6B** (view+process) | P6 N/A → P6B |
| P6B | fila, detalhe, iniciar, bloquear, comentar, retomar | PASS |

HML deixado **ROLLED BACK** após o smoke.

---

## 6. Problemas encontrados (F4b)

1. `depends_on: postgres-plugins` quebrou profile isolado → `depends_on: !override {}`  
2. JWT global devolvia 401 em path LNF dark → 404 explícito no middleware quando `LNF_HOSTED_ENABLED=false`  
3. HML sem `financial-api` → binários INCONCLUSIVE no ensaio  
4. Checkout HML em `projetos-teste` — pull ff-only após push em `origin/main`  
5. Matriz AuthZ estourava `limit_req` (429) → pacing 0,12 s no `ContractClient` quando host HML  
6. Suíte TLS HML → `SSL_CERT_FILE` / `_tls_verify()` no client  
7. Bootstrap HML: usar `LNF_BOOTSTRAP_ADMIN_USERNAME=hml-tester@hml.invalid` (não `admin@hml.invalid`)  
8. `LNF_NOTIFICATIONS_ENABLED=false` no BFF HML → notify INCONCLUSIVE até ligar `true` no ensaio  
9. Sem JWT, api-delpi com módulo off responde **401**; com JWT → **404** (validar corte com token)  
10. Teste `test_totvs_sql_call_parity` no host HML precisa deps de app (`fastapi`) — fora do escopo gateway; **N/A runtime**

---

## 7. Estado final HML (F4b)

**ROLLED BACK** (= início do ensaio):

- `LNF_HOSTED_ENABLED=false`  
- `LNF_MODULE_ENABLED=true`  
- `VITE_LNF_API_BASE=/apps/api-delpi/lancamento-notas-fiscais`  
- BFF LNF **404**; api-delpi LNF **200**; AuthZ **314/314**
