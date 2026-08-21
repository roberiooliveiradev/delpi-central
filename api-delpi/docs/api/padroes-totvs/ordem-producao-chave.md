# Chave da ordem de produção (SC2) e alocação de operação (SH8)

Convenção Delpi para identificar OPs no Protheus e para ler a fila de operações já alocadas a centros de trabalho.

Constantes canônicas: [`app/domain/totvs/protheus_production_orders.py`](../../../app/domain/totvs/protheus_production_orders.py).

## Composição da chave

| Campo | Tamanho | Papel |
|-------|---------|-------|
| `C2_NUM` | 6 | Número da ordem |
| `C2_ITEM` | 2 | Item da ordem |
| `C2_SEQUEN` | 3 | Sequência — `001` é a **OP mãe** (o PA); `002+` são as filhas |
| `C2_OP` | 11 | Chave completa = número + item + sequência |

`SH8010.H8_OP` **já grava a chave completa de 11 posições**, igual a `C2_OP`. Juntar SH8 com SC2 por `C2_OP = H8_OP` — não concatenar `C2_NUM + C2_ITEM + C2_SEQUEN` de novo.

## OP mãe (o PA)

A OP mãe é sempre a sequência `001` do mesmo par número + item:

```sql
LEFT(H8_OP, 8) + '001'   -- mother_order_key_sql("H8_OP")
```

Use isso sempre que precisar de um dado **consolidado do PA** a partir de uma OP filha. O caso concreto que motivou o padrão: `DT_ENTREGA` da OP filha diverge da mãe na maioria dos registros, então a entrega mostrada ao PCP tem que vir da mãe.

Filtro equivalente quando a consulta já está em SC2: `RTRIM(LTRIM(C2_SEQUEN)) = '001'` (`SC2_MOTHER_OP_SEQUENCE_SQL`, usado no OTD).

## Conjunto de OPs (mãe + filhas)

O Protheus cria as OPs de um produto **em pacote**: a mãe e uma filha por intermediário da estrutura. Esse pacote é o **conjunto**, e sua chave é `C2_FILIAL + C2_NUM + C2_ITEM` — **não** `C2_NUM` sozinho.

Sonda na filial 01 (ago/2026), conjuntos com saldo em aberto:

| Fato medido | Número | Consequência |
|---|---|---|
| Conjuntos (número + item) com exatamente uma linha `001` | 2 365 | A mãe identifica o conjunto |
| Conjuntos abertos **sem** linha `001` viva | 11 | Sem produto raiz não há estrutura esperada — ficam fora de qualquer conferência |
| `C2_NUM` distintos com mais de um `C2_ITEM` | 33 (até **96** itens no mesmo número) | Agrupar só por `C2_NUM` mistura pacotes e inventa falta/sobra |
| Produto da mãe com `B1_TIPO = 'PA'` / `'PI'` | 2 320 / 556 | O raiz **nem sempre** é produto acabado |
| OPs filhas apontando para `MP` | 0 | Só `PI` e `PA` ganham OP própria |

### Estrutura esperada de um conjunto

Para saber quais filhas o conjunto **deveria** ter, explodir a estrutura do produto raiz e ficar com os componentes `B1_TIPO IN ('PI','PA')`, excluindo o próprio raiz.

A vigência da estrutura tem de ser lida na **emissão da OP mãe** (`C2_EMISSAO`), nunca em `GETDATE()`: o conjunto nasce com a estrutura da época e continua correto depois de uma troca de engenharia. Medindo a filial 01, a data de hoje acusava 147 conjuntos com falta **e** sobra ao mesmo tempo — assinatura clássica de troca de versão; pela emissão sobram 3.

### O que NÃO fazer

- Tratar `C2_NUM` como conjunto.
- Assumir que o produto da `001` é `PA`.
- Esperar OP para matéria-prima.
- Ler a vigência da estrutura em `GETDATE()` ao conferir um conjunto já emitido.
- Recortar coluna indexada no join (`RTRIM(G1_COD) = RTRIM(...)`): a conferência da filial passa de ~1 s para timeout.

## Alocação de operação (SH8010)

| Coluna | Significado |
|--------|-------------|
| `H8_CTRAB` | Centro de trabalho (nome em `SHB010.HB_NOME`) |
| `H8_OPER` | Código da operação (descrição em `SG2010.G2_DESCRI`) |
| `H8_FERRAM` | **Ferramenta** da alocação; `MOD` = mão de obra (operação manual) |
| `H8_DTINI` / `H8_HRINI` | Início programado — chave natural de sequenciamento |
| `H8_OP` | Chave da OP (11 posições) |
| `H8_QUANT` | ⚠ **Não é a quantidade da ordem** — vem sempre `1` |

Descrição da operação: junção completa `G2_FILIAL`, `G2_PRODUTO = C2_PRODUTO`, `G2_CODIGO = C2_ROTEIRO`, `G2_OPERAC = H8_OPER`. Omitir o roteiro (`G2_CODIGO`) duplica linhas quando o produto tem mais de um roteiro.

## O que fazer

- Quantidade da operação → `SC2010.C2_QUANT`; saldo → `C2_QUANT - C2_QUJE`.
- Ferramenta → `H8_FERRAM` direto da alocação (não deduzir do roteiro).
- OP em aberto → `C2_QUANT > C2_QUJE`.
- Dado consolidado do PA a partir de OP filha → `mother_order_key_sql(...)`.

## O que NÃO fazer

- Usar `H8_QUANT` como quantidade planejada.
- Reconstruir `C2_OP` concatenando os três campos quando já existe `H8_OP` / `C2_OP`.
- Espalhar o literal `'001'` — importar `MOTHER_ORDER_SEQUENCE`.
- Assumir que a entrega da OP filha é a entrega do PA.

## Onde é usado

- [production-machine-load.md](../production-machine-load.md) — carga máquina (`/production/machine-load/*`).
- [production-order-sets-incomplete.md](../production-order-sets-incomplete.md) — conjuntos incompletos (`/production/production-order-sets/incomplete`).
- OTD e detalhe de OP — `production_pa_sql_filters.py`.
- Apontamentos de produção — `production_appointments_scope.MOTHER_OP_SUFFIX`.
