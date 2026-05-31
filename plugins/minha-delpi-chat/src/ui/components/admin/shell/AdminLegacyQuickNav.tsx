import {
  ADMIN_LEGACY_QUICK_NAV,
  legacyTabToNav,
  type AdminNavState,
  type LegacyAdminTab,
} from "../../../../navigation/adminNavigation";

import "./AdminLegacyQuickNav.css";

type AdminLegacyQuickNavProps = {
  nav: AdminNavState;
  onNavChange: (nav: Partial<AdminNavState>) => void;
};

function isLegacyTabActive(nav: AdminNavState, tab: LegacyAdminTab): boolean {
  const target = legacyTabToNav(tab, nav.agentId);

  return target.section === nav.section && target.subTab === nav.subTab;
}

export function AdminLegacyQuickNav({ nav, onNavChange }: AdminLegacyQuickNavProps) {
  return (
    <nav className="mdc-admin-legacy-quick" aria-label="Acesso direto às áreas do admin">
      <span className="mdc-admin-legacy-quick__label">Acesso direto</span>
      <div className="mdc-admin-legacy-quick__track">
        {ADMIN_LEGACY_QUICK_NAV.map((item) => (
          <button
            key={item.tab}
            type="button"
            className={isLegacyTabActive(nav, item.tab) ? "is-active" : undefined}
            aria-current={isLegacyTabActive(nav, item.tab) ? "page" : undefined}
            onClick={() => onNavChange(legacyTabToNav(item.tab, nav.agentId))}
          >
            {item.label}
          </button>
        ))}
      </div>
    </nav>
  );
}
