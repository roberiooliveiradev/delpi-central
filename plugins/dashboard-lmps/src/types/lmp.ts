export type LmpStatus = "Pontual" | "Atrasado" | "Andamento" | "Retornada";
export type LmpNivel = "Nível 1" | "Nível 2" | "Nível 3";

export type LmpProduct = {
  code: string;
  description: string;
  group_code: string;
  type: string;
  qtd_pi?: number | null;
};

export type LmpListingKind = "LMP" | "AMOSTRA";

export type LmpItem = {
  branch?: string | null;
  sale_number: string;
  sale_description: string;
  listing_kind?: LmpListingKind | null;
  start_date?: string | null;
  end_date?: string | null;
  engineering_status?: string | null;
  qtd_engineering_entries?: number;
  qtd_engineering_closed?: number;
  qtd_advanced_from_engineering?: number;
  qtd_returned_from_engineering?: number;
  engineering_total_minutes?: number;
  qtd_pi?: number | null;

  costumer_code?: string | null;
  costumer_store?: string | null;
  costumer_name?: string | null;
  seller_code?: string | null;
  seller_name?: string | null;
  list_products?: LmpProduct[];
};

export type LmpDashboardItem = LmpItem & {
  nivel: LmpNivel;
  dias_uteis_sla: number;
  data_limite?: string | null;
  lead_time_util?: number | null;
  status: LmpStatus;
};

export type Page<T> = {
  items: T[];
  total: number;
  page: number;
  page_size: number;
};

export type ListLmpsParams = {
  date_start?: string;
  date_end?: string;
  branch?: string;
  listing_type?: string;
  page?: number;
  page_size?: number;
};

export type ApiSuccessResponse<T> = {
  success: boolean;
  message?: string;
  data: T;
};