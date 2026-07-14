import type { BookingStatus, BranchCode, ResourceType } from "../constants/scheduling";
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
  requires_approval?: boolean;
  created_by_user_id: string | null;
  created_at: string;
  updated_at: string;
};

export type RecurrenceFrequency = "weekly" | "monthly";

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
  status: BookingStatus;
  recurrence_series_id?: string | null;
  recurrence_frequency?: RecurrenceFrequency | null;
  decided_by_user_id?: string | null;
  decided_by_name?: string | null;
  decided_at?: string | null;
  decision_reason?: string | null;
  expires_at?: string | null;
  created_at: string;
  updated_at: string;
  resource_name?: string;
  resource_type?: ResourceType;
  requires_approval?: boolean;
};

export type RecurrencePayload = {
  frequency: RecurrenceFrequency;
  until: string;
  interval?: number;
};

export type CreateBookingPayload = {
  branch_code: BranchCode;
  resource_id: string;
  title: string;
  notes?: string;
  start_at: string;
  end_at: string;
  recurrence?: RecurrencePayload;
};

export type RecurringBookingResult = {
  series_id: string;
  frequency: RecurrenceFrequency;
  created: SchedulingBooking[];
  skipped: Array<{ start_at: string; end_at: string; reason: string }>;
  total_created: number;
  total_skipped: number;
};

export type CreateBookingResult = SchedulingBooking | RecurringBookingResult;

export function isRecurringBookingResult(
  result: CreateBookingResult,
): result is RecurringBookingResult {
  return "series_id" in result && "created" in result;
}

export type CancelScope = "occurrence" | "future" | "all";

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
  requires_approval?: boolean;
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
    requires_approval: boolean;
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

export async function createBooking(payload: CreateBookingPayload): Promise<CreateBookingResult> {
  const envelope = await httpPost<ApiEnvelope<CreateBookingResult>>(
    `${API_BASE}/bookings`,
    payload,
  );
  return unwrapApiDelpiEnvelope(envelope, "Erro na API de agendamento");
}

export async function cancelBooking(
  bookingId: string,
  scope: CancelScope = "occurrence",
): Promise<SchedulingBooking & { cancelled_count?: number }> {
  const params = new URLSearchParams({ scope });
  const envelope = await httpPatch<ApiEnvelope<SchedulingBooking & { cancelled_count?: number }>>(
    `${API_BASE}/bookings/${bookingId}/cancel?${params.toString()}`,
    {},
  );
  return unwrapApiDelpiEnvelope(envelope, "Erro na API de agendamento");
}

export async function fetchPendingBookings(
  branch: BranchCode,
  mine = false,
): Promise<SchedulingBooking[]> {
  const params = new URLSearchParams({ branch, mine: String(mine) });
  const envelope = await httpGet<ApiEnvelope<SchedulingBooking[]>>(
    `${API_BASE}/bookings/pending?${params.toString()}`,
  );
  return unwrapApiDelpiEnvelope(envelope, "Erro na API de agendamento");
}

export async function fetchMyBookings(
  branch: BranchCode,
  limit = 100,
): Promise<SchedulingBooking[]> {
  const params = new URLSearchParams({ branch, limit: String(limit) });
  const envelope = await httpGet<ApiEnvelope<SchedulingBooking[]>>(
    `${API_BASE}/bookings/mine?${params.toString()}`,
  );
  return unwrapApiDelpiEnvelope(envelope, "Erro na API de agendamento");
}

export async function approveBooking(bookingId: string): Promise<SchedulingBooking> {
  const envelope = await httpPost<ApiEnvelope<SchedulingBooking>>(
    `${API_BASE}/bookings/${bookingId}/approve`,
    {},
  );
  return unwrapApiDelpiEnvelope(envelope, "Erro na API de agendamento");
}

export async function rejectBooking(
  bookingId: string,
  reason: string,
): Promise<SchedulingBooking> {
  const envelope = await httpPost<ApiEnvelope<SchedulingBooking>>(
    `${API_BASE}/bookings/${bookingId}/reject`,
    { reason },
  );
  return unwrapApiDelpiEnvelope(envelope, "Erro na API de agendamento");
}

export async function fetchMeProfile(): Promise<MeProfile> {
  return httpGet<MeProfile>("/core-api/me");
}
