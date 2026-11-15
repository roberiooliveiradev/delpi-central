# TES-01 — TES no Fechamento mensal da Controladoria

Versão da ficha: 1.0 · 14/11/2026.

## Identificação

- Código: **TES-01** — onde e como cada relatório do fechamento usa a TES.
- Implementação: **IMPLEMENTED** (consolida regras já implementadas; não cria regra nova).
- Fontes: código da api-delpi (`stock_kardex_sql.py`, `stock_movements_sql.py`, `cpv_query_repository.py`, `billing_mod_breakdown_sql.py`, `billing_exclusion_roster_sql.py`, `entry_audit_sql.py`) e fichas R05, R06, R07, R09, R10, R11 e AE-*. A regra de cada relatório continua sendo da ficha dele; esta ficha é o índice transversal.
- Evidência: PROVEN quando a regra está no código e na ficha do relatório; pendências marcadas como TO_INVENTORY.

## Dois jeitos de usar a TES

- **Por atributo**: o relatório não fixa código; pergunta à TES o que ela faz (movimenta estoque? gera duplicata? controla poder de terceiros?). TES nova com o mesmo atributo entra sozinha.
- **Por código**: o relatório usa uma lista fixa de TES. TES nova com o mesmo papel **não** entra até alguém atualizar a lista.

## Regras por atributo

| Relatório | Regra pela TES | Evidência |
|---|---|---|
| R05 — Entradas e saídas (MATR320) | SD1 e SD2 só entram com `F4_ESTOQUE='S'`. Na entrada: `F4_PODER3='N'` e nota não-devolução = compras; nota tipo D = devolução de venda; `F4_PODER3<>'N'` = entrada de terceiros. Na saída: o espelho (vendas, devolução de compra, saída de terceiros). SD3 por tipo de movimento (`D3_TM`). | PROVEN (código + BR-R05-003/004) |
| R06 — Kardex (MATR910) | SD1 e SD2 só entram com `F4_ESTOQUE='S'`; SD3 entra por tipo de movimento. TES sem estoque não aparece no kardex. | PROVEN (código + BR-R06-002) |
| CPV gerencial | Não filtra por TES: usa os CFOPs de venda 5101, 5124, 6101 e 6124 e o custo do item (`D2_CUSTO1`). Item com TES sem estoque entra com custo zero. | PROVEN (código; custo zero PROVEN para a 594 em BR-R11-005) |
| R07 — Ajustes de inventário | SD3 com `D3_DOC='INVENT'`, tipos de movimento 499 (entrada, DE0) e 999 (saída, RE0). Não são TES (ficha TES-00). | PROVEN (BR-R07) |
| R08 — Material em processo (H02) | SD3 com OP e saldo do armazém de processo. A ficha não registra regra por TES. | — |
| R09 — Faturamento × MOD | Produto acabado faturado = SD2 com TES `F4_DUPLIC='S'` na competência. | PROVEN (código + BR-R09-003) |
| Auditoria de entradas | Lê na SF4 se a TES calcula e credita ICMS e IPI, o livro fiscal, se é de consumo, o tipo e o CFOP. O crédito é decidido pelo livro fiscal (SFT); a TES confirma. TES ausente da SF4 = «Depende da TES». | PROVEN (código + AE-10) |

- As fichas R01–R04, R08 e R12–R15 não registram regra por TES.

## TES citadas por código

