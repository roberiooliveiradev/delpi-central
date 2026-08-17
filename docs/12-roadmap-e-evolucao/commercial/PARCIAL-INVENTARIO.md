# Inventário Parcial — Portal Comercial

> **Status:** canônico · sincronizado com ATA-2 / ATA-MAPA / Follow-up / Playbook  
> **Atualização W0:** em curso (código) — marcar Existe ao fechar cada etapa  
> **Não substitui:** [ATA-ALINHAMENTO-AGO2026-2.md](./ATA-ALINHAMENTO-AGO2026-2.md) · [ATA-MAPA-NECESSIDADES.md](./ATA-MAPA-NECESSIDADES.md)

Inventário **deduplicado** de itens com status **Parcial** (e afins) na documentação commercial. Classes: `W0` (implementação imediata) · `W1`…`W5` (backlog) · `HOMOLOG` · `DOC` · `FORA`.

## Legenda de status de entrega

| Status | Significado |
|--------|-------------|
| **W0-pendente** | Na onda imediata; ainda não Existe no código |
| **Existe** | Entregue no Portal / SI |
| **Backlog** | Onda W1–W5 — plano fino na entrada |
| **Homolog** | Sem código; aguarda negócio |
| **Fora** | Outro bounded context ou não agora |

---

## W0 — implementação imediata

Ordem: `E0 → E1 (SI) → E3 → E2 → E4.S1 → E4.S2 → E5 → E6 → E7`.

| ID | Tema | Etapa | Status | Pacotes | Fontes |
|----|------|-------|--------|---------|--------|
| P-META | Meta proporcional diária + flags + parity notas | E1 | **Existe** (SI) | `strategic-indicators-api` | ATA-2 §5 · KPI-ROL |
| P-META-LABEL | «Meta acumulada» / «· parcial» na UI | E2 | **Existe** | `plugins/commercial` + plugin-ui | ATA-2 §5 |
| P-LABEL | Chip MTD/YTD nos cards Overview | E2 | **Existe** | `plugins/commercial` | ATA-2 §5 |
| P-RENAME | «Data de faturamento» + FOB/CIF | E3 | **Existe** | MFE + help | ATA-2 §14–15 |
| P-OPP | Filtros Conta: período, produto, família | E4 | **Existe** | api-delpi + BFF + MFE | ATA-2 §21 |
| P-OTD-COPY | Help OTD = DatFat × entrega prometida | E5 | **Existe** | MFE help | ATA-2 §16 |
| P-FAV | Favoritos no PluginShell | E6 | **Existe** | MFE shell | ATA-2 §39 |

---

## W1 — Carteira / consolidado (backlog)

| ID | Tema | Status | Fontes |
|----|------|--------|--------|
| P-CART-KPI | Carteira consolidada valor/itens | **Backlog** | MAPA · Playbook #4 |
| P-CART-ROL | Carteira + ROL / 2 anos | **Backlog** | MAPA §5.3 |
| P-CART-HORIZ | Glossário aberto × faturado | **Backlog** | FOLLOWUP |
| P-BRUTO-LIQ | Bruto vs líquido explícito | **Backlog** | MAPA |
| P-POSTERG | UX postergado vs disponível | **Backlog** | Playbook #4 |
| P-CART-PCP | Distinguir carteira × PCP | **Backlog** | Playbook #4 |
| P-PROJ | Projeção / FCT | **Backlog** | Forecast F6 |
| P-SHARE | % empresa / seletor livre | **Backlog** | FOLLOWUP |

**Entrada:** fórmula KPI consolidada fechada em KPI-FICHAS.

---

## W2 — Ofertas (backlog)

| ID | Tema | Status | Fontes |
|----|------|--------|--------|
| P-OFF-SLA | Etapas / SLA / área | **Backlog** | Playbook #3 |
| P-OFF-AGG | Agregações por colaborador | **Backlog** | MAPA §5.2 |
| P-OFF-AGE | Idade + status canônicos | **Backlog** | MAPA |
| P-OFF-FU | Follow-up dedicado OV | **Backlog** | MAPA |
| P-FILT-ADV | Filtros analista/etapa/família/grupo | **Backlog** | MAPA |
| P-HIT-DOC | Ficha metodologia hit rate | **Backlog** / DOC | MAPA |

**Entrada:** spec OFF-SLA.

---

## W3 — Clientes (backlog)

| ID | Tema | Status | Fontes |
|----|------|--------|--------|
| P-CLI-ATIVO | Formalizar KPI-CLIENTE-ATIVO | **Backlog** | Playbook #7 |
| P-CLI-CLASS | Ativo/novo/recuperado/ticket | **Backlog** | Playbook #7 |
| P-SEG | Segmentação estruturada (fonte) | **Backlog** | Playbook #6 |
| P-CLI-FILT | Filtros família/grupo na carteira | **Backlog** | MAPA |
| P-CONTA-360 | Conta pré-reunião completa | **Backlog** | Playbook #5 |
| P-HIST-NEG | Histórico + ticket/rentabilidade | **Backlog** | MAPA |
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
| P-GR-TV | GR de Vendas | **Backlog** | **tv-dashboard** | ATA-2 §35 |
| P-HOME-PERS | Home por perfil | **Backlog** | MFE | FOLLOWUP |
| P-RANK-BI | Ranking produtividade | **Backlog** | MFE | MAPA |
| P-CAP-PCP | Capacidade fábrica | **Backlog** / Fora Link | Produção/PCP | Playbook #14 |
| P-IA-ALIM | Alimentar GAV/GR/IA | **Backlog** | Posterior | DESIGN-IA |
| P-VIS-INT | Lacunas gerenciais | **Backlog** | Contínuo | MAPA |
| P-NOTIF | Notificações além toast | **Backlog** | Core + commercial | FOLLOWUP |

**Entrada GR:** indicadores Junior/Laércio.

---

## Homolog / Doc / Fora

| ID | Tema | Status | Fontes |
|----|------|--------|--------|
| H-YOY | Preferência visual mês a mês YoY | **Homolog** | ATA-2 §6 |
| H-ADMIN-CFG | Config sensível só manage | Manter | FOLLOWUP |
| D-HIT | Completar ficha hit rate | **DOC** | MAPA |
| D-CATALOG-UI | Catálogo plugin-ui UnderlineNav | **DOC** | IMPLEMENTATION-PLAN |
| F-EMPTY-SAVED | SavedViewChips | **Fora** | IMPLEMENTATION-PLAN |
| F-OCUP-FULL | Cockpit capacidade PCP | **Fora** | MAPA |

### Falta (fora do inventário Parcial — ATA-2)

Confirmação pedidos · sala interação · Reunião Diretoria · MyVEG · aviso CRM funil (P1-FUNNEL).

---

## Histórico de fechamento W0

| Etapa | Commit | Data |
|-------|--------|------|
| E0 | (este) | — |
| E1–E7 | — | — |
