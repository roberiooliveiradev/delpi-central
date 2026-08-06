# Portal Comercial — UX polish e evolução de tarefas (ago/2026)

> **Status:** UX Home + Meu dia + Carteiras **entregues** · backlog de tarefas CRM documentado (não implementado além do MVP Wave G+)  
> **Relacionados:** [DESIGN-IA-COMERCIAL.md](./DESIGN-IA-COMERCIAL.md) · [IMPLEMENTATION-PLAN.md](./IMPLEMENTATION-PLAN.md) · [HOMOLOGACAO-WAVE-G.md](./HOMOLOGACAO-WAVE-G.md) · [DATA-MODEL.md](./DATA-MODEL.md) § 4.1 · [API-ROUTES.md](./API-ROUTES.md) § 3.6 / attachments

Documento canônico das **melhorias de UI** pós–Wave G+ e do **roadmap de tarefas/follow-ups** alinhado ao mercado (HubSpot / Pipedrive / Salesforce).

---

## 1. Melhorias UX entregues (pós Wave G+ P1)

### 1.1 Shell e kit (`plugin-ui` + `commercial`)

| Entrega | Onde | Nota |
|---------|------|------|
| `PageHero` (linguagem SI / IGD) | kit + Início + Meu dia + Carteiras | Eyebrow, título accent, descrição, highlights, badge |
| `TopBar` flush | kit | Sem banda `--surface`; sticky transparente |
| `ViewTransition` | kit | Fade/slide na troca de tela e de bucket |
| `UnderlineNav` suave | kit | Transições hover/ativo ~220 ms |
| `SimpleKpiCard` clicável | kit | `onClick` → deep link |

### 1.2 Início (`HomePage`)

| Antes | Depois |
|-------|--------|
| Barra de chips sob a nav (duplicava hero/KPIs) | Removida; **Atualizar** só em “Seus números” |
| Hero com highlights estáticos | Highlights **vivos** via `HomeHeroMetricsContext` (follow-ups, valor, atrasos) |
| Atalhos + Analytics + nav (3 caminhos) | Sem Atalhos; Analytics = deep links externos (Dashboard, Propostas) |
| Equipe: CTA duplicado + empty alto | Um CTA; empty `state-box--compact` |
| KPIs só leitura | Clicáveis → pedidos (`?stock=` / `?focus=late`) e Meu dia (`?bucket=`) |
| Alertas “vazio heróico” | Empty compacto; warning/danger com fundo |
| Gestão: botões no rodapé da Equipe | “Ver no Dashboard” no header + KPIs → BI |

Ordem canônica: **Atenção → Seus números → Gestão/Equipe (admin) → Analytics**.

### 1.3 Meu dia (`MyDayPage`)

| Antes | Depois |
|-------|--------|
| Só SectionCard + pills ActionButton + help por chip | `PageHero` com contagens vivas + badge |
| Empty alto | Compacto + CTA **Criar follow-up** (scroll/foco no form) |
| Buckets com HelpTooltip em cada botão | `ScopeChipBar` (ajuda na seção) |
| Form em grid genérico | Grid 2 colunas; título full-width; foco visual em deep link |
| Troca de fila sem transição | `ViewTransition` por bucket |

### 1.4 Carteiras (`SellerPortfoliosPage`)

| Antes | Depois |
|-------|--------|
| Quatro cards empilhados, mesma hierarquia | `PageHero` (Admin) com totais vivos + badge |
| Empty alto sem CTA | Compacto + CTA **Criar carteira** (scroll/foco no form) |
| Sem filtro | `ScopeChipBar` Todas / Ativas / Inativas |
| Form create/transfer em `cm-form-grid` solto | Grid 2 colunas (`cm-portfolios-form`) |
| Gerenciar sem empty de seleção | Empty compacto + `ViewTransition` ao trocar carteira |
| Sem Atualizar na lista | Atualizar no header da seção Carteiras |

Ordem canônica: **Hero → Lista (filtro) → Nova carteira → Editar (condicional) → Gerenciar → Transferir**.

