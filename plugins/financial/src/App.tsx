import { useEffect } from "react";

import { configureHttpClient } from "./api/httpClient";
import { FinAppShell } from "./components/FinAppShell";
import { copy } from "./content/copy";
import { DEFAULT_SUBPLUGIN } from "./constants/routes";
import { useFinancialRouterPath } from "./hooks/useFinancialRouterPath";
import { useSubplugins } from "./hooks/useSubplugins";
import { BillingPage } from "./pages/BillingPage";
import { CostCenterMonthPage } from "./pages/CostCenterMonthPage";
import { CostCentersPage } from "./pages/CostCentersPage";
import { DelinquencyPage } from "./pages/DelinquencyPage";
import { FreightPage } from "./pages/FreightPage";
import { IndicatorsPage } from "./pages/IndicatorsPage";
import { OverviewPage } from "./pages/OverviewPage";
import {
  buildFinancialHref,
  navigateFinancial,
  parseFinancialPath,
  readStoredBranch,
  storeBranch,
} from "./utils/routeParser";

/** Subplugins com página própria — os demais voltam para a gestão à vista. */
const WORKSPACES = new Set([
  DEFAULT_SUBPLUGIN,
  "billing",
  "delinquency",
  "cost-centers",
  "freight",
  "indicators",
]);

export type AppProps = {
  getAccessToken?: () => string | undefined;
  pathname?: string;
};

export default function App({ getAccessToken, pathname: pathnameFromHost }: AppProps) {
  configureHttpClient(() => getAccessToken?.());
  const { pathname, search } = useFinancialRouterPath(pathnameFromHost);
  const storedBranch = readStoredBranch();
  const route = parseFinancialPath(pathname, search, storedBranch);
  const { items, error } = useSubplugins();

  useEffect(() => {
    storeBranch(route.branch);
  }, [route.branch]);

  useEffect(() => {
    if (WORKSPACES.has(route.subpluginId)) return;
    const known = items.find((item) => item.id === route.subpluginId);
    if (!known || known.status === "coming_soon") {
      navigateFinancial(
        buildFinancialHref({ subpluginId: DEFAULT_SUBPLUGIN, branch: route.branch }),
      );
    }
  }, [items, route.branch, route.subpluginId]);

  let workspace = (
    <OverviewPage
      branch={route.branch}
      startDate={route.startDate}
      endDate={route.endDate}
    />
  );
  if (route.subpluginId === "billing") {
    workspace = (
      <BillingPage
        branch={route.branch}
        startDate={route.startDate}
        endDate={route.endDate}
        granularity={route.granularity}
      />
    );
  } else if (route.subpluginId === "delinquency") {
    workspace = (
      <DelinquencyPage
        branch={route.branch}
        startDate={route.startDate}
        endDate={route.endDate}
        clientKey={route.clientKey}
        customerCode={route.customerCode}
        customerStore={route.customerStore}
        status={route.status}
        delayRange={route.delayRange}
        page={route.page}
      />
    );
  } else if (route.subpluginId === "cost-centers" && route.month) {
    workspace = (
      <CostCenterMonthPage
        branch={route.branch}
        month={route.month}
        costCenter={route.costCenter}
        supplierCode={route.supplierCode}
        supplierStore={route.supplierStore}
        excludeMp={route.excludeMp}
        search={route.search}
        page={route.page}
      />
    );
  } else if (route.subpluginId === "cost-centers") {
    workspace = (
      <CostCentersPage
        branch={route.branch}
        startDate={route.startDate}
        endDate={route.endDate}
        search={route.search}
        costCenter={route.costCenter}
        supplierCode={route.supplierCode}
        supplierStore={route.supplierStore}
        excludeMp={route.excludeMp}
        page={route.page}
      />
    );
  } else if (route.subpluginId === "freight") {
    workspace = (
      <FreightPage
        branch={route.branch}
        issueStart={route.issueStart}
        issueEnd={route.issueEnd}
        entryStart={route.entryStart}
        entryEnd={route.entryEnd}
        supplierCode={route.supplierCode}
        invoiceDocument={route.invoiceDocument}
        freightDocument={route.freightDocument}
        situation={route.situation}
        page={route.page}
      />
    );
  } else if (route.subpluginId === "indicators") {
    workspace = <IndicatorsPage branch={route.branch} />;
  }

  return (
    <FinAppShell
      items={items}
      activeId={route.subpluginId || DEFAULT_SUBPLUGIN}
      branch={route.branch}
    >
      {error ? (
        <div className="fin-state fin-state--error" role="alert">
          {error}
        </div>
      ) : (
        workspace
      )}
      <span className="fin-sr-only">{copy.productName}</span>
    </FinAppShell>
  );
}
