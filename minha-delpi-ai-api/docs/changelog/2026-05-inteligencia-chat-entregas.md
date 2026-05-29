# Changelog — inteligência do chat (maio/2026)

Entregas documentadas após a última atualização ampla do checklist manual (**G1–G8**, commit `bd80eb94`).

| Commit | Resumo |
|--------|--------|
| `d57f622a` | Sync GPT_instructions no RAG; bloqueio inicial de produção → `/products/search` |
| `6de28da3` | Roadmap Onda 12 — skill análise desenhos PDF (doc only) |
| `cd1047de` | Fast path SQL produção (G1–G3); download de anexos/fontes; bundle exportável do agente |
| `50edaf65` | Normas Técnicas em `company-knowledge`; intent de descrição técnica de matéria-prima |

---

## 1. SQL produção — fast path (G1–G3)

**Problema:** «quais produtos serão produzidos hoje?» ia para busca de catálogo ou RAG lento.

**Solução (chat base):**

| Componente | Função |
|------------|--------|
| `ChatSqlOperationalIntentService` | Detecta perguntas de produção/programação do dia |
| `ChatSqlProductionQueryService` | Template SQL SC2010; execução via `POST /data/sql` ou resposta direta com SQL (G3) |
| `ExternalActionSelectionService` | Fix `_resolve_data_sql_action` → action `/data/sql`, não KPI «production» |

**Comportamento:**

| ID | Pergunta | Pipeline |
|----|----------|----------|
| G1–G2 | produção / programação de hoje | Fast path + 1 tool SQL; `skipRag` |
| G3 | monte uma query… | Resposta direta com bloco SQL; sem LLM |
| G5 | busque parafuso m8 | Regressão: continua `search_products` |

**Validação:** [`../testing/smoke-operacional-manual.md`](../testing/smoke-operacional-manual.md) (G1–G8), `scripts/smoke_gpt_instructions_improvements.py`.

---

## 2. Download de fontes e anexos

**Backend:**

| Método | Path | Uso |
|--------|------|-----|
| GET | `/chat/attachments/{id}/download` | Anexo da conversa |
| GET | `/chat/sources/{id}/download` | Fonte de agente, projeto ou nota |

**Frontend (plugin `minha-delpi-chat`):** botão de download em fontes do agente, fontes do projeto e anexos nas mensagens (`downloadChatAttachment`, `downloadChatSource`).

**Doc API:** [`../api/05-projetos-fontes-anexos-artefatos.md`](../api/05-projetos-fontes-anexos-artefatos.md), [`../api/10-referencia-rapida-endpoints.md`](../api/10-referencia-rapida-endpoints.md).

---

## 3. Bundle exportável — agente `minha-delpi-chat`

**Pasta:** [`../knowledge/domains/agents/minha-delpi-chat/`](../knowledge/domains/agents/minha-delpi-chat/)

- 12 arquivos com nomes **canônicos** (`sql-data-api-instructions.md`, `drawing-rules-delpi.md`, …)
- `manifest.json` — mapeamento original → nome normalizado
- Regenerar: `scripts/export_agent_knowledge_bundle.py --agent-key minha-delpi-chat`

**Normalização:** `AgentKnowledgeFilenameService` — padrão `{categoria}-{topico}.{ext}`.

---

## 4. Conhecimento global — Normas Técnicas DELPI

**Pasta:** [`../knowledge/domains/global/`](../knowledge/domains/global/)

| Arquivo | Escopo RAG |
|---------|------------|
| `normas-tecnicas-delpi.md` | Descrição técnica de matérias-primas (grupos 1001–1025) |
| `gpt-instructions.md` | Regras gerais GPT |
| `o-arquiteto-do-codigo.md` | Identidade/plataforma |

**Sync:** `scripts/sync_gpt_instructions_knowledge.py --sync-global [--ingest-global --user-id <uuid>]`

**Intent (chat base):** `ChatTechnicalDescriptionIntentService` — «como descrever um terminal?» → RAG Normas + policy `technical-description-normas.md`; **sem** `/products/search`.

**Validação manual:** checklist **N1–N4** em [`../testing/smoke-operacional-manual.md`](../testing/smoke-operacional-manual.md).

---

## 5. Onde ler mais

| Tópico | Documento |
|--------|-----------|
| Arquitetura completa | [`../architecture/chat-intelligence-base.md`](../architecture/chat-intelligence-base.md) |
| Mapa GPT_instructions | [`../knowledge/gpt-instructions-coverage-map.md`](../knowledge/gpt-instructions-coverage-map.md) |
| Onda 12 (PDF desenhos) | [`../roadmap/inteligencia-chat-onda-12-skill-analise-desenhos-pdf.md`](../roadmap/inteligencia-chat-onda-12-skill-analise-desenhos-pdf.md) |
| Checklist manual | [`../testing/smoke-operacional-manual.md`](../testing/smoke-operacional-manual.md) |
