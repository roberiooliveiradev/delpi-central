import { useEffect, useMemo } from "react";

import { configureHttpClient } from "./api/httpClient";
import { PpcAllowedBranchesProvider } from "./branchAccessContext";
import { PpcAppShell } from "./components/PpcAppShell";
import { PpcConfirmDialogProvider } from "./components/PpcConfirmDialogProvider";
import { copy } from "./content/copy";
import { DEFAULT_SUBPLUGIN, PPC_BASE_PATH } from "./constants/routes";
import { usePpcRouterPath } from "./hooks/usePpcRouterPath";
import { useSubplugins } from "./hooks/useSubplugins";
import { DeliveryMapPage } from "./pages/DeliveryMapPage";
import { DemandPage } from "./pages/DemandPage";
import { LineFeederPage } from "./pages/LineFeederPage";
import { MachineLoadPage } from "./pages/MachineLoadPage";
import { MaterialsPage } from "./pages/MaterialsPage";
import { MyWegNeedsPage } from "./pages/MyWegNeedsPage";
import { OverviewPage } from "./pages/OverviewPage";
import { ProblemAnalysisPage } from "./pages/ProblemAnalysisPage";
import { ProductModelsPage } from "./pages/ProductModelsPage";
import { ReportsPage } from "./pages/ReportsPage";
import { SequencingProfilesPage } from "./pages/SequencingProfilesPage";
import {
  resolveActiveBranch,
  resolveAllowedBranches,
} from "./utils/branchAccess";
import {
  buildPpcHref,
  navigatePpc,
  parsePpcPath,
  readStoredBranch,
  storeBranch,
} from "./utils/routeParser";

/** Subplugins com página própria — os demais caem no fallback de «em breve». */
const WORKSPACES = new Set([
  DEFAULT_SUBPLUGIN,
  "demand",
  "problem-analysis",
  "machine-load",
  "materials",
  "line-feeder",
  "delivery-map",
  "reports",
  "product-models",
  "sequencing-profiles",
  "myweg-needs",
]);

export type AppProps = {
  getAccessToken?: () => string | undefined;
  pathname?: string;
  permissions?: string[];
  isSuperadmin?: boolean;
};

