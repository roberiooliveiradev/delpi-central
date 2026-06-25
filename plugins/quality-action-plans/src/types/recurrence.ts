export type RecurrenceGroup = {
  recurrence_key: string;
  branch_code?: string | null;
  product_code?: string | null;
  failure_mode?: string | null;
  total_plans: number;
  open_plans: number;
  critical_open: number;
  last_plan_code?: string | null;
  last_plan_id?: string | null;
  last_opened_at?: string | null;
};

export type PagedRecurrenceResponse = {
  items: RecurrenceGroup[];
  pagination: {
    page: number;
    page_size: number;
    total: number;
    total_pages: number;
  };
};
