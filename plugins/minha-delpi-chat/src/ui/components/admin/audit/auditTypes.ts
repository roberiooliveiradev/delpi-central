export type AuditFilters = {
  search: string;
  context: string;
  action: string;
  userId: string;
};

export type AuditBackendPlaceholders = {
  reloadAuditLogs?: (filters: AuditFilters) => Promise<void>;
  exportAuditLogs?: (filters: AuditFilters) => Promise<void>;
};
