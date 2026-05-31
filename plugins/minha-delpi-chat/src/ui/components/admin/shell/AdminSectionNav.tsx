import { useState } from "react";
import { ChevronDown } from "lucide-react";

import {
  ADMIN_SECTIONS,
  type AdminNavState,
  type AdminSection,
} from "../../../../navigation/adminNavigation";

import "./AdminSectionNav.css";

type AdminSectionNavProps = {
  nav: AdminNavState;
  onNavigate: (section: AdminSection) => void;
};

export function AdminSectionNav({ nav, onNavigate }: AdminSectionNavProps) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const activeItem =
    ADMIN_SECTIONS.find((item) => item.key === nav.section) ?? ADMIN_SECTIONS[0];
  const ActiveIcon = activeItem.icon;

  return (
    <>
      <nav
        className="mdc-admin-section-nav mdc-chat-project-home__tabs"
        aria-label="Seções do admin"
      >
        {ADMIN_SECTIONS.map((item) => {
          const Icon = item.icon;
          const isActive = item.key === nav.section;

          return (
            <button
              key={item.key}
              type="button"
              className={isActive ? "is-active" : undefined}
              aria-current={isActive ? "page" : undefined}
              onClick={() => onNavigate(item.key)}
            >
              <Icon size={16} aria-hidden="true" />
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>

      <div className="mdc-admin-section-nav__mobile">
        <button
          type="button"
          className="mdc-admin-section-nav__mobile-trigger"
          aria-expanded={mobileOpen}
          onClick={() => setMobileOpen((open) => !open)}
        >
          <ActiveIcon size={18} aria-hidden="true" />
          <span>{activeItem.label}</span>
          <ChevronDown size={16} aria-hidden="true" />
        </button>

        {mobileOpen ? (
          <div className="mdc-admin-section-nav__mobile-menu" role="menu">
            {ADMIN_SECTIONS.map((item) => {
              const Icon = item.icon;

              return (
                <button
                  key={item.key}
                  type="button"
                  role="menuitem"
                  onClick={() => {
                    onNavigate(item.key);
                    setMobileOpen(false);
                  }}
                >
                  <Icon size={16} aria-hidden="true" />
                  <span>{item.label}</span>
                </button>
              );
            })}
          </div>
        ) : null}
      </div>
    </>
  );
}
