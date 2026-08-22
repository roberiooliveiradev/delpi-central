import type { ReportDetail } from "../api/travelExpensesApi";
import {
  formatExpenseAttachmentLabel,
  isImageMime,
  type ReceiptPreviewAsset,
} from "../utils/reportAttachments";

type Props = {
  report: ReportDetail;
  receiptPreviews: ReceiptPreviewAsset[];
};

export function ReportExpenseAttachmentsSection({ report, receiptPreviews }: Props) {
  const expensesWithReceipts = report.expenses.filter((expense) => expense.receipts.length > 0);
  if (expensesWithReceipts.length === 0) {
    return null;
  }

  const previewByReceiptId = new Map(
    receiptPreviews.map((item) => [item.receiptId, item]),
  );

  return (
    <div className="te-doc-section te-doc-attachments">
      <h3 className="te-doc-section-title">Anexos das despesas</h3>
      <p className="te-doc-attachments-intro">
        Cupons e comprovantes agrupados pela despesa correspondente.
      </p>
      {expensesWithReceipts.map((expense) => (
        <section key={expense.id} className="te-doc-attachment-group">
          <h4 className="te-doc-attachment-heading">{formatExpenseAttachmentLabel(expense)}</h4>
          <div className="te-doc-attachment-grid">
            {expense.receipts.map((receipt) => {
              const preview = previewByReceiptId.get(receipt.id);
              const showImage = preview?.previewUrl && isImageMime(receipt.mimeType);
              return (
                <figure key={receipt.id} className="te-doc-attachment-item">
                  {showImage ? (
                    <img
                      src={preview.previewUrl}
                      alt={receipt.originalName}
                      className="te-doc-attachment-image"
                    />
                  ) : (
                    <div className="te-doc-attachment-file" aria-hidden="true">PDF</div>
                  )}
                  <figcaption className="te-doc-attachment-caption">{receipt.originalName}</figcaption>
                </figure>
              );
            })}
          </div>
        </section>
      ))}
    </div>
  );
}
