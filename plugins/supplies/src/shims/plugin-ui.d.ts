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

  export function ActionButton(props: {
    children: ReactNode;
    variant?: "primary" | "secondary" | "ghost" | "danger";
    onClick?: () => void;
    disabled?: boolean;
    type?: "button" | "submit" | "reset";
    className?: string;
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

  export function sectionCardPacBemClasses(prefix: string): Record<string, string>;
  export function sectionRouteCardBemClasses(prefix: string): Record<string, string>;
  export function catalogSearchBarBemClasses(prefix: string): Record<string, string>;

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

  export function createDashboardTopBarSearchTrigger(config: {
    prefix: string;
  }): ComponentType<{
    onOpen: () => void;
    label: string;
    shortcutLabel: string;
    "aria-label": string;
    title?: string;
    className?: string;
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

  export function createDashboardPageHero(config: { prefix: string }): ComponentType<{
    eyebrow?: ReactNode;
    title: ReactNode;
    description?: ReactNode;
    badge?: ReactNode;
    actions?: ReactNode;
    highlights?: Array<{
      id: string;
      label: ReactNode;
      value: ReactNode;
      tone?: "neutral" | "warning" | "danger";
    }>;
    density?: "comfortable" | "compact";
    "aria-label"?: string;
    children?: ReactNode;
  }>;

  export function createDashboardSectionCard(config: {
    classNames: Record<string, string>;
    labels: {
      titleHelpAriaLabel: (title: string) => string;
      expandAriaLabel: (title: string) => string;
      collapseAriaLabel: (title: string) => string;
    };
  }): ComponentType<{
    title: string;
    subtitle?: string;
    hint?: string;
    children: ReactNode;
    actions?: ReactNode;
  }>;

  export function createDashboardSectionRouteCard(config: {
    classNames: Record<string, string>;
  }): ComponentType<{
    title: string;
    description?: string;
    icon?: ReactNode;
    routes: Array<{
      id: string;
      label: string;
      onClick: () => void;
      pinned?: boolean;
      onPinClick?: () => void;
      pinLabel?: string;
      unpinLabel?: string;
    }>;
  }>;

  export function createDashboardCatalogSearchBar(config: {
    classNames: Record<string, string>;
  }): ComponentType<{
    value: string;
    onChange: (value: string) => void;
    hits?: ReadonlyArray<{ id: string; label: string; groupLabel?: string }>;
    onSelectHit: (id: string) => void;
    placeholder?: string;
    clearLabel?: string;
    emptyHitsLabel?: string;
    "aria-label"?: string;
  }>;

  export function createDashboardHubChipRow(config: {
    prefix: string;
  }): ComponentType<{
    label: string;
    "aria-label"?: string;
    children: ReactNode;
  }>;

  export function createDashboardRouteChip(config: { prefix: string }): ComponentType<{
    label: string;
    tone?: "pinned" | "recent" | "default";
    leadingIcon?: ReactNode;
    onNavigate: () => void;
    onRemove?: () => void;
    removeLabel?: string;
  }>;

  export function createDashboardStatusBadge(config: { prefix: string }): ComponentType<{
    label: string;
    variant?: "neutral" | "info" | "success" | "warning" | "danger";
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
