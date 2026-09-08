# PLAYBOOK — Portal Suprimentos (Minha DELPI)

> **Status:** playbook oficial de produto/arquitetura · **set/2026 · documentação**  
> **Nome ao usuário:** **Portal Suprimentos**  
> **Id:** `supplies` · **basePath:** `/apps/supplies` · **API:** `supplies-api`  
> Complementos: [INVENTARIO](./INVENTARIO-ATIVOS.md) · [DESIGN-IA](./DESIGN-IA-SUPRIMENTOS.md) · [IMPLEMENTATION-PLAN](./IMPLEMENTATION-PLAN.md) · ADRs

---

## 1. Propósito

Hub **operacional, analítico e gerencial** do domínio de Suprimentos. Não é coleção de links, nem cópia dos BIs, nem segundo dashboard isolado.

Substitui progressivamente:

```text
vários BIs + plugins + Sheets + filtros diferentes
        ↓
Portal Suprimentos → Meu trabalho · Compras · Fornecedores · Produtos/MP · Estoques · Negociações · Gestão
```

### 1.1 Pilares

1. **Minhas atividades** — worklist, alertas, follow-ups, SC/PC críticos.
2. **Compras** — solicitações, pedidos, entregas/atrasos, importações, alçadas (quando validadas).
3. **Fornecedor 360** — identidade TOTVS + OTD + qualidade projetada + notas Delpi.
4. **Produto / MP 360** — saldo, ESTSEG, onde usado, fornecedores, última compra, preço.
5. **Estoques** — valor, saldos, segurança, giro, consumo.
6. **Negociações** — savings IDD, variação de preço (sem segunda meta).
7. **Gestão** — Overview 6–8 KPIs + SI.
8. **Administração** — escopos, mappings, settings.

### 1.2 Matriz dores × cobertura

Dor central: o time não tem visão única do ciclo **necessidade → SC → PC → entrega → estoque → fornecedor**, e opera com regras/filtros fragmentados.

| # | Dor | Cobertura | Onde | Fase | Lacuna |
|---|-----|-----------|------|------|--------|
| 1 | Informações em 6–8 apps | **Sim** (roadmap) | Hub WF-01 | E3–E4 | BIs sem URL |
| 2 | SC vs ES com perms divergentes | **Parcial** | PERFIS aliases | E3 | Dump comprador ES |
| 3 | Atraso em BI e em OTD | **Parcial** | WF-07/11 | E9 | Regra do BI |
| 4 | Estoque vs ESTSEG vs giro misturados | **Sim** | WF-15–17 | E7–E8 | BI SC |
| 5 | Item fragmentado (onde-usado, saldo, preço) | **Sim** | WF-13 | E11 | — |
| 6 | Sem Fornecedor 360 | **Sim** (novo) | WF-10 | E10 | Qualidade = projeção |
| 7 | Savings em Sheets e SI | **Parcial** | KPI-SAVINGS | E12 | Quem edita a planilha |
| 8 | Sem worklist do comprador | **Sim** (novo P0) | WF-03 | E13 | Estado Delpi novo |
| 9 | Importações só em BI | **Bloqueado** | WF-08 | E1.S1 | Sem contrato TOTVS no git |
| 10 | Alçadas só em BI | **Bloqueado** | — | E1 | `C7_APROV` ≠ UI |
| 11 | Frete misturado com compras | **Fora** | DEEP_LINK financeiro | — | — |
| 12 | Qualidade no ranking de compras | **Parcial** | 360 INTEGRAR | E10 | Processo Qualidade |

---

## 2. Decisões irrevogáveis

1. Identidade [ADR-004](./adr/ADR-004-plugin-identity-and-css-root.md).
2. MFE → só supplies-api [ADR-001](./adr/ADR-001-supplies-api.md).
3. Absorção progressiva SC [ADR-002](./adr/ADR-002-purchase-requests-api.md).
4. Coexistência até paridade [ADR-003](./adr/ADR-003-legacy-app-consolidation.md).
5. Home ≠ Overview.
6. Capability-driven.
7. Identificadores novos em inglês; `filial-01/02` preservado.
8. Kit `@delpi/plugin-ui`; CSS root `.dashboard-supplies-portal`; zero `.delpi-ui-*` no MFE.
9. Ajuda no mesmo entregável de feature user-facing.
10. Sem escrita TOTVS neste roadmap.
11. Sem espelho TOTVS no Postgres.
12. BIs PO = dump Core antes de depreciação [ADR-005](./adr/ADR-005-external-bi-core-dump.md).
13. Unidades = eixo B `supplies.unit.filial-{TOTVS}` — não inflar capabilities [ADR-006](./adr/ADR-006-unit-permissions.md).

---

## 3. Arquitetura

Ver README e MATRIZ-BOUNDARIES. Observabilidade: correlation id, logs estruturados, sem token em log, timeouts, métricas de BFF (latência gateway, 403 filial, cache hit). Detalhe em [INTEGRACOES.md](./INTEGRACOES.md).

---

## 4. Capabilities (produto)

Não são permission codes 1:1. O MFE deriva flags a partir do catálogo em [PERFIS-E-PERMISSOES.md](./PERFIS-E-PERMISSOES.md) + aliases legados.

