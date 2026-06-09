# Especificação — View TOTVS `VW_PEDIDOS_VENDA_ABERTOS_COMPRADORES`

> **Status:** planejamento (jun/2026)  
> **Objetivo:** contrato de dados entre SQL Server, api-delpi e plugin MFE

---

## 1. Identificação

| Campo | Valor |
|-------|--------|
| Objeto SQL | `dbo.VW_PEDIDOS_VENDA_ABERTOS_COMPRADORES` |
| Tipo | View (read-only) |
| Sistema origem | Protheus / TOTVS |
| Granularidade | Uma linha = um item de pedido em aberto |

---

## 2. Campos expostos pela API

Todos os campos abaixo devem ser selecionados **explicitamente** no repository (sem `SELECT *`).

| Campo API | Tipo JSON | Descrição | Observações |
|-----------|-----------|-----------|-------------|
| `nome_cliente` | string | Razão social ou nome do cliente/fornecedor | Exibir na tabela |
| `tipo_entidade` | string | `CLIENTE` ou `FORNECEDOR` | Filtro na UI |
| `tipo_pedido` | string | Tipo do pedido Protheus | Ex.: `N` |
| `pedido_cliente` | string | Pedido informado pelo cliente | Busca livre |
| `filial` | string | Código da filial | Filtro select |
| `pedido` | string | Número do pedido Protheus | Busca livre |
| `linha` | string | Linha do item no pedido | Chave composta |
| `produto` | string | Código/descrição do produto | Busca livre |
| `codigo_cliente` | string | Código do cliente no cadastro | Busca livre |
| `quantidade` | number | Quantidade pedida | Formato pt-BR na UI |
| `entregue` | number | Quantidade já entregue | |
| `saldo` | number | Quantidade em aberto | `quantidade - entregue` (validar na view) |
| `data_despacho` | string \| null | Data de despacho | `null` → "Não informado" na UI |
| `data_entrega` | string | Data prevista de entrega | ISO `YYYY-MM-DD`; ordenação default DESC |
| `no_estoque` | number | Quantidade disponível em estoque | Base dos badges de estoque |
| `preco_venda` | number | Preço unitário de venda | BRL na UI |
| `valor_aberto` | number | Valor financeiro em aberto | BRL na UI |

---

## 3. Agregados do summary (SQL)

Calculados no repository sobre **todas** as linhas retornadas:

| Campo summary | Regra SQL (conceitual) |
|---------------|------------------------|
| `total_linhas` | `COUNT(*)` |
| `valor_total_aberto` | `SUM(valor_aberto)` |
| `saldo_total` | `SUM(saldo)` |
| `itens_com_estoque` | `COUNT` onde `no_estoque >= saldo` |
| `itens_estoque_parcial` | `COUNT` onde `no_estoque > 0 AND no_estoque < saldo` |
| `itens_sem_estoque` | `COUNT` onde `no_estoque <= 0` |

Na UI, após filtros client-side, o summary é **recalculado** sobre as linhas filtradas.

---

## 4. Ordenação padrão

```sql
ORDER BY data_entrega DESC
```

Entregas mais recentes / mais distantes no futuro aparecem primeiro (conforme validação SQL do requisito).

---

## 5. Query de referência (repository)

```sql
-- Items
SELECT
  nome_cliente,
  tipo_entidade,
  tipo_pedido,
  pedido_cliente,
  filial,
  pedido,
  linha,
  produto,
  codigo_cliente,
  quantidade,
  entregue,
  saldo,
  CONVERT(VARCHAR(10), data_despacho, 23) AS data_despacho,
  CONVERT(VARCHAR(10), data_entrega, 23) AS data_entrega,
  no_estoque,
  preco_venda,
  valor_aberto
FROM dbo.VW_PEDIDOS_VENDA_ABERTOS_COMPRADORES
ORDER BY data_entrega DESC;

-- Summary
SELECT
  COUNT(*) AS total_linhas,
  ISNULL(SUM(valor_aberto), 0) AS valor_total_aberto,
  ISNULL(SUM(saldo), 0) AS saldo_total,
  SUM(CASE WHEN no_estoque >= saldo THEN 1 ELSE 0 END) AS itens_com_estoque,
  SUM(CASE WHEN no_estoque > 0 AND no_estoque < saldo THEN 1 ELSE 0 END) AS itens_estoque_parcial,
  SUM(CASE WHEN no_estoque <= 0 THEN 1 ELSE 0 END) AS itens_sem_estoque
FROM dbo.VW_PEDIDOS_VENDA_ABERTOS_COMPRADORES;
```

> **Nota:** Se os nomes físicos das colunas na view divergirem, ajustar aliases no SELECT — documentar divergências em [FASE0-VALIDACAO-VIEW.md](./FASE0-VALIDACAO-VIEW.md).

---

## 6. Regras de negócio (UI)

### Status de entrega

| Condição | Label |
|----------|-------|
| `entregue = 0` | Em aberto |
| `entregue > 0` AND `saldo > 0` | Entregue parcial |

### Status de estoque

| Condição | Label |
|----------|-------|
| `no_estoque >= saldo` | Com estoque |
| `no_estoque > 0` AND `no_estoque < saldo` | Estoque parcial |
| `no_estoque <= 0` | Sem estoque |

### Despacho

| Condição | Exibição |
|----------|----------|
| `data_despacho === null` ou string vazia `""` | Texto "Não informado" + badge "Sem despacho" |
| `data_despacho` preenchida | Data formatada `dd/MM/yyyy` |

> **Validado na Fase 0:** ~70% das linhas sem despacho; o `BaseRepository` converte NULL SQL em `""` — a API deve normalizar para `null` JSON na Fase 1.

---

## 7. Validações da Fase 0

Antes de implementar o repository, confirmar:

1. View existe no banco configurado em `TOTVS_DB_DATABASE`
2. Todas as 17 colunas existem (ou têm alias mapeável)
3. Tipos numéricos coerentes (`saldo`, `valor_aberto`, `no_estoque`)
4. `%` de `data_despacho` nula documentado
5. Valores distintos de `tipo_entidade` e `filial`
6. Volume total (`COUNT(*)`) estimado

Resultado: [FASE0-VALIDACAO-VIEW.md](./FASE0-VALIDACAO-VIEW.md).
