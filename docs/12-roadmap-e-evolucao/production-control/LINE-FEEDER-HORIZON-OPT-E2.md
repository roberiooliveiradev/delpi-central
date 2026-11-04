# Alimentador de Linha — Otimização Etapa 2: tempo padrão progressivo

**TASK_ID:** `LINE-FEEDER-HORIZON-OPT-E2`  
**Depende de:** [LINE-FEEDER-HORIZON-E2.md](./LINE-FEEDER-HORIZON-E2.md) (motor), [LINE-FEEDER-HORIZON-SAFETY-E1.md](./LINE-FEEDER-HORIZON-SAFETY-E1.md) (segurança)  
**Escopo:** reduzir chamadas de tempo padrão fora do horizonte. **Não** é a Etapa 3 de materiais.

## Problema

`preview_horizon()` montava **todas** as operações abertas do CT (com ST) antes de `allocate_work_center_horizon()`. Em filas longas, dezenas de consultas api-delpi/Protheus ocorriam para ops que o motor nunca alocaria.

## Algoritmo

```text
saldos em lote (inalterado)
→ para cada CT, na ordem PUBLISHED:
    → ops fechadas: entram no prefixo sem ST
    → ops abertas: fetch ST (cache da requisição + limite global)
    → allocate_work_center_horizon(prefixo)
    → se horizon_needs_more_operations(result) == false: encerrar CT
→ shortfall/incomplete/complete + diagnósticos E1 preservados
```

`horizon_needs_more_operations`:

| completeness | continua? |
|---|---|
| complete | não |
| incomplete | não |
| shortfall `queue_shorter_than_horizon` | sim (se houver mais ops) |
| outros shortfall | não |

## Decisões

| Tema | Decisão |
|------|--------|
| Motor | **REUSE** `allocate_work_center_horizon` (sem segunda fórmula) |
| Cache ST | Preservado por `(OP, operação)` na requisição |
| Limite | `horizonMaxStandardTimeCalls` conta só chamadas reais |
| Paralelismo / workers | **Não** ativado — `horizonStandardTimeWorkers` permanece config sem uso; ganho principal é progressive stop |
| Pooling HTTP / batch ST | Fora desta etapa (sem evidência de necessidade pós-progressivo) |
| Contrato | Aditivo: `standard_time_calls_avoided`, `progressive_allocation` no CT |

## Rework — parcial não pede mais ST

Cobertura **parcial** (sobra < 1 peça da OP atual) mantém `completeness=complete` e **não** marca
`queue_shorter_than_horizon`. Assim `horizon_needs_more_operations` encerra o CT sem consultar
ops posteriores (evita falso `standard_time_call_limit`).

Materiais: ver [LINE-FEEDER-MATERIALS-E3.md](./LINE-FEEDER-MATERIALS-E3.md) — demanda = empenho SD4
aberto integral das ops contempladas (sem proporção por peças cobertas).

## Baseline vs depois (testes)

Cenário AC-01 (1 CT, 55 ops, 8 h, 5 suficientes):

| Métrica | Antes (comportamento pré-OPT) | Depois |
|---------|-------------------------------|--------|
| Chamadas ST | 55 (ou até limite) | **5** |
| Evitadas | 0 | **50** |
| Latência p50/p95 prod | não medida nesta entrega | PENDING amostragem |

## Aceite

Ver `tests/test_line_feeder_horizon.py` (bloco Otimização Etapa 2) + regressão `test_line_feeder_materials.py`.

## Etapa 3 (fora)

Empenhos SD4, estoque 99/01, consolidação, localizações, bloqueios — sem mudança aqui.
