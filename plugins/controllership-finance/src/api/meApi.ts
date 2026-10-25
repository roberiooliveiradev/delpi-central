/** Cliente da BFF — superfícies self-only (Minhas tarefas, perfil). */
import { cfApiUrl, httpGet } from "./httpClient";

type Envelope<T> = { data?: T };

export type TaskContext = {
  contextType: string;
  contextId: string;
  contextLabel: string;
  competence: string;
};

export type MyTask = {
  id: string;
  sourceType: "PENDENCY" | "PACKAGE" | string;
  sourceId: string;
  actionKind:
    | "PENDENCY_ACTION_REQUIRED"
    | "PACKAGE_REVIEW_REQUIRED"
    | "PACKAGE_CLARIFICATION_REQUIRED"
    | string;
  title: string;
  ownerPage: string;
  ownerState: string;
  statusLabel: string;
  assigneeUserId: string;
  context: TaskContext;
  pendingSince?: string | null;
  sourceStatus: string;
  deepLink: string;
};

export type MyTasksProjection = {
  items: MyTask[];
  total: number;
  source: string;
  selfOnly: boolean;
};

export type MyProfile = {
  id: string;
  displayName: string | null;
  email: string | null;
  groups: string[];
  permissions: string[];
  personProfile: Record<string, unknown> | null;
};

export async function listMyTasks(
  options?: { period?: string; signal?: AbortSignal },
): Promise<MyTasksProjection> {
  const qs = options?.period
    ? `?period=${encodeURIComponent(options.period)}`
    : "";
  const envelope = await httpGet<Envelope<MyTasksProjection>>(
    cfApiUrl(`/me/tasks${qs}`),
    options,
  );
  return (
    envelope?.data ?? {
      items: [],
      total: 0,
      source: "controllership-finance-api",
      selfOnly: true,
    }
  );
}

export async function getMyProfile(
  options?: { signal?: AbortSignal },
): Promise<MyProfile> {
  const envelope = await httpGet<Envelope<MyProfile>>(
    cfApiUrl("/me/profile"),
    options,
  );
  if (!envelope?.data) {
    throw new Error("Perfil não encontrado.");
  }
  return envelope.data;
}
