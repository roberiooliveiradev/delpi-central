# Inteligência do chat — Onda 1

Documento operacional para implementação no `minha-delpi-ai-api`.  
**Status:** Onda 1 concluída (maio/2026). Continuação: [Onda 2](./inteligencia-chat-onda-2.md).  
**Última revisão:** maio/2026

Documentos relacionados:

- [README do roadmap](./README.md)
- [Melhorias futuras (admin)](./melhorias-futuras.md) — onda anterior, concluída
- API do chat: `docs/api/` (mensagens, anexos, agentes)

---

## Objetivo da Onda 1

Aumentar a qualidade das respostas do chat com **baixo risco** e **sem mudança de contrato HTTP** no plugin. Foco em:

1. Contexto de anexos mais confiável no prompt
2. Seleção e ranking semântico de actions OpenAPI autorizadas
3. Catálogo de actions utilizável fora dos padrões produto/LMP/SQL
4. RAG com filtro de score mínimo (menos ruído no contexto)

**Fora de escopo desta onda:** tool-calling nativo em loop, RAG híbrido, embeddings persistidos em `ai_external_actions`, alteração de modelo LLM padrão, mudanças no plugin (salvo exibir metadados já existentes).

---

## Pipeline atual (referência)

```
Mensagem → Segurança → Workspace (projeto/agente/capabilities)
         → ChatIntelligencePipelineService (decisões base: operacional, análise, contexto)
         → RAG (embedding + pgvector, até 6 chunks)
         → ChatToolContextService (tools + finalize inteligência base)
         → ChatPromptBuilderService → LLM stream
```

**Regra de arquitetura:** melhorias de inteligência (comparação, insights, contexto de ferramentas no histórico, supressão de resposta direta) ficam em serviços **base do chat** (`ChatIntelligencePipelineService`, `ChatToolContextService`, policies em `prompt_policies/`). Use cases (`Send`/`Stream`), **agentes** e **simulação admin** apenas consomem esse pipeline — não duplicar lógica por agente.

Pontos fracos que a Onda 1 corrige:

| # | Problema | Evidência no código |
|---|----------|---------------------|
| A | Anexo só aparece como nome no system prompt | `ChatPromptBuilderService.build_messages` — sem trecho do arquivo |
| B | `find_candidate_actions` retorna `[]` sem keywords produto/LMP/SQL | `postgres_external_action_repository.py` L233–234 |
| C | Action genérica usa `candidates[0]` sem ranking | `external_action_selection_service._select_generic_allowed_action` |
| D | `RAG_ASSERTIVENESS_MIN_SCORE` só no admin/métricas | `admin_routes.py`, não em `RagContextService` |

---

## Itens da Onda 1

### 1.1 — Contexto inline de anexos (`ChatAttachmentContextService`)

**Problema:** O modelo depende do RAG para “ver” o anexo. Se o chunk não subir no top‑K ou o score for baixo, a resposta ignora o arquivo.

**Solução:** Novo serviço que monta um bloco de texto **somente para o LLM** (não persistido em `toolCalls` nem exposto ao cliente com dados sensíveis).

**Comportamento:**

| Situação | Ação |
|----------|------|
| `status == indexed` e `metadata.knowledgeDocumentId` presente | Buscar chunks do documento (ordem `chunk_index`), concatenar até `CHAT_ATTACHMENT_CONTEXT_MAX_CHARS` |
| `status` pendente / `index_failed` / sem documento | Extrair texto via `ChatAttachmentTextExtractor` (mesmo fluxo do index), truncar ao limite |
| `unsupported` | Não injetar conteúdo; manter só linha informativa no prompt |
| Vários anexos | Um bloco por arquivo; respeitar orçamento global `CHAT_ATTACHMENT_CONTEXT_MAX_CHARS` total |

**Formato no system prompt** (substituir observação genérica atual):

```text
Conteúdo dos arquivos anexados nesta mensagem (use como fonte primária para esta pergunta):

### {original_filename}
{trecho}

Observação: trechos podem estar truncados; o RAG pode trazer fontes adicionais.
```

**Arquivos:**

