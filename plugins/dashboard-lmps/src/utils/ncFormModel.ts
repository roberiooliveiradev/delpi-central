import type {
  LmpNcProductLine,
  LmpNcStatus,
  LmpNonconformity,
  LmpNonconformityPayload,
} from "../types/lmpNonconformity";

export type NcFormState = {
  status: LmpNcStatus;
  sale_number: string;
  customer_name: string;
  launch_date: string;
  last_revision_date: string;
  executed_by: string;
  released_by: string;
  defect_description: string;
  corrective_actions: string;
  technical_opinion: string;
  products: LmpNcProductLine[];
};

export function toDateInput(iso: string | null | undefined): string {
  if (!iso) return "";
  return iso.slice(0, 10);
}

export function formatDisplayDate(iso: string | null | undefined): string {
  if (!iso) return "—";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleString("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function formatDisplayDateOnly(iso: string | null | undefined): string {
  if (!iso) return "—";
  const text = iso.slice(0, 10);
  const [y, m, d] = text.split("-");
  if (!y || !m || !d) return iso;
  return `${d}/${m}/${y}`;
}

/** OV tipicamente numérica (ex.: 000160). */
export function looksLikeOvCode(value: string): boolean {
  return /^\d{4,20}$/.test(value.trim());
}

export function emptyNcForm(): NcFormState {
  return {
    status: "open",
    sale_number: "",
    customer_name: "",
    launch_date: "",
    last_revision_date: "",
    executed_by: "",
    released_by: "",
    defect_description: "",
    corrective_actions: "",
    technical_opinion: "",
    products: [],
  };
}

export function recordToNcForm(record: LmpNonconformity): NcFormState {
  const products =
    record.products?.length
      ? record.products.map((p) => ({
          product_code: p.product_code ?? "",
          product_description: p.product_description ?? "",
        }))
      : (record.product_codes ?? []).map((code) => ({
          product_code: code,
          product_description: "",
        }));
  return {
    status: (record.status as LmpNcStatus) || "open",
    sale_number: record.sale_number ?? "",
    customer_name: record.customer_name ?? "",
    launch_date: toDateInput(record.launch_date),
    last_revision_date: toDateInput(record.last_revision_date),
    executed_by: record.executed_by ?? "",
    released_by: record.released_by ?? "",
    defect_description: record.defect_description ?? "",
    corrective_actions: record.corrective_actions ?? "",
    technical_opinion: record.technical_opinion ?? "",
    products,
  };
}

export function ncFormToPayload(form: NcFormState): LmpNonconformityPayload {
  return {
    status: form.status,
    sale_number: form.sale_number.trim() || null,
    customer_name: form.customer_name.trim() || null,
    launch_date: form.launch_date.trim() || null,
    last_revision_date: form.last_revision_date.trim() || null,
    executed_by: form.executed_by.trim() || null,
    released_by: form.released_by.trim() || null,
    defect_description: form.defect_description.trim() || null,
    corrective_actions: form.corrective_actions.trim() || null,
    technical_opinion: form.technical_opinion.trim() || null,
    products: form.products
      .map((p) => ({
        product_code: p.product_code.trim(),
        product_description: (p.product_description ?? "").trim() || null,
      }))
      .filter((p) => p.product_code),
  };
}

export function productsSummary(row: LmpNonconformity): string {
  const codes =
    row.products?.map((p) => p.product_code).filter(Boolean) ??
    row.product_codes ??
    [];
  if (!codes.length) return "—";
  if (codes.length <= 2) return codes.join(", ");
  return `${codes.slice(0, 2).join(", ")} +${codes.length - 2}`;
}
