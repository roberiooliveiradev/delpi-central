# Changelog — Playbook 18: prosa template × LLM desacoplada

**Data:** jun/2026  
**Escopo:** gate canônico `ChatPresentationProseDeliveryService`, pipeline data-only, MFE render-only, CI.

## Resumo

Narrativa operacional (`summary_then_evidence`, overview de produto) passa a usar **prosa LLM** no turno; template do presenter permanece só em listagens auditáveis (playbook, KPI, factual estreito).

## Entregas

| Fase | Destaque |
|------|----------|
| P0 | Gate `template` \| `llm` \| `direct` + decouple + audit |
| P1 | Guard format service, tipos MFE, banner `responseModeEffectNotice` |
| P2 | `dataOnlyPresentation`, smoke qualidade, simulate unificado |
| P3 | `proseDeliveryByEntity/Profile/Tier/EntitySet`, métricas audit |
| P4 | MFE `renderPlan` v1-only, linhas fora da UI LLM, playbook-13 §8.7 |
| P4.4 | Desacoplamento completo — consumidores via helpers + audit `linhas` diretas |
| P5 | `llmProseEverywhere: true` — inferência substitui template/direct em todas as rotas |
| P5.1 | Kinds `operational_data`, `sql_result`, `error_recovery` + fatos SQL/erro/playbook |

## Contrato metadata

- `proseDeliveryMode`, `llmProseDecoupled`, `templateProseArchive`
- `renderPlan.segments[].source = assistantMessage` no lead LLM
- `resolve_effective_humanized_summary()` para follow-up e contexto histórico
- `should_block_template_prose_metadata()` + `resolve_humanized_lines_for_display|facts()` — consumo pós-gate

## Gates CI

```bash
cd minha-delpi-ai-api
python scripts/audit_presentation_prose_delivery.py --check
```

Workflow: `.github/workflows/minha-delpi-ai-api-presentation.yml` (job `presentation-coverage`).

Smoke live (jun/2026): `SMOKE_SCENARIO=factory_status` — `passed: true`, `templateChars: 0`, `llmProseDecoupled: true`.

## Referências

- [`playbook-18-prosa-template-llm-desacoplamento.md`](../roadmap/playbook-18-prosa-template-llm-desacoplamento.md)
- [`playbook-19-inferencia-llm-universal.md`](../roadmap/playbook-19-inferencia-llm-universal.md)
- [`2026-06-playbook-19-prosa-latencia-analyser.md`](./2026-06-playbook-19-prosa-latencia-analyser.md) — correções pós-P5 (analyser, latência, skip RAG)
- [`chat-response-modes.md`](../architecture/chat-response-modes.md)
- Regra Cursor: `presentation-operational-decoupling.mdc`
