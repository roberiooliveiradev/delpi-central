export type MyQueueSummary = {
  open_actions: number;
  overdue_actions: number;
};

export type MyQueueItem = {
  action_id: string;
  plan_id: string;
  action_type: string;
  description: string;
  responsible_user_id?: string | null;
  responsible_name?: string | null;
  department?: string | null;
  due_date?: string | null;
  completed_at?: string | null;
  evidence_required?: boolean;
  evidence_count?: number;
  action_status: string;
  is_overdue: boolean;
  completed_late?: boolean;
  is_due_soon?: boolean;
  days_until_due?: number | null;
  due_sla_level?: "ok" | "due_soon" | "overdue" | "completed_late";
  plan_code?: string | null;
  plan_title?: string | null;
  plan_status: string;
  plan_severity: string;
  branch_code?: string | null;
  nonconformity_scope?: string | null;
  customer_name?: string | null;
  product_code?: string | null;
};

export type MyQueueResponse = {
  user_id: string;
  summary: MyQueueSummary;
  items: MyQueueItem[];
  pagination: {
    page: number;
    page_size: number;
    total: number;
    total_pages: number;
  };
};
