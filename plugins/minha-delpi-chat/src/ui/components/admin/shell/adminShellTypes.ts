export type AdminTab =
  | "knowledge"
  | "metrics"
  | "guidelines"
  | "simulate"
  | "evaluations"
  | "agents"
  | "security"
  | "tools"
  | "audit"
  | "notifications";

export type AdminTabItem = {
  key: AdminTab;
  label: string;
};
