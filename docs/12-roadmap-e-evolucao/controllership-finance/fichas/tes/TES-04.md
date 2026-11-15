# TES-04 — Catálogo das TES de saída

Versão da ficha: 1.0 · 14/11/2026 · gerada de `fonte/sf4-2026-11-09.csv` por `fonte/gerar_catalogo_tes.py`.

## Identificação

- Código: **TES-04** — catálogo das TES de saída cadastradas na SF4 da Delpi.
- Implementação: **IMPLEMENTED** (conhecimento citável; a CLARA não lê a SF4 ao vivo).
- Fonte: extração da SF4 fornecida pela Controladoria em 09/11/2026 (a mesma cópia usada pela auditoria de entradas). OWNER_REPORTED_VIA_PO.
- Faixa de códigos de saída: **501 a 764**. Total: **206 TES**, das quais **93 ativas** e **113 bloqueadas**. PROVEN (cadastro de 09/11/2026).
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

## Exportação (saída)

Saídas para o exterior (CFOP 7xxx).

- Ativas: 10 TES; 8 atualizam estoque, 4 geram duplicata, 0 creditam ICMS.
- Bloqueadas: 1 TES.
- Códigos ativos: 659, 662, 667, 719, 720, 721, 723, 724, 763, 764.

### Exportação — TES de saída ativas

| TES | Descrição | CFOP | Estoque | Duplicata | ICMS calc/créd/livro | IPI calc/créd/livro | PIS/COFINS | Poder 3º | Consumo | TES devol. |
|---|---|---|---|---|---|---|---|---|---|---|
| 659 | EXP . DRAWBACK | 7127 | S | S | S/N/O | N/N/O | — | — | N | — |
| 662 | VENDA EXPORTACAO | 7101 | S | S | S/N/O | N/N/O | — | — | N | — |
| 667 | VENDA EXPORTACAO | 7101 | S | S | S/N/O | N/N/O | Deb | — | N | — |
| 719 | EXPORTAÇÃO MERCADORI | 7102 | S | S | S/N/O | N/N/O | Deb | — | N | — |
| 720 | AMOSTRA EXP | 7949 | S | N | S/N/O | N/N/O | — | — | N | — |
| 721 | IMPORT.OUTRAS ENTRAD | 7949 | S | N | S/N/O | N/N/O | — | — | N | 309 |
| 723 | AMOSTRA EXP | 7949 | S | N | S/N/O | N/N/O | — | — | N | — |
| 724 | IMPORT.OUTRAS ENTRAD | 7949 | N | N | S/N/O | N/N/O | — | — | N | 309 |
| 763 | ENT.IMPORTACAO DIRET (7949 - IMPORTACAO P/INDUSTRIALIZACAO C/ICMS DIFERIDO E C/IPI E  C/CRED PIS/COFINS) | 7201 | N | N | S/N/O | S/S/T | Deb | — | N | 308 |
| 764 | ENT.IMPORTACAO DIRET (7949 - IMPORTACAO P/INDUSTRIALIZACAO C/ICMS DIFERIDO E C/IPI E  C/CRED PIS/COFINS) | 7201 | S | N | N/N/O | S/S/T | Deb | — | N | 308 |

### Exportação — TES de saída bloqueadas

| TES | Descrição | CFOP | Estoque | Duplicata | ICMS calc/créd/livro | IPI calc/créd/livro | PIS/COFINS | Poder 3º | Consumo | TES devol. |
|---|---|---|---|---|---|---|---|---|---|---|
| 750 | AMOSTRA GRATIS | 7949 | S | N | N/N/I | N/N/I | — | — | N | — |

## Vendas (saída)

Venda de produção própria e de mercadoria de revenda (CFOP x101, x102, x401, x405). O CPV gerencial usa os CFOPs 5101, 5124, 6101 e 6124 com o custo do item (D2_CUSTO1). Atenção: o mesmo CFOP 5101 tem TES que baixam estoque e TES que não baixam (ex.: 614 baixa; 594 não baixa e tem custo zero).

- Ativas: 16 TES; 12 atualizam estoque, 16 geram duplicata, 13 creditam ICMS.
- Bloqueadas: 29 TES.
- Códigos ativos: 501, 505, 506, 515, 538, 594, 606, 609, 614, 619, 663, 666, 706, 707, 708, 716.

### Vendas — TES de saída ativas

