export type AuditFilters = {
  search: string;
  context: string;
  action: string;
  userId: string;
  traceId: string;
  dateFrom: string;
  dateTo: string;
};

export const DEFAULT_AUDIT_FILTERS: AuditFilters = {
  search: "",
  context: "",
  action: "",
  userId: "",
  traceId: "",
  dateFrom: "",
  dateTo: "",
};

export type AuditBackendPlaceholders = {
  reloadAuditLogs?: (filters: AuditFilters) => Promise<void>;
  exportAuditLogs?: (filters: AuditFilters) => Promise<void>;
  exportAuditLogsCsv?: (filters: AuditFilters) => Promise<void>;
};
