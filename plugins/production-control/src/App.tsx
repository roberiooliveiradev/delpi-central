import { useEffect } from "react";

import { configureHttpClient } from "./api/httpClient";
import { PpcAppShell } from "./components/PpcAppShell";
import { PpcConfirmDialogProvider } from "./components/PpcConfirmDialogProvider";
import { copy } from "./content/copy";
import { DEFAULT_SUBPLUGIN } from "./constants/routes";
import { usePpcRouterPath } from "./hooks/usePpcRouterPath";
import { useSubplugins } from "./hooks/useSubplugins";
import { DemandPage } from "./pages/DemandPage";
import { MachineLoadPage } from "./pages/MachineLoadPage";
import { OverviewPage } from "./pages/OverviewPage";
import { ProblemAnalysisPage } from "./pages/ProblemAnalysisPage";
import {
  buildPpcHref,
  navigatePpc,
  parsePpcPath,
  readStoredBranch,
  storeBranch,
} from "./utils/routeParser";

/** Subplugins com página própria — os demais caem no fallback de «em breve». */
const WORKSPACES = new Set([DEFAULT_SUBPLUGIN, "demand", "problem-analysis", "machine-load"]);

export type AppProps = {
  getAccessToken?: () => string | undefined;
  pathname?: string;
};

export default function App({ getAccessToken, pathname: pathnameFromHost }: AppProps) {
  configureHttpClient(() => getAccessToken?.());
  const { pathname, search } = usePpcRouterPath(pathnameFromHost);
  const storedBranch = readStoredBranch();
  const route = parsePpcPath(pathname, search, storedBranch);
  const { items, error } = useSubplugins();

  useEffect(() => {
    storeBranch(route.branch);
  }, [route.branch]);

  useEffect(() => {
    if (WORKSPACES.has(route.subpluginId)) return;
    const known = items.find((item) => item.id === route.subpluginId);
    if (known?.status === "coming_soon") {
      navigatePpc(buildPpcHref({ subpluginId: DEFAULT_SUBPLUGIN, branch: route.branch }));
    }
  }, [items, route.branch, route.subpluginId]);

  let workspace = <OverviewPage branch={route.branch} />;
  if (route.subpluginId === "demand") {
    workspace = (
      <DemandPage
        branch={route.branch}
        search={route.demandSearch}
        status={route.demandStatus}
      />
    );
  } else if (route.subpluginId === "problem-analysis") {
    workspace = <ProblemAnalysisPage branch={route.branch} detectorId={route.detectorId} />;
  } else if (route.subpluginId === "machine-load") {
    workspace = (
      <MachineLoadPage
        branch={route.branch}
        workCenter={route.workCenter}
        startDate={route.startDate}
        endDate={route.endDate}
        locateQuery={route.locateQuery}
      />
    );
  }

  return (
    <PpcConfirmDialogProvider>
      <PpcAppShell items={items} activeId={route.subpluginId || DEFAULT_SUBPLUGIN} branch={route.branch}>
        {error ? (
          <div className="ppc-state ppc-state--error" role="alert">
            {error}
          </div>
        ) : (
          workspace
        )}
        <span className="ppc-sr-only">{copy.productName}</span>
      </PpcAppShell>
    </PpcConfirmDialogProvider>
  );
}