| Cap | Telas |
|-----|-------|
| `shell` | Home, busca, help, palette (`supplies.access`) |
| `analytics` | Overview, CPV, OTD gerencial, giro, savings |
| `purchaseRequests` | Lista/detalhe SC |
| `purchaseRequestsAll` | Bypass CC |
| `inventory` | Controle estoque + ESTSEG |
| `suppliers` | Lista + 360 |
| `products` | Consulta item + 360 |
| `worklist` | Minhas atividades / alertas |
| `admin` | Administração |

Unidades **não** são cap de tela: eixo B `allowedUnits[]` derivado só de `supplies.unit.filial-*` ([ADR-006](./adr/ADR-006-unit-permissions.md)).

---

## 5. Jornadas P0

1. Abrir Home e agir no alerta (SC parada, atraso, déficit ESTSEG).
2. Filtrar unidade (catálogo × `allowedUnits`; backend valida).
3. Consultar SC e exportar se cap.
4. Abrir item 360 (saldo + onde usado + última compra).
5. Abrir fornecedor 360 (OTD + PCs abertos).
6. Ver Overview (6–8 KPIs) e furar para página de foco.
7. Abrir Ajuda / Quero→onde.

---

## 6. Novas funcionalidades (após o existente)

Legenda dado: `DADO_EXISTENTE` · `DERIVAVEL` · `ENDPOINT_NOVO` · `ESTADO_NOVO_SUPPLIES_API` · `VALIDACAO_FUNCIONAL`

### Mercado vs Delpi

| PADRAO_DE_MERCADO (2025–26) | DECISAO_DELPI |
|-----------------------------|---------------|
| Supplier 360 + scorecard contínuo a partir do ERP | **P0/P1** 360 com OTD+volume+qualidade projetada; scorecard composto **P2** após fichas |
| Worklist / exception-based buying | **P0** Minhas atividades (derivável + estado Delpi) |
| Lead time real × cadastrado | **P1** DERIVAVEL (BZ_PE vs SD1) — precisa ficha |
| AI follow-up automático a fornecedor | **P3** — fora até haver canal e política |
| Predictive delay | **P3** — dados 12–24m existem em parte; sem ML neste portal |
| Onboarding de fornecedor / GED | **Fora** — cadastro TOTVS |

### Backlog priorizado

**P0**

- Worklist (SC aging, PC atrasado, déficit ESTSEG) — DERIVAVEL + ESTADO_NOVO (ack/follow-up)
- Fornecedor 360 leitura — DADO_EXISTENTE composto
- Produto 360 leitura — DADO_EXISTENTE composto
- Home + Overview + shell capability — DADO_EXISTENTE
- Paridade dashboard KPIs via BFF — DADO_EXISTENTE
- Paridade SC via gateway — DADO_EXISTENTE
- Paridade ESTSEG via BFF — DADO_EXISTENTE
- Ajuda esqueleto — conteúdo

**P1**

- Pedidos de compra lista/detalhe (OTD panel) — DADO_EXISTENTE sem MFE
- Lead time real × BZ_PE — DERIVAVEL + VALIDACAO
- Aging SC/PC na UI — DERIVAVEL
- Price variance / histórico no 360 — DADO_EXISTENTE
- Alertas persistidos (atribuição) — ESTADO_NOVO
- Importações se dump Core revelar contrato — VALIDACAO
- Cobertura / slow moving (regras a ficha) — VALIDACAO

**P2**

- Scorecard composto (OTD+qualidade+preço)
- Concentração / fornecedor único
- Alçadas UI se BI confirmar regra
- Comparativo fornecedores
- Obsolescência

**P3**

- Predição de atraso
- Follow-up automático e-mail
- Simulação ESTSEG **gravando** Protheus (escrita — fora do ADR atual)

---

## 7. RBAC e multi-unidade

Dois eixos: capability (o quê) × `supplies.unit.filial-{TOTVS}` (onde). Dado TOTVS exige **AND**. Nova unidade = **um** permission, sem variantes por tela. `manage` não libera site. Backend valida `branch` contra o conjunto do JWT; recorte omitido = união das units do usuário. Superadmin = único bypass, auditado. Detalhe: [PERFIS-E-PERMISSOES.md](./PERFIS-E-PERMISSOES.md) · [ADR-006](./adr/ADR-006-unit-permissions.md).

---

## 8. KPIs

Seis a oito no Overview: OTD, valor estoque, giro, CPV (ou CPV/ROL), savings, SC pendentes, atrasos, materiais críticos. Fichas em [KPI-FICHAS.md](./KPI-FICHAS.md). Sem fórmula inventada.

---

## 9. UX

[DESIGN-IA-SUPRIMENTOS.md](./DESIGN-IA-SUPRIMENTOS.md) · [WIREFRAMES.md](./WIREFRAMES.md). Família visual do Comercial; prefixo `sp-`; touch 44×44; tabelas com modo stacked/cards ≤768px.

---

## 10. Roadmap (fases)

E1 validação residual → E2 API → E3–E4 shell/Home → E5 Overview → E6 SC → E7–E8 estoques → E9 OTD/PC → E10–E11 360 → E12 savings → E13 worklist → E14 SI → E15 admin → E16 ajuda → E17–E18 paridade/cutover → E19 P2/P3 → E20 verify.

---

## 11. Riscos e gates

Ver README. Gate de paridade por ativo em [HOMOLOGACAO-PARIDADE.md](./HOMOLOGACAO-PARIDADE.md).

---

## 12. Cutover

[CUTOVER-RUNBOOK.md](./CUTOVER-RUNBOOK.md). Nada é removido neste documento.
