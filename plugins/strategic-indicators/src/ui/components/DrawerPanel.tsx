import { DrawerShell, type DrawerShellClassNames } from "@delpi/plugin-ui";
import type { PropsWithChildren, ReactNode } from "react";

import { lockPageScroll } from "../utils/pageScrollLock";
import "./DrawerPanel.css";

type DrawerPanelProps = PropsWithChildren<{
  open: boolean;
  onClose: () => void;
  title: string;
  description?: string;
  footer?: ReactNode;
  size?: "md" | "lg" | "xl";
}>;

const SI_DRAWER_CLASS_NAMES: DrawerShellClassNames = {
  root: "si-drawer-root",
  backdrop: "si-drawer-root__backdrop",
  panel: "si-drawer",
  header: "si-drawer__header",
  headerText: "si-drawer__header-text",
  title: "si-drawer__title",
  description: "si-drawer__description",
  closeButton: "si-drawer__close",
  body: "si-drawer__body",
  footer: "si-drawer__footer",
};

export function DrawerPanel({
  open,
  onClose,
  title,
  description,
  footer,
  size = "lg",
  children,
}: DrawerPanelProps) {
  return (
    <DrawerShell
      open={open}
      title={title}
      description={description}
      footer={footer}
      onClose={onClose}
      classNames={SI_DRAWER_CLASS_NAMES}
      className={`si-drawer--${size}`}
      lockPageScroll={lockPageScroll}
    >
      {children}
    </DrawerShell>
  );
}
