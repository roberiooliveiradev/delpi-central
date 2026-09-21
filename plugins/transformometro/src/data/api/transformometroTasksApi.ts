import { TRANSFORMOMETRO_API_BASE, buildAuthHeaders } from "./transformometroApiBase";
import { parseApiEnvelope } from "./transformometroHttp";

export type TransformometroTask = {
  id: string;
  title: string;
  description: string | null;
  status: "pending" | "completed" | "cancelled";
  assignee_user_id: string;
  created_by_user_id: string;
  due_date: string | null;
  created_at?: string | null;
  updated_at?: string | null;
  completed_at?: string | null;
  source_interaction_message_id?: string | null;
};

export type MyTaskItemDto = {
  id: string;
  type: "manual_task" | "meeting_minute_signature";
  title: string;
  description?: string | null;
  status: string;
  status_label: string;
  source_label: string;
  source_id: string;
  due_date?: string | null;
  due_date_label?: string | null;
  overdue?: boolean;
  assignee_user_id?: string | null;
  context_label?: string | null;
  route?: string | null;
  actions?: {
    can_open?: boolean;
    can_edit?: boolean;
    can_complete?: boolean;
    can_cancel?: boolean;
  };
};

export type MyTaskItemsResponse = {
  items: MyTaskItemDto[];
  summary: { pending: number; due_soon: number; overdue: number };
  partial_error?: string | null;
};

export type TaskWritePayload = {
  title: string;
  description?: string | null;
  assignee_user_id?: string | null;
  due_date?: string | null;
  source_interaction_message_id?: string | null;
};

async function request<T>(
  path: string,
  getAccessToken?: () => string | undefined,
  init?: RequestInit,
): Promise<T> {
  const response = await fetch(`${TRANSFORMOMETRO_API_BASE}${path}`, {
    ...init,
    headers: {
      ...buildAuthHeaders(getAccessToken),
      ...(init?.body ? { "Content-Type": "application/json" } : {}),
      ...init?.headers,
    },
  });
  return parseApiEnvelope<T>(response);
}

export function listMyTaskItems(
  getAccessToken?: () => string | undefined,
  status = "pending",
) {
  return request<MyTaskItemsResponse>(`/my-tasks?status=${encodeURIComponent(status)}`, getAccessToken);
}

export function createTask(payload: TaskWritePayload, getAccessToken?: () => string | undefined) {
  return request<TransformometroTask>("/tasks", getAccessToken, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getTask(id: string, getAccessToken?: () => string | undefined) {
  return request<TransformometroTask>(`/tasks/${id}`, getAccessToken);
}

export function updateTask(
  id: string,
  payload: TaskWritePayload,
  getAccessToken?: () => string | undefined,
) {
  return request<TransformometroTask>(`/tasks/${id}`, getAccessToken, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function completeTask(id: string, getAccessToken?: () => string | undefined) {
  return request<TransformometroTask>(`/tasks/${id}/complete`, getAccessToken, { method: "POST" });
}

export function cancelTask(id: string, getAccessToken?: () => string | undefined) {
  return request<TransformometroTask>(`/tasks/${id}/cancel`, getAccessToken, { method: "POST" });
}

export type ProcessoRelatedTasksResponse = {
  items: TransformometroTask[];
  total: number;
};

export function listProcessoRelatedTasks(
  processoId: string,
  getAccessToken?: () => string | undefined,
) {
  return request<ProcessoRelatedTasksResponse>(
    `/processos/${encodeURIComponent(processoId)}/related-tasks`,
    getAccessToken,
  );
}
