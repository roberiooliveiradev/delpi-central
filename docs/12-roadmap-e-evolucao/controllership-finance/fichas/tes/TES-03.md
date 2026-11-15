# TES-03 — Catálogo das TES de entrada

Versão da ficha: 1.0 · 14/11/2026 · gerada de `fonte/sf4-2026-11-09.csv` por `fonte/gerar_catalogo_tes.py`.

## Identificação

- Código: **TES-03** — catálogo das TES de entrada cadastradas na SF4 da Delpi.
- Implementação: **IMPLEMENTED** (conhecimento citável; a CLARA não lê a SF4 ao vivo).
- Fonte: extração da SF4 fornecida pela Controladoria em 09/11/2026 (a mesma cópia usada pela auditoria de entradas). OWNER_REPORTED_VIA_PO.
- Faixa de códigos de entrada: **001 a 416 (e o código alfanumérico 3A8)**. Total: **252 TES**, das quais **141 ativas** e **111 bloqueadas**. PROVEN (cadastro de 09/11/2026).
- O catálogo é foto do cadastro naquela data: TES criada ou editada depois não aparece aqui. Diga a data da extração ao citar.

## Como ler a tabela

- **Estoque** (`F4_ESTOQUE`): S = movimenta estoque e custo; N = não movimenta.
- **Duplicata** (`F4_DUPLIC`): S = gera título no financeiro (a pagar na entrada, a receber na saída) e, na saída, conta como faturamento.
- **ICMS calc/créd/livro**: calcula ICMS (`F4_ICM`) / credita ICMS (`F4_CREDICM`) / livro fiscal de ICMS (`F4_LFICM`: T = Tributado, I = Isento, O = Outros, N = Não).
- **IPI calc/créd/livro**: o mesmo para IPI (`F4_IPI`, `F4_CREDIPI`, `F4_LFIPI`).
- **PIS/COFINS**: Cred = credita; Deb = debita; Calc = só calcula; — = não calcula.
- **Poder 3º** (`F4_PODER3`): R = Remessa, D = Devolução, — = não controla. Material em poder de terceiros não é estoque próprio.
- **Consumo** (`F4_CONSUMO`): S = TES de material de uso e consumo.
- **TES devol.**: TES que o Protheus sugere para devolver esta operação.
- Famílias agrupadas pela natureza do CFOP (três últimos dígitos). A família ajuda a achar a TES; o comportamento real é o das colunas.

## Compras de insumo, matéria-prima e revenda (entrada)

Compra de matéria-prima, insumo e mercadoria para revenda (CFOP x101, x102, x401, x403). Em regra atualizam estoque e geram duplicata; creditam ICMS e IPI quando o fornecedor destaca e a operação dá direito. As que atualizam estoque entram no kardex (R06) e no R05 como compras. As TES 001 e 003 ficam fora da apuração de despesas do R10.

- Ativas: 11 TES; 7 atualizam estoque, 8 geram duplicata, 7 creditam ICMS.
- Bloqueadas: 17 TES.
- Códigos ativos: 001, 002, 003, 004, 015, 016, 045, 128, 193, 199, 310.

### Compras de insumo, matéria-prima e revenda — TES de entrada ativas

| TES | Descrição | CFOP | Estoque | Duplicata | ICMS calc/créd/livro | IPI calc/créd/livro | PIS/COFINS | Poder 3º | Consumo | TES devol. |
|---|---|---|---|---|---|---|---|---|---|---|
| 001 | COMPRAS MP (COMPRA MP COM ICMS E IPI PIS COFINS) | 1101 | S | S | S/S/T | S/S/T | Cred | — | N | 530 |
| 002 | COMPRA EMPRESA OPT MEI | 1101 | S | S | N/N/O | N/N/T | Cred | — | N | 530 |
| 003 | COMPRAS MP S/IPI | 1101 | S | S | S/S/T | N/N/O | Cred | — | N | 561 |
| 004 | COMPRAS MP SIMPLES (COMPRAS MP SIMPLES NACIONAL) | 1101 | S | S | S/N/O | N/N/O | Cred | — | N | 554 |
| 015 | COMPRA DE MERCADORIA | 1102 | N | S | S/S/T | S/N/T | Cred | — | N | — |
| 016 | COMPRAS CONTA ORDEM (COMPRAS COM CONTA E ORDEM) | 1101 | S | N | S/S/T | S/S/T | Cred | — | N | 560 |
| 045 | COMPRA MP | 1122 | N | S | S/S/T | N/N/O | Cred | — | N | — |
| 128 | ENTRADA MERCADORIA COMPRA FUTURA | 1117 | S | N | S/S/T | N/N/O | Cred | — | N | — |
| 193 | COMPRA CONTA E ORDEM | 1122 | N | S | S/S/T | S/N/O | Cred | — | N | — |
| 199 | COMPRA ORINADA DE COMPRA FUTURA | 1117 | N | N | S/N/O | N/N/O | — | — | N | — |
| 310 | COMPRA DE MERCADORIA  S IPI | 1102 | S | S | S/N/O | N/N/O | Cred | — | N | — |

### Compras de insumo, matéria-prima e revenda — TES de entrada bloqueadas

| TES | Descrição | CFOP | Estoque | Duplicata | ICMS calc/créd/livro | IPI calc/créd/livro | PIS/COFINS | Poder 3º | Consumo | TES devol. |
|---|---|---|---|---|---|---|---|---|---|---|
| 005 | EMBALAGEM S/ IPI | 1101 | S | S | N/N/O | N/N/O | Cred | — | N | — |
| 006 | COMPRAS | 1101 | N | S | S/S/T | S/S/T | Cred | — | N | — |
| 007 | EMBALAGEM C/ ICM/IPI | 1101 | S | S | S/S/T | S/S/T | Cred | — | N | 560 |
| 013 | COMP. MAT PRIMA | 1101 | N | S | S/S/T | N/N/O | Cred | — | N | — |
| 049 | MATÉRIA-PRIMA - SIMP | 1101 | S | S | N/N/O | N/N/O | Cred | — | N | — |
| 051 | MP SIMPLES S EST | 1101 | N | S | N/N/O | N/N/O | Cred | — | N | — |
| 055 | INTERMEDIÁRIO | 1101 | S | S | N/N/O | N/N/O | Cred | — | N | — |
| 062 | INTERM SIMPLES | 1101 | S | S | N/N/O | N/N/O | Cred | — | N | — |
| 075 | COMPRA | 1101 | N | N | N/N/O | N/N/O | Cred | — | N | — |
| 076 | COMPRA MP | 1101 | N | N | N/N/O | N/N/O | Cred | — | N | — |
| 137 | REM FAT ANTECIPADO | 1116 | N | N | N/N/O | N/N/O | — | — | N | — |
| 138 | ENTRADA MAT PRIMA | 1101 | N | N | S/S/T | S/S/T | Cred | — | N | — |
| 140 | MATERIA PRIMA C/ ST | 1401 | S | S | N/S/T | S/S/T | — | — | N | — |
| 141 | COMPRA M.P COM ST | 1401 | S | S | N/N/O | N/N/O | — | — | N | 652 |
| 143 | COMPRA MP COM ST | 1401 | N | S | N/N/O | N/N/O | — | — | N | — |
| 146 | MAT. PRIMA COM ST | 1401 | S | S | S/S/O | N/N/O | — | — | N | — |
| 405 | COMPRA MP SEM ESTOQU (COMPRA DE MP SEM ESTOQUE) | 1101 | N | S | S/S/T | S/S/O | Cred | — | N | — |

