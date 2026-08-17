# Ata de alinhamento 2 — Portal Comercial (ago/2026)

> **Status:** inventário + backlog pós-reunião de alinhamento (segunda ata)  
> **Produto:** Portal Comercial · `/apps/commercial` · `commercial-api` · reads TOTVS via `api-delpi`  
> **Não substitui:** [ATA-MAPA-NECESSIDADES.md](./ATA-MAPA-NECESSIDADES.md) · [ATA-FOLLOWUP-IMPLEMENTACOES-AGO2026.md](./ATA-FOLLOWUP-IMPLEMENTACOES-AGO2026.md) · [KPI-FICHAS.md](./KPI-FICHAS.md)  
> **Origem:** reunião de alinhamento da aplicação Comercial (itens §5–§17, §21, §33–§35, §38–§40)  
> **PDF:** se versionado, colocar em `docs/12-roadmap-e-evolucao/commercial/assets/` e linkar aqui  
> **GR de Vendas:** implementação no app **[TV Dashboard](../../../plugins/tv-dashboard/README.md)** — ver § 4; Comercial só reutiliza/alimenta painéis

Este documento responde, para cada ponto da ata: **já temos?** · **o que falta?** · **próximo passo** · **onde implementar**.

---

## 0. Resumo executivo

| Dimensão | Situação no Portal |
|----------|-------------------|
| Meta acumulada (proporcional diária) | **Parcial** — hoje meses civis × meta SI; corrigir P0 |
| Labels MTD/YTD nos cards | **Parcial** — presets existem; falta rótulo explícito |
| Faturamento histórico Protheus | **Existe** |
| Aviso de cobertura CRM no funil | **Falta** |
| Confirmação de pedidos (Apoio→PCP→cliente) | **Falta** (epico F7 / ORD-*) |
| Sala de interação / passagem de bastão | **Falta** (evolução Meu Dia) |
| Rename entrega → faturamento (timeline) | **Falta** (P0 labels) |
| OTD fluxo completo (entrada→faturamento) | **Parcial** |
| Filtros avançados de oportunidades (Conta) | **Parcial** |
| MyVEG | **Falta** (estudo) |
| Reunião Diretoria | **Falta** (aguardar modelo Junior/Laércio) |
| GR de Vendas | **Registrar no TV Dashboard** — não build no Comercial |
| Create carteira / telefone / ranking / Kanban próximos / Contatos | **Existe** |
| Favoritos na topbar | **Parcial** (só Início) — Baixa |

**Acordo da ata:** Comercial continua hub Minha DELPI; reutilizar apps/dados existentes; correções Alta em ondas P0; GR = TV.

---

## 1. Como ler

| Status | Significado |
|--------|-------------|
| **Existe** | Disponível no Portal (rota + permissão) — não reinventar |
| **Parcial** | Há dado/UI incompleto vs. pedido da ata |
| **Falta** | Sem superfície; backlog Comercial |
| **Fora** | Outro bounded context (Expedição, etc.) |
| **TV-GR** | Entrega no **tv-dashboard**, não no MFE Comercial |

---

## 2. Matriz por item da ata

### §5 — Meta acumulada e clareza de período

| Necessidade | Status | Evidência | Próximo passo |
|-------------|--------|-----------|---------------|
| Meta = **soma** proporcional **por dia** no intervalo (não média mensal) | **Parcial** | SI `_calculate_standard_period_goal` / meses civis; ROL% via api-delpi enrich | **P0-META** — `strategic-indicators-api` + testes período parcial/YTD |
| Evidenciar YTD/MTD nos cards | **Parcial** | Presets Overview; label = intervalo datas | **P0-LABEL** — chip/rótulo no card |

Regra de negócio travada: para cada mês do intervalo, `meta_mês / dias_do_mês × dias_sobrepostos`; somar. Suporta mês parcial, YTD, custom.

### §6 — Histórico de faturamento vs funil CRM

| Necessidade | Status | Evidência | Próximo passo |
|-------------|--------|-----------|---------------|
| Faturamento histórico da base operacional/Protheus | **Existe** | Conta `?secao=historico` · billing-series | Manter; documentar fonte |
| Funil/conversão: só onde há CRM confiável + aviso na UI | **Falta** | Hit rate sem banner de cobertura | **P1-FUNNEL** — copy + UI |
| Preferência visual mês a mês entre anos | **Parcial** | YoY overlay Overview | Homologar com Junior/Laércio (média) |

### §9–§10 — Entrada e confirmação de pedidos

