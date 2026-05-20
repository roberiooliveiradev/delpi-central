export type EngineeringFilterParams = {
  start_date?: string;
  end_date?: string;
  filial_id?: string;
  branch?: string;
  name_process?: string;
  sector_name?: string;
  status?: string;
};

export type TransformaProcess = {
  id: string;
  name_process: string;
  filial_id?: string | null;
  sector_name?: string | null;
  daily_savings?: number | null;
  payback_months?: number | null;
  status?: string | null;
  implementetion_date?: string | null;
};

export type TransformaProcessesList = {
  total: number;
  items: TransformaProcess[];
};

export type TransformaMonthlyItem = {
  month: string;
  gross_savings_month: number;
  gross_costs_month: number;
  gross_investment_month: number;
  gross_recurring_investment_month: number;
  shared_resource_cost_month: number;
  net_savings_month: number;
};

export type TransformaSummary = {
  implemented_solutions_count: number;
  total_net_savings_until_now: number;
  total_hours_saved_until_now: number;
  total_gross_costs_until_now: number;
  total_gross_savings_in_period: number;
  average_roi: number;
  monthly_breakdown: TransformaMonthlyItem[];
  range_summary?: {
    start_date: string | null;
    end_date: string | null;
    accumulated_net_savings_until_now: number;
  } | null;
};
