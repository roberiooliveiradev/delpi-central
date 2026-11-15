# TES-02 — Padrões das TES na Delpi

Versão da ficha: 1.0 · 14/11/2026.

## Identificação

- Código: **TES-02** — como o cadastro de TES da Delpi está organizado e quais pontos merecem atenção.
- Implementação: **IMPLEMENTED** (conhecimento citável).
- Fonte: extração da SF4 de 09/11/2026 fornecida pela Controladoria (OWNER_REPORTED_VIA_PO). Os números abaixo são contagens dessa extração (PROVEN para aquela data).
- O que está aqui é fato do cadastro. Interpretação de negócio só onde a ficha diz de onde veio.

## Números do cadastro

| Item | Entrada | Saída | Total |
|---|---|---|---|
| Faixa de códigos | 001–416 e 3A8 | 501–764 | — |
| TES cadastradas | 252 | 206 | 458 |
| Ativas | 141 | 93 | 234 |
| Bloqueadas | 111 | 113 | 224 |
| Ativas que movimentam estoque | 70 | 52 | 122 |
| Ativas que geram duplicata | 64 | 41 | 105 |

## Famílias

- Famílias pela natureza do CFOP (três últimos dígitos). Contagem ativas / bloqueadas.

| Família | Entrada | Saída |
|---|---|---|
| Compras de insumo, matéria-prima e revenda | 11 / 17 | — |
| Vendas | — | 16 / 29 |
| Importação / Exportação | 12 / 0 | 10 / 1 |
| Industrialização por encomenda (x124/x125) | 4 / 4 | 8 / 5 |
| Remessa e retorno para industrialização | 10 / 7 | 8 / 9 |
| Devolução de venda / Devolução de compra | 8 / 5 | 10 / 18 |
| Transferências entre filiais | 4 / 1 | 3 / 3 |
| Uso e consumo | 19 / 23 | 4 / 0 |
| Combustíveis e lubrificantes | 4 / 0 | — |
| Ativo imobilizado | 7 / 10 | 3 / 4 |
| Energia elétrica | 3 / 0 | — |
| Comunicação | 2 / 0 | — |
| Frete e transporte | 8 / 1 | 0 / 1 |
| Serviços tomados | 3 / 13 | — |
| Conserto e reparo | 5 / 6 | 4 / 8 |
| Vasilhame e embalagem retornável (carretéis) | 2 / 2 | 2 / 4 |
| Bonificação, amostra, demonstração, consignação e comodato | 22 / 12 | 13 / 17 |
| Entrega futura e conta e ordem | 1 / 0 | — |
| Baixa de estoque e perdas | — | 1 / 2 |
| Outras operações e estornos | 16 / 10 | 11 / 12 |

## Padrões de uso

- **Compra de matéria-prima**: 001 (com ICMS e IPI), 003 (sem IPI), 004 (fornecedor do Simples Nacional — é a TES do crédito presumido de 7% de SC na auditoria), 002 (fornecedor MEI, sem crédito de ICMS). Devolução sugerida: 001 → 530, 003 → 561, 004 → 554.
- **Venda de produção**: 29 TES usam o CFOP 5101 (11 ativas); ativas com estoque: 501, 609, 614, 663, 706, 707, 708. A 614 é devolvida pela 120.
- **Industrialização para terceiros**: o par **510** (custo, CFOP 5124, com estoque) + **594** (faturamento, CFOP 5101, sem estoque). A 594 é devolvida pela 127 (devolução de venda sem estoque).
- **Devolução de venda**: 120 (com estoque, padrão) e 127 (sem estoque, par da 594).
- **Transferência de produção entre filiais**: 590, 627 (com estoque) e 704 (sem estoque), CFOP 6151.
- **Frete (CT-e), ativas**:
  - creditam ICMS: 040 (AQUIS. SERV.TRANSP.), 148 (AQUIS. TRANSP VENDA), 158 (AQUISIÇÃO SERV TRANS);
  - não creditam: 025 (frete s/ manutenção de máquina), 026 (frete ativo), 042 (transporte consumo), 165 (frete Simples Nacional), 180 (aquis. transporte).
  - A 036 (FRETE S/ VENDAS) está bloqueada.
- **Carretéis**: a família de vasilhame cobre a embalagem retornável dos cabos (ex.: 582 «DEV. CARRETEL»).
- **Descrições repetidas**: 16 TES de saída se chamam «OUTRAS SAIDAS» e 9 se chamam «VENDA DE PRODUCAO DO ESTABELECIMENTO». Identifique sempre pelo código, nunca pela descrição.

## Pontos de atenção do cadastro

Fatos da extração de 09/11/2026. São pontos a verificar com o fiscal, não erros confirmados.

| # | Ponto | TES ativas | Por que importa |
|---|---|---|---|
| A1 | Material de consumo que credita IPI | 017, 052, 106, 169, 184, 406 | A auditoria de entradas aponta «Crédito de IPI em material de uso e consumo» (Alta) quando item com IPI passa por elas |
| A2 | Entrada com crédito de ICMS e livro fiscal desencontrados | 093, 117, 198, 312, 317, 413, 414, 415 | Sem o livro fiscal (SFT), a auditoria fica em «Depende da TES» para essas TES |
| A3 | Mesmo CFOP com e sem baixa de estoque | 5101: 505, 594, 619, 716 sem estoque; 5124: 511, 671, 756 sem estoque | Itens nessas TES entram no CPV com custo zero (ficha TES-01) |
| A4 | Frete que movimenta estoque | 040, 042, 158, 180 | Significado no custo é TO_INVENTORY |
| A5 | Campo de bloqueio vazio | 33 TES (001, 003, 004, 020, 030, 040, 120, 501…) | Vazio = não bloqueada |
| A6 | Código alfanumérico | 3A8 (ENT.IMPORTACAO DIRET, CFOP 3101) | Filtro numérico por faixa pode deixá-la de fora |

## Governança

- Owner: Controladoria e equipe fiscal. Correção de cadastro é feita no Protheus por quem tem acesso; a CLARA só aponta.
- Contagens valem para a extração de 09/11/2026. Ao atualizar a extração, refazer as contagens (`fonte/gerar_catalogo_tes.py --resumo`).
