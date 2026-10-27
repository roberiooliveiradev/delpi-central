/**
 * Páginas contextuais de relatório — UX-011 (Plano 113 §26, doc 112 §46).
 *
 * A aba «Relatórios e divergências» continua hub; o detalhamento completo
 * de cada relatório abre rota contextual própria dentro do Fechamento
 * Mensal (`closing/monthly-closing/{period}/reports/{reportKey}`) — não
 * é quarta aba nem rota legada.
 *
 * Reuso: as páginas existentes de Baixas Financeiras e Estoque/P7 são
 * renderizadas em modo `reportContext` (competência travada + seções do
 * relatório), sem duplicar filtros/tabela/paginação. O slot de PDF é o
 * mesmo estado honesto para todo relatório sem produtor homologado.
 */
import type { ReactNode } from "react";

import {
  CfActionButton,
  CfEmptyState,
  cfEmptyStateClassNames,
} from "../../app/controllershipFinanceUi";
import { FinancialSettlementsPage } from "./FinancialSettlementsPage";
import { StockInventoryPage } from "./StockInventoryPage";

/** Famílias com página contextual implementada (hub → rota). */
export type ReportKey = "financial-settlements" | "stock-inventory";

export type ReportFamily = "settlements" | "stock";

export const FAMILY_TO_REPORT_KEY: Record<ReportFamily, ReportKey> = {
  settlements: "financial-settlements",
  stock: "stock-inventory",
};

export const REPORT_KEY_TO_FAMILY: Record<ReportKey, ReportFamily> = {
  "financial-settlements": "settlements",
  "stock-inventory": "stock",
};

export const REPORT_KEY_LABELS: Record<ReportKey, string> = {
  "financial-settlements": "Baixas financeiras",
  "stock-inventory": "Estoque e conciliação",
};

export function isReportKey(value: string | undefined): value is ReportKey {
  return (
    value === "financial-settlements" || value === "stock-inventory"
  );
}

export function MonthlyReportPage({
  period,
  reportKey,
  onBack,
}: {
  period: string;
  reportKey: string;
  onBack: () => void;
}) {
  const backButton: ReactNode = (
    <div className="cf-settlements-actions">
      <CfActionButton variant="ghost" onClick={onBack}>
        ← Voltar para Relatórios e divergências
      </CfActionButton>
    </div>
  );

  if (!isReportKey(reportKey)) {
    return (
      <div className="cf-page-stack">
        {backButton}
        <CfEmptyState
          classNames={cfEmptyStateClassNames}
          defaultMessage="Este relatório ainda não possui uma página contextual — verifique a matriz R01–R15 na aba Relatórios e divergências."
        />
      </div>
    );
  }

  return (
    <div
      className="cf-page-stack"
      aria-label={`Relatório ${REPORT_KEY_LABELS[reportKey]}`}
    >
      {backButton}
      {reportKey === "financial-settlements" ? (
        <FinancialSettlementsPage reportContext={{ period }} />
      ) : (
        <StockInventoryPage reportContext={{ period }} />
      )}
    </div>
  );
}
