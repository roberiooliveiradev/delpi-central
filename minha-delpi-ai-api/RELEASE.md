# Minha DELPI Chat — AI API

## Versão

1.0.0

## Provider de desenvolvimento

- Ollama
- Modelo padrão: qwen2.5:1.5b

## Provider de produção

- vLLM
- Configurado por `LLM_PROVIDER=vllm`

## Escopo MVP

- Autenticação via Keycloak JWT
- Autorização via Core API + RBAC
- Sessões de chat
- Histórico por usuário
- Streaming SSE
- RAG documental com PostgreSQL + pgvector
- Tools internas autorizadas
- Auditoria
- Admin APIs
- Provider vLLM preparado para produção