| Necessidade | Status | Evidência | Próximo passo |
|-------------|--------|-----------|---------------|
| Digitalizar fluxo e-mail Apoio→PCP→Compras→confirmação | **Falta** | [ATA-MAPA](./ATA-MAPA-NECESSIDADES.md) §13 · [API-ROUTES](./API-ROUTES.md) §3.13 F7 | Epico **P2**; mapear + definir SLA (Comercial+áreas) |
| Momento 1: recebimento automático | **Falta** | — | Spec no epico |
| Momento 2: data firme + confirmação ao cliente | **Falta** | — | Spec no epico |
| IA leitura de e-mail com validação humana | **Falta** | — | Futuro; nunca sem gate humano |

### §11–§12 — Passagem de bastão / sala de interação

| Necessidade | Status | Evidência | Próximo passo |
|-------------|--------|-----------|---------------|
| Informação acompanhar Oferta→Engenharia→Compras | **Falta** | Follow-up colaboração | Epico **P2** — evolução worklist/tarefas |
| Sala tipo Teams: menções, tarefas, anexos, vínculo pedido/OV | **Falta** | Realtime = worklist/carteira, não chat de entidade | Spec + WF stub |

### §14–§15 — Nomenclatura entrega vs faturamento

| Necessidade | Status | Evidência | Próximo passo |
|-------------|--------|-----------|---------------|
| Timeline: «data de entrega do pedido» → **«data de faturamento»** | **Falta** | Coluna/help «Entrega pedido»; OTD já usa faturamento em outra superfície | **P0-RENAME** |
| Não afirmar chegada ao cliente sem registro (FOB/CIF) | **Parcial** (conceito) | — | Copy/help alinhados no rename |

### §16 — OTD comercial fluxo completo

| Necessidade | Status | Evidência | Próximo passo |
|-------------|--------|-----------|---------------|
| OTD fabricação / DatFat vs Entreg | **Existe** (parcial vs desejo) | `/analytics/otd` | Manter |
| Marco entrada Apoio → análise → confirmação → fab → fat → expedição | **Falta** | Depende §9–10 | Roadmap Onda D; documentar etapas |

### §17 — Expedição

| Necessidade | Status | Evidência | Próximo passo |
|-------------|--------|-----------|---------------|
| Consumir bipagem entrada/saída (TOTVS ou Minha Delpi) | **Fora** / irmão | — | Comercial consome quando existir contrato |
| Área Expedição no módulo Comercial | **Falta** | — | Decisão futura pós-fonte |

### §21 — Oportunidades (filtros)

| Necessidade | Status | Evidência | Próximo passo |
|-------------|--------|-----------|---------------|
| Conta: status / abertas / ganhas / andamento | **Parcial** | `CustomerOpportunitiesSection` | Ampliar |
| Período, OV, produto/família | **Parcial** / **Falta** | Global Opp tem período; Conta sem família | **P0-OPP** |

### §33 — MyVEG

| Necessidade | Status | Evidência | Próximo passo |
|-------------|--------|-----------|---------------|
| Pedidos/programação WEG ainda não no Protheus | **Falta** | Zero código | Encaminhamento Robério + PCP + Elaine + Michael |

### §34 — Reunião Diretoria

| Necessidade | Status | Evidência | Próximo passo |
|-------------|--------|-----------|---------------|
| Acesso rápido: realizado, histórico, carteira, projeção | **Falta** | Aguardar apresentação Junior/Laércio | Stub nav em GESTAO; UI após modelo |

### §35 — GR de Vendas

| Necessidade | Status | Evidência | Próximo passo |
|-------------|--------|-----------|---------------|
| 1º GR até fim ago/2026; indicadores de Vendas | **TV-GR** | Sequência Portal → api-delpi → TV | Ver § 4; **não** implementar slides no Comercial |

### §38–§39 — Decisões e ajustes (demais)

| Ajuste | Prioridade ata | Status código | Ação |
|--------|----------------|---------------|------|
| Corrigir meta acumulada | Alta | Parcial | P0-META |
| Evidenciar YTD/MTD | Alta | Parcial | P0-LABEL |
| Gráficos históricos | Média | Parcial | Homologar |
| Filtros opp | Alta | Parcial | P0-OPP |
| Rename faturamento | Alta | Falta | P0-RENAME |
| OTD fluxo completo | Alta | Parcial | Roadmap |
| Confirmação pedidos | Alta | Falta | P2 |
| Erro criação carteira | Alta | **Existe** (name-first) | Só reabrir se bug novo |
| MyVEG | Alta | Falta | Estudo |
| Reunião Diretoria | Alta | Falta | Após modelo |
| Indicadores GR Vendas | Alta | TV-GR | TV Dashboard |
| Favoritos topbar | Baixa | Parcial | Backlog |
| Telefone perfil | Baixa | **Existe** | — |
| Ranking crescimento/queda | Média | **Existe** | Homologar |
| Revisar Kanban «próximos» | Média | **Existe** | Homologar regra |
| Contatos TOTVS RO + locais | (decisão §38) | **Existe** | — |

