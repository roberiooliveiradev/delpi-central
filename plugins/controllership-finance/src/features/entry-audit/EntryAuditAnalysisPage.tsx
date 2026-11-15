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
import { DataTableSection, type DataTableColumn } from "../../app/cfDataTableUi";
import { navigatePluginPath } from "../../app/pluginNavigation";
import { CF_HELP } from "../../content/helpTooltips";
import { EntryAuditLoadingState } from "./EntryAuditLoadingState";
import { EntryAuditSeverityBadge } from "./EntryAuditSeverityBadge";
import {
  ENTRY_AUDIT_ACTION_ICONS,
  ENTRY_AUDIT_TABS,
  auditStatusBadgeVariant,
  conformityRatio,
  displayValue,
  entryAuditClaraSuggestions,
  entryAuditTabResource,
  formatAuditStatus,
  formatBranchLabel,
  formatDifference,
  formatDocumentType,
  formatMoneyBRL,
  formatNoteSeries,
  formatPeriodLabel,
  formatTheme,
  parseEntryAuditTab,
  severityBadgeVariant,
  severityFromUrl,
  severityToUrl,
  type EntryAuditTab,
} from "./entryAuditPresentation";

const kpiIcon = (node: ReactNode) => node;

function currentSearch(): URLSearchParams {
  return new URLSearchParams(
    typeof window === "undefined" ? "" : window.location.search,
  );
}

