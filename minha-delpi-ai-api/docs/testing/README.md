# Testes — minha-delpi-ai-api

## Fonte canônica de avaliação da IA

**[`chat-ai-flow-families.md`](./chat-ai-flow-families.md)** é a única fonte de critérios para avaliar inteligência do chat.

Ela define:

- famílias F01–F24/F25+;
- dimensões **R1–R11**;
- graders determinísticos/semânticos/humanos;
- baseline × candidate;
- multiple trials;
- outcome/task success;
- safety/governance;
- efficiency/cost;
- API externa desconhecida e teste metamórfico;
- pedidos longos/compostos;
- evidência imutável de release;
- protocolo obrigatório para o Cursor.

Roadmaps, changelogs, perguntas datadas e arquivos de evidence anteriores **não definem PASS**.

---

## Camadas de teste

```text
unit/contract
→ offline eval baseline/candidate
→ live send
→ stream/simulate quando aplicável
→ UI manual quando necessário
→ release decision R1–R11
```

### Unitários

```bash
cd minha-delpi-ai-api
pytest tests/unit -q
pytest tests/unit/domain/services/test_chat_intelligence_regression.py -q
pytest tests/unit/application/services/test_external_action_selection_service.py -q
python scripts/audit_clean_architecture.py
```

Fixtures de regressão devem conter positive + sibling + negative e não podem ensinar path/operationId esperado ao runtime.

---

## Harnesses live

| Script | Uso |
|--------|-----|
| `scripts/human_interaction_battery_live.py` | Interação humana simulada, typos e multi-turn |
| `scripts/smoke_chat_flow_families_f01_f04_f03.py` | Gates rápidos de famílias críticas |
| `scripts/eval_packages_a_d_human_live.py` | Guidance/compare/dataAnswer |
| `scripts/smoke_new_intent_user_simulation.py` | SQL/new intent/deixis |
| smokes especializados | Contrato específico da feature/surface |

Exemplo:

```bash
docker exec -e SMOKE_BASE_URL=http://delpi-gateway \
  -w /app delpi-minha-delpi-ai-api \
  python scripts/human_interaction_battery_live.py
```

**Regra:** scripts são harnesses. Um `PASS` do script só é gate de release quando as `requiredDimensions` do caso foram realmente avaliadas conforme R1–R11.

---

## Evidence de release

Runs relevantes devem ser imutáveis:

```text
docs/testing/evidence/runs/
  <timestamp>_<gitSha>_<runId>/
    manifest.json
    cases.json
    summary.json
```

O manifest deve registrar pelo menos:

```text
runId
timestamp
gitSha
environment
datasetVersion
model/provider/config hash
agent config hash
OpenAPI schema hash
Action Catalog hash
trialCount
```

Execuções com `SMOKE_ONLY`/`SMOKE_FAMILY` são parciais e não substituem uma bateria completa.

---

## Mudança de inteligência

Fluxo obrigatório:

1. congelar dataset/config;
2. rodar baseline;
3. registrar bug + sibling + negative;
4. implementar causa raiz;
5. rodar candidate no mesmo corpus;
6. comparar R1–R11 e métricas;
7. executar live/surface tests;
8. rodar architecture enforcement;
9. declarar `PASS`, `FAIL` ou `INCONCLUSIVE` com evidência.

Para mudança em tools/actions, incluir API externa fictícia desconhecida e teste metamórfico.

---

## Mudança em api-delpi

1. validar contrato/OpenAPI da api-delpi;
2. `scripts/sync_api_delpi_openapi.py`;
3. confirmar Action Catalog/index atualizado;
4. testar retrieval/planner/arguments pelo OpenAPI;
5. validar outcome + apresentação;
6. executar evals R1–R11 relevantes;
7. provar que nenhuma regra técnica por endpoint foi adicionada ao core do chat.

Checklist arquitetural: [`../architecture/new-api-route-checklist.md`](../architecture/new-api-route-checklist.md).

---

## Referências vigentes

- [Protocolo canônico R1–R11](./chat-ai-flow-families.md)
- [Arquitetura de inteligência](../architecture/chat-intelligence-base.md)
- [Nova API/action](../architecture/new-api-route-checklist.md)
- [Actions OpenAPI](../api/04-actions-openapi.md)
- `.cursor/rules/ai-intelligence-evaluation.mdc`
- `.cursor/rules/openapi-first-universal-tool-routing.mdc`
