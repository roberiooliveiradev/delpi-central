/**
 * Entradas e Saídas — R05 (MATR320) — Central de Fechamento.
 *
 * Consome `GET /closing/stock-movements` da BFF — resumo por tipo de
 * produto com as 13 colunas do MATR320 (movimentos SD1/SD2/SD3/SF4 +
 * saldo SB9). Saldo inicial é coluna derivada (SA − movimento líquido),
 * transferências para processo são memo. `source_missing`/`incomplete`
 * são estados próprios — nunca zero fabricado. Paridade MATR320
 * declarada pendente até homologação por competência.
 */
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { ApiError } from "../../api/httpClient";
import { saveDocumentBlob } from "../../api/documentsApi";
import {
  exportStockMovements,
  getStockMovements,
  stockMovementsExportFilename,
  type StockMovementsPayload,
  type StockMovementsTypeRow,
} from "../../api/stockMovementsApi";
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
  ArrowDownUp,
  Building2,
  CalendarDays,
  CircleDollarSign,
  Download,
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
import { formatAmount, formatCivilDate } from "../../utils/formatters";
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
};

type FetchState =
  | { kind: "error"; status: number; code: string | null; message: string }
  | { kind: "ready"; payload: StockMovementsPayload };

type FetchResult = { key: string } & FetchState;

export type StockMovementsReportContext = { period: string };

function moneyColumn(
  key: keyof StockMovementsTypeRow,
  header: string,
): DataTableColumn<StockMovementsTypeRow> {
  return {
    key: String(key),
    header,
    align: "right",
    className: "cf-table__col--numeric",
    render: (row) => {
      const value = row[key];
      return value !== null && value !== undefined ? (
        <span className="cf-cell-amount">{formatAmount(value)}</span>
      ) : (
        "—"
      );
    },
  };
}

