# Release MVP 1.0.0 — Minha DELPI Chat

## Identificação

- Plugin: Minha DELPI Chat
- Plugin ID: `minha-delpi-chat`
- Backend: `minha-delpi-ai-api`
- Versão: `1.0.0`
- Branch de release: `chat`

## Escopo entregue

- Microfrontend React + Vite + Module Federation
- Manifesto oficial `delpi.manifest.json`
- Backend Flask + Clean Architecture
- Autenticação JWT via Keycloak
- Autorização via Core API + RBAC
- PostgreSQL + pgvector
- Ollama em desenvolvimento
- vLLM preparado para produção
- Streaming SSE
- RAG documental com fontes
- Tools internas autorizadas
- Auditoria
- Página admin MVP
- Homologação HTTP versionada

## Permissões

- `minha-delpi.chat.access`
- `minha-delpi.chat.ask`
- `minha-delpi.chat.history.view`
- `minha-delpi.chat.admin`
- `minha-delpi.chat.knowledge.manage`
- `minha-delpi.chat.tools.use`

## Validações obrigatórias

- [ ] `python3 -m compileall app`
- [ ] `pytest`
- [ ] `npm run build`
- [ ] `curl /apps/minha-delpi-ai/api/health`
- [ ] `curl -I /apps/minha-delpi-chat/assets/remoteEntry.js`
- [ ] Script `scripts/homologacao/check-minha-delpi-chat.sh`
- [ ] Manifesto JSON válido
- [ ] Plugin registrado na Core API
- [ ] Menu aparece para usuário autorizado
- [ ] Usuário sem permissão não acessa
- [ ] Streaming funcional
- [ ] Histórico persistido
- [ ] RAG retorna fontes com documento ativo
- [ ] Tools auditadas
- [ ] Admin lista documentos e auditoria

## Critérios de segurança

- [ ] Sem OpenAI, Azure OpenAI, Anthropic ou Gemini
- [ ] LLM sem acesso direto ao banco
- [ ] Tools com allowlist
- [ ] Tools com RBAC
- [ ] Sem secrets versionados
- [ ] Erros em envelope `errors[]`
- [ ] Logs sem token
- [ ] Frontend sem regra efetiva de permissão

## Comandos de release

```bash
git commit -m "chore(chat): prepare MVP release 1.0.0"
git tag minha-delpi-chat-v1.0.0
git push origin chat
git push origin minha-delpi-chat-v1.0.0
```

## Pendências pós-MVP

- Reativação de documento pela UI
- Upload/ingestão de documento pela UI admin
- Rate limit
- Testes de integração com banco
- Homologação real do vLLM em produção
- Tools operacionais da API DELPI/TOTVS
- Melhorias de prompt para respostas mais objetivas com tools
- Filtros avançados na auditoria administrativa
- Gestão de versões/reindexação de documentos RAG

## Evidências de homologação

Preencher no momento do release:

```text
Data:
Branch:
Commit:
Tag:
Ambiente:
Usuário homologador:
Resultado geral:
Pendências bloqueantes:
Pendências não bloqueantes:
```

## Resultado esperado

O release `minha-delpi-chat-v1.0.0` deve representar o MVP funcional do Minha DELPI Chat, com chat conversacional, RAG documental, ferramentas internas autorizadas, auditoria, administração básica e preparação para produção com vLLM.

## Atualização pós-release

Após a release MVP `1.0.0`, foram adicionadas melhorias pós-MVP:

- Validação de ingestão de documentos.
- Reativação e reindexação de documentos.
- Filtros e paginação na administração de documentos.
- Contagem de chunks por documento.
- Auditoria de ingestão.
- Testes de integração HTTP.
- Plano de homologação vLLM.
- Produção provisória com Ollama por ausência de GPU NVIDIA no `srv-api`.
- Métricas administrativas.
- Ambiente local de testes com `pytest.ini`.

A pendência produtiva principal permanece a homologação do vLLM em servidor com GPU NVIDIA compatível.
