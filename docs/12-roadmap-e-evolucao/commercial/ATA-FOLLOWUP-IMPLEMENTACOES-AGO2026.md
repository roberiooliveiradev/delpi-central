# Ata → novas implementações (ago/2026)

> **Origem:** ata de follow-up comercial (pedidos, carteira, Meu Dia, perfis/notificações, colaboração)  
> **Produto:** Portal Comercial · `/apps/commercial` · `commercial-api` · TOTVS via `api-delpi`  
> **Como ler:** cada bloco = **já temos** · **implementar** · **investigar / decisão** · **fora / irmão**  
> **Não substitui:** [ATA-MAPA-NECESSIDADES.md](./ATA-MAPA-NECESSIDADES.md) · [ATA-ALINHAMENTO-AGO2026-2.md](./ATA-ALINHAMENTO-AGO2026-2.md) · [WIREFRAMES.md](./WIREFRAMES.md) · [UX-E-TASKS-EVOLUTION.md](./UX-E-TASKS-EVOLUTION.md) · [PERFIS-E-PERMISSOES.md](./PERFIS-E-PERMISSOES.md)

---

## 0. Resumo executivo

| Tema da ata | Situação no Portal | Próximo passo sugerido |
|-------------|--------------------|------------------------|
| Pedidos em aberto (filtros, KPI, tabela/cards, colunas) | **Existe** | Homologar UX; não reinventar |
| Kanban de pedidos por etapa (próximos → faturar → concluídos) | **Existe** | Board + BFF `kanbanStage` + concluídos recently-closed |
| Responsável pela criação do pedido (Protheus) | **Indisponível** (doc padroes-totvs) | Sem UI de criador neste ciclo |
| Comparativos de faturamento na carteira (empresa, YoY, períodos, tendência) | **Existe** | T3 share · T4 períodos/YoY · T5 ranking — [PARCIAL-INVENTARIO.md](./PARCIAL-INVENTARIO.md) P-SHARE |
| Meu Dia (tarefas, cliente, anexos, responsável, realtime, gestor) | **Existe** (MVP forte) | P3 CRM (lembrete/notif push); visita→frota |
| Integração visita × Central de Agendamento (veículos) | **Falta** (app irmão existe) | BFF + deep-link / reserva no fluxo Visita |
| Home por perfil (vendedor × gestor × orçamentista × faturamento) | **Parcial** | Vendedor/gestor **Existem**; orçamentista/faturamento = T7 |
| Notificar «pronto para faturar» (faturamento + vendedores) | **Existe** | Snapshot + outbox + sino Minha Delpi; config `billing*` só admin/app |
| Config sensível só admin da aplicação | **Existe** | Grants `manage` internos; não expandir toggles ao gestor |
| Área de colaboração (feed, menções, vínculos, Outlook/Teams) | **Parcial** | P0 sala (**Existe**) · Outlook/Teams = T11 |

### Ata alinhamento 2 (epicos apontados)

| Tema | Situação | Doc canônico |
|------|----------|--------------|
| Sala de interação / passagem de bastão | **Existe** (P0) | [ATA-ALINHAMENTO-AGO2026-2.md](./ATA-ALINHAMENTO-AGO2026-2.md) §11–12 · P2-SALA · [API-ROUTES.md](./API-ROUTES.md) § 3.21 |
| Confirmação de pedidos (2 momentos + SLA) | **Falta** | ATA-2 §9–10 · P2-CONF · API-ROUTES §3.13 |
| Reunião Diretoria | **Falta** (aguardar modelo) | ATA-2 §34 · P2-DIR |
| MyVEG | **Falta** (estudo) | ATA-2 §33 · P2-MYVEG |
| GR de Vendas | **TV-GR** | ATA-2 §4 · tv-dashboard |

Legenda: **Existe** · **Parcial** · **Falta** · **Investigar** · **Fora** (outro bounded context) · **TV-GR**.

---

## 1. Pedidos em aberto (`/open-orders`)

### 1.1 Já temos

