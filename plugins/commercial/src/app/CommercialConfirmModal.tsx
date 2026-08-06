import type { ReactNode } from "react";

import {
  ConfirmModalPanel,
  confirmModalBemClasses,
  createHostContainedModalShell,
} from "@delpi/plugin-ui/index";

import { UI_PREFIX } from "./commercialUi";

const COMMERCIAL_HOST_CLASS = "dashboard-commercial";

const CommercialHostDialog = createHostContainedModalShell({
  prefix: UI_PREFIX,
  portalScopeClassName: COMMERCIAL_HOST_CLASS,
  containedLayout: "dialog",
});

const cmConfirmModalClassNames = confirmModalBemClasses(UI_PREFIX);

export type CommercialConfirmModalProps = {
  open: boolean;
  title?: string;
  message: ReactNode;
  confirmLabel?: string;
  cancelLabel?: string;
  secondaryLabel?: string;
  confirmBusy?: boolean;
  variant?: "default" | "danger";
  onConfirm: () => void;
  onCancel: () => void;
  onSecondary?: () => void;
};

/** Confirmação host-contained (não cobre a sidebar do portal). */
export function CommercialConfirmModal({
  open,
  title = "Confirmar",
  message,
  confirmLabel = "Confirmar",
  cancelLabel = "Cancelar",
  secondaryLabel,
  confirmBusy = false,
  variant = "default",
  onConfirm,
  onCancel,
  onSecondary,
}: CommercialConfirmModalProps) {
  return (
    <CommercialHostDialog
      open={open}
      title={title}
      onClose={onCancel}
      className="cm-modal--confirm"
    >
      <ConfirmModalPanel
        message={message}
        confirmLabel={confirmLabel}
        cancelLabel={cancelLabel}
        secondaryLabel={secondaryLabel}
        confirmBusy={confirmBusy}
        variant={variant}
        onConfirm={onConfirm}
        onCancel={onCancel}
        onSecondary={onSecondary}
        classNames={cmConfirmModalClassNames}
      />
    </CommercialHostDialog>
  );
}
