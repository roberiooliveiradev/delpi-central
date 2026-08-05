// portal/src/ui-kit/breadcrumb/Breadcrumb.tsx

import type { HTMLAttributes } from "react";
import "./Breadcrumb.css";

export type BreadcrumbItem = {
  label: string;
  onClick?: () => void;
};

export type BreadcrumbProps = HTMLAttributes<HTMLElement> & {
  items: BreadcrumbItem[];
};

export function Breadcrumb({ items, className, ...rest }: BreadcrumbProps) {
  const classes = ["portal-ui-breadcrumb", className ?? ""]
    .filter(Boolean)
    .join(" ");

  return (
    <nav aria-label="Breadcrumb" {...rest}>
      <ol className={classes}>
        {items.map((item, index) => {
          const isLast = index === items.length - 1;
          return (
            <li key={`${item.label}-${index}`} className="portal-ui-breadcrumb__item">
              {index > 0 ? (
                <span className="portal-ui-breadcrumb__sep" aria-hidden="true">
                  /
                </span>
              ) : null}
              {isLast || !item.onClick ? (
                <span
                  className={
                    isLast
                      ? "portal-ui-breadcrumb__current"
                      : "portal-ui-breadcrumb__link"
                  }
                  aria-current={isLast ? "page" : undefined}
                >
                  {item.label}
                </span>
              ) : (
                <button
                  type="button"
                  className="portal-ui-breadcrumb__link"
                  onClick={item.onClick}
                >
                  {item.label}
                </button>
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