| TES | Descrição | CFOP | Estoque | Duplicata | ICMS calc/créd/livro | IPI calc/créd/livro | PIS/COFINS | Poder 3º | Consumo | TES devol. |
|---|---|---|---|---|---|---|---|---|---|---|
| 501 | VENDA DE PRODUCAO DO ESTABELECIMENTO | 5101 | S | S | S/S/T | S/S/T | Deb | — | N | 120 |
| 505 | VENDA DE PRODUCAO DO ESTABELECIMENTO | 5101 | N | S | S/S/T | S/S/T | Deb | — | N | — |
| 506 | VENDA DE MERC. ADQ. OU RECEBIDA DE TERC. | 5102 | S | S | S/S/T | S/S/T | Deb | — | N | — |
| 515 | VENDA MERC. ADQ. RECEBIDA TERC. S/ IPI | 5102 | S | S | S/S/T | N/N/O | Deb | — | N | — |
| 538 | VENDA MERC. ADQ. RECEBIDA TERC. | 5102 | S | S | S/S/T | N/N/O | Deb | — | N | — |
| 594 | VENDA DE PRODUCAO DO ESTABELECIMENTO | 5101 | N | S | S/S/T | S/S/T | Deb | — | N | 127 |
| 606 | VENDA DE PRODUCAO DO ESTAB. ZFM | 6109 | S | S | S/N/I | N/N/O | — | — | N | 181 |
| 609 | VENDA DE PRODUCAO DO ESTAB. CONSUMO | 5101 | S | S | S/S/T | S/S/T | Deb | — | N | — |
| 614 | VENDA DE PRODUCAO DO ESTABELECIMENTO | 5101 | S | S | S/S/T | S/S/T | Deb | — | N | 120 |
| 619 | VENDA DE PRODUCAO DO ESTAB. SUCATAS | 5101 | N | S | S/N/O | N/N/O | Deb | — | N | — |
| 663 | VENDA DE PRODUCAO DO ESTABELECIMENTO | 5101 | S | S | S/S/T | N/N/O | Deb | — | N | 011 |
| 666 | VENDA MERC. ADQ. RECEBIDA TERC. | 5102 | S | S | S/S/T | S/S/T | Deb | — | N | — |
| 706 | VENDA DE PRODUCAO DO ESTABELECIMENTO (VENDA) | 5101 | S | S | S/S/T | S/S/T | Deb | — | N | 120 |
| 707 | VENDA DE PRODUCAO DO ESTAB. CONSUMO RED (VENDA) | 5101 | S | S | S/S/T | S/S/T | Deb | — | N | 120 |
| 708 | VENDA DE PRODUCAO DO ESTABELECIMENTO | 5101 | S | S | S/N/O | S/S/T | Deb | — | N | 120 |
| 716 | VENDA DE PRODUCAO DO ESTABELECIMENTO (VENDA) | 5101 | N | S | S/S/T | S/S/T | Deb | — | N | 009 |

### Vendas — TES de saída bloqueadas

| TES | Descrição | CFOP | Estoque | Duplicata | ICMS calc/créd/livro | IPI calc/créd/livro | PIS/COFINS | Poder 3º | Consumo | TES devol. |
|---|---|---|---|---|---|---|---|---|---|---|
| 502 | VENDA DE MERCADORIAS | 5102 | N | S | N/S/T | S/S/T | Deb | — | N | — |
| 503 | VENDA S ICMS | 5101 | N | S | N/N/T | S/S/T | Deb | — | N | 010 |
| 504 | VENDAS | 5101 | S | S | S/S/T | S/S/T | Deb | — | N | — |
| 507 | VENDAS | 5101 | N | S | S/N/T | S/S/T | Deb | — | N | 120 |
| 508 | VENDAS | 5101 | S | S | N/N/O | S/S/T | Deb | — | N | 009 |
| 509 | VENDA REM.ANT.CONSIG | 6111 | N | S | N/N/N | N/N/N | — | — | N | — |
| 513 | VENDA MERC. S/ ESTOQ | 5102 | N | S | S/S/T | S/S/T | Deb | — | N | — |
| 516 | COMPLEM. ICMS | 5101 | N | N | S/S/T | N/N/N | — | — | N | — |
| 517 | VENDA SUBS. TRIB | 5401 | S | S | S/S/T | S/S/T | Deb | — | N | — |
| 523 | VENDA | 5101 | S | S | S/S/O | N/N/O | Deb | — | N | — |
| 545 | VENDA REMETIDA P IND | 5122 | S | S | S/S/T | S/S/T | — | — | N | — |
| 556 | VENDA MERC. A ORDEM | 5123 | S | S | S/S/T | S/S/T | Deb | — | N | — |
| 565 | VENDA PROD. PROPRIA | 5401 | S | S | N/N/O | S/S/T | Deb | — | N | — |
| 566 | VENDA PRODUÇÃO | 5101 | N | S | N/N/O | S/S/T | Deb | — | N | — |
| 573 | VENDA MERC. ADQ. RECEBIDA TERC. | 5102 | S | S | S/N/I | N/N/O | Deb | — | N | 201 |
| 611 | VENDA MERCADORIA | 5102 | S | S | S/N/O | S/S/T | Deb | — | N | — |
| 612 | VENDA PROD. PROPRIA | 5101 | S | S | S/N/T | S/N/T | Deb | — | N | — |
| 621 | VENDA PRODUÇÃO | 5101 | N | S | S/S/T | S/S/T | Deb | — | N | 120 |
| 625 | VENDA COM ST | 5405 | N | S | N/N/O | N/N/O | — | — | N | — |
| 629 | VENDA DE PRODUCAO DO ESTABELECIMENTO | 5101 | N | S | S/S/T | S/S/T | Deb | — | N | — |
| 635 | COMPLEM. ICMS | 5101 | N | N | S/S/T | N/N/N | Deb | — | N | — |
| 636 | VENDA MERC. ADQ. RECEBIDA TERC. | 5102 | S | S | S/S/T | S/S/T | Deb | — | N | — |
| 639 | VENDA SUCATA | 5101 | S | S | S/N/O | N/N/O | Deb | — | N | — |
| 665 | VENDA SUCATA | 5101 | N | S | S/N/T | N/N/O | Deb | — | N | — |
| 670 | VENDA PROD. | 5101 | N | S | S/S/T | S/S/T | Deb | — | N | 120 |
| 700 | VENDAS (VENDAS  - FILIAL 02) | 5101 | S | S | S/S/T | S/S/T | Deb | — | N | 400 |
| 703 | VENDA SUCATA ES (VENDA SUCATA) | 5101 | N | S | N/N/O | N/N/O | Deb | — | N | 191 |
| 715 | VENDA PRODUÇÃO PROPI | 5101 | S | S | S/N/T | S/N/T | Deb | — | N | — |
| 758 | VENDA PRODUÇÃO (VENDA) | 5101 | N | S | S/S/T | S/S/T | Deb | — | N | 120 |

## Industrialização por encomenda (x124/x125) (saída)

