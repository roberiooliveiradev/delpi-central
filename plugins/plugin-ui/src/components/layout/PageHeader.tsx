import type { ReactNode } from "react";
import { RefreshCw } from "lucide-react";

import { delpiUiClass } from "../../utils/delpiUiClass";

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
  nav?: string;
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

function pair(local: string, canonical: string): string {
  return delpiUiClass(local, canonical);
}

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
          {nav && classNames.nav ? <div className={classNames.nav}>{nav}</div> : nav}
          <h1>{title}</h1>
          {subtitle && classNames.subtitle ? (
            <span className={classNames.subtitle}>{subtitle}</span>
          ) : null}
        </div>
      </div>
      {mergedActions}
    </>
  );
}

function TitleRowLayout(props: PageHeaderProps) {
  const { classNames, title, subtitle, icon, nav, actions, onRefresh, refreshing, labels } = props;

  return (
    <>
      <div className={classNames.titleWrap ?? classNames.content}>
        {nav && classNames.nav ? <div className={classNames.nav}>{nav}</div> : nav}
        <div className={classNames.titleRow}>
          {icon && classNames.icon ? (
            <span className={classNames.icon} aria-hidden={true}>
              {icon}
            </span>
          ) : null}
          <div>
            <h1 className={classNames.title}>{title}</h1>
            {subtitle ? (
              classNames.description || classNames.subtitle ? (
                <p className={classNames.description ?? classNames.subtitle}>{subtitle}</p>
              ) : (
                <p>{subtitle}</p>
              )
            ) : null}
          </div>
        </div>
      </div>
      {actions || onRefresh ? (
        <div className={classNames.actions}>
          {actions}
          <RefreshButton
            onRefresh={onRefresh}
            refreshing={refreshing}
            classNames={classNames}
            labels={labels}
          />
        </div>
      ) : null}
    </>
  );
}

function StackLayout(props: PageHeaderProps) {
  const { classNames, title, subtitle, eyebrow, badge, nav, actions } = props;

  return (
    <>
      <div className={classNames.content}>
        {nav && classNames.nav ? <div className={classNames.nav}>{nav}</div> : nav}
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
  const root = `${prefix}-page-header`;
  const ui = "delpi-ui-page-header";
  return {
    root: pair(root, ui),
    rootCompact: pair(`${root} ${root}--compact`, `${ui} ${ui}--compact`),
    brand: pair(`${root}__brand`, `${ui}__brand`),
    icon: pair(`${prefix}-header__icon`, `${ui}__icon`),
    content: pair(`${root}__content`, `${ui}__content`),
    eyebrow: pair(`${prefix}-eyebrow`, `${ui}__eyebrow`),
    subtitle: pair(`${prefix}-page-subtitle`, `${ui}__subtitle`),
    nav: pair(`${root}__nav`, `${ui}__nav`),
    actions: pair(`${prefix}-header-actions`, `${ui}__actions`),
    primaryButton: `${prefix}-primary-btn`,
  };
}

export function pageHeaderPacBrandBemClasses(prefix: string): PageHeaderClassNames {
  const root = `${prefix}-page-header`;
  const ui = "delpi-ui-page-header";
  return {
    root: pair(root, ui),
    brand: pair(`${root}__brand`, `${ui}__brand`),
    icon: pair(`${prefix}-header__icon`, `${ui}__icon`),
    content: pair(`${root}__content`, `${ui}__content`),
    eyebrow: pair(`${prefix}-eyebrow`, `${ui}__eyebrow`),
    subtitle: pair(`${prefix}-page-subtitle`, `${ui}__subtitle`),
    nav: pair(`${root}__nav`, `${ui}__nav`),
    actions: pair(`${prefix}-header-actions`, `${ui}__actions`),
  };
}

export function pageHeaderTitleRowBemClasses(
  prefix: string,
  options?: { buttonClass?: string; spinClass?: string },
): PageHeaderClassNames {
  const root = `${prefix}-page-header`;
  const ui = "delpi-ui-page-header";
  const button = options?.buttonClass ?? `${prefix}-btn ${prefix}-btn--primary`;
  return {
    root: pair(root, ui),
    titleWrap: pair(`${root}__title-wrap`, `${ui}__title-wrap`),
    titleRow: pair(`${root}__title-row`, `${ui}__title-row`),
    title: pair(`${root}__title`, `${ui}__title`),
    description: pair(`${root}__description`, `${ui}__description`),
    icon: pair(`${root}__icon`, `${ui}__icon`),
    nav: pair(`${root}__nav`, `${ui}__nav`),
    actions: pair(`${root}__actions`, `${ui}__actions`),
    primaryButton: button,
    spinClass: options?.spinClass ?? `${prefix}-spin`,
  };
}

export function pageHeaderStackBemClasses(prefix: string): PageHeaderClassNames {
  const root = `${prefix}-page-header`;
  const ui = "delpi-ui-page-header";
  return {
    root: pair(root, ui),
    content: pair(`${root}__content`, `${ui}__content`),
    eyebrow: pair(`${root}__eyebrow`, `${ui}__eyebrow`),
    titleRow: pair(`${root}__title-row`, `${ui}__title-row`),
    title: pair(`${root}__title`, `${ui}__title`),
    badge: pair(`${root}__badge`, `${ui}__badge`),
    description: pair(`${root}__description`, `${ui}__description`),
    nav: pair(`${root}__nav`, `${ui}__nav`),
    actions: pair(`${root}__actions`, `${ui}__actions`),
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
