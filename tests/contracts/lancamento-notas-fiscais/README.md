# Suíte caixa-preta — Lançamento de Notas Fiscais (F2/F2b)

Somente HTTP. Não importa `api-delpi` nem a BFF. Aborta se `LNF_BASE_URL` for produção.

## Recriar usuários DEV

```bash
python3 setup/provision_dev_users.py
```

O script é idempotente, só aceita Keycloak/Core em `localhost`/`127.0.0.1`, registra o manifesto LNF no Core DEV, cria `lnf-contract-p0`…`p9` + `p6b` e grava tokens em `.env.local` (gitignored).

Perfis relevantes para o ciclo:

| Perfil | Permission | Notas |
|---|---|---|
| P5 | `create` | Passa `@require_permission(create)`; create com filial cai em `BRANCH_FORBIDDEN` (sem view/process/manage) |
| P6 / P6B | `process` | Start/block/resume; **não** passa rotas `@require_permission(create)` |
| P7 | `manage` | Run/reconciliation; **não** passa rotas create estritas |
| P9 | superadmin | Cria em qualquer filial (bypass) |
| P11 | `create` + `view.filial-01` | Perfil combinado realista — cria na 01 |
| P12 | `create` + `view.filial-02` | Perfil combinado realista — cria na 02 |

`TOTVS_DB_HOST` do DEV aponta para ERP real (`192.168.1.230`/`DELPI`); a suíte limita `reconciliation/run` a **1× por execução**.

## Rodar

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
set -a && source .env.local && set +a
LNF_WRITE_GOLDEN=1 LNF_ALLOW_RECONCILE_RUN=1 \
  .venv/bin/python -m pytest -q
```

Estabilidade (2 execuções):

```bash
rm -rf golden-run-a golden-run-b
LNF_WRITE_GOLDEN=1 LNF_ALLOW_RECONCILE_RUN=1 .venv/bin/python -m pytest -q
cp -a golden golden-run-a
LNF_WRITE_GOLDEN=1 LNF_ALLOW_RECONCILE_RUN=1 .venv/bin/python -m pytest -q
cp -a golden golden-run-b
python3 compare_golden.py golden-run-a golden-run-b
```

Comparar goldens entre alvos:

```bash
python3 compare_golden.py golden-run-a golden-bff
```
