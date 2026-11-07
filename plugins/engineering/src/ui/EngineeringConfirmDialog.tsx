import type { ReactNode } from "react";

import {
  ConfirmModalPanel,
  confirmModalBemClasses,
} from "@delpi/plugin-ui/index";

import { EngineeringHostDialog, ENG_UI_PREFIX } from "./engineeringUi";

const engConfirmClassNames = confirmModalBemClasses(ENG_UI_PREFIX);

export type EngineeringConfirmDialogProps = {
  open: boolean;
  title?: string;
  message: ReactNode;
  confirmLabel?: string;
  cancelLabel?: string;
  confirmBusy?: boolean;
  variant?: "default" | "danger";
  showCancel?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
};

/** Confirmação host-contained (não cobre a sidebar do portal) — mesmo
 * padrão do CommercialConfirmModal, via façade engineering. */
export function EngineeringConfirmDialog({
  open,
  title = "Confirmar",
  message,
  confirmLabel = "Confirmar",
  cancelLabel = "Cancelar",
  confirmBusy = false,
  variant = "default",
  showCancel = true,
  onConfirm,
  onCancel,
}: EngineeringConfirmDialogProps) {
  return (
    <EngineeringHostDialog
      open={open}
      title={title}
      onClose={onCancel}
      className="engineering-prc-confirm"
    >
      <ConfirmModalPanel
        message={message}
        confirmLabel={confirmLabel}
        cancelLabel={cancelLabel}
        confirmBusy={confirmBusy}
        variant={variant}
        showCancel={showCancel}
        onConfirm={onConfirm}
        onCancel={onCancel}
        classNames={engConfirmClassNames}
      />
    </EngineeringHostDialog>
  );
}
