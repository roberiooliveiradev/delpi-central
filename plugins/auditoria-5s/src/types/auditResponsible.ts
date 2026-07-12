export type AuditResponsibleSelection = {
  user_id: string | null;
  display_name: string;
};

export function emptyResponsibleSelection(): AuditResponsibleSelection {
  return { user_id: null, display_name: "" };
}