Na entrada: industrialização feita por outra empresa para a Delpi. Na saída: industrialização que a Delpi fez para outra empresa (cobrança do serviço e dos insumos aplicados). A TES 510 é o item que carrega o custo; o par de faturamento da industrialização é a TES 594 (família Vendas).

- Ativas: 8 TES; 5 atualizam estoque, 8 geram duplicata, 5 creditam ICMS.
- Bloqueadas: 5 TES.
- Códigos ativos: 510, 511, 622, 661, 671, 673, 756, 757.

### Industrialização por encomenda (x124/x125) — TES de saída ativas

| TES | Descrição | CFOP | Estoque | Duplicata | ICMS calc/créd/livro | IPI calc/créd/livro | PIS/COFINS | Poder 3º | Consumo | TES devol. |
|---|---|---|---|---|---|---|---|---|---|---|
| 510 | INDUSTRIALIZACAO EFET. P/ OUTRA EMPRESA | 5124 | S | S | S/N/O | N/N/O | Deb | — | N | — |
| 511 | INDUSTRIALIZACAO EFET. P/ OUTRA EMPRESA | 5124 | N | S | S/N/O | N/N/O | Deb | — | N | 312 |
| 622 | INDUSTRIALIZACAO EFET. P/ OUTRA EMPRESA | 5124 | S | S | S/N/O | N/N/O | Deb | — | N | 168 |
| 661 | INDUSTRIALIZACAO EFET. INSUMOS | 5124 | S | S | S/S/T | N/N/O | Deb | — | N | — |
| 671 | INDUSTRIALIZACAO EFET. INSUMOS | 5124 | N | S | S/S/T | N/N/O | Deb | — | N | — |
| 673 | INDUSTRIALIZACAO EFET. P/ OUTRA EMPRESA | 5124 | S | S | S/S/T | N/N/O | Deb | — | N | — |
| 756 | INDUSTRIALIZACAO EFET. INSUMOS | 5124 | N | S | S/S/T | S/S/T | Deb | — | N | — |
| 757 | INDUSTRIALIZACAO EFET. INSUMOS | 5124 | S | S | S/S/T | S/S/T | Deb | — | N | — |

### Industrialização por encomenda (x124/x125) — TES de saída bloqueadas

| TES | Descrição | CFOP | Estoque | Duplicata | ICMS calc/créd/livro | IPI calc/créd/livro | PIS/COFINS | Poder 3º | Consumo | TES devol. |
|---|---|---|---|---|---|---|---|---|---|---|
| 512 | INDUST. P/OUTRA EMPR | 6124 | N | S | S/S/T | N/N/O | Deb | — | N | 164 |
| 610 | INDUSTRIALIZACAO EFET. INSUMOS | 5124 | N | S | S/S/T | N/N/O | Deb | — | N | — |
| 656 | INDUSTRIALIZACAO EFET. INSUMOS | 5124 | S | S | S/S/T | N/S/T | Deb | — | N | — |
| 669 | IND.EFET.P/OUTRA EMP | 5124 | S | S | S/N/O | N/N/O | Deb | — | N | — |
| 712 | INDUST.TERCEIRO ES | 5124 | N | S | S/N/T | N/N/O | Deb | — | N | — |

## Remessa e retorno para industrialização (saída)

Material que vai ou volta de industrialização (CFOP x901, x902, x903). Em regra não geram duplicata e boa parte controla poder de terceiros (Remessa = o material sai ou entra sem mudar de dono; Devolução = retorno desse material). As TES 080, 085 e 159 ficam fora da apuração de despesas do R10.

- Ativas: 8 TES; 3 atualizam estoque, 0 geram duplicata, 0 creditam ICMS, 6 controlam poder de terceiros.
- Bloqueadas: 9 TES.
- Códigos ativos: 519, 522, 524, 525, 528, 534, 539, 613.

### Remessa e retorno para industrialização — TES de saída ativas

| TES | Descrição | CFOP | Estoque | Duplicata | ICMS calc/créd/livro | IPI calc/créd/livro | PIS/COFINS | Poder 3º | Consumo | TES devol. |
|---|---|---|---|---|---|---|---|---|---|---|
| 519 | REMESSSA P/ INDUSTRIALIZACAO POR ENCOM. | 5901 | S | N | S/N/O | N/N/O | — | R | N | 122 |
| 522 | RETORNO DE MERC. UTILIZADA NA IND. | 5902 | S | N | S/N/O | N/N/O | — | D | N | — |
| 524 | RETORNO MERC. RECEB. P/ IND. NAO APLICAD | 5903 | S | N | S/N/O | N/N/O | — | D | N | 085 |
| 525 | RETORNO DE MERC. UTILIZADA NA IND. | 5902 | N | N | S/N/O | N/N/O | — | D | N | 085 |
| 528 | RETORNO MERC. RECEB. P/ IND. NAO APLICAD | 5903 | N | N | S/N/O | N/N/O | — | — | N | — |
| 534 | RETORNO MERC. RECEB. P/ IND. NAO APLICAD | 5903 | N | N | S/N/O | N/N/O | — | D | N | 085 |
| 539 | RETORNO DE MERC. UTILIZADA NA IND. | 5902 | N | N | S/N/O | N/N/O | — | — | N | — |
| 613 | REMESSA INDUSTRIALIZ | 5901 | N | N | S/N/O | N/N/O | — | R | N | 081 |

### Remessa e retorno para industrialização — TES de saída bloqueadas

