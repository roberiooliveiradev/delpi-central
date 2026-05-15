export type AdminTab = "knowledge" | "guidelines" | "tools" | "audit";

export type AdminTabItem = {
  key: AdminTab;
  label: string;
};
