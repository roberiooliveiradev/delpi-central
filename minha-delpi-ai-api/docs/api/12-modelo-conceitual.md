# 12 — Modelo conceitual (entidades do Minha DELPI Chat)

Este documento define as principais entidades do ecossistema **Minha DELPI Chat** e como elas se relacionam. Para contratos HTTP, use os arquivos numerados em [`README.md`](README.md).

## Visão em camadas

```text
Usuário
  └── Sessão de chat (conversa)
        ├── Mensagens (user / assistant)
        ├── Fontes, anexos, artefatos (opcional)
        └── Agente (opcional) ── Skills (prompt)
                              └── Actions (HTTP OpenAPI)
                                    └── Providers / rotas
```

## Chat (conversa)

| Conceito | Descrição | Persistência / API |
|---|---|---|
| **Chat comum** | Conversa sem agente dedicado; políticas padrão da plataforma | `ai_chat_sessions` sem `agent_key` ou com agente default |
| **Sessão** | Thread de mensagens com histórico, pin, arquivo | `POST/GET /chat/sessions` — ver `02-chat-sessoes-mensagens.md` |
| **Mensagem** | Turno user/assistant; pode ter tool calls, fontes, apresentação rica | Stream `.../messages/stream` ou send síncrono |
| **Projeto** | Agrupador opcional de sessões e contexto | `05-projetos-fontes-anexos-artefatos.md` |

O chat resolve em runtime: permissões (`/chat/capabilities`), contexto RAG, tools/actions permitidas e skills ativas.

## Agente

Assistente configurável com identidade, prompt de sistema e capacidades.

| Campo / aspecto | Função |
|---|---|
| `key` | Identificador estável (slug) usado na sessão |
| `system_prompt` | Instruções base do personagem |
| `metadata` | Icebreakers, capabilities, **skills**, legado `allowed_actions` |
| `visibility` | `private`, `public`, `system` (oficial) |
| Actions (tabelas) | Providers e overrides de rotas por agente |

**API:** `03-agentes.md`

Duplicar agente pode copiar actions (`copyActions`); skills ficam no `metadata` exportado.

## Skill

**O que é:** módulo de **comportamento** — trechos de policy carregados no prompt quando habilitados.

**O que não é:** chamada HTTP, rota OpenAPI ou permissão de banco.

| Aspecto | Detalhe |
|---|---|
| Catálogo | Registry em código (`GET /chat/skills`) |
| Por agente | `metadata.skills.<key>.<flag>` ou API `GET/PUT .../skills` |
| Exemplo | `sql` + `authoring: true` → policy `sql-assistant-skill.md` |
| Derivado | `sqlExecutionAvailable` = action `/data/sql` habilitada (não é skill gravada) |

**API:** `11-skills.md`

**Chat comum:** skill SQL default via env `CHAT_DEFAULT_SQL_AUTHORING_SKILL`.

## Action

**O que é:** rota OpenAPI autorizada que o pipeline pode invocar (`execute_external_action`).

| Camada | Entidade | Tabela |
|---|---|---|
| Global | Provider + catálogo de rotas | `ai_external_action_providers`, `ai_external_actions` |
| Agente | Vínculo ao provider | `ai_chat_agent_action_providers` |
| Agente | Override por rota (enable, sensitivity) | `ai_chat_agent_actions` |

**API:** `04-actions-openapi.md`

Teste e logs: `POST .../actions/{actionId}/test`, `GET .../logs`.

## Provider (action)

Conjunto de rotas importadas de um documento OpenAPI (ex.: API DELPI Transforma+).

- `providerKey`, `baseUrl`, `authMode`, schema importado
- Ligado ao agente com flags `allowRead`, `allowWrite`, `allowAdmin`

## Tool (ferramenta interna)

Execução direta via `/tools` (fora do fluxo principal de chat com agente). Documentação: `07-tools.md`.

Distinto de **external action**, embora no runtime ambos alimentem `toolCalls` na mensagem.

## Knowledge (RAG)

Documentos ingeridos para recuperação semântica no contexto.

- Ingestão/busca: `06-knowledge.md`
- Fontes por agente/sessão: anexos em `05-projetos-fontes-anexos-artefatos.md`
- Knowledge operacional para rotas DELPI: `../knowledge/api-delpi-rotas-agente.md`

## Fonte, anexo, artefato

| Entidade | Uso |
|---|---|
| **Fonte** | Texto/arquivo persistente no workspace do agente ou sessão |
| **Anexo** | Arquivo enviado em uma mensagem |
| **Artefato** | Saída gerada (ex.: relatório) vinculada à sessão |

## Apresentação rica

Estrutura derivada do retorno de actions (tabela, gráfico, KPI) em `toolCalls[].metadata.presentation`, renderizada no front (`ChatRichPresentation`). Não é entidade persistida separada.

## Capabilities (resposta fixa)

Respostas determinísticas para “o que você faz?” (`ChatCapabilitiesService`), sem LLM — listam formatos suportados e distinguem skills vs actions.

## Permissões (resumo)

| Permissão | Escopo |
|---|---|
| `chat.access` | Usar módulo, listar skills catálogo |
| `chat.ask` | Enviar mensagens |
| `chat.tools.manage` | Agentes próprios, actions, skills |
| `chat.admin` | Agentes oficiais/system |

## Matriz Skills × Actions (SQL)

| Necessidade | Skill `sql.authoring` | Action `POST /data/sql` |
|---|---|---|
| Montar/mostrar/ajustar query | Sim | Não obrigatória |
| Executar e ver tabela | Recomendada (contexto) | **Obrigatória** |
| Chat comum só elaborar | Env default | Bloqueado |

## Onde implementar mudanças

| Mudança | Local típico |
|---|---|
| Nova skill | `domain/skills/chat_skill_registry.py` + `domain/prompt_policies/*.md` |
| Nova action | Import OpenAPI no provider |
| Regra elaborar vs executar SQL | `ChatSqlIntentService` + `sql-assistant-skill.md` |
| UI gestão skills | `ChatAgentSkillsPage.tsx` |
| UI gestão actions | `ChatAgentActionsPage.tsx` |
