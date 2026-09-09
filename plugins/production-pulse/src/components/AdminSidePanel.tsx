import type { ReactNode } from "react";

import { PpActionButton, PpHostContainedDrawer } from "../app/productionPulseUi";
import { useViewportBucket } from "../hooks/useViewportBucket";
import { isMobileViewport } from "../utils/viewportLayout";

type AdminSidePanelProps = {
  open: boolean;
  title: string;
  onClose: () => void;
  children: ReactNode;
  preferDrawerOnMobile?: boolean;
};

export function AdminSidePanel({
  open,
  title,
  onClose,
  children,
  preferDrawerOnMobile = true,
}: AdminSidePanelProps) {
  const viewport = useViewportBucket();
  const mobile = isMobileViewport(viewport);

  if (!open) return null;

  if (preferDrawerOnMobile && mobile) {
    return (
      <PpHostContainedDrawer open={open} title={title} onClose={onClose}>
        {children}
      </PpHostContainedDrawer>
    );
  }

  return (
    <aside className="pp-admin-side-panel" aria-label={title}>
      <header className="pp-admin-side-panel__head">
        <h2 className="pp-admin-side-panel__title">{title}</h2>
        <PpActionButton variant="ghost" onClick={onClose} aria-label="Fechar painel">
          Fechar
        </PpActionButton>
      </header>
      <div className="pp-admin-side-panel__body">{children}</div>
    </aside>
  );
}
