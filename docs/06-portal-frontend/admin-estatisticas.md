# Portal — Admin: Estatísticas

> **Código:** `portal/src/ui/admin/tabs/StatsTab.tsx`  
> **API:** `GET /core-api/admin/statistics` (`adminApi.getAdminStatistics`)

---

## 1. Aba Estatísticas

Primeira aba do `/admin`, com **subpáginas** internas e visual alinhado aos tokens Minha DELPI (`--primary`, `--secundary`).

| Subpágina | Conteúdo |
|-----------|----------|
| **Visão geral** | KPIs + donuts resumidos (usuários, apps, notificações) |
| **Usuários** | Online, logins, ativos/inativos |
| **Aplicações** | Quem usa cada app agora, top 30d, fantasmas, tipos |
| **Acesso RBAC** | Rankings de papéis/grupos e vínculos |
| **Notificações** | Status dos envios de campanha |

Código em `portal/src/ui/admin/stats/` (páginas em `stats/pages/`).
| Visão RBAC | Contagens de vínculos e permissões |
| Notificações | Envios de campanha (total, pendente, concluído, falha) |

Cada painel tem atalho **Gerenciar** que navega para a aba correspondente.

---

## 2. Atualização

Botão **Atualizar** recarrega o snapshot. Timestamp exibido em `generatedAt` (horário de Brasília na UI).

---

## 3. Relacionados

- [Controllers e rotas — estatísticas](../04-core-api/controllers-e-rotas.md#7-admin--estatísticas-e-presença)
- [Presença online e uso de apps (Socket.IO)](../01-arquitetura/event-driven-e-socket.md)
