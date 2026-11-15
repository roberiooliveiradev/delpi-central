import { useEffect, useMemo, useState, type ReactNode } from "react";
import {
  AlertCircle,
  AlertTriangle,
  FileText,
  GitCompare,
  Link2Off,
  Wallet,
} from "lucide-react";

import {
  downloadEntryAuditExport,
  getEntryAuditAnalysis,
  getEntryAuditBreakdowns,
  getEntryAuditDaily,
  getEntryAuditSummary,
  listEntryAuditOptions,
  listEntryAuditRows,
  listEntryAuditTes,
  setEntryAuditOccurrenceStatus,
  type EntryAuditAnalysis,
  type EntryAuditBreakdowns,
  type EntryAuditDaily,
  type EntryAuditDocument,
  type EntryAuditFilters,
  type EntryAuditOccurrence,
  type EntryAuditOption,
  type EntryAuditPage,
  type EntryAuditSummary,
  type EntryAuditTes,
} from "../../api/entryAuditApi";
import {
  CfActionButton,
  CfComparativeAreaChart,
  CfDistributionDonut,
  CfHorizontalValueBars,
  CfLoadingCard,
  CfMetricKpiCard,
  CfMetricStrip,
  CfPageHero,
  CfPagePath,
  CfResolutionStatusCell,
  CfScopeChipBar,
  CfSectionCard,
  CfSemicircleProgressGauge,
  CfStateBanner,
  CfStatusBadge,
  CfTitleWithHelp,
  CfTrendDelta,
  CfUnderlineNav,
} from "../../app/controllershipFinanceUi";
import {
  DataTableSection,
  renderCfRecordCard,
  type DataTableColumn,
} from "../../app/cfDataTableUi";
import { navigatePluginPath } from "../../app/pluginNavigation";
import { CF_HELP } from "../../content/helpTooltips";
import { EntryAuditLoadingState } from "./EntryAuditLoadingState";
import { EntryAuditSeverityBadge } from "./EntryAuditSeverityBadge";
import {
  ENTRY_AUDIT_ACTION_ICONS,
  ENTRY_AUDIT_TABS,
  auditStatusBadgeVariant,
  alignEntryAuditDailySeries,
  conformityRatio,
  displayValue,
  entryAuditClaraSuggestions,
  entryAuditDailyPointAriaLabel,
  entryAuditPreviousPeriodLabel,
  entryAuditTabResource,
  type EntryAuditDailyChartPoint,
  formatEntryAuditChartDay,
  formatAuditStatus,
  entryAuditFieldLabel,
  formatBranchLabel,
  formatDifference,
  formatOccurrenceValue,
  formatDocumentType,
  formatMoneyBRL,
  formatNoteSeries,
  formatPeriodLabel,
  formatTheme,
  entryAuditDetailFiltersFromSearch,
  entryAuditDetailFiltersKey,
  parseEntryAuditTab,
  severityBadgeVariant,
  severityToUrl,
  type EntryAuditTab,
} from "./entryAuditPresentation";
import { buildEntryAuditGenericColumns } from "./entryAuditTableColumns";

const kpiIcon = (node: ReactNode) => node;

function currentSearch(): URLSearchParams {
  return new URLSearchParams(
    typeof window === "undefined" ? "" : window.location.search,
  );
}

function trendPct(current: number, previous: number): number | null {
  if (previous === 0) return current === 0 ? 0 : null;
  return ((current - previous) / previous) * 100;
}

function severityTone(
  name: string,
): "danger" | "warning" | "neutral" | "info" | "success" | undefined {
  const variant = severityBadgeVariant(name);
  return variant === "neutral" ? "neutral" : variant;
}

