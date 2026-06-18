# Changelog — workspace, projetos, agentes e UI do chat (jun/2026)

Entregas da sessão de melhorias **17–18/06/2026** no MFE `minha-delpi-chat` e na API `minha-delpi-ai-api`. Commits locais (`c946b97f` … `69f802f4`, branch `main`).

---

## 1. Composer e contexto

| Entrega | Detalhe |
|---------|---------|
| **Badges de contexto** | `ChatComposerContextBadges` — chips visíveis acima do input (agente, projeto, anexos, etc.) |
| **Menu `@`** | Ancorado na posição do caret; largura responsiva ao viewport |
| **Menus `@` e `+`** | Refino de itens, navegação por teclado e integração com menções de agente/projeto |
| **Testes** | `chatComposerMention.test.ts` atualizado |

**Arquivos:** `ChatInput.tsx`, `ChatComposerContextBadges.tsx`, `chatComposerMention.ts`, `useChatComposerBindings.ts`.

---

## 2. Projetos — UX e configuração

| Entrega | Detalhe |
|---------|---------|
| **Criação simplificada** | Modal de novo projeto pede apenas **nome** e **ícone** (atalhos Lucide) |
| **Configurações dedicadas** | `ChatProjectSettingsModal` — nome, descrição, ícone, instruções, agente default, fontes; substitui fluxo pesado na home |
| **Ícone nas configurações** | Mesmo picker de ícone da criação (`ChatWorkspaceIconPicker` + `normalizeProjectIcon`) |
| **Home do projeto** | Hero centralizado; botão **Gerenciar projeto** (owner) no lugar do menu `⋯`, alinhado ao padrão «Gerenciar agente» |
| **Ícones Lucide na UI** | `ChatProjectIcon` + slugs kebab-case em cards, sidebar e listagens |
| **API PATCH projeto** | Suporte a `icon` em `UpdateChatProjectRequest` |

**Arquivos:** `ChatProjectHome.tsx`, `ChatProjectSettingsModal.tsx`, `ChatProjectCreateModal.tsx`, `chatProjectIcon.ts`, `project_routes.py`, `chat_projects_use_cases.py`.

---

## 3. Colaboração em projetos (desativada)

Colaboração multiusuário (share editor/viewer, contexto compartilhado entre conversas) **não está disponível** nesta versão.

| Camada | Comportamento |
|--------|----------------|
| **Feature flag** | `PROJECT_COLLABORATION_ENABLED = False` em `app/domain/features/chat_project_collaboration.py` |
| **API** | Rotas de share retornam **501**; listagem ignora shares; `shareConversationContext` ignorado no PATCH |
| **MFE** | Seções «Compartilhamento» removidas do settings; badges editor/viewer ocultos em `ChatProjectsPage` |
| **Roadmap** | [`projetos-colaborativos-futuro.md`](../roadmap/projetos-colaborativos-futuro.md) |

---

## 4. Mover conversas soltas para projetos (drag-and-drop)

| Camada | Detalhe |
|--------|---------|
| **UX** | Arrastar conversa da seção **Conversas** (sem `project_id`) e soltar no card do projeto na sidebar |
| **MIME drag** | `application/x-delpi-chat-session-id` — `chatSessionDragDrop.ts` |
| **API** | `PATCH /chat/sessions/{id}` aceita `title` e/ou `projectId` |
| **Use case** | `UpdateChatSessionUseCase` — valida projeto via `ChatProjectRepositoryPort` |
| **MFE** | `moveChatSessionToProject` → `useChatSession.moveSessionToProject`; highlight de drop em `ChatSidebarProjectsSection` |
| **Testes** | `test_update_chat_session_use_case.py`, `chatSessionDragDrop.test.ts` |

**Fluxo:**

```text
Conversa solta (sidebar) → drag → card Projeto → PATCH { projectId }
  → sessão some de «Conversas» → aparece ao abrir o projeto
```

---

## 5. Ícones Lucide para agentes (catálogo completo)

