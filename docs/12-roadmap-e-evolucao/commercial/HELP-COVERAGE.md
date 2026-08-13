# Cobertura de help — Portal Comercial

> Atualizado em 2026-08-13 (E2.S5).  
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

## Allowlist / estado final

**E2.S5 concluído:** gaps auditados = **0**. Allowlist vazia (sem isenções documentadas além das fixas acima).

Gate: `src/content/helpCoverage.structural.test.mjs` — falha se surgir gap fora da allowlist ou entrada stale. Crescer a allowlist exige justificativa explícita no PR (isensão documentada neste arquivo).

## Snapshot

| Métrica | Valor |
|---------|-------|
| Gaps (auditor) | **0** |
| Allowlist | `[]` |
| Isenções documentadas extras | nenhuma |

## Referências cobertas (manter)

- `components/FilterBar.tsx` + `OpenOrdersTable.tsx` + `openOrdersColumnHelp.ts`
- `features/analytics/components/AnalyticsFilters.tsx`
- `features/seller-portfolios/SellerPortfoliosList.tsx` (colunas)
- Contatos locais: `AccountContactsPanel` → `CM_HELP.customerDetail.contact*`
- PDF proposta: `ProposalDetailPage` → `CM_HELP.proposals.pdfContact*`
- Carteiras: detalhe / uncovered / bulk transfer → `CM_HELP.sellerPortfolios.col*` / `bulkTransferConfirmFrom`
- Auditoria Minha Carteira: `MyPortfolioAuditSection` → `CM_HELP.customers.portfolioAudit`

## CLI

```bash
cd plugins/commercial
node scripts/audit_help_coverage.mjs
node scripts/audit_help_coverage.mjs --markdown
node scripts/audit_help_coverage.mjs --write-allowlist   # só na baseline / reset consciente
```
