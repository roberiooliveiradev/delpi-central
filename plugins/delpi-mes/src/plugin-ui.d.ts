declare module "@delpi/plugin-ui/index" {
  import type { ReactNode } from "react";
  export type EmptyStateClassNames = { root: string; withTitle: boolean };
  export function emptyStatePanelBemClasses(prefix: string): EmptyStateClassNames;
  export function EmptyState(props: { title?: string; message?: string; classNames: EmptyStateClassNames; defaultTitle?: string; defaultMessage: string; children?: ReactNode; role?: "status" | "alert" }): ReactNode;
  export function LoadingState(props: { message?: string; classNames: { root: string; spinner?: string }; defaultMessage: string }): ReactNode;
  export function loadingStatePanelBemClasses(prefix: string): { root: string; spinner?: string };
  export function MetricStrip(props: { classNames: unknown; items: Array<{ id: string; label: string; value: ReactNode; description?: string; tone?: "neutral" | "success" | "warning" | "danger" | "info" }>; density?: "comfortable" | "compact"; "aria-label"?: string }): ReactNode;
  export function metricStripBemClasses(prefix: string): unknown;
  export function StatusBadge(props: { label: string; variant?: "neutral" | "info" | "success" | "warning" | "danger"; classNames: unknown }): ReactNode;
  export function statusBadgeBemClasses(prefix: string): unknown;
  export function InlineMeter(props: { classNames: unknown; value?: number; max?: number; tone?: "neutral" | "success" | "warning" | "danger"; label?: ReactNode; "aria-label"?: string }): ReactNode;
  export function inlineMeterBemClasses(prefix: string): unknown;
  export function DrawerShell(props: { open: boolean; title: string; description?: string; onClose: () => void; children: ReactNode; classNames: unknown; portalScopeClassName?: string; closeOnBackdropClick?: boolean }): ReactNode;
  export function drawerShellBemClasses(prefix: string): unknown;
  export function Timeline(props: { items: Array<{ id: string; title: ReactNode; occurredAt?: string | null; timeLabel?: ReactNode; detail?: ReactNode; meta?: ReactNode; tone?: "default" | "danger" | "warning" | "success" | "info" }>; loading?: boolean; emptyMessage?: string; classNames: unknown; prefix: string; "aria-label"?: string }): ReactNode;
  export function timelineBemClasses(prefix: string): unknown;
  export type ModalShellClassNames = {
    overlay: string; dialog: string; header: string; title: string;
    closeButton: string; body: string; headerText?: string;
    description?: string; footer?: string; headerActions?: string;
  };
  export function modalShellBemClasses(prefix: string): ModalShellClassNames;
  export function ModalShell(props: {
    open: boolean; title: string; description?: string; footer?: ReactNode;
    headerActions?: ReactNode; onClose: () => void; children: ReactNode;
    classNames: ModalShellClassNames; className?: string;
    overlayClassName?: string; closeAriaLabel?: string;
    closeOnOverlayClick?: boolean; initialFocusSelector?: string;
    portalScopeClassName?: string;
  }): ReactNode;
  export type ConfirmModalClassNames = {
    root: string; rootDanger: string; iconWrap: string; iconWrapDanger: string;
    message: string; actions: string; cancelButton: string;
    confirmButton: string; confirmButtonDanger: string; secondaryButton?: string;
  };
  export function confirmModalBemClasses(prefix: string, options?: { actionsBlock?: string; actionsAlign?: "start" | "end" }): ConfirmModalClassNames;
  export function ConfirmModalPanel(props: {
    message: ReactNode; confirmLabel?: string; cancelLabel?: string;
    secondaryLabel?: string; confirmBusy?: boolean; confirmBusyLabel?: string;
    variant?: "default" | "danger"; showCancel?: boolean;
    onConfirm: () => void; onCancel: () => void; onSecondary?: () => void;
    classNames: ConfirmModalClassNames;
  }): ReactNode;
  export type FloatingNoticeItem = {
    id: string; message: ReactNode; title?: string;
    variant?: "error" | "warning" | "success" | "info";
    autoDismissMs?: number | null;
    action?: { label: string; onClick: () => void };
    onClose?: () => void;
  };
  export type FloatingNoticeInput = Omit<FloatingNoticeItem, "id"> & { id?: string };
  export type FloatingNoticeStackClassNames = {
    stack: string; notice: string; icon: string; content: string;
    title: string; message: string; action: string; closeButton: string; progress: string;
  };
  export function floatingNoticeStackBemClasses(prefix: string): FloatingNoticeStackClassNames;
  export function useFloatingNotices(): {
    items: FloatingNoticeItem[];
    push: (notice: FloatingNoticeInput | string) => string;
    dismiss: (id: string) => void;
    clear: () => void;
  };
  export function FloatingNoticeStack(props: {
    items: FloatingNoticeItem[]; onDismiss: (id: string) => void;
    classNames: FloatingNoticeStackClassNames;
    labels?: { dismissAriaLabel?: string; stackAriaLabel?: string };
    defaultAutoDismissMs?: Partial<Record<"error" | "warning" | "success" | "info", number | null>>;
    portalScopeClassName?: string;
  }): ReactNode;
  export function AnchoredPanelPortal(props: {
    open: boolean;
    anchorRef: { current: HTMLElement | null };
    panelRef: { current: HTMLDivElement | null };
    className?: string;
    variant?: "shape" | "bare";
    role?: string;
    "aria-label"?: string;
    matchAnchorWidth?: boolean;
    preferredPlacement?: "bottom" | "top" | "right" | "left";
    allowFlip?: boolean;
    horizontalAlign?: "start" | "end";
    gap?: number;
    portalScopeClassName?: string;
    onDismiss?: () => void;
    exclusive?: boolean;
    children?: ReactNode;
  }): ReactNode;
}
