// portal/src/ui-kit/tabs/Tabs.tsx

import type { HTMLAttributes, ReactNode } from "react";
import { Badge } from "../badge/Badge";
import "./Tabs.css";

export type TabItem = {
  id: string;
  label: string;
  icon?: ReactNode;
  errorCount?: number;
  disabled?: boolean;
  /** Alvo do tour guiado do portal (`data-tour`). */
  dataTour?: string;
};

export type TabsProps = Omit<HTMLAttributes<HTMLDivElement>, "onChange"> & {
  items: TabItem[];
  value: string;
  onChange: (id: string) => void;
};

export function Tabs({
  items,
  value,
  onChange,
  className,
  ...rest
}: TabsProps) {
  const classes = ["portal-ui-tabs", className ?? ""].filter(Boolean).join(" ");

  return (
    <div className={classes} role="tablist" {...rest}>
      {items.map((item) => {
        const active = item.id === value;
        const tabClass = [
          "portal-ui-tabs__tab",
          active ? "portal-ui-tabs__tab--active" : "",
        ]
          .filter(Boolean)
          .join(" ");

        return (
          <button
            key={item.id}
            type="button"
            role="tab"
            id={`portal-ui-tab-${item.id}`}
            aria-selected={active}
            disabled={item.disabled}
            className={tabClass}
            data-tour={item.dataTour}
            onClick={() => onChange(item.id)}
          >
            {item.icon ? (
              <span className="portal-ui-tabs__icon" aria-hidden="true">
                {item.icon}
              </span>
            ) : null}
            <span className="portal-ui-tabs__label">{item.label}</span>
            {item.errorCount != null && item.errorCount > 0 ? (
              <Badge tone="danger" count aria-label={`${item.errorCount} erros`}>
                {item.errorCount}
              </Badge>
            ) : null}
          </button>
        );
      })}
    </div>
  );
}
