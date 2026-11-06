# Avaliação semântica de flexibilidade e eficiência — 5 cenários reais

TASK_ID: DELIA-C3-PYDANTIC-AI-SEMANTIC-FLEXIBILITY-EFFICIENCY-GENERALIZATION-01
EVALUATED: HEAD working tree | kimi-k3 | v41 | ~$0.15 | typed records

## Resultados por cenário

| ID | Pergunta | Calls | Errors | Outcome | Veredicto |
|---|---|---|---|---|---|
| A1 | resumo consolidado | 1 | 0 | analyze direto → GROUNDED | FLEXÍVEL+EFICIENTE |
| B1 | analise departamento engenharia | 8 | 5 | 5× MESMO erro "exige filial_id e setor_id" → limit | REPEATED_ERROR_PROVEN |
| C1 | processos na engenharia | 8 | 3 | reads ok + 2× analyze erro + page_size | PARCIAL |
| D1 | o que o transformômetro mede | 8 | 2 | knowledge churn + recoveries | PARCIAL |
| E1 | indicadores marketing | 8 | 1 | discovers 0 + analyze ok + invalid data | PARCIAL |

## Achados causais

DEFEITO PROVEN — REPEATED_ERROR_CLASS: B1 chamou analyze 5× com
  erro idêntico; o modelo leu "exige filial_id e setor_id" mas NUNCA
  buscou filial_id (teo.read entity=branch disponível) nem trocou
  para view consolidada — retry cego de mesma classe.
FIRST_DIVERGENT_BOUNDARY: ERROR_INTERPRETATION / next-step selection.
O tool-result entrega o erro; o modelo não extrai a ação corretiva
  (resolver identificador faltante via READ legítimo).

Dedup non_progress: rege só chamada IDÊNTICA (fingerprint); repetição
  de erro MESMA-CLASSE com args variantes passa — gap comprovado
  (mas NÃO autorizado corrigir nesta task).

EFICIÊNCIA: A1=1 call ideal; B1/C1/D1/E1 saturaram o limite de 8 com
  falhas repetidas/discover baixo-rendimento.

## Avaliação de mecanismos nativos
Tool-result errors: USADO e funcional (erro chega ao modelo).
ModelRetry: usado só p/ arg-shape — correto.
FALTA COMPROVADA: dedup por classe-de-erro; instrução de recuperação
  "resolver identificador ausente via READ" é lacuna de contrato do
  owner (filial não derivável sem READ).

## Proposta bounded (para aprovação futura)
Estender non_progress dedup: se 3+ calls consecutivas falharem com
o mesmo error_code/root_code, projetar repeated_equivalent_failure
com instrução técnica ("o argumento X é exigido e não foi informado —
obtenha-o via leitura autorizada ou mude de estratégia"). Provider-
neutral, sem heurística por owner. RED: B1-like scenario.
