# Changelog — `viewIntent` e modo Automático (apresentação)

**Data:** jun/2026  
**Escopo:** decisão de formato no chat base quando o usuário não escolhe Tabela/Gráfico/Texto explicitamente.  
**Motivação:** listagens operacionais (ex.: programação de produção do dia) caíam em gráfico vazio por catch-all de path (`/production/` → `kpi_series`) e heurística tabular genérica.

---

## Entregas

| Camada | Mudança |
|--------|---------|
| `ChatPresentationDataShapeAnalyzer` | Campo `viewIntent` (`auditable_list`, `ranking`, `temporal_series`, `table_only`, …) |
| `ChatPresentationViewIntentService` | Orquestra shape + perfil + mensagem; `prefers_table_for_automatic()`, `automatic_score_deltas()` |
| `ChatPresentationDecisionService` | Respeita `viewIntent` e perfil antes de favorecer chart no Automático |
| `presentation_profiles.json` | `entitySetProfileContracts`, `pathRules` específicas, `noChartEntities`, `chartPolicy: skip` em listagens |
| `presentation_vocabulary.json` | `automaticScoreMarkers` (listagem vs ranking na mensagem) |
| `ChatPresentationCoverageService` | `find_entity_set_profile_gaps()` integrado em `audit_presentation_coverage.py --check-profiles` |

---

## Prioridade no Automático

1. Preferência explícita do usuário (toolbar / mensagem)
2. Perfil JSON (`chartPolicy`, `defaultViewPolicy`)
3. `dataShape.viewIntent`
4. Marcadores de mensagem (`automaticScoreMarkers`)
5. `presentationDecision.scores`

---

## Documentação

- Checklist rota nova: [new-api-route-checklist.md](../architecture/new-api-route-checklist.md)
- Pipeline e serviços: [chat-intelligence-base.md](../architecture/chat-intelligence-base.md) (Playbook 09)
- Contrato metadata: [chat-assistant-content-presentation.md](../architecture/chat-assistant-content-presentation.md)
- Playbook: [playbook-09-apresentacao-rica.md](../roadmap/playbook-09-apresentacao-rica.md) (caso P17)

---

## Testes e CI

```bash
cd minha-delpi-ai-api
.venv/bin/python scripts/audit_presentation_coverage.py --check-profiles
.venv/bin/python -m pytest tests/unit/domain/services/test_chat_presentation_view_intent_service.py -q
.venv/bin/python -m pytest tests/unit/domain/services/test_chat_presentation_decision_scores.py -q
```

Homologação: [presentation-homologation-jun2026.md](../testing/presentation-homologation-jun2026.md).
