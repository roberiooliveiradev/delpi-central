import { useEffect, useMemo, useState } from "react";

import {
  downloadEntryAuditExport,
  getEntryAuditAnalysis,
  getEntryAuditBreakdowns,
  getEntryAuditSummary,
  listEntryAuditRows,
  listEntryAuditTes,
  setEntryAuditOccurrenceStatus,
  type EntryAuditAnalysis,
  type EntryAuditBreakdowns,
  type EntryAuditDocument,
  type EntryAuditFilters,
  type EntryAuditOccurrence,
  type EntryAuditPage,
  type EntryAuditSummary,
  type EntryAuditTes,
} from "../../api/entryAuditApi";
import {
  CfActionButton,
  CfDistributionDonut,
  CfHorizontalValueBars,
  CfMetricStrip,
  CfPageHero,
  CfResolutionStatusCell,
  CfScopeChipBar,
  CfSectionCard,
  CfSegmentToggle,
  CfSemicircleProgressGauge,
  CfStateBanner,
  CfTitleWithHelp,
} from "../../app/controllershipFinanceUi";
import { DataTableSection, type DataTableColumn } from "../../app/cfDataTableUi";
import { navigatePluginPath } from "../../app/pluginNavigation";
import { CF_HELP } from "../../content/helpTooltips";
import {
  conformityRatio,
  displayValue,
  ENTRY_AUDIT_TABS,
  entryAuditClaraSuggestions,
  formatAuditStatus,
  formatPeriodLabel,
  parseEntryAuditTab,
  severityFromUrl,
  severityToUrl,
  type EntryAuditTab,
} from "./entryAuditPresentation";

type AnalysisData = {
  analysis: EntryAuditAnalysis;
  summary: EntryAuditSummary;
  breakdowns: EntryAuditBreakdowns;
};

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
    q: params.get("q") ?? "",
  };
}