## Importação (entrada)

Entradas de importação (CFOP 3xxx), incluindo drawback e importação para industrialização com ICMS diferido.

- Ativas: 12 TES; 10 atualizam estoque, 0 geram duplicata, 6 creditam ICMS.
- Bloqueadas: nenhuma.
- Códigos ativos: 303, 305, 308, 309, 312, 316, 317, 318, 320, 321, 322, 3A8.

### Importação — TES de entrada ativas

| TES | Descrição | CFOP | Estoque | Duplicata | ICMS calc/créd/livro | IPI calc/créd/livro | PIS/COFINS | Poder 3º | Consumo | TES devol. |
|---|---|---|---|---|---|---|---|---|---|---|
| 303 | COMPRA MATERIA PRIMA | 3101 | S | N | S/S/T | S/S/T | Cred | — | N | — |
| 305 | ENTRADA IMPORTAÇÃO | 3101 | S | N | N/N/O | S/S/T | Cred | — | N | — |
| 308 | ENT.IMPORTACAO DIRET (3101 - IMPORTACAO P/INDUSTRIALIZACAO C/ICMS DIFERIDO E C/IPI E  C/CRED PIS/COFINS) | 3101 | S | N | N/N/O | S/S/T | Cred | — | N | 763 |
| 309 | IMPORT.OUTRAS ENTRAD (IMPORT.OUTRAS ENTRADAS COURRIER) | 3949 | S | N | S/S/T | N/N/O | — | — | N | 721 |
| 312 | COMPRA MP DRAWBACK | 3127 | S | N | N/S/O | N/S/O | — | — | N | — |
| 316 | COMPRA MATERIA PRIMA | 3101 | S | N | S/S/T | S/S/T | Cred | — | N | — |
| 317 | IMPORT.OUTRAS ENTRAD | 3949 | S | N | N/N/T | N/N/O | Calc | — | N | — |
| 318 | IMPORT.OUTRAS ENTRAD | 3101 | S | N | S/S/T | N/N/O | — | — | N | — |
| 320 | ENT.IMPORTACAO DIRET (3101 - IMPORTACAO P/INDUSTRIALIZACAO C/ICMS DIFERIDO E C/IPI E  C/CRED PIS/COFINS) | 3101 | N | N | N/N/O | S/S/T | Cred | — | N | — |
| 321 | ENT.IMPORTACAO DIRET (3101 - IMPORTACAO ATIVO IMOBILIZADO C/ICMS DIFERIDO E C/IPI E  C/CRED PIS/COFINS) | 3551 | N | N | N/N/O | N/N/T | Cred | — | N | — |
| 322 | ENT.IMPORTACAO DIRET (3101 - IMPORTACAO P/INDUSTRIALIZACAO C/ICMS DIFERIDO E C/IPI E  C/CRED PIS/COFINS) | 3101 | S | N | S/S/T | S/S/T | Cred | — | N | 763 |
| 3A8 | ENT.IMPORTACAO DIRET (3101 - IMPORTACAO P/INDUSTRIALIZACAO C/ICMS DIFERIDO E C/IPI E  C/CRED PIS/COFINS) | 3101 | S | N | N/N/O | S/S/T | Cred | — | N | — |

## Industrialização por encomenda (x124/x125) (entrada)

Na entrada: industrialização feita por outra empresa para a Delpi. Na saída: industrialização que a Delpi fez para outra empresa (cobrança do serviço e dos insumos aplicados). A TES 510 é o item que carrega o custo; o par de faturamento da industrialização é a TES 594 (família Vendas).

- Ativas: 4 TES; 3 atualizam estoque, 3 geram duplicata, 3 creditam ICMS.
- Bloqueadas: 4 TES.
- Códigos ativos: 048, 058, 130, 131.

### Industrialização por encomenda (x124/x125) — TES de entrada ativas

| TES | Descrição | CFOP | Estoque | Duplicata | ICMS calc/créd/livro | IPI calc/créd/livro | PIS/COFINS | Poder 3º | Consumo | TES devol. |
|---|---|---|---|---|---|---|---|---|---|---|
| 048 | INDUST. TRIANGULAR | 1125 | S | N | S/S/T | S/S/T | Calc | — | N | — |
| 058 | INDUST. TERC | 1125 | S | S | S/S/T | S/S/T | Cred | — | N | — |
| 130 | INDUSTRI P/OUTRA EMP | 1124 | S | S | S/S/T | N/N/O | Cred | — | N | — |
| 131 | IND. TERCEIROS S/ ES | 1124 | N | S | N/N/O | N/N/I | Cred | — | N | — |

### Industrialização por encomenda (x124/x125) — TES de entrada bloqueadas

| TES | Descrição | CFOP | Estoque | Duplicata | ICMS calc/créd/livro | IPI calc/créd/livro | PIS/COFINS | Poder 3º | Consumo | TES devol. |
|---|---|---|---|---|---|---|---|---|---|---|
| 041 | IND. EFET. 3ºC/IPI | 1124 | N | S | S/S/T | S/S/T | — | — | N | — |
| 054 | INDUST TERC | 1124 | N | N | N/N/O | N/N/O | — | — | N | — |
| 057 | INDUST. TERC | 1124 | S | S | S/S/T | S/S/T | — | — | N | — |
| 132 | INDUST. TERCEIROS | 1124 | S | S | S/S/T | N/N/O | — | — | N | — |

## Remessa e retorno para industrialização (entrada)

Material que vai ou volta de industrialização (CFOP x901, x902, x903). Em regra não geram duplicata e boa parte controla poder de terceiros (Remessa = o material sai ou entra sem mudar de dono; Devolução = retorno desse material). As TES 080, 085 e 159 ficam fora da apuração de despesas do R10.

- Ativas: 10 TES; 5 atualizam estoque, 0 geram duplicata, 0 creditam ICMS, 8 controlam poder de terceiros.
- Bloqueadas: 7 TES.
- Códigos ativos: 021, 073, 079, 080, 081, 085, 159, 207, 301, 412.

### Remessa e retorno para industrialização — TES de entrada ativas

