# GLPI #1353 — D2.1 Regras funcionais da Auditoria de Consumo por Operação

> **Estado:** DRAFT / PROPOSED — NÃO HOMOLOGADO. Data: 2026-10-29.
> **Natureza:** especificação de requisitos e critérios verificáveis; não é autorização para implementação.
> **Referências:** [fluxo e evidências D1](./GLPI-1353-PRODUCTION-CONSUMPTION-AUDIT-FLOW-20261029.md), [boundaries](./MATRIZ-BOUNDARIES.md), [ADR-009](./adr/ADR-009-product-access-and-operational-data-scope.md), D0 Devin (baseline informado `d955f51cfda36e9d5f5af5d04194e1441ae34d36`).
> **Gates:** D0 ACCEPT_WITH_RESIDUAL; D1 INCONCLUSIVE (causalidade e exceções); D2 PENDING; implementação NOT_AUTHORIZED.

## 1. Resultado de negócio esperado

Permitir que Suprimentos investigue, com evidências verificáveis, **se a baixa dos componentes de uma OP é compatível com a estrutura e com as operações realmente apontadas**. Sinalizar indícios e suas explicações possíveis, não condenações automáticas. Uma diferença no consumo **não comprova furo físico**.

### RQ / AC

| ID | Regra/requisito proposto | Critério de aceite documental / teste |
|---|---|---|
| RQ-01 | Grão primário **filial × OP × operação × componente × unidade** | AC-01: dois componentes de operações diferentes jamais colapsam em um mesmo total de baixa |
| RQ-02 | Comparar fontes distintas: teórico SG1 válido na referência homologada; empenho/consumo derivado SD4; movimentos SD3 classificados | AC-02: exibir os três valores e respectivas fontes; divergência SD3/SD4 é informação e não erro presumido |
| RQ-03 | Interpretar estado real da operação antes de determinar falta de consumo | AC-03: empenho aberto em operação comprovadamente não executada não gera alerta conclusivo |
| RQ-04 | Segregar movimento de transferência, retorno, estorno, inventário, mão de obra e consumo elegível | AC-04: transferência de 0,64 MT na OP de referência não eleva consumo para 81,39 MT |
| RQ-05 | Preservar rastreabilidade de OP, operação, item, armazém, documento, data, TM/CF, natureza, origem, UM e motivo de não classificação | AC-05: cada cálculo de consumo é reconstituível sem usar documento isolado como chave única |
| RQ-06 | Diferenciar indício calculado de irregularidade confirmada | AC-06: nenhuma ocorrência recebe rótulo de fraude, furo ou ajuste ERP sem prova e fluxo de homologação |
| RQ-07 | Respeitar vigência de estrutura, substituição/engenharia, OPs relacionadas e conversão de UM | AC-07: faltando semântica ou dados, resultado é INCONCLUSIVE/unclassified, não zero inventado |
| RQ-08 | Não alterar saldos, baixas, empenhos ou apontamentos | AC-08: MVP de cálculo é READ-ONLY |
| RQ-09 | Não confundir E12 consumo mensal por produto/período com GLPI #1353 por OP/operação | AC-09: contratos e navegação diferentes, sem sobrepor a E12 nem promover página automaticamente |

## 2. Fluxo funcional candidato

1. Selecionar filial 01 ou 02, período e OP; validar escopo.
2. Ler OP SC2, OPs vinculadas/origem, seu estado de encerramento e quantidades.
3. Resolver BOM SG1 efetiva na data de referência **a definir com PCP**; preservar versão e exceções de engenharia.
4. Ler roteiro/centros e execução/apontamentos **efetivos**, não apenas operações cadastradas na SH8.
5. Associar SD4 a OP e operação, inclusive `D4_OPORIG`; discriminar empenho original, saldo e derivado, sem tratar derivado como consumo líquido definitivo.
6. Classificar movimentos SD3 pelo domínio `api-delpi` e reconciliar retornos, estornos e conversões autorizadas.
7. Confrontar teórico, SD4 e SD3, com cobertura/completude/fonte e tolerâncias somente após homologação.
8. Expor diferenças e situações `reconciled`, `arithmetic_difference`, `requires_investigation` ou `unclassified` como **proposta de classificação**.
9. Registrar decisão humana/justificativa apenas em fase futura explicitamente aprovada; nenhuma escrita no Protheus.

**Regra operacional relatada:** ao executar/apontar uma operação, a baixa de matéria-prima é automática no Protheus. **Status: BUSINESS_RULE_CANDIDATE**, ainda sem correlação causal evento apontado → documento de baixa validada no runtime.