| Capacidade | Onde | Notas |
|------------|------|-------|
| Filtros (estoque, atraso, escopo carteira/vendedor, datas…) | `OpenOrdersPage` + deep links | Ver helps `CM_HELP.openOrders` |
| Indicadores resumidos / strip de status | Página + factory strip | Cobertura, atrasos, etc. |
| Visualização **tabela**, **cards** ou **board** (Kanban) | Preferência persistida | Layout toggle + WF-OPEN-ORDERS-KANBAN |
| Colunas Kanban `upcoming` · `in_progress` · `ready_to_invoice` · `completed` | BFF `kanbanStage` + recently-closed | FIFO `OpenOrderStockAllocationService` → `OpenOrderKanbanStageService` via `EnrichOpenOrdersKanbanService`; MFE só agrupa. Badge «Meus pedidos» = `kanbanStageCounts.ready_to_invoice` (mesma regra do chip «Pode faturar») |
| Escolher e ordenar colunas | Preferências de coluna | Table settings |
| Detalhe de linha / OP, links reais Conta/Pedido/OP | Detalhe produção + `CommercialEntityLink` | WF pedidos / links ago/2026 |
| Export Excel | Toolbar | |

Rota: `/apps/commercial/open-orders` · permissão típica: `commercial.accounts.view`.

### 1.2 Implementar

| Item da ata | Ferramenta / entrega | Dependências |
|-------------|----------------------|--------------|
| **Kanban** por etapas | **Entregue** (ago/2026) — board read-only + deep link `?view=board&stage=` | Homologar com Comercial; DnD / OP movendo coluna = fora |
| Coluna / filtro por **criador do pedido** | **Cancelado** — campo indisponível no Protheus | Discovery § 1.3 |

**Não fazer:** reimplementar filtros/KPI/tabela/cards já estáveis.

### 1.3 Investigar (Protheus)

| Pergunta | Resultado (ago/2026) |
|----------|----------------------|
| Existe campo do **usuário que criou** o pedido de venda? | **Não** — ver [pedido-venda-criador.md](../../../api-delpi/docs/api/padroes-totvs/pedido-venda-criador.md) |
| `C5_MSUIDT` | UUID técnico (SX3 «Campo UUID»); não usar como criador |
| Filtro carteira por criador | **Não prometido** na UI até haver fonte nova |

Probe: `api-delpi/scripts/sql/sc5_order_creator_probe.py`.  
**UI criador (coluna/filtro):** cancelada neste ciclo.

---

## 2. Carteira — comparações de faturamento

### 2.1 Já temos

| Capacidade | Onde | Notas |
|------------|------|-------|
| Faturamento / ROL no período | Visão geral `/overview`, Conta `?secao=historico` | Séries BFF analytics / billing |
| **YoY** (mesmo período −1 ano) em ROL e conversão | Overview + Minha Carteira + Conta | Overlay sem rota nova (`periodShift`) |
| **Share** carteira ÷ empresa | Overview + Minha Carteira | BFF `portfolio-billing-share` (RBAC) |
| **Ranking** crescimento/queda | Minha Carteira | BFF `portfolio-billing-ranking` + Excel |
| Carteira aberta + **gap vs meta** + buckets no tempo | Overview (`open-portfolio-horizon`) | Chips → deep link Meus pedidos |
| Análise por **cliente** | Conta 360 + Minha Carteira | Pedidos, histórico, opp |
| Escopo por **vendedor / carteira** | Filtro de escopo shell + Admin | Membership N:N |
| Evolução / série por período (presets + N anos) | Overview + Minha Carteira + Conta | `PeriodCompareControls` até 3 anos |

Refs: [KPI-FICHAS.md](./KPI-FICHAS.md) · [ATA-MAPA-NECESSIDADES.md](./ATA-MAPA-NECESSIDADES.md) § Onda A/B · [WIREFRAMES.md](./WIREFRAMES.md) WF-OV.

### 2.2 Implementar

