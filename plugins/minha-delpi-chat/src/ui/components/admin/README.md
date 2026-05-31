# Admin Minha DELPI Chat

A área admin é organizada por **6 seções** no topbar, cada uma com **sub-abas** quando aplicável. Deep links em `navigation/adminNavigation.ts` e `navigation/chatRoutes.ts`.

## Estrutura

| Seção | Sub-abas | Pasta principal |
|-------|----------|-----------------|
| **Painel** | — | `overview/` (+ `rbac/` no painel) |
| **Conhecimento** | Documentos, Diretrizes, Comportamentos | `knowledge/`, `guidelines/`, `skills/` |
| **Agentes** | Especialização, Simulação | `agents/`, `simulate/` |
| **Qualidade** | Métricas, Avaliações | `metrics-tab/`, `evaluations/` |
| **Plataforma** | Ferramentas, Inteligência | `tools/`, `platform/` |
| **Governança** | Segurança, Auditoria | `security/`, `audit/` |

- `shell/`: topbar (6 abas + ícones), sub-nav, **status strip** (erro/sucesso, última atualização), menu mobile.
- `shared/`: `AdminSectionLinks` (cross-links entre abas relacionadas), formulários compartilhados.

Notificações de plataforma ficam no **Portal** (`/admin` → aba Notificações), não neste plugin.

## Navegação

- Default: `/apps/minha-delpi-chat/admin` → **Painel** (não Conhecimento).
- Legado: props `initialTab` / rotas antigas remapeadas; em DEV o console avisa depreciação.
- Builder de agentes: lista em `/apps/minha-delpi-chat/agentes`; configuração em `/agentes/:id/configurar`. Atalhos na aba **Agentes → Especialização**.

## Cross-links (Fase 4)

- **Governança:** Segurança ↔ Auditoria.
- **Agentes:** Especialização ↔ Builder ↔ Simulação.

## Regras

1. Não colocar CSS de aba dentro de `ChatAdminPage.css`.
2. `ChatIntelligenceSettingsPanel` permanece em **Plataforma → Inteligência** e também em **Qualidade → Métricas** (paridade com o admin anterior).
3. `AdminRbacPanel` aparece no **Painel** e em **Plataforma → Ferramentas** (como antes do Playbook 11).
4. Barra **Acesso direto** com as 10 abas planas originais, além das 6 seções.
4. Contratos em `data/api/adminApi.ts` e `adminTypes.ts`; API em `minha-delpi-ai-api/docs/api/08-admin.md`.
