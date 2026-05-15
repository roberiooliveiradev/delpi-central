export type AdminTab = "knowledge" | "metrics" | "guidelines" | "tools" | "audit";

export type AdminTabItem = {
  key: AdminTab;
  label: string;
};
