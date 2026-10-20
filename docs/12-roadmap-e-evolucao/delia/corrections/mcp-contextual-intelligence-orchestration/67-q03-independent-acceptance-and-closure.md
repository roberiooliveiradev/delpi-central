# Q03 — parecer independente de encerramento

**TASK:** `DELIA-C3-I04-Q03-INDEPENDENT-ACCEPTANCE-AND-CLOSURE-01`  
**DATA:** 2026-10-20  
**BASE_HEAD:** `aad2369d5bc4c0c09dc1269e61b726827ab5a272`  
**VERDICT:** `ACCEPT_WITH_RESIDUAL`

Revisão independente, sem diff de runtime, sem deploy e sem nova bateria de modelo. A autorização de entrada está no plano 16 (`12b3d0f437`), no roadmap 59 §21 (`1f46818cb8`) e no ledger §6.341 (`576cf0d06f`).

## Correspondência de código

`delia-api` não tem diff entre o commit do orçamento `a9f5f8d3c2ac389747ce4249e0e185cca72f52e1` e este HEAD. A suíte 1685 reportada nesse SHA continua válida para o fonte avaliado e não foi reexecutada. O SIPOC real foi medido no host `a9c3df812d`, ancestral deste HEAD e com o mesmo `delia-api`. Commits posteriores são de outras aplicações e de documentação.

Checagem estática neste HEAD:

- `admission_outcome=EARLY_CONVERSATIONAL_ADMISSION` aparece uma vez na orquestração.
- `_typed_compare_outcome_content` está ausente.
- `_selected_proven_differences` permanece.
- `OWNER_RECORD_NOT_FOUND` permanece.
- `classify_result_intent` e `unique_structural_ticket_list_capability` permanecem.

## Parecer por eixo

| Eixo | Resultado |
|---|---|
| Arquitetura | O modelo propõe admissão, seleção e argumentos. A DÉLIA valida contrato, prazo, provenance e outcome. Síntese factual continua selection-only. |
| Owners | Core autoriza. A API de domínio continua autoridade dos dados. MCP/A2A e OpenAPI não autorizam. |
| Contratos | Sem contrato público novo nesta trilha. A projeção de ausência usa o envelope já existente do owner. |
| Segurança | Modelo, metadata e histórico não concedem permissão. Erro de owner continua terminal. Não houve ACT no smoke. |
| Generalização | A admissão e a seleção não têm ramo por DAVI/TÉO/VISTA. B1 é a exceção lexical, limitada a um READ/QUERY de chamados. |
| Performance | Orçamento global 30 s. Admissão antecipada usa o saldo. Fallback pós-orquestração conserva 12 s. Sem retry automático. |
| Funcional | SIPOC PASS. Hipóteses PASS. Comparação conversacional PASS. Paráfrase OpenAPI GROUNDED PASS. Formatos com limitação honesta PASS. |

## Evidência real já registrada

| Caso | Estado | Onde |
|---|---|---|
| SIPOC | PASS, 13412 ms, admissão conversacional, sem frase de teto | doc 66, §6.339–6.340 |
| Hipóteses | PASS | doc 63 |
| Comparação conversacional | PASS; não exercitou o gate tipado | doc 63 |
| Paráfrase OpenAPI | PASS, GROUNDED | doc 63 |
| Formatos | PASS, limitação honesta | doc 63 |
| Identificador sintético | PARTIAL no runtime anterior à projeção de 404; nenhum registro inventado | doc 63 |
| HTTP 404 no runtime novo | TEST_NOT_RUN | doc 64 |
| Comparação tipada de dois registros | NOT_EXERCISED | doc 63, §6.340 |
| DAVI/TÉO/VISTA amplo | incompleto | §6.341 |

A amostra SIPOC terminou a resposta em cerca de 11,1 s. Ela prova o cenário observado e o marcador no processo. Não prova um estágio acima de 12 s.

## B1

`unique_structural_ticket_list_capability` só devolve capability quando a intenção lexical é contar ou listar, o texto é de chamados e existe exatamente um READ/QUERY cujo schema anuncia `action=tickets`. Zero ou mais de um resultado devolve vazio. Não escolhe escrita e não inventa capability.

```text
B1_RISK=NON_CRITICAL
B1_DECISION_STATUS=UNRESOLVED_FORMALLY_DEFERRED
```

O risco não bloqueia o aceite: não escala permissão e falha fechado fora do caso único. Também não está resolvido. A ADR 58 ainda prefere proposta do modelo para classificação semântica. A decisão de produto é manter o atalho por causa de R4/R5 e dos 30 s, ou substituí-lo numa tarefa separada.

## O que não entra no aceite

- `I04_ACCEPTED` permanece `NO`.
- `C3_EXECUTED` permanece `NO`.
- Produção não é declarada pronta.
- B1 não é declarado corrigido.
- Lacunas ao vivo não são promovidas a PASS.

## Próxima decisão de produto

Escolher, fora desta trilha, se B1 será mantido como exceção permanente, se a comparação tipada e a projeção de 404 serão medidas uma vez no runtime atual, e se I04 terá review próprio. Nenhuma dessas escolhas reabre Q01–Q03.
