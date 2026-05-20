export type LmpStatus = "Pontual" | "Atrasado" | "Andamento" | "Retornada";
export type LmpNivel = "Nível 1" | "Nível 2" | "Nível 3";
export type LmpListingKind = "LMP" | "AMOSTRA" | "OUTRO";

export type LmpDashboardItem = {
  branch?: string | null;
  sale_number: string;
  sale_description: string;
  listing_kind?: LmpListingKind | null;
  start_date?: string | null;
  end_date?: string | null;
  engineering_status?: string | null;
  qtd_pi?: number | null;
  nivel: LmpNivel;
  dias_uteis_sla: number;
  data_limite?: string | null;
  lead_time_util?: number | null;
  status: LmpStatus;
};

export type LmpsDashboardSummary = {
  total_lmps: number;
  total_items?: number;
  percent_dentro_prazo: number;
  avg_lead_time: number;
};

export type LmpsChartDatum = { name: string; value: number };
export type LmpsLeadByLevelDatum = { nivel: string; valor: number };
export type LmpsEvolutionDatum = {
  periodo: string;
  mediaLead: number;
  propostas: number;
};

export type LmpsDashboardCharts = {
  levelData?: LmpsChartDatum[];
  statusData?: LmpsChartDatum[];
  leadByLevel?: LmpsLeadByLevelDatum[];
  evolutionData?: LmpsEvolutionDatum[];
};

export type LmpsDashboardResponse = {
  items: LmpDashboardItem[];
  total: number;
  page: number;
  page_size: number;
  summary: LmpsDashboardSummary;
  charts?: LmpsDashboardCharts;
};

export type LmpsDashboardParams = {
  date_start?: string;
  date_end?: string;
  branch?: string;
  listing_type?: string;
  status?: string;
  page?: number;
  page_size?: number;
};
