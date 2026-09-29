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
}
