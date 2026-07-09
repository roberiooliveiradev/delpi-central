import { ModalShell, type ModalShellClassNames } from "@delpi/plugin-ui";
import type { PropsWithChildren, ReactNode } from "react";

import { lockPageScroll } from "../utils/pageScrollLock";
import "./Modal.css";

type ModalSize = "sm" | "md" | "lg" | "xl";

type ModalProps = PropsWithChildren<{
  open: boolean;
  title: string;
  description?: string;
  footer?: ReactNode;
  onClose: () => void;
  size?: ModalSize;
  initialFocusSelector?: string;
}>;

const SI_MODAL_CLASS_NAMES: ModalShellClassNames = {
  overlay: "si-modal-overlay",
  dialog: "si-modal",
  header: "si-modal__header",
  headerText: "si-modal__header-text",
  title: "si-modal__title",
  description: "si-modal__description",
  closeButton: "si-modal__close",
  body: "si-modal__body",
  footer: "si-modal__footer",
};

export function Modal({
  open,
  title,
  description,
  children,
  footer,
  onClose,
  size = "md",
  initialFocusSelector,
}: ModalProps) {
  return (
    <ModalShell
      open={open}
      title={title}
      description={description}
      footer={footer}
      onClose={onClose}
      classNames={SI_MODAL_CLASS_NAMES}
      className={`si-modal--${size}`}
      initialFocusSelector={initialFocusSelector}
      lockPageScroll={lockPageScroll}
      closeAriaLabel="Fechar janela"
      overlayAriaHidden
    >
      {children}
    </ModalShell>
  );
}
