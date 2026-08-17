declare module "@delpi/plugin-ui/index" {
  import type { ComponentType, ReactNode } from "react";

  export type MetricKpiCardTone = "default" | "positive" | "negative" | "warning";

  export type DashboardMetricKpiCardProps = {
    label?: string;
    titleHint?: string;
    value: string;
    hint?: ReactNode;
    icon?: ReactNode;
    tone?: MetricKpiCardTone;
    className?: string;
    fitValue?: boolean;
  };

  export function createMetricKpiCard(
    prefix: string,
  ): ComponentType<DashboardMetricKpiCardProps>;

  export type SectionCardClassNames = {
    section: string;
    header: string;
    title: string;
    titleWithHelp: string;
    subtitle: string;
    actions: string;
    body?: string;
    collapseToggle?: string;
  };

  export type SectionCardLabels = {
    titleHelpAriaLabel: (title: string) => string;
    expandAriaLabel?: (title: string) => string;
    collapseAriaLabel?: (title: string) => string;
  };

  export type DashboardSectionCardProps = {
    title: string;
    subtitle?: string;
    hint?: string;
    children: ReactNode;
    actions?: ReactNode;
    className?: string;
    collapsible?: boolean;
    defaultOpen?: boolean;
    open?: boolean;
    onOpenChange?: (open: boolean) => void;
  };

  export function sectionCardPacBemClasses(prefix: string): SectionCardClassNames;

  export function createDashboardSectionCard(config: {
    classNames: SectionCardClassNames;
    labels: SectionCardLabels;
  }): ComponentType<DashboardSectionCardProps>;

  export type InlineMeterTone = "neutral" | "success" | "warning" | "danger";

  export type DashboardInlineMeterProps = {
    value?: number;
    max?: number;
    tone?: InlineMeterTone;
    label?: ReactNode;
    size?: "sm" | "md";
    className?: string;
    "aria-label"?: string;
  };

  export function createDashboardInlineMeter(config: {
    prefix: string;
  }): ComponentType<DashboardInlineMeterProps>;

  export type CreateModalShellConfig = {
    prefix: string;
    portalScopeClassName: string;
    containedLayout?: "fill" | "dialog";
    closeAriaLabel?: string;
    labels?: Record<string, string>;
  };

  export type DashboardModalShellProps = {
    open: boolean;
    onClose: () => void;
    title?: ReactNode;
    children?: ReactNode;
    footer?: ReactNode;
    className?: string;
    size?: string;
  };

  export function createHostContainedModalShell(
    config: CreateModalShellConfig,
  ): ComponentType<DashboardModalShellProps>;

  export type ConfirmModalClassNames = {
    root: string;
    rootDanger: string;
    iconWrap: string;
    iconWrapDanger: string;
    message: string;
    actions: string;
    cancelButton: string;
    confirmButton: string;
    confirmButtonDanger: string;
    secondaryButton?: string;
  };

  export type ConfirmModalPanelProps = {
    message: ReactNode;
    confirmLabel?: string;
    cancelLabel?: string;
    secondaryLabel?: string;
    confirmBusy?: boolean;
    confirmBusyLabel?: string;
    variant?: "default" | "danger";
    showCancel?: boolean;
    onConfirm: () => void;
    onCancel: () => void;
    onSecondary?: () => void;
    classNames: ConfirmModalClassNames;
  };

  export function confirmModalBemClasses(prefix: string): ConfirmModalClassNames;

  export function ConfirmModalPanel(props: ConfirmModalPanelProps): ReactNode;
}
