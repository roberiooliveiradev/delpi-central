export const AUDIT_5S_SOCKET_PATH = "/apps/api-delpi/socket.io";

export type AuditPresenceUser = {
  user_id: string;
  display_name: string;
};

export type AuditTypingUser = AuditPresenceUser & {
  client_id: string;
};

export type AuditResponseUpdatedEvent = {
  audit_id: string;
  response: {
    id: string;
    criterion_id: string;
    score: number | null;
    is_not_applicable: boolean;
    observation: string | null;
    version: number;
  };
  audit: import("../api/audit5sApi").AuditDetail;
  actor_user_id: string;
  actor_display_name: string;
};

export type AuditUpdatedEvent = {
  audit_id: string;
  audit: import("../api/audit5sApi").AuditDetail;
  event_type: "evaluation_complete" | "nc_created" | "closed" | string;
  actor_user_id: string;
  actor_display_name: string;
};

export type AuditPresenceUpdatedEvent = {
  audit_id: string;
  users: AuditPresenceUser[];
};

export type AuditObservationTypingUpdatedEvent = {
  audit_id: string;
  criterion_id: string;
  users: AuditTypingUser[];
};