| TES | Descrição | CFOP | Estoque | Duplicata | ICMS calc/créd/livro | IPI calc/créd/livro | PIS/COFINS | Poder 3º | Consumo | TES devol. |
|---|---|---|---|---|---|---|---|---|---|---|
| 520 | RET.MERC.INDUSTRIAL. | 5902 | S | N | N/N/O | S/S/O | — | — | N | — |
| 521 | RET.MERC.INDUS. | 5902 | S | N | N/N/O | N/N/O | — | R | N | — |
| 531 | RETORNO SEM IND. | 5903 | S | N | N/N/O | N/N/O | — | D | N | — |
| 546 | REM.P/ CONTA ORDEM | 5924 | N | N | N/N/O | N/N/O | — | — | N | — |
| 570 | RET.MERC.INDUS. | 5902 | S | N | N/N/O | N/N/O | — | D | N | — |
| 605 | RET.MERC.IND. | 5902 | S | N | N/N/O | N/N/O | — | D | N | — |
| 631 | RETORNO MERC.INDUSTR (RETORNO MERCADORIA INDUSTRIALIZACAO) | 5902 | N | N | N/N/O | N/N/O | — | — | N | 085 |
| 642 | REMESSA INDUSTRIALIZ | 5901 | N | N | N/N/O | N/N/O | — | — | N | 159 |
| 646 | REMESSSA P/ INDUSTRI | 5901 | S | N | N/N/O | N/N/O | — | — | N | — |

## Devolução de compra (saída)

Saída da mercadoria comprada que a Delpi devolve ao fornecedor (CFOP x201, x202, x410, x411, x556). No R05 entram como devolução de compra (tipo de nota D). Exemplos: 530 e 561 devolvem compras feitas nas TES 001 e 003.

- Ativas: 10 TES; 5 atualizam estoque, 10 geram duplicata, 5 creditam ICMS.
- Bloqueadas: 18 TES.
- Códigos ativos: 529, 530, 547, 554, 561, 580, 588, 617, 649, 650.

### Devolução de compra — TES de saída ativas

| TES | Descrição | CFOP | Estoque | Duplicata | ICMS calc/créd/livro | IPI calc/créd/livro | PIS/COFINS | Poder 3º | Consumo | TES devol. |
|---|---|---|---|---|---|---|---|---|---|---|
| 529 | DEVOL. DE COMPRA DE USO OU CONSUMO SN | 5556 | S | S | S/N/O | N/N/O | — | — | N | — |
| 530 | DEVOL. DE COMPRA PARA INDUSTRIALIZACAO | 5201 | S | S | S/S/T | S/S/T | Deb | — | N | 404 |
| 547 | DEVOLUCAO DE ATIVO IMOBILIZADO SN | 6553 | N | S | S/N/O | N/N/O | — | — | N | 153 |
| 554 | DEVOL. DE COMPRA PARA IND. SN | 5201 | S | S | S/N/O | N/N/O | Deb | — | N | 004 |
| 561 | DEVOL. DE COMPRA PARA INDUSTRIALIZACAO | 6201 | S | S | S/S/T | N/N/O | Deb | — | N | 003 |
| 580 | DEVOL. DE COMPRA PARA INDUSTRIALIZACAO | 6201 | N | S | S/S/T | N/N/O | Deb | — | N | — |
| 588 | DEVOLUCAO DE ATIVO IMOBILIZADO | 6553 | N | S | S/S/T | N/N/O | — | — | N | 182 |
| 617 | DEVOL. DE COMPRA DE USO OU CONSUMO (DEV. CONSUMO IPI NA BASE) | 6556 | S | S | S/S/T | N/N/O | Cred | — | N | — |
| 649 | DEVOL. DE COMPRA DE USO OU CONSUMO (5556 DEVOLUCAO USO/CONSUMO C/ICMS REDUCAO) | 5556 | N | S | S/N/T | N/N/O | — | — | N | 166 |
| 650 | DEVOL. DE COMPRA DE USO OU CONSUMO SN (5556 DEVOLUCAO USO/CONSUMO C/ICMS) | 5556 | N | S | S/N/O | N/N/O | — | — | N | — |

### Devolução de compra — TES de saída bloqueadas

| TES | Descrição | CFOP | Estoque | Duplicata | ICMS calc/créd/livro | IPI calc/créd/livro | PIS/COFINS | Poder 3º | Consumo | TES devol. |
|---|---|---|---|---|---|---|---|---|---|---|
| 514 | DEVOLU. S/IPI | 5201 | S | N | S/S/T | N/N/O | Cred | — | N | — |
| 544 | DEVOLUÇÃO | 5201 | N | N | S/S/T | N/N/O | Cred | — | N | — |
| 559 | DEV.CONS. C/IPI C/ST (DEV.COMPRA MAT.CONSUMO C/ST E C/IPI) | 5413 | S | S | N/N/N | S/N/O | — | — | N | — |
| 560 | DEV. DE COMPRA | 6201 | S | S | S/S/T | S/S/T | Cred | — | N | — |
| 562 | DEVOLUÇÃO COMPRAS | 5201 | N | N | S/S/T | S/S/T | Cred | — | N | — |
| 563 | DEVOL. VENDAS | 5201 | N | S | S/S/T | S/S/T | Deb | — | N | — |
| 569 | DEV. COMPRA MP | 6201 | S | N | S/N/T | N/N/O | Cred | — | N | — |
| 574 | DEV.CONS. S/IPI C/ST | 5413 | S | S | N/N/O | N/N/N | — | — | N | — |
| 593 | DEVOL. DE COMPRAS | 5201 | N | S | S/N/T | S/N/T | Deb | — | N | — |
| 608 | DEVOLUÇÃO CONSUMO | 5556 | S | N | S/S/T | S/S/T | — | — | N | 052 |
| 620 | DEV. CONSUMO ST | 5413 | S | S | N/N/O | N/N/O | — | — | N | 142 |
| 623 | COMPLE. ICMS CONSUMO | 5556 | N | N | S/S/T | N/N/N | — | — | N | — |
| 630 | DEV. MAT PRIMA ST | 5410 | S | S | N/N/O | N/N/O | — | — | N | — |
| 652 | DEVOL CONSUMO ST | 5413 | N | S | N/N/O | N/N/O | — | — | N | — |
| 653 | DEVOLUÇÃO DE COMPRA | 6201 | N | N | S/N/T | S/N/O | Cred | — | N | — |
| 654 | DEV. COMPRAS COFINS | 6201 | S | N | S/N/T | S/N/T | Cred | — | N | — |
| 711 | DEVOLUÇÃO CONSUMO | 5556 | S | S | S/N/O | N/N/O | — | — | N | — |
| 753 | DEVOL. DE COMPRA PARA INDUSTRIALIZACAO | 5201 | S | S | S/N/O | N/N/O | Deb | — | N | 004 |

