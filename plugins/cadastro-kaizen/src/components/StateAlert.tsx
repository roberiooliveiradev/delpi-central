import type { ReactNode } from "react";

type StateAlertProps = {
  children: ReactNode;
  variant?: "error" | "success";
};

export function StateAlert({ children, variant }: StateAlertProps) {
  const className =
    variant === "error"
      ? "kz-state kz-state--error"
      : variant === "success"
        ? "kz-state kz-state--success"
        : "kz-state";

  return <div className={className}>{children}</div>;
}
