# Runbook — migração `invoice_issuance` → `my_requests` (E8)

One-shot operacional. **Não** apaga o schema legado. Após E13 o MFE legado sai do Compose; schema/volume/lookups seguem a § Retenção abaixo.

## Pré-requisitos

1. Migrations `requests-api` aplicadas (inclui **V006** seed `invoice-issuance`).
2. Schema plugin `invoice-issuance` (`V001`–`V004`) já existente no Postgres plugins.
3. Volumes montados no host (ver `infra/README-ambiente.md`):
   - Legado: `${DELPI_DATA_HOST_DIR}/invoice-issuance` → `/app/data/invoice-issuance`
   - Destino: `${DELPI_DATA_HOST_DIR}/my-requests-attachments` → `/app/data/my-requests-attachments`
4. Container `delpi-requests-api` com `PLUGINS_DB_*` e paths de upload configurados.
5. Homologação dual-run / checklist P0 preferencialmente concluída antes de `--apply` em produção.

## Comandos

### Dry-run (padrão — sem escrita)

```bash
docker exec delpi-requests-api \
  python scripts/migrate_invoice_issuance_to_my_requests.py
```

O JSON de saída inclui:

| Campo | Significado |
|-------|-------------|
| `legacy_requests` / `items` / `history` / `attachments` | Contagens no schema legado |
| `already_migrated` | UUIDs já presentes em `my_requests.requests` |
| `to_migrate` | Candidatos novos |
| `missing_attachment_files` | Paths listados no DB sem arquivo no volume |

Conferir: `legacy_requests ≈ already_migrated + to_migrate`.

### Apply (staging primeiro)

```bash
docker exec delpi-requests-api \
  python scripts/migrate_invoice_issuance_to_my_requests.py --apply
```

Comportamento:

- Preserva o **mesmo UUID** como `my_requests.requests.id` (reexecução é idempotente: skip se já existe).
- Gera `request_number` via `my_requests.request_number_seq` (`REQ-{ano}-{n}`).
- Grava `payload._migration = { source, legacy_id, migrated_at }`.
- Copia anexos e calcula `checksum_sha256`.
- Falha se um anexo do DB não existir no disco (use `--skip-missing-attachments` só se consciente do gap).

### Reexecução

Rodar de novo com `--apply` só migra o que ainda não está em `my_requests.requests` (mesmo `id`).

## Verificação pós-apply

```sql
-- Contagens
SELECT COUNT(*) FROM invoice_issuance.invoice_issuance_requests;
SELECT COUNT(*) FROM my_requests.requests r
  JOIN my_requests.request_types t ON t.id = r.request_type_id
 WHERE t.code = 'invoice-issuance'
   AND r.payload ? '_migration';

-- Amostra de status canônico
SELECT status, COUNT(*) FROM my_requests.requests r
  JOIN my_requests.request_types t ON t.id = r.request_type_id
 WHERE t.code = 'invoice-issuance'
 GROUP BY 1;
```

Checklist anexos: para cada `request_attachments.storage_key`, o arquivo deve existir sob `MY_REQUESTS_ATTACHMENT_UPLOAD_DIR` e o SHA-256 deve bater com `checksum_sha256`.

## Rollback

- **Não** dropar `invoice_issuance` após a migração.
- Se a migração estiver incorreta: apagar apenas as linhas migradas em `my_requests` (mesmo UUID / `payload._migration`) e os arquivos copiados no volume destino; o legado permanece fonte da verdade até cutover validado.
- Nunca usar `run_plugins_migrations.py reset` em produção.

## Mapeamento rápido

| Legado | Destino |
|--------|---------|
| `pending` | `submitted` |
| `returned` | `needs_information` |
| `issued` | `completed` (+ `completed_at` ← `issued_at`) |
| `in_progress` / `cancelled` | iguais |
| colunas party/freight/carrier/items | `payload` JSONB |
| `invoice_issuance_history` | `request_status_history` |
| anexos em disco | volume my-requests + `request_attachments` |

Detalhe: playbook §20.2 · script: `requests-api/scripts/migrate_invoice_issuance_to_my_requests.py`.

## Migração aplicada (registro)

Ver evidências e JSON em [PARITY-P0.md](./PARITY-P0.md) § **E15 verify**. Ambientes com `legacy_requests > 0`: executar dry-run → `--apply` staging → prod e anexar o JSON naquela seção.

## Retenção pós-descomission (E13)

| Recurso | Política |
|---------|----------|
| Schema `invoice_issuance` | **Retido** — sem `DROP` / sem `run_plugins_migrations.py reset` |
| Volume `${DELPI_DATA_HOST_DIR}/invoice-issuance` | **Retido ≥ 90 dias** após apply validado em prod (anexos históricos / auditoria) |
| Lookups api-delpi `/invoice-issuance/*` | **Mantidos** enquanto `requests-api` `ApiDelpiAdapter` consumir |
| MFE Compose `invoice-issuance` | **Removido** (E13) — código no monorepo só como referência |
| Permissões `invoice-issuance.*` | Coexistem até runbook IAM; mapa em PLAYBOOK §20.5 |

## Mapa RBAC (resumo)

| Legado | Canônico |
|--------|----------|
| `invoice-issuance.access` | `my-requests.access` |
| `invoice-issuance.create` | `my-requests.invoice-issuance.create` |
| `invoice-issuance.view.filial-*` | `my-requests.view.filial-*` |
| `invoice-issuance.process` | `my-requests.invoice-issuance.process` |
| `invoice-issuance.manage` | `my-requests.manage` |

Não revogar permissões legadas neste runbook sem confirmação de IAM / suporte.
