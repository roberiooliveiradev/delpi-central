export type LmpNcStatus = "open" | "in_progress" | "done";

export type LmpNcProductLine = {
  product_code: string;
  product_description?: string | null;
};

export type LmpNonconformity = {
  id: string;
  registered_at: string;
  sale_number?: string | null;
  customer_name?: string | null;
  launch_date?: string | null;
  last_revision_date?: string | null;
  executed_by?: string | null;
  released_by?: string | null;
  status: LmpNcStatus | string;
  defect_description?: string | null;
  corrective_actions?: string | null;
  technical_opinion?: string | null;
  products?: LmpNcProductLine[];
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
  status: LmpNcStatus;
  sale_number?: string | null;
  customer_name?: string | null;
  launch_date?: string | null;
  last_revision_date?: string | null;
  executed_by?: string | null;
  released_by?: string | null;
  defect_description?: string | null;
  corrective_actions?: string | null;
  technical_opinion?: string | null;
  products?: LmpNcProductLine[];
};

export const LMP_NC_STATUS_OPTIONS: { value: LmpNcStatus; label: string }[] = [
  { value: "open", label: "Aberta" },
  { value: "in_progress", label: "Em andamento" },
  { value: "done", label: "Concluída" },
];

export function lmpNcStatusLabel(status: string): string {
  return LMP_NC_STATUS_OPTIONS.find((o) => o.value === status)?.label ?? status;
}
