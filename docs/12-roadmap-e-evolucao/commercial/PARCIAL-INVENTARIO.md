# Inventário Parcial — Portal Comercial

> **Status:** canônico · sincronizado com ATA-2 / ATA-MAPA / Follow-up / Playbook  
> **Atualização W0:** **fechada** (E0–E7) — itens W0 = Existe; W1–W5 = backlog  
> **Correções pós-W0:** hub SI + shell (meta sum/average, rótulos, favoritos na topbar, filtros Opp) — **Existe**  
> **Revisão código ago/2026:** itens W1/DOC cuja entrega já está no `main` promovidos a **Existe** (não confundir com backlog de produto W2–W5)  
> **Não substitui:** [ATA-ALINHAMENTO-AGO2026-2.md](./ATA-ALINHAMENTO-AGO2026-2.md) · [ATA-MAPA-NECESSIDADES.md](./ATA-MAPA-NECESSIDADES.md)

Inventário **deduplicado** de itens com status **Parcial** (e afins) na documentação commercial. Classes: `W0` (implementação imediata) · `W1`…`W5` (backlog) · `HOMOLOG` · `DOC` · `FORA`.

## Legenda de status de entrega

| Status | Significado |
|--------|-------------|
| **W0-pendente** | Na onda imediata; ainda não Existe no código |
| **Existe** | Entregue no Portal / SI |
| **Backlog** | Onda W1–W5 — plano fino na entrada (implementável sob `.cursor`) |
| **Bloqueado** | **Não implementar** até desbloqueio; motivo = diretriz `.cursor` e/ou ficha/política (ver § Bloqueado) |
| **Homolog** | Aguarda negócio (sem código novo de regra) |
| **Fora** | Outro bounded context ou não agora |

---

## W0 — implementação imediata

Ordem: `E0 → E1 (SI) → E3 → E2 → E4.S1 → E4.S2 → E5 → E6 → E7`.

| ID | Tema | Etapa | Status | Pacotes | Fontes |
|----|------|-------|--------|---------|--------|
| P-META | Meta proporcional diária + flags + parity notas | E1 | **Existe** (SI; % incompleto = sum diária; YTD % = average) | `strategic-indicators-api` | ATA-2 §5 · KPI-ROL |
| P-META-LABEL | «Meta» / «Meta parcial» / «Meta acumulada» (`goal_period_kind` + `buildKpiGoalPresentation.goalPrefix`) | E2 | **Existe** | `plugins/plugin-ui` + dashboards SI + commercial Overview | ATA-2 §5 |
| P-META-REF | Tríade `goal_value` / `comparable_goal` / `reference_goal` + dual-line «Meta mês» + HelpTooltip; TV/Chat só rótulos | pós-W0 | **Existe** | SI + api-delpi + plugin-ui + hubs + TV + chat | plano meta mensal |
| P-LABEL | Chip MTD/YTD nos cards Overview | E2 | **Existe** | `plugins/commercial` | ATA-2 §5 |
| P-RENAME | «Data de faturamento» + FOB/CIF | E3 | **Existe** | MFE + help | ATA-2 §14–15 |
| P-OPP | Filtros Conta: período, produto, família (grid + debounce/foco) | E4 | **Existe** | api-delpi + BFF + MFE | ATA-2 §21 |
| P-OTD-COPY | Help OTD = DatFat × entrega prometida | E5 | **Existe** | MFE help | ATA-2 §16 |
| P-FAV | Favoritos no slot `secondary` da TopBar | E6 | **Existe** | MFE shell + plugin-ui | ATA-2 §39 |

### Correções pós-W0 (hub)

