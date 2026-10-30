/**
 * Despesas por Centro de Custo — R10 — Central de Fechamento.
 *
 * Consome `GET /closing/cost-center-expenses` (+`/export`) da BFF.
 * Dois universos estritos (doc 126/127):
 * - `calculation` — apuração histórica documentada: SD1 pelo eixo
 *   D1_DTDIGIT, treze TES excluídos, sem matéria-prima e sem linhas de
 *   benefícios. Reproduz o artefato de set/2026 (353 linhas /
 *   R$ 169.704,12) — paridade oficial ainda pendente de homologação.
 * - `investigation` — linhas da competência FORA da seleção oficial
 *   (matérias-primas, TES excluídos, benefícios), para investigar
 *   possíveis divergências de classificação/rateio. Totalizadores dos
 *   dois universos nunca são somados.
 *
 * Achados são sempre POSSIBLE_DIVERGENCE — nunca erro confirmado;
 * a correção é atividade humana externa no TOTVS/Protheus.
 */
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { ApiError } from "../../api/httpClient";
import { saveDocumentBlob } from "../../api/documentsApi";
import {
  costCenterExpensesExportFilename,
  exportCostCenterExpenses,
  getCostCenterExpenses,
  type CostCenterExpenseItem,
  type CostCenterExpensesPayload,
  type CostCenterExpensesUniverse,
  type CostCenterExpensesView,
  type StockInventoryBranch,
} from "../../api/costCenterExpensesApi";
import {
  CfActionButton,
  CfMetricStrip,
  CfSectionCard,
  CfStatusBadge,
  CfTitleWithHelp,
} from "../../app/controllershipFinanceUi";
import {
  CalendarDays,
  CircleDollarSign,
  Download,
  ListOrdered,
  OctagonAlert,
} from "lucide-react";
import {
  ClosingHero,
  type ClosingHeroMetric,
} from "../../app/ClosingHero";
import {
  CfFeedbackMessage,
  CfQueryErrorBanner,
} from "../../app/cfFeedbackUi";
import {
  DataTableSection,
  type DataTableColumn,
} from "../../app/cfDataTableUi";
import {
  FilterInputField,
  FilterSelectField,
  FiltersRow,
} from "../../app/cfFiltersUi";
import { CF_HELP } from "../../content/helpTooltips";
import {
  formatAmount,
  formatCivilDate,
  formatQuantity,
} from "../../utils/formatters";

const BRANCH_OPTIONS = [
  { value: "all", label: "Todas as filiais" },
  { value: "01", label: "Matriz (01)" },
  { value: "02", label: "Filial 02" },
] as const;

const UNIVERSE_OPTIONS = [
  { value: "calculation", label: "Apuração (universo do relatório)" },
  { value: "investigation", label: "Investigação (fora da apuração)" },
] as const;

const VIEW_OPTIONS = [
  { value: "all", label: "Todos os registros" },
  { value: "divergences", label: "Somente possíveis divergências" },
  { value: "unclassified", label: "Sem classificação comprovada" },
] as const;

const STATUS_LABELS: Record<string, string> = {
  available: "Disponível",
  no_matching_items: "Sem dados para o filtro",
};

const CC_STATUS_LABELS: Record<string, string> = {
  registered_analytic: "Cadastrado",
  registered_synthetic: "Sintético",
  registered_blocked: "Bloqueado",
  not_registered: "Não cadastrado",
  not_applicable: "—",
};

const RULE_LABELS: Record<string, string> = {
  "DV-R10-01": "MP com centro de custo",
  "DV-R10-02": "CC fora do cadastro",
  "DV-R10-03": "Produto × CC",
  "DV-R10-04": "Sem centro de custo",
  "DV-R10-05": "Sem classificação",
  "DV-R10-06": "Classificação divergente",
};

const EXCLUSION_LABELS: Record<string, string> = {
  tes_excluded: "TES excluído",
  raw_material_product: "Matéria-prima",
  benefit_line: "Benefício",
};