---

## 2. Tarefas / Meu dia — o que existe hoje (MVP)

**Decisão Wave G+:** Meu dia = **fila do próprio usuário** (activity queue própria), não CRM de equipe completo.

| Capacidade | UI Meu dia | API / banco | Nota |
|------------|------------|-------------|------|
| Título, tipo, prazo, prioridade, cliente | Sim | Sim | Prazo default = hoje EOD |
| Concluir / Adiar +1 dia | Sim | Sim | |
| Deep link Conta → form | Sim | — | `?createTask=1&customer_*` |
| Buckets atrasadas / hoje / depois | Sim | worklist | |
| **Responsável** | Sempre **você** | `assignee_user_id` = caller na create | Sem picker |
| **Reatribuir** | Não | Spec `POST /tasks/{id}/reassign` | Não implementado no código Wave G |
| **Observação / description** | Não no form | Coluna + body `description` no create | **API pronta; UI não expõe** |
| **Anexo** | Não | Spec `/attachments` | Fora da wave; storage persistente obrigatório |
| Checklist / subtarefas | Não | Spec `task_dependencies` | Futuro |
| Lembrete / recorrência | Não | — | Mercado sim |
| Convidados / local / calendário busy | Não | — | Pipedrive meetings |

Referência de mercado usada na análise: HubSpot Tasks (Assigned to, Notes, associations, reminders), Pipedrive Activities (owner, note, description, link deal/person), Salesforce Task/Event (assignee + related record + notes).

---

## 3. Evolução proposta (backlog)

Prioridade alinhada a valor × esforço e ao que já existe no contrato.

### P0 — Observação (rápido)

- Campo **Observação** (`description`) no form Nova tarefa (`CommercialTextAreaField`).
- Exibir trecho/resumo na `WorklistItem` / meta da fila.
- Teste API já cobre create com description se aplicável; regressão MFE mínima.
- **Não** exige migration nova.

### P1 — Responsável / equipe

- Picker **Responsável** (default = eu; opções = usuários da equipe / carteiras geridas).
- Implementar `reassign_task` + listagem “tarefas da equipe” (gestão) se permissão.
- RBAC: `followups.manage` + escopo de equipe; não permitir reassign sem manage.
- Atualizar worklist: “Minhas” vs “Equipe” (chip) para supervisor.

### P2 — Anexos

- `POST/GET/DELETE /attachments` ligados a `task` (e depois conta).
- Volume Compose persistente (`persistent-upload-storage`).
- UI: upload no form + lista na tarefa / Conta 360.
- Limites e tipos MIME em content JSON / config.

### P3 — Paridade CRM (depois)

| Item | Referência mercado | Nota Delpi |
|------|-------------------|------------|
| Reminder (e-mail/push antes do due) | HubSpot | Depende de outbox/notificação |
| Checklist / subtarefas | HubSpot / Asana-like | `task_dependencies` |
| Recorrência | HubSpot | Nova regra + job |
| Meeting: local, guests, busy/free | Pipedrive | Só se calendário entrar no escopo |
| Auto-tasks (pedido atrasado → follow-up) | HubSpot workflows | “Start tasks” já no backlog Wave G |
| Sequências / cadências | HubSpot Sequences | Spec P2 em API-ROUTES |

---

## 4. Fora de escopo (explícito)

- Substituir Meu dia por inbox multi-canal (e-mail/WhatsApp nativo).
- Analytics de produtividade de tarefas no Início (permanece deep link BI).
- Anexos em `/tmp` ou sem volume — **proibido**.

---

## 5. Critérios de aceite (quando implementar)

| Entrega | Aceite |
|---------|--------|
| P0 Observação | Criar com texto longo; aparece na fila; sobrevive reload |
| P1 Responsável | Criar para outro; destinatário vê na worklist; audit/reassign |
| P2 Anexos | Upload → metadado + binário no volume; download após recreate do container |

Homologação visual continua em [HOMOLOGACAO-WAVE-G.md](./HOMOLOGACAO-WAVE-G.md).
