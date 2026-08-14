# Playbook — Emissão de Notas Fiscais

> **Plugin:** `invoice-issuance`  
> **API:** `/apps/api-delpi/invoice-issuance`  
> **README:** [plugins/invoice-issuance/README.md](../../../plugins/invoice-issuance/README.md)

## North star

Solicitante preenche um wizard alinhado ao guia de faturamento; Faturamento atende a fila; o sino do portal avisa os dois lados. **Não** lança NF no Protheus nesta versão.

## Papéis

| Papel | Permissão | Ação |
|-------|-----------|------|
| Solicitante | `create` + `view.filial-*` | Wizard, acompanhar próprias, corrigir `returned` |
| Faturamento | `process` | Iniciar, devolver, marcar emitida |
| Admin | `manage` | Cancelar não terminais |

## Fluxo

`pending` → `in_progress` → `issued` | `returned` | `cancelled`.  
`returned` → PATCH + `resubmit` → `pending`.

## Deploy

```bash
docker exec delpi-api-delpi python scripts/run_plugins_migrations.py status --plugin invoice-issuance
docker exec delpi-api-delpi python scripts/run_plugins_migrations.py up --plugin invoice-issuance
./infra/scripts/up-dev-sequential.sh --fase mfe --build invoice-issuance
```

Produção: mesmo `up` (nunca `reset`). Rebuild MFE:

```bash
./infra/scripts/up-prod-sequential.sh --fase remote --build plugin-ui
./infra/scripts/up-prod-sequential.sh --fase mfe --build invoice-issuance
```

Registrar manifesto: `POST /core-api/admin/apps/register` com `plugins/invoice-issuance/invoice-issuance.manifest.json`. RBAC no Portal depois.

## Smoke

```bash
curl -sI http://localhost/apps/invoice-issuance/assets/remoteEntry.js | head -3
```
