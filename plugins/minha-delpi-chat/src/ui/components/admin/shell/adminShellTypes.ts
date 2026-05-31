export type AdminTab =
  | "knowledge"
  | "metrics"
  | "guidelines"
  | "skills"
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
