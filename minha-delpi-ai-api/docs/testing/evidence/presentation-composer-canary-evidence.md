# Evidence — Presentation Composer canary (bounded rollout)

**Status:** guia operacional  
**Escopo:** `PRESENTATION_COMPOSER_CANARY=1` — authoritative **somente** se `validation.ok`  
**Pré-requisito:** shadow evidence estável (`presentation-composer-shadow-evidence.md`)

---

## 1. Habilitar canary (cohort bounded)

```bash
export PRESENTATION_COMPOSER_SHADOW=1   # recomendado manter compare
export PRESENTATION_COMPOSER_CANARY=1
```

Default produção: **ambos off** → pipeline 100% determinístico.

### Comportamento

| Condição | Resultado |
|----------|-----------|
| policy `invoke=false` | skip — sem LLM |
| flags off | `decision=invoke_flag_off` |
| LLM + `validation.ok` + canary on | `presentationComposerAuthoritative=true`, re-apply PI + rebuild renderPlan |
| LLM fail / invalid JSON / validation fail | `policy.fallback=true`, slots determinísticos preservados |

Código canônico: `PresentationSpecComposerApplicationService.apply_shadow_or_canary`.

---

## 2. Rollback

### Rollback imediato (sem redeploy de código)

```bash
unset PRESENTATION_COMPOSER_CANARY
# opcional: unset PRESENTATION_COMPOSER_SHADOW
```

Reiniciar pods/containers. Efeito: próximo turno volta ao binder determinístico; mensagens já persistidas mantêm metadata histórica.

### Rollback com evidência

1. Congelar runs com `presentationComposerAuthoritative=true`;
2. Comparar vs baseline heatmap/labels (smoke inprocess);
3. Registrar incidente em `docs/testing/evidence/runs/.../summary.json`;
4. Manter canary off até novo candidate PASS.

**Proibição:** rollout 100% imediato; big-bang delete do path determinístico.

---

## 3. Guard `validation.ok`

Testes canônicos:

- `tests/unit/domain/services/test_presentation_intelligence_orchestrator.py::test_canary_fallback_keeps_deterministic_when_composer_fails`
- `tests/unit/domain/services/test_presentation_intelligence_orchestrator.py::test_canary_authoritative_only_when_validation_ok`

Invariante:

```text
presentationComposerAuthoritative = true
  ⟹ presentationComposerShadow.ok = true
  ⟹ presentationComposerPolicy.fallback = false
```

---

## 4. Métricas canary

| Métrica | Definição |
|---------|-----------|
| `canary_authoritative_rate` | authoritative / invocações com ok |
| `canary_user_visible_change_rate` | renderPlan/slot diff vs shadow-only |
| `canary_regression_rate` | smoke T1–T5 FAIL pós-canary |

Coletar junto com telemetria § `presentation-intelligence.md` (sem rows/prompt).
