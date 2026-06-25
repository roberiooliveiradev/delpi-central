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
  action_status: string;
  is_overdue: boolean;
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
