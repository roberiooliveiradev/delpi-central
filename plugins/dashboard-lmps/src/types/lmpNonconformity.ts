export type LmpNcStatus = "open" | "in_progress" | "done";

export type LmpNonconformity = {
  id: string;
  registered_at: string;
  sale_number?: string | null;
  branch_code?: string | null;
  material_code?: string | null;
  supplier_name?: string | null;
  purchase_order?: string | null;
  invoice_number?: string | null;
  qty_received?: number | null;
  qty_accepted?: number | null;
  qty_rejected?: number | null;
  status: LmpNcStatus | string;
  defect_description?: string | null;
  corrective_actions?: string | null;
  technical_opinion?: string | null;
  product_codes?: string[];
  created_by?: string | null;
  updated_by?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
};

export type LmpNonconformityListResponse = {
  items: LmpNonconformity[];
  total: number;
  page: number;
  page_size: number;
};

export type LmpNonconformityPayload = {
  registered_at: string;
  status: LmpNcStatus;
  sale_number?: string | null;
  branch_code?: string | null;
  material_code?: string | null;
  supplier_name?: string | null;
  purchase_order?: string | null;
  invoice_number?: string | null;
  qty_received?: number | null;
  qty_accepted?: number | null;
  qty_rejected?: number | null;
  defect_description?: string | null;
  corrective_actions?: string | null;
  technical_opinion?: string | null;
  product_codes?: string[];
};

export const LMP_NC_STATUS_OPTIONS: { value: LmpNcStatus; label: string }[] = [
  { value: "open", label: "Aberta" },
  { value: "in_progress", label: "Em andamento" },
  { value: "done", label: "Concluída" },
];

export function lmpNcStatusLabel(status: string): string {
  return LMP_NC_STATUS_OPTIONS.find((o) => o.value === status)?.label ?? status;
}