## Transferências entre filiais (saída)

Transferência de produção, mercadoria ou insumo entre estabelecimentos da Delpi (CFOP x151, x152, x408, x409). Não geram duplicata. A TES 204 (transferência de matéria-prima) fica fora da apuração de despesas do R10.

- Ativas: 3 TES; 2 atualizam estoque, 0 geram duplicata, 2 creditam ICMS.
- Bloqueadas: 3 TES.
- Códigos ativos: 590, 627, 704.

### Transferências entre filiais — TES de saída ativas

| TES | Descrição | CFOP | Estoque | Duplicata | ICMS calc/créd/livro | IPI calc/créd/livro | PIS/COFINS | Poder 3º | Consumo | TES devol. |
|---|---|---|---|---|---|---|---|---|---|---|
| 590 | TRANSFERENCIA DE PRODUCAO DO ESTAB. | 6151 | S | N | S/N/T | N/N/O | — | — | N | — |
| 627 | TRANSFERENCIA DE PRODUCAO DO ESTAB. | 6151 | S | N | S/S/T | N/N/O | — | — | N | — |
| 704 | TRANSFERENCIA DE PRODUCAO DO ESTAB. (TRANSFERENCIA MP) | 6151 | N | N | S/S/T | N/N/O | — | — | N | — |

### Transferências entre filiais — TES de saída bloqueadas

| TES | Descrição | CFOP | Estoque | Duplicata | ICMS calc/créd/livro | IPI calc/créd/livro | PIS/COFINS | Poder 3º | Consumo | TES devol. |
|---|---|---|---|---|---|---|---|---|---|---|
| 584 | TRANSF MERC ADQ | 5152 | N | N | S/N/O | N/N/O | — | — | N | — |
| 638 | TRANSF. MP FILIAIS | 6151 | S | N | S/S/T | S/S/T | — | — | N | — |
| 713 | TRANSF. MP | 6151 | N | N | S/S/T | S/S/T | — | — | N | — |

## Uso e consumo (saída)

Material de uso e consumo (CFOP x556, x557, x407). Na regra geral não dão crédito de ICMS. Material de consumo com crédito de IPI é ponto de atenção da auditoria de entradas (regra «Crédito de IPI em material de uso e consumo»).

- Ativas: 4 TES; 2 atualizam estoque, 0 geram duplicata, 0 creditam ICMS.
- Bloqueadas: nenhuma.
- Códigos ativos: 589, 597, 628, 657.

### Uso e consumo — TES de saída ativas

| TES | Descrição | CFOP | Estoque | Duplicata | ICMS calc/créd/livro | IPI calc/créd/livro | PIS/COFINS | Poder 3º | Consumo | TES devol. |
|---|---|---|---|---|---|---|---|---|---|---|
| 589 | TRANSFERENCIA DE USO OU CONSUMO | 6557 | S | N | S/N/O | N/N/O | — | — | N | — |
| 597 | TRANSFERENCIA DE USO OU CONSUMO | 6557 | N | N | S/N/T | N/N/O | — | — | N | — |
| 628 | TRANSFERENCIA DE USO OU CONSUMO | 6557 | S | N | S/N/T | N/N/O | — | — | N | — |
| 657 | TRANSF INSUMOS CONSUMO | 5557 | N | N | S/N/T | N/N/O | — | — | N | — |

## Ativo imobilizado (saída)

Compra, remessa, retorno, venda e transferência de bens do ativo, e lançamento do crédito de ICMS do ativo (CIAP, CFOP x604). Não atualizam o ativo fixo pela TES no cadastro desta extração (Atual.Ativo? = Não em todas).

- Ativas: 3 TES; 0 atualizam estoque, 0 geram duplicata, 0 creditam ICMS.
- Bloqueadas: 4 TES.
- Códigos ativos: 555, 626, 701.

### Ativo imobilizado — TES de saída ativas

| TES | Descrição | CFOP | Estoque | Duplicata | ICMS calc/créd/livro | IPI calc/créd/livro | PIS/COFINS | Poder 3º | Consumo | TES devol. |
|---|---|---|---|---|---|---|---|---|---|---|
| 555 | VENDA DE ATIVO IMOBILIZADO | 5551 | N | N | S/N/I | N/N/O | — | — | N | — |
| 626 | TRANSFERENCIA DE ATIVO IMOBILIZADO | 6552 | N | N | S/N/O | N/N/O | — | — | N | — |
| 701 | TRANSFERENCIA BEM AT (TRANSFERENCIA ATIVO IMOBILIZADO) | 6552 | N | N | S/N/O | N/N/O | — | — | N | — |

### Ativo imobilizado — TES de saída bloqueadas