function currentCompetence(): string {
  const now = new Date();
  return `${now.getUTCFullYear()}-${String(now.getUTCMonth() + 1).padStart(2, "0")}`;
}

type AppliedFilters = {
  period: string;
  branch: StockInventoryBranch;
  universe: CostCenterExpensesUniverse;
  view: CostCenterExpensesView;
  costCenter: string;
  productCode: string;
  document: string;
  tes: string;
  page: number;
  pageSize: number;
};

type FetchResult =
  | { key: string; kind: "error"; status: number; code: string | null; message: string }
  | { key: string; kind: "ready"; payload: CostCenterExpensesPayload };

export type CostCenterExpensesReportContext = { period: string };

export function CostCenterExpensesPage({
  reportContext,
}: {
  reportContext?: CostCenterExpensesReportContext;
}) {
  const [period, setPeriod] = useState(
    () => reportContext?.period ?? currentCompetence(),
  );
  const [branch, setBranch] = useState<StockInventoryBranch>("all");
  const [universe, setUniverse] =
    useState<CostCenterExpensesUniverse>("calculation");
  const [view, setView] = useState<CostCenterExpensesView>("all");
  const [costCenter, setCostCenter] = useState("");
  const [productCode, setProductCode] = useState("");
  const [document, setDocument] = useState("");
  const [tes, setTes] = useState("");
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(50);
  const [result, setResult] = useState<FetchResult | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [retryNonce, setRetryNonce] = useState(0);
  const [exporting, setExporting] = useState<"csv" | "pdf" | null>(null);
  const [exportError, setExportError] = useState<string | null>(null);
  const requestId = useRef(0);

  const effectivePeriod = reportContext?.period ?? period;
  const filtersValid = /^\d{4}-(0[1-9]|1[0-2])$/.test(effectivePeriod);
  const applied: AppliedFilters | null = useMemo(
    () =>
      filtersValid
        ? {
            period: effectivePeriod,
            branch,
            universe,
            view,
            costCenter: costCenter.trim(),
            productCode: productCode.trim(),
            document: document.trim(),
            tes: tes.trim(),
            page,
            pageSize,
          }
        : null,
    [
      filtersValid,
      effectivePeriod,
      branch,
      universe,
      view,
      costCenter,
      productCode,
      document,
      tes,
      page,
      pageSize,
    ],
  );

  const clearFilters = useCallback(() => {
    setPeriod(reportContext?.period ?? currentCompetence());
    setBranch("all");
    setUniverse("calculation");
    setView("all");
    setCostCenter("");
    setProductCode("");
    setDocument("");
    setTes("");
    setPage(1);
  }, [reportContext]);

  const retry = useCallback(() => setRetryNonce((n) => n + 1), []);

  const handleExport = useCallback(
    async (format: "csv" | "pdf") => {
      if (!applied || exporting) return;
      setExporting(format);
      setExportError(null);
      try {
        const blob = await exportCostCenterExpenses(
          {
            period: applied.period,
            branch: applied.branch,
            universe: applied.universe,
            view: applied.view,
            costCenter: applied.costCenter || undefined,
            productCode: applied.productCode || undefined,
            document: applied.document || undefined,
            tes: applied.tes || undefined,
          },
          format,
        );
        saveDocumentBlob(
          blob,
          costCenterExpensesExportFilename(applied, format),
        );
      } catch (error) {
        setExportError(
          error instanceof ApiError
            ? error.message
            : "Não foi possível exportar o relatório agora.",
        );
      } finally {
        setExporting(null);
      }
    },
    [applied, exporting],
  );

  const queryKey = applied
    ? JSON.stringify({ ...applied, retryNonce })
    : null;
  const current: FetchResult | null =
    result && result.key === queryKey ? result : null;
  const loading = applied !== null && current === null;
  const payload = current?.kind === "ready" ? current.payload : null;

  useEffect(() => {
    if (!applied || !queryKey) return;
    const id = ++requestId.current;
    const controller = new AbortController();
    getCostCenterExpenses(
      {
        period: applied.period,
        branch: applied.branch,
        universe: applied.universe,
        view: applied.view,
        costCenter: applied.costCenter || undefined,
        productCode: applied.productCode || undefined,
        document: applied.document || undefined,
        tes: applied.tes || undefined,
        page: applied.page,
        pageSize: applied.pageSize,
      },
      { signal: controller.signal },
    )
      .then((data) => {
        if (controller.signal.aborted || requestId.current !== id) return;
        setResult({ key: queryKey, kind: "ready", payload: data });
        setLastUpdated(new Date());
      })
      .catch((error: unknown) => {
        if (controller.signal.aborted || requestId.current !== id) return;
        setResult({
          key: queryKey,
          kind: "error",
          status: error instanceof ApiError ? error.status : 0,
          code: error instanceof ApiError ? error.code : null,
          message:
            error instanceof ApiError
              ? error.message
              : "Falha de comunicação com a API de despesas por centro de custo.",
        });
      });
    return () => controller.abort();
  }, [applied, queryKey]);

  const columns = useMemo<DataTableColumn<CostCenterExpenseItem>[]>(
    () => [
      {
        key: "entryDate",
        header: "Data digitação",
        headerHint: CF_HELP.costCenterExpenses.columns.entryDate,
        render: (row) => formatCivilDate(row.entryDate),
      },
      {
        key: "document",
        header: "Documento",
        render: (row) => (
          <div>
            <div>{row.document}</div>
            <div className="cf-cell-muted">
              {row.series ? `série ${row.series} · ` : ""}item {row.item}
            </div>
          </div>
        ),
      },
      {
        key: "productCode",
        header: "Produto",
        headerHint: CF_HELP.costCenterExpenses.columns.product,
        render: (row) => (
          <div>
            <div>{row.productCode}</div>
            <div className="cf-cell-muted">
              {row.productDescription ?? ""}
              {row.productType ? ` · ${row.productType}` : ""}
            </div>
          </div>
        ),
      },
      {
        key: "costCenter",
        header: "Centro de custo",
        headerHint: CF_HELP.costCenterExpenses.columns.costCenter,
        render: (row) =>
          row.costCenter ? (
            <div>
              <div>{row.costCenter}</div>
              <div className="cf-cell-muted">
                {row.costCenterDescription ??
                  CC_STATUS_LABELS[row.costCenterCatalogStatus] ??
                  row.costCenterCatalogStatus}
              </div>
            </div>
          ) : (
            <CfStatusBadge
              label="Sem centro de custo"
              variant="warning"
            />
          ),
      },
      {
        key: "tes",
        header: "TES",
        render: (row) => row.tes ?? "—",
      },
      {
        key: "supplier",
        header: "Fornecedor",
        render: (row) => (
          <div>
            <div>{row.supplierCode ?? "—"}</div>
            <div className="cf-cell-muted">{row.supplierName ?? ""}</div>
          </div>
        ),
      },
      {
        key: "quantity",
        header: "Quantidade",
        align: "right",
        className: "cf-table__col--numeric",
        render: (row) => (
          <span className="cf-cell-amount">
            {formatQuantity(row.quantity)}
          </span>
        ),
      },
      {
        key: "totalValue",
        header: "Valor",
        align: "right",
        className: "cf-table__col--numeric",
        render: (row) => (
          <span className="cf-cell-amount">
            {formatAmount(row.totalValue)}
          </span>
        ),
      },
      {
        key: "calculationExclusion",
        header: "Fora da apuração",
        headerHint: CF_HELP.costCenterExpenses.columns.exclusion,
        render: (row) =>
          row.calculationExclusion ? (
            <CfStatusBadge
              label={
                EXCLUSION_LABELS[row.calculationExclusion] ??
                row.calculationExclusion
              }
              variant="info"
            />
          ) : (
            "—"
          ),
      },
      {
        key: "findings",
        header: "Alertas",
        headerHint: CF_HELP.costCenterExpenses.columns.findings,
        className: "cf-table__col--status",
        render: (row) =>
          row.findings.length > 0 ? (
            <div className="cf-page-stack">
              {row.findings.map((ruleId) => (
                <CfStatusBadge
                  key={ruleId}
                  label={RULE_LABELS[ruleId] ?? ruleId}
                  variant="warning"
                />
              ))}
            </div>
          ) : (
            "—"
          ),
      },
    ],
    [],
  );

  const heroMetrics = useMemo<ClosingHeroMetric[] | undefined>(() => {
    if (!payload) {
      return loading
        ? [
            {
              id: "status",
              label: "Disponibilidade",
              value: "",
              icon: <CalendarDays size={20} aria-hidden />,
            },
          ]
        : undefined;
    }
    const summary = payload.summary;
    return [
      {
        id: "status",
        label: "Disponibilidade",
        value: STATUS_LABELS[payload.status] ?? payload.status,
        hint: `competência ${payload.period} · ${payload.universe === "calculation" ? "apuração" : "investigação"}`,
        tone: payload.status === "available" ? "default" : "warning",
        icon: <CalendarDays size={20} aria-hidden />,
      },
      {
        id: "lines",
        label: "Linhas",
        value: String(summary?.lineCount ?? 0),
        hint: `${summary?.documentCount ?? 0} documentos · ${summary?.costCenterCount ?? 0} centros de custo`,
        icon: <ListOrdered size={20} aria-hidden />,
      },
      {
        id: "total",
        label: "Valor total",
        value: formatAmount(summary?.totalValue ?? "0"),
        hint:
          payload.universe === "calculation"
            ? "universo da apuração"
            : "somente investigação — nunca somado",
        icon: <CircleDollarSign size={20} aria-hidden />,
      },
      {
        id: "findings",
        label: "Possíveis divergências",
        value: String(summary?.findingCount ?? 0),
        hint: "candidatos a revisão no ERP",
        tone: (summary?.findingCount ?? 0) > 0 ? "warning" : "default",
        icon: <OctagonAlert size={20} aria-hidden />,
      },
    ];
  }, [payload, loading]);

  const renderStatusBanner = () => {
    if (!payload) return null;
    if (payload.status === "no_matching_items") {
      return (
        <CfFeedbackMessage intent="info" title="Sem dados para o filtro">
          A origem respondeu, mas nenhum lançamento corresponde aos
          filtros aplicados neste universo.
        </CfFeedbackMessage>
      );
    }
    return null;
  };

  const exportDisabled = exporting !== null || !payload;

  return (
    <section
      className="cf-page-stack cf-closing-layout"
      aria-label="Despesas por centro de custo — R10"
    >
      <ClosingHero
        title={
          <CfTitleWithHelp
            title="Despesas por centro de custo — R10"
            hint={CF_HELP.costCenterExpenses.page}
          />
        }
        subtitle={
          reportContext
            ? `Despesas por centro de custo da competência ${reportContext.period} — apuração histórica e investigação de divergências.`
            : "Despesas por centro de custo por competência — apuração histórica (eixo de digitação) e universo investigativo separado. Leitura: nenhuma correção é executada no ERP."
        }
        updatedAt={lastUpdated}
        onRefresh={retry}
        refreshing={loading}
        metrics={heroMetrics}
        notice={
          <CfFeedbackMessage intent="info" title="Paridade pendente">
            Seleção histórica reproduzida para set/2026 filial 01 (353
            linhas / R$ 169.704,12); a homologação oficial por competência
            segue pendente — achados são possíveis divergências para
            conferência humana no Protheus, nunca erro confirmado.
          </CfFeedbackMessage>
        }
        filters={
          <form
            className="cf-settlements-filters"
            onSubmit={(event) => event.preventDefault()}
          >
            <FiltersRow>
              {reportContext ? null : (
                <FilterInputField
                  id="cf-r10-period"
                  label="Competência"
                  type="month"
                  value={period}
                  onChange={setPeriod}
                />
              )}
              <FilterSelectField
                label="Filial"
                value={branch}
                onChange={(value) =>
                  setBranch(value as StockInventoryBranch)
                }
                options={BRANCH_OPTIONS}
              />
              <FilterSelectField
                label="Universo"
                value={universe}
                onChange={(value) => {
                  setUniverse(value as CostCenterExpensesUniverse);
                  setPage(1);
                }}
                options={UNIVERSE_OPTIONS}
              />
              <FilterSelectField
                label="Visão"
                value={view}
                onChange={(value) => {
                  setView(value as CostCenterExpensesView);
                  setPage(1);
                }}
                options={VIEW_OPTIONS}
              />
              <FilterInputField
                id="cf-r10-cc"
                label="Centro de custo"
                type="text"
                value={costCenter}
                onChange={setCostCenter}
                placeholder="código"
              />
              <FilterInputField
                id="cf-r10-product"
                label="Produto"
                type="text"
                value={productCode}
                onChange={setProductCode}
                placeholder="código"
              />
              <FilterInputField
                id="cf-r10-doc"
                label="Documento"
                type="text"
                value={document}
                onChange={setDocument}
                placeholder="número"
              />
              <FilterInputField
                id="cf-r10-tes"
                label="TES"
                type="text"
                value={tes}
                onChange={setTes}
                placeholder="código"
              />
            </FiltersRow>
            {!filtersValid ? (
              <CfFeedbackMessage intent="error" title="Competência inválida">
                Informe uma competência válida no formato AAAA-MM.
              </CfFeedbackMessage>
            ) : null}
            {payload?.universe === "investigation" ? (
              <CfFeedbackMessage
                intent="info"
                title="Universo investigativo"
              >
                Estas linhas ficam fora da apuração do relatório — os
                totais desta visão nunca se somam ao total oficial.
              </CfFeedbackMessage>
            ) : null}
          </form>
        }
        onClearFilters={clearFilters}
        extraActions={
          <>
            <CfActionButton
              variant="ghost"
              type="button"
              onClick={() => handleExport("csv")}
              disabled={exportDisabled}
              title={CF_HELP.costCenterExpenses.export}
            >
              <Download size={16} aria-hidden />{" "}
              {exporting === "csv" ? "Exportando…" : "Exportar CSV"}
            </CfActionButton>
            <CfActionButton
              variant="ghost"
              type="button"
              onClick={() => handleExport("pdf")}
              disabled={exportDisabled}
              title={CF_HELP.costCenterExpenses.export}
            >
              <Download size={16} aria-hidden />{" "}
              {exporting === "pdf" ? "Exportando…" : "Exportar PDF"}
            </CfActionButton>
          </>
        }
      />

      <div className="cf-page-stack" aria-busy={loading}>
        {exportError ? (
          <CfFeedbackMessage intent="error" title="Exportação não concluída">
            {exportError}
          </CfFeedbackMessage>
        ) : null}
        {current?.kind === "error" ? (
          <CfQueryErrorBanner
            error={current}
            dataset="as despesas por centro de custo"
            onRetry={retry}
          />
        ) : null}
        {renderStatusBanner()}

        {payload?.summary ? (
          <CfSectionCard
            title="Totais do universo"
            hint={CF_HELP.costCenterExpenses.totals}
          >
            <CfMetricStrip
              aria-label="Totais das despesas por centro de custo"
              items={[
                {
                  id: "lines",
                  label: "Linhas",
                  value: String(payload.summary.lineCount),
                  description: `${payload.summary.documentCount} documentos`,
                },
                {
                  id: "total",
                  label: "Valor total",
                  value: formatAmount(payload.summary.totalValue),
                  description:
                    payload.universe === "calculation"
                      ? "apuração"
                      : "investigação — nunca somado",
                },
                {
                  id: "ccs",
                  label: "Centros de custo",
                  value: String(payload.summary.costCenterCount),
                  description: `${payload.summary.supplierCount} fornecedores`,
                },
                {
                  id: "findings",
                  label: "Possíveis divergências",
                  value: String(payload.summary.findingCount),
                  description:
                    "candidatos a revisão — não são erro confirmado",
                },
              ]}
            />
            <p className="cf-cell-muted">
              <CfStatusBadge
                label={
                  payload.parityStatus === "PENDING"
                    ? "Paridade oficial: pendente"
                    : `Paridade: ${payload.parityStatus}`
                }
                variant="warning"
              />{" "}
              {(payload.parityNotes ?? []).join(" ")}
            </p>
          </CfSectionCard>
        ) : null}

        {payload && payload.summary && payload.summary.byCostCenter.length > 0 ? (
          <CfSectionCard
            title="Resumo por centro de custo"
            hint={CF_HELP.costCenterExpenses.summaryCostCenter}
          >
            <CfMetricStrip
              aria-label="Despesas por centro de custo"
              items={payload.summary.byCostCenter
                .slice(0, 12)
                .map((row) => ({
                  id: `cc-${row.costCenter ?? "sem-cc"}`,
                  label: row.costCenter
                    ? `CC ${row.costCenter}${row.costCenterDescription ? ` · ${row.costCenterDescription}` : ""}`
                    : "Sem centro de custo",
                  value: formatAmount(row.totalValue),
                  description: `${row.lineCount} linha(s)${row.findingCount ? ` · ${row.findingCount} alerta(s)` : ""}`,
                }))}
            />
          </CfSectionCard>
        ) : null}

        {payload && payload.findings.length > 0 ? (
          <CfSectionCard
            title="Possíveis divergências"
            hint={CF_HELP.costCenterExpenses.findings}
          >
            <ul className="cf-page-stack" aria-label="Lista de possíveis divergências">
              {payload.findings.slice(0, 25).map((finding) => {
                const src = finding.sourceRecord as Record<
                  string,
                  unknown
                >;
                return (
                  <li key={finding.findingId}>
                    <CfFeedbackMessage
                      intent="warning"
                      title={`${RULE_LABELS[finding.ruleId] ?? finding.ruleId} — doc ${src.document ?? "—"} item ${src.item ?? "—"}`}
                    >
                      {finding.findingExplanation}
                      <br />
                      <span className="cf-cell-muted">
                        Produto {String(src.productCode ?? "—")} · CC{" "}
                        {String(src.costCenterCode ?? "—")} · TES{" "}
                        {String(src.tes ?? "—")} ·{" "}
                        {finding.erpReviewGuidance}
                      </span>
                    </CfFeedbackMessage>
                  </li>
                );
              })}
            </ul>
            {payload.findingsTruncated || payload.findings.length > 25 ? (
              <p className="cf-cell-muted">
                Exibindo {Math.min(payload.findings.length, 25)} de{" "}
                {payload.summary?.findingCount ?? payload.findings.length}{" "}
                achados — use a visão «Somente possíveis divergências» ou
                a exportação para a lista completa.
              </p>
            ) : null}
          </CfSectionCard>
        ) : null}

        <DataTableSection<CostCenterExpenseItem>
          title={
            payload?.universe === "investigation"
              ? "Linhas investigativas do período"
              : "Linhas da apuração"
          }
          titleHint={CF_HELP.costCenterExpenses.table}
          columns={columns}
          rows={payload?.items ?? []}
          rowKey={(row) => String(row.lineId)}
          loading={loading}
          hideSearch
          emptyMessage="Nenhum lançamento no período para os filtros aplicados."
          columnPreferencesKey="cf:closing:cost-center-expenses:v1"
          serverPagination={
            payload?.pagination
              ? {
                  page: payload.pagination.page,
                  pageSize: payload.pagination.page_size,
                  total: payload.pagination.total_items,
                  onPageChange: setPage,
                  onPageSizeChange: (size) => {
                    setPageSize(size);
                    setPage(1);
                  },
                }
              : undefined
          }
        />
      </div>
    </section>
  );
}
