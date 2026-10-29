/**
 * Estoque histórico — P7 (R03) — Central de Fechamento.
 *
 * Consome `GET /closing/stock-inventory` da BFF. Motor P7 do Portal —
 * composição oficial do registro de inventário (EM ESTOQUE + EM
 * PROCESSO) calculada sobre SB9 + MATR989. Paridade com a emissão
 * MATR460 declarada como pendente até homologação por competência —
 * nunca apresentada como selo oficial. `source_missing`/`incomplete`
 * são estados próprios — nunca confundidos com total zero nem com erro.
 */
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { ApiError } from "../../api/httpClient";
import { getP3State, type P3Status } from "../../api/p3Api";
import { saveDocumentBlob } from "../../api/documentsApi";
import {
  exportStockInventory,
  getStockInventory,
  stockInventoryExportFilename,
  type StockInventoryBranch,
  type StockInventoryItem,
  type StockInventoryPayload,
  type StockInventoryScope,
  type StockInventoryTypeSummary,
  type StockInventoryWarehouseSummary,
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
  Boxes,
  Building2,
  CalendarDays,
  CircleDollarSign,
  Download,
  Package,
} from "lucide-react";
import {
  ClosingHero,
  type ClosingHeroMetric,
} from "../../app/ClosingHero";
import {
  CfFeedbackMessage,
  CfQueryErrorBanner,
} from "../../app/cfFeedbackUi";
import { DataTableSection, type DataTableColumn } from "../../app/cfDataTableUi";
import {
  FilterInputField,
  FilterSelectField,
  FiltersRow,
} from "../../app/cfFiltersUi";
import { CF_HELP } from "../../content/helpTooltips";
import {
  formatCivilDate,
  formatQuantity,
  formatAmount,
  formatSharePercent,
} from "../../utils/formatters";
import { useDebouncedValue } from "../../utils/useDebouncedValue";
import {
  P3ReconciliationSection,
} from "./ReportSharedSections";
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
  no_matching_items: "Sem itens para o filtro",
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
  | { kind: "ready"; payload: StockInventoryPayload };

type FetchResult = { key: string } & FetchState;

/**
 * Contexto do relatório dentro do Fechamento Mensal (UX-011): a
 * competência vem da rota contextual e não é filtro editável; o modo
 * exibe a conciliação P3 canônica, agrupamentos em tabela e o slot PDF.
 */
export type StockInventoryReportContext = { period: string };

