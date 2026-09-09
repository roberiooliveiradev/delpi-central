import type { ReactNode } from "react";

import { PpActionButton, PpWorkbenchDialog } from "../app/productionPulseUi";
import { useViewportBucket } from "../hooks/useViewportBucket";
import { isMobileViewport } from "../utils/viewportLayout";

type AdminSidePanelProps = {
  open: boolean;
  title: string;
  onClose: () => void;
  children: ReactNode;
  /** On mobile, catalogs open as page dialog (not side drawer). */
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
      <PpWorkbenchDialog open={open} title={title} onClose={onClose}>
        {children}
      </PpWorkbenchDialog>
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
