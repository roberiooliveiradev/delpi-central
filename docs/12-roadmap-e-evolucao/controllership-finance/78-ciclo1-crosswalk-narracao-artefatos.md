# 78 — PROC-0072 | Cruzamento da narração do PO com as fontes do Ciclo 1

**Data:** 23/10/2026. **Escopo:** revisão documental sanitizada. **AS-IS:** relato guiado do PO sobre Joici registrado nos docs 56 e 57; doc 55 é recorte específico. **TARGET:** contratos e ADRs vigentes, sem alterações. Esta análise não reproduz vídeo, valores, pessoas, títulos, notas ou planilhas privadas. Narração documentada não equivale a homologação ERP.

## Crosswalk de evidência

| Narração (doc 57) | Docs de inventário | Atividade narrada | Correspondência documental | Limite de prova |
|---|---|---|---|---|
| V01-V04 | 56 R01-R04 | Acompanha Custos, reposicao, Refaz Saldos | sem arquivo final especifico | OWNER_REPORTED_VIA_PO; job/algoritmo TO_INVENTORY |
| V05,V16 | 65 | Faturamento x MOD | planilha com componentes, horas e custos | estrutura PROVEN; previsto x realizado TO_INVENTORY |
| V07-V08 | 69,70 | Posicoes e compensacao | saldos em aberto | matching e outcome INCONCLUSIVE |
| V09 | 71-75 | Cinco saidas auxiliares financeiras | PDFs por data/natureza e XLSBs | FINR190 candidato; paridade TEST_NOT_RUN |
| V10 | 77 (Analise) | variacao de custo medio | custo medio inicial/final | formula oficial TO_INVENTORY |
| V11 | 63,68 | P7 completo e variante | diferencas MP observadas | parametros TO_INVENTORY |
| V12 | 61 | Kardex 01/99 | exportacao fisico-financeira | cobertura de armazens TO_INVENTORY |
| V13 | 62,64 | MATR320 e processo | resumo e saldo analitico | recortes nao equivalentes |
| V14 | 66 | inventario INVENT | RE0/DE0 observados | soma 01/99 TEST_NOT_RUN |
| V15 | 61,67 | previa de CPV | Kardex e excecoes candidatas | filtro oficial TO_INVENTORY |
| V17 | 62-64,68 | conciliacao estoque | MATR320/P7/processo | RC01/RC02 INCONCLUSIVE |
| V18-V19 | 59,63,68 | entrega contabil e externos | checklist e PDFs | aceite real nao comprovado |
| V20-V22 | 77 (CC matriz) | classificacao SD1 | centros de custo e exclusoes | catalogo/rules TO_INVENTORY |
| V23 | 56,57 | sugestao assistida | sem artefato de implementacao | TARGET/DECISION_REQUIRED |

## Protocolo de validação a preparar para o Ciclo 2 (sem GO)

| Prioridade de investigação | Questão | Evidência mínima | Owner candidato |
|---|---|---|---|
| P0 | MATR320 x P7 x saldo em processo | recorte comum, equações e diferenças por grupo | Joici + api-delpi |
| P0 | P7 completo x reduzido | parâmetros e explicação da divergência MP | Contabilidade + api-delpi |
| P0 | CPV no Kardex | CFOP, terceiros, sinais, custo | Custos + api-delpi |
| P0 | Baixas financeiras | paridade PDF/XLSB, compensação e logs | Financeiro + api-delpi |
| P1 | Inventário 01/99 | população, movimentos, sinais por armazém | Estoques + api-delpi |
| P1 | Faturamento x MOD | base de horas, teórico/realizado | Custos + PCP |
| P1 | Variação de custo médio | fórmula e critérios de anomalia | Joici + api-delpi |
| P1 | Despesas por CC | cadastro, exclusões e vigência | Controladoria + Contabilidade |
| P1 | Entregas por competência | obrigatoriedade, destinatários e aceite humano | Joici + PO |

Prioridades e owners são sugestões de planejamento, não aprovações. Conservar distinções STOCK_CLOSED, PACKAGE_SENT e MONTHLY_CLOSING_COMPLETED; ATTACHED não significa VALIDATED. Nenhuma hipótese vira fórmula oficial por este registro.

## Divergências e limites

1. As duas variantes P7 exibem divergência em matéria-prima; não são comprovadamente simples visões reduzidas.
2. P7, MATR320 e material em processo não têm reconciliação oficial demonstrada.
3. Horas e custos MOD observados em XLSB não comprovam apontamento real.
4. Baixas financeiras não equivalem a saldo aberto ou movimento bancário; logs ausentes.
5. Narrativa de classificação de SD1 não homologou regras por prefixo de CC.
6. A alegação de conferência em ~30:45 foi retirada no doc 55, não criar requisito.
7. O registro integral ditado pelo PO consta nos docs 56/57; conferência direta independente de áudio/timecodes permanece INCONCLUSIVE, não significa relato ausente.

## Gate e veredito

**Revisão:** ACCEPT_WITH_RESIDUAL. **Ciclo 1:** documentação cruzada, fechamento formal PENDING. **Ciclo 2:** NO_GO até gate e aprovação explícita. **SQL parity:** TEST_NOT_RUN. **Runtime:** nenhuma autorização adicional. Manter fontes operacionais privadas fora do GitHub.
