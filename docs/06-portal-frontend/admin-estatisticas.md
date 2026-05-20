# Portal — Admin: Estatísticas

> **Código:** `portal/src/ui/admin/tabs/StatsTab.tsx`  
> **API:** `GET /core-api/admin/statistics` (`adminApi.getAdminStatistics`)

---

## 1. Aba Estatísticas

Primeira aba do `/admin`, pensada como **painel executivo** antes das telas operacionais.

| Bloco | Conteúdo |
|-------|----------|
| KPIs | Totais de usuários, apps, papéis e grupos |
| Gráficos (donut + barras) | Usuários, adoção de apps, notificações, rankings RBAC |
| Painéis 2×2 | Detalhes por domínio com visualização em barras |
| Aplicações — uso | **Quem** está em cada app agora (nome/e-mail), top 30 dias, **apps fantasmas** |
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
