import type { ReactNode } from "react";

type FormActionsProps = {
  children: ReactNode;
  align?: "start" | "end";
};

export function FormActions({ children, align = "start" }: FormActionsProps) {
  return (
    <div className={`pac-form-actions pac-form-actions--${align}`}>{children}</div>
  );
}
