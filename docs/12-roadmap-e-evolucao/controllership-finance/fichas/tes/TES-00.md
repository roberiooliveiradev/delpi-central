# TES-00 — O que é TES e como ler

Versão da ficha: 1.0 · 14/11/2026.

## Identificação

- Código: **TES-00** — visão geral da família de fichas sobre TES.
- Implementação: **IMPLEMENTED** (conhecimento citável da CLARA).
- Finalidade: explicar o que é TES, o que ela decide no Protheus e por que pesa no Fechamento mensal da Controladoria.
- Evidência: o significado dos campos é padrão TOTVS; os números são do cadastro SF4 da Delpi extraído em 09/11/2026 (PROVEN); o uso nos relatórios vem do código da api-delpi e das fichas R05–R11 (PROVEN).
- Família: TES-00 (conceito), TES-01 (uso no fechamento), TES-02 (padrões da Delpi), TES-03 (catálogo de entrada), TES-04 (catálogo de saída), TES-05 (pendências, manutenção e como a CLARA responde).

## Significado

- **TES = Tipo de Entrada e Saída.** É o cadastro do Protheus na tabela **SF4**.
- Toda linha de nota fiscal leva uma TES: entrada em `D1_TES` (SD1) e saída em `D2_TES` (SD2).
- A TES é o **manual de instruções da linha da nota**: o produto e o valor dizem o quê e quanto; a TES diz o que o Protheus faz com isso (estoque, financeiro, impostos, livro fiscal, poder de terceiros).
- Uma TES errada quase nunca trava o lançamento: a nota grava. O efeito aparece no fechamento, em estoque, custo, faturamento ou crédito de imposto.

## O que a TES decide

| Pergunta | Campo SF4 | Coluna na extração | Efeito no fechamento |
|---|---|---|---|
| Movimenta estoque? | `F4_ESTOQUE` | Atu.Estoque? | Entra ou não no kardex (R06), no R05 e no custo do item. Saída sem estoque não gera custo (`D2_CUSTO1` = 0) |
| Gera duplicata? | `F4_DUPLIC` | Gera Dupl. ? | Gera título a pagar (entrada) ou a receber (saída); na saída marca faturamento (R09 usa isso) |
| Calcula ICMS? | `F4_ICM` | Calcula ICMS | O Protheus calcula o ICMS da linha |
| Credita ICMS? | `F4_CREDICM` | Cred. ICMS ? | Na entrada, o ICMS vira crédito e sai do custo da compra |
| Livro fiscal de ICMS | `F4_LFICM` | L.Fisc. ICMS | Tributado, Isento, Outros ou Não: é o que vai ao livro e ao SPED |
| Calcula / credita IPI? | `F4_IPI`, `F4_CREDIPI` | Calcula IPI?, Credita IPI? | Mesma lógica para o IPI |
| Livro fiscal de IPI | `F4_LFIPI` | L.Fiscal IPI | Tributado, Isento, Outros ou Não |
| Poder de terceiros | `F4_PODER3` | Poder Terc. | Remessa ou Devolução: material que não é estoque próprio (ou que é nosso e está fora) |
| Material de consumo | `F4_CONSUMO` | Mat.Consumo | Marca TES de uso e consumo |
| CFOP | `F4_CF` | Cod. Fiscal | Código fiscal que vai para a nota |
| Descrição | `F4_TEXTO` | Txt Padrao | Texto do cadastro; não é único (16 TES de saída se chamam «OUTRAS SAIDAS») |
| Finalidade | `F4_FINALID` | Finalidade | Texto livre; a Comercial usa «BAIXA ESTOQUE» como critério |
| Tipo | `F4_TIPO` | Tipo do TES | E = entrada, S = saída |

- Os nomes `F4_*` acima são os usados pelo código da api-delpi (PROVEN). PIS/COFINS (`Cred.PIS/COF`), TES de devolução (`Tes Devol.`) e bloqueio (`Bloqueado`) aparecem na extração; o nome técnico desses três campos é TO_INVENTORY no dicionário (SX3) da Delpi.
- O SPED não lê a TES nem a SD1: lê o livro fiscal (SFT/SF3), gravado na classificação da nota com a TES daquele momento. Por isso `D1_VALICM` preenchido não é crédito (ficha AE-10).

