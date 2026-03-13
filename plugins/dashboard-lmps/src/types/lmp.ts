export type LmpItem = {
  sale_number: string;
  sale_description: string;
  start_date?: string | null;
  end_date?: string | null;
  qtd_pi?: number | null;
};

export type Page<T> = {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages?: number;
};

export type ApiSuccessResponse<T> = {
  success: boolean;
  data: T;
  message?: string;
};

export type ListLmpsParams = {
  date_start?: string;
  date_end?: string;
  page?: number;
  page_size?: number;
};

export type LmpStatus = "Pontual" | "Atrasado" | "Andamento";
export type LmpNivel = "Nível 1" | "Nível 2" | "Nível 3";

export type EnrichedLmpItem = LmpItem & {
  nivel: LmpNivel;
  dias_uteis_sla: number;
  data_limite: string | null;
  lead_time_util: number | null;
  status: LmpStatus;
};