| TES | Descrição | CFOP | Estoque | Duplicata | ICMS calc/créd/livro | IPI calc/créd/livro | PIS/COFINS | Poder 3º | Consumo | TES devol. |
|---|---|---|---|---|---|---|---|---|---|---|
| 021 | ENT IND CONTA E ORDEM ADQ | 1924 | N | N | N/N/O | N/N/O | — | — | N | — |
| 073 | RET. INDUSTRIALIZAÇÃ | 1903 | S | N | N/N/O | N/N/O | — | D | N | — |
| 079 | RETORNO SEM INDUSRIA | 1903 | N | N | N/N/O | N/N/O | — | D | N | 613 |
| 080 | ENTRADA IND.P/ENCOM. | 1901 | N | N | N/N/O | N/N/O | — | R | N | 525 |
| 081 | RETORNO DE INDUSTRIA | 1902 | N | N | N/N/O | N/N/O | — | D | N | 613 |
| 085 | ENTRADA IND.P/ENCOM. | 1901 | S | N | N/N/O | N/N/O | — | R | N | 525 |
| 159 | REMESSA PARA INDUSTR | 1901 | N | N | N/N/O | N/N/O | — | — | N | — |
| 207 | ENTRADA IND.P/ENCOM. (CUSTO ZERO) | 1901 | S | N | N/N/O | N/N/O | — | R | N | 525 |
| 301 | RETORNO INDUSTRIALIZ | 1902 | S | N | N/N/O | N/N/O | — | D | N | 519 |
| 412 | RETORNO DE INDUSTRIALIZACAO | 1902 | S | N | N/N/O | N/N/O | — | R | N | — |

### Remessa e retorno para industrialização — TES de entrada bloqueadas

| TES | Descrição | CFOP | Estoque | Duplicata | ICMS calc/créd/livro | IPI calc/créd/livro | PIS/COFINS | Poder 3º | Consumo | TES devol. |
|---|---|---|---|---|---|---|---|---|---|---|
| 047 | REMESSA TRIANGULAR | 1925 | S | N | N/N/T | N/N/I | — | — | N | — |
| 072 | RETORNO REM | 1902 | N | N | N/N/O | N/N/O | — | R | N | 613 |
| 118 | ENTRADA DE INDUS. | 1901 | N | S | N/N/O | N/N/O | — | R | N | 525 |
| 123 | RETORNO S/ INDUSTRIA | 1903 | N | N | N/N/O | N/N/O | — | — | N | — |
| 147 | RET MERCADORIA IND | 1902 | N | N | N/N/O | N/N/O | — | — | N | — |
| 160 | REMESSA PARA INDUSTR | 1901 | S | N | N/N/O | N/N/O | — | — | N | — |
| 302 | RET. INDUSTRIALIZAÇÃ | 1902 | N | N | N/N/N | N/N/N | — | D | N | 613 |

## Devolução de venda (entrada)

Entrada da mercadoria que a Delpi vendeu e o cliente devolveu (CFOP x201, x202, x410, x411). A TES 120 é a devolução de venda padrão e fica fora da apuração de despesas do R10.

- Ativas: 8 TES; 4 atualizam estoque, 8 geram duplicata, 5 creditam ICMS.
- Bloqueadas: 5 TES.
- Códigos ativos: 011, 014, 120, 127, 181, 191, 201, 415.

### Devolução de venda — TES de entrada ativas

| TES | Descrição | CFOP | Estoque | Duplicata | ICMS calc/créd/livro | IPI calc/créd/livro | PIS/COFINS | Poder 3º | Consumo | TES devol. |
|---|---|---|---|---|---|---|---|---|---|---|
| 011 | DEVOLUCAO DE PRODUTO | 1201 | N | S | S/S/T | N/N/O | Cred | — | N | — |
| 014 | DEV. MERCADORIA | 1202 | S | S | S/S/T | S/N/O | Cred | — | N | — |
| 120 | DEVOLUCAO DE VENDAS | 1201 | S | S | S/S/T | S/S/T | Cred | — | N | 595 |
| 127 | DEVOLUCAO DE VENDAS | 1201 | N | S | S/S/T | S/S/T | Cred | — | N | 594 |
| 181 | DEV VENDA ZONA FRANC | 1203 | S | S | S/N/I | N/N/O | — | — | N | 606 |
| 191 | DEV. MP S/ IPI E S/ (ESTORNO NF MANAUS) | 1201 | N | S | S/N/O | N/N/O | Cred | — | N | — |
| 201 | DEVOLUCAO DE VENDA | 1201 | S | S | S/N/I | N/N/O | Cred | — | N | — |
| 415 | DEVOLUCAO DE PRODUTO   COMPLEMENTAR  IPI | 1201 | N | S | N/S/N | S/N/T | Cred | — | N | — |

### Devolução de venda — TES de entrada bloqueadas

| TES | Descrição | CFOP | Estoque | Duplicata | ICMS calc/créd/livro | IPI calc/créd/livro | PIS/COFINS | Poder 3º | Consumo | TES devol. |
|---|---|---|---|---|---|---|---|---|---|---|
| 009 | DEV. COMPRAS | 1201 | S | N | S/S/T | S/S/T | — | — | N | — |
| 010 | DEVOLVUCÄO DE CLIENT | 1201 | N | S | N/N/O | S/S/T | — | — | N | — |
| 012 | DEV. MP S/ IPI E S/ | 1201 | S | S | N/N/O | N/N/O | — | — | N | — |
| 190 | DEV. VENDA ZFM | 1203 | S | S | S/N/O | N/N/O | — | — | N | 606 |
| 400 | DEVOLUCAO COMPRAS (DEVOLUCAO DE VENDAS - FILIAL 02) | 1201 | S | N | S/S/T | S/S/T | — | — | N | — |

## Transferências entre filiais (entrada)

Transferência de produção, mercadoria ou insumo entre estabelecimentos da Delpi (CFOP x151, x152, x408, x409). Não geram duplicata. A TES 204 (transferência de matéria-prima) fica fora da apuração de despesas do R10.

- Ativas: 4 TES; 3 atualizam estoque, 0 geram duplicata, 3 creditam ICMS.
- Bloqueadas: 1 TES.
- Códigos ativos: 126, 150, 197, 204.

### Transferências entre filiais — TES de entrada ativas

| TES | Descrição | CFOP | Estoque | Duplicata | ICMS calc/créd/livro | IPI calc/créd/livro | PIS/COFINS | Poder 3º | Consumo | TES devol. |
|---|---|---|---|---|---|---|---|---|---|---|
| 126 | TRANSF. MAT. PRIMA | 1151 | S | N | S/S/T | S/S/T | — | — | N | — |
| 150 | TRANSF. MAT. PRIMA | 1151 | S | N | S/S/T | N/N/T | — | — | N | — |
| 197 | TRANSF. MAT. PRIMA | 1151 | N | N | S/S/T | N/N/T | — | — | N | — |
| 204 | TRANSF. MAT. PRIMA | 1151 | S | N | S/N/O | N/N/O | — | — | N | — |

### Transferências entre filiais — TES de entrada bloqueadas