export function StockMovementsPage({
  reportContext,
}: {
  reportContext?: StockMovementsReportContext;
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
        ? { period: effectivePeriod, branch, reportScope }
        : null,
    [filtersValid, effectivePeriod, branch, reportScope],
  );

  const clearFilters = useCallback(() => {
    setPeriod(reportContext?.period ?? currentCompetence());
    setBranch("all");
    setReportScope("all_products");
  }, [reportContext]);

  const retry = useCallback(() => setRetryNonce((n) => n + 1), []);

  const handleExport = useCallback(
    async (format: "csv" | "pdf") => {
      if (!applied || exporting) return;
      setExporting(format);
      setExportError(null);
      try {
        const blob = await exportStockMovements(applied, format);
        saveDocumentBlob(
          blob,
          stockMovementsExportFilename(applied, format),
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
  const hydrateFromUrl = useCallback((params: URLSearchParams) => {
    const parsed = parseStockQuery(params);
    setBranch(parsed.branch);
    setReportScope(parsed.scope);
  }, []);
  useReportQuerySync({
    enabled: Boolean(reportContext),
    serialize: () => {
      const query = serializeStockQuery({
        branch,
        scope: reportScope,
        warehouse: "",
        page: 1,
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
    getStockMovements(applied, { signal: controller.signal })
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
              : "Falha de comunicação com a API de entradas e saídas.",
        });
      });
    return () => controller.abort();
  }, [applied, queryKey]);

  const columns = useMemo<DataTableColumn<StockMovementsTypeRow>[]>(
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
      moneyColumn("openingBalance", "Saldo inicial"),
      moneyColumn("purchases", "Compras"),
      moneyColumn("internalMovements", "Mov. internas"),
      moneyColumn("productionRequisitions", "Requisições"),
      moneyColumn("transfers", "Transferências"),
      moneyColumn("production", "Produção"),
      moneyColumn("sales", "Vendas"),
      moneyColumn("processTransfersMemo", "Transf. processo (memo)"),
      moneyColumn("salesReturns", "Dev. vendas"),
      moneyColumn("purchaseReturns", "Dev. compras"),
      moneyColumn("thirdPartyIn", "Ent. poder 3º"),
      moneyColumn("thirdPartyOut", "Saí. poder 3º"),
      moneyColumn("closingBalance", "Saldo atual"),
      moneyColumn("netMovement", "Movimento líquido"),
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
        id: "types",
        label: "Tipos de produto",
        value: String(payload.rows.length),
        hint:
          payload.reportScope === "mp_pi_pa"
            ? "MP / PI / PA"
            : "todos os produtos",
        icon: <Building2 size={20} aria-hidden />,
      },
      ...(payload.totals.closingBalance != null
        ? [
            {
              id: "total",
              label: "Saldo atual total",
              value: formatAmount(payload.totals.closingBalance),
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
          {payload.period} — os movimentos do período são exibidos, mas o
          saldo atual não pode ser certificado. A ausência não é um saldo
          zero.
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
          {payload.branchesMissing.join(", ")} — os saldos cobrem somente{" "}
          {payload.branchesAvailable.join(", ")}.
        </CfFeedbackMessage>
      );
    }
    return (
      <CfFeedbackMessage intent="info" title="Sem dados para o filtro">
        A origem respondeu, mas nenhum tipo de produto corresponde aos
        filtros aplicados.
      </CfFeedbackMessage>
    );
  };

  const exportDisabled =
    exporting !== null || !payload || payload.status === "source_missing";

  return (
    <section
      className="cf-page-stack cf-closing-layout"
      aria-label="Entradas e saídas — R05"
    >
      <ClosingHero
        title={
          <CfTitleWithHelp
            title="Entradas e saídas — R05"
            hint={CF_HELP.stockMovements.page}
          />
        }
        subtitle={
          reportContext
            ? `Resumo de movimentações da competência ${reportContext.period} · regra MATR320 (SD1/SD2/SD3 + SB9).`
            : "Resumo de movimentações por competência, filial e tipo de produto — regra MATR320 (SD1/SD2/SD3 + SB9)."
        }
        updatedAt={lastUpdated}
        onRefresh={retry}
        refreshing={loading}
        metrics={heroMetrics}
        notice={
          <CfFeedbackMessage intent="info" title="Paridade pendente">
            Regra MATR320 comprovada célula a célula na competência de
            referência; a homologação por competência contra nova emissão
            oficial ainda está pendente — os valores não são selo oficial.
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
                  id="cf-r05-period"
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
              title={CF_HELP.stockMovements.export}
            >
              <Download size={16} aria-hidden />{" "}
              {exporting === "csv" ? "Exportando…" : "Exportar CSV"}
            </CfActionButton>
            <CfActionButton
              variant="ghost"
              type="button"
              onClick={() => handleExport("pdf")}
              disabled={exportDisabled}
              title={CF_HELP.stockMovements.export}
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
            dataset="o resumo de entradas e saídas"
            onRetry={retry}
          />
        ) : null}
        {renderStatusBanner()}

        {payload && payload.status !== "source_missing" ? (
          <CfSectionCard
            title="Totais do período"
            hint={CF_HELP.stockMovements.totals}
          >
            <CfMetricStrip
              aria-label="Totais do resumo de movimentações"
              items={[
                {
                  id: "opening",
                  label: "Saldo inicial",
                  value:
                    payload.totals.openingBalance != null
                      ? formatAmount(payload.totals.openingBalance)
                      : "—",
                  description: "derivado: saldo atual − movimento líquido",
                },
                {
                  id: "net",
                  label: "Movimento líquido",
                  value:
                    payload.totals.netMovement != null
                      ? formatAmount(payload.totals.netMovement)
                      : "—",
                  description: "entradas − saídas da competência",
                },
                {
                  id: "closing",
                  label: "Saldo atual",
                  value:
                    payload.totals.closingBalance != null
                      ? formatAmount(payload.totals.closingBalance)
                      : "—",
                  description: "snapshot SB9 — todos os armazéns",
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
            defaultMessage="Informe uma competência válida para ver o resumo de movimentações."
          />
        ) : null}

        {payload?.status !== "source_missing" ? (
          <DataTableSection<StockMovementsTypeRow>
            title="Resumo por tipo de produto"
            titleHint={CF_HELP.stockMovements.table}
            columns={columns}
            rows={payload?.rows ?? []}
            rowKey={(row) => row.productType ?? "sem-tipo"}
            loading={loading}
            hideSearch
            emptyMessage="Nenhum tipo de produto com movimentação no período para os filtros aplicados."
            columnPreferencesKey="cf:closing:stock-movements:v1"
          />
        ) : null}
      </div>
    </section>
  );
}
