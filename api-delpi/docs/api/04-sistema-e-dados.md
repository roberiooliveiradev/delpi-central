# 04 — Sistema (metadados Protheus) e Dados (SQL)

## Sistema — prefixo `/system`

Explora dicionário de dados do Protheus (tabelas SX2, colunas SX3, índices SIX, relacionamentos SX9).

**Permissão:** `api-delpi.access.full` **ou** `api-delpi.system` (`@require_any_permission`).

### GET /system/tables/search

Busca tabelas por descrição (SX2).

| Query | Obrigatório | Descrição |
|---|---|---|
| `description` | sim (mín. 2 chars) | Texto da descrição. |
| `page` | não | Default `1`. |
| `limit` | não | Default `20`, máx. `200`. |

---

### GET /system/tables/{tableName}

Metadados de uma tabela.

---

### GET /system/tables/{tableName}/columns

Colunas com paginação.

| Query | Default |
|---|---|
| `page` | `1` |
| `limit` | `50` (máx. `200`) |

---

### GET /system/tables/{tableName}/indexes

Índices (SIX010).

---

### GET /system/tables/{tableName}/relations

Relacionamentos (SX9010).

---

### GET /system/tables/{tableName}/schema

Schema agregado (SX2 + SX3 + SIX + SX9) no contrato **`composite_analysis`**:

| Seção (`data`) | Conteúdo |
|---|---|
| `summary` | `tableName`, `alias`, `description`, contagens |
| `columns` | `{ items, total, truncated }` — dicionário SX3 |
| `indexes` | `{ items, total, truncated }` — SIX |
| `relations` | `{ items, total, truncated }` — SX9 (aggregate pode truncar; `total` preserva o total real) |
| `table` | `{ items, total, truncated }` — metadados SX2 (1 item) |

`meta.sections[]` lista as seções com `key`, `label`, `itemCount`, `truncated` (mesmo padrão de factory-status / safety-stock).

---

### GET /system/tables/{tableName}/columns/search

Busca colunas dentro de uma tabela.

| Query | Obrigatório |
|---|---|
| `q` | sim (mín. 2 caracteres) |

---

### GET /system/columns/search

Busca global de colunas por descrição (SX3010 + ranking semântico).

| Query | Descrição |
|---|---|
| `description` | Texto descritivo (mín. 2 chars). |
| `page`, `limit` | Paginação. |

---

## Dados — prefixo `/data`

### POST /data/sql

Executa SQL **somente leitura** no SQL Server Protheus.

**Permissão:** `api-delpi.access.full` **ou** `api-delpi.data`

**Content-Type aceitos:**

1. `application/json`

```json
{
  "sql": "SELECT TOP 3 B1_COD, B1_DESC FROM SB1010 WHERE D_E_L_E_T_ = '';"
}
```

2. `text/plain` — corpo é a string SQL diretamente.

**Regras de segurança (`SqlValidator`):**

| Permitido | Bloqueado |
|---|---|
| `SELECT`, `WITH` (CTE), `DECLARE` controlado | `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `CREATE`, `TRUNCATE`, `MERGE` |
| Múltiplos `SELECT` (até 10) | `EXEC`, `BEGIN`/`COMMIT`/`ROLLBACK`, `GRANT`/`REVOKE` |
| Tabelas na whitelist `allowed_tables.json` | Tabelas fora da whitelist |

Variável de ambiente opcional: `ALLOWED_TABLES_PATH` apontando para JSON alternativo.

**Temporário (dev — mapeamento CRM):** `DATA_SQL_SKIP_TABLE_WHITELIST=true` ignora a allowlist e permite `SELECT` em qualquer tabela física. DDL/DML continuam bloqueados. **Não ligar em produção** (`docker-compose.yml` não define o flag; default é `false`). Desligar depois do ETL/inventário.

**Resposta sucesso:**

```json
{
  "success": true,
  "message": "SQL executed successfully.",
  "data": { }
}
```

O conteúdo de `data` depende do use case (colunas, linhas, metadados).

**Erros comuns:**

| Situação | Mensagem típica |
|---|---|
| Corpo vazio | `Empty body — SQL not provided.` |
| SQL inválido ou tabela não permitida | Mensagem do validador em `message` |
