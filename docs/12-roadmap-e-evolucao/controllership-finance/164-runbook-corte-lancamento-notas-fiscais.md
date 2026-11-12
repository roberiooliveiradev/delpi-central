# 164 — Runbook do corte F5 · Lançamento de Notas Fiscais (api-delpi → BFF)

> Status: **DRAFT** (F4 — não executar)
> Owner de execução: operador de plataforma + PO (janela combinada)
> Schema: **imutável** no corte (V001–V014; sem apply)

---

## 1. Pré-requisitos (checklist)

| # | Item | Critério |
|---|---|---|
| P1 | Passo 2 F4 (PROD RO) | Ledger 14/14 = SHA256SUMS BFF; contagens capturadas |
| P2 | Paridade HML | Suíte api-delpi × BFF HML com `compare_golden` diffs=0 (exceto D8); **bloqueado** até existir BFF no stack HML (ver DECISION_REQUIRED F4) |
| P3 | Imagem BFF | Contém bounded context `invoice_posting` + runner verify |
| P4 | Envs PROD BFF | `LNF_HOSTED_ENABLED`, `LNF_MIGRATIONS_MODE=verify`, `LNF_*`, `PLUGINS_DB_*`, `TOTVS_DB_*`, `FINANCIAL_API_*`, `CORE_API_*`, `API_DELPI_INTERNAL_SERVICE_TOKEN` |
| P5 | Volume DANFE | Mount host → `LNF_DANFE_UPLOAD_DIR` na BFF (hoje ausente no container PROD) |
| P6 | Rede | BFF alcança Protheus SQL, financial-api, Core (TCP/health) |
| P7 | D9 Chat/TV | Painéis/provider LNF inventariados; uso>0 ⇒ decisão do owner antes do corte |
| P8 | Janela | Congelamento curto combinado; rollback ensaiado (redeploy) |
| P9 | Quem executa | Operador faz deploy; PO valida smoke; Chat/TV regen com dono do catálogo |

---

## 2. Sequência do corte (comandos)

Ordem fixa. Não inverter. Sem `LNF_MIGRATIONS_MODE=apply`.

### (1) Aviso / congelamento curto

- Comunicar usuários do MFE LNF (fila congelada ~15–30 min).
- Pausar operações manuais de conciliação (`reconciliation/run`).

### (2) Deploy da BFF de PROD com LNF ligado

No checkout canônico de produção (`~/projetos/delpi-central` em `srv-api`):

```bash
git pull --ff-only
# Garantir em infra/.env (não commitado): LNF_HOSTED_ENABLED=true
# LNF_MIGRATIONS_MODE=verify
# Mount DANFE: ${DELPI_DATA_HOST_DIR}/lancamento-notas-fiscais-danfe
./infra/scripts/up-prod-sequential.sh --build controllership-finance-api
```

Verificar:

```bash
docker exec delpi-controllership-finance-api printenv LNF_HOSTED_ENABLED LNF_MIGRATIONS_MODE
curl -sS -o /dev/null -w '%{http_code}\n' \
  https://minhadelpi.com.br/apps/controllership-finance-api/lancamento-notas-fiscais/requests?page=1
# esperado: 401/403 com token inválido — NÃO 404
```

Se o runner verify falhar no boot (checksum), **parar** e rollback da BFF.

### (3) Deploy da api-delpi SEM o módulo LNF

Código F5 (ainda não nesta fase): remover router LNF + runner do schema no startup da api-delpi.

```bash
./infra/scripts/up-prod-sequential.sh --build api-delpi
curl -sS -o /dev/null -w '%{http_code}\n' \
  https://minhadelpi.com.br/apps/api-delpi/lancamento-notas-fiscais/requests?page=1
# esperado: 404
```

### (4) Build/deploy do MFE

Alterar `API_BASE` para:

```text
/apps/controllership-finance-api/lancamento-notas-fiscais
```

Rebuild `lancamento-notas-fiscais` / `plugin-ui` conforme pipeline canônico; deploy via compose sequencial.

### (5) Regenerar catálogos Chat / TV

- Reimport OpenAPI da api-delpi (sem operations LNF) e da BFF (com operations LNF), conforme owners dos catálogos.
- Invalidar/republish painéis TV que referenciem `*_lancamento_notas_fiscais_*` se ainda existirem.

### (6) Gateway

Só se faltar location `/apps/controllership-finance-api/` (PROD já tem em `gateway/nginx.conf`). Não editar gateway “por precaução”.

---

## 3. Verificação pós-corte

| Check | Como |
|---|---|
| Smoke federado filial-01/02 | Perfis reais create/process/view; list/get/create/start |
| Contagens | Mesmo SQL do Passo 2b — iguais ao baseline pré-corte |
| Notificação | Block cross-user → inbox com `sourceApp=lancamento-notas-fiscais` |
| PDF/XML | DANFE + received-invoice binários (hash) |
| Refresh | `reconciliation/refresh` cooldown 45 s |
| AuthZ D8 | Service token **não** bypassa na BFF |

---

## 4. Rollback

| Situação | Ação |
|---|---|
| BFF verify falha / 5xx LNF | Redeploy imagem BFF anterior; `LNF_HOSTED_ENABLED=false` |
| MFE quebrado | Redeploy MFE com `API_BASE` antigo (`/apps/api-delpi/...`) |
| Corte completo instável | Redeploy api-delpi **com** módulo + MFE antigo + BFF dark |
| Schema | **Não** rollback de migration — dados permanecem válidos para ambos |

Tempo estimado de rollback: 15–25 min (pull + up sequencial dos 2–3 serviços).

---

## 5. RACI e tempo

| Papel | Responsabilidade | Tempo estimado |
|---|---|---|
| Operador | (2)(3)(4)(6), rollback | 45–90 min |
| PO | (1), smoke (3) | 20–40 min |
| Owner Chat/TV | (5) | 20–40 min |
| Janela total | — | **~2 h** (com margem) |

---

## 6. Fora deste runbook

- `LNF_MIGRATIONS_MODE=apply` em qualquer ambiente
- Mutação SSH/rsync dentro do container
- Dual-write api-delpi + BFF
- Alterar checksums V001–V014