export function EntryAuditAnalysisPage({
  basePath,
  analysisId,
}: {
  basePath: string;
  analysisId: string;
}) {
  const [routeEpoch, setRouteEpoch] = useState(0);
  const [analysis, setAnalysis] = useState<EntryAuditAnalysis | null>(null);
  const [summary, setSummary] = useState<EntryAuditSummary | null>(null);
  const [breakdowns, setBreakdowns] = useState<EntryAuditBreakdowns | null>(
    null,
  );
  const [daily, setDaily] = useState<EntryAuditDaily | null>(null);
  const [branchOptions, setBranchOptions] = useState<EntryAuditOption[]>([]);
  const [rows, setRows] = useState<
    Array<EntryAuditOccurrence | EntryAuditDocument | EntryAuditTes>
  >([]);
  const [page, setPage] = useState<EntryAuditPage<unknown> | null>(null);
  const [rowsLoading, setRowsLoading] = useState(false);
  const [summaryRefreshing, setSummaryRefreshing] = useState(false);
  const [error, setError] = useState("");
  const [refresh, setRefresh] = useState(0);
  const [exporting, setExporting] = useState(false);
  const [copiedHint, setCopiedHint] = useState("");
  const [tabTotals, setTabTotals] = useState<Partial<Record<EntryAuditTab, number>>>(
    {},
  );
  const params = useMemo(() => currentSearch(), [routeEpoch]);
  const tab = parseEntryAuditTab(params.get("tab"));
  const detailFiltersKey = useMemo(
    () => entryAuditDetailFiltersKey(params),
    [routeEpoch],
  );
  const filters = useMemo(
    () => entryAuditDetailFiltersFromSearch(params),
    [detailFiltersKey],
  );
  const tablePage = Math.max(1, Number(params.get("page") || "1") || 1);
  const tablePageSize = Math.min(
    200,
    Math.max(10, Number(params.get("page_size") || "50") || 50),
  );
  const tableSort = (params.get("sort") || "").trim();
  const tableOrder = (params.get("order") || "asc").toLowerCase() === "desc" ? "desc" : "asc";

  useEffect(() => {
    const sync = () => setRouteEpoch((value) => value + 1);
    window.addEventListener("popstate", sync);
    return () => window.removeEventListener("popstate", sync);
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    void listEntryAuditOptions(controller.signal)
      .then((options) => {
        if (!controller.signal.aborted) setBranchOptions(options.branches);
      })
      .catch(() => undefined);
    return () => controller.abort();
  }, []);

  /** Só troca de análise zera o quadro; filtro de detalhe mantém hero/KPIs (stale-while-revalidate). */
  useEffect(() => {
    setAnalysis(null);
    setSummary(null);
    setBreakdowns(null);
    setDaily(null);
    setRows([]);
    setPage(null);
    setTabTotals({});
  }, [analysisId]);

  useEffect(() => {
    const controller = new AbortController();
    setError("");
    void getEntryAuditAnalysis(analysisId, controller.signal)
      .then((payload) => {
        if (!controller.signal.aborted) setAnalysis(payload);
      })
      .catch((reason: unknown) => {
        if (!controller.signal.aborted) {
          setError(
            reason instanceof Error ? reason.message : "Falha ao carregar análise.",
          );
        }
      });
    return () => controller.abort();
  }, [analysisId, refresh]);

  /** R1 — summary primeiro (KPIs); não depende de tab/page/sort. */
  useEffect(() => {
    const controller = new AbortController();
    setSummaryRefreshing(true);
    void getEntryAuditSummary(analysisId, filters, controller.signal)
      .then((payload) => {
        if (!controller.signal.aborted) setSummary(payload);
      })
      .catch((reason: unknown) => {
        if (!controller.signal.aborted) {
          setError(
            reason instanceof Error ? reason.message : "Falha ao carregar resumo.",
          );
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setSummaryRefreshing(false);
      });
    return () => controller.abort();
  }, [analysisId, detailFiltersKey, refresh, filters]);

  useEffect(() => {
    if (!analysis || !summary) return;
    const controller = new AbortController();
    void getEntryAuditBreakdowns(analysisId, filters, controller.signal)
      .then((payload) => {
        if (!controller.signal.aborted) setBreakdowns(payload);
      })
      .catch(() => {
        if (!controller.signal.aborted) setBreakdowns(null);
      });
    return () => controller.abort();
  }, [analysisId, analysis, summary, detailFiltersKey, refresh, filters]);

  useEffect(() => {
    if (!analysis || !summary) return;
    const multiDay = analysis.date_from !== analysis.date_to;
    if (!multiDay) {
      setDaily(null);
      return;
    }
    const controller = new AbortController();
    void getEntryAuditDaily(analysisId, filters, controller.signal)
      .then((payload) => {
        if (!controller.signal.aborted) setDaily(payload);
      })
      .catch(() => {
        if (!controller.signal.aborted) setDaily(null);
      });
    return () => controller.abort();
  }, [analysisId, analysis, summary, detailFiltersKey, refresh, filters]);

  useEffect(() => {
    if (!summary) return;
    const controller = new AbortController();
    setRowsLoading(true);
    const resource = entryAuditTabResource(tab);
    const tabFilters: EntryAuditFilters =
      tab === "posted_outside"
        ? { ...filters, situation: "posted_outside_period" }
        : filters;

    const sortArg = tableSort || undefined;
    const orderArg = tableSort ? (tableOrder as "asc" | "desc") : undefined;
    const request =
      resource === "tes"
        ? listEntryAuditTes(
            analysisId,
            tabFilters,
            controller.signal,
            sortArg,
            orderArg,
          ).then((payload) => ({
            items: payload.items,
            page: 1,
            page_size: payload.items.length || 1,
            total: payload.items.length,
          }))
        : listEntryAuditRows<EntryAuditOccurrence | EntryAuditDocument>(
            analysisId,
            resource,
            tabFilters,
            tablePage,
            tablePageSize,
            controller.signal,
            sortArg,
            orderArg,
          );
    request
      .then((payload) => {
        if (controller.signal.aborted) return;
        setRows(payload.items);
        setPage(payload);
        setTabTotals((prev) => ({
          ...prev,
          [tab]: payload.total,
        }));
      })
      .catch((reason: unknown) => {
        if (!controller.signal.aborted) {
          setError(
            reason instanceof Error
              ? reason.message
              : "Falha ao carregar registros.",
          );
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setRowsLoading(false);
      });
    return () => controller.abort();
  }, [
    analysisId,
    tab,
    filters,
    refresh,
    summary,
    tablePage,
    tablePageSize,
    tableSort,
    tableOrder,
  ]);

  const navigateWith = (changes: Record<string, string>) => {
    const next = currentSearch();
    const touchesPagingOnly =
      Object.keys(changes).length > 0 &&
      Object.keys(changes).every(
        (key) => key === "page" || key === "page_size" || key === "sort" || key === "order",
      );
    Object.entries(changes).forEach(([key, value]) => {
      if (value) next.set(key, value);
      else next.delete(key);
    });
    if (!touchesPagingOnly && !("page" in changes)) {
      next.delete("page");
    }
    const query = next.toString();
    navigatePluginPath(
      `${basePath}/entry-audit/analyses/${encodeURIComponent(analysisId)}${query ? `?${query}` : ""}`,
      { replace: true },
    );
    setRouteEpoch((value) => value + 1);
  };

  const openOccurrence = (row: EntryAuditOccurrence) => {
    const query = currentSearch().toString();
    navigatePluginPath(
      `${basePath}/entry-audit/analyses/${encodeURIComponent(analysisId)}/occurrences/${encodeURIComponent(row.stable_key)}${query ? `?${query}` : ""}`,
    );
  };

  const goHome = () => navigatePluginPath(basePath);
  const goEntry = () => navigatePluginPath(`${basePath}/entry-audit`);

  const occurrenceColumns: DataTableColumn<EntryAuditOccurrence>[] = [
    {
      key: "severity",
      header: "Severidade",
      sortable: true,
      render: (row) => <EntryAuditSeverityBadge severity={row.severity} />,
    },
    {
      key: "document",
      header: "Nota/Série",
      sortable: true,
      render: (row) => formatNoteSeries(row.document_number, row.series),
    },
    {
      key: "supplier",
      header: "Fornecedor",
      sortable: true,
      render: (row) => displayValue(row.supplier_name),
    },
    {
      key: "rule",
      header: "Regra",
      sortable: true,
      render: (row) => displayValue(row.rule_name ?? row.title),
    },
    {
      key: "field",
      header: "Campo",
      sortable: true,
      render: (row) => entryAuditFieldLabel(row),
    },
    {
      key: "protheus",
      header: "Protheus",
      sortable: true,
      render: (row) => formatOccurrenceValue(row.protheus_value, row),
    },
    {
      key: "xml",
      header: "XML",
      sortable: true,
      render: (row) => formatOccurrenceValue(row.xml_value, row),
    },
    {
      key: "difference",
      header: "Diferença",
      sortable: true,
      render: (row) => formatDifference(row.difference, row.field),
      align: "right",
    },
    {
      key: "status",
      header: "Status",
      sortable: true,
      render: (row) => (
        <CfResolutionStatusCell
          status={row.status === "resolved" ? "resolved" : "open"}
          onResolve={
            row.status === "resolved"
              ? undefined
              : async () => {
                  await setEntryAuditOccurrenceStatus(row.stable_key, "resolve");
                  setRefresh((value) => value + 1);
                }
          }
          onReopen={
            row.status === "resolved"
              ? async () => {
                  await setEntryAuditOccurrenceStatus(row.stable_key, "reopen");
                  setRefresh((value) => value + 1);
                }
              : undefined
          }
        />
      ),
    },
  ];

  const genericColumns = useMemo(
    () => buildEntryAuditGenericColumns(tab, branchOptions),
    [tab, branchOptions],
  );

  const exportFile = async () => {
    setExporting(true);
    try {
      const blob = await downloadEntryAuditExport(analysisId);
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = `auditoria-entradas-${analysisId}.xlsx`;
      anchor.click();
      URL.revokeObjectURL(url);
    } finally {
      setExporting(false);
    }
  };

  const dailyChart = useMemo(() => {
    if (!daily?.series?.length) return { points: [], includePrevious: false };
    const includePrevious =
      summary?.previous != null && Boolean(daily.previous?.length);
    return {
      points: alignEntryAuditDailySeries(
        daily.series,
        includePrevious ? daily.previous : [],
      ),
      includePrevious,
    };
  }, [daily, summary?.previous]);

  const dailySelectedName = useMemo(() => {
    if (!filters.day) return null;
    const match = dailyChart.points.find((point) => point.day === filters.day);
    return match?.name ?? formatEntryAuditChartDay(filters.day);
  }, [dailyChart.points, filters.day]);

  const previousPeriodLegend = useMemo(
    () =>
      analysis
        ? entryAuditPreviousPeriodLabel(analysis.date_from, analysis.date_to)
        : null,
    [analysis],
  );

  if (error && !analysis && !summary) {
    return (
      <section className="cf-page-stack">
        <CfStateBanner variant="error">
          {error}
          <CfActionButton variant="ghost" onClick={() => setRefresh((v) => v + 1)}>
            Tentar de novo
          </CfActionButton>
        </CfStateBanner>
      </section>
    );
  }

  if (!analysis || !summary) {
    return (
      <EntryAuditLoadingState
        back={{ label: "Início", href: basePath, onNavigate: goHome }}
        pathItems={[
          {
            id: "entry",
            label: "Auditoria de Entradas",
            href: `${basePath}/entry-audit`,
            onNavigate: goEntry,
          },
        ]}
        current="Análise"
        title="Resultado da análise"
        hint={CF_HELP.entryAudit.analysis}
      />
    );
  }

  const periodLabel = formatPeriodLabel(
    analysis.date_from,
    analysis.date_to,
  );
  const claraSuggestions = entryAuditClaraSuggestions(
    analysis.date_from,
    analysis.date_to,
  );
  const cleanShare = conformityRatio(
    summary.conformity.clean,
    summary.conformity.divergent,
  );
  const { kpis, previous } = summary;
  const hasPrevious = previous != null;
  const multiDay = analysis.date_from !== analysis.date_to;
  const noPreviousHint = "Sem análise do período anterior para comparar";

  const chips = [
    ...(filters.severity
      ? [
          {
            id: "severity",
            label: `Severidade: ${filters.severity}`,
            active: true,
            onSelect: () => navigateWith({ severity: "" }),
          },
        ]
      : []),
    ...(filters.theme
      ? [
          {
            id: "theme",
            label: `Tema: ${formatTheme(filters.theme)}`,
            active: true,
            onSelect: () => navigateWith({ theme: "" }),
          },
        ]
      : []),
    ...(filters.supplier
      ? [
          {
            id: "supplier",
            label: `Fornecedor: ${filters.supplier}`,
            active: true,
            onSelect: () => navigateWith({ supplier: "" }),
          },
        ]
      : []),
    ...(filters.tes
      ? [
          {
            id: "tes",
            label: `TES: ${filters.tes}`,
            active: true,
            onSelect: () => navigateWith({ tes: "" }),
          },
        ]
      : []),
    ...(filters.day
      ? [
          {
            id: "day",
            label: `Dia: ${formatEntryAuditChartDay(filters.day)}`,
            active: true,
            onSelect: () => navigateWith({ day: "" }),
          },
        ]
      : []),
    ...(filters.situation
      ? [
          {
            id: "situation",
            label: `Situação: ${filters.situation}`,
            active: true,
            onSelect: () => navigateWith({ situation: "" }),
          },
        ]
      : []),
  ];

  const summaryTabCounts: Partial<Record<EntryAuditTab, number>> = {
    occurrences: kpis.occurrences,
    documents: kpis.documents,
    unmatched: summary.conformity.unmatched_open,
    posted_outside: summary.conformity.posted_outside_period.count,
  };

  const navItems = ENTRY_AUDIT_TABS.map((item) => {
    const count = tabTotals[item.value] ?? summaryTabCounts[item.value];
    const label =
      typeof count === "number"
        ? `${item.label} (${count.toLocaleString("pt-BR")})`
        : item.label;
    return {
      id: item.value,
      label,
      controlId: `entry-audit-tabpanel-${item.value}`,
      tabId: `entry-audit-tab-${item.value}`,
      onSelect: () =>
        navigateWith({
          tab: item.value,
          sort: "",
          order: "",
          page: "1",
        }),
    };
  });

  const copySuggestion = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedHint("Copiado");
      window.setTimeout(() => setCopiedHint(""), 2000);
    } catch {
      setCopiedHint("Não foi possível copiar");
      window.setTimeout(() => setCopiedHint(""), 2000);
    }
  };

  const metaParts = [
    analysis.branches
      .map((code) => formatBranchLabel(code, branchOptions))
      .join(" · "),
    analysis.document_types.map(formatDocumentType).join(" · "),
  ].filter(Boolean);

  return (
    <section
      className="cf-page-stack"
      aria-label="Resultado da auditoria de entradas"
    >
      <CfPagePath
        ariaLabel="Caminho da página"
        size="sm"
        back={{
          label: "Início",
          href: basePath,
          onNavigate: (event: { preventDefault: () => void }) => {
            event.preventDefault();
            goHome();
          },
        }}
        items={[
          {
            id: "notas",
            label: "Notas fiscais",
            href: basePath,
            onNavigate: (event: { preventDefault: () => void }) => {
              event.preventDefault();
              goHome();
            },
          },
          {
            id: "entry",
            label: "Auditoria de Entradas",
            href: `${basePath}/entry-audit`,
            onNavigate: (event: { preventDefault: () => void }) => {
              event.preventDefault();
              goEntry();
            },
          },
        ]}
        current={`Análise ${periodLabel}`}
      />

      <CfPageHero
        eyebrow="Notas fiscais"
        title={
          <CfTitleWithHelp
            title={`Análise de ${periodLabel}`}
            hint={CF_HELP.entryAudit.analysis}
          />
        }
        description={metaParts.join(" · ")}
        badge={
          <CfStatusBadge
            label={formatAuditStatus(analysis.status)}
            variant={auditStatusBadgeVariant(analysis.status)}
          />
        }
        actions={
          <>
            <CfActionButton
              variant="primary"
              onClick={exportFile}
              disabled={exporting}
              softDisabled
              title={CF_HELP.entryAudit.export}
            >
              <span className="cf-action-with-icon">
                {ENTRY_AUDIT_ACTION_ICONS.download}
                {exporting ? "Exportando…" : "Exportar"}
              </span>
            </CfActionButton>
            <CfActionButton
              variant="default"
              onClick={goEntry}
              title={CF_HELP.entryAudit.rerun}
            >
              <span className="cf-action-with-icon">
                {ENTRY_AUDIT_ACTION_ICONS.refresh}
                Executar de novo
              </span>
            </CfActionButton>
            <CfActionButton
              variant="ghost"
              onClick={goEntry}
              title={CF_HELP.entryAudit.newAnalysis}
            >
              <span className="cf-action-with-icon">
                {ENTRY_AUDIT_ACTION_ICONS.plus}
                Nova análise
              </span>
            </CfActionButton>
          </>
        }
      />

      {error ? (
        <CfStateBanner variant="error">
          {error}
          <CfActionButton variant="ghost" onClick={() => setRefresh((v) => v + 1)}>
            Tentar de novo
          </CfActionButton>
        </CfStateBanner>
      ) : null}
      {summary.branches_unavailable?.length ? (
        <CfStateBanner variant="default">
          Dados indisponíveis para:{" "}
          {summary.branches_unavailable
            .map((code) => formatBranchLabel(code, branchOptions))
            .join(", ")}
          .
        </CfStateBanner>
      ) : null}

      <div
        className="cf-kpi-grid"
        role="group"
        aria-label="Indicadores da auditoria"
        aria-busy={summaryRefreshing ? true : undefined}
      >
        <CfMetricKpiCard
          label="Notas conferidas"
          titleHint={
            hasPrevious
              ? CF_HELP.entryAudit.kpiDocuments
              : `${CF_HELP.entryAudit.kpiDocuments} ${noPreviousHint}.`
          }
          value={String(kpis.documents)}
          icon={kpiIcon(<FileText size={22} strokeWidth={1.75} aria-hidden />)}
          hint={
            hasPrevious ? (
              <CfTrendDelta
                value={trendPct(kpis.documents, previous.documents)}
              />
            ) : (
              noPreviousHint
            )
          }
        />
        <CfMetricKpiCard
          label="Valor conferido"
          titleHint={
            hasPrevious
              ? CF_HELP.entryAudit.kpiGross
              : `${CF_HELP.entryAudit.kpiGross} ${noPreviousHint}.`
          }
          value={formatMoneyBRL(kpis.gross_checked)}
          icon={kpiIcon(<Wallet size={22} strokeWidth={1.75} aria-hidden />)}
          hint={
            hasPrevious ? (
              <CfTrendDelta
                value={trendPct(kpis.gross_checked, previous.gross_checked)}
              />
            ) : (
              noPreviousHint
            )
          }
        />
        <CfMetricKpiCard
          label="Ocorrências pendentes"
          titleHint={CF_HELP.entryAudit.kpiPending}
          value={String(kpis.pending)}
          hint={`${kpis.resolved} resolvidas`}
          icon={kpiIcon(
            <AlertTriangle size={22} strokeWidth={1.75} aria-hidden />,
          )}
          tone={kpis.pending ? "warning" : "default"}
        />
        <CfMetricKpiCard
          label="Alta"
          titleHint={CF_HELP.entryAudit.kpiHigh}
          value={String(kpis.high)}
          icon={kpiIcon(
            <AlertCircle size={22} strokeWidth={1.75} aria-hidden />,
          )}
          tone={kpis.high ? "negative" : "default"}
          onSelect={() =>
            navigateWith({
              severity: filters.severity === "Alta" ? "" : severityToUrl("Alta"),
              tab: "occurrences",
              sort: "",
              order: "",
              page: "1",
            })
          }
          hint={
            hasPrevious ? (
              <CfTrendDelta value={trendPct(kpis.high, previous.high)} />
            ) : (
              noPreviousHint
            )
          }
        />
        <CfMetricKpiCard
          label="Diferença nas Altas"
          titleHint={CF_HELP.entryAudit.kpiHighDiff}
          value={formatMoneyBRL(kpis.high_difference)}
          icon={kpiIcon(
            <GitCompare size={22} strokeWidth={1.75} aria-hidden />,
          )}
          tone={kpis.high_difference ? "negative" : "default"}
        />
        <CfMetricKpiCard
          label="Sem par em aberto"
          titleHint={CF_HELP.entryAudit.kpiUnmatched}
          value={String(summary.conformity.unmatched_open)}
          icon={kpiIcon(<Link2Off size={22} strokeWidth={1.75} aria-hidden />)}
          onSelect={() =>
            navigateWith({
              tab: "unmatched",
              sort: "",
              order: "",
              page: "1",
            })
          }
        />
      </div>

      <div className="cf-analysis-charts">
        <div className="cf-analysis-panorama-row">
          <CfSectionCard title="Panorama" hint={CF_HELP.entryAudit.panorama}>
            <div className="cf-analysis-panorama">
              <div className="cf-analysis-panorama__conformity">
                <CfTitleWithHelp
                  title="Conformidade"
                  hint={CF_HELP.entryAudit.conformity}
                />
                <CfSemicircleProgressGauge
                  value={cleanShare}
                  centerLabel="Notas limpas"
                  aria-label="Percentual de notas limpas"
                  legend={[
                    {
                      id: "clean",
                      label: "Limpas",
                      count: summary.conformity.clean,
                      tone: "success",
                    },
                    {
                      id: "divergent",
                      label: "Divergentes",
                      count: summary.conformity.divergent,
                      tone: "danger",
                    },
                  ]}
                />
                <CfMetricStrip
                  aria-label="Resumo de conformidade"
                  items={[
                    {
                      id: "unmatched-open",
                      label: "Sem par em aberto",
                      value: summary.conformity.unmatched_open,
                    },
                    {
                      id: "explained",
                      label: "Explicadas",
                      value: summary.conformity.unmatched_explained,
                    },
                  ]}
                />
              </div>
              {breakdowns ? (
                <div className="cf-analysis-panorama__severity">
                  <CfTitleWithHelp
                    title="Severidade"
                    hint={CF_HELP.entryAudit.severity}
                  />
                  <CfDistributionDonut
                    ariaLabel="Distribuição por severidade"
                    legendPlacement="below"
                    items={breakdowns.by_severity.map((item) => ({
                      id: item.name,
                      label: item.name,
                      value: item.count,
                      tone: severityTone(item.name),
                    }))}
                    onSelect={(item) => {
                      if (!item) {
                        navigateWith({ severity: "" });
                        return;
                      }
                      navigateWith({ severity: severityToUrl(item.id) });
                    }}
                    selectedId={filters.severity || undefined}
                  />
                </div>
              ) : (
                <CfLoadingCard title="Carregando severidade…" />
              )}
            </div>
          </CfSectionCard>

          {dailyChart.points.length > 1 ? (
            <CfSectionCard
              title="Evolução por dia"
              hint={CF_HELP.entryAudit.dailyEvolution}
            >
              <CfComparativeAreaChart
                data={dailyChart.points}
                height={280}
                series={
                  dailyChart.includePrevious
                    ? [
                        {
                          dataKey: "current",
                          name: "Este período",
                          color: "var(--delpi-ui-accent, #2563eb)",
                        },
                        {
                          dataKey: "previous",
                          name: previousPeriodLegend
                            ? `Período anterior (${previousPeriodLegend})`
                            : "Período anterior",
                          color: "var(--delpi-ui-muted, #94a3b8)",
                        },
                      ]
                    : [
                        {
                          dataKey: "current",
                          name: "Este período",
                          color: "var(--delpi-ui-accent, #2563eb)",
                        },
                      ]
                }
                valueFormatter={(value) => value.toLocaleString("pt-BR")}
                onPointSelect={(point) => {
                  const day =
                    typeof point.day === "string" && point.day
                      ? point.day
                      : "";
                  if (!day) return;
                  navigateWith({
                    day: filters.day === day ? "" : day,
                  });
                }}
                pointAriaLabel={(point) =>
                  entryAuditDailyPointAriaLabel(
                    point as EntryAuditDailyChartPoint,
                    dailyChart.includePrevious,
                  )
                }
                selectedName={dailySelectedName}
              />
            </CfSectionCard>
          ) : multiDay && !daily ? (
            <CfLoadingCard title="Carregando evolução diária…" />
          ) : null}
        </div>

        {breakdowns ? (
          <CfSectionCard
            title="Onde estão as ocorrências"
            hint={CF_HELP.entryAudit.occurrencesWhere}
          >
            <div className="cf-analysis-breakdowns">
              <div className="cf-analysis-breakdowns__column">
                <CfTitleWithHelp
                  title="Por tema"
                  hint={CF_HELP.entryAudit.occurrences}
                />
                <CfHorizontalValueBars
                  layout="stacked"
                  aria-label="Ocorrências por tema"
                  items={breakdowns.by_theme.map((item) => ({
                    id: item.name,
                    label: formatTheme(item.name),
                    value: item.count,
                  }))}
                  onItemClick={(item) =>
                    navigateWith({
                      theme: filters.theme === item.id ? "" : item.id,
                    })
                  }
                  selectedId={filters.theme || undefined}
                />
              </div>
              <div className="cf-analysis-breakdowns__column">
                <p className="cf-analysis-breakdowns__heading">
                  Por fornecedor (top 8)
                </p>
                <CfHorizontalValueBars
                  layout="stacked"
                  aria-label="Ocorrências por fornecedor"
                  items={breakdowns.suppliers.slice(0, 8).map((item) => ({
                    id: item.name,
                    label: item.name,
                    value: item.count,
                  }))}
                  onItemClick={(item) =>
                    navigateWith({
                      supplier: filters.supplier === item.id ? "" : item.id,
                    })
                  }
                  selectedId={filters.supplier || undefined}
                />
              </div>
              <div className="cf-analysis-breakdowns__column">
                <p className="cf-analysis-breakdowns__heading">Por TES (top 8)</p>
                <CfHorizontalValueBars
                  layout="stacked"
                  aria-label="Ocorrências por TES"
                  items={breakdowns.tes.slice(0, 8).map((item) => ({
                    id: item.name,
                    label: item.label
                      ? `${item.name} · ${item.label}`
                      : item.name,
                    value: item.count,
                  }))}
                  onItemClick={(item) =>
                    navigateWith({
                      tes: filters.tes === item.id ? "" : item.id,
                    })
                  }
                  selectedId={filters.tes || undefined}
                />
              </div>
            </div>
          </CfSectionCard>
        ) : (
          <CfLoadingCard title="Carregando distribuição das ocorrências…" />
        )}
      </div>

      {summary.conformity.posted_outside_period.count > 0 ? (
        <p className="cf-analysis-posted-outside-note">
          <CfTitleWithHelp
            title={`Lançadas fora do período: ${summary.conformity.posted_outside_period.count.toLocaleString("pt-BR")}`}
            hint={CF_HELP.entryAudit.postedOutside}
          />
        </p>
      ) : null}

      {chips.length ? (
        <CfScopeChipBar
          label="Filtros aplicados"
          chips={chips}
          aria-label="Filtros de detalhamento da auditoria"
          clearAllLabel="Limpar filtros"
          onClearAll={() =>
            navigateWith({
              severity: "",
              theme: "",
              supplier: "",
              tes: "",
              day: "",
              situation: "",
            })
          }
        />
      ) : null}

      <CfUnderlineNav
        mode="tabs"
        items={navItems}
        activeId={tab}
        aria-label="Visões da auditoria"
      />

      {rowsLoading && !rows.length ? (
        <CfLoadingCard title="Carregando registros da aba…" />
      ) : tab === "occurrences" ? (
        <DataTableSection<EntryAuditOccurrence>
          title={`Ocorrências (${page?.total ?? 0})`}
          titleHint={CF_HELP.entryAudit.occurrences}
          columns={occurrenceColumns}
          rows={rows as EntryAuditOccurrence[]}
          rowKey={(row) => row.stable_key}
          onRowClick={openOccurrence}
          loading={rowsLoading}
          hidePaginationWhenSinglePage
          columnPreferencesKey="controllership-finance:entry-audit:occurrences:columns:v1"
          fontSizePreferencesKey="controllership-finance:entry-audit:occurrences:font:v1"
          viewLayoutPreferencesKey="controllership-finance:entry-audit:occurrences:layout:v1"
          renderCard={(row) =>
            renderCfRecordCard(occurrenceColumns, row, {
              onActivate: openOccurrence,
              ariaLabel: `Ocorrência ${row.document_number ?? ""}`,
              skipKeys: ["status"],
            })
          }
          serverPagination={{
            page: page?.page ?? tablePage,
            pageSize: page?.page_size ?? tablePageSize,
            total: page?.total ?? 0,
            onPageChange: (nextPage) =>
              navigateWith({ page: String(nextPage) }),
            onPageSizeChange: (size) =>
              navigateWith({ page_size: String(size), page: "1" }),
          }}
          serverSort={{
            sortKey: tableSort || "severity",
            sortDirection: tableOrder,
            onSortChange: (key) => {
              const nextOrder =
                tableSort === key && tableOrder === "asc" ? "desc" : "asc";
              navigateWith({ sort: key, order: nextOrder, page: "1" });
            },
          }}
        />
      ) : (
        <DataTableSection<EntryAuditDocument | EntryAuditTes>
          title={`${ENTRY_AUDIT_TABS.find((item) => item.value === tab)?.label} (${page?.total ?? rows.length})`}
          columns={genericColumns}
          rows={rows as Array<EntryAuditDocument | EntryAuditTes>}
          rowKey={(row) =>
            String(
              ("stable_key" in row && row.stable_key) ||
                ("access_key" in row && row.access_key) ||
                ("tes" in row && row.tes) ||
                JSON.stringify(row),
            )
          }
          loading={rowsLoading}
          hidePaginationWhenSinglePage
          columnPreferencesKey={`controllership-finance:entry-audit:${tab}:columns:v1`}
          fontSizePreferencesKey={`controllership-finance:entry-audit:${tab}:font:v1`}
          viewLayoutPreferencesKey={`controllership-finance:entry-audit:${tab}:layout:v1`}
          renderCard={(row) =>
            renderCfRecordCard(genericColumns, row, {
              ariaLabel: "Registro da auditoria",
            })
          }
          serverPagination={
            entryAuditTabResource(tab) === "tes"
              ? undefined
              : {
                  page: page?.page ?? tablePage,
                  pageSize: page?.page_size ?? tablePageSize,
                  total: page?.total ?? 0,
                  onPageChange: (nextPage) =>
                    navigateWith({ page: String(nextPage) }),
                  onPageSizeChange: (size) =>
                    navigateWith({ page_size: String(size), page: "1" }),
                }
          }
          serverSort={{
            sortKey:
              tableSort ||
              (tab === "tes"
                ? "tes_code"
                : tab === "cte"
                  ? "document_number"
                  : "received_date"),
            sortDirection: tableOrder,
            onSortChange: (key) => {
              const nextOrder =
                tableSort === key && tableOrder === "asc" ? "desc" : "asc";
              navigateWith({ sort: key, order: nextOrder, page: "1" });
            },
          }}
        />
      )}

      <CfSectionCard
        title="Pergunte à CLARA"
        subtitle="A CLARA lê esta mesma análise"
        hint={CF_HELP.entryAudit.clara}
      >
        <div
          className="cf-analysis-clara-actions"
          role="group"
          aria-label="Sugestões para o chat"
        >
          {claraSuggestions.map((suggestion) => (
            <CfActionButton
              key={suggestion}
              type="button"
              variant="ghost"
              onClick={() => copySuggestion(suggestion)}
            >
              {suggestion}
            </CfActionButton>
          ))}
        </div>
        <p aria-live="polite">{copiedHint}</p>
      </CfSectionCard>
    </section>
  );
}