| TES | Descrição | CFOP | Estoque | Duplicata | ICMS calc/créd/livro | IPI calc/créd/livro | PIS/COFINS | Poder 3º | Consumo | TES devol. |
|---|---|---|---|---|---|---|---|---|---|---|
| 157 | TRANSF. ENTRE FILIAI | 1151 | S | N | S/S/T | S/S/T | — | — | N | — |

## Uso e consumo (entrada)

Material de uso e consumo (CFOP x556, x557, x407). Na regra geral não dão crédito de ICMS. Material de consumo com crédito de IPI é ponto de atenção da auditoria de entradas (regra «Crédito de IPI em material de uso e consumo»).

- Ativas: 19 TES; 10 atualizam estoque, 16 geram duplicata, 0 creditam ICMS.
- Bloqueadas: 23 TES.
- Códigos ativos: 008, 017, 018, 019, 024, 031, 052, 069, 070, 088, 106, 142, 151, 155, 156, 166, 169, 189, 406.

### Uso e consumo — TES de entrada ativas

| TES | Descrição | CFOP | Estoque | Duplicata | ICMS calc/créd/livro | IPI calc/créd/livro | PIS/COFINS | Poder 3º | Consumo | TES devol. |
|---|---|---|---|---|---|---|---|---|---|---|
| 008 | CONS ADM C EST S IPI | 1556 | S | S | S/N/O | N/N/O | — | — | S | 711 |
| 017 | CONSUMO RED 70% BASE CALC ICMS | 1556 | S | S | S/N/O | S/S/T | — | — | S | — |
| 018 | INSUMO C EST S IPI (USO PROD INSUMO MATERIAL SEG) | 1556 | S | S | S/N/O | N/N/O | Cred | — | S | 529 |
| 019 | CONSUMO SIMPLES NACIONAL DENTRO ESTADO | 1556 | N | S | N/N/O | N/N/O | — | — | S | 547 |
| 024 | INSUMO RED ICMS CONV 5291 | 1556 | N | S | S/N/O | N/N/O | Cred | — | S | — |
| 031 | CONS ADM S EST S IPI (CONSUMO ADM SEM ESTOQUE E S IPI (ALIMENTACAO,EDIFICACAO,LIMPEZA,EXPEDIENTE)) | 1556 | N | S | S/N/O | N/N/O | — | — | S | 650 |
| 052 | INSUMO C EST C IPI | 1556 | S | S | S/N/O | S/S/T | Cred | — | S | 608 |
| 069 | CONS ADM C EST C IPI BASE | 1556 | S | S | S/N/O | S/N/O | — | — | S | — |
| 070 | CONS ADM SEM IMP C ESTOQUE | 1556 | S | S | S/N/O | N/N/N | — | — | S | 542 |
| 088 | CONSUMO ADM SEM DUPLICATA | 1556 | N | N | S/N/O | N/N/O | — | — | S | — |
| 106 | INSUMO IPI NA BASE (1556 COMPRA USO/CONSUMO C/ICMS IPI) | 1556 | S | S | S/N/O | S/S/O | Cred | — | S | 617 |
| 142 | CONSUMO ST | 1407 | S | S | N/N/O | N/N/O | — | — | N | 620 |
| 151 | TRANS. CONS C EST | 1557 | S | N | S/N/O | N/N/O | — | — | N | — |
| 155 | TRANS. CONS S EST | 1557 | N | N | N/N/O | N/N/O | — | — | N | — |
| 156 | CONSUMO ST | 1407 | N | S | N/N/O | N/N/O | — | — | N | — |
| 166 | CONS ADM S EST C IPI (1556 COMPRA USO/CONSUMO C/ICMS IPI) | 1556 | N | S | S/N/O | S/N/O | — | — | S | 649 |
| 169 | INSUMO C EST C IPI BASE (1556 COMPRA USO/CONSUMO C/ICMS IPI) | 1556 | S | S | S/N/O | S/S/T | Cred | — | S | 530 |
| 189 | MANT MAQ S/ IPI | 1556 | N | S | S/N/O | N/N/O | Cred | — | S | 650 |
| 406 | MANUT MAQUIN COM IPI | 1556 | N | S | S/N/O | S/S/T | Cred | — | S | — |

### Uso e consumo — TES de entrada bloqueadas

| TES | Descrição | CFOP | Estoque | Duplicata | ICMS calc/créd/livro | IPI calc/créd/livro | PIS/COFINS | Poder 3º | Consumo | TES devol. |
|---|---|---|---|---|---|---|---|---|---|---|
| 022 | MAT SEGURANÇA | 1556 | S | S | S/N/O | N/N/O | Cred | — | S | — |
| 023 | FERRAM. PER S/ IPI | 1556 | S | S | S/N/O | N/N/O | Cred | — | S | — |
| 029 | INFORMÁTICA | 1556 | N | S | S/N/O | N/N/O | — | — | S | — |
| 034 | ALIMENTAÇÃO | 1556 | N | S | S/N/O | N/N/O | — | — | S | — |
| 037 | MAN. VEICULOS | 1556 | N | S | S/N/O | N/N/O | — | — | S | — |
| 050 | COMPRA MERC. CONS.ST | 1407 | N | S | S/N/O | N/N/O | — | — | N | — |
| 066 | PEÇAS INFORMATI | 1556 | N | N | S/N/O | N/N/O | — | — | S | — |
| 071 | CONSUMO ADM COM ESTOQUE | 1556 | S | S | S/N/O | N/N/O | — | — | S | — |
| 103 | CONSUMO | 1556 | S | S | S/N/T | N/N/O | — | — | S | — |
| 145 | CONSUMO ST | 1407 | S | S | S/N/T | N/N/O | — | — | N | — |
| 162 | MAT.CONS.C/IPI C/ST (COMPRA MAT.CONSUMO C/ST E C/IPI) | 1407 | S | S | N/N/N | S/N/O | — | — | N | 559 |
| 163 | MAT.CONS.S/IPI C/ST | 1407 | S | S | N/N/O | N/N/N | — | — | N | 574 |
| 167 | COMPRA USO/CONSUMO (1556 COMPRA USO/CONSUMO C/ICMS) | 1556 | N | S | S/N/O | N/N/N | — | — | S | 650 |
| 177 | MANT MAQ S/ IPI | 1556 | S | S | S/N/O | N/N/O | Cred | — | S | — |
| 179 | MATERIAL DE CONSUMO (MATERIAL DE CONSUMO COM DIFA POR DENTRO) | 1556 | S | S | S/N/O | N/N/O | — | — | S | — |
| 195 | CONSUMO ST | 1407 | N | S | S/N/O | S/S/O | Calc | — | N | — |
| 202 | TRANS. CONSUMO | 1557 | S | N | S/N/O | N/N/O | — | — | N | — |
| 307 | AQUISIÇAO CONSUMO ST | 1407 | N | S | N/N/O | N/N/O | — | — | N | 652 |
| 311 | COMPRA USO/CONSUMO | 1556 | S | S | S/N/O | S/N/O | — | — | S | — |
| 314 | CONSUMO COM DIFAL | 1556 | S | S | S/S/T | N/N/O | Calc | — | S | — |
| 315 | CONSUMO S/ IPI | 1556 | N | S | S/N/O | N/N/O | — | — | S | — |
| 403 | CONSUMO ST | 1407 | N | S | N/N/O | S/S/T | — | — | N | — |
| 409 | TRANS. CONSUMO | 1557 | S | N | N/S/O | N/N/O | — | — | N | — |