| Tema | Decisão | Status |
|------|--------|--------|
| Meta % no YTD | `average` ponderada por dias (não soma de meses) | **Existe** |
| Meta % mês incompleto | `sum` das parcelas diárias (`meta_mês × dias/dias_mês`) | **Existe** |
| Meta R$/count | `sum` prorata diária | **Existe** |
| Rótulo | 1 mês fechado → «Meta»; &lt; 1 mês → «Meta parcial»; multi-mês → «Meta acumulada» (`goal_period_kind` + presentation) | **Existe** |
| Meta mês (referência) | `reference_goal` (standard = `goal_value`; curva = média dos meses do filtro); dual-line + help no kit; TV/Chat rótulos canônicos | **Existe** |
| Preset «Esta semana» | URL `period_preset` preserva intenção na segunda (range = Hoje) | **Existe** |
| Favoritos | Na topbar (`secondary`), sem faixa abaixo da nav | **Existe** |
| Opp Conta | Filtros em linha; inputs estáveis no refetch | **Existe** |

---

## W1 — Carteira / consolidado

| ID | Tema | Status | Evidência no código | Fontes |
|----|------|--------|---------------------|--------|
| P-CART-KPI | Carteira consolidada valor/itens | **Existe** | BFF `GET /analytics/open-portfolio-summary` + card Overview | MAPA · KPI-CARTEIRA |
| P-CART-ROL | Soma ROL + carteira (uma métrica) | **Bloqueado** | UI/KPI único **proibido**; lado a lado **Existe** | MAPA §5.3 · KPI-ROL-CARTEIRA · § Bloqueado |
| P-CART-HORIZ | Glossário aberto × faturado | **Existe** | `CM_HELP.*.glossaryOpenVsBilled` + horizon | FOLLOWUP · KPI-CARTEIRA-HORIZON |
| P-BRUTO-LIQ | Toggle bruto inventado (sem contrato) | **Bloqueado** | Rótulo «ROL líquido» OK; série gross sem BFF = não | MAPA · § Bloqueado |
| P-POSTERG | UX postergado vs disponível | **Existe** | BFF `availability` + `?postponed=1` · [pedido-venda-postergacao.md](../../../api-delpi/docs/api/padroes-totvs/pedido-venda-postergacao.md) | Playbook #4 |
| P-CART-PCP | Distinguir carteira × PCP | **Existe** | Copy Overview + `overviewMetricsCatalog` / helps | Playbook #4 |
| P-PROJ | Projeção / FCT | **Existe** (MVP declarado) | `GET/PUT /forecast/current` + card Overview | Forecast F6 |
| P-SHARE | % empresa (carteira ÷ empresa) | **Existe** | BFF `portfolio-billing-share` + cards Overview/Carteira (RBAC) | FOLLOWUP T3 |

**W1 implementável:** P-PROJ (FCT declarado). **Bloqueado:** P-CART-ROL, P-BRUTO-LIQ (toggle). P-POSTERG **Existe**.

---

## W2 — Ofertas (backlog)

| ID | Tema | Status | Fontes |
|----|------|--------|--------|
| P-OFF-SLA | Etapas / SLA / área | **Backlog** | Playbook #3 |
| P-OFF-AGG | Agregações por colaborador | **Backlog** | MAPA §5.2 |
| P-OFF-AGE | Idade + status canônicos | **Backlog** | MAPA |
| P-OFF-FU | Follow-up dedicado OV | **Backlog** | MAPA |
| P-FILT-ADV | Filtros analista/etapa/família/grupo | **Backlog** | MAPA |
| P-HIT-DOC | Ficha metodologia hit rate | **Existe** (DOC) | Ver D-HIT / KPI-HIT-RATE — homolog regra ainda `em_validacao` |

**Entrada:** spec OFF-SLA.

---

## W3 — Clientes (backlog)

