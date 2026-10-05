# 04 — Regras de Negócio Consolidadas

## GAP-RULE-01 — SD1 / Centro de Custo

**Estado:** CLOSED_AT_REPORT_LEVEL / PARTIAL_AUTOMATION.

Campos funcionais confirmados:
- competência: `DT Digitação`;
- filtro visual: `Tipo Entrada`;
- `Cod. F` é campo distinto com códigos fiscais de 4 dígitos;
- `Tipo Produto` identifica MP;
- CC original: `C Custo`;
- analítico: `Classificação / Tipo Despesa`.

Valores aceitos na fatia validada:
`001, 003, 016, 018, 019, 020, 028, 030, 080, 083, 085, 204, 318`.

A lista executável completa continua PARTIAL.

Não inferir campos físicos D1*/B1*.

02xx/03xx/04xx = padrão/heurística, não classificador determinístico.

0407/0413 = casos reais; tratamento caso a caso. Não existe target CC universal provado.

Coparticipação pode ficar sem CC conforme natureza/descrição; fornecedor sozinho é insuficiente.

Owner da autoridade de CC: gestor/solicitante.

## GAP-RULE-02 — Kardex 01 / CPV

**Estado:** DETERMINISTIC no nível do relatório.

- Kardex Físico-Financeiro/Estoque;
- armazém 01;
- período da competência;
- filtro `C.F.`;
- valores aceitos: 5101, 6101, 6124;
- TES é distinto;
- totalização `SAIDAS CUST`;
- cálculo por unidade.

Acompanha Custos = pré-requisito PROVEN.

Fechamento do faturamento é necessário para valor final.

Custo Reposição/Refaz Saldos não são pré-requisitos estritos comprovados.

Residual ~R$3,80/R$4,00 = caso específico, não tolerância.

Destino: Fiscal.

## GAP-RULE-03 — Kardex 99 / Inventário

**Estado:** CLOSED_AT_BUSINESS_RULE_LEVEL / INFORMED.

- armazém 99;
- INVENT/INVENTE;
- entradas = sobra/ganho;
- saídas = falta/perda;
- líquido = Entradas Custo - Saídas Custo.

Exemplo ~-R$57 mil não é target.

Acompanha Custos = dependência forte.

Destino: Contábil.

## GAP-RULE-04 — Faturamento × MOD

**Estado:** DETERMINISTIC.

Relatório `Kardex e Faturamento por MOD`.

Campos: Produto, Descrição, Nota, Quantidade, Centro de Trabalho, Valor MOD/Mão de Obra, Valor Total.

Regra:
- considerar linhas válidas de produtos faturados;
- ignorar headers/subtotais;
- `SUM(Valor MOD)` por unidade.

Sem filtro PROVEN `Valor MOD > 0`.

MOD = mão de obra incorporada/faturada no produto, não folha.

Separar de custo-hora anual/PROC-0010.

Destino: Contábil.

## GAP-RULE-05 — Conciliação tripla

Exemplo:
- Entradas/Saídas = R$ 3.890.247,18
- P7 = R$ 3.776.994,69
- H02 = R$ 64.591,71

```text
Divergência = Entradas/Saídas - P7 - H02
```

Calculado: R$ 48.660,78. Verbal: R$ 48.660,77.

Diferença R$0,01 = UNKNOWN_CAUSE.

Não inventar hidden decimals/transcription.

Target final = zero / "fechar na vírgula".

R$0,25 em Insumos = caso específico, não tolerância.

Investigação: `total → grupo → item/evidência`.

## GAP-RULE-06 — Cutoff / revalidação / sacramentação

Cutoff = fim dos movimentos que ainda podem alterar estoque/faturamento.

~18h é referência prática, não regra fixa.

Estados:

```text
PRELIMINARY
→ WAITING_FOR_CUTOFF
→ REVALIDATION_REQUIRED
→ READY_TO_CLOSE
→ STOCK_CLOSED
```

Pós-cutoff:
- P7;
- Entradas/Saídas;
- H02;
- conciliação tripla.

`READY_TO_CLOSE = cutoff + revalidação aplicável + divergência zero`.

MATA280 = INFORMED / INFERRED / TO_INVENTORY.

## GAP-RULE-07 — Pacote / completude

Processo inicia no primeiro dia e termina após envio + esclarecimentos.

XML/SPED não deve virar upload obrigatório sem mudança formal.

Dennis = dependência específica XP.

Estados:

```text
PACKAGE_INCOMPLETE
→ READY_TO_FINALIZE
→ PACKAGE_FINALIZED
→ PACKAGE_SENT
→ WAITING_FOR_CLARIFICATION
→ MONTHLY_CLOSING_COMPLETED
```

## Regras adicionais

### FINR190
- primeiro ao último dia;
- pagos por DATA e NATUREZA;
- Receber altera "Da Carteira?";
- procedimento cita empresas 01,03,04.

### Extratos
Conta aplicável sem movimento ainda requer extrato.

`NO_MOVEMENT != NOT_APPLICABLE`.

### P7 / consumo
- P7 = MATR460;
- consumo/Relação por OP = MATR860;
- `MATR860 != P7`.

### Vocabulário fiscal
Inclui Alimentação, Amostra MP, Assistência Médica, Ativo, Combustível, Consumo Geral, Embalagem, EPI, Frete, Informática, Insumo, Limpeza, Manutenção, Material de Expediente, MP, Segurança/Vigilância.

Não inferir campo físico do Protheus a partir desse vocabulário.
