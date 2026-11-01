# 215 — Checkpoint de execução S2–S6 (doc 214 §0.5/§8)

- **Estado:** `INCOMPLETE` — handoff verificável. Nenhum gate S2–S6 declarado.
- **SHA base:** `9c50cfb580` (Doc 213 entregue). HEAD no momento do checkpoint: revalidar `git rev-parse HEAD`.
- **Entregas já incorporadas ao baseline (não re-executar):**
  - Envelopes tipados nos 6 owners (`code=ARGUMENT_VALIDATION`, `recoverable=true`) — commit `3bf75b7e94`; GREEN probe clara + `owner_argument_rejected` pelo stack real; recovery e2e provado (cmp_10: `suri.analyze` EXC→`get_context`→`analyze` COMPLETED).
  - Bateria doc211 pós-envelopes: 9/28 (EVA 0→3, TÉO 1→2, VISTA 4→0 real). Artefatos: `delia-api/.battery/task36/doc211_run1.{log,runs.json}`.
  - Diagnóstico: `owner_error` hint chega ao prompt de re-proposta (`orchestration.py:10801`); residual = arggen do modelo 4B, não plumbing.
  - Inventário + matriz de frameworks + alvo: Doc 213.

## Checkpoints por slice (doc 214 §8)

| Slice | Estado | Próximo comando/ação |
|---|---|---|
| S0 baseline/RED | parcial — baseline congelada acima | montar matriz de incidentes T34 → fixtures RED paramétricas |
| S2 arggen | **enums owner-side publicados + arggen real verde** — tools/list verificado nos 5 owners (clara get_context.topic Literal `e8573b5615` + analyze/knowledge via enum injection; caio analyze 21 + knowledge 17; eva analyze 5 + knowledge 4; teo/suri já literais). Helper `enum_constrained_parameters` em `delpi_mcp.tool_metadata`. `_s2_arggen_probe.py`: 7/7 discriminadores ∈ enum + schema_valid (`s2_arggen.json`). Fix incidente: `caio_commercial_knowledge.json` corrompido por merge commitado — resolvido upstream 4.1.1. Vocabulários abertos (get_context.topic caio/eva, suri knowledge.topic) corretamente não enumados. | bateria doc211 v2 com envs `DELIA_MCP_{CAIO,CLARA,EVA,SURI}_*` habilitados → `s2_gate_4cases_v2.log`; depois held-out + negativos + eval pela DÉLIA para fechar gate §2 |
| S3 subobjetivos | não iniciado | modelo de estado `subobjective(id,goal,deps,evidence_needed,state,attempts,evidence_refs,gaps)` reutilizando `GoalEvidenceJudgment`/`Work` existentes — TO_INVENTORY primeiro |
| S4 paralelismo | não iniciado | `Send`+reducers no `langgraph_engine` (existe em `app/infrastructure/orchestration/langgraph_engine.py`, eval-only); benchmark vs fan-out custom |
| S5 checkpoint | não iniciado | `SqliteSaver` (langgraph-checkpoint 4.3.1 instalado) no composition root, thread/investigation-scoped; prova interrupt→restart→resume; sem tokens/CoT |
| S6 evidência | não iniciado | rubrica por subobjetivo `SATISFIED/PARTIAL/UNSUPPORTED/CONTRADICTED` no avaliador; golden tests catálogo/clarificação ≠ PASS |
| Integração | pendente | full regression + interop A–F + 10 cenários E2E + rollback |

## Comandos de retomada (ordem)

```bash
cd /home/analistaptd/projetos/delpi-central && git status && git rev-parse HEAD
# HEAD esperado: ff41499261 (S2 enums owner-side) — workstreams concorrentes preservados (UU SURI ledger NÃO resolver aqui)
wsl -e docker exec delia-t21-main python3 /app/scripts/_s2_schema_probe.py caio eva clara teo suri   # re-verificar enums no wire
# bateria doc211 v2 (ENVS OBRIGATÓRIOS — container só habilita davi/teo/vista por default):
wsl -e docker exec -e CORPUS_SET=doc211 \
  -e DELIA_MCP_CAIO_ENABLED=1 -e DELIA_MCP_CAIO_BASE_URL=http://commercial-api:8000/mcp -e DELIA_MCP_CAIO_HOST_HEADER=localhost:8000 \
  -e DELIA_MCP_CLARA_ENABLED=1 -e DELIA_MCP_CLARA_BASE_URL=http://controllership-finance-api:8000/mcp -e DELIA_MCP_CLARA_HOST_HEADER=localhost:8000 \
  -e DELIA_MCP_EVA_ENABLED=1 -e DELIA_MCP_EVA_BASE_URL=http://engineering-api:8000/mcp -e DELIA_MCP_EVA_HOST_HEADER=localhost:8000 \
  -e DELIA_MCP_SURI_ENABLED=1 -e DELIA_MCP_SURI_BASE_URL=http://supplies-mcp:8000/mcp -e DELIA_MCP_SURI_HOST_HEADER=localhost:8000 \
  delia-t21-main python3 /app/scripts/local_orchestration_reliability_eval.py 1
# arggen real isolado: wsl -e docker exec <mesmos -e> delia-t21-main python3 /app/scripts/_s2_arggen_probe.py
```

## Resultado bateria doc211 v2 (SHA ff41499261, envs corretos)

`{executions:4, outcomes:{PASS:2, FAIL:2}}` — cmp_03 PASS (caio.get_context COMPLETED), cmp_05 PASS (clara.get_context COMPLETED). cmp_13/cmp_19 FAIL `GROUP_SELECTION_ERROR` com eva.*/teo.* invocados — owner correto selecionado mas nenhum cap COMPLETED: primeira investigação da próxima sessão = status do invoke (arggen→invoke→reject?) via proposals/invokes do eval (adicionar dump de invokes por cenário ou rerodar cmp_13,cmp_19 com `-v`).

## Workstreams concorrentes ativos (não tocar)

- `supplies-api` SURI V10 G7 (conflicts parciais no worktree).
- `tv-dashboard-api` VISTA DI-series.
- `.worktrees/` e `api-delpi/api-delpi/` locais.

`PRODUCTION_DEPLOY=NO`; `BUSINESS_WRITES=0`; `FABRICATIONS=0`.
