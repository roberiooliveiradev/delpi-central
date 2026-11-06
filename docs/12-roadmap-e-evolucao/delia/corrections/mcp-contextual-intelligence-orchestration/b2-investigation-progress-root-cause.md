# B2 root cause — 8 invokes, redundância e progresso

TASK_ID: DELIA-C3-PYDANTIC-AI-B2-INVESTIGATION-PROGRESS-ROOT-CAUSE-01
EVALUATED: trace tipado /tmp/delia_b2t (SHA e905fbd4aa, kimi-k3, v41)

## Sequência cronológica e utilidade

| # | Tool | Resultado | Info nova | Veredicto |
|---|---|---|---|---|
| 1 | teo.get_context | perfil do usuário | contexto | USEFUL |
| 2 | davi.discover (indicadores engenharia) | 0 candidatos | nenhuma | NO_PROGRESS — discovery semântico não resolve "indicadores" → caps |
| 3 | teo.read department | 10 setores (achou Engenharia) | setor_id | USEFUL |
| 4 | davi.discover (indicadores por setor) | 0 candidatos | nenhuma | REDUNDANT_PROVEN — segunda tentativa ~igual, 0 resultados |
| 5 | teo.read measurement | 82 medições (sem filtro efetivo) | massa bruta | PARTIAL — result amplo, não filtrado por setor |
| 6 | teo.analyze view+setor_id | 400 "exige filial_id e setor_id" | nenhuma | FAILED — contrato exige filial_id; modelo não forneceu |
| 7 | teo.analyze view only | SUCCESS 14.2s — indicadores estratégicos Engenharia | RESPOSTA | USEFUL — produziu a resposta |
| 8 | davi.discover (indicador engenharia) | 1 candidato | tardia | LATE_NO_EFFECT — dados já obtidos |

## Progresso: resposta veio de 1(7)+3+5; discovers 2/4/8 não contribuíram;
#6 falhou por contrato (filial_id ausente no input ou schema não declara required de forma visível).

## Causas-raiz

SYMPTOM A — discovers redundantes (2,4,8: 0-1 candidatos, queries
  ~sinônimas): modelo re-tenta discovery semântico que não resolve o
  vocabulário de capabilities; CONTRIBUTING_FACTOR (model churn) +
  POSSIBLE_CONTRACT_GAP: discover não mapeia "indicadores"→analyze.
SYMPTOM B — analyze #6 errou 400 filial_id: modelo omitiu filial_id;
  contrato owner exige — CONTRIBUTING_FACTOR (model arg omission +
  schema required não visível ao modelo).
SYMPTOM C — read measurement 82 itens: filtro por setor não aplicado
  efetivamente — PARTIAL.
OUTCOME: GROUNDED com answer correta via #7; limitações honestas
  (multiple_observations_without_compose, coverage_unknown,
  declared_status_overridden) — acceptor preservado.

## Fronteira divergente: TOOL SELECTION / discovery semântico — o
Agent chamou discover 3× sem progresso antes de acertar com analyze.
Não é transporte nem validação — é churn de seleção (limitação do
modelo + possível gap do discovery vocabulary). Sem código local defeituoso comprovado.

## Recomendação minimal: documentar; se quiser reduzir churn,
avaliar se discover deve ranquear caps por view/entity — decisão de
contrato, não de código local.
