# Evidence — Presentation Composer shadow (staging)

**Status:** guia operacional  
**Escopo:** `PRESENTATION_COMPOSER_SHADOW=1` em staging/homologação  
**Baseline:** `presentation-composer-universal-baseline.json` (imutável)  
**Candidate:** `presentation-composer-universal-candidate.json`

---

## 1. Habilitar shadow

No container/serviço `minha-delpi-ai-api`:

```bash
export PRESENTATION_COMPOSER_SHADOW=1
# CANARY permanece off nesta fase
unset PRESENTATION_COMPOSER_CANARY
```

Reiniciar o serviço após alterar env. Shadow **não** altera a UI: slots determinísticos permanecem authoritative.

---

## 2. O que coletar

### 2.1 Por turno (metadata entregue / admin debug)

| Campo | Uso |
|-------|-----|
| `presentationComposerPolicy.decision` | `skip` \| `invoke_flag_off` \| `invoke` |
| `presentationComposerPolicy.invoke` | policy gate passou |
| `presentationComposerPolicy.fallback` | true = UI manteve determinístico |
| `presentationComposerPolicy.latencyMs` | latência compose+validate |
| `presentationComposerPolicy.repairUsed` | repair JSON/schema |
| `presentationComposerShadow.ok` | validation.ok do candidato LLM |
| `presentationComposerShadow.reason` | falha (`invalid_json`, `validation_failed`, …) |
| `presentationComposerShadow.specSummary` | `{view, mark, paletteFamily, fieldCount}` |
| `presentationIntelligence.needsComposer` | ambiguidade detectada |
| `presentationIntelligence.bindConfidence` | confiança binder |
| `presentationIntelligence.specApplied` | determinístico ok antes do shadow |

**Proibido** em logs/evidence de release: raw rows, prompt completo, tokens/secrets.

### 2.2 Métricas agregadas (janela ≥ 3 dias staging)

| Métrica | Definição | Alvo inicial |
|---------|-----------|--------------|
| `composer_invocation_rate` | `decision=invoke` / turns com tabular data | medir — HIPOTESE_A_VALIDAR |
| `composer_validation_ok_rate` | `shadow.ok=true` / invocações | ≥ baseline determinístico em R5 |
| `composer_disagreement_rate` | specSummary difere do spec aplicado (view/mark/palette) | documentar, não bloquear shadow |
| `composer_latency_p95_ms` | p95 de `policy.latencyMs` | ≤ budget R8 modo Normal |
| `composer_fallback_rate` | `policy.fallback=true` / invocações | esperado alto em shadow-only |

---

## 3. Harness recomendado

```bash
cd minha-delpi-ai-api

# inprocess (sem gateway)
PYTHONPATH=. .venv/bin/python -u scripts/smoke_presentation_composer_multiview_live.py

# live HTTP (gateway + credenciais smoke)
SMOKE_PC_PHASE=http SMOKE_BASE_URL=http://localhost \
  PYTHONPATH=. .venv/bin/python -u scripts/smoke_presentation_intelligence_live.py
```

Salvar evidence em `docs/testing/evidence/runs/<timestamp>_<sha>_shadow/`:

```text
manifest.json    # env, datasetVersion, flags
cases.json       # turns + metadata composer
summary.json     # métricas agregadas
```

---

## 4. Critério para avançar a canary

Shadow **não** substitui eval R1–R11. Só avançar para `PRESENTATION_COMPOSER_CANARY=1` quando:

1. candidate gap matrix ≥ baseline nas dimensões R4/R5/R9/R10;
2. smoke T1–T5 PASS inprocess;
3. `composer_validation_ok_rate` estável (≥3 dias);
4. nenhuma regressão heatmap / labels PT-BR;
5. invocation rate dentro do budget R11 (policy skip quando `specApplied`).

Ver rollback canary: `presentation-composer-canary-evidence.md`.