## Combustíveis e lubrificantes (entrada)

Compra de combustível e lubrificante para consumo (CFOP x651/x652/x653).

- Ativas: 4 TES; 3 atualizam estoque, 4 geram duplicata, 0 creditam ICMS.
- Bloqueadas: nenhuma.
- Códigos ativos: 038, 108, 184, 185.

### Combustíveis e lubrificantes — TES de entrada ativas

| TES | Descrição | CFOP | Estoque | Duplicata | ICMS calc/créd/livro | IPI calc/créd/livro | PIS/COFINS | Poder 3º | Consumo | TES devol. |
|---|---|---|---|---|---|---|---|---|---|---|
| 038 | COMBUST. E LUB ADM | 1653 | N | S | N/N/O | N/N/O | — | — | S | — |
| 108 | COMBUST. E LUB ADM | 1653 | S | S | N/N/O | N/N/O | — | — | S | — |
| 184 | COMBUST. E LUB PROD | 1653 | S | S | S/N/O | S/S/O | Cred | — | S | — |
| 185 | COMBUST. E LUB PROD | 1653 | S | S | S/N/O | N/N/O | Cred | — | S | — |

## Ativo imobilizado (entrada)

Compra, remessa, retorno, venda e transferência de bens do ativo, e lançamento do crédito de ICMS do ativo (CIAP, CFOP x604). Não atualizam o ativo fixo pela TES no cadastro desta extração (Atual.Ativo? = Não em todas).

- Ativas: 7 TES; 1 atualizam estoque, 6 geram duplicata, 0 creditam ICMS.
- Bloqueadas: 10 TES.
- Códigos ativos: 133, 144, 153, 174, 182, 187, 205.

### Ativo imobilizado — TES de entrada ativas

| TES | Descrição | CFOP | Estoque | Duplicata | ICMS calc/créd/livro | IPI calc/créd/livro | PIS/COFINS | Poder 3º | Consumo | TES devol. |
|---|---|---|---|---|---|---|---|---|---|---|
| 133 | ATIVO PERM. PRODUCAO | 1551 | N | S | N/N/O | N/N/O | Cred | — | S | 547 |
| 144 | ATIVO COM ST | 1406 | S | S | N/N/O | N/N/O | — | — | N | — |
| 153 | COMPRA ATIVO IMOB | 1551 | N | S | N/N/O | N/N/O | — | — | N | 547 |
| 174 | TRANS. ATIVO | 1552 | N | N | S/N/O | N/N/O | — | — | N | — |
| 182 | COMPRA ATIVO IMOB | 1551 | N | S | S/N/O | N/N/N | — | — | N | 588 |
| 187 | ATIVO PERM.PROD | 1551 | N | S | S/N/O | S/N/O | Calc | — | S | — |
| 205 | ATIVO PERM.PROD (BASE DE CALC. RED. 26,57%) | 1551 | N | S | S/N/O | S/N/O | Calc | — | S | — |

### Ativo imobilizado — TES de entrada bloqueadas

| TES | Descrição | CFOP | Estoque | Duplicata | ICMS calc/créd/livro | IPI calc/créd/livro | PIS/COFINS | Poder 3º | Consumo | TES devol. |
|---|---|---|---|---|---|---|---|---|---|---|
| 044 | CREDITO ICMS ATIVO | 1604 | N | N | S/S/O | N/N/N | — | — | N | — |
| 060 | COMPRA DE ATIVO IMOB | 1551 | S | S | N/N/O | N/N/O | — | — | N | — |
| 078 | REM. ATIVO | 1554 | N | N | N/N/O | N/N/O | — | — | N | 527 |
| 086 | ENTRADA ATIVO IMOBIL | 1555 | N | N | N/N/O | N/N/O | — | R | N | 527 |
| 102 | REM ATIVO | 1554 | N | N | N/N/O | N/N/O | — | R | N | 527 |
| 152 | TRANS. ATIVO | 1552 | S | N | N/N/O | N/N/O | — | — | N | — |
| 154 | COMPRA ATIVO IMOB | 1406 | N | S | N/N/O | N/N/O | — | — | N | — |
| 171 | COMPRA ATIVO IMOB | 1551 | N | S | N/S/O | N/S/O | — | — | N | — |
| 176 | TRANS. ATIVO | 1552 | S | N | N/N/O | N/N/O | — | — | N | — |
| 260 | CRED. ATIVO IMOBILIZ | 1604 | N | N | N/N/O | N/N/N | — | — | N | — |

## Energia elétrica (entrada)

Aquisição de energia elétrica (CFOP x252/x253). A TES 020 fica fora da apuração de despesas do R10.

- Ativas: 3 TES; 0 atualizam estoque, 2 geram duplicata, 1 creditam ICMS.
- Bloqueadas: nenhuma.
- Códigos ativos: 020, 402, 416.

### Energia elétrica — TES de entrada ativas

| TES | Descrição | CFOP | Estoque | Duplicata | ICMS calc/créd/livro | IPI calc/créd/livro | PIS/COFINS | Poder 3º | Consumo | TES devol. |
|---|---|---|---|---|---|---|---|---|---|---|
| 020 | AQUIS. ENER. ELETR. | 1252 | N | S | S/S/T | N/N/O | Cred | — | N | — |
| 402 | ENERGIA ELETRICA | 1252 | N | S | N/N/O | N/N/O | Cred | — | N | — |
| 416 | ENERGIA ELETRICA  VALOR ZERADO | 1252 | N | N | N/N/O | N/N/O | Cred | — | N | — |

## Comunicação (entrada)

Serviços de comunicação (CFOP x302/x303). A TES 030 fica fora da apuração de despesas do R10.

- Ativas: 2 TES; 0 atualizam estoque, 2 geram duplicata, 0 creditam ICMS.
- Bloqueadas: nenhuma.
- Códigos ativos: 030, 408.

### Comunicação — TES de entrada ativas

| TES | Descrição | CFOP | Estoque | Duplicata | ICMS calc/créd/livro | IPI calc/créd/livro | PIS/COFINS | Poder 3º | Consumo | TES devol. |
|---|---|---|---|---|---|---|---|---|---|---|
| 030 | SERV. COMUNICAÇÃO | 1302 | N | S | N/N/O | N/N/O | — | — | N | — |
| 408 | SERV. COMUNICAÇÃO | 1302 | N | S | N/N/O | N/N/O | — | — | N | — |

## Frete e transporte (entrada)

