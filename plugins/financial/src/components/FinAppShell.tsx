import type { ReactNode } from "react";

import { FinRail } from "./FinRail";
import type { FinancialBranch, Subplugin } from "../types";

type FinAppShellProps = {
  items: Subplugin[];
  activeId: string;
  branch: FinancialBranch;
  children: ReactNode;
};

export function FinAppShell({ items, activeId, branch, children }: FinAppShellProps) {
  return (
    <div className="dashboard-financial dashboard-page">
      <div className="fin-app-shell">
        <FinRail items={items} activeId={activeId} branch={branch} />
        <div className="fin-workspace">{children}</div>
      </div>
    </div>
  );
}
