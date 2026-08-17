# Portal Comercial — UX polish e evolução de tarefas (ago/2026)

> **Status:** UX Home + Meu dia + Carteiras **entregues** · **Tasks P0 + P1 + P2 entregues** · P3 backlog  
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
| Form em grid genérico | Grid 2 colunas; título + observação full-width |
| Sem notes na fila | `WorklistItem.detail` com trecho da observação |
| Só 3 tipos | Follow-up / Ligar / E-mail / Visita / To-do + filtro por tipo |
| Troca de fila sem transição | `ViewTransition` por bucket/tipo |

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

**Wave G+:** Meu dia = fila do próprio usuário. **P1 (gestão):** chips Minhas / Equipe + responsável / reassign.

| Capacidade | UI Meu dia | API / banco | Nota |
|------------|------------|-------------|------|
| Título, tipo, prazo, prioridade, cliente | Sim | Sim | Prazo default = hoje EOD |
| Concluir / Adiar +1 dia | Sim | Sim | |
| Deep link Conta → form | Sim | — | `?createTask=1&customer_*` |
| Buckets atrasadas / hoje / depois | Sim | worklist | |
| **Responsável** | Picker (gestão) / self (vendedor) | `assignee_user_id` no create | **P1 entregue** |
| **Reatribuir** | Campo Responsável em **Editar** (gestão) | `PATCH` assignee (`POST .../reassign` ainda na API) | UI unificada no Editar |
| Fila equipe | Chips Minhas / Equipe + filtro responsável | `GET /me/worklist?scope=team` | **P1 entregue** |
| **Observação / description** | Sim (form + card) | Coluna + create + activity body | **P0 entregue** |
| Filtro por tipo | Sim | Client-side na worklist | Padrão Pipedrive/HubSpot |
| Tipos Ligar/E-mail/Visita | Sim | `task_type` | Alinhado ao DATA-MODEL |
| **Anexo** | Prévia no card; gestão em Nova/Editar | `/attachments` + volume | **P2 entregue** |
| **Editar tarefa** | Form colapsável (campos + anexos + responsável) | `PATCH /tasks/{id}` | Só o **criador** |
| **Excluir tarefa** | Botão Excluir + confirm | `DELETE /tasks/{id}` (soft delete) | Só o **criador** |
| **Adiar** | +1 dia | `POST .../defer` | Só o **criador** |
| **Concluir** | Botão Concluir | `POST .../complete` | Responsável (ou gestor da equipe) |
| **Realtime worklist** | WS invalida fila + toast in-app (Meu dia / Início) | `GET /commercial/realtime/ws` | Entregue ago/2026 |
| **Tarefas concluídas na UI** | Chip **Concluídas** (somente leitura) | `GET /me/worklist/done` | **Entregue ago/2026** |
| Checklist / subtarefas | Não | Spec `task_dependencies` | Futuro |
| Lembrete / recorrência | Não | — | Mercado sim |
| Convidados / local / calendário busy | Não | — | Pipedrive meetings |

Referência de mercado usada na análise: HubSpot Tasks (Assigned to, Notes, associations, reminders), Pipedrive Activities (owner, note, description, link deal/person), Salesforce Task/Event (assignee + related record + notes).

---

## 3. Evolução proposta (backlog)

Prioridade alinhada a valor × esforço e ao que já existe no contrato.

### P0 — Observação + fila CRM (entregue ago/2026)

- Campo **Observação** (`description`) no form Nova tarefa.
- Trecho da nota na `WorklistItem` (`detail`).
- Tipos alinhados ao mercado: Follow-up / Ligar / E-mail / Visita / To-do.
- Filtro por tipo na fila (padrão Pipedrive/HubSpot).
- Create grava nota no histórico de atividade da conta.
- Teste: `test_create_task_persists_description_in_worklist_and_activity`.

### P1 — Responsável / equipe (entregue ago/2026)

