import type { ReactNode } from "react";

type StateAlertProps = {
  children: ReactNode;
  variant?: "error" | "success";
};

export function StateAlert({ children, variant }: StateAlertProps) {
  const className =
    variant === "error"
      ? "pac-state pac-state--error"
      : variant === "success"
        ? "pac-state pac-state--success"
        : "pac-state";

  return <div className={className}>{children}</div>;
}
