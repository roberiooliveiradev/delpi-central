## Formato do relatório (obrigatório)

Devolva exatamente esta estrutura, em português. Identificadores técnicos (status, vereditos, ids)
ficam como estão. Não omita seções: se uma seção não tem conteúdo, escreva `nenhum`.

````markdown
# Relatório do delpi-verifier

veredito: <ACCEPT | ACCEPT_WITH_RESIDUAL | REWORK | EXECUTION_DRIFT | INCONCLUSIVE>
rodada: <1 | 2 | 3>
escalar: <SIM | NAO>
escopo: <base..head | working tree @ HEAD curto>
contrato: <PRESENTE | AUSENTE>
independencia: <OK | DEGRADADA> (verificador: <modelo>; executor: <modelo>)
registro: <OK | FALHOU: motivo>

## Resumo
<3 a 5 linhas: o que foi pedido, o que foi entregue, por que este veredito.>

## Expectativas (escritas antes de ler o diff)
| AC | Comportamento que prova | Evidência buscada | Irmão | Negativo |
|---|---|---|---|---|

## Critérios de aceite × evidência
| AC | Status | Evidência |
|---|---|---|

## Alegações do executor × realidade
| Alegação | Resultado | Evidência |
|---|---|---|

## Comandos executados
| Comando | Saída (exit) | Trecho relevante |
|---|---|---|

## Ordens de correção
<Uma por bloco. Só achados introduzidos pelo escopo com confiança ≥ 80.>

### OC-1 · <severidade: CRITICA | ALTA | MEDIA> · <categoria>
- **Viola:** <AC-x / RQ-x / regra do contrato>
- **Evidência:** <arquivo:linha e/ou comando + saída>
- **Esperado:** <comportamento correto, observável>
- **Reconferência:** <comando ou checagem exata que vai decidir se foi corrigido>
- **Confiança:** <80–100>

## Decisões necessárias (DECISION_REQUIRED)
| Id | Decisão | Opções | Impacto de cada opção |
|---|---|---|---|

## Ordens anteriores (rodadas 2 e 3)
| Ordem | Situação | Evidência |
|---|---|---|
<Situação: CORRIGIDA | CONTESTADA_ACEITA | CONTESTADA_REJEITADA | ABERTA>

## Observações (não bloqueiam)
<Achados com confiança < 80, pré-existentes, riscos residuais, sugestões. Cada um com evidência.>

## Não verificado
<Tudo o que ficou fora: comandos TEST_NOT_RUN e por quê, áreas não inspecionadas, dependências externas.>
````

Regras do formato:

- **Severidade** de ordem de correção: `CRITICA` (perda/corrupção de dado, falha de segurança, quebra de
  contrato público, objetivo principal não cumprido), `ALTA` (AC não cumprido, regressão em consumidor,
  atalho para passar no teste), `MEDIA` (defeito real com impacto limitado). Algo menor que isso não é
  ordem de correção: vai para `Observações`.
- **Reconferência** é obrigatória e precisa ser objetiva (um comando, um teste, um grep com resultado
  esperado). Ordem sem reconferência objetiva não é ordem: rebaixe para observação.
- **Nunca** inclua o código da correção. Descreva o comportamento esperado.
- Evidência sempre com caminho relativo à raiz do repositório e número de linha quando houver.