| TES | Descrição | CFOP | Estoque | Duplicata | ICMS calc/créd/livro | IPI calc/créd/livro | PIS/COFINS | Poder 3º | Consumo | TES devol. |
|---|---|---|---|---|---|---|---|---|---|---|
| 526 | REM  BEM ATIVO IMOBI | 5554 | N | N | S/N/I | N/N/I | — | — | N | — |
| 527 | RET. ATIVO IMOBILIZA | 5555 | N | N | S/N/I | N/N/O | — | D | N | — |
| 607 | VENDA ATIVO IMOBILIZ | 5551 | N | S | S/N/I | N/N/I | — | — | N | 182 |
| 751 | TRANSFERENCIA FILIAL | 6551 | S | N | S/N/T | S/N/T | — | — | N | — |

## Frete e transporte (saída)

Conhecimentos de transporte (CT-e) e anulação de frete (CFOP x352, x353, x206, x932). O crédito de ICMS do frete depende do que foi transportado: frete de venda ou de insumo dá direito; frete de consumo ou ativo não. A auditoria de entradas identifica frete pelo CFOP terminado em 352 e lê o crédito na TES (ficha AE-05). A TES 040 fica fora da apuração de despesas do R10.

- Ativas: nenhuma.
- Bloqueadas: 1 TES.
- Códigos ativos: —.

### Frete e transporte — TES de saída bloqueadas

| TES | Descrição | CFOP | Estoque | Duplicata | ICMS calc/créd/livro | IPI calc/créd/livro | PIS/COFINS | Poder 3º | Consumo | TES devol. |
|---|---|---|---|---|---|---|---|---|---|---|
| 651 | ESTORNO FRETE | 5206 | N | N | S/S/T | N/N/O | — | — | N | — |

## Conserto e reparo (saída)

Remessa e retorno de bens para conserto (CFOP x915/x916). Não geram duplicata.

- Ativas: 4 TES; 2 atualizam estoque, 1 geram duplicata, 0 creditam ICMS, 3 controlam poder de terceiros.
- Bloqueadas: 8 TES.
- Códigos ativos: 540, 541, 577, 755.

### Conserto e reparo — TES de saída ativas

| TES | Descrição | CFOP | Estoque | Duplicata | ICMS calc/créd/livro | IPI calc/créd/livro | PIS/COFINS | Poder 3º | Consumo | TES devol. |
|---|---|---|---|---|---|---|---|---|---|---|
| 540 | REMES. MERC. BEM P/ CONSERTO | 5915 | N | N | S/N/O | N/N/O | — | R | N | 094 |
| 541 | RETORNO DE MERCADORIA PARA CONSERTO | 5916 | S | N | S/N/O | N/N/O | — | D | N | — |
| 577 | RETORNO DE MERCADORIA PARA CONSERTO | 5916 | N | N | S/N/O | N/N/O | — | D | N | — |
| 755 | REMESSA PARA CONSERTO | 6915 | S | S | S/N/O | S/N/O | — | — | N | 262 |

### Conserto e reparo — TES de saída bloqueadas

| TES | Descrição | CFOP | Estoque | Duplicata | ICMS calc/créd/livro | IPI calc/créd/livro | PIS/COFINS | Poder 3º | Consumo | TES devol. |
|---|---|---|---|---|---|---|---|---|---|---|
| 518 | RETORNO DE MERCADORIA PARA CONSERTO | 5916 | N | N | S/N/O | N/N/O | — | — | N | 074 |
| 542 | REMESS P/CONSERTO | 5915 | S | N | S/N/O | N/N/O | — | R | N | 100 |
| 548 | RETORNO 3º | 5916 | N | N | S/N/O | N/N/O | — | D | N | — |
| 549 | RET. REM. P/ CONSERT | 5916 | S | N | S/N/O | N/N/O | — | D | N | 097 |
| 604 | REMESSA P/ CONSERTO | 6915 | N | N | S/N/O | N/N/O | — | R | N | 094 |
| 645 | REMESSA P/ CONSERTO | 6915 | N | N | N/N/O | N/N/O | — | — | N | — |
| 647 | REMESS P/CONSERTO | 5915 | S | N | N/N/I | N/N/I | — | — | N | — |
| 754 | SUBS EM GARANTIA | 6915 | S | S | S/S/T | S/S/T | — | — | N | — |

## Vasilhame e embalagem retornável (saída)

Vasilhame e embalagem retornável (CFOP x920/x921) — na Delpi, os carretéis dos cabos. A TES 083 fica fora da apuração de despesas do R10.

- Ativas: 2 TES; 0 atualizam estoque, 0 geram duplicata, 0 creditam ICMS, 2 controlam poder de terceiros.
- Bloqueadas: 4 TES.
- Códigos ativos: 550, 624.

### Vasilhame e embalagem retornável — TES de saída ativas

| TES | Descrição | CFOP | Estoque | Duplicata | ICMS calc/créd/livro | IPI calc/créd/livro | PIS/COFINS | Poder 3º | Consumo | TES devol. |
|---|---|---|---|---|---|---|---|---|---|---|
| 550 | DEVOL. VASILHAME OU SACARIA | 5921 | N | N | S/N/I | N/N/O | — | D | N | 083 |
| 624 | REMESSA DE VASILHAME | 5920 | N | N | N/N/O | N/N/O | — | R | N | — |

### Vasilhame e embalagem retornável — TES de saída bloqueadas

| TES | Descrição | CFOP | Estoque | Duplicata | ICMS calc/créd/livro | IPI calc/créd/livro | PIS/COFINS | Poder 3º | Consumo | TES devol. |
|---|---|---|---|---|---|---|---|---|---|---|
| 533 | DEVOLUCAO DE VASILHA | 5921 | N | N | S/N/I | N/N/O | — | — | N | — |
| 648 | REMESSA VASILHAME | 5920 | N | N | N/N/O | N/N/O | — | — | N | — |
| 668 | REMESSA VASILHAME | 5920 | S | N | N/N/I | N/N/N | — | R | N | — |
| 752 | DEVOLUÇÃO VASILHAME | 5921 | N | N | N/N/O | N/N/O | — | D | N | — |