Antes: grade fixa de **10 ícones**. Agora: mesmo padrão do **portal** (plugins).

| Entrega | Detalhe |
|---------|---------|
| **Modal** | `ChatLucideIconPickerModal` — busca, grade (até 360), preview, salva em `kebab-case` |
| **Resolver** | `lucideIconResolver.ts` — resolve qualquer export Lucide dinamicamente |
| **Render** | `ChatAgentIcon` usa resolver (fallback `bot`) |
| **Builder** | Botão «Selecionar ícone» + atalhos rápidos (`AGENT_ICON_OPTIONS`) |
| **Persistência** | Campo `icon` até 60 chars na API (slug Lucide) |
| **Testes** | `lucideIconResolver.test.ts`, `chatAgentIcon.test.ts` |

---

## 6. Modais — botões de fechar/ação centralizados

Classe canônica em `chat-modal.css`:

| Classe | Uso |
|--------|-----|
| `mdc-chat-modal-icon-btn` | Fechar (X), ações icônicas |
| `mdc-chat-modal-tool-btn` | Ações secundárias na toolbar do modal |

Modais migrados: projeto (create/settings), confirm/prompt, expand, attachment preview, help, tour, web research, arquivados, memória, inline error, sidebar mobile, canvas, `ActionTestPanel`. CSS duplicado removido dos `.css` locais.

---

## 7. Commits (ordem cronológica)

| Hash | Resumo |
|------|--------|
| `c946b97f` | Badges no composer; `ChatProjectSettingsModal`; melhorias na área de projetos |
| `6d911e41` | Menu `@` ancorado no caret com largura responsiva |
| `10257aac` | Refino dos menus `@` e `+` do composer |
| `a7b16be9` | Criação de projeto simplificada (nome + ícone) |
| `35cae7a6` | Ícones Lucide para projetos e agentes em toda a UI |
| `69f802f4` | Drag-and-drop conversa→projeto; picker Lucide agentes; modais; colaboração off; Gerenciar projeto |

---

## 8. Validação

```bash
# Frontend
cd plugins/minha-delpi-chat
npm test -- --run src/ui/chatSessionDragDrop.test.ts src/ui/utils/lucideIconResolver.test.ts src/ui/components/workspace/chatAgentIcon.test.ts
npm run build

# Backend
cd minha-delpi-ai-api
.venv/bin/python -m pytest tests/unit/application/use_cases/test_update_chat_session_use_case.py \
  tests/unit/domain/features/test_chat_project_collaboration.py \
  tests/unit/domain/services/test_chat_project_settings_service.py -q

# Containers (dev)
cd infra
docker compose -f docker-compose.dev.yml --env-file .env up --build -d --force-recreate minha-delpi-ai-api minha-delpi-chat gateway
```

**Homologação manual sugerida:**

1. Sidebar — arrastar conversa solta para um projeto; confirmar sumiço da lista «Conversas».
2. Projeto — «Gerenciar projeto» abre settings; trocar ícone e salvar.
3. Agente — builder → «Selecionar ícone» → buscar `factory` ou `microscope`; publicar e ver ícone na lista.
4. Composer — badges de agente/projeto visíveis; menu `@` alinhado ao cursor.

---

## 9. Referências

| Tópico | Documento |
|--------|-----------|
| PATCH sessão (`projectId`) | [`02-chat-sessoes-mensagens.md`](../api/02-chat-sessoes-mensagens.md) |
| Projetos (API) | [`05-projetos-fontes-anexos-artefatos.md`](../api/05-projetos-fontes-anexos-artefatos.md) |
| Colaboração futura | [`projetos-colaborativos-futuro.md`](../roadmap/projetos-colaborativos-futuro.md) |
| Ícones portal (referência) | `portal/src/ui/admin/modals/IconPickerModal.tsx` |
| Status plataforma | [`status-atual.md`](../../../docs/12-roadmap-e-evolucao/minha-delpi-chat/status-atual.md) |