## 3. Matriz candidata de ocorrências

| ID | Situação a investigar | Pré-condição que evita falso positivo | Resultado enquanto não homologado |
|---|---|---|---|
| A | Consumo efetivo acima do esperado | operação/produção de referência comprovadas, UM consistente, retorno/estorno liquidado e tolerância ratificada | arithmetic_difference |
| B | Consumo abaixo do esperado | só sinalizar falta após identificar operação executada e baixa exigível; OP aberta não equivale a consumo faltante | requires_investigation ou unclassified |
| C | OP encerrada sem baixa elegível | encerramento e universo de operações confirmados; revisar filtro legado `C2_PRIOR=500` | requires_investigation |
| D | Movimento de componente ausente da estrutura | excluir corretamente MO/serviços, substituição e auxiliares autorizados, BOM histórica, OP relacionada | unclassified até decidir |
| E | Empenho residual após encerramento | encerramento confiável e vínculo OP/origem validado | requires_investigation |
| F | Movimento possivelmente atribuído à OP errada | comparar chave completa filial/OP/operação/item; documento pode ser compartilhado | requires_investigation |
| G | Divergência com inventário físico | requer contagem/inventário SB7, recorte produto/armazém e nexo comprovável; **não inferir furo físico de A–F** | escopo futuro, não incluído no MVP |

## 4. Cenário real documentado — nunca extrapolar

**Filial 01, OP 24884201006, PI 50226108, planejado 0,125 MI.** SH8 lista operação 01/CT-23 (cabo) e 02/CT-35 (terminal); SH6 retornou apontamento `H6_QTDPROD=0,125`, mas SC2 retornou `C2_QUJE=0` e sem encerramento: **inconsistência semântica pendente**, não tratar como OP concluída.

| Operação | Componente | SG1 teórico preliminar | SD4 derivado | SD3 consumo classificado |
|---|---|---:|---:|---:|
| 01 / CT-23 | 10010030 cabo | 80,75 MT | 80,75 MT | 80,75 MT |
| 02 / CT-35 | 10080329 terminal | 250 PC | 0 PC | nenhuma baixa na amostra dessa OP |

`220039839` = 0,64 MT, transferência inbound (não segundo consumo); `220039841` = 80,75 MT, consumo outbound; `220039840` = `MOD216`, mão de obra direta `MO` 0,233 HR, fora da soma de MP. O documento 220039841 também contém linha de outra OP. SG1 consultada foi válida entre 2026-10-20 e 2049-12-31, abrangendo emissão de 2026-10-20. A linha SD4 de OP `24884201002` referencia `D4_OPORIG=24884201006`; sem atribuição automática de consumo sem regra de origem homologada.

**Conclusão estrita:** não gerar alerta de sobreconsumo de 0,64 para o cabo; não presumir falha dos 250 terminais reservados; **não afirmar execução individual das operações 01/02 apenas pela SH8**.

## 5. Pendências que exigem decisão

| Decisão | Dono da validação | Estado |
|---|---|---|
| Significado de SH6 `H6_TIPO=P`/0,125 frente ao `C2_QUJE=0` | PCP/owner do Protheus + Joici/Michael | TO_INVENTORY |
| Fonte/evento da execução efetiva **por operação**, e correlação causal com baixa automática | PCP/owner do Protheus | TO_INVENTORY |
| Marco temporal e fator de cálculo (quantidade planejada, produzida ou apontada por operação) | Joici/Michael + PCP | TO_INVENTORY |
| Tratamento de estorno, devolução, transferência, refugo, substituição e consumo adicional | PCP/owner do Protheus | TO_INVENTORY |
| Regra para `D4_OPORIG`, OP filha/mãe e dupla contagem | PCP/owner do Protheus | TO_INVENTORY |
| Tolerâncias por família/UM/operação, severidade, momento de abertura e fechamento de alerta | Joici/Michael | TO_INVENTORY |
| Regra `C2_PRIOR=500` e escopo de OPs elegíveis | PCP | TO_INVENTORY |
| Posicionamento no Portal distinto de E12, dependência do gate E11 | Product Owner | PENDING |

## 6. Aceite e próximo gate

D2.1 permanece **DRAFT** até assinatura funcional das decisões acima. Próxima atividade: sessão dirigida Joici/Michael/PCP com exemplos de operação executada, pendente, baixa parcial e retorno; anexar evidência e registrar decisão explícita por RQ. Não mudar status das regras apenas porque um único caso conciliou.
