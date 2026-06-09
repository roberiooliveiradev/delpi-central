# Fase 0 — Validação TOTVS (Pedidos de Venda em Aberto)

> **View:** `dbo.VW_PEDIDOS_VENDA_ABERTOS_COMPRADORES`  
> **Status:** ✅ **Pronto para Fase 1**  
> **Gerado em:** `2026-06-09` (validação via `delpi-api-delpi`)

---

## Resultado geral

| Indicador | Valor |
|-----------|-------|
| View acessível | ✅ Sim |
| Colunas compatíveis com [ESPECIFICACAO-VIEW.md](./ESPECIFICACAO-VIEW.md) | ✅ Sim (17/17) |
| Amostra com dados | ✅ Sim |
| **Pronto para Fase 1** | ✅ `ready_for_phase_1: true` |

Checks automáticos: **9/9** | Checklist Fase 0: **8/8**

---

## Checklist Fase 0

| # | Check | OK? | Observação |
|---|-------|-----|------------|
| 1 | `SELECT TOP 10` retorna linhas | ✅ | 10 linhas retornadas |
| 2 | Coluna `nome_cliente` presente | ✅ | 17 colunas confirmadas via `INFORMATION_SCHEMA` |
| 3 | Coluna `tipo_entidade` presente | ✅ | |
| 4 | Coluna `data_despacho` aceita NULL | ✅ | 110/157 (70,06%) sem despacho; ver nota abaixo |
| 5 | Coluna `data_entrega` ordenável | ✅ | `ORDER BY data_entrega DESC` validado |
| 6 | Campos numéricos (`saldo`, `valor_aberto`) numéricos | ✅ | Summary agregou sem erro |
| 7 | Literais `tipo_entidade` documentados | ✅ | CLIENTE (151), FORNECEDOR (6) |
| 8 | Filiais distintas listadas | ✅ | 01 (126), 02 (31) |
| 9 | Volume total (`COUNT(*)`) estimado | ✅ | **157 linhas** |
| 10 | Query summary retorna agregados coerentes | ✅ | Ver tabela summary abaixo |

**Checks:** 10/10

---

## Nota técnica — `data_despacho` nula

Na amostra, registros sem despacho chegam ao Python como **string vazia `""`** após `_normalize_row` do `BaseRepository` (não como `null` JSON). Na **Fase 1**, o use case deve normalizar `""` → `null` antes de serializar a resposta HTTP, para que a UI trate corretamente como "Não informado" / badge "Sem despacho".

---

## Amostra TOP 10

```sql
SELECT TOP 10
  nome_cliente, tipo_entidade, filial, pedido, linha, produto,
  saldo, data_despacho, data_entrega, no_estoque, valor_aberto
FROM dbo.VW_PEDIDOS_VENDA_ABERTOS_COMPRADORES
ORDER BY data_entrega DESC;
```

| nome_cliente | tipo_entidade | filial | pedido | linha | produto | saldo | data_despacho | data_entrega | no_estoque | valor_aberto |
|--------------|---------------|--------|--------|-------|---------|-------|---------------|--------------|------------|--------------|
| WEG AUTOMACAO | CLIENTE | 01 | 101852 | 02 | 90300079 | 6.1 | 2026-10-05 | 2026-10-06 | 4.6 | 12032.31 |
| WEG AUTOMACAO | CLIENTE | 01 | 101534 | 02 | 90300079 | 4.3 | 2026-09-04 | 2026-09-08 | 4.6 | 8481.79 |
| WANKE SA | CLIENTE | 02 | 002465 | 03 | 90264142 | 2.0 | 2026-08-21 | 2026-08-28 | 0.03 | 4174.40 |
| FRANKLIN ELECTRIC-SC | CLIENTE | 01 | 102441 | 01 | 90262806 | 0.064 | _(vazio)_ | 2026-08-25 | 0.064 | 5786.32 |
| FRANKLIN ELECTRIC-SC | CLIENTE | 01 | 102441 | 02 | 90350294 | 0.064 | _(vazio)_ | 2026-08-25 | 0.064 | 1928.77 |
| FRANKLIN ELECTRIC-SC | CLIENTE | 01 | 102441 | 03 | 90262803 | 0.064 | _(vazio)_ | 2026-08-25 | 0.064 | 4565.52 |
| FRANKLIN ELECTRIC-SC | CLIENTE | 01 | 102441 | 04 | 90350291 | 0.064 | _(vazio)_ | 2026-08-25 | 0.032 | 1521.84 |
| FRANKLIN ELECTRIC-SC | CLIENTE | 01 | 102441 | 05 | 90262802 | 0.032 | _(vazio)_ | 2026-08-25 | 0.0 | 1811.61 |
| FRANKLIN ELECTRIC-SC | CLIENTE | 01 | 102441 | 06 | 90350290 | 0.032 | _(vazio)_ | 2026-08-25 | 0.032 | 603.87 |
| WEG AUTOMACAO | CLIENTE | 01 | 101147 | 02 | 90300079 | 3.2 | 2026-08-21 | 2026-08-24 | 4.6 | 6312.03 |

---

## Literais `tipo_entidade`

| tipo_entidade | total |
|---------------|-------|
| CLIENTE | 151 |
| FORNECEDOR | 6 |

---

## Filiais

| filial | total |
|--------|-------|
| 01 | 126 |
| 02 | 31 |

---

## Volume

| total_linhas |
|--------------|
| 157 |

**Decisão de paginação:**

- ✅ Volume ≤ 5.000 → MVP com carga completa + filtros client-side (Fase 3)
- ☐ Volume > 5.000 → planejar paginação server-side na Fase 6

---

## Sanidade — `data_despacho` nula

| total | sem_despacho | pct_sem_despacho |
|-------|--------------|------------------|
| 157 | 110 | 70,06 |

---

## Summary de referência

| total_linhas | valor_total_aberto | saldo_total | itens_com_estoque | itens_estoque_parcial | itens_sem_estoque |
|--------------|-------------------|-------------|-------------------|----------------------|-------------------|
| 157 | 2.348.421,81 | 4.453,58 | 78 | 29 | 50 |

---

## Colunas da view (INFORMATION_SCHEMA)

| # | Coluna | Tipo |
|---|--------|------|
| 1 | nome_cliente | varchar |
| 2 | tipo_entidade | varchar |
| 3 | tipo_pedido | varchar |
| 4 | pedido_cliente | varchar |
| 5 | filial | varchar |
| 6 | pedido | varchar |
| 7 | linha | varchar |
| 8 | produto | varchar |
| 9 | codigo_cliente | varchar |
| 10 | quantidade | numeric |
| 11 | entregue | numeric |
| 12 | saldo | numeric |
| 13 | data_despacho | date |
| 14 | data_entrega | date |
| 15 | no_estoque | numeric |
| 16 | preco_venda | numeric |
| 17 | valor_aberto | numeric |

**Divergências de schema:** nenhuma — todos os 17 campos do contrato API estão presentes com os nomes esperados.

---

## Como regenerar

```bash
docker exec delpi-api-delpi python -c "
# ou, após criar o script permanente:
# docker exec delpi-api-delpi python scripts/validate_pedidos_venda_abertos_view.py \
#   --markdown docs/12-roadmap-e-evolucao/pedidos-venda-abertos/FASE0-VALIDACAO-VIEW.md
"
```

Validação executada em 2026-06-09 contra o banco configurado em `TOTVS_DB_*` do ambiente dev (`delpi-api-delpi`).
