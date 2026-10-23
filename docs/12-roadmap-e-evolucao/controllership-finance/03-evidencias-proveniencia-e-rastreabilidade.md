# 03 — Evidências, Proveniência e Rastreabilidade

## Checklist oficial

Fonte: **Arquivos de envio - contabil para fechamento mensal.pdf**.

### Bancos/documentos externos
XP/Dennis, Banco do Brasil, aplicações BB, Bradesco, aplicações Bradesco, cartões, contas Nordeste, Sicoob, Conta Capital e aplicações.

### Financeiro
- baixas Receber PDF/Excel;
- Pagar Excel;
- Pagar PDF Natureza;
- Pagar PDF Data.

### Importações
Swift, contrato de câmbio, encontro de contas, fechamentos Excel + ACSI.

### Estoque/custos
- Valor Estoque Entradas/Saídas ou P7 layout H → Contábil;
- CPV/Kardex01 → Fiscal;
- Inventários 01/99 INVENT → Contábil;
- Fat × MOD → Contábil;
- Material em Processo → Contábil;
- itens NF por CC;
- NF venda 9035 → Fiscal;
- CPV zero-value check → Fiscal;
- P7 layout H.

## Procedimento "Relatórios enviados à Contabilidade"

Registra FINR190, primeiro/último dia, Pagar por DATA/NATUREZA, Receber com "Da Carteira?", empresas 01/03/04, lista bancária histórica, P7 = MATR460 e consumo/Relação por OP = MATR860.

`MATR860 != P7`.

## Entrevista <GESTORA-PROC>

- início no primeiro dia;
- XML/SPED obtido pela Contabilidade;
- demais docs dependem da DELPI segundo a entrevista;
- XP depende de Dennis;
- conclusão após envio/esclarecimentos;
- conhecimento concentrado.

## NotebookLM

Aceito: checklist, structured vs external, multi-anexo, upload != validação, snapshot, envio humano e limite da IA.

Rejeitados como overclaim: destinatários incorretos, defaults opcionais, SD1 conflado, unidade universal, N/A universal, MATA280 PROVEN, ~18h fixo, e-mail/pasta universal, todos bancos observados, banco direto target, confidence como prova.

## Vídeo

MP4 original anteriormente inspecionado:
- 00:54:44.125;
- 126.314.059 bytes;
- SHA256 `fdbdddcdfe0aa511944f396fe6d29a9fcb1cb4c75c597687ed6bfc2519150078`.

Extração derivada cita 01:02:15. Causa UNKNOWN.

`TIMECODE_PROVENANCE = STALE_EVIDENCE / TO_RECONCILE`.

## Drift bancário

Checklist e procedimento divergem.

`BANK_SCOPE_DRIFT = PRESENT`.

A lista será configurável. Falta confirmar seed/owner/unidade.

## Regra

Exemplo de reunião não vira regra universal. Preservar origem e classificação de toda decisão.


## R03 — P7/MATR460: proveniência consolidada após Fases A e B1 (20/10/2026)

**Autoridades segregadas:** TÉO/PROC-0072 sustenta a existência dos passos P7 padrão, P7 Bloco H e conferência tripla. NotebookLM é análise **derivada fornecida pelo PO**, não auditoria independente do vídeo. DAVI comprova somente dados físicos/consultas SQL efetivamente executadas. GitHub é authority do TARGET e guarda resultados auditáveis nos [docs 46 §§10–11](./46-t01-report-source-inventory-v1.md).

### Relato derivado do NotebookLM — não observado diretamente nesta rodada

O texto recebido relata que <GESTORA-PROC> emite o relatório funcional **P7 — Registro de Inventário** em 30/09/2026, filial 01 (procedimento também na 02), saída padrão e layout H, opção terceiros não, 91 páginas, seis colunas (produto, descrição, UM, quantidade, custo unitário e total), resumo por grupos, emissão PDF e conciliação com Entradas/Saídas/H02. Referências do relato: P7 padrão **3.776.994,69**, Insumos **266.321,45**, Entradas/Saídas **3.890.247,18**, H02 **64.591,71**, resíduo **48.660,78**. Esses números **não são outcome Protheus verificado**. Relato sobre regra de tipos MP/PA/PI do Bloco H carece de confirmação de parâmetros/regras; não implementá-la por suposição.

**Inconsistências da derivação:** menciona marcações >01:00:00 quando MP4 original catalogado dura 00:54:44.125; fornece diferença de Insumos como R$0,25 embora 266.321,46 − 266.321,45 = **R$0,01**. Re-extração após 18h é relato contextual de corte fabril, não regra universal nem autorização para automatizar bloqueio por relógio. Critério AS-IS de conciliação final: **R$0,00 até centavos**, sem aceitar diferença por arredondamento não homologado.

### Prova DAVI da fonte — não equivale a relatório emitido

Filial 01 em SB9010 30/09/2026: 4.812 linhas, 4.027 produtos, soma B9_VINI1 **3.884.439,52**; `B1_TIPO='II'` na junção SB1010 soma **266.321,45**, coincidindo com Insumos derivado. Soma SB9 vs P7 derivado difere em **107.444,83**. Armazéns 01/98/99 e demais, custos/quantidades zero, configurações SX6010 e ausência de grupo exato MATR460 nas buscas SX1010 analisados no doc 46 §§10–11. Não há justificativa comprovada para filtrar arbitrariamente. Tabelas H_ de 2023–2025 são evidência da saída histórica Bloco H, não equivalência com o P7 padrão 2026.

**Gates:** `NOTEBOOKLM_DERIVED=INFORMED`; `VIDEO_DIRECT_REVIEW=TEST_NOT_RUN`; `TIMECODE_PROVENANCE=STALE_EVIDENCE`; `SQL_SOURCE_DISCOVERY=PROVEN`; `MATR460_ALGORITHM=TO_INVENTORY`; `P7_REPRODUCTION=INCONCLUSIVE`; `EXPORT_REFERENCE=NOT_PROVIDED`; `EXPORT_PARITY=TEST_NOT_RUN`. Sem PDF exportado, parâmetros originais ou fonte ADVPL/trace autorizada, não afirmar P7 reproduzido nem homologado.
