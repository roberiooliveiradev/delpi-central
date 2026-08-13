# Cobertura de help — Portal Comercial

> Gerado em 2026-08-13 a partir de `scripts/audit_help_coverage.mjs`.  
> Catálogo: `plugins/commercial/src/content/helpTooltips.ts` (`CM_HELP`).  
> Allowlist: `plugins/commercial/src/content/help_coverage_allowlist.json`.

## Regras

| Superfície | Prop canônica | Texto |
|------------|---------------|-------|
| Input / select / date / textarea / multi | `hint` (ou `labels.hint`) | `CM_HELP.*` |
| Coluna DataTable | `headerHint` | `CM_HELP.*` |
| Proibido | `hint="…"` literal novo; ícone «?» solto | — |

## Isenções fixas (não entram no auditor)

- Colunas `actions` / `action` / `expand` / `index` / `#` / `rowIndex`
- Campos `Commercial*Field` **sem** `label` / `fieldLabel` / `labels.title`
- `app/commercialUi.ts` (factories)

## Allowlist

Baseline com **todos** os gaps atuais. Ondas E2 **só removem** entradas. Crescer a allowlist exige justificativa explícita no PR.

Gate: `src/content/helpCoverage.structural.test.mjs` — falha se surgir gap fora da allowlist ou entrada stale.

## Snapshot por área

| Área | Fields | Columns |
|------|--------|---------|
| administration | 5 | 5 |
| analytics | 1 | 18 |
| customers | 13 | 33 |
| proposals | 6 | 3 |
| seller-portfolios | 1 | 6 |

**Totais:** 26 fields + 65 columns = **91** gaps.

## Referências já cobertas (manter)

- `components/FilterBar.tsx` + `OpenOrdersTable.tsx` + `openOrdersColumnHelp.ts`
- `features/analytics/components/AnalyticsFilters.tsx`
- `features/seller-portfolios/SellerPortfoliosList.tsx` (colunas)

## Gaps detalhados

