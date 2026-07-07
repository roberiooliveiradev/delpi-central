import type { ReactNode } from "react";
import { RefreshCw } from "lucide-react";

export type PageHeaderLayout = "brand" | "titleRow" | "stack";

export type PageHeaderClassNames = {
  root: string;
  rootCompact?: string;
  brand?: string;
  icon?: string;
  content?: string;
  eyebrow?: string;
  subtitle?: string;
  actions?: string;
  titleWrap?: string;
  titleRow?: string;
  title?: string;
  badge?: string;
  description?: string;
  primaryButton?: string;
  spinClass?: string;
};

export type PageHeaderLabels = {
  refresh: string;
  refreshing: string;
};

export type PageHeaderProps = {
  layout: PageHeaderLayout;
  title: ReactNode;
  subtitle?: ReactNode;
  eyebrow?: ReactNode;
  icon?: ReactNode;
  badge?: ReactNode;
  nav?: ReactNode;
  actions?: ReactNode;
  onRefresh?: () => void;
  refreshing?: boolean;
  compact?: boolean;
  classNames: PageHeaderClassNames;
  labels: PageHeaderLabels;
};

function RefreshButton({
  onRefresh,
  refreshing,
  classNames,
  labels,
}: Pick<PageHeaderProps, "onRefresh" | "refreshing" | "classNames" | "labels">) {
  if (!onRefresh || !classNames.primaryButton) return null;

  return (
    <button
      type="button"
      className={classNames.primaryButton}
      onClick={onRefresh}
      disabled={refreshing}
    >
      <RefreshCw
        size={16}
        aria-hidden={true}
        className={refreshing && classNames.spinClass ? classNames.spinClass : undefined}
      />
      {refreshing ? labels.refreshing : labels.refresh}
    </button>
  );
}

function BrandLayout(props: PageHeaderProps) {
  const { classNames, title, subtitle, eyebrow, icon, nav, actions, onRefresh, refreshing, labels } =
    props;
  const mergedActions =
    actions || onRefresh ? (
      <div className={classNames.actions}>
        {actions}
        <RefreshButton
          onRefresh={onRefresh}
          refreshing={refreshing}
          classNames={classNames}
          labels={labels}
        />
      </div>
    ) : null;

  return (
    <>
      <div className={classNames.brand}>
        {icon && classNames.icon ? (
          <div className={classNames.icon} aria-hidden={true}>
            {icon}
          </div>
        ) : null}
        <div className={classNames.content}>
          {eyebrow && classNames.eyebrow ? <p className={classNames.eyebrow}>{eyebrow}</p> : null}
          <h1>{title}</h1>
          {subtitle && classNames.subtitle ? (
            <span className={classNames.subtitle}>{subtitle}</span>
          ) : null}
          {nav}
        </div>
      </div>
      {mergedActions}
    </>
  );
}

function TitleRowLayout(props: PageHeaderProps) {
  const { classNames, title, subtitle, icon, actions, onRefresh, refreshing, labels } = props;

  return (
    <>
      <div className={classNames.titleWrap}>
        {icon && classNames.icon ? (
          <span className={classNames.icon} aria-hidden={true}>
            {icon}
          </span>
        ) : null}
        <div>
          <h1>{title}</h1>
          {subtitle ? <p>{subtitle}</p> : null}
        </div>
      </div>
      <div className={classNames.actions}>
        {actions}
        <RefreshButton
          onRefresh={onRefresh}
          refreshing={refreshing}
          classNames={classNames}
          labels={labels}
        />
      </div>
    </>
  );
}

function StackLayout(props: PageHeaderProps) {
  const { classNames, title, subtitle, eyebrow, badge, actions } = props;

  return (
    <>
      <div className={classNames.content}>
        {eyebrow && classNames.eyebrow ? (
          <p className={classNames.eyebrow}>{eyebrow}</p>
        ) : null}
        <div className={classNames.titleRow}>
          <h1 className={classNames.title}>{title}</h1>
          {badge && classNames.badge ? <div className={classNames.badge}>{badge}</div> : null}
        </div>
        {subtitle && classNames.description ? (
          <p className={classNames.description}>{subtitle}</p>
        ) : null}
      </div>
      {actions && classNames.actions ? (
        <div className={classNames.actions}>{actions}</div>
      ) : null}
    </>
  );
}

export function pageHeaderBrandBemClasses(prefix: string): PageHeaderClassNames {
  return {
    root: `${prefix}-page-header`,
    rootCompact: `${prefix}-page-header ${prefix}-page-header--compact`,
    brand: `${prefix}-page-header__brand`,
    icon: `${prefix}-header__icon`,
    content: `${prefix}-page-header__content`,
    eyebrow: `${prefix}-eyebrow`,
    subtitle: `${prefix}-page-subtitle`,
    actions: `${prefix}-header-actions`,
    primaryButton: `${prefix}-primary-btn`,
  };
}

export function pageHeaderPacBrandBemClasses(prefix: string): PageHeaderClassNames {
  return {
    root: `${prefix}-page-header`,
    brand: `${prefix}-page-header__brand`,
    icon: `${prefix}-header__icon`,
    eyebrow: `${prefix}-eyebrow`,
    subtitle: `${prefix}-page-subtitle`,
    actions: `${prefix}-header-actions`,
  };
}

export function pageHeaderTitleRowBemClasses(
  prefix: string,
  options?: { buttonClass?: string; spinClass?: string },
): PageHeaderClassNames {
  const button = options?.buttonClass ?? `${prefix}-btn ${prefix}-btn--primary`;
  return {
    root: `${prefix}-page-header`,
    titleWrap: `${prefix}-page-header__title`,
    icon: `${prefix}-page-header__icon`,
    actions: `${prefix}-page-header__actions`,
    primaryButton: button,
    spinClass: options?.spinClass ?? `${prefix}-spin`,
  };
}

export function pageHeaderStackBemClasses(prefix: string): PageHeaderClassNames {
  return {
    root: `${prefix}-page-header`,
    content: `${prefix}-page-header__content`,
    eyebrow: `${prefix}-page-header__eyebrow`,
    titleRow: `${prefix}-page-header__title-row`,
    title: `${prefix}-page-header__title`,
    badge: `${prefix}-page-header__badge`,
    description: `${prefix}-page-header__description`,
    actions: `${prefix}-page-header__actions`,
  };
}

export function PageHeader(props: PageHeaderProps) {
  const headerClass = [
    props.compact && props.classNames.rootCompact
      ? props.classNames.rootCompact
      : props.classNames.root,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <header className={headerClass}>
      {props.layout === "brand" ? <BrandLayout {...props} /> : null}
      {props.layout === "titleRow" ? <TitleRowLayout {...props} /> : null}
      {props.layout === "stack" ? <StackLayout {...props} /> : null}
    </header>
  );
}

export type DashboardPageHeaderProps = Omit<PageHeaderProps, "classNames" | "labels" | "layout">;

export function createDashboardPageHeader(config: {
  layout: PageHeaderLayout;
  classNames: PageHeaderClassNames;
  labels: PageHeaderLabels;
}) {
  return function DashboardPageHeader(props: DashboardPageHeaderProps) {
    return (
      <PageHeader
        layout={config.layout}
        classNames={config.classNames}
        labels={config.labels}
        {...props}
      />
    );
  };
}
