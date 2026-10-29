/**
 * Material em Processo — R08 (MATR989) — Central de Fechamento.
 *
 * Consome `GET /closing/work-in-process` da BFF — a mesma composição
 * MATR989 que o motor P7 certifica como EM PROCESSO: bloco físico
 * sem-OP (SB9 armazém 99) + saldo alocado líquido (RE − DE) em ordens
 * vivas na data de emissão. `source_missing`/`incomplete` são estados
 * próprios — nunca zero fabricado. Paridade MATR989 pendente de
 * homologação por competência.
 */
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { ApiError } from "../../api/httpClient";
import { saveDocumentBlob } from "../../api/documentsApi";
import {
  exportWorkInProcess,
  getWorkInProcess,
  workInProcessExportFilename,
  type WorkInProcessItem,
  type WorkInProcessPayload,
  type WorkInProcessTypeSummary,
} from "../../api/workInProcessApi";
import type {
  StockInventoryBranch,
  StockInventoryScope,
} from "../../api/stockInventoryApi";
import {
  CfActionButton,
  CfEmptyState,
  CfMetricStrip,
  CfSectionCard,
  CfSegmentToggle,
  CfStatusBadge,
  CfTitleWithHelp,
  cfEmptyStateClassNames,
} from "../../app/controllershipFinanceUi";
import {
  CalendarDays,
  CircleDollarSign,
  Download,
  Factory,
  ScrollText,
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
import { useDebouncedValue } from "../../utils/useDebouncedValue";
import {
  parseStockQuery,
  readReportSearchParams,
  serializeStockQuery,
  useReportQuerySync,
} from "./reportQueryParams";

const PAGE_SIZE = 50;
const DEBOUNCE_MS = 400;

const BRANCH_OPTIONS = [
  { value: "all", label: "Todas as filiais" },
  { value: "01", label: "Matriz (01)" },
  { value: "02", label: "Filial 02" },
] as const;

const SCOPE_OPTIONS = [
  { value: "all_products", label: "Todos os produtos" },
  { value: "mp_pi_pa", label: "MP / PI / PA" },
] as const;

const STATUS_LABELS: Record<string, string> = {
  available: "Disponível",
  incomplete: "Parcialmente disponível",
  source_missing: "Não encontrado",
  no_matching_items: "Sem dados para o filtro",
};

function currentCompetence(): string {
  const now = new Date();
  return `${now.getUTCFullYear()}-${String(now.getUTCMonth() + 1).padStart(2, "0")}`;
}

type AppliedFilters = {
  period: string;
  branch: StockInventoryBranch;
  reportScope: StockInventoryScope;
  warehouse: string;
};

type FetchState =
  | { kind: "error"; status: number; code: string | null; message: string }
  | { kind: "ready"; payload: WorkInProcessPayload };

type FetchResult = { key: string } & FetchState;

export type WorkInProcessReportContext = { period: string };

export function WorkInProcessPage({
  reportContext,
}: {
  reportContext?: WorkInProcessReportContext;
}) {
  const [period, setPeriod] = useState(
    () => reportContext?.period ?? currentCompetence(),
  );
  // RW01: no modo contextual os filtros iniciais vêm da query da rota.
  const [urlInit] = useState(() =>
    reportContext ? parseStockQuery(readReportSearchParams()) : null,
  );
  const [branch, setBranch] = useState<StockInventoryBranch>(
    () => urlInit?.branch ?? "all",
  );
  const [reportScope, setReportScope] = useState<StockInventoryScope>(
    () => urlInit?.scope ?? "all_products",
  );
  const [warehouse, setWarehouse] = useState(
    () => urlInit?.warehouse ?? "",
  );
  const debouncedWarehouse = useDebouncedValue(
    warehouse.trim(),
    DEBOUNCE_MS,
  );
  const [page, setPage] = useState(() => urlInit?.page ?? 1);
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
            reportScope,
            warehouse: debouncedWarehouse,
          }
        : null,
    [
      filtersValid,
      effectivePeriod,
      branch,
      reportScope,
      debouncedWarehouse,
    ],
  );

  const appliedFingerprint = JSON.stringify(applied);
  const [appliedFingerprintSeen, setAppliedFingerprintSeen] =
    useState(appliedFingerprint);
  if (appliedFingerprint !== appliedFingerprintSeen) {
    setAppliedFingerprintSeen(appliedFingerprint);
    if (page !== 1) setPage(1);
  }

  const clearFilters = useCallback(() => {
    setPeriod(reportContext?.period ?? currentCompetence());
    setBranch("all");
    setReportScope("all_products");
    setWarehouse("");
  }, [reportContext]);

  const retry = useCallback(() => setRetryNonce((n) => n + 1), []);

  const handleExport = useCallback(
    async (format: "csv" | "pdf") => {
      if (!applied || exporting) return;
      setExporting(format);
      setExportError(null);
      try {
        const blob = await exportWorkInProcess(applied, format);
        saveDocumentBlob(
          blob,
          workInProcessExportFilename(applied, format),
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

  // RW01: query da rota espelha os filtros — deep link e F5
  // restauram o recorte exato da análise.
  const hydrateFromUrl = useCallback(
    (params: URLSearchParams) => {
      const parsed = parseStockQuery(params);
      setBranch(parsed.branch);
      setReportScope(parsed.scope);
      setWarehouse(parsed.warehouse);
      setAppliedFingerprintSeen(
        JSON.stringify({
          period: effectivePeriod,
          branch: parsed.branch,
          reportScope: parsed.scope,
          warehouse: parsed.warehouse.trim(),
        }),
      );
      setPage(parsed.page);
    },
    [effectivePeriod],
  );
  useReportQuerySync({
    enabled: Boolean(reportContext),
    serialize: () => {
      const query = serializeStockQuery({
        branch,
        scope: reportScope,
        warehouse: warehouse.trim(),
        page,
      });
      return query ? `?${query}` : "";
    },
    hydrate: hydrateFromUrl,
  });

  const queryKey = applied
    ? JSON.stringify({ ...applied, page, retryNonce })
    : null;
  const current: FetchResult | null =
    result && result.key === queryKey ? result : null;
  const loading = applied !== null && current === null;
  const payload = current?.kind === "ready" ? current.payload : null;

  useEffect(() => {
    if (!applied || !queryKey) return;
    const id = ++requestId.current;
    const controller = new AbortController();
    getWorkInProcess(
      { ...applied, page, pageSize: PAGE_SIZE },
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
              : "Falha de comunicação com a API de material em processo.",
        });
      });
    return () => controller.abort();
  }, [applied, page, queryKey]);

  const itemColumns = useMemo<DataTableColumn<WorkInProcessItem>[]>(
    () => [
      {
        key: "productCode",
        header: "Produto",
        headerHint: CF_HELP.workInProcess.columns.product,
        className: "cf-table__col--compact",
        render: (row) => (
          <span className="cf-cell-primary">{row.productCode}</span>
        ),
      },
      {
        key: "description",
        header: "Descrição",
        headerHint: CF_HELP.workInProcess.columns.description,
        className: "cf-table__col--wrap",
        render: (row) => row.description ?? "—",
      },
      {
        key: "productType",
        header: "Tipo",
        headerHint: CF_HELP.stockMovements.columns.type,
        className: "cf-table__col--status",
        render: (row) =>
          row.productType ? (
            <CfStatusBadge label={row.productType} variant="neutral" />
          ) : (
            "Sem tipo"
          ),
      },
      {
        key: "productionOrder",
        header: "Ordem de produção",
        headerHint: CF_HELP.workInProcess.columns.order,
        className: "cf-table__col--compact",
        render: (row) => row.productionOrder ?? "—",
      },
      {
        key: "branchCode",
        header: "Filial",
        headerHint: CF_HELP.stockInventory.columns.branch,
        className: "cf-table__col--compact",
        render: (row) =>
          row.branchCode ? `Filial ${row.branchCode}` : "—",
      },
      {
        key: "allocatedQuantity",
        header: "Qtd. alocada",
        headerHint: CF_HELP.workInProcess.columns.allocatedQuantity,
        align: "right",
        className: "cf-table__col--numeric",
        render: (row) => formatQuantity(row.allocatedQuantity),
      },
      {
        key: "allocatedValue",
        header: "Valor alocado",
        headerHint: CF_HELP.workInProcess.columns.allocatedValue,
        align: "right",
        className: "cf-table__col--numeric",
        render: (row) => (
          <span className="cf-cell-amount">
            {formatAmount(row.allocatedValue)}
          </span>
        ),
      },
    ],
    [],
  );

  const typeColumns = useMemo<
    DataTableColumn<WorkInProcessTypeSummary>[]
  >(
    () => [
      {
        key: "productType",
        header: "Tipo",
        headerHint: CF_HELP.stockMovements.columns.type,
        className: "cf-table__col--status",
        render: (row) =>
          row.productType ? (
            <CfStatusBadge label={row.productType} variant="neutral" />
          ) : (
            "Sem tipo"
          ),
      },
      {
        key: "physicalValue",
        header: "Físico (armazém 99)",
        headerHint: CF_HELP.workInProcess.columns.physical,
        align: "right",
        className: "cf-table__col--numeric",
        render: (row) => (
          <span className="cf-cell-amount">
            {formatAmount(row.physicalValue)}
          </span>
        ),
      },
      {
        key: "allocatedValue",
        header: "Alocado em OPs",
        headerHint: CF_HELP.workInProcess.columns.allocatedValue,
        align: "right",
        className: "cf-table__col--numeric",
        render: (row) => (
          <span className="cf-cell-amount">
            {formatAmount(row.allocatedValue)}
          </span>
        ),
      },
      {
        key: "totalValue",
        header: "Total",
        headerHint: CF_HELP.workInProcess.columns.total,
        align: "right",
        className: "cf-table__col--numeric",
        render: (row) => (
          <span className="cf-cell-amount">
            {formatAmount(row.totalValue)}
          </span>
        ),
      },
      {
        key: "openOrderCount",
        header: "Ordens abertas",
        headerHint: CF_HELP.workInProcess.columns.openOrders,
        align: "right",
        className: "cf-table__col--numeric",
        render: (row) => formatQuantity(String(row.openOrderCount)),
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
              icon: <Factory size={20} aria-hidden />,
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
        icon: <Factory size={20} aria-hidden />,
      },
      {
        id: "dataAsOf",
        label: "Data-base",
        value: formatCivilDate(payload.dataAsOf),
        hint: `competência ${payload.period}`,
        icon: <CalendarDays size={20} aria-hidden />,
      },
      {
        id: "orders",
        label: "Linhas alocadas",
        value: String(payload.pagination.total_items),
        hint: "com ordem de produção viva",
        icon: <ScrollText size={20} aria-hidden />,
      },
      ...(payload.grandTotal !== null
        ? [
            {
              id: "total",
              label: "Total em processo",
              value: formatAmount(payload.grandTotal),
              hint: `competência ${payload.period}`,
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
          O ERP não possui fechamento de estoque registrado para{" "}
          {payload.period} — o material em processo não pode ser
          certificado. A ausência não é um saldo zero.
        </CfFeedbackMessage>
      );
    }
    if (payload.status === "incomplete") {
      return (
        <CfFeedbackMessage
          intent="warning"
          title="Dados parcialmente disponíveis"
        >
          O snapshot de {payload.period} não existe para{" "}
          {payload.branchesMissing.join(", ")} — os totais cobrem somente{" "}
          {payload.branchesAvailable.join(", ")}.
        </CfFeedbackMessage>
      );
    }
    return (
      <CfFeedbackMessage intent="info" title="Sem dados para o filtro">
        A origem respondeu, mas nenhum material em processo corresponde
        aos filtros aplicados.
      </CfFeedbackMessage>
    );
  };

  const exportDisabled =
    exporting !== null || !payload || payload.status === "source_missing";

  return (
    <section
      className="cf-page-stack cf-closing-layout"
      aria-label="Material em processo — R08"
    >
      <ClosingHero
        title={
          <CfTitleWithHelp
            title="Material em processo — R08"
            hint={CF_HELP.workInProcess.page}
          />
        }
        subtitle={
          reportContext
            ? `Material em processo da competência ${reportContext.period} · regra MATR989 (SB9 armazém 99 + ordens vivas).`
            : "Material em processo por competência e filial — regra MATR989 (SB9 armazém 99 + saldo alocado em ordens vivas)."
        }
        updatedAt={lastUpdated}
        onRefresh={retry}
        refreshing={loading}
        metrics={heroMetrics}
        notice={
          <CfFeedbackMessage intent="info" title="Paridade pendente">
            Mesma composição MATR989 certificada pelo motor P7 (bloco
            físico do armazém 99 + saldo alocado em ordens vivas). A
            homologação por competência contra nova emissão oficial ainda
            está pendente — os valores não são selo oficial.
          </CfFeedbackMessage>
        }
        filters={
          <form
            className="cf-settlements-filters"
            onSubmit={(event) => event.preventDefault()}
          >
            <CfSegmentToggle<StockInventoryScope>
              options={SCOPE_OPTIONS}
              value={reportScope}
              onChange={setReportScope}
              ariaLabel="Visão do relatório"
              size="sm"
            />
            <FiltersRow>
              {reportContext ? null : (
                <FilterInputField
                  id="cf-r08-period"
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
                id="cf-r08-warehouse"
                label="Armazém"
                type="text"
                value={warehouse}
                onChange={setWarehouse}
                placeholder="Código do armazém"
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
              title={CF_HELP.workInProcess.export}
            >
              <Download size={16} aria-hidden />{" "}
              {exporting === "csv" ? "Exportando…" : "Exportar CSV"}
            </CfActionButton>
            <CfActionButton
              variant="ghost"
              type="button"
              onClick={() => handleExport("pdf")}
              disabled={exportDisabled}
              title={CF_HELP.workInProcess.export}
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
            dataset="o material em processo"
            onRetry={retry}
          />
        ) : null}
        {renderStatusBanner()}

        {payload && payload.status !== "source_missing" ? (
          <CfSectionCard
            title="Composição — material em processo"
            hint={CF_HELP.workInProcess.totals}
          >
            <CfMetricStrip
              aria-label="Totalizadores do material em processo"
              items={[
                {
                  id: "physical",
                  label: "Físico (armazém 99)",
                  value:
                    payload.physicalTotal !== null
                      ? formatAmount(payload.physicalTotal)
                      : "—",
                  description: "bloco sem ordem de produção",
                },
                {
                  id: "allocated",
                  label: "Alocado em OPs",
                  value:
                    payload.allocatedTotal !== null
                      ? formatAmount(payload.allocatedTotal)
                      : "—",
                  description: "saldo líquido em ordens vivas",
                },
                {
                  id: "grand",
                  label: "Total em processo",
                  value:
                    payload.grandTotal !== null
                      ? formatAmount(payload.grandTotal)
                      : "—",
                  description:
                    payload.reportScope === "mp_pi_pa"
                      ? "escopo MP / PI / PA"
                      : "todos os produtos",
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

        {!applied ? (
          <CfEmptyState
            classNames={cfEmptyStateClassNames}
            defaultMessage="Informe uma competência válida para ver o material em processo."
          />
        ) : null}

        {payload &&
        payload.status !== "source_missing" &&
        payload.summariesByType.length > 0 ? (
          <DataTableSection<WorkInProcessTypeSummary>
            title="Resumo por tipo de produto"
            titleHint={CF_HELP.workInProcess.summaryType}
            columns={typeColumns}
            rows={payload.summariesByType}
            rowKey={(row) => row.productType ?? "sem-tipo"}
            loading={loading}
            hideSearch
            emptyMessage="Nenhum agrupamento por tipo para os filtros aplicados."
            columnPreferencesKey="cf:closing:wip-type-summary:v1"
          />
        ) : null}

        {payload?.status !== "source_missing" ? (
          <DataTableSection<WorkInProcessItem>
            title="Saldo alocado por ordem de produção"
            titleHint={CF_HELP.workInProcess.table}
            columns={itemColumns}
            rows={payload?.items ?? []}
            rowKey={(row) =>
              `${row.branchCode}-${row.productionOrder}-${row.productCode}`
            }
            loading={loading}
            hideSearch
            serverPagination={
              payload
                ? {
                    page: payload.pagination.page,
                    pageSize: payload.pagination.page_size,
                    total: payload.pagination.total_items,
                    onPageChange: setPage,
                  }
                : undefined
            }
            emptyMessage="Nenhum saldo alocado a ordens de produção para os filtros aplicados."
            columnPreferencesKey="cf:closing:work-in-process:v1"
          />
        ) : null}
      </div>
    </section>
  );
}
