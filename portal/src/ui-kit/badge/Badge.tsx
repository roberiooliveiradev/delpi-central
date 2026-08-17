// portal/src/ui-kit/badge/Badge.tsx

import type { HTMLAttributes, ReactNode } from "react";
import "./Badge.css";

export type BadgeTone =
  | "default"
  | "primary"
  | "success"
  | "warning"
  | "danger"
  | "info";

export type BadgeProps = HTMLAttributes<HTMLSpanElement> & {
  tone?: BadgeTone;
  count?: boolean;
  children?: ReactNode;
};

export function Badge({
  tone = "default",
  count = false,
  className,
  children,
  ...rest
}: BadgeProps) {
  const classes = [
    "portal-ui-badge",
    `portal-ui-badge--${tone}`,
    count ? "portal-ui-badge--count" : "",
    className ?? "",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <span className={classes} {...rest}>
      {children}
    </span>
  );
}
