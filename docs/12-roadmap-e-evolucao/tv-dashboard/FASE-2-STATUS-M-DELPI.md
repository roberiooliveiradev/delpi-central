# Fase 2 — status do compilador M DELPI

> **Status:** implementação concluída em 2026-07-16; runtime permanece fora de escopo
> **Profile:** `m-delpi-v1`
> **Flags de rollout:** `mQuery.enabled=false`, `mQuery.writeV2Enabled=false`

## Entregue

- gramática declarativa Lark 1.3.1 com parser singleton LALR e lexer contextual;
- AST própria, imutável e com `SourceRange` derivado dos metadados do parser;
- `let/in`, identificadores simples/cotados, literais, listas, records controlados,
  calls, `each`, acesso de campo, `if`, operadores com precedência e tipos;
- formatter canônico idempotente;
- registry JSON deny-by-default com assinatura, categoria, descrição, parâmetros,
  exemplos, versão e disponibilidade por superfície;
- análise semântica de símbolos, etapas, schema, argumentos, records e referências;
- compilação para `TransformPlan` imutável, sem executar M;
- limites de bytes, etapas, nós e profundidade carregados de
  `tv_dashboard_settings.json`;
- `POST /data/m/compile` e `GET /data/m/functions`, ambos com envelope atual e
  `TV_READ`;
- testes unitários, golden, corpus adversarial, HTTP e RBAC.

## Funções de tabela liberadas

`Table.RenameColumns`, `SelectColumns`, `RemoveColumns`, `SelectRows`, `Sort`,
`ReplaceValue`, `FirstN`, `LastN`, `Skip`, `RemoveLastN`,
`TransformColumnTypes`, `FillDown`, `PromoteHeaders` e `AddColumn`.

Funções escalares controladas de `Text`, `Number`, `Date`, `DateTime`,
`Duration` e `List` estão disponíveis apenas dentro de expressões autorizadas.

## Segurança

- toda função ausente do registry é rejeitada;
- `Web`, `File`, `Folder`, `Sql`, `Value.NativeQuery`,
  `Expression.Evaluate`, `#shared`, função de usuário, recursão e símbolos
  dinâmicos são rejeitados com código estável e range;
- não há `eval`, `exec`, transpile para Python, resolução dinâmica ou regex
  crescente;
- compile/functions não chamam preview, gateway, catálogo de fonte nem
  `api-delpi`;
- o frontend e a DSL legada não foram ampliados.

## Contrato HTTP

`POST /data/m/compile` aceita `profile`, `script`, `sourceSchema`,
`queryBindings`, `targetStepName` e `culture`. A resposta contém script
canônico, hash, etapas, output, diagnósticos e consultas referenciadas.

`GET /data/m/functions?profile=m-delpi-v1` devolve o registry declarativo.

## Fora de escopo

- execução do `TransformPlan`;
- fetch da fonte e preview por etapa;
- DAG/RBAC de consultas irmãs no runtime;
- persistência v2 ativa;
- mutação de script e editor frontend;
- funções de tabela previstas para a Fase 3.

`tv_data_transform_service.py` continua sendo a fachada canônica e só será
evoluída para consumir o plano M na Fase 3.
