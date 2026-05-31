import { useMemo, useState } from "react";
import { ChevronDown } from "lucide-react";

import {
  ADMIN_SECTIONS,
  type AdminNavState,
  type AdminSection,
  type AdminSubTab,
  getAdminSectionConfig,
} from "../../../../navigation/adminNavigation";
import { AdminSubTabNav } from "./AdminSubTabNav";

import "./AdminShellTopbar.css";

type AdminShellTopbarProps = {
  nav: AdminNavState;
  isLoading: boolean;
  onRefresh: () => void;
  onBack: () => void;
  onNavChange: (nav: Partial<AdminNavState>) => void;
};

export function AdminShellTopbar({
  nav,
  isLoading,
  onRefresh,
  onBack,
  onNavChange,
}: AdminShellTopbarProps) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const sectionConfig = getAdminSectionConfig(nav.section);

  const mobileItems = useMemo(
    () =>
      ADMIN_SECTIONS.flatMap((section) => {
        if (!section.subTabs.length) {
          return [{ section: section.key, subTab: null as AdminSubTab | null, label: section.label }];
        }

        return section.subTabs.map((subTab) => ({
          section: section.key,
          subTab: subTab.key,
          label: `${section.label} · ${subTab.label}`,
        }));
      }),
    [],
  );

  const activeMobileLabel =
    mobileItems.find(
      (item) => item.section === nav.section && item.subTab === (nav.subTab ?? null),
    )?.label ?? sectionConfig.label;

  function selectSection(section: AdminSection) {
    const config = getAdminSectionConfig(section);
    onNavChange({
      section,
      subTab: config.subTabs[0]?.key ?? null,
      agentId: section === "agents" ? nav.agentId : null,
    });
    setMobileOpen(false);
  }

  function selectSubTab(subTab: AdminSubTab) {
    onNavChange({ section: nav.section, subTab });
    setMobileOpen(false);
  }

  return (
    <header className="mdc-admin-topbar">
      <div className="mdc-admin-topbar__content">
        <div>
          <p className="mdc-chat-eyebrow">Administração</p>
          <h1>Minha DELPI Chat</h1>
          <p>{sectionConfig.description}</p>
        </div>

        <div className="mdc-admin-topbar__actions">
          <button
            type="button"
            className="mdc-chat-ws-toolbar-btn mdc-chat-ws-toolbar-btn--primary"
            onClick={onRefresh}
            disabled={isLoading}
          >
            Atualizar
          </button>
          <button type="button" className="mdc-chat-ws-outline-btn" onClick={onBack}>
            Voltar ao chat
          </button>
        </div>
      </div>

      <div className="mdc-admin-mobile-select">
        <button
          type="button"
          className="mdc-admin-mobile-trigger"
          aria-expanded={mobileOpen}
          onClick={() => setMobileOpen((open) => !open)}
        >
          <span>{activeMobileLabel}</span>
          <ChevronDown size={18} aria-hidden />
        </button>
        {mobileOpen ? (
          <div className="mdc-admin-mobile-menu" role="menu">
            {mobileItems.map((item) => (
              <button
                key={`${item.section}:${item.subTab ?? ""}`}
                type="button"
                role="menuitem"
                className={
                  item.section === nav.section && item.subTab === (nav.subTab ?? null)
                    ? "is-active"
                    : undefined
                }
                onClick={() => {
                  onNavChange({ section: item.section, subTab: item.subTab });
                  setMobileOpen(false);
                }}
              >
                {item.label}
              </button>
            ))}
          </div>
        ) : null}
      </div>

      <nav className="mdc-admin-tabs mdc-admin-tabs--sections" aria-label="Seções do admin">
        {ADMIN_SECTIONS.map((section) => {
          const Icon = section.icon;
          const isActive = nav.section === section.key;

          return (
            <button
              key={section.key}
              type="button"
              className={isActive ? "is-active" : undefined}
              aria-current={isActive ? "page" : undefined}
              onClick={() => selectSection(section.key)}
            >
              <Icon size={16} aria-hidden />
              <span>{section.label}</span>
            </button>
          );
        })}
      </nav>

      <AdminSubTabNav
        section={sectionConfig}
        activeSubTab={nav.subTab}
        onSubTabChange={selectSubTab}
      />
    </header>
  );
}
