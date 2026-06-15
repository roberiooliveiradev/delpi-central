export type SavingsType = "tempo" | "material" | "financeiro" | "qualitativo" | "misto";

export type KaizenStatus = "em_andamento" | "implantado" | "descontinuado" | "cancelado";

export type KaizenRecord = {
  id: string;
  branch_code: string;
  title: string;
  accountable: string | null;
  sector: string | null;
  investment: number | null;
  savings_type: SavingsType;
  seconds_per_occurrence: number | null;
  occurrences_per_day: number | null;
  hourly_cost: number | null;
  quantity_saved_per_day: number | null;
  unit_material_cost: number | null;
  fixed_daily_savings: number | null;
  daily_savings: number | null;
  annual_savings: number | null;
  status: KaizenStatus;
  date_implemented: string | null;
  date_discontinued: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
};

export type KaizenListResponse = {
  items: KaizenRecord[];
  pagination: {
    page: number;
    page_size: number;
    total: number;
    total_pages: number;
  };
};

export type KaizenFormValues = {
  branch_code: string;
  title: string;
  accountable: string;
  sector: string;
  investment: string;
  savings_type: SavingsType | "";
  seconds_per_occurrence: string;
  occurrences_per_day: string;
  hourly_cost: string;
  quantity_saved_per_day: string;
  unit_material_cost: string;
  fixed_daily_savings: string;
  status: KaizenStatus;
  date_implemented: string;
  date_discontinued: string;
  notes: string;
};
