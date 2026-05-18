export type AdminTab =
  | "knowledge"
  | "metrics"
  | "guidelines"
  | "simulate"
  | "evaluations"
  | "agents"
  | "security"
  | "tools"
  | "audit";

export type AdminTabItem = {
  key: AdminTab;
  label: string;
};
