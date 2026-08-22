import type { Expense } from "../api/travelExpensesApi";
import { CATEGORY_LABELS, formatBrl, formatDate } from "../constants/labels";

export type ReceiptPreviewAsset = {
  receiptId: string;
  expenseId: string;
  fileName: string;
  mimeType: string;
  previewUrl: string | null;
};

export function formatExpenseAttachmentLabel(expense: Expense) {
  const category = CATEGORY_LABELS[expense.categoryId] || expense.categoryId;
  const merchant = expense.merchant?.trim() || "Sem estabelecimento";
  return `${formatDate(expense.expenseDate)} · ${category} · ${merchant} · ${formatBrl(expense.amountBrl)}`;
}

export function isImageMime(mimeType: string | null | undefined) {
  return String(mimeType || "").toLowerCase().startsWith("image/");
}
