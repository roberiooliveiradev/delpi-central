# Testes — minha-delpi-ai-api

> **Suíte automatizada:** `tests/unit/` (pytest)  
> **Regressão de inteligência:** `tests/fixtures/chat_intelligence_regression_cases.py`

---

## Automatizados

```bash
# Tudo
pytest tests/unit -q

# Regressão inteligência (amostra crítica)
pytest tests/unit/domain/services/test_chat_intelligence_regression.py -q

# Seleção de actions
pytest tests/unit/application/services/test_external_action_selection_service.py -q

# Inventário / escopo de fontes do projeto (jun/2026)
pytest tests/unit/domain/services/test_chat_project_sources_intent_service.py \
  tests/unit/application/use_cases/test_search_knowledge_scope_boost.py -q

# Clean architecture
python scripts/audit_clean_architecture.py
```

### Fixtures importantes

| Arquivo | Conteúdo |
|---------|----------|
| `chat_intelligence_regression_cases.py` | Casos SIMPLE_TURN, UNCLEAR, DATA_INTERPRETATION, DATE_RANGE, **PROJECT_SOURCES_INTENT**… |
| `rich_presentation_cases.py` | Apresentação rica P1–P16 |
| `api_delpi_responses/` | Payloads mock de rotas api-delpi |

---

## Smokes (scripts)

Executar **dentro do container** com DB e LLM:

```bash
docker compose -f infra/docker-compose.dev.yml exec -T minha-delpi-ai-api \
  python scripts/smoke_identity_rag.py <user_id> <session_id> "quem te criou?"

docker compose -f infra/docker-compose.dev.yml exec -T minha-delpi-ai-api \
  python scripts/smoke_gpt_instructions_improvements.py [user_id] [session_id]

docker compose -f infra/docker-compose.dev.yml exec -T minha-delpi-ai-api \
  python scripts/smoke_playbook_product_routes.py
```

| Script | Escopo |
|--------|--------|
| `smoke_identity_rag.py` | Identidade + filtro RAG |
| `smoke_gpt_instructions_improvements.py` | SQL produção, Normas, G1–G14 |
| `smoke_playbook_product_routes.py` | Rotas produto + sessão ativa |
| `smoke_web_search_planning.py` | Planejamento web search |
| `validate_stream_incremental_persistence_e2e.py` | Persistência incremental stream |

Cenários E2E declarativos: `app/content/pt-BR/assistant/smoke_e2e_scenarios.json`.

---

## Homologação manual

| Documento | Conteúdo |
|-----------|----------|
| [smoke-operacional-manual.md](./smoke-operacional-manual.md) | **Principal** — U1–U9, G1–G3, N1–N4, #70–79, persistência stream |
| [perguntas-teste-chat-jun2026.md](./perguntas-teste-chat-jun2026.md) | Perguntas por categoria |
| [smoke-operational-intelligence-e2e.md](./smoke-operational-intelligence-e2e.md) | E2E operacional |
| [smoke-api-delpi-domain-routing.md](./smoke-api-delpi-domain-routing.md) | Domínios de rota |
| [smoke-system-metadata-homologacao.md](./smoke-system-metadata-homologacao.md) | Metadados `/system` |
| [homologacao-apresentacao-rag-assertividade-jun2026.md](./homologacao-apresentacao-rag-assertividade-jun2026.md) | RAG + apresentação |
| [presentation-homologation-jun2026.md](./presentation-homologation-jun2026.md) | Modos de apresentação |
| [homologacao-docie-produto-pb15-jun2026.md](./homologacao-docie-produto-pb15-jun2026.md) | DOCIE — produto + PB15 |

---

## Memória e assertividade

```bash
# Script dedicado (quando disponível no repo)
scripts/run_memory_context_validation.sh
```

Casos: `MEMORY_CONTEXT_REGRESSION_CASES`, `CONTEXT_ASSERTIVENESS_CASES` em fixtures.

Doc: [architecture/session-memory.md](../architecture/session-memory.md).

---

## Após alterar api-delpi

1. `scripts/sync_api_delpi_openapi.py`
2. Regressão selection + presenter
3. Revisar [api-delpi-chat-intelligence-audit.md](../roadmap/api-delpi-chat-intelligence-audit.md)
4. Smoke manual de rotas afetadas

---

## Referências

- Guia dev: [development/guia-desenvolvimento.md](../development/guia-desenvolvimento.md)
- Pipeline: [architecture/chat-intelligence-base.md](../architecture/chat-intelligence-base.md)
