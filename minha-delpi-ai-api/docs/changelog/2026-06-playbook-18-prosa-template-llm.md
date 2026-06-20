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

## Contrato metadata

- `proseDeliveryMode`, `llmProseDecoupled`, `templateProseArchive`
- `renderPlan.segments[].source = assistantMessage` no lead LLM
- `resolve_effective_humanized_summary()` para follow-up e contexto histórico

## Gates CI

```bash
cd minha-delpi-ai-api
python scripts/audit_presentation_prose_delivery.py --check
```

Workflow: `.github/workflows/minha-delpi-ai-api-presentation.yml` (job `presentation-coverage`).

## Referências

- [`playbook-18-prosa-template-llm-desacoplamento.md`](../roadmap/playbook-18-prosa-template-llm-desacoplamento.md)
- [`chat-response-modes.md`](../architecture/chat-response-modes.md)
- Regra Cursor: `presentation-operational-decoupling.mdc`
