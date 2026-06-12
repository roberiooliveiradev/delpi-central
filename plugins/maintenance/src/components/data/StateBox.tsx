import type { ReactNode } from "react";

type StateBoxProps = {
  children: ReactNode;
  variant?: "default" | "error" | "success";
};

export function StateBox({ children, variant = "default" }: StateBoxProps) {
  const className =
    variant === "error"
      ? "dm-state-box dm-state-box--error"
      : variant === "success"
        ? "dm-state-box dm-state-box--success"
        : "dm-state-box";

  return <p className={className}>{children}</p>;
}
