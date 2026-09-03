export type Envelope<T> = {
  success: boolean;
  message?: string;
  data: T;
};

export type AllowedAction = string;

export type RequestSummary = {
  id: string;
  request_number: string;
  type_code: string;
  status: string;
  status_alias?: string | null;
  priority: string;
  branch_code?: string | null;
  version: number;
  created_by_user_id: string;
  created_by_name: string;
  created_at?: string | null;
  updated_at?: string | null;
  allowed_actions: AllowedAction[];
};

export type RequestDetail = RequestSummary & {
  payload: Record<string, unknown>;
  return_reason?: string | null;
  cancel_justification?: string | null;
  completed_at?: string | null;
  cancelled_at?: string | null;
};

export type RequestListResponse = {
  items: RequestSummary[];
  total: number;
  page?: number;
  page_size?: number;
};

export type RequestTypeSummary = {
  id: string;
  code: string;
  name: string;
  description?: string | null;
  active: boolean;
  presentation_mode?: string;
  branch_scope?: string;
};

export type TimelineEvent = {
  id: string;
  event_type: string;
  actor_user_id?: string | null;
  actor_name?: string | null;
  payload?: Record<string, unknown>;
  created_at?: string | null;
};

export type RequestComment = {
  id: string;
  body: string;
  author_user_id?: string | null;
  author_name?: string | null;
  created_at?: string | null;
};

export type RequestAttachment = {
  id: string;
  file_name: string;
  content_type?: string | null;
  size_bytes?: number | null;
  created_at?: string | null;
};

export type RequestArtifact = {
  id: string;
  file_name: string;
  content_type?: string | null;
  size_bytes?: number | null;
  kind?: string | null;
  created_at?: string | null;
};
