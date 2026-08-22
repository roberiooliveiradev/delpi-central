import { useEffect, useState } from "react";

import { fetchReceiptBlob, type ReportDetail } from "../api/travelExpensesApi";
import type { ReceiptPreviewAsset } from "../utils/reportAttachments";

export function useReportReceiptPreviews(reportId: string, report: ReportDetail | null) {
  const [receiptPreviews, setReceiptPreviews] = useState<ReceiptPreviewAsset[]>([]);

  useEffect(() => {
    if (!report) {
      setReceiptPreviews([]);
      return () => undefined;
    }

    let cancelled = false;
    const objectUrls: string[] = [];

    const jobs = report.expenses.flatMap((expense) =>
      expense.receipts.map(async (receipt) => {
        try {
          const blob = await fetchReceiptBlob(reportId, expense.id, receipt.id);
          const previewUrl = URL.createObjectURL(blob);
          objectUrls.push(previewUrl);
          return {
            receiptId: receipt.id,
            expenseId: expense.id,
            fileName: receipt.originalName,
            mimeType: receipt.mimeType,
            previewUrl,
          } satisfies ReceiptPreviewAsset;
        } catch {
          return {
            receiptId: receipt.id,
            expenseId: expense.id,
            fileName: receipt.originalName,
            mimeType: receipt.mimeType,
            previewUrl: null,
          } satisfies ReceiptPreviewAsset;
        }
      }),
    );

    void Promise.all(jobs).then((items) => {
      if (!cancelled) setReceiptPreviews(items);
    });

    return () => {
      cancelled = true;
      objectUrls.forEach((url) => URL.revokeObjectURL(url));
    };
  }, [report, reportId]);

  return receiptPreviews;
}