| Ação | Arquivo |
|------|---------|
| Criar | `app/application/services/chat_attachment_context_service.py` |
| Alterar | `app/application/services/chat_prompt_builder_service.py` — parâmetro `attachment_context: str \| None` |
| Alterar | `app/application/use_cases/stream_chat_message_use_case.py` |
| Alterar | `app/application/use_cases/send_chat_message_use_case.py` |
| Alterar | `app/application/use_cases/admin_agent_simulate_use_case.py` (se receber `attachmentIds` no futuro; opcional nesta onda) |
| Alterar | `app/composition/chat_composer.py` — factory do novo serviço |
| Alterar | `app/domain/ports/knowledge_repository_port.py` |
| Alterar | `app/infrastructure/persistence/postgres_knowledge_repository.py` |

**Novo método no repositório de conhecimento:**

```python
def list_chunks_by_document_id(
    self,
    document_id: UUID,
    *,
    limit: int = 12,
) -> list[KnowledgeChunk]:
```

Implementação: `ORDER BY chunk_index ASC`, `limit` configurável.

**Settings novos:**

| Variável | Default | Descrição |
|----------|---------|-----------|
| `CHAT_ATTACHMENT_CONTEXT_ENABLED` | `true` | Liga/desliga injeção inline |
| `CHAT_ATTACHMENT_CONTEXT_MAX_CHARS` | `6000` | Teto total de texto de anexos no prompt |

**Critérios de aceite:**

- [ ] Mensagem com PDF/MD indexado: system prompt contém trecho do arquivo (não só nome)
- [ ] Anexo não indexado mas extraível: trecho aparece via extractor
- [ ] `MAX_CONTEXT_CHARS` global do chat não é ultrapassado pela soma RAG + tools + anexos (anexos entram no orçamento do `ChatPromptBuilderService` ou truncam antes)
- [ ] Metadados da mensagem no cliente continuam sem conteúdo bruto do arquivo

**Testes:**

- `tests/unit/application/services/test_chat_attachment_context_service.py`
- Ajuste em testes do `ChatPromptBuilderService` se existirem

---

### 1.2 — Ranking semântico de actions (`ExternalActionSemanticRankerService`)

**Problema:** Mesmo com candidatos, a primeira action da lista pode ser irrelevante.

**Solução:** Serviço que recebe lista de actions (dicts do repositório) + mensagem do usuário e devolve a lista ordenada por similaridade de embedding.

**Algoritmo (Onda 1 — sem migration):**

1. Normalizar mensagem (trim, max 2000 chars)
2. `embedding_gateway.embed(message)` — uma chamada
3. Para cada action (máx. `EXTERNAL_ACTION_SEMANTIC_RANK_LIMIT`, default 40):
   - Montar texto: `{method} {path} | {summary} | {description} | {operationId} | tags`
   - `embed(action_text)` — N chamadas (aceitável na Onda 1; cache em memória por `action_id` fica para Onda 2)
4. Score = cosine similarity (reutilizar fórmula de `KnowledgeSemanticDeduplicatorService` ou extrair util `cosine_similarity(a, b)`)
5. Ordenar descendente; desempate: GET antes de POST, path mais curto

**Integração:**

- `ExternalActionSelectionService._select_generic_allowed_action` — usar melhor score ≥ `EXTERNAL_ACTION_SEMANTIC_MIN_SCORE`
- `_select_sql_or_data_action`, `_select_product_action` — aplicar ranker nos `candidates` antes de escolher
- Incluir `reason` com `selectionScore` apenas no contexto interno de tool (opcional em `metadata` seguro, arredondado 2 casas)

**Arquivos:**

| Ação | Arquivo |
|------|---------|
| Criar | `app/application/services/external_actions/external_action_semantic_ranker_service.py` |
| Criar (opcional) | `app/domain/services/vector_similarity.py` — cosine entre listas float |
| Alterar | `app/application/services/external_actions/external_action_selection_service.py` |
| Alterar | `app/composition/chat_composer.py` — injetar ranker + `LocalEmbeddingGateway` |

**Settings:**

| Variável | Default | Descrição |
|----------|---------|-----------|
| `EXTERNAL_ACTION_SEMANTIC_RANK_ENABLED` | `true` | Usa ranking semântico |
| `EXTERNAL_ACTION_SEMANTIC_RANK_LIMIT` | `40` | Máx. actions embedadas por mensagem |
| `EXTERNAL_ACTION_SEMANTIC_MIN_SCORE` | `0.42` | Score mínimo para executar action genérica |

**Fallback:** Se embedding falhar (timeout/Ollama), manter ordem atual do repositório (primeiro candidato).

**Critérios de aceite:**

