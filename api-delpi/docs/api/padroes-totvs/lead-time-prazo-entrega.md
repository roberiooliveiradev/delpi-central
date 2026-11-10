# Prazo de Entrega (Lead Time) por filial — Protheus DELPI

Parte da [biblioteca de padrões TOTVS](./README.md). Relacionado a [cadastro de produto](./cadastro-produto.md), [filiais](./filiais.md) e [princípios SQL](./principios-sql.md).

> **Regra canônica DELPI (validada no TOTVS em 10/11/2026):** para consultar o **Prazo de Entrega (Lead Time)** cadastrado de um produto **por filial**, consultar `SBZ010.BZ_PE`, filtrar `BZ_FILIAL` e interpretar a unidade em `BZ_TIPE`. **Não substituir automaticamente por `SB1010.B1_PE` nem por `SA5010.A5_PE`.**

## O que significa `BZ_PE`?

`BZ_PE` é o campo numérico **Prazo de Entrega** da tabela `SBZ010` (**Indicadores de Produtos**, cadastro por filial). No uso de planejamento de materiais da DELPI, é o **Lead Time cadastrado por filial**. O valor precisa ser interpretado em conjunto com `BZ_TIPE` (tipo/unidade de prazo); quando `BZ_TIPE = 'D'`, o valor é expresso em **dias**.

`BZ_PE` é **parâmetro cadastral**, não uma medição automática de dias efetivamente decorridos entre pedido e entrega. Portanto não equivale, por si só, a lead time real histórico de compras.

### Tabelas e campos: não confundir

| Fonte | Campo | Significado e uso |
|-------|-------|-------------------|
| `SBZ010` | **`BZ_PE`** | **Prazo de Entrega (Lead Time) por filial — referência para consultas DELPI por filial** |
| `SBZ010` | `BZ_TIPE` | Tipo/unidade do prazo; `D` = dias |
| `SBZ010` | `BZ_FILIAL` / `BZ_COD` | Filial e código do produto (chave do cadastro específico) |
| `SBZ010` | `BZ_FORPRZ` | Fórmula de cálculo do prazo; **não é o número de dias** |
| `SB1010` | `B1_PE` / `B1_TIPE` | Prazo de Entrega (Lead Time) e unidade no **cadastro geral** do produto; **frequentemente zerado/não preenchido na DELPI**, não deve sobrepor o `BZ_PE` por filial |
| `SB1010` | `B1_FORPRZ` | Fórmula de cálculo do prazo; **não é lead time numérico** |
| `SA5010` | `A5_PE` / `A5_TIPE` | Prazo de Entrega (Lead Time) por **amarração produto–fornecedor**; semântica e granularidade diferentes do cadastro por filial |
| `SB1010` | `B1_COD`, `B1_DESC`, `B1_UM`, `B1_TIPO`, `B1_TPMAT` | Código, descrição, unidade, tipo de produto e indicador de produto de terceiro |

**Atenção:** `BZ_YLEADOP` (Lead OP) é outro indicador, não o mesmo campo que `BZ_PE`. `SB5010.B5_LEADTR` é Lead Time de **transferência**, também não substitui `BZ_PE`.

## Evidência operacional verificada

Produto `10100049` — fio rígido PVC 105°C 16AWG:

| Cadastro | Filial | Prazo | Unidade |
|----------|--------|-------|---------|
| `SBZ010.BZ_PE` | `01` | **7** | `D` (7 dias) |
| `SBZ010.BZ_PE` | `02` | **69** | `D` (69 dias) |
| `SB1010.B1_PE` | Cadastro geral | **0** | `D` |
| `SA5010.A5_PE` | Amarração com fornecedor `000688/01` | **0** | em branco |

A consulta apenas ao cadastro geral teria concluído incorretamente que o produto não possui lead time, apesar de o prazo estar parametrizado **por filial**.

Na verificação pontual da `SB1010` em 10/11/2026, dentre 55.396 registros ativos, 55.271 possuíam `B1_PE = 0`. Esse número é uma **fotografia histórica do ambiente**, não regra fixa nem garantia para períodos posteriores.

## SQL — Prazo de Entrega (Lead Time) para uma filial