Conhecimentos de transporte (CT-e) e anulação de frete (CFOP x352, x353, x206, x932). O crédito de ICMS do frete depende do que foi transportado: frete de venda ou de insumo dá direito; frete de consumo ou ativo não. A auditoria de entradas identifica frete pelo CFOP terminado em 352 e lê o crédito na TES (ficha AE-05). A TES 040 fica fora da apuração de despesas do R10.

- Ativas: 8 TES; 4 atualizam estoque, 6 geram duplicata, 3 creditam ICMS.
- Bloqueadas: 1 TES.
- Códigos ativos: 025, 026, 040, 042, 148, 158, 165, 180.

### Frete e transporte — TES de entrada ativas

| TES | Descrição | CFOP | Estoque | Duplicata | ICMS calc/créd/livro | IPI calc/créd/livro | PIS/COFINS | Poder 3º | Consumo | TES devol. |
|---|---|---|---|---|---|---|---|---|---|---|
| 025 | FRETE S/ MAN. MAQ. | 1352 | N | S | S/N/O | N/N/I | Cred | — | S | — |
| 026 | FRETE ATIVO | 1352 | N | S | S/N/O | N/N/I | — | — | S | — |
| 040 | AQUIS. SERV.TRANSP. | 1352 | S | S | S/S/T | N/N/I | Cred | — | N | — |
| 042 | TRANSP. CONSUMO (FRETE CONSUMO SEM CRED ICMS PIS COF) | 1352 | S | S | S/N/O | N/N/O | — | — | S | — |
| 148 | AQUIS. TRANSP VENDA | 1352 | N | S | S/S/T | N/N/O | Cred | — | N | — |
| 158 | AQUISIÇÃO SERV TRANS | 1352 | S | N | S/S/T | N/N/O | Cred | — | N | — |
| 165 | FRETE SIMPLES NACION | 1352 | N | S | N/N/O | N/N/O | Cred | — | N | — |
| 180 | AQUIS. TRANSPORTE RO | 1352 | S | N | N/N/O | N/N/O | Cred | — | N | — |

### Frete e transporte — TES de entrada bloqueadas

| TES | Descrição | CFOP | Estoque | Duplicata | ICMS calc/créd/livro | IPI calc/créd/livro | PIS/COFINS | Poder 3º | Consumo | TES devol. |
|---|---|---|---|---|---|---|---|---|---|---|
| 036 | FRETE S/ VENDAS | 1352 | N | S | S/S/O | N/N/I | Cred | — | N | — |

## Serviços tomados (entrada)

Serviços tributados pelo ISS (CFOP x933). A TES 046 aparece no R10 na exclusão da coparticipação de plano de saúde (parcela do colaborador).

- Ativas: 3 TES; 0 atualizam estoque, 3 geram duplicata, 0 creditam ICMS.
- Bloqueadas: 13 TES.
- Códigos ativos: 028, 032, 046.

### Serviços tomados — TES de entrada ativas

| TES | Descrição | CFOP | Estoque | Duplicata | ICMS calc/créd/livro | IPI calc/créd/livro | PIS/COFINS | Poder 3º | Consumo | TES devol. |
|---|---|---|---|---|---|---|---|---|---|---|
| 028 | SERV. 3º PROD. IR | 1933 | N | S | N/N/O | N/N/O | Cred | — | N | — |
| 032 | SERV. ADM FATURAS | 1933 | N | S | N/N/N | N/N/N | — | — | N | — |
| 046 | SERVICOS ADM/CONSUMO | 1933 | N | S | N/N/O | N/N/N | — | — | N | — |

### Serviços tomados — TES de entrada bloqueadas

| TES | Descrição | CFOP | Estoque | Duplicata | ICMS calc/créd/livro | IPI calc/créd/livro | PIS/COFINS | Poder 3º | Consumo | TES devol. |
|---|---|---|---|---|---|---|---|---|---|---|
| 033 | VALE TRANSPORTES | 1933 | N | S | N/N/O | N/N/O | — | — | S | — |
| 039 | SAMAE | 1933 | N | S | N/N/N | N/N/N | — | — | N | — |
| 043 | SERV. MANUT. | 1933 | N | N | N/N/O | N/N/O | — | — | N | — |
| 053 | FRETE VENDAS SIMPLES | 1933 | N | S | N/N/N | N/N/N | — | — | N | — |
| 061 | VIGILANCIA | 1933 | N | S | N/N/I | N/N/I | — | — | N | — |
| 063 | MED TRABALHO | 1933 | N | S | N/N/I | N/N/I | — | — | N | — |
| 064 | COMISSAO | 1933 | N | S | N/N/N | N/N/N | — | — | N | — |
| 065 | CONTABILIDADE | 1933 | N | N | N/N/N | N/N/N | — | — | N | — |
| 067 | JURIDICO | 1933 | N | S | N/N/N | N/N/N | — | — | N | — |
| 113 | SERV. COM RETENÇ | 1933 | N | S | N/N/N | N/N/I | — | — | N | — |
| 261 | PRESTAÇÃO DE SERVIÇO | 1933 | N | S | N/N/I | N/N/I | — | — | N | — |
| 401 | TICKET ALIMENTAÇÃO | 1933 | N | S | N/N/I | N/N/O | — | — | N | — |
| 407 | NF SERVIÇO C/ RED. | 1933 | N | S | N/N/I | N/N/I | — | — | N | — |

## Conserto e reparo (entrada)

Remessa e retorno de bens para conserto (CFOP x915/x916). Não geram duplicata.

- Ativas: 5 TES; 3 atualizam estoque, 0 geram duplicata, 0 creditam ICMS, 4 controlam poder de terceiros.
- Bloqueadas: 6 TES.
- Códigos ativos: 094, 097, 099, 100, 262.

### Conserto e reparo — TES de entrada ativas

| TES | Descrição | CFOP | Estoque | Duplicata | ICMS calc/créd/livro | IPI calc/créd/livro | PIS/COFINS | Poder 3º | Consumo | TES devol. |
|---|---|---|---|---|---|---|---|---|---|---|
| 094 | RET CONSERTO S/EST C/POD3 | 1916 | N | N | N/N/O | N/N/N | — | D | N | — |
| 097 | REM P/CONSERTO C/EST C/POD3 | 1915 | S | N | N/N/O | N/N/N | — | R | N | 541 |
| 099 | REM P/CONSERTO S/EST C/POD3 | 1915 | N | N | N/N/O | N/N/N | — | R | N | 541 |
| 100 | RET CONSERTO C/EST C/POD3 | 1916 | S | N | N/N/O | N/N/N | — | D | N | 542 |
| 262 | REM P/CONSERTO C/EST C/POD3 | 1915 | S | N | N/N/O | N/N/N | — | — | N | — |

### Conserto e reparo — TES de entrada bloqueadas