| File | Kind | Id |
|------|------|----|
| `features/administration/AdministrationGroupsPage.tsx` | field | `newGroupName` |
| `features/administration/AdministrationGroupsPage.tsx` | field | `renameDraft` |
| `features/administration/AdministrationTeamPage.tsx` | field | `search` |
| `features/administration/AdministrationTeamPage.tsx` | field | `groupId` |
| `features/administration/AdministrationTeamPage.tsx` | field | `portfolioId` |
| `features/administration/AdministrationTeamPage.tsx` | column | `person` |
| `features/administration/AdministrationTeamPage.tsx` | column | `online` |
| `features/administration/AdministrationTeamPage.tsx` | column | `email` |
| `features/administration/AdministrationTeamPage.tsx` | column | `groups` |
| `features/administration/AdministrationTeamPage.tsx` | column | `portfolios` |
| `features/analytics/AnalyticsOpportunitiesPage.tsx` | field | `Busca` |
| `features/analytics/AnalyticsOpportunityDetailPage.tsx` | column | `desc` |
| `features/analytics/AnalyticsOpportunityDetailPage.tsx` | column | `group` |
| `features/analytics/AnalyticsOpportunityDetailPage.tsx` | column | `type` |
| `features/analytics/AnalyticsOpportunityDetailPage.tsx` | column | `qty` |
| `features/analytics/AnalyticsOpportunityDetailPage.tsx` | column | `process` |
| `features/analytics/AnalyticsOpportunityDetailPage.tsx` | column | `stage` |
| `features/analytics/AnalyticsOpportunityDetailPage.tsx` | column | `start` |
| `features/analytics/AnalyticsOpportunityDetailPage.tsx` | column | `end` |
| `features/analytics/AnalyticsOpportunityDetailPage.tsx` | column | `dur` |
| `features/analytics/AnalyticsOpportunityDetailPage.tsx` | column | `status` |
| `features/analytics/AnalyticsOtdPage.tsx` | column | `order` |
| `features/analytics/AnalyticsOtdPage.tsx` | column | `status` |
| `features/analytics/AnalyticsOtdPage.tsx` | column | `promised` |
| `features/analytics/AnalyticsOtdPage.tsx` | column | `otd01` |
| `features/analytics/AnalyticsTeamPage.tsx` | column | `customers` |
| `features/analytics/AnalyticsTeamPage.tsx` | column | `lines` |
| `features/analytics/AnalyticsTeamPage.tsx` | column | `openValue` |
| `features/analytics/components/CommercialProposalsTable.tsx` | column | `ov` |
| `features/customers/billing/components/CustomerBillingFilters.tsx` | field | `Data inicial` |
| `features/customers/billing/components/CustomerBillingFilters.tsx` | field | `Data final` |
| `features/customers/billing/components/CustomerBillingFilters.tsx` | field | `Situação` |
| `features/customers/billing/components/CustomerBillingFilters.tsx` | field | `Busca` |
| `features/customers/billing/components/CustomerInvoiceItems.tsx` | column | `description` |
| `features/customers/billing/components/CustomerInvoicesTable.tsx` | column | `issue` |
| `features/customers/billing/components/CustomerInvoicesTable.tsx` | column | `invoice` |
| `features/customers/billing/components/CustomerInvoicesTable.tsx` | column | `sales-order` |
| `features/customers/billing/components/CustomerInvoicesTable.tsx` | column | `customer-order` |
| `features/customers/billing/components/CustomerInvoicesTable.tsx` | column | `situation` |
| `features/customers/billing/components/CustomerInvoicesTable.tsx` | column | `items` |
| `features/customers/billing/components/CustomerInvoicesTable.tsx` | column | `value` |
| `features/customers/components/AccountContactsPanel.tsx` | field | `Nome completo` |
| `features/customers/components/AccountContactsPanel.tsx` | field | `Cargo ou função` |
| `features/customers/components/AccountContactsPanel.tsx` | field | `Canal preferencial` |
| `features/customers/components/AccountContactsPanel.tsx` | field | `E-mail` |
| `features/customers/components/CustomerBillingSeriesChart.tsx` | field | `Cliente` |
| `features/customers/components/CustomerBillingSeriesChart.tsx` | field | `Data inicial` |
| `features/customers/components/CustomerBillingSeriesChart.tsx` | field | `Data final` |
| `features/customers/components/CustomerOpenOrdersPreview.tsx` | column | `issue` |
| `features/customers/components/CustomerOpenOrdersPreview.tsx` | column | `forecast` |
| `features/customers/components/CustomerOpenOrdersPreview.tsx` | column | `value` |
| `features/customers/components/CustomerOpenOrdersPreview.tsx` | column | `status` |
| `features/customers/components/CustomerOpenOrdersPreview.tsx` | column | `opportunity` |
| `features/customers/components/CustomerOrderLines.tsx` | column | `ordered` |
| `features/customers/components/CustomerOrderLines.tsx` | column | `delivered` |
| `features/customers/components/CustomerOrderLines.tsx` | column | `balance` |
| `features/customers/components/CustomerOrderLines.tsx` | column | `delivery` |
| `features/customers/components/CustomerOrderLines.tsx` | column | `open-value` |
| `features/customers/components/CustomerOrdersTable.tsx` | column | `branch` |
| `features/customers/components/CustomerOrdersTable.tsx` | column | `customer-order` |
| `features/customers/components/CustomerOrdersTable.tsx` | column | `lines` |
| `features/customers/components/CustomerOrdersTable.tsx` | column | `overdue` |
| `features/customers/components/CustomerOrdersTable.tsx` | column | `delivery` |
| `features/customers/components/CustomerOrdersTable.tsx` | column | `value` |
| `features/customers/components/CustomerPurchaseEvolutionChart.tsx` | field | `Período` |
| `features/customers/components/CustomersTable.tsx` | column | `nome` |
| `features/customers/components/CustomersTable.tsx` | column | `sellerName` |
| `features/customers/components/CustomersTable.tsx` | column | `city` |
| `features/customers/components/CustomersTable.tsx` | column | `lastPurchaseDate` |
| `features/customers/components/CustomersTable.tsx` | column | `billed12m` |
| `features/customers/components/CustomersTable.tsx` | column | `status` |
| `features/customers/components/CustomersTable.tsx` | column | `valorTotalAberto` |
| `features/customers/components/CustomersTable.tsx` | column | `quantidadePedidosAtrasados` |
| `features/customers/components/CustomersTable.tsx` | column | `proximaEntrega` |
| `features/customers/components/MyPortfolioAuditSection.tsx` | field | `anon:80:<CommercialSelectField label={PORTFOLIO_` |
| `features/proposals/ProposalDetailPage.tsx` | field | `pdfContactValue` |
| `features/proposals/ProposalDetailPage.tsx` | field | `pdfContatoNome` |
| `features/proposals/ProposalDetailPage.tsx` | field | `pdfContatoDepartamento` |
| `features/proposals/ProposalDetailPage.tsx` | field | `pdfContatoEmail` |
| `features/proposals/ProposalDetailPage.tsx` | field | `pdfContatoTelefone` |
| `features/proposals/ProposalDetailPage.tsx` | field | `pdfObservacoes` |
| `features/proposals/ProposalDetailPage.tsx` | column | `qty` |
| `features/proposals/ProposalDetailPage.tsx` | column | `prazo` |
| `features/proposals/ProposalsDocumentsTable.tsx` | column | `ov` |
| `features/seller-portfolios/SellerPortfolioBulkTransferWizard.tsx` | field | `anon:80:<CommercialTextField label={C.confirmFro` |
| `features/seller-portfolios/SellerPortfolioDetail.tsx` | column | `code` |
| `features/seller-portfolios/SellerPortfolioDetail.tsx` | column | `name` |
| `features/seller-portfolios/SellerPortfolioDetail.tsx` | column | `coverage` |
| `features/seller-portfolios/SellerPortfolioDetail.tsx` | column | `user` |
| `features/seller-portfolios/SellerPortfolioDetail.tsx` | column | `role` |
| `features/seller-portfolios/UncoveredCustomersPanel.tsx` | column | `code` |

## CLI

```bash
cd plugins/commercial
node scripts/audit_help_coverage.mjs
node scripts/audit_help_coverage.mjs --markdown
node scripts/audit_help_coverage.mjs --write-allowlist   # só na baseline / reset consciente
```
