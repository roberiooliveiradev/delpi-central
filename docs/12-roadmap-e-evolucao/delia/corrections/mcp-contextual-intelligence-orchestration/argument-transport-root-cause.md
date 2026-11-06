# Root cause — argument transport (guards aparentemente ineficazes)

TASK_ID: DELIA-C3-PYDANTIC-AI-ARGUMENT-TRANSPORT-ROOT-CAUSE-01
BASE_HEAD: 7c1bbee4b05cdf3ecfc6cbaa981c89a6d517bdf9

## Causa-raiz comprovada do falso negativo de observação

`scripts/native_mcptoolset_direct_eval.py:135` — o invoke record
serializa todo valor de argumento via `str(v)[:200]`. Um `dict` real
enviado pelo modelo renderiza `{'filter': ...}` IDÊNTICO a uma string
enviada pelo modelo. Os wire records NÃO distinguem str-vs-dict —
a evidência de "params ainda chega como string" usada na task anterior
é não-conclusiva por construção (H5 PROVEN: records representam um
estágio/formato diferente do presumido).

## O que é genuinamente comprovado (não é artifact)

- C2: read process com filtro retornou 109 itens NÃO filtrados → o
  owner recebeu algo que não podia interpretar como filtro.
- B2: INVALID_FIELD e 400s em params stringificados → strings reais
  atravessaram o wire em algumas chamadas.
- Logo: strings inválidas EXISTEM no wire — mas a frequência/taxa é
  indeterminável pelos records.

## Por que os guards "não dispararam" — análise

- Guard adapter (_governed_invoke): log de debug nunca apareceu →
  provável caminho real via FunctionToolset direto ou signature
  divergente do process_tool_call em 2.50.0 (TO_INVENTORY).
- Guard gates (_governed_semantic_tool_invoke): se os args chegam
  como dict real (modelo correto) → corretamente não rejeita; se
  chegam como str → deveria rejeitar. Os records não distinguem.
- _validate_instance (jsonschema): params anyOf[object,null] deve
  rejeitar string; strings passaram → ou schema solto/ausente, ou o
  str() ocorre entre validação e wire (transport-side serialization).

## Fronteira divergente (evidência)

FIRST_DIVERGENT: observability artifact — harness record str()-ifica
args; impossível classificar tipo real sem instrumentação tipada.
Próximo passo bounded: 1 log com type(v).__name__ por arg na entrada
de _governed_semantic_tool_invoke + 1 run B2 (~$0.03) → resolve
definitivamente H1/H2/H6 vs str()-downstream.

## Classificação

- harness record serializer: CONTRIBUTING_DEFECT (observation, não produção)
- _governed_invoke / _governed_semantic_tool_invoke: INCONCLUSIVE no caminho real
- _validate_instance: INCONCLUSIVE (schema do TÉO para params pode ser solto)
- transport serialization (adapter→wire): TO_INVENTORY
