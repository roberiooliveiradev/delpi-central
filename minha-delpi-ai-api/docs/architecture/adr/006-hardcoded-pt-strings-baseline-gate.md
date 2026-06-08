# ADR 006 — Gate de strings PT (baseline)

**Status:** Aceito (jun/2026)

## Contexto

Mesmo com JSON centralizado, regressões introduziam títulos e mensagens em Python (presenter, selection, canvas). Varredura total em `app/application` geraria milhares de falsos positivos (heurísticas, docstrings, prompts internos).

## Decisão

1. Scanner `hardcoded_pt_string_scanner.py` varre **caminhos protegidos** (presenters, selection, content services).
2. Baseline versionada `tests/fixtures/hardcoded_pt_strings_baseline.json` — CI falha só em ocorrências **novas**.
3. `test_no_hardcoded_pt_strings.py` + `audit_clean_architecture.py` executam o mesmo gate.
4. Dívida conhecida (ex.: `chat_canvas_content_service`) permanece na baseline até migração para bundle.

## Consequências

- Reduzir baseline = migrar string para JSON e atualizar fixture.
- Heurísticas de roteamento em selection podem permanecer em Python (termos curtos / regex) com entrada na baseline.
- Template PR lembra: «alterou texto? atualizou `assistant/`?».
