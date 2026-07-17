# Fase 5 — Paridade funcional Power Query essencial

**Status:** concluída em 2026-07-17
**Baseline:** `7fcd13705`

## Resultado

O perfil seguro `m-delpi-v1` passou a cobrir, de ponta a ponta, as famílias
essenciais de preparação de dados. Cada transformação publicada parte de um
comando tipado no frontend, é convertida em M exclusivamente por
`MQueryMutationService`, compilada para `TransformPlan` e executada pela fachada
canônica `tv_data_transform_service`.

O browser continua sem parser, sem executor e sem concatenação de M. Texto M só
entra como expressão explícita de coluna personalizada, sempre analisada pelo
compilador backend. O editor avançado continua reservado à Fase 6.

## Funções e famílias

- colunas: escolher, remover, reordenar, renomear, duplicar, dividir e índice;
- linhas: filtro, topo/base, intervalo, distinct, reverse e tratamento de erros;
- tipos: `text`, `number`, `logical`, `date`, `datetime`, `duration`, `any` e
  cultura `pt-BR`;
- escalares: texto, número, data/datetime/duration e listas de agregação;
- tabela: fill up/down, transpose, group, pivot/unpivot e append;
- combinar: nested left join 1:N, expansão e limite de cardinalidade;
- adição: personalizada, condicional, duplicada, índice e transformação escalar;
- erros: célula de erro estruturada, `Table.RemoveRowsWithErrors` e
  `Table.ReplaceErrorValues`, sem conversão silenciosa em `null`.

O registry `m_delpi_v1_functions.json` v1.2.0 é deny-by-default e registra nome,
kind, categoria, assinatura, parâmetros, exemplo, versão e disponibilidade.

## UI e contratos

- `DataQueryInsertOperation` fecha o conjunto de operações geradas pela ribbon;
- ações principais estão na ribbon e menu de contexto, com nomes de etapa
  estáveis;
- autocomplete e ajuda continuam consumindo `GET /data/m/functions`;
- nenhum componente novo foi criado em `plugin-ui`: os elementos M-específicos
  permanecem locais porque não possuem segundo consumidor.

## Gaps explícitos do perfil seguro

- `try ... otherwise` ainda não integra a gramática. O tratamento seguro
  publicado nesta fase é `RemoveRowsWithErrors` ou `ReplaceErrorValues`.
- joins `Inner`, `RightOuter` e `FullOuter` permanecem bloqueados. Somente
  `JoinKind.LeftOuter` possui semântica 1:N e limites validados.
- `Table.RowCount` produz escalar e não pode ser etapa tabular no contrato atual;
  contagem deve ser feita por agregação `Table.Group`/`List.Count`.
- detecção automática de tipo não grava mudança sem confirmação; a confirmação
  continua sendo `Table.TransformColumnTypes`.
- split está limitado a delimitador literal com `QuoteStyle.Csv`.
- append aceita somente consultas já autorizadas no DAG da requisição.

Esses itens não aparecem como suporte no registry/ribbon além do subconjunto
acima.

## Testes

- golden backend das novas famílias, registry e mutações tipadas;
- regressão de erro estruturado e tratamento explícito;
- append, fill up, transpose, distinct, índice, split e transformações escalares;
- frontend da ribbon, barra fx, transação e concorrência.

As flags de rollout continuam controlando leitura e escrita v2.
