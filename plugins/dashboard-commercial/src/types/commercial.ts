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

export type CommercialFilterParams = {
  start_date?: string;
  end_date?: string;
  branch?: string;
};
