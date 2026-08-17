import type { ReactNode } from "react";
import {
  ConfirmModalPanel,
  confirmModalBemClasses,
  createDashboardInlineMeter,
  createDashboardSectionCard,
  createHostContainedModalShell,
  createMetricKpiCard,
  sectionCardPacBemClasses,
} from "@delpi/plugin-ui/index";

/** Prefixo BEM local; estilos visuais vêm do dual-class `delpi-ui-*` no kit. */
export const UI_PREFIX = "adc";

/** Escopo CSS do shell do MFE — portal do modal fica contido no host. */
export const CONSOLE_HOST_CLASS = "api-delpi-console";

export const ConsoleMetricKpiCard = createMetricKpiCard(UI_PREFIX);

export const ConsoleInlineMeter = createDashboardInlineMeter({ prefix: UI_PREFIX });

export const consoleSectionLabels = {
  titleHelpAriaLabel: (title: string) => `Ajuda: ${title}`,
  expandAriaLabel: (title: string) => `Expandir ${title}`,
  collapseAriaLabel: (title: string) => `Recolher ${title}`,
};

export const ConsoleSectionCard = createDashboardSectionCard({
  classNames: sectionCardPacBemClasses(UI_PREFIX),
  labels: consoleSectionLabels,
});

const ConsoleHostDialog = createHostContainedModalShell({
  prefix: UI_PREFIX,
  portalScopeClassName: CONSOLE_HOST_CLASS,
  containedLayout: "dialog",
  closeAriaLabel: "Fechar",
});

const consoleConfirmClassNames = confirmModalBemClasses(UI_PREFIX);

export type ConsoleConfirmDialogProps = {
  open: boolean;
  title?: string;
  message: ReactNode;
  confirmLabel?: string;
  cancelLabel?: string;
  confirmBusy?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
};

/** Confirmação host-contained (não cobre a sidebar do portal). */
export function ConsoleConfirmDialog({
  open,
  title = "Confirmar",
  message,
  confirmLabel = "Confirmar",
  cancelLabel = "Cancelar",
  confirmBusy = false,
  onConfirm,
  onCancel,
}: ConsoleConfirmDialogProps) {
  return (
    <ConsoleHostDialog open={open} title={title} onClose={onCancel}>
      <ConfirmModalPanel
        message={message}
        confirmLabel={confirmLabel}
        cancelLabel={cancelLabel}
        confirmBusy={confirmBusy}
        variant="danger"
        onConfirm={onConfirm}
        onCancel={onCancel}
        classNames={consoleConfirmClassNames}
      />
    </ConsoleHostDialog>
  );
}