## Bonificação, amostra, demonstração, consignação e comodato (saída)

Bonificação (x910), amostra grátis (x911), demonstração (x912/x913), consignação (x917–x919) e comodato (x908/x909). Em regra não geram duplicata.

- Ativas: 13 TES; 6 atualizam estoque, 0 geram duplicata, 1 creditam ICMS, 4 controlam poder de terceiros.
- Bloqueadas: 17 TES.
- Códigos ativos: 535, 536, 551, 558, 567, 572, 576, 579, 581, 583, 585, 592, 658.

### Bonificação, amostra, demonstração, consignação e comodato — TES de saída ativas

| TES | Descrição | CFOP | Estoque | Duplicata | ICMS calc/créd/livro | IPI calc/créd/livro | PIS/COFINS | Poder 3º | Consumo | TES devol. |
|---|---|---|---|---|---|---|---|---|---|---|
| 535 | RETORNO DE MERC. REC. DEMONSTRACAO | 6913 | N | N | S/N/O | S/S/O | — | D | N | 095 |
| 536 | RETORNO DE MERC. REC. DEMONSTRACAO | 5913 | S | N | S/N/O | S/S/O | — | D | N | — |
| 551 | AMOSTRA GRATIS | 5911 | S | N | S/N/I | N/N/O | — | — | N | — |
| 558 | RETORNO DE MERC. REC. DEMONSTRACAO | 5913 | N | N | S/N/O | N/N/O | — | D | N | — |
| 567 | BONIFICAÇÃO | 6910 | S | N | S/S/T | S/S/T | — | — | N | 035 |
| 572 | REMESSA AMOSTRA ZF | 5911 | N | N | S/N/I | N/N/O | — | — | N | — |
| 576 | REMESSA PARA DEMONSTRAÇÃO | 5912 | N | N | S/N/O | S/S/T | — | — | N | 188 |
| 579 | RETORNO DE MERC. REC. DEMONSTRACAO | 5913 | S | N | S/N/O | N/N/O | — | — | N | — |
| 581 | REMESSA PARA DEMONSTRAÇÃO | 5912 | N | N | S/N/O | N/N/O | — | — | N | 200 |
| 583 | REMESSA PARA DEMONSTRAÇÃO | 5912 | S | N | S/N/O | N/N/O | — | — | N | 188 |
| 585 | RET DEMONSTRACAO | 5913 | S | N | S/N/O | S/S/T | — | — | N | 194 |
| 592 | AMOSTRA GRATIS | 5911 | N | N | S/N/I | N/N/O | — | — | N | — |
| 658 | REMESSA EM COMODATO | 5908 | N | N | S/N/O | N/N/O | — | R | N | — |

### Bonificação, amostra, demonstração, consignação e comodato — TES de saída bloqueadas

| TES | Descrição | CFOP | Estoque | Duplicata | ICMS calc/créd/livro | IPI calc/créd/livro | PIS/COFINS | Poder 3º | Consumo | TES devol. |
|---|---|---|---|---|---|---|---|---|---|---|
| 537 | DEV. DEMONST. | 6913 | N | N | S/S/T | N/N/O | — | — | N | — |
| 543 | DEV. DEMONST | 5913 | N | N | S/N/O | N/N/O | — | — | N | 068 |
| 552 | AMOSTRA | 5911 | N | N | S/S/T | S/S/T | — | — | N | 089 |
| 553 | AMOSTRA GRATIS | 5911 | S | N | S/S/T | N/N/O | — | — | N | — |
| 557 | REMESSA AMOSTRA | 5911 | N | N | S/S/T | N/N/O | — | — | N | — |
| 578 | RET DEMONSTRACAO | 5913 | N | N | N/N/O | S/S/O | — | — | N | 173 |
| 586 | RETORNO DE DEMONSTRA | 5913 | S | N | S/N/O | S/S/T | — | — | N | 578 |
| 587 | BONIFICAÇÃO PROD | 1910 | S | N | S/S/T | S/S/T | — | — | N | — |
| 603 | REM MERC CONSIGNACAO | 5917 | S | N | S/S/T | S/S/T | — | — | N | — |
| 632 | DEVOL. DEMOSNTRAÇÃO (DEVOL DEMONSTRAÇÃO  RED BASE ICMS 78,58%) | 6913 | N | N | S/N/O | N/N/O | — | — | N | — |
| 637 | RET REM DEMONSTRAÇÃO | 5913 | N | N | S/S/T | N/N/O | — | R | N | — |
| 640 | RETORNO DEMONSTRAÇÃO | 5913 | S | N | S/N/T | N/N/O | — | — | N | — |
| 641 | RETORNO REM COMODATO | 5909 | N | N | N/N/O | N/N/O | — | D | N | 178 |
| 643 | DEV. DEMONST. | 5913 | S | N | S/S/T | N/N/O | — | D | N | — |
| 644 | DEV. DEMONST. | 6913 | N | N | S/S/T | N/N/O | — | D | N | — |
| 655 | DEVOLUÇÃO DEMONSTRAÇ | 5913 | S | N | N/N/I | S/N/T | — | D | N | 087 |
| 664 | DEVOLUÇÃO DEMONSTRAÇ | 5913 | N | N | S/N/O | S/S/O | — | — | N | — |

## Baixa de estoque e perdas (saída)

Baixa de estoque por perda, roubo ou deterioração (CFOP x927). Tiram do estoque sem gerar duplicata.

- Ativas: 1 TES; 1 atualizam estoque, 0 geram duplicata, 0 creditam ICMS.
- Bloqueadas: 2 TES.
- Códigos ativos: 714.

