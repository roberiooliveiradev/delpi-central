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
| S2 arggen | **benchmark executado + causa-raiz provada** (pydantic-ai 2.60.0, `_s2_ab_benchmark.py` em `bd229c9a28`+`0c5bd4a1f2`) | PROVA tools/list clara: `topic` é `anyOf[string,null]` — free-string; enum `summary\|actor\|catalog\|schema\|persona` só na description. Pydantic-ai produz tipos válidos mas inventa discriminadores → NOT_ADOPT nesta fronteira. **PRÓXIMO FIX owner-side:** tools são registrados por decorator `@mcp.tool` com signature `topic: str` → schema gerado da assinatura. Trocar para `Literal["summary","actor","catalog","schema","persona"] \| None` no server.py de cada owner publica o enum no inputSchema (sem enum hardcoded na DÉLIA). Aplica-se a: clara `topic`, caio `topic`, eva/teo `analysis_type`, suri `analysis`. Próxima ação: editar signatures + rebuild + tools/list verify + rerun benchmark. |
| S3 subobjetivos | não iniciado | modelo de estado `subobjective(id,goal,deps,evidence_needed,state,attempts,evidence_refs,gaps)` reutilizando `GoalEvidenceJudgment`/`Work` existentes — TO_INVENTORY primeiro |
| S4 paralelismo | não iniciado | `Send`+reducers no `langgraph_engine`; benchmark vs fan-out custom (latência/tokens/coverage) |
| S5 checkpoint | não iniciado | `SqliteSaver` no composition root, thread/investigation-scoped; prova interrupt→restart→resume; sem tokens/CoT persistidos |
| S6 evidência | não iniciado | rubrica por subobjetivo `SATISFIED/PARTIAL/UNSUPPORTED/CONTRADICTED` no avaliador; golden tests catálogo/clarificação ≠ PASS |
| Integração | pendente | full regression + interop A–F + 10 cenários E2E + rollback |

## Comandos de retomada (ordem)

```bash
cd /home/analistaptd/projetos/delpi-central && git status && git rev-parse HEAD
docker ps | grep -E "delia|commercial|controllership|supplies|engineering|transformometro|tv-dashboard|keycloak"
# re-verificar envelopes: python3 -c probe get_context clara (task36)
# bateria doc211: CORPUS_SET=doc211 python3 scripts/local_orchestration_reliability_eval.py 1 (delia-t21-main)
```

## Workstreams concorrentes ativos (não tocar)

- `supplies-api` SURI V10 G7 (conflicts parciais no worktree).
- `tv-dashboard-api` VISTA DI-series.
- `.worktrees/` e `api-delpi/api-delpi/` locais.

`PRODUCTION_DEPLOY=NO`; `BUSINESS_WRITES=0`; `FABRICATIONS=0`.