| Item da ata | Status vs atual | Ferramenta / entrega |
|-------------|-----------------|----------------------|
| Faturamento da **carteira ÷ faturamento total da empresa** | **Entregue** (T3) | KPI-PORTFOLIO-SHARE · BFF `portfolio-billing-share` · cards Overview + Minha Carteira (RBAC analytics/team/manage) |
| Período atual × **mesmo período ano anterior** | **Entregue** (T4) | YoY Overview + Minha Carteira + Conta `?secao=historico` via `periodShift` / billing |
| Comparação com **períodos e anos escolhidos pelo usuário** | **Entregue** (T4) | `PeriodCompareControls`: presets + custom + até 3 anos overlay nas séries |
| Evolução da carteira no tempo | **Existe** | Aberto = horizon; faturado = séries/billing; glossário `CM_HELP.*.glossaryOpenVsBilled`. FCT declarado **não** entra no produto (fora das atas; metas SI cobrem). |
| Tendência de faturamento com **período configurável** | **Entregue** (T4) | Janela 7/30/90/custom (default 30) no enrichment + UI Minha Carteira |
| Cortes cliente × vendedor × período (crescimento/queda) | **Entregue** (T5) | BFF `portfolio-billing-ranking` + tabela/Excel Minha Carteira; `group_by=seller` só team/manage |

### 2.3 Fora / cuidado

- Não misturar **carteira aberta (backlog)** com **ROL faturado** no mesmo card sem rótulo (já documentado em KPI-FICHAS · `KPI-PORTFOLIO-SHARE`).
- Totais «empresa» = escopo RBAC (gestor com `analytics` / team); vendedor operacional **não** vê % empresa (só faturamento do escopo).
- **Glossário UI (CM_HELP):** `overview.glossaryOpenVsBilled` / `customers.glossaryOpenVsBilled` — aberto = backlog snapshot; faturado = ROL/NF no período; share e tendência usam só faturado.

---

## 3. Follow-up e organização de atividades (Meu Dia)

### 3.1 Já temos

| Capacidade da ata | Estado | Onde |
|-------------------|--------|------|
| Cadastro e acompanhamento de tarefas / atividades | **Existe** | `/my-tasks` (alias `/my-day`) |
| Vínculo a **cliente** | **Existe** | Form + Conta «Agendar follow-up» |
| **Anexos** | **Existe** (P2) | Volume `commercial-attachments` |
| **Responsáveis** + reatribuir | **Existe** (P1) | Gestão: chips Minhas / Equipe |
| Gestor atribui a vendedores da carteira | **Existe** | Escopo team + picker |
| Realtime (conclusão visível aos envolvidos) | **Existe** | WebSocket worklist + toast |
| Tipos (Follow-up, Ligar, E-mail, Visita, To-do) | **Existe** | |
| Observação / histórico na conta | **Existe** (P0) | |

Refs: [UX-E-TASKS-EVOLUTION.md](./UX-E-TASKS-EVOLUTION.md) · [HOMOLOGACAO-WAVE-G.md](./HOMOLOGACAO-WAVE-G.md).

### 3.2 Implementar

| Item da ata | Status | Ferramenta / entrega |
|-------------|--------|----------------------|
| **Notificações no Minha Delpi** (além do toast in-app) | **Existe** (T6/T9) | Outbox → Core (pronto a faturar + tarefas). **Falta:** P3 «Reminder» CRM em UX-E-TASKS |
| Integração **visita → Central de Agendamento (veículos)** | **Falta** | Ao tipo **Visita**: consultar disponibilidade, data/hora, reservar recurso; UI no Portal + gateway HTTP para api-delpi `/scheduling…` (dono: Central de Agendamento) |

App irmão já existe: [`plugins/central-agendamento`](../../../plugins/central-agendamento/README.md) · rotas ES/SC · doc [central-agendamento.md](../../../api-delpi/docs/api/central-agendamento.md).

**Princípio de fronteira:** Comercial **não** reimplementa frota; orquestra reserva via API do agendamento (ou deep-link autenticado com retorno ao Meu Dia).

### 3.3 Backlog CRM já listado (P3)

Checklist, lembrete antes do prazo, recorrência, convidados/local — ver UX-E-TASKS § 3 P3. Não misturar com o épico de colaboração (§ 5).

---

## 4. Perfis de acesso e notificações

### 4.1 Já temos

| Capacidade | Estado | Notas |
|------------|--------|-------|
| Informações conforme **capacidade** (não cargo hardcoded) | **Existe** | [PERFIS-E-PERMISSOES.md](./PERFIS-E-PERMISSOES.md) — papéis Minha Delpi agrupam codes |
| Vendedor: pedidos, carteira (membership), Meu Dia, Conta | **Existe** | Home prioriza atenção / números do escopo |
| Gestor: Visão geral, escopo equipe, Admin carteiras/equipe | **Existe** | `analytics.view`, `accounts.team.view`, `seller-portfolios.manage` |
| Config sensível em Admin (não no dia a dia do gestor de campo) | **Existe** | CRUD carteiras/grupos só `manage`; evitar proliferar toggles |

