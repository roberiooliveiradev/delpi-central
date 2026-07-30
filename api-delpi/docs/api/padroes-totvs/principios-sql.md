# Princípios SQL Protheus (Delpi)

Parte da [biblioteca de padrões TOTVS](./README.md).

Complementa (performance/cache): `.cursor/rules/sql-query-development.mdc`.

---

## Empresa / tabelas

| Convenção | Significado |
|-----------|-------------|
| Sufixo `010` | Empresa padrão Delpi nesta entrega (`SB1010`, `SB2010`, `SBC010`, …) |
| Schema | SQL Server TOTVS — acesso via repositórios em `app/infrastructure/persistence/totvs/` |

---

## Filtros obrigatórios recorrentes

| Regra | Expressão típica |
|-------|------------------|
| Registro ativo | `D_E_L_E_T_ = ''` em **todas** as tabelas do join |
| Leitura analítica | `WITH (NOLOCK)` em dashboards/KPI/série — **não** em escrita/conciliação |
| Parâmetros | Bind `?` — não concatenar valores de usuário no SQL |

---

## O que fazer

1. Filtrar cedo: exclusão lógica, filial, datas, tipo de movimento.
2. Datas Protheus: strings `YYYYMMDD` / `YYYYMM`; janelas **closed-open** (`>= start` e `< end_exclusive`) quando o módulo já usa esse padrão.
3. Extrair SQL compartilhado em `*_sql.py` — use case não embute SQL.
4. Ao juntar `SB2` (estoque/custo): filtrar ou agregar por `B2_LOCAL` — ver [armazem-custo.md](./armazem-custo.md).

### O que NÃO fazer

| Anti-padrão | Por quê |
|-------------|---------|
| Omitir `D_E_L_E_T_ = ''` | Inclui registros excluídos logicamente |
| `JOIN SB2010` sem filtro/agregação de local | Multiplica linhas e infla totais |
| Funções em massa em coluna indexada no `WHERE` (`RTRIM` desnecessário em todo o scan) | Preferir padrão do módulo; medir peso |
| SQL N+1 por bucket/filial sem cache | Ver `sql-query-development.mdc` |

---

## Checklist

- [ ] `D_E_L_E_T_` em todas as tabelas do FROM/JOIN
- [ ] Bind parameters
- [ ] Valoração / SB2 → seção armazém-custo
- [ ] Teste `test_*_sql.py` ou assert de parâmetros/SQL no repositório