- Picker **Responsável** no create (default = eu; opções = carteiras ativas).
- `POST /tasks/{id}/reassign` + UI **Reatribuir** (só gestão / `seller-portfolios.manage`).
- Worklist `scope=mine|team` + filtro `assignee_user_id`; chips Minhas / Equipe no Meu dia.
- Complete/defer: assignee **ou** gestor da equipe do assignee.
- Destino de create/reassign deve ter carteira ativa.
- Testes: `test_create_and_reassign_team_task`, RBAC `reassign_task_*`.

### P2 — Anexos (entregue ago/2026)

- `POST/GET/DELETE /attachments` ligados a `task` (`owner_type=task`).
- Volume Compose `commercial-attachments` (`persistent-upload-storage`).
- UI Meu dia: anexo opcional na criação + lista/baixar/remover na linha.
- Limites: 10 MB; PDF, imagem, TXT, Word, Excel.
- Migration `V004__attachments.sql`.
- Testes: `tests/test_attachments_use_case.py`.

### P3 — Paridade CRM (depois)

| Item | Referência mercado | Nota Delpi |
|------|-------------------|------------|
| Reminder (e-mail/push antes do due) | HubSpot | Depende de outbox/notificação |
| Checklist / subtarefas | HubSpot (pedido frequente) | `task_dependencies` |
| Recorrência | HubSpot | Nova regra + job |
| Meeting: local, guests, busy/free | Pipedrive | Só se calendário entrar no escopo |
| Auto-tasks (pedido atrasado → follow-up) | HubSpot workflows | “Start tasks” já no backlog Wave G |
| Sequências / cadências | HubSpot Sequences | Spec P2 em API-ROUTES |
| **Realtime worklist (WS)** | HubSpot live board | **Entregue ago/2026** — invalidação + refetch Meu dia/Início |

### 3.1 Tarefas concluídas na UI (entregue ago/2026)

**Antes:** ao **Concluir**, a tarefa sumia da fila Meu dia (só restava no banco / activity da conta).

**Agora:**

| Camada | Comportamento |
|--------|----------------|
| Banco `commercial.tasks` | `status=done`; `completed_at` preenchido |
| Worklist aberta `GET /me/worklist` | Só `status=open` (atrasadas / hoje / depois) |
| Histórico `GET /me/worklist/done` | Até 100 concluídas, `completed_at` DESC; `scope=mine\|team` |
| UI Meu dia | Chip **Concluídas**; cards somente leitura (Abrir conta + anexos em prévia) |

Deep link: `?bucket=done`. Filtro por período (hoje / 7 dias) permanece backlog opcional.

---

## 4. Fora de escopo (explícito)

- Substituir Meu dia por inbox multi-canal (e-mail/WhatsApp nativo) — ver também § 6 (E7).
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

---

## 6. Backlog futuro — carteiras E7 (fora do ciclo E1–E6)

Itens de mercado **não** entregues com o MVP multi-membro / E6. Registrados aqui para priorização futura; **não** iniciar implementação sem plano dedicado.

| ID | Tema | Problema de produto | Dependências / notas |
|----|------|---------------------|----------------------|
| E7.1 | Mapa de territórios | Visualizar clientes/carteiras em mapa; desenhar polígonos | Geo no cadastro TOTVS/SA1; lib de mapa no MFE; RBAC manage |
| E7.2 | AI carve | Sugerir redistribuição equilibrando carga/região | Usa `load-summary` TOTVS (open_value/atenção) + política de aceite humano |
| E7.3 | Rotate de leads | Round-robin / rotação periódica de contas novas | Regras Comercial + audit; não misturar com owner estático |
| E7.4 | Inbox e-mail compartilhado | Caixa da carteira (não só tarefas Meu dia) | Integração e-mail; volume persistente; ≠ WhatsApp nativo |

Wireframes placeholder: [WIREFRAMES.md](./WIREFRAMES.md) § WF-05R «E7 — backlog futuro».

**Dívidas E6 (fechadas):** gap `filter=uncovered` (universo = open-orders), `open_value`/`attention_count` via `list_customer_open_order_metrics`, badge `has_portal_access` no detalhe (+ gate core-api).
