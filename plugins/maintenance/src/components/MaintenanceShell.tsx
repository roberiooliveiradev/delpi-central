import type { ReactNode } from "react";

type MaintenanceShellProps = {
  children: ReactNode;
};

export function MaintenanceShell({ children }: MaintenanceShellProps) {
  return <div className="dashboard-maintenance dashboard-page dm-app-shell">{children}</div>;
}
