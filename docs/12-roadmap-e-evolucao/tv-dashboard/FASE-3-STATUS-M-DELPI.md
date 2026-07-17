# Fase 3 — status da execução M DELPI

> **Status:** implementação concluída em 2026-07-16
> **Base:** `ccb941fb9`
> **Flags:** `mQuery.enabled=false`, `mQuery.writeV2Enabled=false`

## Entregue

- `TransformPlan` M é executado pela fachada canônica
  `tv_data_transform_service.py`; v1 continua pelo adapter legado;
- interpretador fechado de `CompiledExpression`, sem `eval`, `exec`, transpile,
  resolução dinâmica ou segundo executor tabular;
- `if` lazy e `and`/`or` com curto-circuito;
- tipos `text`, `number`, `logical`, `date`, `datetime`, `duration` e `any`,
  com cultura `pt-BR` explícita;
- erros por célula preservados no valor e em `runtimeErrors`; falhas estruturais
  interrompem a etapa e são devolvidas com código e `stepName`;
- execução das funções MVP da Fase 2, `Table.Group`, `Pivot`, `Unpivot`,
  `UnpivotOtherColumns`, `NestedJoin` e `ExpandTableColumn`;
- left join 1:N sem perda de correspondências;
- DAG por `queryName → sourceId`, ordem topológica independente da ordem dos
  blocos e rejeição de ciclos antes de fetch;
- pré-autorização allowlist/filial de todas as consultas do DAG antes do
  primeiro fetch;
- `/data/preview-block` com `targetStepName`, `previewOptions`, schema tipado,
  nulabilidade, origem do tipo, diagnósticos, erros, tempo e amostragem, sem
  remover `data.block.resolved`;
- `/data/validate-config` compila todos os scripts v2, valida referências,
  ciclos, profile e limites e agrega diagnósticos;
- limites configuráveis de bytes, AST/profundidade, linhas, colunas, células,
  join, pivot e deadline, verificados também dentro de loops;
- editor administrativo, preview e apresentação pública convergem no mesmo
  enrichment e na mesma fachada. O runtime v2 só ativa com `mQuery.enabled`;
  a escrita v2 permanece desligada.

## Segurança e compatibilidade

- conectores, funções desconhecidas, avaliação dinâmica e funções de usuário
  continuam deny-by-default;
- consultas irmãs só entram no ambiente depois de autorização;
- cache continua isolado por contexto de autorização;
- configurações v1 mantêm o caminho legado e o contrato `resolved`;
- nenhum dado, AST ou plano compilado é persistido.

## Testes

`tests/test_m_query_phase3_execution.py` cobre lazy evaluation, curto-circuito,
tipos/cultura, erros de célula, group/pivot/unpivot, join 1:N, DAG/ciclos,
pré-autorização RBAC e contrato HTTP de target step. A suíte existente cobre
paridade v1 e contratos anteriores.

## Rollout

1. manter `writeV2Enabled=false`;
2. ativar `mQuery.enabled` primeiro em ambiente controlado;
3. validar limites e p95 com dados reais;
4. habilitar escrita v2 apenas na Fase 4, junto ao workbench transacional.