| TES | Descrição (SF4) | Onde | Efeito | Evidência |
|---|---|---|---|---|
| 001 | COMPRAS MP | R10 | Fora da apuração de despesas | PROVEN |
| 003 | COMPRAS MP S/IPI | R10 | Fora da apuração de despesas | PROVEN |
| 016 | COMPRAS CONTA ORDEM | R10 | Fora da apuração de despesas | PROVEN |
| 020 | AQUIS. ENER. ELETR. | R10 | Fora da apuração de despesas | PROVEN |
| 030 | SERV. COMUNICAÇÃO | R10 | Fora da apuração de despesas | PROVEN |
| 040 | AQUIS. SERV.TRANSP. | R10 | Fora da apuração de despesas | PROVEN |
| 080 | ENTRADA IND.P/ENCOM. | R10 | Fora da apuração de despesas | PROVEN |
| 083 | ENTRADA DE VASILHAME | R10 | Fora da apuração de despesas | PROVEN |
| 085 | ENTRADA IND.P/ENCOM. | R10 | Fora da apuração de despesas | PROVEN |
| 120 | DEVOLUCAO DE VENDAS | R10 | Fora da apuração de despesas | PROVEN |
| 159 | REMESSA PARA INDUSTR | R10 | Fora da apuração de despesas | PROVEN |
| 204 | TRANSF. MAT. PRIMA | R10 | Fora da apuração de despesas | PROVEN |
| 318 | IMPORT.OUTRAS ENTRAD | R10 | Fora da apuração de despesas | PROVEN |
| 046 | SERVICOS ADM/CONSUMO | R10 | Coparticipação de plano de saúde (parcela do colaborador, sem centro de custo) fica fora | PROVEN |
| 594 | VENDA DE PRODUCAO DO ESTABELECIMENTO | R11, CPV | Com o grupo 9035, seleciona as notas a desconsiderar; não movimenta estoque, custo zero esperado | PROVEN; critério oficial TO_INVENTORY (E11b) |
| 510 | INDUSTRIALIZACAO EFET. P/ OUTRA EMPRESA | R11 | Item-irmão da 594: movimenta estoque e carrega o custo; nota com 594 sem 510 vira possível divergência | PROVEN |
| 004 | COMPRAS MP SIMPLES | Auditoria | TES do crédito presumido de 7% de SC (configuração `ENTRY_AUDIT_PRESUMED_CREDIT_TES`) | PROVEN |
| 036 | FRETE S/ VENDAS | Auditoria | Credita ICMS com livro Outros; sem SFT o CT-e fica «Depende da TES». **Bloqueada** no cadastro de 09/11/2026 | PROVEN |

- **R10 — as 13 TES excluídas.** O procedimento narrado fala em «12 tipos»; o conjunto que reproduz o relatório ao centavo tem 13 (016 e 159 a mais, ambas sem duplicata). A lista oficial é TO_INVENTORY (LISTA-13). Como é lista fixa, TES nova de compra de MP, energia, comunicação, transporte etc. **entra** na apuração até a lista ser atualizada.

## TES de poder de terceiros (ativas)

- Pesam no R05 (entradas e saídas de terceiros) e no saldo em poder de terceiros. Cadastro de 09/11/2026: 33 TES de Remessa e 40 de Devolução no total; ativas: 13 de Remessa e 21 de Devolução. PROVEN.
- Entrada, com estoque: 073, 085, 097, 100, 124, 207, 301, 412.
- Entrada, sem estoque: 079, 080, 081, 083, 094, 099, 115, 178, 186, 198.
- Saída, com estoque: 519, 522, 524, 536, 541.
- Saída, sem estoque: 525, 534, 535, 540, 550, 558, 568, 577, 613, 624, 658.
- Quais delas entram no saldo de terceiros do P7 é TO_INVENTORY (ficha TES-05).

## Vendas nos CFOPs do CPV sem baixa de estoque (ativas)

- CFOP 5101 sem estoque: 505, 594, 619 (sucatas), 716. Com estoque: 501, 609, 614, 663, 706, 707, 708.
- CFOP 5124 sem estoque: 511, 671, 756. Com estoque: 510, 622, 661, 673, 757.
- Item nas TES sem estoque entra no CPV com custo zero. Para a 594 isso é PROVEN (R11); para as demais é a mesma configuração, e confirmar nos dados é TO_INVENTORY.

## Perguntas que esta ficha responde

- «A TES 120 afeta o quê?» → fica fora da apuração de despesas do R10; como movimenta estoque, aparece no kardex e no R05 como devolução de venda.
- «Por que o item da 594 tem custo zero?» → a 594 não movimenta estoque (`F4_ESTOQUE='N'`); custo zero é estrutural.
- «Por que essa nota não aparece no kardex?» → a TES não movimenta estoque.
- «Quais TES ficam fora do R10?» → as 13 da tabela, mais a 046 na parcela de benefícios; lista oficial pendente.

## Governança

- Esta ficha não cria regra: se um relatório mudar a regra, a ficha do relatório manda e esta é atualizada junto.
- Ao explicar, cite a TES (código e descrição), o relatório e a ficha de origem.
