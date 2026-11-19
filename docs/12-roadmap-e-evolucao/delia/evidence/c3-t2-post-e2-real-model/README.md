# C3/T2 — Post-E2 real-model functional recovery evidence

TASK: `DELIA-C3-T2-POST-E2-REAL-MODEL-FUNCTIONAL-RECOVERY-01`
EVALUATED_SHA: `e09f9884ac8621b03750bd7f68524651b9aa502d` (E2 `d9f9abec4b` ancestral confirmado)
RUNTIME: container `delpi-delia-api` (working tree montado), `DELIA_ENV=development`
PROFILE: `local_ollama` → `qwen3:8b` via `http://ollama:11434/v1`, config_fingerprint `8599c328b501ecf1`, runtime_sha `30ac7cbb4467f2d4703f266a701979747857a54c`
PYDANTIC_AI: 2.50.0

## O que foi provado com modelo real

- Token de sujeito real mintado via Keycloak/gateway (realm `delpi`, client `delpi-central`, user `ti_delpi` — password re-sincronizado ao `DEV_PORTAL_PASSWORD` via admin API após re-seed do realm).
- Core platform access resolvido (`CorePlatformAccessAdapter` → actor `572e5d23-…`).
- Catálogo semântico projetado: 12 capabilities / 3 owners (api-delpi, transformometro-api, tv-dashboard-api via grupos davi/teo/vista).
- Toolsets MCP nativos compostos (`native_mcp_toolsets`, prepared() E2 path ativo).
- **Run 2**: admission model call completou em 57s → `interaction_admission decision=owner_surface class=operational` — compreensão real do modelo validada na fronteira de admissão.
- Investigação: model call não completa dentro de `provider_call_timeout_seconds=90` / `turn_budget_seconds=300`.

## Resultado real registrado (cenário A — execuções)

| run | admission | investigation | resultado |
|-----|-----------|---------------|-----------|
| 1 | timeout 60s → budget_exhausted | não completou | `turn_budget_exhausted` @713s, NON_GROUNDED, 0 governed attempts |
| 2 | ok 57s → owner_surface/operational | não completou | `turn_budget_exhausted` @390s, NON_GROUNDED, 0 governed attempts |
| 3 | ok → owner_surface/operational | **loop real engajado**: `davi.get_context(action='str')` → provider_invoke ok (256ms) → CAPABILITY_NOT_MATCHED (eligible=118); `davi.read(capability='str', arguments=None)` → `semantic_plan invalid_expected_delivery` ×2 | `turn_budget_exhausted` @311s, NON_GROUNDED |
| 4 | ok → owner_surface/operational | mesmo padrão: provider_invoke ok → CAPABILITY_NOT_MATCHED; `invalid_expected_delivery` ×3 com feedback `valid_expected_delivery` ecoado | `turn_budget_exhausted` @321s, NON_GROUNDED |

Resposta final em todas: `EpistemicClass.HYPOTHESIS` + `GroundingStatus.NON_GROUNDED` + limitation `delpi_source_unverified` + texto honesto ("nenhum dado operacional foi verificado"). **Zero fabricação; budget enforcement e honestidade epistêmica funcionaram no caminho real.**

## Fronteiras reais exercitadas (run 3)

- Compreensão real: `interaction_admission decision=owner_surface class=operational` — o modelo classificou corretamente a consulta de produto como operacional.
- Seleção de owner: o modelo escolheu o grupo `davi` (owner de domínio de produto) — seleção semanticamente correta.
- Invocação governada real: `semantic_tool_invoke → provider_invoke decision=ok capability=davi.get_context` — chamada MCP legítima end-to-end.
- `arg_type_gate` logou `action='str'` (o modelo 8b emitiu o nome do tipo como valor — fraqueza do modelo, não defeito do gate: `'str'` é string válida para `action: string`; o owner respondeu corretamente `CAPABILITY_NOT_MATCHED` com 118 elegíveis — feedback autoritativo).
- `semantic_plan` aceitar rejeitou `expected_delivery` inválido ×2 com feedback bounded (funcionando como projetado — F1/RC5).
- `usage` ausente do resultado = correto: `InteractiveTurnResult` não expõe usage; observability projection só existe com ledger bound (contrato, não defeito PKG-3).

## Causa do bloqueio (medida, não inferida)

- Ollama CPU-only (`size_vram=0`; GPU RTX 3050 presente no host mas sem nvidia-container-toolkit — runtime docker só `runc`).
- Prompt governado ~7.9k tokens → prompt processing medido ~8–19 tok/s → 7–15min por chamada vs provider timeout 90s.
- Inferência trivial: prompt 19 tokens + 20 completion = 82s (geração ~0.4 tok/s, thinking mode).
- Conclusão: hardware DEV atual não comporta o modelo configurado nos budgets do profile. Bloqueio operacional, não defeito de código.

## Determinístico (continuidade funcional)

`test_pydantic_ai_real_owner_tool_loop_rework.py` + `test_f2_native_refactor_e1{,_final,_closure}.py` + `test_interaction_continuity.py` = **133/133 PASS @ e09f9884** — P1 bounded retry, prepared() nativo, RunUsage compartilhado e contrato de paginação permanecem verdes no caminho do orchestrator real.

## Não executado (honesto)

- Cenários B/C/D, P1-live (fault injection), paginação real, multi-evidência: `TEST_NOT_RUN` — impossível sem uma chamada de investigação completável no hardware disponível.
- OpenRouter alcançável mas proibido fora de produção (dev exige hosts LLM locais — regra validada).
- Independent verification: verify.py r1 → INCONCLUSIVE (motor devin sem auth — mesmo bloqueio não-transitório de E1/E2).

## Operações de ambiente realizadas (registro)

- `delpi-core-api` + `delpi-keycloak-db`/`delpi-keycloak` estavam parados/recriados; stack sofreu recriação concorrente durante a sessão (outros agentes).
- Reset da senha do usuário dev `ti_delpi` ao valor configurado (`DEV_PORTAL_PASSWORD`) via admin API — necessário para mint de subject token.
- Warmup de `qwen3:8b` (~230s cold load, keep_alive 30m).
