# 20 — Fase 2B.3 — Anexos CAPEX (backend)

**Branch:** `feat/planejamento-orcamentario`  
**Data:** 2026-08-05  
**Escopo:** migration V005, entidade de anexo, storage seguro reutilizado, upload multipart, listagem, download autenticado, soft-archive, autorização contextual, auditoria, testes.  
**Fora:** frontend, submissão, aprovação, reprovação, exportações, conta contábil, restauração de anexo.  
**Commit:** nenhum (conforme brief).

---

## Status

```text
STATUS: CONCLUÍDO
```

---

## 1. Migration e tabela

Arquivo: `api-delpi/migrations/plugins/planejamento-orcamentario/V005__create_capex_investment_attachments.sql`

Tabela: `planejamento_orcamentario.capex_investment_attachments`

| Campo | Detalhe |
|-------|---------|
| `investment_id` | FK → `capex_investments` |
| `attachment_type` | enum controlado (CHECK) |
| `display_name` | obrigatório |
| `original_filename` / `mime_type` / `file_size` | metadados do arquivo |
| `storage_key` | nome físico gerado (não exposto na API) |
| `idempotency_key` | opcional — evita dupla criação em retry |
| Soft-archive | `is_active` + `archived_by` / `archived_at` |

Índices: investimento, investimento+ativo, ativo, `created_at`, unique parcial `(investment_id, idempotency_key)`.

Aplicação (somente `up`, sem reset):

```bash
docker exec delpi-api-delpi python scripts/run_plugins_migrations.py status --plugin planejamento-orcamentario
docker exec delpi-api-delpi python scripts/run_plugins_migrations.py up --plugin planejamento-orcamentario
```

V001–V005 = **APLICADA**. Nenhum reset de schema/volume.

---

## 2. Storage reutilizado

Classe canônica: `BudgetDocumentStorage`  
(`app/application/services/planejamento_orcamentario/document_storage.py`)

- Volume: `PLANEJAMENTO_ORCAMENTARIO_UPLOAD_DIR` (Compose já montado)
- Nome físico: `{uuid}{ext}` sob `{base}/{exercise_id}/`
- Valida MIME, extensão e tamanho (25 MB)
- Bloqueia path traversal em `resolve_file`

Não foi criado segundo mecanismo de arquivos.

---

## 3. Tipos e validações

Tipos (`attachment_type`):

```text
quotation | commercial_proposal | technical_specification | image | justification | other
```

Validações: investimento existente e **draft**; autenticação + acesso; ack de orientações; responsabilidade no CC; display_name; tipo; MIME; extensão; tamanho; basename do filename (anti path traversal).

---

## 4. Endpoints

Prefixo: `/planejamento-orcamentario`

| Método | Path | operation_id |
|--------|------|----------------|
| GET | `/capex/investments/{investment_id}/attachments` | `list_…_attachments` |
| POST | `/capex/investments/{investment_id}/attachments` | `upload_…_attachment` (multipart) |
| GET | `/capex/attachments/{attachment_id}/download` | `download_…_attachment` |
| POST | `/capex/attachments/{attachment_id}/archive` | `archive_…_attachment` |

Upload Form: `file`, `attachment_type`, `display_name`, `description?`, `idempotency_key?`.

Resposta pública **sem** `storage_key`. Listagem operacional: só `is_active = true`.

---

## 5. Autorização e IDOR

1. Permissão de acesso ao app  
2. `BudgetGuidanceAcknowledgementGuard.assert_modules_unlocked`  
3. `BudgetResponsibilityGuard` no CC do investimento  

IDOR (outro CC): `budget_capex_investment_not_found` / `budget_capex_attachment_not_found` (não revela existência). Admin com ack pode listar/baixar qualquer CC. Upload em investimento arquivado: `budget_capex_investment_archived`.

---

## 6. Auditoria

`entity_type = capex_investment_attachment`

| Ação | Quando |
|------|--------|
| `attachment.uploaded` | upload OK (estado público, sem storage_key) |
| `attachment.downloaded` | download autorizado |
| `attachment.archived` | soft-archive |
| `attachment.access_denied` | tentativa sem responsabilidade no CC |
| `attachment.upload_rejected` | falha de validação (sem binário) |

---

## 7. Códigos de erro

```text
budget_capex_attachment_not_found
budget_capex_attachment_forbidden
budget_capex_attachment_type_invalid
budget_capex_attachment_mime_invalid
budget_capex_attachment_extension_invalid
budget_capex_attachment_too_large
budget_capex_attachment_archived
budget_capex_investment_archived
```

(+ códigos já existentes: investment not found, acknowledgement required, …)

---

## 8. Testes

Arquivo: `tests/unit/planejamento_orcamentario/test_capex_attachment_use_cases.py`

Cobertura: upload válido, investimento inexistente, outro CC, arquivado, extensão/MIME/tamanho, path traversal, listagem, download, IDOR por anexo, arquivamento, download arquivado, sem `storage_key`, auditoria, sem ack, sem responsabilidade, sem permissão, admin, idempotência.

Suite `tests/unit/planejamento_orcamentario/`: **81 passed**.

---

## 9. Arquivos principais

- `migrations/plugins/planejamento-orcamentario/V005__create_capex_investment_attachments.sql`
- `domain/.../capex_attachment_constants.py`, `exceptions.py`
- `application/.../capex_attachment_use_cases.py`
- `application/services/.../document_storage.py` (helpers `check_*`)
- `postgres_budget_planning_repository.py` (CRUD metadados)
- `planejamento_orcamentario_composer.py`, `planejamento_orcamentario_router.py`
- `route_contract_registry.py`
- testes + esta doc

---

## 10. Pendências

- Frontend de anexos (fase seguinte)
- Submissão / aprovação / exportações
- Restauração de anexo
- Conta contábil

---

## 11. Relatório resumido

Backend 2B.3 entregue com V005 aplicada incrementalmente, storage da Fase 1 reutilizado, endpoints multipart/download/archive, guards de ack + CC, auditoria e testes verdes. Sem reset de banco/volumes e sem commit.
