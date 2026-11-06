# B2 root cause — chamadas redundantes e progresso da investigação

TASK_ID: DELIA-C3-PYDANTIC-AI-B2-INVESTIGATION-PROGRESS-ROOT-CAUSE-01
Pergunta: "Quais indicadores são acompanhados na área de engenharia?"
SHA: 8018a3a1c7/HEAD | Kimi | v41 | traces /tmp/delia_dbgb2*

## Sequência cronológica (8 invokes)

| # | Tool | Args | Resultado | Info nova | Avaliação |
|---|------|------|-----------|-----------|-----------|
| 1 | teo.get_context | overview | contexto semântico TÉO | vocab/entidades | ÚTIL — entrada correta |
| 2 | davi.discover | "indicadores engenharia" | 0 candidatos | DAVI não tem indicadores | ÚTIL (descoberta honesta) |
| 3 | davi.discover | "indicador por setor engenharia" | 0 candidatos | nada novo | **REDUNDANTE** — mesma família, mesmo vazio |
| 4 | teo.read(department) | params obj filter name=engenharia | 10 registros de setores | setor_id da engenharia | ÚTIL — args tipados ok |
| 5 | teo.read(measurement) | params obj filter setor_id | **INVALID_FIELD** — setor_id não é filtro permitido p/ measurement | filtro inválido | ÚTIL parcial — erro de contrato revelado |
| 6 | teo.analyze | dashboard_strategic_indicators, setor_id | **400** — view exige filial_id+setor_id | arg faltante | ERRO — modelo adivinhou arg |
| 7 | teo.analyze | dashboard_summary_live, setor_id | dados de indicadores | panorama do setor | ÚTIL |
| 8 | teo.analyze | summary / by_family | dados/empty | complemento | MARGINAL |
| — | tool_calls_limit | — | dump de setor + result_truncated | resposta não sintetizada | **OUTCOME GAP** |

## Causas-raiz

1. **Contrato do owner TÉO (CONTRIBUTING_FACTOR)**: filtros permitidos variam
   por entidade (measurement rejeita setor_id; analyze views exigem
   filial_id) — o modelo descobre isso por tentativa-erro, queimando
   chamadas. O vocabulário de filtros existe em get_context(catalog,
   entity) mas não é consultado antes da primeira leitura.
2. **Churn do modelo (CONTRIBUTING_FACTOR)**: discover DAVI duplicado
   (mesma classe de busca, mesmo resultado vazio) e 2× analyze com arg
   errado antes de acertar → ~3 chamadas sem progresso.
3. **Budget consumido pela descoberta de contrato (ROOT_CAUSE_PROVEN)**:
   ~4/8 chamadas foram gasta aprendendo o schema de filtros do owner por
   tentativa-erro → tool_calls_limit antes da síntese → dump em vez de
   resposta composta. Não é defeito de código DÉLIA: guards corretos,
   args tipados preservados, erros devolvidos recuperavelmente.
4. **Outcome**: pergunta não respondida diretamente (dump de setor) —
   BUSINESS_OUTCOME insuficiente; TECHNICAL_SUCCESS parcial.

## Arquivos/funções

- Nenhum arquivo DÉLIA comprovado defeituoso nesta execução.
- Owner-side: contrato TÉO (filtros por entidade, required args) — fora
  do escopo de correção na DÉLIA.
- Mecanismo nativo aplicável: nenhum novo — o erro já retorna ao modelo
  via tool result; a correção natural é o modelo consultar
  get_context(catalog, entity) antes de reads filtradas (instrução/
  instrução de investigação já incentiva discovery semântico).

## Recomendação bounded para próxima task

Adicionar à projeção de observação de erro de contrato (INVALID_FIELD /
400) os campos permitidos quando o owner os devolve no payload de erro
(ex.: `fields: [...]` em INVALID_FIELD) — já retornado pelo owner, basta
não truncá-lo no _attempt_projection. Custo zero de chamadas extras.
Sem aumento de limites, sem novo planner.
