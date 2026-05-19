export type ProductionFilterParams = {
  start_date?: string;
  end_date?: string;
  branch?: string;
};

export type DirectLaborCostPctData = {
  direct_labor_cost_pct: number | null;
};

export type ProductionCostPctData = {
  production_cost_pct: number | null;
};

export type DepreciationPctData = {
  depreciation_pct: number | null;
};

export type OeePctData = {
  overall_equipment_effectiveness_pct: number | null;
};

export type OtdPctData = {
  on_time_delivery_pct: number | null;
};
