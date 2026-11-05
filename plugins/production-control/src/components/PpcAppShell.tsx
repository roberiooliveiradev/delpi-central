import type { ReactNode } from "react";

import { PpcRail } from "./PpcRail";
import type { PpcBranch, Subplugin } from "../types";

type PpcAppShellProps = {
  items: Subplugin[];
  activeId: string;
  branch: PpcBranch;
  children: ReactNode;
};

export function PpcAppShell({ items, activeId, branch, children }: PpcAppShellProps) {
  return (
    <div className="dashboard-production-control dashboard-page">
      <div className="ppc-app-shell">
        <PpcRail items={items} activeId={activeId} branch={branch} />
        <div className="ppc-workspace">{children}</div>
      </div>
    </div>
  );
}
