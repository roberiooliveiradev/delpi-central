// portal/src/ui-kit/layout/PageChrome.tsx

import type { HTMLAttributes, ReactNode } from "react";
import { Breadcrumb, type BreadcrumbItem } from "../breadcrumb/Breadcrumb";
import { Tabs, type TabItem } from "../tabs/Tabs";
import "./PageChrome.css";

export type PageChromeProps = HTMLAttributes<HTMLDivElement> & {
  breadcrumb?: BreadcrumbItem[];
  title: ReactNode;
  subtitle?: ReactNode;
  leading?: ReactNode;
  actions?: ReactNode;
  tabs?: {
    items: TabItem[];
    value: string;
    onChange: (id: string) => void;
  };
  footer?: ReactNode;
  children?: ReactNode;
};

export function PageChrome({
  breadcrumb,
  title,
  subtitle,
  leading,
  actions,
  tabs,
  footer,
  children,
  className,
  ...rest
}: PageChromeProps) {
  const classes = ["portal-ui-page", className ?? ""].filter(Boolean).join(" ");

  return (
    <div className={classes} {...rest}>
      <header className="portal-ui-page__header">
        {breadcrumb && breadcrumb.length > 0 ? (
          <Breadcrumb items={breadcrumb} />
        ) : null}

        <div className="portal-ui-page__title-row">
          <div className="portal-ui-page__identity">
            {leading != null ? (
              <div className="portal-ui-page__leading">{leading}</div>
            ) : null}
            <div className="portal-ui-page__titles">
              <h1 className="portal-ui-page__title">{title}</h1>
              {subtitle != null ? (
                <div className="portal-ui-page__subtitle">{subtitle}</div>
              ) : null}
            </div>
          </div>
          {actions != null ? (
            <div className="portal-ui-page__actions">{actions}</div>
          ) : null}
        </div>

        {tabs ? (
          <div className="portal-ui-page__tabs">
            <Tabs
              items={tabs.items}
              value={tabs.value}
              onChange={tabs.onChange}
            />
          </div>
        ) : null}
      </header>

      <div className="portal-ui-page__body">{children}</div>

      {footer != null ? (
        <footer className="portal-ui-page__footer">{footer}</footer>
      ) : null}
    </div>
  );
}