| ID | Tema | Status | Fontes |
|----|------|--------|--------|
| P-CLI-ATIVO | Formalizar KPI-CLIENTE-ATIVO | **Bloqueado** (ficha rascunho) | Playbook #7 · KPI-FICHAS — UI só após `em_validacao` |
| P-CLI-CLASS | Badges ativo/novo/recuperado/ticket | **Bloqueado** | Playbook #7 · gate ficha KPI |
| P-SEG | Segmentação estruturada (fonte) | **Backlog** | Playbook #6 — ADR fonte antes de inventar |
| P-CLI-FILT | Filtros família/grupo na carteira | **Parcial** | Produto em aberto na lista + Conta Opp `product_group`; B1_GRUPO na lista = ADR-003 | MAPA |
| P-CONTA-360 | Conta pré-reunião (checklist do Existe) | **Backlog** | Playbook #5 |
| P-HIST-NEG | Ticket/rentabilidade na Conta | **Bloqueado** | FIN-004 / KPI-TICKET · § Bloqueado |
| P-PROD-COM | Produtividade ofertas/colaborador | **Backlog** | overlap W2 |

**Entrada:** ADR fonte de segmentação.

---

## W4 — OTD / rastreio (backlog)

| ID | Tema | Status | Bloqueio | Fontes |
|----|------|--------|----------|--------|
| P-OTD-FLOW | OTD entrada Apoio → faturamento | **Backlog** | P2-CONF (parcial) | ATA-2 · MAPA |
| P-OTD-VAR | Variantes OTD | **Backlog** | — | Playbook #10 |
| P-OTD-CAUSE | Causas atraso | **Backlog** | — | Playbook #10 |
| P-MARCOS | Embarque / trânsito | **Backlog** | Expedição | MAPA |
| P-FNE | FNE formal ≠ chip estoque | **Backlog** | FNE Falta | MAPA |
| P-FAT-EMB | Faturado não embarcado | **Backlog** | F7 + TOTVS | Playbook #11 |
| P-PRAZO-GARG | Gargalos interdept. | **Backlog** | — | MAPA |

---

## W5 — GAV / GR / Home (backlog)

| ID | Tema | Status | Dono | Fontes |
|----|------|--------|------|--------|
| P-GAV-N1 | Gestão à Vista N1 gaps | **Backlog** | Comercial + TV | MAPA · Playbook |
| P-GR-TV | GR de Vendas **no MFE commercial** | **Bloqueado** / Fora | **tv-dashboard** | ATA-2 §35 · bounded context — só Link |
| P-HOME-PERS | Home orçamentista / faturamento | **Backlog** | MFE | FOLLOWUP T7 — por capabilities |
| P-RANK-BI | Ranking produtividade (ofertas/colaborador) | **Backlog** | MFE + BFF | MAPA — ≠ ranking faturamento T5 (**Existe**) |
| P-CAP-PCP | Cockpit capacidade PCP no commercial | **Bloqueado** / Fora Link | Produção/PCP | Playbook #14 · § Bloqueado — Link OK |
| P-IA-ALIM | Alimentar GAV/GR/IA | **Backlog** | Posterior | DESIGN-IA |
| P-VIS-INT | Lacunas gerenciais | **Backlog** | Contínuo | MAPA |
| P-NOTIF | Canal plataforma (sino Minha Delpi) | **Existe** | commercial-api + Core | FOLLOWUP T6/T9 — P3 reminder CRM permanece backlog |

**Entrada GR:** indicadores Junior/Laércio.

---

## Bloqueado por diretrizes `.cursor` (não implementar)

**Trava de engenharia:** PR que entregue UI/código destes itens = rejeitar até a coluna **Desbloqueio**. Espelho do plano quatro blocos § 0.1.

