# Materiais de terceiros / beneficiamento (`SB6`)

Parte da [biblioteca de padrões TOTVS](./README.md).

Controle de remessas recebidas de **clientes** para beneficiamento e dos
retornos associados. Fonte operacional: tabela `SB6010` (`SB6`) + view
somente leitura `dbo.VW_PD3_BENEF_RETORNOS`.

Constantes: `app/domain/totvs/protheus_third_party_materials.py`.

Não confundir com [`B1_TPMAT`](./cadastro-produto.md) (cadastro de produto de
terceiro no SB1). Este padrão trata **poder de terceiros** na `SB6`.

---

## Vocabulário

| Campo / código | Significado |
|----------------|-------------|
| `B6_PODER3 = R` | Remessa / origem (NF recebida) |
| `B6_PODER3 = D` | Devolução / retorno (NF de saída) |
| `B6_TIPO = D` | Material de terceiro em poder da empresa |
| `B6_IDENT` | Identidade compartilhada pela remessa e seus retornos |
| `B6_SALDO` | Saldo **atual** ainda pendente na remessa |
| `B6_TPCF` | Classificação C/F do parceiro no movimento — **não** é chave |
| `B6_IDENTB6` | Não usar como chave neste ambiente (pode estar vazio) |

Chave validada:

```text
B6_FILIAL + B6_PRODUTO + B6_IDENT
```

Parceiro da **remessa**: enriquecer com `SA1` (cliente). `SA2` não se aplica.
No retorno, a view live expõe só `TIPO_PARCEIRO_RETORNO` (`B6_TPCF` do
movimento) — **não** há `COD_PARCEIRO_RETORNO` / `LOJA_PARCEIRO_RETORNO`.
A API não deve selecionar colunas que a view homolog não tem.

Ref. Cliente do produto: `SB1.B1_REFEREN` (API `customer_reference`). A view
live não expõe o campo — consultar via `LEFT JOIN SB1010` (mesmo padrão de
produtos / pedidos de venda em aberto). Não confundir com o código SA1 do
parceiro.

---

## O que fazer

1. Filtrar remessa: `D_E_L_E_T_ = ' '` + `B6_PODER3 = R` + `B6_TIPO = D`.
2. Filtrar retorno: `D_E_L_E_T_ = ' '` + `B6_PODER3 = D` + `B6_TIPO = D`.
3. Usar `B6_SALDO` da remessa como posição atual; `qtd devolvida = B6_QUANT − B6_SALDO`.
4. Converter quantidades para `decimal(28,8)` antes de somar.
5. Agregar indicadores por `RECNO_REMESSA` — a view detalha 1 linha por retorno e **repete** saldo/qtd recebida.
6. Ocultar produtos de teste (`99999999`) por **configuração da aplicação**, nunca na view.
7. Expor e filtrar Ref. Cliente via `SB1.B1_REFEREN` (prefixo `LIKE`, collate CI_AI).

## O que NÃO fazer

| Anti-padrão | Por quê |
|-------------|---------|
| Incluir `B6_TPCF` na chave | Retornos históricos válidos vieram como `F` em remessas de cliente |
| Usar `B6_IDENTB6` como chave principal | Ficou vazio nos retornos validados |
| Somar `QTD_RECEBIDA` / `SALDO_A_ENTREGAR` nas linhas detalhadas | Infla totais (saldo se repete por retorno) |
| Gravar / “corrigir” `SB6` pela API | Somente leitura |
| Filtrar `B1_TPMAT` neste fluxo | Domínio diferente (cadastro vs poder de terceiros) |
| Reconstruir saldo em data passada | `B6_SALDO` é só a posição atual |

---

## Referências

- Rota / plugin: [materiais-terceiros.md](../materiais-terceiros.md)
- Relatórios TOTVS descontinuados: MATR480 / MATR485 (TDN)
- Cadastro SB1 `B1_TPMAT`: [cadastro-produto.md](./cadastro-produto.md)