### 4.2 Implementar

| Item da ata | Ferramenta / entrega |
|-------------|----------------------|
| Home **vendedor** = meus clientes / pedidos / carteira / atividades | Layout/prioridade do Início por conjunto de permissões (já parcialmente); validar copy e ordem com Comercial |
| Home **gestor** = equipe + carteiras + pedidos + indicadores | Reforçar bloco Gestão/Equipe + deep links Overview; ranking produtividade se faltar |
| Perfis **orçamentista** e **faturamento** | Novos **papéis** Minha Delpi (agrupando codes existentes + futuros `*.view` se necessário); telas/atalhos: OV/propostas vs. «pronto a faturar» |
| Notificar **responsável faturamento** + **vendedores** quando pedido **pronto para faturar** | **Entregue** — FIFO `OpenOrderStockAllocationService` + `OpenOrderKanbanStageService` + checkpoint `integration_checkpoints` + outbox + `POST /integrations/jobs/ready-to-invoice-scan` → Core `/integrations/notifications` (deep link board). Destinatários: membership da carteira do cliente + `billingUserIds` / `billingPermissionCodes` em `ready_to_invoice_notification.json` (só ops/admin app). Catálogo: categoria `commercial`. |
| Notificar envolvidos em **tarefas** (atribuída / grupo / concluída / prazo) | **Entregue** — hooks worklist + outbox + `POST /integrations/jobs/task-due-scan` → Core (`category=commercial_tasks`). Destinatários = `userIds` envolvidos (sem permission code novo). Preferências: «Tarefas comerciais». |
| Permissões sensíveis só equipe da aplicação | Política ops: grants de `manage` / auditoria só internos; documentar no PERFIS |

**Não fazer:** permission codes nomeados `commercial.vendedor` / `commercial.gestor` — manter modelo por capacidade.

---

## 5. Área de colaboração comercial

### 5.1 Já temos (adjacente, não substitui)

| Peça | Onde | Limite |
|------|------|--------|
| Atividades / follow-ups por cliente | Meu Dia + Conta | Não é feed de equipe |
| Realtime worklist / portfolio | commercial-api WS | Eventos de domínio, não chat |
| Conta Outlook Minha Delpi (integração existente) | Plataforma | Ampliar escopo calendário/eventos conforme ata |

### 5.2 Implementar (épico)

**P0 entregue (T10 parcial):** sala por entidade/processo/mural, inbox, `@` menções tipadas + unfurl, anexos `room_message`, pins, criar tarefa a partir da mensagem, WS `room.*`, notificação colaboração — ver [API-ROUTES.md](./API-ROUTES.md) § 3.21 · WF-SALA · README do plugin.

| Capacidade da ata | Ferramenta / entrega | Notas |
|-------------------|----------------------|-------|
| Publicar mensagens e orientações | **Existe** (thread + wall global/grupo) | Mural board completo = fora do P0 |
| Menções a colaboradores | **Existe** (`@user` + notif) | Diretório Admin |
| Vincular cliente, pedido, proposta, etc. | **Existe** (kinds + deep link) | Suggest/preview no BFF |
| Preview resumido do item mencionado | **Existe** (unfurl + card opaco sem RBAC) | |
| Histórico formal | **Existe** (persistência + soft delete) | Busca avançada = evolução |
| Criar reuniões/compromissos a partir da mensagem | Action «Agendar» | Backlog T11 / Graph |
| Integração **Outlook** e **Teams** | Graph / conectores Minha Delpi | Conta já existe; ampliar scopes — **T11** |
| Consultar disponibilidade dos participantes | Free/busy Graph | **T11** |
| Convites + eventos nas agendas | Create event + attendees | **T11** |

**Fora do escopo imediato do MFE Comercial sozinho:** política de tenant Graph, consentimento admin, rate limits — coordenar com plataforma/auth.

