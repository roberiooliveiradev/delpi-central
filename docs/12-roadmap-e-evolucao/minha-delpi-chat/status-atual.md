# Status Atual — Minha DELPI Chat

## Visão geral

O Minha DELPI Chat está em estágio pós-MVP, com release `1.0.0` publicado na branch `chat` e tag `minha-delpi-chat-v1.0.0`.

O plugin está funcional como microfrontend oficial da Minha DELPI, com backend próprio `minha-delpi-ai-api`, autenticação via Keycloak, autorização via Core API/RBAC, histórico persistido, streaming SSE, RAG documental, tools internas autorizadas, auditoria e página administrativa.

## Estado do MVP

Status: aprovado funcionalmente.

Entregas principais:

- Microfrontend React + Vite + Module Federation.
- Manifesto oficial `delpi.manifest.json`.
- Backend Flask com Clean Architecture.
- Autenticação JWT via Keycloak.
- Autorização via Core API + RBAC.
- PostgreSQL com pgvector.
- Streaming SSE.
- Sessões e histórico persistidos.
- RAG documental com fontes.
- Tools internas autorizadas.
- Auditoria.
- Admin MVP.
- Testes unitários e contratos HTTP básicos.
- Release versionada `1.0.0`.

## Produção provisória

Status: operando provisoriamente com Ollama.

A homologação produtiva com vLLM foi bloqueada no servidor `srv-api` por ausência de GPU NVIDIA detectada.

Evidências do servidor:

    lspci | grep -i nvidia
    # sem retorno

    ls -l /dev/nvidia*
    # No such file or directory

Decisão temporária:

- Usar Ollama em produção enquanto não houver host com GPU para vLLM.
- Manter a solução 100% open source/self-hosted.
- Não usar OpenAI, Azure OpenAI, Anthropic, Gemini ou serviços fechados.
- Manter vLLM como pendência de infraestrutura produtiva.

## Configuração produtiva provisória

Variáveis principais:

    LLM_PROVIDER=ollama
    OLLAMA_BASE_URL=http://ollama:11434
    OLLAMA_MODEL=qwen2.5:1.5b
    OLLAMA_TIMEOUT_SECONDS=300
    EMBEDDING_MODEL=bge-m3
    EMBEDDING_TIMEOUT_SECONDS=120
    LLM_TEMPERATURE=0.2
    LLM_MAX_TOKENS=1024

Modelos necessários no Ollama:

    qwen2.5:1.5b
    bge-m3

Comandos úteis:

    docker compose -f docker-compose.yml --env-file .env exec ollama ollama pull qwen2.5:1.5b
    docker compose -f docker-compose.yml --env-file .env exec ollama ollama pull bge-m3
    curl -s http://localhost:11434/api/tags | python3 -m json.tool

## Banco de dados

Serviço produtivo:

    postgres-plugins

Imagem obrigatória:

    pgvector/pgvector:pg15

Estado validado em produção:

- Container `delpi-postgres-plugins` usando `pgvector/pgvector:pg15`.
- Extensão `vector` instalada.
- Migrations do `minha-delpi-ai-api` aplicadas.
- Tabelas `ai_*` criadas.

Tabelas esperadas:

    ai_audit_logs
    ai_chat_messages
    ai_chat_sessions
    ai_knowledge_chunks
    ai_knowledge_documents

Validação:

    docker compose -f docker-compose.yml --env-file .env exec postgres-plugins \
      sh -lc 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "\dt ai_*"'

    docker compose -f docker-compose.yml --env-file .env exec postgres-plugins \
      sh -lc 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "select extname, extversion from pg_extension where extname = '\''vector'\'';"'

## Deploy e pós-deploy obrigatório

Após subir o backend em ambiente novo ou banco novo, aplicar migrations:

    docker compose -f docker-compose.yml --env-file .env exec minha-delpi-ai-api \
      flask --app app.create_app:create_app db upgrade

Conferir revision:

    docker compose -f docker-compose.yml --env-file .env exec minha-delpi-ai-api \
      flask --app app.create_app:create_app db current

Conferir status do provider:

    curl -s \
      -H "Authorization: Bearer $TOKEN" \
      http://localhost/apps/minha-delpi-ai/api/admin/llm/status | python3 -m json.tool

Resultado provisório esperado:

    {
      "provider": "ollama",
      "model": "qwen2.5:1.5b",
      "temperature": 0.2,
      "maxTokens": 1024
    }

## Endpoints principais