### Baixa de estoque e perdas — TES de saída ativas

| TES | Descrição | CFOP | Estoque | Duplicata | ICMS calc/créd/livro | IPI calc/créd/livro | PIS/COFINS | Poder 3º | Consumo | TES devol. |
|---|---|---|---|---|---|---|---|---|---|---|
| 714 | BAIXA ESTOQUE PERDA (BAIXA ESTOQUE) | 5927 | S | N | S/N/O | N/N/O | — | — | N | — |

### Baixa de estoque e perdas — TES de saída bloqueadas

| TES | Descrição | CFOP | Estoque | Duplicata | ICMS calc/créd/livro | IPI calc/créd/livro | PIS/COFINS | Poder 3º | Consumo | TES devol. |
|---|---|---|---|---|---|---|---|---|---|---|
| 710 | BAIXA ESTOQUE PERDA (BAIXA DE ESTOQUE) | 5927 | S | N | S/N/T | N/N/O | — | — | N | — |
| 717 | BAIXA ESTOQUE PERDA (BAIXA ESTOQUE) | 5927 | S | N | N/N/N | S/S/O | — | — | N | — |

## Outras operações e estornos (saída)

Outras entradas e saídas não especificadas (CFOP x949), estornos e ajustes. Descrição genérica: confira a finalidade da nota antes de concluir qualquer efeito.

- Ativas: 11 TES; 6 atualizam estoque, 2 geram duplicata, 9 creditam ICMS, 1 controlam poder de terceiros.
- Bloqueadas: 12 TES.
- Códigos ativos: 564, 568, 571, 595, 600, 601, 602, 616, 633, 634, 672.

### Outras operações e estornos — TES de saída ativas

| TES | Descrição | CFOP | Estoque | Duplicata | ICMS calc/créd/livro | IPI calc/créd/livro | PIS/COFINS | Poder 3º | Consumo | TES devol. |
|---|---|---|---|---|---|---|---|---|---|---|
| 564 | OUTRAS SAIDAS | 6949 | S | N | S/S/T | S/S/T | — | — | N | — |
| 568 | OUTRAS SAIDAS | 5949 | N | N | N/N/O | S/S/O | — | D | N | — |
| 571 | OUTRAS SAIDAS | 5949 | N | N | S/S/T | N/N/O | — | — | N | 164 |
| 595 | OUTRA SAIDAS RED BASE CALC | 5949 | N | S | S/S/O | N/N/O | Deb | — | N | — |
| 600 | OUTRAS SAIDAS | 5949 | S | N | S/S/T | S/S/T | — | — | N | 110 |
| 601 | OUTRAS SAIDAS | 5949 | N | N | S/S/T | S/S/T | — | — | N | 110 |
| 602 | OUTRAS SAIDAS | 6949 | S | N | S/S/T | S/S/T | — | — | N | 113 |
| 616 | OUTRAS SAIDAS ENVIO PARA TESTE | 5949 | S | N | S/S/T | N/N/N | — | — | N | 172 |
| 633 | OUTRAS SAIDAS | 5949 | S | N | S/S/T | S/S/T | — | — | N | — |
| 634 | OUTRAS SAIDAS | 5949 | N | N | S/S/T | S/S/T | — | — | N | — |
| 672 | OUTRAS SAIDAS ZFM | 6949 | S | S | S/N/I | N/N/O | — | — | N | 181 |

### Outras operações e estornos — TES de saída bloqueadas

| TES | Descrição | CFOP | Estoque | Duplicata | ICMS calc/créd/livro | IPI calc/créd/livro | PIS/COFINS | Poder 3º | Consumo | TES devol. |
|---|---|---|---|---|---|---|---|---|---|---|
| 532 | OUTRAS SAIDAS | 5949 | N | N | N/N/O | N/N/O | — | D | N | — |
| 575 | OUTRAS SAIDAS | 5949 | N | N | S/N/O | S/N/O | — | — | N | 110 |
| 582 | DEV. CARRETEL | 5949 | N | N | S/N/O | N/N/O | — | D | N | — |
| 596 | OUTRAS SAIDAS | 5949 | N | S | S/S/T | S/S/T | Deb | — | N | — |
| 615 | OUTRAS SAIDAS | 5949 | N | N | N/N/O | N/N/O | — | — | N | 139 |
| 618 | OUTRA SAIDA | 6949 | N | N | S/N/I | N/N/O | — | — | N | 112 |
| 660 | OUTRAS ENT. N ESPECI | 2949 | N | S | N/N/O | N/N/O | — | — | N | — |
| 702 | REMESSA RESÍDUO | 5949 | N | N | S/N/O | N/N/O | — | — | N | — |
| 759 | OUTRAS SAIDAS | 5949 | N | N | S/S/O | N/N/O | — | R | N | 100 |
| 760 | OUTRAS SAIDAS | 5949 | N | N | S/N/O | N/N/O | — | R | N | 100 |
| 761 | OUTRAS SAIDAS | 5949 | N | N | S/N/O | N/N/O | — | R | N | — |
| 762 | OUTRAS SAIDAS | 5949 | N | N | S/N/O | N/N/O | — | R | N | — |

## Governança

- Owner do cadastro: Controladoria e equipe fiscal. A CLARA não cria, edita nem bloqueia TES.
- Bloqueada (`F4_MSBLQL`) = não pode ser usada em nota nova. Nota antiga pode ter TES hoje bloqueada: isso é normal e não é erro.
- Configuração estranha no cadastro é ponto a verificar com o fiscal, nunca erro confirmado (ficha TES-02).
- Atualização: gerar CSV novo da SF4, rodar `fonte/gerar_catalogo_tes.py`, revisar o diff e republicar o corpus.
