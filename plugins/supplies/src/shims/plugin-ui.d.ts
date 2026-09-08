/**
 * Contratos do remote `@delpi/plugin-ui` para o tsc do MFE.
 * Runtime: Module Federation. Vitest: pluginUiTestAliases → fonte do kit.
 */
declare module "@delpi/plugin-ui/index" {
  import type { ComponentType, MouseEventHandler, ReactNode } from "react";

  export function HelpTooltip(props: {
    content: string;
    ariaLabel?: string;
    children?: ReactNode;
  }): ReactNode;

  export function emptyStateCardBemClasses(prefix: string): {
    root: string;
    withTitle: boolean;
  };

  export function stateBannerBemClasses(prefix: string): {
    root: string;
    error: string;
    success: string;
  };

  export function createDashboardEmptyState(config: {
    classNames: { root: string; withTitle: boolean };
    defaultMessage: string;
    defaultTitle?: string;
  }): ComponentType<{
    title?: string;
    message?: string;
    children?: ReactNode;
    role?: "status" | "alert";
  }>;

  export function createDashboardStateBanner(config: {
    classNames: { root: string; error: string; success: string };
  }): ComponentType<{
    children: ReactNode;
    variant?: "default" | "error" | "success";
    className?: string;
  }>;

  export function createDashboardTopBar(config: { prefix: string }): ComponentType<{
    items: Array<{
      id: string;
      label: ReactNode;
      icon?: ReactNode;
      title?: string;
      count?: number;
      onSelect?: () => void;
    }>;
    activeId: string;
    "aria-label"?: string;
    collapsible?: boolean;
    collapseMode?: "rail" | "hamburger";
    collapseTrigger?: "manual" | "overflow";
    storageKey?: string;
    collapseLabel?: string;
    expandLabel?: string;
    menuLabel?: string;
    portalScopeClassName?: string;
    actions?: ReactNode;
    secondary?: ReactNode;
  }>;

  export function createDashboardCommandPalette(config: {
    prefix: string;
    portalScopeClassName: string;
  }): ComponentType<{
    open: boolean;
    onClose: () => void;
    title: string;
    value: string;
    onChange: (value: string) => void;
    hits?: ReadonlyArray<{ id: string; label: string; groupLabel?: string }>;
    onSelectHit: (id: string) => void;
    placeholder?: string;
    emptyHitsLabel?: string;
    closeAriaLabel?: string;
    "aria-label"?: string;
  }>;

  export function createDashboardPagePath(config: {
    prefix: string;
    portalScopeClassName?: string;
  }): ComponentType<{
    back: {
      label: string;
      href: string;
      onNavigate?: MouseEventHandler<HTMLAnchorElement>;
    };
    items?: Array<{ id: string; label: string; href: string }>;
    current: string;
  }>;

  export function createDashboardViewTransition(config: { prefix: string }): ComponentType<{
    transitionKey: string;
    tone?: "page" | "panel";
    children: ReactNode;
  }>;

  export type KpiCardLabels = {
    goalPrefix: string;
    iddScorePrefix: string;
    badgesStatus: string;
  };

  export type DashboardKpiCardProps = {
    title: string;
    titleHint?: string;
    value: string;
    contextLabel?: string;
    goalLabel?: string | null;
    subtitle?: string;
    icon: ReactNode;
    footer?: ReactNode;
    loading?: boolean;
    className?: string;
    onClick?: () => void;
    "aria-label"?: string;
  };

  export function createDashboardKpiCard(config: {
    prefix: string;
    labels: KpiCardLabels;
    cardModifier?: string;
  }): ComponentType<DashboardKpiCardProps>;
}

declare module "@delpi/plugin-ui/styles";
