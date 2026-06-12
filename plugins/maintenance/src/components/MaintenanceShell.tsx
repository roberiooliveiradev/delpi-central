import type { ReactNode } from "react";

type MaintenanceShellProps = {
  children: ReactNode;
  variant?: "default" | "embed";
};

export function MaintenanceShell({ children, variant = "default" }: MaintenanceShellProps) {
  const className = [
    "dashboard-maintenance",
    "dashboard-page",
    "dm-app-shell",
    variant === "embed" ? "dashboard-page--embed" : "",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div className={className} lang="pt-BR">
      {children}
    </div>
  );
}
