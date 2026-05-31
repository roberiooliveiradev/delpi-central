import {
  getAdminSectionItem,
  type AdminNavState,
  type AdminSubTab,
} from "../../../../navigation/adminNavigation";

import "./AdminSubTabNav.css";

type AdminSubTabNavProps = {
  nav: AdminNavState;
  onSubTabChange: (subTab: AdminSubTab) => void;
};

export function AdminSubTabNav({ nav, onSubTabChange }: AdminSubTabNavProps) {
  const section = getAdminSectionItem(nav.section);

  if (section.subTabs.length === 0) {
    return null;
  }

  const activeSubTab = nav.subTab ?? section.subTabs[0]?.key;

  return (
    <nav className="mdc-admin-subtab-nav" aria-label={`Sub-seções de ${section.label}`}>
      {section.subTabs.map((item) => (
        <button
          key={item.key}
          type="button"
          className={activeSubTab === item.key ? "is-active" : undefined}
          aria-current={activeSubTab === item.key ? "page" : undefined}
          onClick={() => onSubTabChange(item.key)}
        >
          {item.label}
        </button>
      ))}
    </nav>
  );
}