| TES | Descrição | CFOP | Estoque | Duplicata | ICMS calc/créd/livro | IPI calc/créd/livro | PIS/COFINS | Poder 3º | Consumo | TES devol. |
|---|---|---|---|---|---|---|---|---|---|---|
| 074 | REMESSA CONSERTO | 1915 | N | N | N/N/O | N/N/O | — | — | N | 518 |
| 077 | REMESSA P/ CONSERTO | 1915 | N | N | S/N/O | N/N/I | — | D | N | — |
| 098 | ENTRADA DE BEM CONS. | 1916 | N | N | N/N/N | N/N/N | — | — | N | — |
| 107 | RET.MERC.REM.CONSER. | 1916 | N | N | N/N/O | N/N/O | — | — | N | — |
| 121 | RET. REM. CONSERTO | 1916 | N | N | N/N/I | N/N/N | — | D | N | — |
| 183 | RET.MERC.REM.CONSERT | 1916 | N | N | S/S/O | N/N/O | — | — | N | — |

## Vasilhame e embalagem retornável (entrada)

Vasilhame e embalagem retornável (CFOP x920/x921) — na Delpi, os carretéis dos cabos. A TES 083 fica fora da apuração de despesas do R10.

- Ativas: 2 TES; 1 atualizam estoque, 0 geram duplicata, 0 creditam ICMS, 2 controlam poder de terceiros.
- Bloqueadas: 2 TES.
- Códigos ativos: 083, 124.

### Vasilhame e embalagem retornável — TES de entrada ativas

| TES | Descrição | CFOP | Estoque | Duplicata | ICMS calc/créd/livro | IPI calc/créd/livro | PIS/COFINS | Poder 3º | Consumo | TES devol. |
|---|---|---|---|---|---|---|---|---|---|---|
| 083 | ENTRADA DE VASILHAME | 1920 | N | N | N/N/I | N/N/N | — | R | N | 550 |
| 124 | RET. EMBALAGEM | 1921 | S | N | N/N/O | N/N/O | — | D | N | 668 |

### Vasilhame e embalagem retornável — TES de entrada bloqueadas

| TES | Descrição | CFOP | Estoque | Duplicata | ICMS calc/créd/livro | IPI calc/créd/livro | PIS/COFINS | Poder 3º | Consumo | TES devol. |
|---|---|---|---|---|---|---|---|---|---|---|
| 119 | ENTRADA DE EMBALAGEM | 1920 | S | N | N/N/O | N/N/O | — | — | N | 550 |
| 249 | ENTRADA DE EMBALAGEM | 1920 | S | N | N/N/O | N/N/O | — | R | N | 550 |

## Bonificação, amostra, demonstração, consignação e comodato (entrada)

Bonificação (x910), amostra grátis (x911), demonstração (x912/x913), consignação (x917–x919) e comodato (x908/x909). Em regra não geram duplicata.

- Ativas: 22 TES; 10 atualizam estoque, 0 geram duplicata, 7 creditam ICMS, 3 controlam poder de terceiros.
- Bloqueadas: 12 TES.
- Códigos ativos: 059, 084, 089, 090, 091, 092, 093, 105, 109, 117, 125, 134, 149, 178, 186, 188, 192, 194, 196, 198, 200, 250.

### Bonificação, amostra, demonstração, consignação e comodato — TES de entrada ativas

| TES | Descrição | CFOP | Estoque | Duplicata | ICMS calc/créd/livro | IPI calc/créd/livro | PIS/COFINS | Poder 3º | Consumo | TES devol. |
|---|---|---|---|---|---|---|---|---|---|---|
| 059 | BONIFICAÇÃO PROD | 1910 | S | N | S/S/T | S/S/T | Cred | — | N | — |
| 084 | ENTRADA DE AMOSTRAS | 1911 | N | N | S/S/T | N/N/O | Cred | — | N | — |
| 089 | AMOSTRA GRATIS | 1911 | S | N | N/N/O | N/N/O | — | — | N | — |
| 090 | ENT. AMOSTRA GRATIS | 1911 | N | N | S/S/T | S/S/T | — | — | N | — |
| 091 | AMOSTRA TRIBUTADA | 1911 | S | N | S/S/T | S/S/T | — | — | N | — |
| 092 | ENTRADA DE AMOSTRAS | 1911 | N | N | N/N/O | N/N/O | — | — | N | — |
| 093 | ENTRADA DE AMOSTRAS IPI NA BASE | 1911 | S | N | S/S/O | S/S/T | — | — | N | — |
| 105 | RET DEMONST C/EST | 1913 | S | N | S/N/O | S/S/T | Cred | — | N | — |
| 109 | RET DEMONST S/EST S/POD3 | 1913 | S | N | N/N/O | N/N/N | — | — | N | — |
| 117 | BONIFICACAO ADM | 1910 | N | N | S/N/T | S/N/N | — | — | N | — |
| 125 | ENTRADA P/ DEMONST. | 1912 | S | N | N/N/O | N/N/O | — | — | N | — |
| 134 | AMOSTRA | 1911 | S | N | S/S/T | N/N/O | — | — | N | — |
| 149 | AMOSTRA GRATIS MP | 1911 | N | N | S/N/O | N/S/O | — | — | N | — |
| 178 | REM COMODATO | 1908 | N | N | N/N/O | N/N/O | — | R | N | 641 |
| 186 | RET. COMODATO | 1909 | N | N | N/N/O | N/N/O | — | D | N | — |
| 188 | RET DEMONST S/EST | 1913 | N | N | N/N/O | S/N/O | — | — | N | 576 |
| 192 | BONIFICAÇÃO PROD | 1910 | N | N | S/S/T | S/S/T | Cred | — | N | — |
| 194 | REMESSA P/ DEMONSTRA | 1912 | S | N | S/N/O | S/S/T | — | — | N | 585 |
| 196 | BONIFICACAO ADM | 1910 | N | N | S/N/O | N/N/O | — | — | N | — |
| 198 | RET. DEMONST S/EST C/POD3 | 1913 | N | N | N/N/T | N/N/N | — | D | N | — |
| 200 | RET DEMONST S/EST S/POD3 | 1913 | N | N | N/N/O | N/N/N | — | — | N | — |
| 250 | DEMONSTRAÇÃO | 1912 | S | N | S/N/O | N/N/O | — | — | N | 579 |

### Bonificação, amostra, demonstração, consignação e comodato — TES de entrada bloqueadas