export function StockInventoryPage({
  reportContext,
}: {
  reportContext?: StockInventoryReportContext;
}) {
  const [period, setPeriod] = useState(
    () => reportContext?.period ?? currentCompetence(),
  );
  // RW01: no modo contextual os filtros iniciais vêm da query da rota —
  // a competência continua travada pela rota (nunca serializada).
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

  const debouncedWarehouse = useDebouncedValue(warehouse.trim(), DEBOUNCE_MS);

  const [page, setPage] = useState(() => urlInit?.page ?? 1);
  const [result, setResult] = useState<FetchResult | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [retryNonce, setRetryNonce] = useState(0);
  const [exporting, setExporting] = useState<"csv" | "pdf" | null>(null);
  const [exportError, setExportError] = useState<string | null>(null);
  const requestId = useRef(0);
  const [p3Result, setP3Result] = useState<{
    key: string;
    data: P3Status | null;
  } | null>(null);
  const p3RequestId = useRef(0);

  // Competência travada no modo contextual — não é filtro editável.
  const effectivePeriod = reportContext?.period ?? period;
  const filtersValid = /^\d{4}-(0[1-9]|1[0-2])$/.test(effectivePeriod);

  // Filtros vigentes: derivados diretamente dos campos (sem botão Consultar).
  // Armazém (digitável) entra com debounce; competência/filial/visão são
  // imediatos. Competência inválida => null => nenhuma consulta é disparada.
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
    [filtersValid, effectivePeriod, branch, reportScope, debouncedWarehouse],
  );

  // Volta para a página 1 quando o universo de filtros muda — ajuste em
  // render-time para que o efeito de fetch veja (applied, page=1) juntos,
  // sem gerar consulta duplicada.
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

  // Export do mesmo motor (doc 119 §8.C) — o arquivo carrega a marca
  // de paridade vigente; nunca promove o recorte a documento oficial
  // enquanto a homologação MATR460 estiver pendente.
  const handleExport = useCallback(
    async (format: "csv" | "pdf") => {
      if (!applied || exporting) return;
      setExporting(format);
      setExportError(null);
      try {
        const blob = await exportStockInventory(applied, format);
        saveDocumentBlob(
          blob,
          stockInventoryExportFilename(applied, format),
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

  // RW01: query da rota espelha os campos brutos — reidratação por
  // popstate nunca regrava valor ainda em debounce na URL.
  const hydrateFromUrl = useCallback((params: URLSearchParams) => {
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
  }, [effectivePeriod]);
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

    getStockInventory(
      {
        period: applied.period,
        branch: applied.branch,
        reportScope: applied.reportScope,
        warehouse: applied.warehouse || undefined,
        page,
        pageSize: PAGE_SIZE,
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
        const detail =
          error instanceof ApiError
            ? {
                status: error.status,
                code: error.code,
                message: error.message,
              }
            : {
                status: 0,
                code: null,
                message: "Falha de comunicação com a API de estoque.",
              };
        setResult({ key: queryKey, kind: "error", ...detail });
      });

    return () => controller.abort();
  }, [applied, page, queryKey]);

  // Conciliação P3 da competência — somente no modo contextual; o estado
  // honesto (`null`/erro) é renderizado pela seção, nunca como zero.
  const p3Key = `p3:${reportContext?.period ?? ""}:${retryNonce}`;
  const p3 = p3Result?.key === p3Key ? p3Result.data : null;
  const p3Loading = Boolean(reportContext) && p3Result?.key !== p3Key;

  useEffect(() => {
    if (!reportContext) return;
    const id = ++p3RequestId.current;
    const controller = new AbortController();
    getP3State(reportContext.period, controller.signal)
      .then((data) => {
        if (controller.signal.aborted || p3RequestId.current !== id) return;
        setP3Result({ key: p3Key, data: data ?? null });
      })
      .catch(() => {
        if (controller.signal.aborted || p3RequestId.current !== id) return;
        setP3Result({ key: p3Key, data: null });
      });
    return () => controller.abort();
  }, [reportContext, p3Key]);

  const columns = useMemo<DataTableColumn<StockInventoryItem>[]>(
    () => [
      {
        key: "productCode",
        header: "Produto",
        headerHint: CF_HELP.stockInventory.columns.product,
        className: "cf-table__col--compact",
        render: (row) =>
          row.productCode ? (
            <span className="cf-cell-primary">{row.productCode}</span>
          ) : (
            "—"
          ),
      },
      {
        key: "description",
        header: "Descrição",
        headerHint: CF_HELP.stockInventory.columns.description,
        className: "cf-table__col--wrap",
        render: (row) =>
          row.description ? (
            <span title={row.description}>{row.description}</span>
          ) : (
            "—"
          ),
      },
      {
        key: "productType",
        header: "Tipo",
        headerHint: CF_HELP.stockInventory.columns.type,
        className: "cf-table__col--status",
        render: (row) =>
          row.productType ? (
            <CfStatusBadge label={row.productType} variant="neutral" />
          ) : (
            "—"
          ),
      },
      {
        key: "productGroup",
        header: "Grupo",
        headerHint: CF_HELP.stockInventory.columns.group,
        className: "cf-table__col--compact",
        render: (row) => row.productGroup ?? "—",
      },
      {
        key: "unit",
        header: "UM",
        headerHint: CF_HELP.stockInventory.columns.um,
        mobileLabel: "Unidade",
        className: "cf-table__col--compact",
        render: (row) => row.unit ?? "—",
      },
      {
        key: "warehouse",
        header: "Armazém",
        headerHint: CF_HELP.stockInventory.columns.warehouse,
        className: "cf-table__col--compact",
        render: (row) => row.warehouse ?? "—",
      },
      {
        key: "branchCode",
        header: "Filial",
        headerHint: CF_HELP.stockInventory.columns.branch,
        className: "cf-table__col--compact",
        render: (row) =>
          row.branchCode ? (
            `Filial ${row.branchCode}`
          ) : (
            <span className="cf-cell-muted">Não identificada</span>
          ),
      },
      {
        key: "historicalQuantity",
        header: "Quantidade",
        headerHint: CF_HELP.stockInventory.columns.quantity,
        align: "right",
        className: "cf-table__col--numeric",
        render: (row) => formatQuantity(row.historicalQuantity),
      },
      {
        key: "historicalStockValue",
        header: "Valor histórico",
        headerHint: CF_HELP.stockInventory.columns.historicalValue,
        align: "right",
        className: "cf-table__col--numeric",
        render: (row) => (
          <span className="cf-cell-amount">
            {formatAmount(row.historicalStockValue)}
          </span>
        ),
      },
    ],
    [],
  );

  // KPIs do hero — somente métricas presentes no payload (doc 50 §4).
  const heroMetrics = useMemo<ClosingHeroMetric[] | undefined>(() => {
    if (!payload) {
      return loading
        ? [
            {
              id: "status",
              label: "Disponibilidade",
              value: "",
              icon: <Package size={20} aria-hidden />,
            },
            {
              id: "dataAsOf",
              label: "Data-base",
              value: "",
              icon: <CalendarDays size={20} aria-hidden />,
            },
            {
              id: "items",
              label: "Itens",
              value: "",
              icon: <Boxes size={20} aria-hidden />,
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
        icon: <Package size={20} aria-hidden />,
      },
      {
        id: "dataAsOf",
        label: "Data-base",
        value: formatCivilDate(payload.dataAsOf),
        hint: `competência ${payload.period}`,
        icon: <CalendarDays size={20} aria-hidden />,
      },
      {
        id: "items",
        label: "Itens",
        value: String(payload.pagination.total_items),
        hint:
          payload.reportScope === "mp_pi_pa"
            ? "MP / PI / PA"
            : "todos os produtos",
        icon: <Boxes size={20} aria-hidden />,
      },
      ...(payload.branchCode === "all"
        ? [
            {
              id: "branches",
              label: "Filiais com dados",
              value: String(payload.branchesAvailable.length),
              hint: `de ${
                payload.branchesAvailable.length +
                payload.branchesMissing.length
              } filiais`,
              icon: <Building2 size={20} aria-hidden />,
            },
          ]
        : []),
      ...(payload.historicalTotal !== null
        ? [
            {
              id: "total",
              label: "Valor histórico total",
              value: formatAmount(payload.historicalTotal),
              hint: `competência ${payload.period}`,
              icon: <CircleDollarSign size={20} aria-hidden />,
            },
          ]
        : []),
    ];
  }, [payload, loading]);

  // Tabelas de agrupamento do modo contextual (UX-011 §10) — mesmas
  // coleções do contrato, agora com colunas explícitas em vez de strip.
  const typeColumns = useMemo<DataTableColumn<StockInventoryTypeSummary>[]>(
    () => [
      {
        key: "productType",
        header: "Tipo",
        headerHint: CF_HELP.stockInventory.columns.type,
        className: "cf-table__col--status",
        render: (group) =>
          group.productType ? (
            <CfStatusBadge label={group.productType} variant="neutral" />
          ) : (
            "Sem tipo"
          ),
      },
      {
        key: "itemCount",
        header: "Itens",
        headerHint: CF_HELP.stockInventory.columns.items,
        align: "right",
        className: "cf-table__col--numeric",
        render: (group) => formatQuantity(String(group.itemCount)),
      },
      {
        key: "totalQuantity",
        header: "Quantidade",
        headerHint: CF_HELP.stockInventory.columns.quantity,
        align: "right",
        className: "cf-table__col--numeric",
        render: (group) => formatQuantity(group.totalQuantity),
      },
      {
        key: "totalStockValue",
        header: "Valor",
        headerHint: CF_HELP.stockInventory.columns.historicalValue,
        align: "right",
        className: "cf-table__col--numeric",
        render: (group) => (
          <span className="cf-cell-amount">
            {formatAmount(group.totalStockValue)}
          </span>
        ),
      },
      {
        key: "share",
        header: "% do total",
        headerHint: CF_HELP.stockInventory.columns.percent,
        align: "right",
        className: "cf-table__col--numeric",
        render: (group) =>
          formatSharePercent(
            group.totalStockValue,
            payload?.historicalTotal ?? null,
          ) ?? "—",
      },
    ],
    [payload?.historicalTotal],
  );

  const warehouseColumns = useMemo<
    DataTableColumn<StockInventoryWarehouseSummary>[]
  >(
    () => [
      {
        key: "warehouse",
        header: "Armazém",
        headerHint: CF_HELP.stockInventory.columns.warehouse,
        className: "cf-table__col--compact",
        render: (group) => group.warehouse ?? "—",
      },
      {
        key: "branchCode",
        header: "Filial",
        headerHint: CF_HELP.stockInventory.columns.branch,
        className: "cf-table__col--compact",
        render: (group) =>
          group.branchCode ? `Filial ${group.branchCode}` : "—",
      },
      {
        key: "itemCount",
        header: "Itens",
        headerHint: CF_HELP.stockInventory.columns.items,
        align: "right",
        className: "cf-table__col--numeric",
        render: (group) => formatQuantity(String(group.itemCount)),
      },
      {
        key: "totalQuantity",
        header: "Quantidade",
        headerHint: CF_HELP.stockInventory.columns.quantity,
        align: "right",
        className: "cf-table__col--numeric",
        render: (group) => formatQuantity(group.totalQuantity),
      },
      {
        key: "totalStockValue",
        header: "Valor",
        headerHint: CF_HELP.stockInventory.columns.historicalValue,
        align: "right",
        className: "cf-table__col--numeric",
        render: (group) => (
          <span className="cf-cell-amount">
            {formatAmount(group.totalStockValue)}
          </span>
        ),
      },
      {
        key: "share",
        header: "% do total",
        headerHint: CF_HELP.stockInventory.columns.percent,
        align: "right",
        className: "cf-table__col--numeric",
        render: (group) =>
          formatSharePercent(
            group.totalStockValue,
            payload?.historicalTotal ?? null,
          ) ?? "—",
      },
    ],
    [payload?.historicalTotal],
  );

  const renderStatusBanner = () => {
    if (!payload || payload.status === "available") return null;
    if (payload.status === "source_missing") {
      return (
        <CfFeedbackMessage intent="warning" title="Snapshot não encontrado">
          O ERP não possui fechamento de estoque registrado para{" "}
          {payload.period}
          {payload.branchesMissing.length > 0
            ? ` na filial ${payload.branchesMissing.join(", ")}`
            : ""}
          . Consulte outra competência ou filial — a ausência não é um saldo
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
          {payload.branchesMissing.length === 1
            ? `a filial ${payload.branchesMissing[0]}`
            : `as filiais ${payload.branchesMissing.join(", ")}`}
          . Os totais abaixo cobrem somente{" "}
          {payload.branchesAvailable.length === 1
            ? `a filial ${payload.branchesAvailable[0]}`
            : `as filiais ${payload.branchesAvailable.join(", ")}`}
          .
        </CfFeedbackMessage>
      );
    }
    return (
      <CfFeedbackMessage intent="info" title="Sem itens para o filtro">
        O snapshot de {payload.period} existe, mas nenhum item corresponde aos
        filtros aplicados.
      </CfFeedbackMessage>
    );
  };

  const showData = payload !== null || loading;

  return (
    <section
      className="cf-page-stack cf-closing-layout"
      aria-label="Estoque histórico — P7"
    >
      <ClosingHero
        title={
          <CfTitleWithHelp
            title="Estoque histórico — P7"
            hint={CF_HELP.stockInventory.page}
          />
        }
        subtitle={
          reportContext
            ? `Registro de inventário da competência ${reportContext.period} · Motor P7 (TOTVS/SB9 + MATR989) + conciliação P3.`
            : "Registro de inventário por competência, filial e classificação de produto — motor P7 (SB9 + MATR989)."
        }
        updatedAt={lastUpdated}
        onRefresh={retry}
        refreshing={loading}
        metrics={heroMetrics}
        notice={
          <CfFeedbackMessage intent="info" title="Paridade pendente">
            Composição oficial do P7 calculada pelo motor do Portal
            (SB9 + MATR989). A homologação por competência contra nova
            emissão MATR460 ainda está pendente — os valores não são selo
            oficial.
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
              ariaLabel="Visão do estoque"
              size="sm"
            />
            <FiltersRow>
              {reportContext ? null : (
                <FilterInputField
                  id="cf-stock-period"
                  label="Competência"
                  type="month"
                  value={period}
                  onChange={setPeriod}
                />
              )}
              <FilterSelectField
                label="Filial"
                value={branch}
                onChange={(value) => setBranch(value as StockInventoryBranch)}
                options={BRANCH_OPTIONS}
              />
              <FilterInputField
                id="cf-stock-warehouse"
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
              disabled={
                exporting !== null ||
                !payload ||
                payload.status === "source_missing"
              }
              title={CF_HELP.stockInventory.export}
            >
              <Download size={16} aria-hidden />{" "}
              {exporting === "csv" ? "Exportando…" : "Exportar CSV"}
            </CfActionButton>
            <CfActionButton
              variant="ghost"
              type="button"
              onClick={() => handleExport("pdf")}
              disabled={
                exporting !== null ||
                !payload ||
                payload.status === "source_missing"
              }
              title={CF_HELP.stockInventory.export}
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
          dataset="o estoque histórico"
          onRetry={retry}
        />
      ) : null}
      {renderStatusBanner()}

      {/* UX-011: conciliação canônica ENTRADAS_SAIDAS − P7 − H02 vem
          primeiro na página do relatório — valores calculados pelo
          backend, nunca derivados no navegador. */}
      {reportContext ? (
        <P3ReconciliationSection
          p3={p3}
          loading={p3Loading}
          p7OperationalAvailable={
            !!payload && payload.status !== "source_missing"
          }
        />
      ) : null}

      {/* Totalizadores oficiais do registro (doc 119 §8): EM ESTOQUE +
          EM PROCESSO = TOTAL — sempre sobre o universo do escopo, nunca
          reduzidos pelo filtro de Armazém. */}
      {showData &&
      payload &&
      payload.status !== "source_missing" &&
      payload.grandTotal != null ? (
        <CfSectionCard
          title="Composição do registro — P7"
          hint={CF_HELP.stockInventory.totals}
        >
          <CfMetricStrip
            aria-label="Totalizadores do registro de inventário"
            items={[
              {
                id: "stock",
                label: "Em estoque",
                value: payload.stockTotal
                  ? formatAmount(payload.stockTotal)
                  : "—",
                description: "saldos fora do armazém de processo",
              },
              {
                id: "process",
                label: "Em processo",
                value: payload.processTotal
                  ? formatAmount(payload.processTotal)
                  : "—",
                description: `armazém ${payload.provenance?.processWarehouse ?? "99"}: ${payload.processPhysicalTotal ? formatAmount(payload.processPhysicalTotal) : "—"} · alocado em OPs: ${payload.processAllocatedTotal ? formatAmount(payload.processAllocatedTotal) : "—"}`,
              },
              {
                id: "grand",
                label: "Total geral",
                value: payload.grandTotal
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
          defaultMessage="Informe uma competência válida para ver o estoque histórico."
        />
      ) : null}

      {reportContext &&
      showData &&
      payload &&
      payload.status !== "source_missing" &&
      payload.summariesByType.length > 0 ? (
        <DataTableSection<StockInventoryTypeSummary>
          title="Resumo por tipo de produto"
          titleHint={CF_HELP.stockInventory.summaryType}
          columns={typeColumns}
          rows={payload.summariesByType}
          rowKey={(group) => group.productType ?? "sem-tipo"}
          loading={loading}
          hideSearch
          emptyMessage="Nenhum agrupamento por tipo para os filtros aplicados."
          columnPreferencesKey="cf:closing:stock-type-summary:v1"
        />
      ) : null}
      {reportContext &&
      showData &&
      payload &&
      payload.status !== "source_missing" &&
      payload.summariesByWarehouse.length > 0 ? (
        <DataTableSection<StockInventoryWarehouseSummary>
          title="Resumo por armazém"
          titleHint={CF_HELP.stockInventory.summaryWarehouse}
          columns={warehouseColumns}
          rows={payload.summariesByWarehouse}
          rowKey={(group) =>
            `${group.branchCode ?? ""}-${group.warehouse ?? "sem-armazem"}`
          }
          loading={loading}
          hideSearch
          emptyMessage="Nenhum agrupamento por armazém para os filtros aplicados."
          columnPreferencesKey="cf:closing:stock-warehouse-summary:v1"
        />
      ) : null}

      {showData &&
      payload &&
      !reportContext &&
      (payload.summariesByType.length > 0 ||
        payload.summariesByWarehouse.length > 0) ? (
        <div className="cf-summary-panels">
          {payload.summariesByType.length > 0 ? (
            <CfSectionCard
              className="cf-summary-card--type"
              title="Resumo por tipo de produto"
              hint={CF_HELP.stockInventory.summaryType}
            >
              <CfMetricStrip
                aria-label="Resumo por tipo de produto"
                items={payload.summariesByType.map((group) => {
                  const share = formatSharePercent(
                    group.totalStockValue,
                    payload.historicalTotal,
                  );
                  return {
                    id: group.productType ?? "sem-tipo",
                    label: group.productType ?? "Sem tipo",
                    value: formatAmount(group.totalStockValue),
                    description: `${group.itemCount} itens${
                      share ? ` · ${share} do total` : ""
                    }`,
                  };
                })}
              />
            </CfSectionCard>
          ) : null}
          {payload.summariesByWarehouse.length > 0 ? (
            <CfSectionCard
              className="cf-summary-card--warehouse"
              title="Resumo por armazém"
              hint={CF_HELP.stockInventory.summaryWarehouse}
            >
              <CfMetricStrip
                aria-label="Resumo por armazém"
                items={payload.summariesByWarehouse.map((group) => {
                  const share = formatSharePercent(
                    group.totalStockValue,
                    payload.historicalTotal,
                  );
                  return {
                    id: `${group.branchCode ?? ""}-${group.warehouse ?? "sem-armazem"}`,
                    label: `Armazém ${group.warehouse ?? "—"} · Filial ${group.branchCode ?? "—"}`,
                    value: formatAmount(group.totalStockValue),
                    description: `${group.itemCount} itens${
                      share ? ` · ${share} do total` : ""
                    }`,
                  };
                })}
              />
            </CfSectionCard>
          ) : null}
        </div>
      ) : null}

      {/* T18: sem snapshot, só o banner — a tabela vazia sugeriria
          «nenhum item» quando na verdade não há dados para a competência. */}
      {showData && payload?.status !== "source_missing" ? (
        <DataTableSection<StockInventoryItem>
          title="Detalhamento por produto e armazém"
          titleHint={CF_HELP.stockInventory.table}
          columns={columns}
          rows={payload?.items ?? []}
          rowKey={(row) =>
            `${row.branchCode}-${row.warehouse}-${row.productCode}`
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
          emptyMessage="Nenhum item de estoque encontrado para os filtros aplicados."
          columnPreferencesKey={`cf:closing:stock-inventory:${applied?.reportScope ?? "all_products"}:v1`}
          fontSizePreferencesKey="cf:closing:stock-inventory:font:v1"
          resizableColumns
        />
      ) : null}
      </div>

    </section>
  );
}
