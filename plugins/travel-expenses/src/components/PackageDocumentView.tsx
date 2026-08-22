import type { ReactNode } from "react";
import {
  DelpiLogoMark,
  DocumentFooter,
  DocumentHeader,
  DocumentPage,
  DocumentReader,
  resolveDelpiLogoUrl,
} from "@delpi/plugin-ui/index";

import type { ReportDetail } from "../api/travelExpensesApi";
import { CATEGORY_LABELS, formatBrl, formatDate, UNIT_LABELS } from "../constants/labels";
import { ReportExpenseAttachmentsSection } from "./ReportExpenseAttachmentsSection";
import { ReportPixKeySection } from "./ReportPixKeySection";
import { TravelBrandBar } from "./TravelBrandBar";
import type { ReceiptPreviewAsset } from "../utils/reportAttachments";

type Props = {
  report: ReportDetail;
  toolbar?: ReactNode;
  receiptPreviews?: ReceiptPreviewAsset[];
};

function TravelDocumentFooter({
  left,
  center,
  right,
}: {
  left?: ReactNode;
  center?: ReactNode;
  right?: ReactNode;
}) {
  return (
    <div className="te-doc-footer">
      <DocumentFooter left={left} center={center} right={right} className="te-doc-footer__meta" />
      <TravelBrandBar className="te-doc-footer__bar" />
    </div>
  );
}

export function PackageDocumentView({
  report,
  toolbar,
  receiptPreviews = [],
}: Props) {
  const byCategory = new Map<string, number>();
  for (const expense of report.expenses) {
    byCategory.set(
      expense.categoryId,
      (byCategory.get(expense.categoryId) || 0) + Number(expense.amountBrl || 0),
    );
  }

  const logoUrl = resolveDelpiLogoUrl();
  const unitLabel = UNIT_LABELS[report.unitCode] || report.unitCode;
  const costCenter = [report.costCenterCode, report.costCenterLabel].filter(Boolean).join(" — ");

  return (
    <DocumentReader toolbar={toolbar} ariaLabel="Relatório da prestação de viagem">
      <DocumentPage
        className="te-doc-page"
        header={
          <div className="te-doc-header">
            <DocumentHeader
              className="te-doc-header__main"
              logo={
                logoUrl ? (
                  <img src={logoUrl} alt="DELPI Conexões Elétricas" className="te-doc-header__logo-img" />
                ) : (
                  <DelpiLogoMark className="te-doc-header__logo-mark" title="DELPI" />
                )
              }
              title="Prestação de contas — despesas de viagem"
              subtitle={`${report.number} · ${unitLabel}`}
            />
            <TravelBrandBar className="te-doc-header__bar" />
          </div>
        }
        watermark={<DelpiLogoMark className="te-doc-watermark" title="" />}
        footer={
          <TravelDocumentFooter
            left="www.delpi.com.br"
            center={
              <>
                DELPI Conexões Elétricas
                <br />
                {unitLabel}
              </>
            }
            right={report.number}
          />
        }
      >
        <div className="te-doc-summary">
          <div className="te-doc-summary__grid">
            <p className="te-doc-info">
              <strong>Destino</strong>
              {report.destination || "—"}
            </p>
            <p className="te-doc-info">
              <strong>Motivo</strong>
              {report.purpose || "—"}
            </p>
            <p className="te-doc-info">
              <strong>Viajante</strong>
              {report.createdByName || "—"}
            </p>
            <p className="te-doc-info">
              <strong>Período</strong>
              {formatDate(report.periodStart)} – {formatDate(report.periodEnd)}
            </p>
            <p className="te-doc-info">
              <strong>Centro de custo</strong>
              {costCenter || "—"}
            </p>
            <p className="te-doc-info">
              <strong>Total</strong>
              {formatBrl(report.totalAmountBrl)}
            </p>
          </div>
        </div>

        <div className="te-doc-section">
          <h3 className="te-doc-section-title">Totais por categoria</h3>
          <table className="te-package-table te-doc-table">
            <thead>
              <tr>
                <th>Categoria</th>
                <th>Total</th>
              </tr>
            </thead>
            <tbody>
              {[...byCategory.entries()].map(([categoryId, total]) => (
                <tr key={categoryId}>
                  <td>{CATEGORY_LABELS[categoryId] || categoryId}</td>
                  <td>{formatBrl(total)}</td>
                </tr>
              ))}
              <tr>
                <td>
                  <strong>Total geral</strong>
                </td>
                <td>
                  <strong>{formatBrl(report.totalAmountBrl)}</strong>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div className="te-doc-section">
          <h3 className="te-doc-section-title">Despesas</h3>
          <table className="te-package-table te-doc-table">
            <thead>
              <tr>
                <th>Data</th>
                <th>Categoria</th>
                <th>Estabelecimento</th>
                <th>Valor</th>
                <th>Cupom</th>
              </tr>
            </thead>
            <tbody>
              {report.expenses.map((expense) => (
                <tr key={expense.id}>
                  <td>{formatDate(expense.expenseDate)}</td>
                  <td>{CATEGORY_LABELS[expense.categoryId] || expense.categoryId}</td>
                  <td>{expense.merchant || "—"}</td>
                  <td>{formatBrl(expense.amountBrl)}</td>
                  <td>{expense.receipts.length ? `${expense.receipts.length} arquivo(s)` : "ausente"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <ReportPixKeySection report={report} />

        <ReportExpenseAttachmentsSection report={report} receiptPreviews={receiptPreviews} />

        <p className="te-doc-note">Documento de rascunho — ainda não enviado ao financeiro.</p>
      </DocumentPage>
    </DocumentReader>
  );
}