function filtersFromUrl(params: URLSearchParams): EntryAuditFilters {
  return {
    branch: params.get("branch") ?? "",
    severity: severityFromUrl(params.get("severity")),
    theme: params.get("theme") ?? "",
    supplier: params.get("supplier") ?? "",
    tes: params.get("tes") ?? "",
    document_type: params.get("document_type") ?? "",
    status: params.get("status") ?? "",
    situation: params.get("situation") ?? "",
    q: params.get("q") ?? "",
    day: params.get("day") ?? "",
  };
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
  const [error, setError] = useState("");
  const [refresh, setRefresh] = useState(0);
  const [exporting, setExporting] = useState(false);
  const [copiedHint, setCopiedHint] = useState("");
  const params = useMemo(() => currentSearch(), [routeEpoch]);
  const tab = parseEntryAuditTab(params.get("tab"));
  const filters = useMemo(() => filtersFromUrl(params), [params]);
  const tablePage = Math.max(1, Number(params.get("page") || "1") || 1);
  const tablePageSize = Math.min(
    200,
    Math.max(10, Number(params.get("page_size") || "50") || 50),
  );

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

  /** R1 — análise + summary primeiro (KPIs); não esperar breakdowns/rows. */
  useEffect(() => {
    const controller = new AbortController();
    setError("");
    setSummary(null);
    setBreakdowns(null);
    setDaily(null);
    setRows([]);
    setPage(null);
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
      });
    return () => controller.abort();
  }, [analysisId, filters, refresh]);

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
  }, [analysisId, analysis, summary, filters, refresh]);

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
  }, [analysisId, analysis, summary, filters, refresh]);

  useEffect(() => {
    if (!summary) return;
    const controller = new AbortController();
    setRowsLoading(true);
    const resource = entryAuditTabResource(tab);
    const tabFilters: EntryAuditFilters =
      tab === "posted_outside"
        ? { ...filters, situation: "posted_outside_period" }
        : filters;

    const request =
      resource === "tes"
        ? listEntryAuditTes(analysisId, tabFilters, controller.signal).then(
            (payload) => ({
              items: payload.items,
              page: 1,
              page_size: payload.items.length || 1,
              total: payload.items.length,
            }),
          )
        : listEntryAuditRows<EntryAuditOccurrence | EntryAuditDocument>(
            analysisId,
            resource,
            tabFilters,
            tablePage,
            tablePageSize,
            controller.signal,
          );
    request
      .then((payload) => {
        if (controller.signal.aborted) return;
        setRows(payload.items);
        setPage(payload);
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
  ]);

  const navigateWith = (changes: Record<string, string>) => {
    const next = currentSearch();
    const touchesPagingOnly =
      Object.keys(changes).length > 0 &&
      Object.keys(changes).every((key) => key === "page" || key === "page_size");
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
      render: (row) => <EntryAuditSeverityBadge severity={row.severity} />,
    },
    {
      key: "document",
      header: "Nota/Série",
      render: (row) => formatNoteSeries(row.document_number, row.series),
    },
    {
      key: "supplier",
      header: "Fornecedor",
      render: (row) => displayValue(row.supplier_name),
    },
    {
      key: "rule",
      header: "Regra",
      render: (row) => displayValue(row.rule_name ?? row.title),
    },
    {
      key: "field",
      header: "Campo",
      render: (row) => displayValue(row.field_label ?? row.field),
    },
    {
      key: "protheus",
      header: "Protheus",
      render: (row) => displayValue(row.protheus_value),
    },
    {
      key: "xml",
      header: "XML",
      render: (row) => displayValue(row.xml_value),
    },
    {
      key: "difference",
      header: "Diferença",
      render: (row) => formatDifference(row.difference, row.field),
      align: "right",
    },
    {
      key: "status",
      header: "Status",
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

  const genericColumns: DataTableColumn<EntryAuditDocument | EntryAuditTes>[] = [
    {
      key: "branch",
      header: "Filial",
      render: (row) =>
        formatBranchLabel(String(row.branch ?? ""), branchOptions),
    },
    {
      key: "document",
      header: tab === "tes" ? "TES" : "Documento",
      render: (row) =>
        displayValue(
          "document_number" in row ? row.document_number : row.tes ?? row.code,
        ),
    },
    {
      key: "description",
      header: tab === "tes" ? "Descrição" : "Fornecedor",
      render: (row) =>
        displayValue(
          "supplier_name" in row ? row.supplier_name : row.description,
        ),
    },
    {
      key: "situation",
      header: "Situação",
      render: (row) =>
        displayValue("situation" in row ? row.situation : "Utilizada"),
    },
  ];

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

  const dailyPoints = useMemo(() => {
    if (!daily?.series?.length) return [];
    const byName = new Map<
      string,
      { name: string; current: number; previous: number }
    >();
    daily.series.forEach((item) => {
      byName.set(item.name, {
        name: item.name,
        current: item.count,
        previous: 0,
      });
    });
    daily.previous.forEach((item) => {
      const existing = byName.get(item.name);
      if (existing) existing.previous = item.count;
      else
        byName.set(item.name, {
          name: item.name,
          current: 0,
          previous: item.count,
        });
    });
    return [...byName.values()].sort((a, b) => a.name.localeCompare(b.name));
  }, [daily]);

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
    ...analysis.branches.map((branch) => ({
      id: `branch-${branch}`,
      label: formatBranchLabel(branch, branchOptions),
      active: filters.branch === branch,
      onSelect: () =>
        navigateWith({ branch: filters.branch === branch ? "" : branch }),
    })),
    ...analysis.document_types.map((type) => ({
      id: `type-${type}`,
      label: formatDocumentType(type),
      active: filters.document_type === type,
      onSelect: () =>
        navigateWith({
          document_type: filters.document_type === type ? "" : type,
        }),
    })),
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
            label: `Dia: ${filters.day}`,
            active: true,
            onSelect: () => navigateWith({ day: "" }),
          },
        ]
      : []),
  ];

  const tabCounts: Partial<Record<EntryAuditTab, number>> = {
    occurrences: kpis.occurrences,
    unmatched: summary.conformity.unmatched_open,
    posted_outside: summary.conformity.posted_outside_period.count,
  };

  const navItems = ENTRY_AUDIT_TABS.map((item) => {
    const count =
      item.value === tab && page ? page.total : tabCounts[item.value];
    return {
      id: item.value,
      label: item.label,
      count: typeof count === "number" ? count : undefined,
      onSelect: () => navigateWith({ tab: item.value }),
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
              variant="default"
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

      <div className="cf-kpi-grid" role="group" aria-label="Indicadores da auditoria">
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
          onSelect={() => navigateWith({ tab: "unmatched" })}
        />
      </div>

      <div className="cf-charts-grid">
        <CfSectionCard title="Conformidade" hint={CF_HELP.entryAudit.conformity}>
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
              {
                id: "posted-outside",
                label: "Lançadas fora do período",
                value: summary.conformity.posted_outside_period.count,
                tone: "neutral",
              },
            ]}
          />
        </CfSectionCard>

        {breakdowns ? (
          <>
            <CfSectionCard title="Severidade" hint={CF_HELP.entryAudit.severity}>
              <CfDistributionDonut
                ariaLabel="Distribuição por severidade"
                items={breakdowns.by_severity.map((item) => ({
                  id: item.name,
                  label: item.name,
                  value: item.count,
                  tone: severityTone(item.name),
                }))}
                onSelect={(item) => {
                  if (item) navigateWith({ severity: severityToUrl(item.id) });
                }}
                selectedId={filters.severity || undefined}
              />
            </CfSectionCard>

            <CfSectionCard title="Por tema" hint={CF_HELP.entryAudit.occurrences}>
              <CfHorizontalValueBars
                aria-label="Ocorrências por tema"
                items={breakdowns.by_theme.map((item) => ({
                  id: item.name,
                  label: formatTheme(item.name),
                  value: item.count,
                }))}
                onItemClick={(item) => navigateWith({ theme: item.id })}
                selectedId={filters.theme || undefined}
              />
            </CfSectionCard>

            <CfSectionCard title="Por fornecedor">
              <CfHorizontalValueBars
                aria-label="Ocorrências por fornecedor"
                items={breakdowns.suppliers.slice(0, 10).map((item) => ({
                  id: item.name,
                  label: item.name,
                  value: item.count,
                }))}
                onItemClick={(item) => navigateWith({ supplier: item.id })}
                selectedId={filters.supplier || undefined}
              />
            </CfSectionCard>

            <CfSectionCard title="Por TES">
              <CfHorizontalValueBars
                aria-label="Ocorrências por TES"
                items={breakdowns.tes.slice(0, 10).map((item) => ({
                  id: item.name,
                  label: item.name,
                  value: item.count,
                }))}
                onItemClick={(item) => navigateWith({ tes: item.id })}
                selectedId={filters.tes || undefined}
              />
            </CfSectionCard>
          </>
        ) : (
          <>
            <CfLoadingCard title="Carregando severidade…" />
            <CfLoadingCard title="Carregando temas…" />
            <CfLoadingCard title="Carregando fornecedores…" />
            <CfLoadingCard title="Carregando TES…" />
          </>
        )}

        {dailyPoints.length > 1 ? (
          <CfSectionCard title="Evolução por dia">
            <CfComparativeAreaChart
              data={dailyPoints}
              series={[
                {
                  dataKey: "current",
                  name: "Período",
                  color: "var(--delpi-ui-accent, #2563eb)",
                },
                {
                  dataKey: "previous",
                  name: "Anterior",
                  color: "var(--delpi-ui-muted, #94a3b8)",
                },
              ]}
              valueFormatter={(value) => value.toLocaleString("pt-BR")}
              onPointSelect={(point) =>
                navigateWith({ day: String(point.name) })
              }
              selectedName={filters.day || null}
            />
          </CfSectionCard>
        ) : multiDay && !daily ? (
          <CfLoadingCard title="Carregando evolução diária…" />
        ) : null}
      </div>

      <CfScopeChipBar
        label="Escopo"
        chips={chips}
        aria-label="Filtros de escopo da auditoria"
        emptyHint="Sem filtros de escopo."
        onClearAll={() =>
          navigateWith({
            branch: "",
            document_type: "",
            severity: "",
            theme: "",
            supplier: "",
            tes: "",
            day: "",
            status: "",
            situation: "",
          })
        }
      />

      <CfUnderlineNav
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
          hidePaginationWhenSinglePage
          serverPagination={{
            page: page?.page ?? tablePage,
            pageSize: page?.page_size ?? tablePageSize,
            total: page?.total ?? 0,
            onPageChange: (nextPage) =>
              navigateWith({ page: String(nextPage) }),
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
          hidePaginationWhenSinglePage
          serverPagination={
            entryAuditTabResource(tab) === "tes"
              ? undefined
              : {
                  page: page?.page ?? tablePage,
                  pageSize: page?.page_size ?? tablePageSize,
                  total: page?.total ?? 0,
                  onPageChange: (nextPage) =>
                    navigateWith({ page: String(nextPage) }),
                }
          }
        />
      )}

      <CfSectionCard
        title="Pergunte à CLARA"
        subtitle="A CLARA lê esta mesma análise"
        hint={CF_HELP.entryAudit.clara}
      >
        <ul className="cf-page-stack">
          {claraSuggestions.map((suggestion) => (
            <li key={suggestion}>
              <CfActionButton
                type="button"
                variant="ghost"
                onClick={() => copySuggestion(suggestion)}
              >
                {suggestion}
              </CfActionButton>
            </li>
          ))}
        </ul>
        <p aria-live="polite">{copiedHint}</p>
      </CfSectionCard>
    </section>
  );
}