- [ ] Pergunta genérica com 3+ actions permitidas escolhe a mais semanticamente próxima em teste unitário com embeddings mockados
- [ ] Score abaixo do mínimo → não dispara `execute_external_action` (comportamento atual preservado)
- [ ] Fluxos produto/LMP/SQL continuam funcionando (regressão nos testes existentes)

**Testes:**

- `tests/unit/application/services/external_actions/test_external_action_semantic_ranker_service.py`
- Estender testes de `external_action_selection_service` (criar se não existir)

---

### 1.3 — Catálogo de actions: `find_candidate_actions` utilizável

**Problema:** Ramo `else: return []` impede qualquer action fora de keywords fixas.

**Solução:**

```python
def find_candidate_actions(
    self,
    query: str,
    limit: int = 8,
    *,
    allowed_action_ids: list[str] | None = None,
) -> list[dict]:
```

**Regras:**

1. Manter filtros ILIKE atuais quando mensagem contém termos produto / LMP / SQL (comportamento atual).
2. **Novo ramo `else`:** se `allowed_action_ids` não vazio:
   - `WHERE action_id IN (...)` + `enabled` + provider enabled
   - `ORDER BY path ASC`
   - `LIMIT limit` (usar até 120 na seleção, 40 no ranker)
3. Se `allowed_action_ids` vazio → `[]` (evita disparar actions globais sem agente).

**Alterar assinatura** em:

- `PostgresExternalActionRepository`
- Port do repositório (se existir; hoje é classe concreta injetada)
- Todas as chamadas em `ExternalActionSelectionService` — passar `allowed_action_ids`

**Critérios de aceite:**

- [ ] Agente com actions permitidas e pergunta “liste os pedidos abertos” retorna candidatos (não lista vazia)
- [ ] Sem `allowed_action_ids` e sem keyword → `[]`
- [ ] Com keyword produto → ainda filtra paths de produto

**Testes:**

- `tests/unit/infrastructure/persistence/test_postgres_external_action_repository_candidates.py` (mock DB ou integração leve)

---

### 1.4 — Filtro de score mínimo no RAG (`RagContextService`)

**Problema:** Chunks com similaridade baixa poluem o contexto e confundem o modelo.

**Solução:** Após `SearchKnowledgeUseCase.execute`, filtrar chunks com `score < Settings.RAG_CONTEXT_MIN_SCORE` antes de montar `context_parts`.

**Settings:**

| Variável | Default | Notas |
|----------|---------|-------|
| `RAG_CONTEXT_MIN_SCORE` | `0.35` | Pode reutilizar valor de `RAG_ASSERTIVENESS_MIN_SCORE` ou delegar: se `RAG_CONTEXT_MIN_SCORE` unset, fallback para `RAG_ASSERTIVENESS_MIN_SCORE` |

Implementação recomendada em `settings.py`:

```python
RAG_CONTEXT_MIN_SCORE = float(os.getenv("RAG_CONTEXT_MIN_SCORE", os.getenv("RAG_ASSERTIVENESS_MIN_SCORE", "0.35")))
```

**Comportamento adicional:**

- Registrar em log debug quantos chunks foram descartados (`logger.debug`)
- `sources` e `context` só incluem chunks que passaram no filtro
- Se todos filtrados → mesmo retorno de “sem chunks” (`context: ""`, `sources: []`)

**Arquivos:**

| Ação | Arquivo |
|------|---------|
| Alterar | `app/infrastructure/config/settings.py` |
| Alterar | `app/application/services/rag_context_service.py` |
| Alterar | `tests/unit/application/services/test_rag_context_service.py` |
| Alterar | `README.md` (tabela env) |
| Alterar | `docs/api/08-admin.md` — nota de que assertividade admin e filtro de chat compartilham limiar |

**Critérios de aceite:**

- [ ] Chunk score 0.20 não aparece no contexto com default 0.35
- [ ] Chunk 0.50 aparece
- [ ] Teste de regressão `test_build_context_limits_chunks_per_document` passa com scores acima do limiar

---

## Ordem de implementação recomendada

Seguir esta sequência para PRs/commits incrementais e debug mais fácil:

| Passo | Item | Motivo |
|-------|------|--------|
| 1 | **1.4** RAG min score | Isolado; testes já existem |
| 2 | **1.3** `find_candidate_actions` | Desbloqueia actions genéricas |
| 3 | **1.2** Ranker semântico | Depende de candidatos não vazios |
| 4 | **1.1** Contexto de anexos | Maior superfície (repo + prompt + use cases) |

