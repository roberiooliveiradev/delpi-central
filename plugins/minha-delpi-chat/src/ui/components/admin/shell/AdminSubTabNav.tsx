import type { AdminSectionConfig, AdminSubTab } from "./adminShellTypes";

import "./AdminSubTabNav.css";

type AdminSubTabNavProps = {
  section: AdminSectionConfig;
  activeSubTab: AdminSubTab | null;
  onSubTabChange: (subTab: AdminSubTab) => void;
};

export function AdminSubTabNav({
  section,
  activeSubTab,
  onSubTabChange,
}: AdminSubTabNavProps) {
  if (!section.subTabs.length) {
    return null;
  }

  const current = activeSubTab ?? section.subTabs[0]?.key;

  return (
    <nav className="mdc-admin-subtabs" aria-label={`${section.label} — sub-abas`}>
      {section.subTabs.map((subTab) => (
        <button
          key={subTab.key}
          type="button"
          className={current === subTab.key ? "is-active" : undefined}
          aria-current={current === subTab.key ? "page" : undefined}
          onClick={() => onSubTabChange(subTab.key)}
        >
          {subTab.label}
        </button>
      ))}
    </nav>
  );
}
