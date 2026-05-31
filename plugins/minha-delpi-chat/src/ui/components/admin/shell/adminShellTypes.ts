export type {
  AdminLegacyTab as AdminTab,
  AdminNavState,
  AdminSection,
  AdminSubTab,
} from "../../../../navigation/adminNavigation";

/** @deprecated Use AdminSectionItem em adminNavigation */
export type AdminTabItem = {
  key: import("../../../../navigation/adminNavigation").AdminLegacyTab;
  label: string;
};
