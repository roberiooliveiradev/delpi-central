# Minha DELPI AI API — Documentação da API

Documentação técnica em Markdown da API `minha-delpi-ai-api`, baseada nas rotas reais do backend e nos clientes/types reais do frontend.

## Base URL

Em produção, o portal consome a API pelo gateway:

```text
/apps/minha-delpi-ai/api
```

Exemplos:

```text
GET /apps/minha-delpi-ai/api/health
GET /apps/minha-delpi-ai/api/chat/capabilities
POST /apps/minha-delpi-ai/api/chat/sessions/{sessionId}/messages/stream
```

## Autenticação

A maioria dos endpoints exige header:

```http
Authorization: Bearer <access_token>
```

Uploads multipart devem enviar apenas o header de autorização; não defina manualmente `Content-Type`, pois o browser/cliente deve montar o boundary.

## Roadmap

| Documento | Conteúdo |
|-----------|----------|
| [`../roadmap/admin-minha-delpi-chat.md`](../roadmap/admin-minha-delpi-chat.md) | Itens 1–15 do painel admin (concluídos) |
| [`../roadmap/agentes-gestao-melhorias.md`](../roadmap/agentes-gestao-melhorias.md) | Gestão de agentes — ondas 1–7 (concluídas) |
| [`../roadmap/melhorias-futuras.md`](../roadmap/melhorias-futuras.md) | Melhorias pós-roadmap (concluídas; RBAC core pendente) |
| [`../roadmap/README.md`](../roadmap/README.md) | Índice do roadmap (inteligência do chat, ondas 1–5) |

Plugin (UI): [`../../../plugins/minha-delpi-chat/README.md`](../../../plugins/minha-delpi-chat/README.md).

## Arquivos deste pacote

| Arquivo | Conteúdo |
|---|---|
| `00-visao-geral.md` | Convenções, base URL, autenticação, erros, SSE, permissões. |
| `01-health-status-capabilities.md` | Health check, status do chat e capabilities resolvidas pelo backend. |
| `02-chat-sessoes-mensagens.md` | Sessões, histórico, mensagens, streaming, pin/archive e edição. |
| `03-agentes.md` | CRUD, compartilhamento, stats, export/import, duplicate, preview e runtime no chat. |
| `04-actions-openapi.md` | Providers/actions OpenAPI, vínculo agente -> provider, rotas, teste e logs. |
| `05-projetos-fontes-anexos-artefatos.md` | Projetos, fontes, anexos e artefatos. |
| `06-knowledge.md` | Ingestão e busca na base de conhecimento. |
| [`../knowledge/README.md`](../knowledge/README.md) | Documentos prontos para anexar à inteligência do agente (ex.: rotas api-delpi). |
| `07-tools.md` | Execução de tools internas. |
| `08-admin.md` | Endpoints administrativos, métricas, LLM, auditoria e knowledge admin. |
| `09-deploy-migrations-schema.md` | Migrações, schema audit e fluxo de deploy. |
| `10-referencia-rapida-endpoints.md` | Tabela consolidada de endpoints. |

## Permissões principais

| Permissão | Finalidade |
|---|---|
| `minha-delpi.chat.access` | Acesso geral de leitura/uso do módulo. |
| `minha-delpi.chat.ask` | Envio de mensagens, fontes e anexos. |
| `minha-delpi.chat.history.view` | Histórico, quando aplicável. |
| `minha-delpi.chat.knowledge.manage` | Ingestão/gestão de conhecimento. |
| `minha-delpi.chat.tools.use` | Execução de tools/actions permitidas. |
| `minha-delpi.chat.tools.manage` | Gerenciar agentes/actions próprios. |
| `minha-delpi.chat.admin` | Administração e gestão de agentes oficiais/system. |

## Observações importantes

- O chat comum não deve executar external actions; actions ficam atreladas a agentes.
- Agentes próprios podem ser gerenciados com `tools.manage`.
- Agentes oficiais/system exigem `chat.admin` ou superadmin para criar, editar e excluir.
- O frontend deve usar `GET /chat/capabilities` para decidir exibição de botões de gestão; não deve inferir permissões pelo JWT.