### §40 — Encaminhamentos

| Encaminhamento | Responsável | Registro |
|----------------|-------------|----------|
| Meta acumulada | Robério | P0-META |
| Nomenclatura timeline | Robério | P0-RENAME |
| Filtros opp | Robério | P0-OPP |
| Create carteiras | Robério | Verificar só se regressão |
| Gráficos comparação | Robério + Junior + Laércio | Média |
| Mapear confirmação | Comercial + TI | P2 |
| SLA confirmação | Comercial + áreas | Antes do epico |
| Passagem de bastão | Robério + áreas | P2 |
| MyVEG | Robério + PCP + Elaine + Michael | Estudo |
| Apresentação Diretoria | Junior / Laércio | Bloqueia UI |
| Visão Diretoria | Robério | Após modelo |
| Indicadores GR | Junior + Laércio + Robério | **TV** |
| Reunião carteiras/GR | Comercial + TI | — |
| Liberar / treinar vendedores | Robério | Ops |
| Feedback pós-uso | Comercial + TI | — |
| Sala interação | Robério | P2 |

---

## 3. Ondas de implementação (código)

| ID | Entrega | Pacotes | Critério de pronto |
|----|---------|---------|-------------------|
| **P0-META** | Meta = soma dias do período | `strategic-indicators-api` (+ Overview se necessário) | Teste parcial/YTD ≠ média meses |
| **P0-LABEL** | Chip MTD/YTD nos cards | `plugins/commercial` | Preset visível no card |
| **P0-RENAME** | «Data de faturamento» na timeline/ficha | MFE + help | Grep timeline sem «entrega do pedido» ambíguo |
| **P0-OPP** | Filtros Conta: status, período, OV, produto/família | MFE (+ BFF) | Caso «drives abertos no período» |
| **P1-FUNNEL** | Aviso cobertura CRM | MFE content | Copy sem inventar data sem fonte |
| **P2-CONF** | Confirmação pedidos | commercial-api F7 + MFE | Spec + SLA |
| **P2-SALA** | Sala de interação | commercial-api + MFE | Spec |
| **P2-DIR** | Reunião Diretoria | MFE | Após modelo |
| **P2-MYVEG** | Integração MyVEG | Discovery | Relatório PCP/Elaine/Michael |

Cada ID = commit próprio quando executado. **Esta entrega (ago/2026-2 docs) não implementa código P0.**

---

## 4. GR de Vendas → TV Dashboard

- **Objetivo ata:** primeiro GR do Depto. de Vendas até fim de **agosto/2026**.
- **Onde implementar:** app **TV Dashboard** (`plugins/tv-dashboard`), slides/playlist GR, dados live api-delpi / painéis já existentes no Comercial.
- **O que o Comercial faz:** continua sendo fonte de KPIs (ROL, carteira, funil, OTD); **não** duplicar editor de GR no MFE Comercial.
- **Próximo passo TV:** definir indicadores com Junior/Laércio; montar playlist GR Vendas; ver nota em [plugins/tv-dashboard/README.md](../../../plugins/tv-dashboard/README.md).

---

## 5. Relação com docs existentes

| Doc | Papel vs esta ata |
|-----|-------------------|
| [ATA-MAPA-NECESSIDADES.md](./ATA-MAPA-NECESSIDADES.md) | Ata 1 — inventário amplo; atualizar status meta/MTD/confirmação/OTD/GR→TV |
| [ATA-FOLLOWUP-IMPLEMENTACOES-AGO2026.md](./ATA-FOLLOWUP-IMPLEMENTACOES-AGO2026.md) | Follow-up pedidos/Kanban/Meu Dia; apontar epicos sala/confirmação/Diretoria/MyVEG para cá |
| [KPI-FICHAS.md](./KPI-FICHAS.md) | Formalizar regra meta proporcional diária em KPI-ROL |
| [GESTAO-A-VISTA.md](./GESTAO-A-VISTA.md) | Nav futuro Diretoria; GR = TV |
| [WIREFRAMES.md](./WIREFRAMES.md) | Stubs WF-CONF / WF-DIR / rename timeline |
| [API-ROUTES.md](./API-ROUTES.md) | F7 order-confirmations já catalogado; MyVEG/Diretoria = investigar |

---

## 6. Critérios de pronto (documentação desta ata)

- [x] Matriz §5–§40 com status e próximo passo
- [x] GR explícito como **TV-GR**
- [x] Itens **Existe** não listados como «implementar de novo»
- [ ] Índices README / MFE / commercial-api / TV apontam para este doc (E2)
