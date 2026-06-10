# Homologação — apresentação, RAG e assertividade (jun/2026)

Checklist unificado para validar a generalização de apresentação nas 130 rotas, a calibração RAG e o monitoramento de assertividade em produção/homologação.

## Pré-requisitos

- API `minha-delpi-ai-api` e `api-delpi` no ar.
- Usuário com permissão `chat:admin`.
- Baseline OpenAPI atualizado (`api-delpi/app/content/openapi_baseline.json`).

## 1. Cobertura estática de apresentação

```bash
cd minha-delpi-ai-api
python scripts/audit_presentation_coverage.py
```

**Metas (baseline jun/2026):**

| Métrica | Meta |
|---------|------|
| `tierBPlusRatio` | ≥ 0.60 (subir rotas tier C → B) |
| `profileCoverageRatio` | 1.0 |
| `entityRoutedRatio` | ≥ 0.95 |
| Gaps tier A/B com `generic` | 0 |

**Admin:**

```http
GET /admin/metrics/presentation/coverage
```

Conferir `summary.metrics.tierBPlusRatio` e `summary.profileCoverageRatio`.

## 2. Preferência de formato respeitada (runtime)

Após tráfego real ou smoke no chat:

```http
GET /admin/metrics/presentation/summary?hours=168
```

| Campo | Interpretação |
|-------|---------------|
| `sessionFormatRespectedRatio` | ≥ 0.80 quando `explicitPreferenceTurns` ≥ 10 |
| `viewSwitchRate` | < 0.45 (alerta se maior) |
| `switchToTableRate` | < 0.50 após troca de vista |

**Smoke manual (5 casos):**

1. Estoque produto → pedir «em tabela» → `selected=table`, `formatRespected=true`.
2. Estrutura → pedir «em árvore» → `selected=tree`.
3. KPI supplies CPV → resposta com `kpi` ou `line_chart` primário.
4. «Só texto» após consulta operacional → `selected=text`.
5. Canvas/desenho → `selected=canvas` quando disponível.

## 3. Calibração RAG

**Produção CPU (`.env` recomendado):**

```env
RAG_CONTEXT_MIN_SCORE=0.40
RAG_IDENTITY_QUESTION_MIN_SCORE=0.22
CHAT_RAG_HYBRID_ENABLED=false
CHAT_RAG_PREFER_KEYWORD_SEARCH=true
CHAT_RAG_RERANK_ENABLED=false
CHAT_OPERATIONAL_FAST_PATH_ENABLED=true
```

**Admin — Teste RAG (10–15 perguntas):**

| # | Pergunta | Esperado |
|---|----------|----------|
| 1 | O que é o Delpi Central? | Chunks ≥ 1, score ≥ min |
| 2 | Como funciona o chat operacional? | Contexto documental |
| 3 | Quem é você? | Identidade (score identidade 0.22) |
| 4 | Política de estoque | Rota ou RAG coerente |
| 5 | OTD de suprimentos | KPI/série, não texto vazio |
| 6 | PPM interno | Gráfico ou KPI |
| 7 | Estrutura do produto X | Árvore ou tabela |
| 8 | Follow-up «e na filial 02?» | Mantém produto no contexto |
| 9 | Termo interno desconhecido | Confirmação de termo (se learning ativo) |
| 10 | Pergunta fora do escopo | Resposta honesta, sem alucinar chunk |

Ajuste fino: subir `ragContextMinScore` em +0.05 se ruído; baixar −0.05 se contexto vazio.

## 4. Assertividade e memória de sessão

```http
GET /admin/metrics/session-memory/summary?hours=168
GET /admin/metrics/quality/unified?hours=168
```

**Metas:**

| Campo (`quality/unified`) | Meta |
|---------------------------|------|
| `health.assertivenessRate` | ≥ 0.70 (testes RAG admin) |
| `sessionMemory.lowAssertivenessTurns` | Tendência estável ou ↓ |
| `sessionMemory.contextLossRiskTurns` | < 15% de `memoryTurnsCount` |
| `presentation.sessionFormatRespectedRatio` | ≥ 0.80 |

**Smoke multiturn:**

```bash
pytest tests/smoke/smoke_context_assertiveness_multiturn.py -q
```

## 5. CI e regressão

```bash
pytest tests/unit/domain/services/test_chat_presentation_coverage_service.py -q
pytest tests/unit/application/use_cases/test_presentation_session_format_respected.py -q
pytest tests/unit/domain/services/test_chat_presentation_admin_metrics_service.py -q
python scripts/audit_presentation_coverage.py --validate-ci
```

## 6. Go / no-go

- [ ] `tierBPlusRatio` ≥ 0.60 no endpoint coverage
- [ ] Zero gaps tier A com perfil `generic`
- [ ] `sessionFormatRespectedRatio` monitorado em summary (não null após tráfego)
- [ ] RAG homologado com 10+ perguntas no admin
- [ ] `quality/unified` exibe blocos `presentation`, `sessionMemory`, `rag`
- [ ] Alertas de apresentação (view switch alto) revisados ou aceitos

## Referências

- [apresentacao-dados-generalizada-jun2026.md](../roadmap/apresentacao-dados-generalizada-jun2026.md)
- [rag-context-min-score-calibracao.md](../roadmap/rag-context-min-score-calibracao.md)
- [perguntas-teste-chat-jun2026.md](./perguntas-teste-chat-jun2026.md)
