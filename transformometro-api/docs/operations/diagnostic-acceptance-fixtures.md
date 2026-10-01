# Diagnostic — acceptance fixtures (local dev)

**Owner:** 07 — Integration & Acceptance (execução) / 01 Backend & Domain (autoridade)
**Escopo:** local dev stack apenas — o script falha fechado fora de `localhost`.

## Estratégia

`stable semantic marker → runtime discovery → canonical create`

Fixtures são Diagnostics cujo `problem_statement` começa com
`[ACCEPTANCE-FIXTURE]`. Nenhum UUID é hardcoded: ids são descobertos em
runtime via `GET /transformometro/revisions/{revision_id}/diagnostics`.

## Setup

```bash
TOKEN="$(bash infra/scripts/get-dev-token.sh)" \
python3 transformometro-api/scripts/dev_diagnostic_acceptance_fixtures.py \
    --base-url http://localhost \
    --revision-id <dev revision uuid>
```

Garante na revision informada (todas as writes via PREPARE→COMMIT canônico):

| Fixture | Conteúdo |
|---|---|
| `[ACCEPTANCE-FIXTURE] baseline` | Diagnostic vazio (base para finding/hypothesis/conclusion flows) |
| `[ACCEPTANCE-FIXTURE] populated` | finding OBSERVED + hypothesis VALIDATED + conclusion VALIDATED com `root_cause_hypothesis_id` |

## Discovery

```bash
curl -s "$BASE/apps/transformometro-api/transformometro/revisions/$REV/diagnostics" \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.data.items[] | select(.problem_statement | startswith("[ACCEPTANCE-FIXTURE]"))'
```

## Cobertura de cenários

- **ZERO Diagnostics:** qualquer revision dev sem Diagnostics (o caso não cria dados).
- **ONE:** revision dev contendo apenas `baseline`.
- **MULTIPLE:** revision contendo os dois fixtures (ou mais).
- **Finding / Hypothesis / causal link / evidence relation / conclusion / RootCauseDesignation / STALE_EVIDENCE / REVALIDATION_REQUIRED / stale proposal / realtime conflict:** criados deterministicamente via `prepare_manage_diagnostic` + `commit_proposal` durante a execução do acceptance (não precisam estar permanentemente seedados).

## Idempotência

A segunda execução descobre os markers e não cria writes: cada passo do
populate verifica o estado atual (exists / lifecycle) antes de PREPARE.
Provado: run 2 = zero commits em 2026-10-XX (ver histórico do master pass).

## Data safety

- Dados controlados e identificáveis por marker; nunca usar revision de
  produção ou dados de negócio reais.
- Cleanup: não existe `delete_diagnostic` no domínio. Fixture é dado
  descartável identificável; se for necessário remover, é operação de DB
  local dev fora deste contrato — nunca contra produção.
- Tokens/senhas nunca são logados; `TOKEN` vem do ambiente.
