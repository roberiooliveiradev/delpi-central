import { Menu, X } from "lucide-react";
import { useEffect, useState, type ReactNode } from "react";

import type { AdminNavState } from "../../../../navigation/adminNavigation";
import { AdminSidebar } from "./AdminSidebar";

import "./AdminShellLayout.css";

type AdminShellLayoutProps = {
  nav: AdminNavState;
  onNavigate: (next: AdminNavState) => void;
  children: ReactNode;
};

export function AdminShellLayout({ nav, onNavigate, children }: AdminShellLayoutProps) {
  const [mobileNavOpen, setMobileNavOpen] = useState(false);

  useEffect(() => {
    setMobileNavOpen(false);
  }, [nav.section, nav.subTab]);

  return (
    <div className="mdc-admin-layout">
      <div className="mdc-admin-layout__nav-toggle-wrap">
        <button
          type="button"
          className="mdc-chat-ws-outline-btn mdc-admin-layout__nav-toggle"
          aria-expanded={mobileNavOpen}
          onClick={() => setMobileNavOpen((open) => !open)}
        >
          {mobileNavOpen ? <X size={16} aria-hidden="true" /> : <Menu size={16} aria-hidden="true" />}
          <span>{mobileNavOpen ? "Fechar menu" : "Menu do admin"}</span>
        </button>
      </div>

      <div
        className={[
          "mdc-admin-layout__body",
          mobileNavOpen ? "mdc-admin-layout__body--nav-open" : "",
        ]
          .filter(Boolean)
          .join(" ")}
      >
        <AdminSidebar nav={nav} onNavigate={onNavigate} className="mdc-admin-layout__sidebar" />
        <div className="mdc-admin-layout__content">{children}</div>
      </div>
    </div>
  );
}
