/**
 * Estoque histórico — P7 (R03) — Central de Fechamento.
 *
 * Consome `GET /closing/stock-inventory` da BFF. Consulta operacional do
 * snapshot mensal de estoque — nunca apresentada como relatório oficial
 * MATR460. `source_missing`/`incomplete` são estados próprios — nunca
 * confundidos com total zero nem com erro.
 */
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { ApiError } from "../../api/httpClient";
import {
  getStockInventory,
  type StockInventoryBranch,
  type StockInventoryItem,
  type StockInventoryPayload,
  type StockInventoryScope,
} from "../../api/stockInventoryApi";
import {
  CfEmptyState,
  CfMetricStrip,
  CfSectionCard,
  CfSegmentToggle,
  CfTitleWithHelp,
  cfEmptyStateClassNames,
} from "../../app/controllershipFinanceUi";
import type { PageHeroHighlight } from "@delpi/plugin-ui/index";
import { ClosingHero } from "../../app/ClosingHero";
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
} from "../../utils/formatters";
import { useDebouncedValue } from "../../utils/useDebouncedValue";

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

export function StockInventoryPage() {
  const [period, setPeriod] = useState(currentCompetence);
  const [branch, setBranch] = useState<StockInventoryBranch>("all");
  const [reportScope, setReportScope] =
    useState<StockInventoryScope>("all_products");
  const [warehouse, setWarehouse] = useState("");

  const debouncedWarehouse = useDebouncedValue(warehouse.trim(), DEBOUNCE_MS);

  const [page, setPage] = useState(1);
  const [result, setResult] = useState<FetchResult | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [retryNonce, setRetryNonce] = useState(0);
  const requestId = useRef(0);

  const filtersValid = /^\d{4}-(0[1-9]|1[0-2])$/.test(period);

  // Filtros vigentes: derivados diretamente dos campos (sem botão Consultar).
  // Armazém (digitável) entra com debounce; competência/filial/visão são
  // imediatos. Competência inválida => null => nenhuma consulta é disparada.
  const applied: AppliedFilters | null = useMemo(
    () =>
      filtersValid
        ? { period, branch, reportScope, warehouse: debouncedWarehouse }
        : null,
    [filtersValid, period, branch, reportScope, debouncedWarehouse],
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
    setPeriod(currentCompetence());
    setBranch("all");
    setReportScope("all_products");
    setWarehouse("");
  }, []);

  const retry = useCallback(() => setRetryNonce((n) => n + 1), []);

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

  const columns = useMemo<DataTableColumn<StockInventoryItem>[]>(
    () => [
      {
        key: "productCode",
        header: "Produto",
        render: (row) => row.productCode || "—",
      },
      {
        key: "description",
        header: "Descrição",
        render: (row) => row.description ?? "—",
      },
      {
        key: "productType",
        header: "Tipo",
        render: (row) => row.productType ?? "—",
      },
      {
        key: "productGroup",
        header: "Grupo",
        render: (row) => row.productGroup ?? "—",
      },
      {
        key: "unit",
        header: "UM",
        render: (row) => row.unit ?? "—",
      },
      {
        key: "warehouse",
        header: "Armazém",
        render: (row) => row.warehouse ?? "—",
      },
      {
        key: "branchCode",
        header: "Filial",
        render: (row) => row.branchCode ?? "—",
      },
      {
        key: "historicalQuantity",
        header: "Quantidade",
        align: "right",
        render: (row) => formatQuantity(row.historicalQuantity),
      },
      {
        key: "historicalStockValue",
        header: "Valor histórico",
        align: "right",
        render: (row) => formatAmount(row.historicalStockValue),
      },
    ],
    [],
  );

  // KPIs do hero — somente métricas presentes no payload (doc 50 §4).
  const heroHighlights = useMemo<PageHeroHighlight[] | undefined>(() => {
    if (!payload) {
      return loading
        ? [
            { id: "status", label: "Disponibilidade", value: "", loading: true },
            { id: "dataAsOf", label: "Data-base", value: "", loading: true },
            { id: "items", label: "Itens", value: "", loading: true },
          ]
        : undefined;
    }
    return [
      {
        id: "status",
        label: "Disponibilidade",
        value: STATUS_LABELS[payload.status] ?? payload.status,
        tone: payload.status === "available" ? "neutral" : "warning",
      },
      {
        id: "dataAsOf",
        label: "Data-base",
        value: formatCivilDate(payload.dataAsOf),
      },
      {
        id: "items",
        label: "Itens",
        value: String(payload.pagination.total_items),
      },
      ...(payload.branchCode === "all"
        ? [
            {
              id: "branches",
              label: "Filiais com dados",
              value: String(payload.branchesAvailable.length),
            },
          ]
        : []),
      ...(payload.historicalTotal !== null
        ? [
            {
              id: "total",
              label: "Valor histórico total",
              value: formatAmount(payload.historicalTotal),
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
        subtitle="Consulta operacional dos saldos históricos por competência, filial e classificação de produto."
        updatedAt={lastUpdated}
        onRefresh={retry}
        refreshing={loading}
        highlights={heroHighlights}
        notice={
          <CfFeedbackMessage intent="info" title="Consulta operacional">
            Os resultados ainda não equivalem ao relatório oficial MATR460.
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
              <FilterInputField
                id="cf-stock-period"
                label="Competência"
                type="month"
                value={period}
                onChange={setPeriod}
              />
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
      />

      <div className="cf-page-stack" aria-busy={loading}>
      {current?.kind === "error" ? (
        <CfQueryErrorBanner
          error={current}
          dataset="o estoque histórico"
          onRetry={retry}
        />
      ) : null}
      {renderStatusBanner()}

      {!applied ? (
        <CfEmptyState
          classNames={cfEmptyStateClassNames}
          defaultMessage="Informe uma competência válida para ver o estoque histórico."
        />
      ) : null}

      {showData && payload && payload.summariesByType.length > 0 ? (
        <CfSectionCard
          title="Resumo por tipo de produto"
          hint={CF_HELP.stockInventory.summaryType}
        >
          <CfMetricStrip
            aria-label="Resumo por tipo de produto"
            items={payload.summariesByType.map((group) => ({
              id: group.productType ?? "sem-tipo",
              label: group.productType ?? "Sem tipo",
              value: formatAmount(group.totalStockValue),
              description: `${group.itemCount} itens`,
            }))}
          />
        </CfSectionCard>
      ) : null}

      {showData && payload && payload.summariesByWarehouse.length > 0 ? (
        <CfSectionCard
          title="Resumo por armazém"
          hint={CF_HELP.stockInventory.summaryWarehouse}
        >
          <CfMetricStrip
            aria-label="Resumo por armazém"
            items={payload.summariesByWarehouse.map((group) => ({
              id: `${group.branchCode ?? ""}-${group.warehouse ?? "sem-armazem"}`,
              label: `Armazém ${group.warehouse ?? "—"} · Filial ${group.branchCode ?? "—"}`,
              value: formatAmount(group.totalStockValue),
              description: `${group.itemCount} itens`,
            }))}
          />
        </CfSectionCard>
      ) : null}

      {showData ? (
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
        />
      ) : null}
      </div>
    </section>
  );
}
