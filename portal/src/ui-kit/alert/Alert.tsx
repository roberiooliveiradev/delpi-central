// portal/src/ui-kit/alert/Alert.tsx

import type { HTMLAttributes, ReactNode } from "react";
import "./Alert.css";

export type AlertTone = "info" | "success" | "warning" | "danger";

export type AlertProps = HTMLAttributes<HTMLDivElement> & {
  tone?: AlertTone;
  title?: string;
  children?: ReactNode;
};

export function Alert({
  tone = "info",
  title,
  className,
  children,
  role = "status",
  ...rest
}: AlertProps) {
  const classes = [
    "portal-ui-alert",
    `portal-ui-alert--${tone}`,
    className ?? "",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div
      className={classes}
      role={tone === "danger" || tone === "warning" ? "alert" : role}
      {...rest}
    >
      {title ? <p className="portal-ui-alert__title">{title}</p> : null}
      {children != null ? (
        <div className="portal-ui-alert__body">{children}</div>
      ) : null}
    </div>
  );
}
