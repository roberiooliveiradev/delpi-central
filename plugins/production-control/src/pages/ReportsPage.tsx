import {
  NavigationCard,
  createDashboardLoadingActivityCard,
  navigationCardBemClasses,
} from "@delpi/plugin-ui/index";
import { ArrowLeft, FileSpreadsheet, Package, Warehouse } from "lucide-react";
import type { ReactNode } from "react";
import { useCallback, useState } from "react";

import { PpcWorkspaceHeader } from "../components/PpcWorkspaceHeader";
import { StockBalancesReportPanel } from "../components/StockBalancesReportPanel";
import { copy } from "../content/copy";
import { helpTooltips } from "../content/helpTooltips";
import { useReportsCatalog } from "../hooks/useReportsCatalog";
import type { PpcBranch, ReportsCatalogItem } from "../types";
import { buildPpcHref, navigatePpc } from "../utils/routeParser";

const navCardClassNames = navigationCardBemClasses("ppc");

const KNOWN_REPORTS = new Set(["stock-balances"]);

const LoadingCard = createDashboardLoadingActivityCard({
  prefix: "ppc",
  labels: {
    progressRemaining: (n) => `Faltam ${n}%`,
    progressAriaDeterminate: (n) => `Faltam ${n} por cento`,
    progressAriaIndeterminate: copy.reports.catalogLoading,
  },
});

function reportIcon(icon: string | null | undefined): ReactNode {
  if (icon === "warehouse") return <Warehouse size={18} strokeWidth={1.75} aria-hidden />;
  if (icon === "package") return <Package size={18} strokeWidth={1.75} aria-hidden />;
  return <FileSpreadsheet size={18} strokeWidth={1.75} aria-hidden />;
}

function reportTitle(reportId: string, cards: ReportsCatalogItem[]): string {
  const fromCatalog = cards.find((item) => item.id === reportId)?.label;
  if (fromCatalog) return fromCatalog;
  if (reportId === "stock-balances") return copy.reports.stockBalances.tab;
  return copy.reports.title;
}

function reportSubtitle(reportId: string, cards: ReportsCatalogItem[]): string {
  const fromCatalog = cards.find((item) => item.id === reportId)?.description;
  if (fromCatalog) return fromCatalog;
  if (reportId === "stock-balances") return copy.reports.stockBalances.tableHint;
  return copy.reports.subtitle;
}

type ReportsPageProps = {
  branch: PpcBranch;
  reportId: string | null;
};

export function ReportsPage({ branch, reportId }: ReportsPageProps) {
  const { data, loading, error, reload: reloadCatalog } = useReportsCatalog(branch);
  const [detailReload, setDetailReload] = useState<(() => void) | null>(null);
  const reports = copy.reports;
  const cards = data?.reports ?? [];
  const activeId = reportId && KNOWN_REPORTS.has(reportId) ? reportId : null;
  const inReport = Boolean(activeId);

  const onRefreshReady = useCallback((reload: () => void) => {
    setDetailReload(() => reload);
  }, []);

  const openReport = (id: string) => {
    navigatePpc(
      buildPpcHref({
        subpluginId: "reports",
        branch,
        reportId: id,
      }),
    );
  };

  const backToCatalog = () => {
    navigatePpc(
      buildPpcHref({
        subpluginId: "reports",
        branch,
      }),
    );
  };

  const handleRefresh = () => {
    if (inReport) {
      detailReload?.();
      return;
    }
    reloadCatalog();
  };

  return (
    <div className="ppc-page-stack ppc-page-stack--reports">
      <PpcWorkspaceHeader
        title={inReport ? reportTitle(activeId!, cards) : reports.title}
        subtitle={inReport ? reportSubtitle(activeId!, cards) : reports.subtitle}
        titleHint={helpTooltips.reports}
        branch={branch}
        subpluginId="reports"
        reportId={activeId}
        onRefresh={handleRefresh}
      />

      {inReport ? (
        <div className="ppc-reports-toolbar">
          <button
            type="button"
            className="ppc-reports-back"
            onClick={backToCatalog}
            aria-label={reports.backAria}
          >
            <ArrowLeft size={15} strokeWidth={1.75} aria-hidden />
            <span>{reports.backLabel}</span>
          </button>
        </div>
      ) : null}

      {!inReport && loading && !data ? (
        <LoadingCard title={reports.catalogLoading} description={reports.catalogLoadingHint} />
      ) : null}

      {!inReport && error ? (
        <div className="ppc-state ppc-state--error" role="alert">
          {error || reports.loadError}
        </div>
      ) : null}

      {!inReport && data ? (
        <section className="ppc-reports-catalog" aria-label={reports.catalogAria}>
          <div className="ppc-reports-catalog__intro">
            <h2 className="ppc-reports-catalog__title">{reports.catalogTitle}</h2>
            <p className="ppc-reports-catalog__lead">{reports.catalogLead}</p>
          </div>

          {cards.length === 0 ? (
            <p className="ppc-state" role="status">
              {reports.catalogEmpty}
            </p>
          ) : (
            <div className="ppc-reports-catalog__grid">
              {cards.map((card) => (
                <ReportCatalogCard key={card.id} item={card} onOpen={() => openReport(card.id)} />
              ))}
            </div>
          )}
        </section>
      ) : null}

      {activeId === "stock-balances" ? (
        <StockBalancesReportPanel branch={branch} onRefreshReady={onRefreshReady} />
      ) : null}
    </div>
  );
}

function ReportCatalogCard({
  item,
  onOpen,
}: {
  item: ReportsCatalogItem;
  onOpen: () => void;
}) {
  const reports = copy.reports;
  return (
    <div className="ppc-report-card" data-report={item.id}>
      <NavigationCard
        classNames={navCardClassNames}
        orientation="horizontal"
        density="default"
        icon={reportIcon(item.icon)}
        eyebrow={item.eyebrow || reports.catalogEyebrowFallback}
        title={item.label}
        description={item.description}
        onClick={onOpen}
      />
    </div>
  );
}
