# 164 — Runbook do corte F5 · Lançamento de Notas Fiscais (api-delpi → BFF)

> Status: **DRAFT atualizado F4b** (ensaio HML em andamento; PROD intocado)
> Owner de execução: operador de plataforma + PO (janela combinada)
> Schema: **imutável** no corte (V001–V014; sem apply)
> Princípio: o corte é **troca de configuração** (flags). Defaults = comportamento atual.

---

## 0. Flags de corte (default = AS-IS)

| Flag | Onde | Default | Corte | Rollback |
|---|---|---|---|---|
| `LNF_HOSTED_ENABLED` | BFF (`controllership-finance-api`) | `false` | `true` (+ `LNF_MIGRATIONS_MODE=verify`) | `false` |
| `LNF_MODULE_ENABLED` | api-delpi | `true` | `false` (router não monta; runner ignora schema LNF) | `true` |
| `VITE_LNF_API_BASE` | build MFE `lancamento-notas-fiscais` | `/apps/api-delpi/lancamento-notas-fiscais` | `/apps/controllership-finance-api/lancamento-notas-fiscais` | default |

Com defaults, qualquer deploy futuro de PROD **não muda** o comportamento.

---

## 1. Pré-requisitos (checklist)

| # | Item | Critério | Estado F4b |
|---|---|---|---|
| P1 | Ledger PROD | 14/14 = SHA256SUMS | OK (F4) |
| P2 | Ensaio HML completo | before/after golden diffs=0; rollback | EM ANDAMENTO |
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

Prova: LNF deixa de ser 404; verify do ledger passa no boot.

### (3) api-delpi `LNF_MODULE_ENABLED=false`

```bash
# HML: infra/.env.hml
sed -i 's/^LNF_MODULE_ENABLED=.*/LNF_MODULE_ENABLED=false/' infra/.env.hml
./infra/scripts/up-hml-sequential.sh --build api-delpi
# Prova: /apps/api-delpi/lancamento-notas-fiscais/* → 404
```

### (4) MFE rebuild com base da BFF

```bash
# HML
sed -i 's|^VITE_LNF_API_BASE=.*|VITE_LNF_API_BASE=/apps/controllership-finance-api/lancamento-notas-fiscais|' infra/.env.hml
./infra/scripts/up-hml-sequential.sh --build lancamento-notas-fiscais
# grep no dist: controllership-finance-api/lancamento-notas-fiscais
```

### (5) Catálogos Chat/TV

Scripts `sync-api-delpi-openapi*.sh` se os serviços existirem no ambiente. HML: só se chat/TV HML estiverem no stack (hoje tipicamente não).

### (6) Gateway

HML: location `/apps/controllership-finance-api/` já no snippet (F4b). PROD: já em `nginx.conf`.

---

## 3. Rollback (ensaio HML = mesma ordem inversa)

1. MFE: `VITE_LNF_API_BASE=/apps/api-delpi/lancamento-notas-fiscais` + rebuild  
2. api-delpi: `LNF_MODULE_ENABLED=true` + rebuild  
3. BFF: `LNF_HOSTED_ENABLED=false` + rebuild  

Schema único → dados criados na janela BFF continuam visíveis via api-delpi.

---

## 4. Tempos medidos (HML F4b — Passo 1)

| Etapa | Comando | Tempo | Resultado |
|---|---|---|---|
| Build+up BFF HML (flag off) | `up-hml-sequential.sh --build controllership-finance-api` | ~28 s (1ª) / ~14 s (rebuild 404) | healthy; `LNF_HOSTED_ENABLED=false` |
| Rebuild gateway | `up-hml-sequential.sh --build gateway` | ~20 s | healthy; location CF ativa |
| Prova dark | curl health / LNF / closing | <1 s | health **200**; LNF **404**; closing **401** (auth) |

Ensaio completo do corte (Passo 3 F4b): preencher após execução.

---

## 5. Go / no-go

**GO** somente se:

- Ensaio HML before/after `diffs=0` (exceto D8) + rollback PASS  
- PROD: imagem com `invoice_posting`, mount DANFE, envs LNF, TCP OK  
- PENDING_OWNER 2d/2e resolvidos ou aceitos pelo owner  

**NO-GO** se verify do ledger falhar, dual-write, ou consumers não mapeados com uso > 0.

---

## 6. Problemas encontrados (F4b)

1. `depends_on: postgres-plugins` quebrou profile isolado → `depends_on: !override {}`  
2. JWT global devolvia 401 em path LNF dark → 404 explícito no middleware quando `LNF_HOSTED_ENABLED=false`  
3. HML sem `financial-api` → binários INCONCLUSIVE no ensaio  
4. Checkout HML em `projetos-teste` — pull ff-only após push em `origin/main`