**Substituição parcial do Teams:** posicionar como **histórico operacional vinculado a registros**; não como chat genérico 1:1.

---

## 6. Mapa de ferramentas (o que construir)

| # | Ferramenta | Pacote dono | Prioridade sugerida | Depende de |
|---|------------|-------------|---------------------|------------|
| T1 | Discovery «criador do pedido» Protheus | api-delpi (+ doc padroes-totvs) | **Feito** (indisponível) | — |
| T2 | Kanban Meus pedidos (etapas) | commercial MFE + commercial-api + api-delpi | **Feito** | Homologação UX |
| T3 | Share faturamento carteira ÷ empresa | commercial-api BFF + Overview/Carteira | **Feito** | Fórmula KPI + RBAC |
| T4 | Comparadores de período livres + tendência na Carteira/Conta | MFE + séries existentes | **Feito** | UX presets vs custom |
| T5 | Ranking crescimento/queda (cliente/vendedor) | BFF analytics | **Feito** | T3/T4 |
| T6 | Notificação «pronto para faturar» | outbox + plataforma notif + papéis | **Feito** | Configurar `billing*` no JSON; cron/ops no job |
| T7 | Home/personas orçamentista & faturamento | Papéis + launcher Home | P2 | T6 |
| T8 | Visita Meu Dia → reserva veículo | commercial + Central de Agendamento | P1 | Contrato HTTP scheduling |
| T9 | Lembretes / notif de tarefa (sino Portal) | commercial-api outbox + catálogo `commercial_tasks` | **Feito** | Job `task-due-scan`; WS toast MFE permanece |
| T10 | Área de colaboração (feed + menções + vínculos) | commercial-api + MFE | **P0 Existe** (sala); Graph = T11 | Design + Graph |
| T11 | Colaboração → Outlook/Teams (busy + invite) | plataforma / Graph | P2–P3 | T10 P0 + scopes |

---

## 7. Alinhamento com backlog já documentado

| Ata (este doc) | Documento existente |
|----------------|---------------------|
| Kanban pedidos | WIREFRAMES: WF-08 pipeline era backlog de **oportunidades**; **Kanban de pedidos** = demanda **nova** (não misturar com OV) |
| YoY / horizon | ATA-MAPA + KPI-FICHAS (entregue Overview) — estender à Carteira |
| Meu Dia anexos/responsável | UX-E-TASKS (entregue); P3 reminder |
| Mapa / inbox e-mail / rotate leads | WIREFRAMES E7 futuro — **diferente** da colaboração feed |
| Perfis | PERFIS-E-PERMISSOES — evoluir papéis, não codes de cargo |
| Agendamento veículos | Plugin `central-agendamento` — integração, não clone |

---

## 8. Próximos passos recomendados (ordem)

1. **Workshop curto** — fechar glossário das colunas do Kanban e regra «pronto para faturar».  
2. **T1 discovery** — campo criador do pedido no Protheus (sim/não + qualidade do dado).  
3. **T6 + persona faturamento** — maior ganho operacional citado na ata.  
4. ~~**T3/T4** — comparativos de faturamento na superfície Carteira/Conta.~~ **Feito** (T3/T4/T5 — ago/2026).  
5. **T8** — visita ↔ veículos (reuso Central de Agendamento).  
6. ~~**T10/T11** — épico colaboração (ADR + spike Graph).~~ **T10 P0 Feito** (sala); **T11** Graph permanece.

---

## Referências

- [ATA-MAPA-NECESSIDADES.md](./ATA-MAPA-NECESSIDADES.md)  
- [WIREFRAMES.md](./WIREFRAMES.md) · [GESTAO-A-VISTA.md](./GESTAO-A-VISTA.md)  
- [UX-E-TASKS-EVOLUTION.md](./UX-E-TASKS-EVOLUTION.md) · [PERFIS-E-PERMISSOES.md](./PERFIS-E-PERMISSOES.md)  
- [KPI-FICHAS.md](./KPI-FICHAS.md) · [API-ROUTES.md](./API-ROUTES.md)  
- [plugins/central-agendamento/README.md](../../../plugins/central-agendamento/README.md)  
- [api-delpi/docs/api/central-agendamento.md](../../../api-delpi/docs/api/central-agendamento.md)  