Healthcheck:

    GET /apps/minha-delpi-ai/api/health

Status LLM:

    GET /apps/minha-delpi-ai/api/admin/llm/status

Resumo admin:

    GET /apps/minha-delpi-ai/api/admin/metrics/summary

Sessões:

    GET /apps/minha-delpi-ai/api/chat/sessions
    POST /apps/minha-delpi-ai/api/chat/sessions

Mensagens:

    GET /apps/minha-delpi-ai/api/chat/sessions/:sessionId/messages
    POST /apps/minha-delpi-ai/api/chat/sessions/:sessionId/messages
    POST /apps/minha-delpi-ai/api/chat/sessions/:sessionId/messages/stream

Knowledge:

    POST /apps/minha-delpi-ai/api/knowledge/documents
    POST /apps/minha-delpi-ai/api/knowledge/search

Tools:

    POST /apps/minha-delpi-ai/api/tools/execute

## Funcionalidades já implementadas

- Chat conversacional.
- Streaming SSE.
- Histórico persistido.
- RAG documental.
- Fontes retornadas ao frontend.
- Ingestão manual de documentos.
- Listagem admin de documentos.
- Filtro/paginação admin de documentos.
- Ativação/desativação/reindexação de documentos.
- Contagem de chunks por documento.
- Auditoria.
- Tools internas com allowlist/RBAC.
- Página admin.
- Métricas administrativas.
- Testes unitários.
- Testes de integração HTTP básicos.
- Ambiente virtual local para testes (`.venv`, ignorado pelo Git).
- `pytest.ini` com `pythonpath = .`.

## Pendências técnicas

- Homologar vLLM em host com GPU NVIDIA.
- Corrigir warning de collation do banco `plugins_hub` em janela controlada.
- Garantir `EMBEDDING_MODEL=bge-m3` explícito no Compose produtivo.
- Documentar checklist final de pós-deploy em script executável.
- Criar testes de integração com banco real para RAG ativo/inativo.
- Criar testes de permissão negativa para admin/tools/sessões de outro usuário.
- Criar teste do `LocalEmbeddingGateway`.
- Criar teste de streaming com provider mockado.
- Melhorar envelope de erro no streaming para logs técnicos internos e mensagem pública segura.

## Pendências funcionais

- Filtros avançados na auditoria administrativa.
- Paginação da auditoria.
- Confirmação modal antes de desativar/reativar/reindexar.
- Upload de documentos `.txt` e `.md`.
- Importação controlada de documentação oficial do repositório.
- Evitar ou alertar duplicidade por `sourceRef`.
- Renomear conversa.
- Copiar resposta.
- Melhorar visualização de fontes.
- Feedback visual de rate limit.

## Tools operacionais futuras

Candidatas:

- `search_lmp`
- `get_lmp_details`
- `search_products`
- `get_product_structure`
- `search_transforma_mais`
- `search_quality_nc`

Critérios antes de implementar qualquer tool operacional:

- Permissão específica.
- DTO de entrada.
- Validação de entrada.
- Use case.
- Port.
- Gateway.
- Limite de resposta.
- Auditoria.
- Teste com usuário autorizado.
- Teste com usuário sem permissão.
- Sem acesso direto do LLM ao banco.

## Observabilidade futura

Já existe resumo administrativo, mas ainda falta observabilidade técnica completa:

- `/metrics` Prometheus.
- Contador por endpoint.
- Latência por endpoint.
- Erros por código.
- Latência de LLM.
- Latência de embedding.
- Contagem de tool calls.
- Dashboard Grafana.
- Alertas de 5xx e LLM indisponível.

## Segurança

Regras mantidas:

- Sem OpenAI, Azure OpenAI, Anthropic ou Gemini.
- Sem APIs proprietárias de LLM.
- LLM sem acesso direto ao banco.
- Tools com allowlist.
- Tools com RBAC.
- Logs sem token.
- Secrets fora do Git.
- Erros em envelope `errors[]` nas rotas HTTP.
- Frontend sem regra efetiva de permissão.
- Toda regra sensível no backend/Core API.

## Próxima ordem recomendada

1. Fechar commit da UI de métricas admin.
2. Garantir `EMBEDDING_MODEL=bge-m3` explícito no Compose.
3. Criar checklist/script de pós-deploy.
4. Criar testes de permissão negativa.
5. Criar paginação/filtros de auditoria.
6. Implementar primeira tool operacional: `search_lmp`.
7. Criar `/metrics` Prometheus.
8. Planejar vLLM em host com GPU.
