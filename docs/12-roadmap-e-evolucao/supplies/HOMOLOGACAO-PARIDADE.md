# HOMOLOGACAO-PARIDADE — Portal vs legado

Depreciação **somente** com esta checklist assinada (owner Suprimentos + QA), analogia [HOMOLOGACAO-PARIDADE-PEDIDOS.md](../commercial/HOMOLOGACAO-PARIDADE-PEDIDOS.md).

Para cada ativo: Funcionalidades · Filtros · KPIs · Tabelas · Drilldowns · Exports · Filiais · Permissões · URLs · Favoritos · Deep links · Erros · Performance · Dados · Ajuda.

---

## 1. `dashboard-supplies`

| Item | Critério Portal | Status |
|------|-----------------|--------|
| Home atalhos + KPIs | WF-01 + WF-02 | pendente |
| `/cpv` | Overview drill ou `/indicators` âncora CPV | pendente |
| `/otd` + ranking atrasos | WF-11 + WF-07 | pendente |
| `/stock` | WF-15 | pendente |
| `/inventory-turnover` | WF-15/giro | pendente |
| `/negotiation-savings` | WF-18 | pendente |
| Filtros branch/datas/location/competência | FiltersKit BFF | pendente |
| Export PDF/tabular | equivalente | pendente |
| Meta SI nos KPIs | enrich SI | pendente |
| Perm `dashboard-supplies.view` | alias analytics | pendente |
| URL `/apps/dashboard-supplies*` | 302 após cutover | pendente |
| Ajuda tooltips | HELP sync | pendente |

## 2. `purchase-requests`

| Item | Critério | Status |
|------|----------|--------|
| Lista grão item + fail-closed | mesmo contrato 0.2 | pendente |
| Filtros (branch, datas, SC, solicitante, CC, produto, fornecedor, pedido, estágio) | iguais | pendente |
| view-all | iguais | pendente |
| unit 01/02 | iguais | pendente |
| Admin mapping/scopes/notif | `/administration` | pendente |
| Export | cap export | pendente |
| Notificações PO/receipt | jobs C2 | pendente |
| Deep link query filtros | URL shareable | pendente |
| 403 filial / vazio CC | testado | pendente |

## 3. `estoque-seguranca`

| Item | Critério | Status |
|------|----------|--------|
| Monitoramento saldo×ESTSEG | WF-16 | pendente |
| Filtros filial/grupo/situação | iguais | pendente |
| Detalhe extrato SC7/SD4 + botão SC1 | 360/modal | pendente |
| Fornecedores + última compra + price history | 360 item | pendente |
| `/analise-consumo` | `/safety-stock/consumption-analysis` + alias | pendente |
| Simulação somente leitura | iguais | pendente |
| Export Excel | iguais | pendente |
| Perms filial-sc/es | aliases 01/02 | pendente |

## 4. BIs externos (após dump)

Tabela a preencher na E1.S1: uma linha por app encontrado no Core. Sem URL = não homologar paridade fictícia.

---

## Assinatura (quando executar)

| Ativo | Data | Owner Suprimentos | QA | Notas |
|-------|------|-------------------|----|-------|
| dashboard-supplies | | | | |
| purchase-requests | | | | |
| estoque-seguranca | | | | |
