export type {
  AdminNavState,
  AdminSection,
  AdminSubTab,
  AdminSectionConfig,
  LegacyAdminTab,
} from "../../../../navigation/adminNavigation";

/** @deprecated Prefer AdminSection */
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