export default function App({
  getAccessToken,
  pathname: pathnameFromHost,
  permissions,
  isSuperadmin = false,
}: AppProps) {
  configureHttpClient(() => getAccessToken?.());
  const { pathname, search } = usePpcRouterPath(pathnameFromHost);
  const storedBranch = readStoredBranch();
  const route = parsePpcPath(pathname, search, storedBranch);
  const { items, error } = useSubplugins();

  const allowedBranches = useMemo(
    () => resolveAllowedBranches(permissions, isSuperadmin),
    [permissions, isSuperadmin],
  );
  const activeBranch = resolveActiveBranch(allowedBranches, route.branch);

  useEffect(() => {
    if (!activeBranch) return;
    storeBranch(activeBranch);
  }, [activeBranch]);

  // Canoniza URL/session quando a filial pedida não está autorizada
  // (ex.: DEFAULT/session em 01 para quem só tem filial 02).
  useEffect(() => {
    if (!activeBranch) return;
    if (!window.location.pathname.startsWith(PPC_BASE_PATH)) return;
    if (route.branch === activeBranch) return;
    navigatePpc(
      buildPpcHref({
        subpluginId: route.subpluginId,
        branch: activeBranch,
        detectorId: route.detectorId,
        workCenter: route.workCenter,
        startDate: route.startDate,
        endDate: route.endDate,
        locateQuery: route.locateQuery,
        demandSearch: route.demandSearch,
        demandStatus: route.demandStatus,
        materialsSearch: route.materialsSearch,
        materialsIssue: route.materialsIssue,
        materialsStatus: route.materialsStatus,
        deliveryMapSearch: route.deliveryMapSearch,
        requestNumber: route.requestNumber,
        requestItem: route.requestItem,
        reportId: route.reportId,
        cutoffDate: route.cutoffDate,
        cutoffTime: route.cutoffTime,
        lineFeederStatus: route.lineFeederStatus,
        planId: route.planId,
        mywegNeedsSearch: route.mywegNeedsSearch,
        mywegNeedsBatchId: route.mywegNeedsBatchId,
        mywegNeedsRemessaFrom: route.mywegNeedsRemessaFrom,
        mywegNeedsRemessaTo: route.mywegNeedsRemessaTo,
        mywegNeedsPage: route.mywegNeedsPage,
        mywegNeedsView: route.mywegNeedsView,
        mywegNeedsAnalysis: route.mywegNeedsAnalysis,
      }),
    );
  }, [activeBranch, route]);

  useEffect(() => {
    if (!activeBranch) return;
    if (WORKSPACES.has(route.subpluginId)) return;
    const known = items.find((item) => item.id === route.subpluginId);
    if (known?.status === "coming_soon") {
      navigatePpc(buildPpcHref({ subpluginId: DEFAULT_SUBPLUGIN, branch: activeBranch }));
    }
  }, [activeBranch, items, route.subpluginId]);

  let workspace = activeBranch ? (
    <OverviewPage branch={activeBranch} startDate={route.startDate} endDate={route.endDate} />
  ) : null;
  if (activeBranch && route.subpluginId === "demand") {
    workspace = (
      <DemandPage
        key={activeBranch}
        branch={activeBranch}
        search={route.demandSearch}
        status={route.demandStatus}
        permissions={permissions}
        isSuperadmin={isSuperadmin}
      />
    );
  } else if (activeBranch && route.subpluginId === "problem-analysis") {
    workspace = <ProblemAnalysisPage branch={activeBranch} detectorId={route.detectorId} />;
  } else if (activeBranch && route.subpluginId === "materials") {
    workspace = (
      <MaterialsPage
        branch={activeBranch}
        search={route.materialsSearch}
        issue={route.materialsIssue}
        status={route.materialsStatus}
        requestNumber={route.requestNumber}
        requestItem={route.requestItem}
      />
    );
  } else if (activeBranch && route.subpluginId === "line-feeder") {
    workspace = (
      <LineFeederPage
        branch={activeBranch}
        cutoffDate={route.cutoffDate}
        cutoffTime={route.cutoffTime}
        workCenter={route.workCenter}
        status={route.lineFeederStatus}
        planId={route.planId}
      />
    );
  } else if (activeBranch && route.subpluginId === "machine-load") {
    workspace = (
      <MachineLoadPage
        branch={activeBranch}
        workCenter={route.workCenter}
        startDate={route.startDate}
        endDate={route.endDate}
        locateQuery={route.locateQuery}
      />
    );
  } else if (activeBranch && route.subpluginId === "delivery-map") {
    workspace = (
      <DeliveryMapPage branch={activeBranch} search={route.deliveryMapSearch} />
    );
  } else if (activeBranch && route.subpluginId === "reports") {
    workspace = <ReportsPage branch={activeBranch} reportId={route.reportId} />;
  } else if (activeBranch && route.subpluginId === "product-models") {
    workspace = <ProductModelsPage branch={activeBranch} />;
  } else if (activeBranch && route.subpluginId === "sequencing-profiles") {
    workspace = (
      <SequencingProfilesPage
        branch={activeBranch}
        permissions={permissions}
        isSuperadmin={isSuperadmin}
      />
    );
  } else if (activeBranch && route.subpluginId === "myweg-needs") {
    workspace = (
      <MyWegNeedsPage
        branch={activeBranch}
        batchId={route.mywegNeedsBatchId}
        search={route.mywegNeedsSearch}
        remessaFrom={route.mywegNeedsRemessaFrom}
        remessaTo={route.mywegNeedsRemessaTo}
        page={route.mywegNeedsPage}
        view={route.mywegNeedsView}
        analysis={route.mywegNeedsAnalysis}
      />
    );
  }

  const shellBranch = activeBranch ?? allowedBranches[0] ?? "01";

  return (
    <PpcAllowedBranchesProvider allowedBranches={allowedBranches}>
      <PpcConfirmDialogProvider>
        <PpcAppShell items={items} activeId={route.subpluginId || DEFAULT_SUBPLUGIN} branch={shellBranch}>
          {error ? (
            <div className="ppc-state ppc-state--error" role="alert">
              {error}
            </div>
          ) : !activeBranch ? (
            <section className="ppc-state ppc-state--error" role="alert">
              <h2>{copy.branch.noAccessTitle}</h2>
              <p>{copy.branch.noAccess}</p>
            </section>
          ) : (
            workspace
          )}
          <span className="ppc-sr-only">{copy.productName}</span>
        </PpcAppShell>
      </PpcConfirmDialogProvider>
    </PpcAllowedBranchesProvider>
  );
}
