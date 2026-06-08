import type { BranchCode, ResourceType } from "../constants/scheduling";
import { API_BASE } from "../constants/scheduling";
import {
  type ApiEnvelope,
  httpGet,
  httpPatch,
  httpPost,
  unwrapApiDelpiEnvelope,
} from "./httpClient";

export type SchedulingResource = {
  id: string;
  branch_code: BranchCode;
  name: string;
  resource_type: ResourceType;
  description: string | null;
  capacity: number | null;
  metadata: Record<string, unknown>;
  active: boolean;
  created_by_user_id: string | null;
  created_at: string;
  updated_at: string;
};

export type SchedulingBooking = {
  id: string;
  resource_id: string;
  branch_code: BranchCode;
  title: string;
  notes: string | null;
  start_at: string;
  end_at: string;
  booked_by_user_id: string;
  booked_by_name: string;
  status: "confirmed" | "cancelled";
  created_at: string;
  updated_at: string;
  resource_name?: string;
  resource_type?: ResourceType;
};

export type MeProfile = {
  id: string;
  name: string;
  email: string;
  permissions: string[];
  is_superadmin?: boolean;
};

export async function fetchResources(
  branch: BranchCode,
  active = true,
): Promise<SchedulingResource[]> {
  const params = new URLSearchParams({ branch, active: String(active) });
  const envelope = await httpGet<ApiEnvelope<SchedulingResource[]>>(
    `${API_BASE}/resources?${params.toString()}`,
  );
  return unwrapApiDelpiEnvelope(envelope, "Erro na API de agendamento");
}

export async function createResource(payload: {
  branch_code: BranchCode;
  name: string;
  resource_type: ResourceType;
  description?: string;
  capacity?: number;
  metadata?: Record<string, unknown>;
}): Promise<SchedulingResource> {
  const envelope = await httpPost<ApiEnvelope<SchedulingResource>>(
    `${API_BASE}/resources`,
    payload,
  );
  return unwrapApiDelpiEnvelope(envelope, "Erro na API de agendamento");
}

export async function updateResource(
  resourceId: string,
  payload: Partial<{
    name: string;
    resource_type: ResourceType;
    description: string | null;
    capacity: number | null;
    metadata: Record<string, unknown>;
    active: boolean;
  }>,
): Promise<SchedulingResource> {
  const envelope = await httpPatch<ApiEnvelope<SchedulingResource>>(
    `${API_BASE}/resources/${resourceId}`,
    payload,
  );
  return unwrapApiDelpiEnvelope(envelope, "Erro na API de agendamento");
}

export async function fetchBookings(
  branch: BranchCode,
  from: Date,
  to: Date,
  resourceId?: string,
): Promise<SchedulingBooking[]> {
  const params = new URLSearchParams({
    branch,
    from: from.toISOString(),
    to: to.toISOString(),
  });
  if (resourceId) {
    params.set("resource_id", resourceId);
  }
  const envelope = await httpGet<ApiEnvelope<SchedulingBooking[]>>(
    `${API_BASE}/bookings?${params.toString()}`,
  );
  return unwrapApiDelpiEnvelope(envelope, "Erro na API de agendamento");
}

export async function createBooking(payload: {
  branch_code: BranchCode;
  resource_id: string;
  title: string;
  notes?: string;
  start_at: string;
  end_at: string;
}): Promise<SchedulingBooking> {
  const envelope = await httpPost<ApiEnvelope<SchedulingBooking>>(
    `${API_BASE}/bookings`,
    payload,
  );
  return unwrapApiDelpiEnvelope(envelope, "Erro na API de agendamento");
}

export async function cancelBooking(bookingId: string): Promise<SchedulingBooking> {
  const envelope = await httpPatch<ApiEnvelope<SchedulingBooking>>(
    `${API_BASE}/bookings/${bookingId}/cancel`,
    {},
  );
  return unwrapApiDelpiEnvelope(envelope, "Erro na API de agendamento");
}

export async function fetchMeProfile(): Promise<MeProfile> {
  return httpGet<MeProfile>("/core-api/me");
}
