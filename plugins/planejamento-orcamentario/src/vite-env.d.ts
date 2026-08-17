/// <reference types="vite/client" />

declare module "@delpi/plugin-ui/styles";

declare module "@delpi/plugin-ui/index" {
  import type { ComponentType, ReactNode } from "react";

  export function sectionCardPacBemClasses(prefix: string): Record<string, unknown>;

  export function createDashboardSectionCard(config: {
    classNames: Record<string, unknown>;
    labels: { titleHelpAriaLabel: (title: string) => string };
  }): ComponentType<{
    title: string;
    hint?: string;
    children: ReactNode;
  }>;

  export function createDashboardLoadingActivityCard(config: {
    prefix: string;
    labels: Record<string, unknown>;
    withCopyWrapper?: boolean;
    block?: string;
    defaultTone?: "neutral" | "info";
  }): ComponentType<{
    title: string;
    description?: string;
    variant?: "compact" | "panel";
    sticky?: boolean;
    progressPercent?: number;
    tone?: "neutral" | "info";
  }>;

  export function createDashboardStateBox(config: { prefix: string }): ComponentType<{
    children: ReactNode;
    variant?: "default" | "error" | "success" | "warning";
    dismissible?: boolean;
    onDismiss?: () => void;
  }>;

  export type DirectoryUserOption = {
    id: string;
    name: string;
    email: string;
  };

  export type UserDirectoryPickerProps = {
    value: DirectoryUserOption[];
    onChange: (users: DirectoryUserOption[]) => void;
    searchUsers: (
      query: string,
      limit?: number,
      signal?: AbortSignal,
    ) => Promise<DirectoryUserOption[]>;
    disabled?: boolean;
    showSelectedList?: boolean;
    showEmail?: boolean;
    maxSelected?: number;
    labels?: {
      title?: string;
      hint?: string;
      placeholder?: string;
    };
    className?: string;
  };

  export const UserDirectoryPicker: ComponentType<UserDirectoryPickerProps>;

  export type DashboardSimpleKpiCardProps = {
    title: string;
    titleHint?: string;
    value: string;
    icon: ReactNode;
    loading?: boolean;
    subtitle?: string;
    variant?: string;
    wide?: boolean;
    valueTone?: "default" | "danger";
    iconClassName?: string;
    valueTag?: "h3" | "p" | "strong";
    layout?: "iconStart" | "iconEnd";
    className?: string;
  };

  export function createSimpleKpiCard(
    prefix: string,
    options?: {
      withBody?: boolean;
      withSubtitle?: boolean;
      layout?: "iconStart" | "iconEnd";
      block?: string;
    },
  ): ComponentType<DashboardSimpleKpiCardProps>;

  export type DashboardModalShellProps = {
    open: boolean;
    title: ReactNode;
    onClose: () => void;
    children?: ReactNode;
    description?: string;
    className?: string;
    footer?: ReactNode;
    closeAriaLabel?: string;
    containedLayout?: "fill" | "dialog";
  };

  export function createHostContainedModalShell(config: {
    prefix: string;
    portalScopeClassName: string;
    containedLayout?: "fill" | "dialog";
    closeAriaLabel?: string;
    variant?: "default" | "wide" | "page";
  }): ComponentType<DashboardModalShellProps>;
}