| ID | Tema | Motivo (diretriz / doc) | Desbloqueio |
|----|------|-------------------------|-------------|
| P-CART-ROL | Soma ROL + carteira (KPI/UI único) | KPI-FICHAS «Proibido somar»; gate ficha; clean-architecture | Ficha `KPI-ROL-CARTEIRA` **aprovada** + base única |
| P-BRUTO-LIQ | Toggle/série bruto inventada | Sem contrato BFF; totvs-product-patterns / centralized-rules | Rota nature `gross` no commercial-api |
| P-CLI-ATIVO / P-CLI-CLASS | Badges classificação KPI | Playbook P0 até ficha; KPI-FICHAS | Ficha `em_validacao`/`aprovada` |
| KPI-TICKET | Ticket médio no cockpit | Ficha bloqueada Onda A | Unidade + bruto/líquido homologados |
| P-HIST-NEG (margem) / rentabilidade | Margem na Conta / relatório | FIN-004; bounded-context | Política + RBAC + auditoria |
| P-GR-TV (no commercial) | Editor/slides GR no MFE | Bounded context = tv-dashboard | Só Link / feed; slides no TV |
| P-CAP-PCP / F-OCUP-FULL | Cockpit PCP no commercial | Dono Produção/PCP | Link dashboard-production; read-model só com contrato |
| (anti-padrão) | MFE → api-delpi direto | `mfe-own-api-no-direct-api-delpi` | Sempre BFF commercial-api |
| (anti-padrão) | Path/campo novo em PT | `english-code-identifiers` | Contrato EN |
| (anti-padrão) | CSS espelho / patch regra só no MFE | `plugins-reusable-components` · `centralized-rules-first` | Kit + domain/BFF |
| (anti-padrão) | Editar migration aplicada | `migrations-immutable-checksum` | Nova `V0NN` |
| (anti-padrão) | UI «rascunho» sem ficha | Guardrails + decisão NEG ago/2026 | Homolog primeiro |

## Homolog / Doc / Fora

| ID | Tema | Status | Fontes |
|----|------|--------|--------|
| H-YOY | Preferência visual mês a mês YoY | **Homolog** | ATA-2 §6 — overlay **Existe**; média visual aguarda Junior/Laércio |
| H-ADMIN-CFG | Config sensível só manage | **Existe** (manter) | FOLLOWUP — CRUD carteiras/grupos só `manage` |
| D-HIT | Ficha hit rate (num/den) | **Existe** | `KPI-HIT-RATE` em [KPI-FICHAS.md](./KPI-FICHAS.md) + doc api-delpi — homologação de regra ainda `em_validacao` |
| D-CATALOG-UI | Catálogo plugin-ui UnderlineNav | **Existe** | `plugins/plugin-ui/docs/component-catalog.md` + demo `layout.UnderlineNav` |
| F-EMPTY-SAVED | SavedViewChips | **Fora** | IMPLEMENTATION-PLAN |
| F-OCUP-FULL | Cockpit capacidade PCP | **Fora** / **Bloqueado** no commercial | MAPA · § Bloqueado |

### Falta (fora do inventário Parcial — ATA-2)

Confirmação pedidos · sala interação · Reunião Diretoria · MyVEG · aviso CRM funil (P1-FUNNEL).

---

## Histórico de fechamento W0

| Etapa | Commit | Data |
|-------|--------|------|
| E0 | (este) | — |
| E1–E7 | — | — |

## Revisão código (ago/2026) — Parcial que já era entrega

Critério: **Parcial na ata só permanece se o código ainda não cobre o pedido**. Homologação de negócio (`em_validacao`) ≠ gap de implementação.

| ID / tema | Antes | Depois | Por quê |
|-----------|-------|--------|---------|
| P-CART-KPI / P-SHARE / P-CART-HORIZ / P-CART-PCP | Backlog | **Existe** | Summary, share, glossário e copy ≠ PCP no Overview/Carteira |
| P-NOTIF (sino) | Backlog | **Existe** | Outbox Core; reminder P3 continua backlog |
| D-HIT / D-CATALOG-UI / H-ADMIN-CFG | DOC / Manter | **Existe** | Ficha + catálogo kit + RBAC manage |
| «Pode faturar» (estoque) | MAPA Parcial | **Existe** | Chip + badge FIFO no BFF (`OpenOrderStockAllocationService`); FNE continua **Falta** |
| MTD/YTD + meta proporcional | MAPA Parcial | **Existe** | Já W0 / ATA-2 |
| FIFO badge ≠ chip | (não inventariado) | **Existe** | `EnrichOpenOrdersKanbanService` aloca antes de `kanbanStageCounts` |
