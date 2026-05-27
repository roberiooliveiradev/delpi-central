# 11 — Skills do chat

Skills são **comportamentos de prompt** injetados no contexto do LLM. Elas orientam *como* o assistente responde (por exemplo, elaborar SQL em blocos de código). **Não** executam HTTP nem acessam bancos diretamente.

Para executar dados externos, use **Actions** (OpenAPI). Veja também [`12-modelo-conceitual.md`](12-modelo-conceitual.md).

## Catálogo global

Skills disponíveis na plataforma ficam na tabela `ai_chat_skill_catalog` e são gerenciadas pelo **admin do chat** (aba **Skills**) ou pela API admin abaixo.

Fallback: se o banco estiver vazio, o `ChatSkillRegistry` usa `app/content/pt-BR/skills/catalog.json` e policies em `app/domain/prompt_policies/*.md`.

### Admin — CRUD de catálogo

**Permissão:** `minha-delpi.chat.tools.manage` (gestores de ferramentas/agentes; aba **Skills** no admin do chat)

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/admin/skills` | Lista catálogo (`?includeInactive=false` para só ativas) |
| POST | `/admin/skills` | Cria skill |
| PUT | `/admin/skills/{skillId}` | Atualiza skill (policy, flags, ordem) |
| DELETE | `/admin/skills/{skillId}` | Desativa skill (`is_active=false`) |

Campos principais: `skillKey`, `label`, `description`, `policyContent` (Markdown), `metadataFlag`, `executionPathHint`, `executionDerivedKey`, `sortOrder`, `isActive`.

### GET `/chat/skills`

Lista o catálogo (somente leitura).

**Permissão:** `minha-delpi.chat.access`

**Resposta 200:**

```json
[
  {
    "skillKey": "sql",
    "label": "Especialista SQL",
    "description": "Elabora, explica, corrige e revisa consultas SELECT (SQL genérico); identifica erros de sintaxe quando o usuário colar SQL ou mensagens de erro.",
    "policyFile": "sql-assistant-skill.md",
    "metadataFlag": "authoring",
    "executionHint": "POST /data/sql"
  }
]
```

## Skills por agente

Configuração persistida em `ai_chat_agents.metadata.skills` (JSONB), gerenciada pela API abaixo.

### GET `/chat/agents/{agentId}/skills`

Retorna o catálogo mesclado com o estado do agente e capacidades derivadas.

**Permissão:** `minha-delpi.chat.access`

**Resposta 200 (exemplo):**

```json
[
  {
    "skillKey": "sql",
    "label": "Especialista SQL",
    "description": "...",
    "policyFile": "sql-assistant-skill.md",
    "enabled": true,
    "executionHint": "POST /data/sql",
    "derived": {
      "sqlExecutionAvailable": true
    }
  }
]
```

| Campo | Significado |
|---|---|
| `enabled` | Skill ativa para este agente |
| `derived.sqlExecutionAvailable` | Existe action habilitada cujo path contém `/data/sql` (não é armazenado; calculado em runtime) |

### PUT `/chat/agents/{agentId}/skills`

Ativa ou desativa uma skill.

**Permissão:** `minha-delpi.chat.tools.manage` (gestores de ferramentas/agentes; aba **Skills** no admin do chat) (e permissão de edição do agente; agentes oficiais exigem `chat.admin`)

**Body:**

```json
{
  "skillKey": "sql",
  "enabled": true
}
```

**Resposta 200:**

```json
{ "ok": true }
```

## Persistência em metadata

Formato canônico:

```json
{
  "skills": {
    "sql": {
      "authoring": true
    }
  }
}
```

Formato legado ainda lido: `skills.sqlAuthoring`.

## Chat comum (sem agente)

Quando não há agente selecionado, os padrões globais seguem variáveis de ambiente:

- `CHAT_DEFAULT_SQL_AUTHORING_SKILL` (default `true`) — skill `sql`

As skills ativas são aplicadas automaticamente no prompt (e no escopo RAG, quando for `company-knowledge`); o usuário não precisa pedir nem clicar em atalhos na home do chat. Configure por agente em **Skills** no builder ou pelos defaults do chat comum via env acima.
- `CHAT_DEFAULT_COMPANY_KNOWLEDGE_SKILL` (default `true`) — skill `company-knowledge` (base documental global / RAG)

Execução SQL no chat comum **não** é permitida via external actions.

### Skill `company-knowledge`

- **Comportamento:** prioriza a base documental global da empresa (políticas, diretrizes, glossário, manuais), injeta policy no prompt e controla `include_global` no escopo RAG.
- **Ferramenta relacionada:** `search_knowledge_base` (quando autorizada ao usuário).
- **Agente:** ative explicitamente em `PUT /chat/agents/{id}/skills` com `skillKey: "company-knowledge"`.

## Skill SQL — elaborar vs executar

| Intenção do usuário | Skill SQL | Action `/data/sql` |
|---|---|---|
| Montar / ajustar / mostrar query | Usada | Não deve ser acionada automaticamente |
| Executar / rodar / trazer dados | Pode complementar | Deve estar habilitada |

O seletor de actions (`ChatSqlIntentService`) evita auto-execução em pedidos de elaboração. A policy `sql-assistant-skill.md` reforça o mesmo no prompt.

## UI (plugin)

Fluxo: **Agentes → Builder → Configurar skills** (`ChatAgentSkillsPage`), espelhando a gestão de Actions.

## Relação com export/import de agente

Export/import de agente inclui `metadata` completo; skills via `metadata.skills` acompanham o pacote. Actions continuam em `actionProviders` / `actions` no export.
