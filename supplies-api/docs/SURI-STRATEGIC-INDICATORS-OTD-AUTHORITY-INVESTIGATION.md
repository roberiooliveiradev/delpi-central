# SURI — Strategic Indicators Authority & OTD Drift Investigation

```
TASK: SUPPLIES-STRATEGIC-INDICATORS-AUTHORITY-AND-OTD-DRIFT-INVESTIGATION-001
BASE_HEAD: dda06d770c · ORIGIN_MAIN: HEAD do investigation worktree
GIT_STATUS: limpo (worktree isolada /tmp/inv-wt; investigação read-only)
```

## Data lineage (provado no HEAD)

```
TOTVS/Protheus
  └─ api-delpi  (SQL canônico; OTD por filial + consolidado)
       ├─ supplies-api OverviewCompositionService
       │    → chama api-delpi SEM filial → consolidado do producer = 91,12%
       ├─ supplies-api OtdAggregateService
       │    → consulta cada filial (01:95,86 / 02:88,14)
       │    → _mean(otd_values) = 92,00%
       └─ strategic-indicators-api
            → delpi_supplies_gateway.get_supplies_otd
            → supplies_indicators_snapshot_provider
              (source_key=supplies_otd, indicator_id=supplies-otd)
```

## Regra oficial encontrada (Strategic Indicators)

```
V022__supplies_average_of_units.sql
  UPDATE department_indicators SET aggregation_mode='average_of_units'
  (indicadores de Suprimentos — inclui supplies-otd)

V034__indicator_branch_value_aggregation.sql
  ADD COLUMN branch_value_aggregation DEFAULT 'auto'
  valores: auto|sum|average|source_consolidated
  comment: "Rollup entre filiais na visão consolidado"
  explicit overrides: commercial-* (sum/average), ppm→source_consolidated
  supplies-otd → NENHUM override → 'auto' (resolve por value_unit)

exposto em: get_dashboard_department_indicators_use_case.py:196
            get_dashboard_indicator_metric_use_case.py:290
            catalog_inputs_fingerprint.py:41
```

## Respostas às perguntas

```
Q1 regra oficial de consolidação do supplies-otd:
   PROVEN — aggregation_mode='average_of_units' (V022) registra
   rollup por média das unidades; branch_value_aggregation='auto'
   (V034, resolve por value_unit). MÉDIA DE UNIDADES é a regra
   cadastrada no owner — não source_consolidated.

Q2 quem calcula o realizado oficial:
   PROVEN — api-delpi fornece os valores por filial (owner do dado
   TOTVS); o método de CONSOLIDAÇÃO homologado está registrado no
   Strategic Indicators (average_of_units). Composição contratual:
   dado do producer + método do catálogo SI.

Q3 por que Overview ≠ página OTD:
   PROVEN — Overview chama api-delpi consolidado sem filial
   (cálculo do producer, ponderado pelos denominadores reais);
   OTD page/SURI faz _mean(95,86+88,14)/2=92,00% — média simples.

Q4 qual valor é oficial para 01+02:
   PROVEN — 92,00% pela regra cadastrada (average_of_units).
   O 91,12% do Overview usa método DIFERENTE do cadastrado
   (consolidado do producer = weighted by denominators).
   ⚠ O valor do producer não é errado — é um método legítimo,
   mas NÃO é o método registrado no SI.

Q5 SI expõe consolidado pronto:
   PARTIAL — SI expõe branch_value_aggregation nos payloads do
   dashboard; se o endpoint aplica a resolução de 'auto' ao
   calcular o consolidado = TO_INVENTORY (campo é exposto; a
   aplicação do rollup no backend precisa de mais leitura).

Q6 outros indicadores divergentes:
   TO_INVENTORY — supplies-stock-value/turnover/cpv têm o mesmo
   padrão V022 (average_of_units); mesma classe de risco de
   divergência entre consolidado producer vs média de unidades.

Q7 menor diff para unificar:
   PROVEN (proposta) — OtdAggregateService já calcula o método
   oficial. O Overview deve consumir o valor consolidado conforme
   a regra do SI (average_of_units para %) em vez do consolidado
   cru do producer — ou o SI deve expor o consolidado pronto e
   ambos consumidores o usam.

Q8 contratos a preservar:
   PROVEN — endpoint api-delpi por filial (insumo), contrato SI
   /dashboard/department-indicators (regra), estrutura de
   resposta do Overview/OTD (shape consumido pelo MFE/SURI).
```

## Proposed minimal diff (NÃO executado)

```
A. Contrato oficial: realizado por filial da api-delpi +
   branch_value_aggregation do catálogo SI.
B. Agregação: no supplies-api (compositor) aplicando o método
   cadastrado no SI — nunca hardcoded _mean quando o catálogo
   disser outra coisa; ler branch_value_aggregation do payload SI.
C. Paridade: Overview, página OTD e SURI consomem o mesmo valor
   consolidado calculado pela regra do SI para o mesmo
   scope+período.
D. Diff: overview_composition_service.py (trocar consolidado
   producer→aplicar branch_value_aggregation sobre valores por
   filial), otd_aggregate_service.py (registrar método usado no
   payload), strategic_indicators_gateway.py (expor
   branch_value_aggregation).
E. Testes: 1 filial / 2 filiais / consolidado / denominadores
   assimétricos (prova que mean≠weighted) / sem dados / falha de
   filial / meta vs realizado / arredondamento / escopo não
   autorizado / paridade entre consumidores.
F. Migração: Overview MFE + SURI overview_summary passam a ver
   o valor average_of_units — BREAKING nos números exibidos
   (91,12→92,00 no cenário observado); requer alinhamento com PO.
```

## Security findings

```
PASS — nenhum acesso direto a banco cruzado; SI consulta api-delpi
por HTTP autorizado; escopo de filiais segue Core; investigação
read-only, nenhum dado mutado.
```

## Final classification

```
FACTS_PROVEN: lineage completo; V022+V034 catalogam a regra;
  91,12 = producer consolidated, 92,00 = average_of_units (regra
  cadastrada); divergence = método, não bug de dados.
TO_INVENTORY: resolução exata de branch_value_aggregation='auto'
  por value_unit no backend; se o endpoint SI já calcula o
  consolidado pronto.
EXECUTION_DRIFT: Overview consome consolidado do producer em vez
  do método cadastrado no SI — divergência consumer↔catálogo.
FINAL_CLASSIFICATION: INVESTIGATION COMPLETE — regra oficial
  identificada com evidência em migrations; correção é decisão
  arquitetural (muda número exibido; requer GO).
NEXT_STEP: revisão arquitetural — aprovar minimal diff §D.
```