export function EntryAuditAnalysisPage({
  basePath,
  analysisId,
}: {
  basePath: string;
  analysisId: string;
}) {
  const [routeEpoch, setRouteEpoch] = useState(0);
  const [data, setData] = useState<AnalysisData | null>(null);
  const [rows, setRows] = useState<Array<EntryAuditOccurrence | EntryAuditDocument | EntryAuditTes>>([]);
  const [page, setPage] = useState<EntryAuditPage<unknown> | null>(null);
  const [error, setError] = useState("");
  const [refresh, setRefresh] = useState(0);
  const [exporting, setExporting] = useState(false);
  const [copiedHint, setCopiedHint] = useState("");
  const params = useMemo(() => currentSearch(), [routeEpoch]);
  const tab = parseEntryAuditTab(params.get("tab"));
  const filters = useMemo(() => filtersFromUrl(params), [params]);

  useEffect(() => {
    const sync = () => setRouteEpoch((value) => value + 1);
    window.addEventListener("popstate", sync);
    return () => window.removeEventListener("popstate", sync);
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    setError("");
    Promise.all([
      getEntryAuditAnalysis(analysisId, controller.signal),
      getEntryAuditSummary(analysisId, filters, controller.signal),
      getEntryAuditBreakdowns(analysisId, filters, controller.signal),
    ])
      .then(([analysis, summary, breakdowns]) => {
        if (!controller.signal.aborted) setData({ analysis, summary, breakdowns });
      })
      .catch((reason: unknown) => {
        if (!controller.signal.aborted) {
          setError(reason instanceof Error ? reason.message : "Falha ao carregar análise.");
        }
      });
    return () => controller.abort();
  }, [analysisId, filters, refresh]);

  useEffect(() => {
    const controller = new AbortController();
    const request =
      tab === "tes"
        ? listEntryAuditTes(analysisId, filters, controller.signal).then((payload) => ({
            items: payload.items,
            page: 1,
            page_size: payload.items.length || 1,
            total: payload.items.length,
          }))
        : listEntryAuditRows<
            EntryAuditOccurrence | EntryAuditDocument
          >(analysisId, tab, filters, 1, 50, controller.signal);
    request
      .then((payload) => {
        if (controller.signal.aborted) return;
        setRows(payload.items);
        setPage(payload);
      })
      .catch((reason: unknown) => {
        if (!controller.signal.aborted) {
          setError(reason instanceof Error ? reason.message : "Falha ao carregar registros.");
        }
      });
    return () => controller.abort();
  }, [analysisId, tab, filters, refresh]);

  const navigateWith = (changes: Record<string, string>) => {
    const next = currentSearch();
    Object.entries(changes).forEach(([key, value]) => {
      if (value) next.set(key, value);
      else next.delete(key);
    });
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

  const occurrenceColumns: DataTableColumn<EntryAuditOccurrence>[] = [
    { key: "severity", header: "Severidade", render: (row) => displayValue(row.severity) },
    { key: "document", header: "Documento", render: (row) => displayValue(row.document_number) },
    { key: "finding", header: "Ocorrência", render: (row) => displayValue(row.title) },
    { key: "supplier", header: "Fornecedor", render: (row) => displayValue(row.supplier_name) },
    { key: "tes", header: "TES", render: (row) => displayValue(row.tes) },
    {
      key: "difference",
      header: "Diferença",
      render: (row) => displayValue(row.difference),
      align: "right",
    },
    {
      key: "status",
      header: "Tratamento",
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
    { key: "branch", header: "Filial", render: (row) => displayValue(row.branch) },
    {
      key: "document",
      header: tab === "tes" ? "TES" : "Documento",
      render: (row) =>
        displayValue(
          "document_number" in row
            ? row.document_number
            : row.tes ?? row.code,
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

  if (error && !data) return <CfStateBanner variant="error">{error}</CfStateBanner>;
  if (!data) return <p aria-live="polite">Carregando análise…</p>;

  const chips = [
    ...data.analysis.branches.map((branch) => ({
      id: `branch-${branch}`,
      label: `Filial ${branch}`,
      active: filters.branch === branch,
      onSelect: () =>
        navigateWith({ branch: filters.branch === branch ? "" : branch }),
    })),
    ...data.analysis.document_types.map((type) => ({
      id: `type-${type}`,
      label: type.toUpperCase(),
      active: filters.document_type === type,
      onSelect: () =>
        navigateWith({
          document_type: filters.document_type === type ? "" : type,
        }),
    })),
  ];
  const periodLabel = formatPeriodLabel(
    data.analysis.date_from,
    data.analysis.date_to,
  );
  const claraSuggestions = entryAuditClaraSuggestions(
    data.analysis.date_from,
    data.analysis.date_to,
  );
  const cleanShare = conformityRatio(
    data.summary.conformity.clean,
    data.summary.conformity.divergent,
  );
  const money = (value: number) =>
    value.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });

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

  return (
    <section className="cf-page-stack" aria-label="Resultado da auditoria de entradas">
      <CfPageHero
        eyebrow="Auditoria de Entradas"
        title={
          <CfTitleWithHelp
            title="Resultado da análise"
            hint={CF_HELP.entryAudit.analysis}
          />
        }
        description={`${periodLabel} · ${formatAuditStatus(data.analysis.status)}`}
        actions={
          <>
            <CfActionButton onClick={exportFile} disabled={exporting} softDisabled>
              {exporting ? "Exportando…" : "Exportar XLSX"}
            </CfActionButton>
            <CfActionButton onClick={() => navigatePluginPath(`${basePath}/entry-audit`)}>
              Nova análise
            </CfActionButton>
          </>
        }
      />

      {error ? <CfStateBanner variant="error">{error}</CfStateBanner> : null}
      {data.summary.branches_unavailable?.length ? (
        <CfStateBanner variant="default">
          Dados indisponíveis para: {data.summary.branches_unavailable.join(", ")}.
        </CfStateBanner>
      ) : null}

      <CfMetricStrip
        aria-label="Indicadores da auditoria"
        items={[
          { id: "documents", label: "Notas conferidas", value: data.summary.kpis.documents },
          { id: "gross", label: "Valor conferido", value: money(data.summary.kpis.gross_checked) },
          {
            id: "high-diff",
            label: "Diferença alta",
            value: money(data.summary.kpis.high_difference),
            tone: data.summary.kpis.high_difference ? "danger" : "neutral",
          },
          { id: "occurrences", label: "Ocorrências", value: data.summary.kpis.occurrences },
          {
            id: "high",
            label: "Alta severidade",
            value: data.summary.kpis.high,
            tone: data.summary.kpis.high ? "danger" : "neutral",
          },
          { id: "pending", label: "Pendentes", value: data.summary.kpis.pending },
          { id: "resolved", label: "Resolvidas", value: data.summary.kpis.resolved },
        ]}
      />

      <div className="cf-charts-grid">
        <CfSectionCard
          title="Conformidade"
          hint={CF_HELP.entryAudit.conformity}
        >
          <CfSemicircleProgressGauge
            value={cleanShare}
            centerLabel="Notas limpas"
            aria-label="Percentual de notas limpas"
            legend={[
              {
                id: "clean",
                label: "Limpas",
                count: data.summary.conformity.clean,
                tone: "success",
              },
              {
                id: "divergent",
                label: "Divergentes",
                count: data.summary.conformity.divergent,
                tone: "danger",
              },
            ]}
          />
          <CfMetricStrip
            aria-label="Resumo de conformidade"
            items={[
              {
                id: "clean",
                label: "Limpas",
                value: data.summary.conformity.clean,
              },
              {
                id: "divergent",
                label: "Divergentes",
                value: data.summary.conformity.divergent,
                tone: data.summary.conformity.divergent ? "danger" : "neutral",
              },
              {
                id: "unmatched-open",
                label: "Sem par em aberto",
                value: data.summary.conformity.unmatched_open,
              },
              {
                id: "posted-outside",
                label: "Fora do período",
                value: data.summary.conformity.posted_outside_period.count,
                tone: "neutral",
              },
            ]}
          />
        </CfSectionCard>
        <CfDistributionDonut
          ariaLabel="Distribuição por severidade"
          items={data.breakdowns.by_severity.map((item) => ({
            id: item.name,
            label: item.name,
            value: item.count,
          }))}
          onSelect={(item) => {
            if (item) navigateWith({ severity: severityToUrl(item.id) });
          }}
          selectedId={filters.severity || undefined}
        />
        <CfHorizontalValueBars
          aria-label="Ocorrências por tema"
          items={data.breakdowns.by_theme.map((item) => ({
            id: item.name,
            label: item.name,
            value: item.count,
          }))}
          onItemClick={(item) => navigateWith({ theme: item.id })}
          selectedId={filters.theme || undefined}
        />
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
            status: "",
          })
        }
      />

      <CfSegmentToggle<EntryAuditTab>
        options={[...ENTRY_AUDIT_TABS]}
        value={tab}
        onChange={(value) => navigateWith({ tab: value })}
        ariaLabel="Visões da auditoria"
      />

      {tab === "occurrences" ? (
        <DataTableSection<EntryAuditOccurrence>
          title={`Ocorrências (${page?.total ?? 0})`}
          titleHint={CF_HELP.entryAudit.occurrences}
          columns={occurrenceColumns}
          rows={rows as EntryAuditOccurrence[]}
          rowKey={(row) => row.stable_key}
          onRowClick={openOccurrence}
          hidePaginationWhenSinglePage
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
        />
      )}

      <CfSectionCard
        title="Pergunte à CLARA"
        subtitle="A CLARA lê esta mesma análise"
        hint={CF_HELP.entryAudit.clara}
        collapsible
        defaultOpen={false}
      >
        <ul className="cf-page-stack">
          {claraSuggestions.map((suggestion) => (
            <li key={suggestion}>
              <span>{suggestion}</span>{" "}
              <CfActionButton
                type="button"
                variant="ghost"
                onClick={() => copySuggestion(suggestion)}
              >
                Copiar
              </CfActionButton>
            </li>
          ))}
        </ul>
        <p aria-live="polite">{copiedHint}</p>
      </CfSectionCard>
    </section>
  );
}