Após cada passo: `pytest tests/unit/application/services/test_rag_context_service.py` (e testes do passo).

---

## Wiring (composition)

Em `app/composition/chat_composer.py`:

```python
def make_chat_attachment_context_service():
    return ChatAttachmentContextService(
        attachment_repository=PostgresChatAttachmentRepository(),
        knowledge_repository=PostgresKnowledgeRepository(),
        text_extractor=ChatAttachmentTextExtractor(),
    )

def make_external_action_semantic_ranker_service():
    return ExternalActionSemanticRankerService(
        embedding_gateway=LocalEmbeddingGateway(),
    )

def make_chat_tool_context_service():
    return ChatToolContextService(
        ...
        external_action_selection_service=ExternalActionSelectionService(
            PostgresExternalActionRepository(),
            semantic_ranker=make_external_action_semantic_ranker_service(),
        ),
    )
```

Nos use cases `SendChatMessageUseCase` e `StreamChatMessageUseCase`, após `_get_message_attachments`:

```python
attachment_context = ""
if self.chat_attachment_context_service and attachments:
    attachment_context = self.chat_attachment_context_service.build_context(
        user_id=user_id,
        session_id=session_id,
        attachments=attachments,
    )
# passar para prompt_builder_service.build_messages(..., attachment_context=attachment_context)
```

---

## Checklist global de conclusão da Onda 1

- [x] **1.4** `RAG_CONTEXT_MIN_SCORE` aplicado em `RagContextService`
- [x] **1.3** `find_candidate_actions` com ramo `allowed_action_ids`
- [x] **1.2** Ranker integrado em `ExternalActionSelectionService`
- [x] **1.1** `ChatAttachmentContextService` + prompt atualizado
- [x] Testes unitários novos/ajustados (`test_rag_context_service`, ranker, anexos)
- [x] `README.md` — variáveis de ambiente documentadas
- [x] Simulação admin herda filtro RAG via `make_rag_context_service()`
- [ ] Smoke manual: chat com anexo + agente com 2+ actions OpenAPI

---

## Observabilidade (opcional nesta onda)

Sem endpoint novo. Registrar em `audit` existente do chat (se já houver campo `metadata` na mensagem):

- `rag.chunksRequested`, `rag.chunksUsed`, `rag.chunksFiltered`
- `tools.externalActionSelectionScore` (quando action executada)
- `attachments.inlineChars` (tamanho injetado, não o conteúdo)

Se não couber no metadata atual, apenas log `INFO` com session_id.

---

## Riscos e mitigação

| Risco | Mitigação |
|-------|-----------|
| Latência por N embeddings de actions | `EXTERNAL_ACTION_SEMANTIC_RANK_LIMIT=40`; fallback sem ranker |
| Prompt estourar contexto | Truncar anexos + `MAX_CONTEXT_CHARS` já existente |
| Action errada com score alto | Manter `allowed_action_ids` do agente; min score; não executar POST destrutivo sem heurística extra (já existe `sensitivity` — revisar na Onda 2) |
| Duplicar texto anexo (inline + RAG) | Instrução no prompt: inline = primário; RAG = complementar |

---

## Onda 2 (preview — não implementar agora)

- Embeddings persistidos em `ai_external_actions` no sync OpenAPI
- Router LLM leve para tool/action (1 chamada curta antes do stream)
- Resumo de histórico além de `CHAT_HISTORY_MAX_MESSAGES`
- Config runtime no admin para limiares RAG/actions

---

## Comandos

```bash
cd minha-delpi-ai-api
pytest tests/unit/application/services/test_rag_context_service.py -q
pytest tests/unit -q

flask --app app.main:app db upgrade   # só se nova migration (Onda 1 não exige por padrão)
```

---

## Registro de implementação

Preencher ao concluir cada item:

| Item | PR/commit | Data | Observações |
|------|-----------|------|-------------|
| 1.4 RAG min score | (local) | 2026-05-18 | `RagContextService`, `Settings.RAG_CONTEXT_MIN_SCORE` |
| 1.3 find_candidate_actions | (local) | 2026-05-18 | Ramo `allowed_action_ids` no repositório Postgres |
| 1.2 Ranker semântico | (local) | 2026-05-18 | `ExternalActionSemanticRankerService` + composition |
| 1.1 Contexto anexos | (local) | 2026-05-18 | `ChatAttachmentContextService`, send/stream use cases |