```sql
SELECT
    Z.BZ_FILIAL AS FILIAL,
    Z.BZ_COD AS CODIGO_PRODUTO,
    B.B1_DESC AS DESCRICAO,
    B.B1_UM AS UNIDADE_ESTOQUE,
    Z.BZ_PE AS LEAD_TIME,
    Z.BZ_TIPE AS TIPO_PRAZO
FROM SBZ010 Z
INNER JOIN SB1010 B
    ON B.B1_COD = Z.BZ_COD
   AND B.D_E_L_E_T_ = ' '
WHERE Z.D_E_L_E_T_ = ' '
  AND Z.BZ_FILIAL = '01'
  AND Z.BZ_COD = '10100049';
```

**Atenção aos cadastros compartilhados:** a `SB1010.B1_FILIAL` pode estar em branco, como no exemplo validado; não exigir `B1_FILIAL = '01'` sem antes conferir a regra de compartilhamento. Filial **não** é armazém.

## SQL — MPs próprias com Lead Time menor que 20 dias, filial 01

```sql
SELECT
    Z.BZ_COD AS CODIGO_PRODUTO,
    B.B1_DESC AS DESCRICAO,
    B.B1_UM AS UNIDADE,
    Z.BZ_PE AS LEAD_TIME_DIAS
FROM SBZ010 Z
INNER JOIN SB1010 B
    ON B.B1_COD = Z.BZ_COD
   AND B.D_E_L_E_T_ = ' '
WHERE Z.D_E_L_E_T_ = ' '
  AND Z.BZ_FILIAL = '01'
  AND Z.BZ_TIPE = 'D'
  AND Z.BZ_PE >= 0
  AND Z.BZ_PE < 20
  AND B.B1_TIPO = 'MP'
  AND LTRIM(RTRIM(B.B1_TPMAT)) <> '2'
ORDER BY Z.BZ_PE DESC, Z.BZ_COD;
```

**Convenção de limites:** `BZ_PE < 20` significa 0–19; para **0 a 20 inclusive**, usar `BZ_PE <= 20`. Para somente valores positivos, somar `BZ_PE > 0`; prazo zero pode significar parâmetro ausente e **não deve ser interpretado automaticamente como entrega imediata**.

**Material de terceiros:** `B1_TPMAT = '1'` significa Não; `'2'` significa Sim. Em análises de MPs próprias, excluir `'2'`; ver [cadastro-produto.md](./cadastro-produto.md).

## O que fazer

1. Consultar `SBZ010` com `BZ_FILIAL`, `BZ_COD`, `BZ_PE` e `BZ_TIPE` para **Prazo de Entrega (Lead Time) por filial**.
2. Usar `SB1010` para enriquecer descrição, unidade e classificação; respeitar `D_E_L_E_T_ = ' '` nas duas tabelas.
3. Filtrar `BZ_TIPE = 'D'` ao fazer análises explicitamente **em dias**, sem comparar indiscriminadamente outras unidades.
4. Declarar se o intervalo é estrito (`< 20`) ou inclusivo (`<= 20`) e se valores zero entram ou não.
5. Ao combinar com consumo, separar **lead time cadastrado** (`SBZ`) de **consumo real**, cuja regra de movimentos/devoluções da `SD3010` deve ser homologada separadamente.

## O que NÃO fazer

- **Não** interpretar `B1_FORPRZ` ou `BZ_FORPRZ` como quantidade de dias: são campos de **fórmula**.
- **Não** consultar apenas `B1_PE` e concluir que não há prazo se o cadastro geral estiver zerado.
- **Não** tratar `A5_PE` (produto–fornecedor) como equivalente a `BZ_PE` (produto–filial).
- **Não** misturar filiais, unidades de prazo ou unidades de estoque em agregações.
- **Não** considerar `BZ_PE = 0` entrega imediata sem confirmar o significado operacional.

## Palavras-chave / busca para agentes

**lead time**, **prazo de entrega**, **prazo de fornecimento**, **tempo de reposição**, **BZ_PE**, **BZ_TIPE**, **SBZ010**, **indicadores por filial**, **B1_PE**, **A5_PE**, **Protheus**.

> Esta seção registra o **lead time cadastrado**, não homologa a fórmula do consumo real da produção nem estabelece prioridade universal entre parametrizações para todas as rotinas do Protheus.