## Faixas de código

- Padrão do Protheus: **001 a 500 = entrada; 501 a 999 = saída.** A Delpi segue: nenhuma TES de entrada acima de 500 e nenhuma de saída abaixo de 501. PROVEN (cadastro de 09/11/2026).
- Faixa usada na Delpi: **entrada 001 a 416**, mais o código alfanumérico **3A8** (importação direta); **saída 501 a 764**.
- Total: **458 TES** — 252 de entrada e 206 de saída. **234 ativas** (141 de entrada e 93 de saída) e **224 bloqueadas**.
- O número não diz a natureza: 001 é compra de matéria-prima, 120 é devolução de venda, 594 é venda. Para saber o que a TES faz, leia o catálogo (TES-03 e TES-04).

## TES não é CFOP

- **CFOP** é código fiscal oficial: diz ao fisco que operação foi (5101 = venda de produção própria dentro do estado).
- **TES** é código interno do Protheus: carrega um CFOP e também decide estoque, financeiro, crédito e livro.
- Duas TES podem ter o **mesmo CFOP e comportamento diferente**. Na Delpi, 29 TES de saída usam o CFOP 5101 (11 ativas): a 614 baixa estoque e tem custo; a 594 não baixa estoque e sai com custo zero. PROVEN.
- Consequência: CFOP sozinho não explica custo nem crédito. Para explicar, olhe a TES.

## TES não é tipo de movimento interno (SD3)

- Movimentos internos de estoque (requisição, devolução, produção, inventário) ficam na **SD3** e usam o **tipo de movimento** `D3_TM`, não TES. PROVEN (código do kardex e do R05: `D3_TM <= '500'` entrada, `> '500'` saída).
- A convenção é a mesma das TES: até 500 entra, acima de 500 sai.
- **499 e 999 do R07 (ajustes de inventário) são tipos de movimento da SD3**, não TES: não existem na SF4 extraída em 09/11/2026. PROVEN. A ficha R07 os chama de «TES 499/DE0» e «TES 999/RE0» por herança do relatório; leia como tipo de movimento 499 (entrada, `D3_CF` DE0) e 999 (saída, `D3_CF` RE0).
- O cadastro dos tipos de movimento no Protheus é a SF5 (padrão TOTVS). A descrição de 499 e 999 na Delpi é TO_INVENTORY.

## TES por filial

- A SF4 tem `F4_FILIAL`. O código da api-delpi procura primeiro a TES da filial da nota e, se não houver, a TES com filial em branco (compartilhada). PROVEN.
- Na extração de 09/11/2026 todas as 458 TES estão com filial em branco: o mesmo cadastro vale para as filiais 01 e 02. PROVEN.
- Filial é dimensão do dado, não regra de permissão.

## TES bloqueada

- Bloqueada = não pode ser usada em nota nova. 224 das 458 TES estão bloqueadas. PROVEN.
- 33 TES têm o campo de bloqueio vazio (entre elas 001, 003, 004, 020, 030, 040, 120 e 501): vazio = não bloqueada (padrão TOTVS: só bloqueia quando marcado).
- Nota antiga pode ter TES hoje bloqueada (ex.: a TES 036, frete sobre vendas). Isso é histórico, não erro.

## Exemplo da Delpi: industrialização para terceiros

- A mesma nota de saída costuma ter dois itens:
  - **TES 510** «INDUSTRIALIZACAO EFET. P/ OUTRA EMPRESA», CFOP 5124: movimenta estoque, tem custo. É o material aplicado.
  - **TES 594** «VENDA DE PRODUCAO DO ESTABELECIMENTO», CFOP 5101: **não movimenta estoque**, gera duplicata. É a cobrança.
- Resultado: o item 594 entra no faturamento com custo zero, e isso é o esperado. PROVEN (ficha R11, BR-R11-003/004).

## Governança

- Owner do cadastro de TES: Controladoria e equipe fiscal. A CLARA explica; não cria, edita nem bloqueia TES.
- A CLARA não lê a SF4 ao vivo: o catálogo é a extração de 09/11/2026. Ao citar uma TES, diga a data da extração.
- Configuração estranha é ponto a verificar, nunca erro confirmado.
