import { unwrapEnvelope, type ApiSuccessResponse } from "../types/api";
import { commercialApiUrl, httpDelete, httpGet, httpPatch, httpPost } from "./httpClient";

export type TaskCustomerDto = {
  customer_code: string;
  customer_store: string;
  customer_name?: string | null;
};

export type TaskAssigneeGroupDto = {
  id: string;
  kind?: string;
  name?: string;
};

export type TaskSourceMessageMentionDto = {
  id: string;
  message_id?: string;
  mention_kind: string;
  ref?: Record<string, unknown>;
  label: string;
};

export type CommercialTaskDto = {
  id: string;
  title: string;
  description?: string | null;
  task_type: string;
  status: string;
  priority: string;
  due_at?: string | null;
  completed_at?: string | null;
  completed_by_user_id?: string | null;
  assignee_user_id: string;
  assignee_user_ids?: string[];
  assignee_group_ids?: string[];
  assignee_groups?: TaskAssigneeGroupDto[];
  created_by_user_id: string;
  customer_code?: string | null;
  customer_store?: string | null;
  customer_name?: string | null;
  customers?: TaskCustomerDto[];
  bucket?: "overdue" | "today" | "later" | string;
  attachment_count?: number;
  source_message_mentions?: TaskSourceMessageMentionDto[];
};

export type WorklistScope = "mine" | "team";

export type WorklistData = {
  overdue: CommercialTaskDto[];
  today: CommercialTaskDto[];
  later: CommercialTaskDto[];
  counts: {
    overdue: number;
    today: number;
    later: number;
    open: number;
  };
  scope?: WorklistScope | string;
  team_user_ids?: string[];
};

export type CompletedWorklistData = {
  items: CommercialTaskDto[];
  count: number;
  scope?: WorklistScope | string;
  team_user_ids?: string[];
  limit?: number;
};

export type CommercialActivityDto = {
  id: string;
  activity_type: string;
  subject?: string | null;
  body?: string | null;
  occurred_at?: string | null;
  actor_user_id: string;
  customer_code?: string | null;
  customer_store?: string | null;
  task_id?: string | null;
};

export async function getMyWorklist(
  options?: {
    scope?: WorklistScope;
    assigneeUserId?: string | null;
    signal?: AbortSignal;
  },
): Promise<WorklistData> {
  const params = new URLSearchParams();
  if (options?.scope === "team") params.set("scope", "team");
  if (options?.assigneeUserId) params.set("assignee_user_id", options.assigneeUserId);
  const query = params.toString();
  const response = await httpGet<ApiSuccessResponse<WorklistData>>(
    commercialApiUrl(`/me/worklist${query ? `?${query}` : ""}`),
    { signal: options?.signal },
  );
  return unwrapEnvelope(response, "Erro ao carregar Meu dia.");
}

export async function getCompletedWorklist(
  options?: {
    scope?: WorklistScope;
    assigneeUserId?: string | null;
    limit?: number;
    signal?: AbortSignal;
  },
): Promise<CompletedWorklistData> {
  const params = new URLSearchParams();
  if (options?.scope === "team") params.set("scope", "team");
  if (options?.assigneeUserId) params.set("assignee_user_id", options.assigneeUserId);
  if (options?.limit != null) params.set("limit", String(options.limit));
  const query = params.toString();
  const response = await httpGet<ApiSuccessResponse<CompletedWorklistData>>(
    commercialApiUrl(`/me/worklist/done${query ? `?${query}` : ""}`),
    { signal: options?.signal },
  );
  return unwrapEnvelope(response, "Erro ao carregar tarefas concluídas.");
}

export type TaskCustomerBody = {
  code: string;
  store: string;
  name?: string | null;
};

export async function createTask(
  body: {
    title: string;
    description?: string;
    task_type?: string;
    priority?: string;
    due_at?: string | null;
    customer_code?: string | null;
    customer_store?: string | null;
    customers?: TaskCustomerBody[] | null;
    assignee_user_id?: string | null;
    assignee_user_ids?: string[] | null;
    assignee_group_ids?: string[] | null;
  },
  signal?: AbortSignal,
): Promise<CommercialTaskDto> {
  const response = await httpPost<ApiSuccessResponse<CommercialTaskDto>>(
    commercialApiUrl("/tasks"),
    body,
    { signal },
  );
  return unwrapEnvelope(response, "Erro ao criar tarefa.");
}

export async function updateTask(
  taskId: string,
  body: {
    title: string;
    description?: string | null;
    task_type?: string;
    priority?: string;
    due_at?: string | null;
    customer_code?: string | null;
    customer_store?: string | null;
    customers?: TaskCustomerBody[] | null;
    assignee_user_id?: string | null;
    assignee_user_ids?: string[] | null;
    assignee_group_ids?: string[] | null;
  },
  signal?: AbortSignal,
): Promise<CommercialTaskDto> {
  const response = await httpPatch<ApiSuccessResponse<CommercialTaskDto>>(
    commercialApiUrl(`/tasks/${encodeURIComponent(taskId)}`),
    body,
    { signal },
  );
  return unwrapEnvelope(response, "Erro ao atualizar tarefa.");
}

export async function deleteTask(taskId: string, signal?: AbortSignal): Promise<CommercialTaskDto> {
  const response = await httpDelete<ApiSuccessResponse<CommercialTaskDto>>(
    commercialApiUrl(`/tasks/${encodeURIComponent(taskId)}`),
    { signal },
  );
  return unwrapEnvelope(response, "Erro ao excluir tarefa.");
}

export async function completeTask(taskId: string, signal?: AbortSignal): Promise<CommercialTaskDto> {
  const response = await httpPost<ApiSuccessResponse<CommercialTaskDto>>(
    commercialApiUrl(`/tasks/${encodeURIComponent(taskId)}/complete`),
    {},
    { signal },
  );
  return unwrapEnvelope(response, "Erro ao concluir tarefa.");
}

export async function deferTask(
  taskId: string,
  dueAt: string,
  signal?: AbortSignal,
): Promise<CommercialTaskDto> {
  const response = await httpPost<ApiSuccessResponse<CommercialTaskDto>>(
    commercialApiUrl(`/tasks/${encodeURIComponent(taskId)}/defer`),
    { due_at: dueAt },
    { signal },
  );
  return unwrapEnvelope(response, "Erro ao adiar tarefa.");
}

export async function reassignTask(
  taskId: string,
  assigneeUserId: string | string[],
  signal?: AbortSignal,
): Promise<CommercialTaskDto> {
  const body =
    Array.isArray(assigneeUserId)
      ? { assignee_user_ids: assigneeUserId }
      : { assignee_user_id: assigneeUserId };
  const response = await httpPost<ApiSuccessResponse<CommercialTaskDto>>(
    commercialApiUrl(`/tasks/${encodeURIComponent(taskId)}/reassign`),
    body,
    { signal },
  );
  return unwrapEnvelope(response, "Erro ao reatribuir tarefa.");
}

export async function listCustomerActivities(
  customerCode: string,
  customerStore: string,
  signal?: AbortSignal,
): Promise<CommercialActivityDto[]> {
  const params = new URLSearchParams({
    customer_code: customerCode,
    customer_store: customerStore,
  });
  const response = await httpGet<ApiSuccessResponse<{ items: CommercialActivityDto[] }>>(
    `${commercialApiUrl("/activities")}?${params.toString()}`,
    { signal },
  );
  const data = unwrapEnvelope(response, "Erro ao carregar atividades.");
  return data.items ?? [];
}
