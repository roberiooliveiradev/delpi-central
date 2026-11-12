# 164 — Runbook do corte F5 · Lançamento de Notas Fiscais (api-delpi → BFF)

> Status: **HML ENSAIO CONCLUÍDO (ROLLED BACK)** · PROD intocado  
> Owner de execução: operador de plataforma + PO (janela combinada)  
> Schema: **imutável** no corte (V001–V014; sem apply)  
> Princípio: o corte é **troca de configuração** (flags). Defaults = comportamento atual.  
> Ensaio F4b: `2026-11-12` · checkout HML `~/projetos-teste/delpi-central` · origin/main `@50cfd2d318` (+ commits de pacing da suíte)

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
| P3 | Imagem BFF com `invoice_posting` | presente no artefato | HML OK; **PROD ainda sem** |
| P4 | Envs LNF na BFF | nomes em `.env` | HML OK; PROD faltam |
| P5 | Mount DANFE na BFF | volume host | HML OK; **PROD ausente** |
| P6 | Rede BFF→SQL/financial/Core | TCP/health | HML parcial (sem financial-api) |
| P7 | D9 Chat/TV | PENDING_OWNER | aberto |
| P8 | Logs 7d callers (F4 2e) | PENDING_OWNER | aberto |
| P9 | Janela + RACI | combinados | — |

---

## 2. Sequência do corte por flags

Ordem fixa. Sem `apply`.

### (1) Congelamento curto

Aviso aos usuários LNF; pausar `reconciliation/run`.

### (2) BFF `LNF_HOSTED_ENABLED=true`

**HML (cronometrado F4b):**

```bash
cd /home/operador/projetos-teste/delpi-central
git pull --ff-only
# infra/.env.hml
sed -i 's/^LNF_HOSTED_ENABLED=.*/LNF_HOSTED_ENABLED=true/' infra/.env.hml
# LNF_MIGRATIONS_MODE=verify
# Para smoke de notificação no ensaio: LNF_NOTIFICATIONS_ENABLED=true
./infra/scripts/up-hml-sequential.sh --build controllership-finance-api
```

**PROD (adaptar):**

```bash
cd ~/projetos/delpi-central
git pull --ff-only
# infra/.env — LNF_HOSTED_ENABLED=true; LNF_MIGRATIONS_MODE=verify
# Mount DANFE obrigatório
./infra/scripts/up-prod-sequential.sh --build controllership-finance-api
```

Prova: LNF deixa de ser 404 (com JWT → 200/envelope); verify do ledger passa no boot (`lnf_migrations_verify_ok` V001–V014).

### (3) api-delpi `LNF_MODULE_ENABLED=false`

```bash
# HML: infra/.env.hml
sed -i 's/^LNF_MODULE_ENABLED=.*/LNF_MODULE_ENABLED=false/' infra/.env.hml
./infra/scripts/up-hml-sequential.sh --build api-delpi
# Prova: /apps/api-delpi/lancamento-notas-fiscais/* → 404 (com JWT)
# Sem JWT o gateway/auth pode devolver 401 antes do 404 — validar com token.
```

### (4) MFE rebuild com base da BFF

```bash
# HML
sed -i 's|^VITE_LNF_API_BASE=.*|VITE_LNF_API_BASE=/apps/controllership-finance-api/lancamento-notas-fiscais|' infra/.env.hml
./infra/scripts/up-hml-sequential.sh --build lancamento-notas-fiscais
# grep no dist: controllership-finance-api/lancamento-notas-fiscais
```

### (5) Catálogos Chat/TV

Scripts `sync-api-delpi-openapi*.sh` se os serviços existirem no ambiente. **HML F4b:** sem chat/TV no stack `delpi-hml-*` → **N/A**.

### (6) Gateway

HML: location `/apps/controllership-finance-api/` já no snippet (F4b). PROD: já em `nginx.conf`.

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

**GO** somente se:

- Ensaio HML before/after `diffs=0` (exceto D8) + rollback PASS → **atendido em F4b**  
- PROD: imagem com `invoice_posting`, mount DANFE, envs LNF, TCP OK → **ainda faltam**  
- PENDING_OWNER 2d/2e resolvidos ou aceitos pelo owner → **abertos**

**NO-GO** se verify do ledger falhar, dual-write, ou consumers não mapeados com uso > 0.

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
