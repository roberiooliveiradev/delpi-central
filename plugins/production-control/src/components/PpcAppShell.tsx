import type { CSSProperties, ReactNode } from "react";

import pcpFactoryBackgroundUrl from "../assets/background/background_pcp_fabrica_desfocada_4k.webp";
import { PpcRail } from "./PpcRail";
import type { PpcBranch, Subplugin } from "../types";

type PpcAppShellProps = {
  items: Subplugin[];
  activeId: string;
  branch: PpcBranch;
  children: ReactNode;
};

export function PpcAppShell({ items, activeId, branch, children }: PpcAppShellProps) {
  const sceneStyle = {
    ["--ppc-workspace-scene-image" as string]: `url(${JSON.stringify(pcpFactoryBackgroundUrl)})`,
  } as CSSProperties;

  return (
    <div className="dashboard-production-control dashboard-page">
      <div className="ppc-app-shell">
        <PpcRail items={items} activeId={activeId} branch={branch} />
        <div className="ppc-workspace ppc-workspace--scene" style={sceneStyle}>
          {children}
        </div>
      </div>
    </div>
  );
}
