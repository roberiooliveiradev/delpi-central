/**
 * Kardex — R06 (regra MATR910) + CPV gerencial — Central de Fechamento.
 *
 * Consome `GET /closing/stock-kardex` (+`/summary`, `/export`) e
 * `GET /closing/cpv` da BFF. O motor canônico aplica a UNION
 * SD1/SD2/SD3 do MATR910 (entrada ≤500/saída >500, devolução negativa,
 * REF F-/P-/OP/CC), saldo inicial do SB9 do fechamento anterior (nunca
 * zero fabricado — `source_missing` é estado próprio) e custo as-of
 * via histórico TTAT (`costAsOfSource`). O CPV é medida viva distinta
 * (D-O1, `asOfConvention: "live"`) — não é o total de saídas do kardex
 * e nunca é reconciliado a ele. Paridade oficial: pendente.
 */
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { ApiError } from "../../api/httpClient";
import { saveDocumentBlob } from "../../api/documentsApi";
import {
  exportStockKardex,
  getCpv,
  getStockKardex,
  getStockKardexSummary,
  kardexExportFilename,
  type CpvPayload,
  type KardexMovementItem,
  type KardexPayload,
  type KardexSummaryPayload,
} from "../../api/stockKardexApi";
import type { StockInventoryBranch } from "../../api/stockInventoryApi";
import {
  CfActionButton,
  CfMetricStrip,
  CfSectionCard,
  CfStatusBadge,
  CfTitleWithHelp,
} from "../../app/controllershipFinanceUi";
import {
  ArrowDownUp,
  CalendarDays,
  CircleDollarSign,
  Download,
  ListOrdered,
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
import { formatAmount, formatCivilDate, formatQuantity } from "../../utils/formatters";
import {
  parseStockQuery,
  readReportSearchParams,
  serializeStockQuery,
  useReportQuerySync,
} from "./reportQueryParams";

const BRANCH_OPTIONS = [
  { value: "all", label: "Todas as filiais" },
  { value: "01", label: "Matriz (01)" },
  { value: "02", label: "Filial 02" },
] as const;

const KIND_OPTIONS = [
  { value: "", label: "Entradas e saídas" },
  { value: "entry", label: "Somente entradas" },
  { value: "output", label: "Somente saídas" },
] as const;

const STATUS_LABELS: Record<string, string> = {
  available: "Disponível",
  incomplete: "Parcialmente disponível",
  source_missing: "Não encontrado",
  no_matching_items: "Sem dados para o filtro",
};

const MOVEMENT_KIND_LABELS: Record<string, string> = {
  entry: "Entrada",
  output: "Saída",
};

function currentCompetence(): string {
  const now = new Date();
  return `${now.getUTCFullYear()}-${String(now.getUTCMonth() + 1).padStart(2, "0")}`;
}

type AppliedFilters = {
  period: string;
  branch: StockInventoryBranch;
  warehouse: string;
  productCode: string;
  movementKind: "entry" | "output" | undefined;
  page: number;
  pageSize: number;
};

type FetchResult =
  | { key: string; kind: "error"; status: number; code: string | null; message: string }
  | { key: string; kind: "ready"; payload: KardexPayload };

export type StockKardexReportContext = { period: string };

export function StockKardexPage({
  reportContext,
}: {
  reportContext?: StockKardexReportContext;
}) {
  const [period, setPeriod] = useState(
    () => reportContext?.period ?? currentCompetence(),
  );
  const [urlInit] = useState(() =>
    reportContext ? parseStockQuery(readReportSearchParams()) : null,
  );
  const [branch, setBranch] = useState<StockInventoryBranch>(
    () => urlInit?.branch ?? "all",
  );
  const [warehouse, setWarehouse] = useState(() => urlInit?.warehouse ?? "");
  const [productCode, setProductCode] = useState("");
  const [movementKind, setMovementKind] = useState<"" | "entry" | "output">("");
  const [page, setPage] = useState(() => urlInit?.page ?? 1);
  const [pageSize, setPageSize] = useState(50);
  const [result, setResult] = useState<FetchResult | null>(null);
  const [summary, setSummary] = useState<KardexSummaryPayload | null>(null);
  const [cpv, setCpv] = useState<CpvPayload | null>(null);
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
            warehouse: warehouse.trim(),
            productCode: productCode.trim(),
            movementKind: movementKind || undefined,
            page,
            pageSize,
          }
        : null,
    [
      filtersValid,
      effectivePeriod,
      branch,
      warehouse,
      productCode,
      movementKind,
      page,
      pageSize,
    ],
  );

  const clearFilters = useCallback(() => {
    setPeriod(reportContext?.period ?? currentCompetence());
    setBranch("all");
    setWarehouse("");
    setProductCode("");
    setMovementKind("");
    setPage(1);
  }, [reportContext]);

  const retry = useCallback(() => setRetryNonce((n) => n + 1), []);

  const handleExport = useCallback(
    async (format: "csv" | "pdf") => {
      if (!applied || exporting) return;
      setExporting(format);
      setExportError(null);
      try {
        const blob = await exportStockKardex(
          {
            period: applied.period,
            branch: applied.branch,
            warehouse: applied.warehouse || undefined,
            productCode: applied.productCode || undefined,
          },
          format,
        );
        saveDocumentBlob(
          blob,
          kardexExportFilename("stock-kardex", applied, format),
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

  // RW01: query da rota espelha os filtros.
  const hydrateFromUrl = useCallback((params: URLSearchParams) => {
    const parsed = parseStockQuery(params);
    setBranch(parsed.branch);
    setWarehouse(parsed.warehouse);
    setPage(parsed.page);
  }, []);
  useReportQuerySync({
    enabled: Boolean(reportContext),
    serialize: () => {
      const query = serializeStockQuery({
        branch,
        scope: "all_products",
        warehouse,
        page,
      });
      return query ? `?${query}` : "";
    },
    hydrate: hydrateFromUrl,
  });

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
    getStockKardex(
      {
        period: applied.period,
        branch: applied.branch,
        warehouse: applied.warehouse || undefined,
        productCode: applied.productCode || undefined,
        movementKind: applied.movementKind,
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
              : "Falha de comunicação com a API de kardex.",
        });
      });
    getStockKardexSummary(
      {
        period: applied.period,
        branch: applied.branch,
        warehouse: applied.warehouse || undefined,
        productCode: applied.productCode || undefined,
      },
      { signal: controller.signal },
    )
      .then((data) => {
        if (controller.signal.aborted || requestId.current !== id) return;
        setSummary(data);
      })
      .catch(() => {
        if (!controller.signal.aborted) setSummary(null);
      });
    getCpv(
      { period: applied.period, branch: applied.branch, topLimit: 10 },
      { signal: controller.signal },
    )
      .then((data) => {
        if (controller.signal.aborted || requestId.current !== id) return;
        setCpv(data);
      })
      .catch(() => {
        if (!controller.signal.aborted) setCpv(null);
      });
    return () => controller.abort();
  }, [applied, queryKey]);

  const columns = useMemo<DataTableColumn<KardexMovementItem>[]>(
    () => [
      {
        key: "movementDate",
        header: "Data",
        render: (row) => formatCivilDate(row.movementDate),
      },
      {
        key: "productCode",
        header: "Produto",
        headerHint: CF_HELP.stockKardex.columns.product,
        render: (row) => (
          <div>
            <div>{row.productCode}</div>
            <div className="cf-cell-muted">{row.description}</div>
          </div>
        ),
      },
      {
        key: "document",
        header: "Documento",
        headerHint: CF_HELP.stockKardex.columns.document,
        render: (row) => row.document,
      },
      {
        key: "movementKind",
        header: "Movimento",
        headerHint: CF_HELP.stockKardex.columns.kind,
        className: "cf-table__col--status",
        render: (row) => (
          <CfStatusBadge
            label={
              MOVEMENT_KIND_LABELS[row.movementKind] ?? row.movementKind
            }
            variant={row.movementKind === "output" ? "warning" : "neutral"}
          />
        ),
      },
      {
        key: "tm",
        header: "TM",
        headerHint: CF_HELP.stockKardex.columns.tm,
        render: (row) => row.tm ?? "—",
      },
      {
        key: "reference",
        header: "REF",
        headerHint: CF_HELP.stockKardex.columns.reference,
        render: (row) => row.reference ?? "—",
      },
      {
        key: "quantity",
        header: "Quantidade",
        align: "right",
        className: "cf-table__col--numeric",
        render: (row) => (
          <span className="cf-cell-amount">
            {formatQuantity(
              row.movementKind === "entry"
                ? row.entryQuantity
                : row.outputQuantity,
            )}
          </span>
        ),
      },
      {
        key: "value",
        header: "Valor",
        align: "right",
        className: "cf-table__col--numeric",
        render: (row) => (
          <span className="cf-cell-amount">
            {formatAmount(
              row.movementKind === "entry"
                ? row.entryValue
                : row.outputValue,
            )}
          </span>
        ),
      },
      {
        key: "unitCost",
        header: "Custo unit.",
        align: "right",
        className: "cf-table__col--numeric",
        headerHint: CF_HELP.stockKardex.columns.unitCost,
        render: (row) =>
          row.unitCost != null ? (
            <span className="cf-cell-amount">
              {formatAmount(row.unitCost)}
            </span>
          ) : (
            "—"
          ),
      },
      {
        key: "runningValue",
        header: "Saldo",
        align: "right",
        className: "cf-table__col--numeric",
        headerHint: CF_HELP.stockKardex.columns.running,
        render: (row) =>
          row.runningValue != null ? (
            <span className="cf-cell-amount">
              {formatAmount(row.runningValue)}
            </span>
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
              icon: <ArrowDownUp size={20} aria-hidden />,
            },
            {
              id: "dataAsOf",
              label: "Data-base",
              value: "",
              icon: <CalendarDays size={20} aria-hidden />,
            },
          ]
        : undefined;
    }
    return [
      {
        id: "status",
        label: "Disponibilidade",
        value: STATUS_LABELS[payload.status] ?? payload.status,
        hint:
          payload.branchesMissing.length > 0
            ? `sem snapshot: filial ${payload.branchesMissing.join(", ")}`
            : `competência ${payload.period}`,
        tone: payload.status === "available" ? "default" : "warning",
        icon: <ArrowDownUp size={20} aria-hidden />,
      },
      {
        id: "dataAsOf",
        label: "Data-base",
        value: formatCivilDate(payload.dataAsOf),
        hint: `competência ${payload.period}`,
        icon: <CalendarDays size={20} aria-hidden />,
      },
      {
        id: "movements",
        label: "Movimentações",
        value: String(payload.totals.movementCount),
        hint: `${payload.totals.blockCount} produto/armazém`,
        icon: <ListOrdered size={20} aria-hidden />,
      },
      ...(payload.totals.closingValue != null
        ? [
            {
              id: "closing",
              label: "Saldo final",
              value: formatAmount(payload.totals.closingValue),
              hint: `abertura ${formatAmount(payload.totals.openingValue ?? "0")}`,
              icon: <CircleDollarSign size={20} aria-hidden />,
            },
          ]
        : []),
    ];
  }, [payload, loading]);

  const renderStatusBanner = () => {
    if (!payload || payload.status === "available") return null;
    if (payload.status === "source_missing") {
      return (
        <CfFeedbackMessage intent="warning" title="Snapshot não encontrado">
          O ERP não possui fechamento de estoque do mês anterior registrado
          para {payload.period} — sem saldo inicial certificado, o kardex
          não é exibido. A ausência não é um saldo zero.
        </CfFeedbackMessage>
      );
    }
    if (payload.status === "incomplete") {
      return (
        <CfFeedbackMessage intent="warning" title="Dados parcialmente disponíveis">
          O snapshot anterior não existe para{" "}
          {payload.branchesMissing.join(", ")} — os saldos cobrem somente{" "}
          {payload.branchesAvailable.join(", ")}.
        </CfFeedbackMessage>
      );
    }
    return (
      <CfFeedbackMessage intent="info" title="Sem dados para o filtro">
        A origem respondeu, mas nenhuma movimentação corresponde aos
        filtros aplicados.
      </CfFeedbackMessage>
    );
  };

  const exportDisabled =
    exporting !== null || !payload || payload.status === "source_missing";

  return (
    <section
      className="cf-page-stack cf-closing-layout"
      aria-label="Kardex — R06"
    >
      <ClosingHero
        title={
          <CfTitleWithHelp
            title="Kardex — R06"
            hint={CF_HELP.stockKardex.page}
          />
        }
        subtitle={
          reportContext
            ? `Movimentações da competência ${reportContext.period} · regra MATR910 (SD1/SD2/SD3 + SB9 + TTAT).`
            : "Kardex de produtos por competência — regra MATR910 (SD1/SD2/SD3 + SB9 + TTAT)."
        }
        updatedAt={lastUpdated}
        onRefresh={retry}
        refreshing={loading}
        metrics={heroMetrics}
        notice={
          <CfFeedbackMessage intent="info" title="Paridade pendente">
            Regra MATR910 reconstruída a partir do produtor oficial; a
            homologação por competência contra uma nova emissão oficial
            ainda está pendente — os valores não são selo oficial.
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
                  id="cf-r06-period"
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
              <FilterInputField
                id="cf-r06-warehouse"
                label="Armazém"
                type="text"
                value={warehouse}
                onChange={setWarehouse}
                placeholder="ex.: 01,99"
              />
              <FilterInputField
                id="cf-r06-product"
                label="Produto"
                type="text"
                value={productCode}
                onChange={setProductCode}
                placeholder="código"
              />
              <FilterSelectField
                label="Movimento"
                value={movementKind}
                onChange={(value) =>
                  setMovementKind(value as "" | "entry" | "output")
                }
                options={KIND_OPTIONS}
              />
            </FiltersRow>
            {!filtersValid ? (
              <CfFeedbackMessage intent="error" title="Competência inválida">
                Informe uma competência válida no formato AAAA-MM.
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
              title={CF_HELP.stockKardex.export}
            >
              <Download size={16} aria-hidden />{" "}
              {exporting === "csv" ? "Exportando…" : "Exportar CSV"}
            </CfActionButton>
            <CfActionButton
              variant="ghost"
              type="button"
              onClick={() => handleExport("pdf")}
              disabled={exportDisabled}
              title={CF_HELP.stockKardex.export}
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
            dataset="o kardex de estoque"
            onRetry={retry}
          />
        ) : null}
        {renderStatusBanner()}

        {payload && payload.status !== "source_missing" ? (
          <CfSectionCard title="Totais do período" hint={CF_HELP.stockKardex.totals}>
            <CfMetricStrip
              aria-label="Totais do kardex"
              items={[
                {
                  id: "opening",
                  label: "Saldo inicial",
                  value:
                    payload.totals.openingValue != null
                      ? formatAmount(payload.totals.openingValue)
                      : "—",
                  description: "snapshot SB9 do fechamento anterior",
                },
                {
                  id: "entries",
                  label: "Entradas",
                  value: formatAmount(payload.totals.entryValue),
                  description: `${formatQuantity(payload.totals.entryQuantity)} un.`,
                },
                {
                  id: "outputs",
                  label: "Saídas",
                  value: formatAmount(payload.totals.outputValue),
                  description: `${formatQuantity(payload.totals.outputQuantity)} un.`,
                },
                {
                  id: "closing",
                  label: "Saldo final",
                  value:
                    payload.totals.closingValue != null
                      ? formatAmount(payload.totals.closingValue)
                      : "—",
                  description: "abertura + entradas − saídas",
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

        {summary && summary.summariesByWarehouse.length > 0 ? (
          <CfSectionCard
            title="Resumo por armazém"
            hint={CF_HELP.stockKardex.summaryWarehouse}
          >
            <CfMetricStrip
              aria-label="Resumo por armazém"
              items={summary.summariesByWarehouse.map((row) => ({
                id: `wh-${row.branchCode}-${row.warehouse}`,
                label: `Armazém ${row.warehouse} · filial ${row.branchCode}`,
                value: formatAmount(
                  String(
                    (
                      Number(row.entryValue) - Number(row.outputValue)
                    ).toFixed(6),
                  ),
                ),
                description: `${row.movementCount} movimentos`,
              }))}
            />
          </CfSectionCard>
        ) : null}

        {cpv ? (
          <CfSectionCard title="CPV gerencial — medida viva" hint={CF_HELP.stockKardex.cpv}>
            <CfMetricStrip
              aria-label="CPV gerencial"
              items={[
                {
                  id: "cpvTotal",
                  label: "CPV do período",
                  value: formatAmount(cpv.summary.cpvTotal),
                  description: `${cpv.summary.totalMovements} movimentos · CFOPs ${cpv.cfops.join("/")}`,
                },
                {
                  id: "cpvAvg",
                  label: "Custo médio/unidade",
                  value: formatAmount(cpv.summary.averageCostPerUnit),
                  description: "medida viva — sujeita a retificação oficial",
                },
                {
                  id: "cpvTop",
                  label: "Maior produto",
                  value: cpv.topProducts[0]?.productCode ?? "—",
                  description: cpv.topProducts[0]?.description ?? "",
                },
              ]}
            />
            <p className="cf-cell-muted">
              <CfStatusBadge label="asOf: live" variant="neutral" />{" "}
              {(cpv.parityNotes ?? []).join(" ")}
            </p>
          </CfSectionCard>
        ) : null}

        {payload?.status !== "source_missing" ? (
          <DataTableSection<KardexMovementItem>
            title="Movimentações do período"
            titleHint={CF_HELP.stockKardex.table}
            columns={columns}
            rows={payload?.items ?? []}
            rowKey={(row) => `${row.sourceTable}-${row.movementId}`}
            loading={loading}
            hideSearch
            emptyMessage="Nenhuma movimentação no período para os filtros aplicados."
            columnPreferencesKey="cf:closing:stock-kardex:v1"
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
        ) : null}
      </div>
    </section>
  );
}