| TES | Descrição | CFOP | Estoque | Duplicata | ICMS calc/créd/livro | IPI calc/créd/livro | PIS/COFINS | Poder 3º | Consumo | TES devol. |
|---|---|---|---|---|---|---|---|---|---|---|
| 068 | DEMONSTRA | 1912 | N | N | N/N/O | N/N/O | — | — | N | 543 |
| 087 | REMESSA P/ DEMOSTRAÇ | 1912 | N | N | S/S/T | S/S/T | — | R | N | 535 |
| 095 | REM. DE DEMONTRACAO | 1912 | S | N | S/S/T | N/N/O | — | R | N | 535 |
| 096 | ENTRADA P/ DEMONST. | 1912 | S | N | S/S/T | N/N/O | — | R | N | 536 |
| 101 | RET. REM. CONSIGNACA | 1918 | S | N | S/S/T | S/S/T | — | — | N | — |
| 104 | REMESSA P/ DEMONSTRA | 1912 | N | N | N/N/O | N/N/O | — | R | N | 558 |
| 135 | REM COMODATO | 1908 | N | N | N/N/O | N/N/O | — | D | N | — |
| 170 | DEMONSTRAÇÃO | 1912 | S | N | N/N/O | N/N/O | — | — | N | 579 |
| 173 | REMESSA P/ DEMOSTRAÇ | 1912 | N | N | N/N/N | S/S/T | — | — | N | 578 |
| 319 | ENT. AMOSTRA GRATIS | 1911 | S | N | S/S/T | S/S/T | Calc | — | N | — |
| 410 | DEVOLUCAO AMOSTRA | 1911 | N | N | N/N/O | N/N/O | — | D | N | — |
| 411 | DEVOLUCAO DE AMOSTRA | 1911 | N | N | N/N/O | N/N/O | — | R | N | — |

## Entrega futura e conta e ordem (entrada)

Lançamento para entrega futura e venda à ordem (CFOP x922/x923).

- Ativas: 1 TES; 0 atualizam estoque, 1 geram duplicata, 0 creditam ICMS.
- Bloqueadas: nenhuma.
- Códigos ativos: 056.

### Entrega futura e conta e ordem — TES de entrada ativas

| TES | Descrição | CFOP | Estoque | Duplicata | ICMS calc/créd/livro | IPI calc/créd/livro | PIS/COFINS | Poder 3º | Consumo | TES devol. |
|---|---|---|---|---|---|---|---|---|---|---|
| 056 | VENDA COM ENTREGA FUTURA | 1922 | N | S | N/N/O | N/N/O | — | — | N | — |

## Outras operações e estornos (entrada)

Outras entradas e saídas não especificadas (CFOP x949), estornos e ajustes. Descrição genérica: confira a finalidade da nota antes de concluir qualquer efeito.

- Ativas: 16 TES; 6 atualizam estoque, 5 geram duplicata, 8 creditam ICMS, 1 controlam poder de terceiros.
- Bloqueadas: 10 TES.
- Códigos ativos: 035, 082, 110, 111, 112, 115, 129, 136, 139, 164, 168, 172, 206, 248, 413, 414.

### Outras operações e estornos — TES de entrada ativas

| TES | Descrição | CFOP | Estoque | Duplicata | ICMS calc/créd/livro | IPI calc/créd/livro | PIS/COFINS | Poder 3º | Consumo | TES devol. |
|---|---|---|---|---|---|---|---|---|---|---|
| 035 | NFS S/ DUPLICATA | 1949 | S | N | S/N/O | N/N/O | — | — | N | — |
| 082 | OUTRAS ENTRADAS | 1949 | N | S | N/N/O | N/N/O | — | — | N | 753 |
| 110 | OUTRAS ENTRADAS | 1949 | N | N | S/S/T | S/S/T | — | — | N | 634 |
| 111 | OUTRAS ENTRADAS IPI NA BASE | 1949 | S | N | S/S/T | S/S/T | Cred | — | N | 600 |
| 112 | OUTRAS ENT. N/ESPCIF (PEÇAS DE REPOSICAO IMPORTAÇÃO CONTA E ORDEM) | 1949 | N | N | S/N/O | S/S/T | Cred | — | N | 618 |
| 115 | SUBST EM GARANTIA | 1949 | N | N | S/S/T | N/N/N | — | D | N | 571 |
| 129 | OUTRAS ENT. N ESPECI | 1949 | N | N | S/N/O | N/N/O | — | — | N | — |
| 136 | ENTRADA MAT FALTANTE | 1949 | N | N | S/N/O | N/N/O | — | — | N | — |
| 139 | OUTRAS ENT. N ESPECI | 1949 | N | N | S/N/O | N/N/O | — | — | N | — |
| 164 | OUTRA ENT.NAO ESPEC. | 1949 | N | N | S/S/T | N/N/O | — | — | N | 571 |
| 168 | ESTORNO 5124 (1949 DEVOLUCAO INDUSTRIALIZACAO) | 1949 | S | S | N/N/O | N/N/O | Cred | — | N | 622 |
| 172 | OUTRAS ENTRADAS | 1949 | S | N | S/S/T | N/N/N | — | — | N | 616 |
| 206 | CONTA E ORDEM ATIVO IMOBILIZADO | 1949 | N | N | S/N/O | N/N/O | Cred | — | N | — |
| 248 | OUTRAS ENTRADAS | 1949 | N | S | S/S/T | S/S/T | — | — | N | — |
| 413 | DEVOLUCAO | 1949 | S | S | S/S/O | N/N/O | — | — | N | — |
| 414 | DEVOLUCAO | 1949 | S | S | S/S/O | N/N/O | Cred | — | N | — |

### Outras operações e estornos — TES de entrada bloqueadas

| TES | Descrição | CFOP | Estoque | Duplicata | ICMS calc/créd/livro | IPI calc/créd/livro | PIS/COFINS | Poder 3º | Consumo | TES devol. |
|---|---|---|---|---|---|---|---|---|---|---|
| 027 | SERV. 3º ADM S/ ISS | 1949 | N | S | N/N/N | N/N/N | — | — | N | — |
| 114 | OUTRA ENT.NAO ESPEC. | 1949 | N | N | S/S/T | N/N/O | — | R | N | 568 |
| 116 | OUTRAS ENTRADAS | 1949 | N | S | N/N/N | N/N/N | — | — | N | — |
| 122 | ESTORNO PODER TERCEIRO | 1949 | S | N | N/N/O | N/N/O | — | D | N | 622 |
| 161 | OUTRAS ENTRADAS | 1949 | S | S | N/N/O | N/N/O | — | — | N | — |
| 175 | OUTRAS ENTRADAS | 1949 | N | S | S/S/T | N/N/N | — | — | N | 530 |
| 203 | ESTORNO | 2949 | S | S | S/S/T | N/N/O | — | — | N | — |
| 300 | SERV. INFORM. 01 | 1949 | N | S | N/N/O | N/N/O | — | — | N | — |
| 313 | OUTRAS ENT. N ESPECI | 2949 | N | S | N/N/O | N/N/O | — | — | N | — |
| 404 | ESTORNO | 2949 | S | S | S/N/T | N/N/O | — | — | N | — |

## Governança

- Owner do cadastro: Controladoria e equipe fiscal. A CLARA não cria, edita nem bloqueia TES.
- Bloqueada (`F4_MSBLQL`) = não pode ser usada em nota nova. Nota antiga pode ter TES hoje bloqueada: isso é normal e não é erro.
- Configuração estranha no cadastro é ponto a verificar com o fiscal, nunca erro confirmado (ficha TES-02).
- Atualização: gerar CSV novo da SF4, rodar `fonte/gerar_catalogo_tes.py`, revisar o diff e republicar o corpus.
