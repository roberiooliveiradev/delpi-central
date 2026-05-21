export type RolTargetData = {
  branch: string;
  start_date?: string | null;
  end_date?: string | null;
  rol: number;
  target: number;
  rol_target_pct: number | null;
};

export type ClosingRateData = {
  branch?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  qtd_proposals: number;
  qtd_won: number;
  sales_conversion_rate_pct: number | null;
};

export type NewClientsAverageData = {
  branch?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  total_new_clients: number;
  qtd_months: number;
  monthly_average: number;
};

export type NewClientsRolPctData = {
  branch?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  new_clients_rol_pct: number | null;
};

export type SalesOrderOtdData = {
  branch?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  total_lines: number;
  on_time_lines: number;
  late_lines: number;
  sales_order_otd_pct: number | null;
};

export type NewBusinessRolPctData = {
  branch?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  total_rol: number;
  new_business_rol: number;
  weg_rol: number;
  new_business_rol_pct: number | null;
};

export type CommercialFilterParams = {
  start_date?: string;
  end_date?: string;
  branch?: string;
};

export type CommercialRolSeriesPoint = {
  periodo: string;
  sort_key: string;
  date_start: string;
  date_end: string;
  rol_matrix: number;
  rol_branch: number;
};

export type CommercialRolSeriesData = {
  granularity: string;
  truncated: boolean;
  points: CommercialRolSeriesPoint[];
};
