/**
 * Baixas financeiras (R01/R02) — Central de Fechamento.
 *
 * Consome `GET /closing/financial-settlements` e `/summary` da BFF.
 * Falha tipada `scope_unavailable` (D3/D3.1) é estado próprio — nunca
 * confundida com ausência de registros nem com falta de autorização.
 */
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { ApiError } from "../../api/httpClient";
import {
  getFinancialSettlements,
  getFinancialSettlementsSummary,
  type SettlementItem,
  type SettlementSide,
  type SettlementSummaryGroup,
  type SettlementsListPayload,
  type SettlementsSummaryPayload,
} from "../../api/financialSettlementsApi";
import {
  CfActionButton,
  CfEmptyState,
  CfSegmentToggle,
  CfStatusBadge,
  CfTitleWithHelp,
  cfEmptyStateClassNames,
} from "../../app/controllershipFinanceUi";
import {
  ArrowLeftRight,
  CircleDollarSign,
  ClipboardList,
  Tags,
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
import { FilterInputField, FilterSelectField, FiltersRow } from "../../app/cfFiltersUi";
import { CF_HELP } from "../../content/helpTooltips";
import { formatAmount, formatCivilDate } from "../../utils/formatters";
import { useDebouncedValue } from "../../utils/useDebouncedValue";
import {
  parseSettlementsQuery,
  readReportSearchParams,
  serializeSettlementsQuery,
  useReportQuerySync,
} from "./reportQueryParams";
import { ReportPdfSlot } from "./ReportSharedSections";

const PAGE_SIZE = 50;
const DEBOUNCE_MS = 400;

const SIDE_OPTIONS = [
  { value: "payable", label: "Baixas a pagar" },
  { value: "receivable", label: "Baixas a receber" },
] as const;

const SORT_BY_OPTIONS = [
  { value: "settlement_date", label: "Data da baixa" },
  { value: "nature", label: "Natureza" },
] as const;

const SORT_DIR_OPTIONS = [
  { value: "desc", label: "Decrescente" },
  { value: "asc", label: "Crescente" },
] as const;

const LINK_STATUS_LABELS: Record<string, string> = {
  resolved: "Vínculo completo",
  missing_document: "Documento ausente",
  missing_nature: "Natureza ausente",
  missing_document_and_nature: "Documento e natureza ausentes",
};

function isoToday(): string {
  return new Date().toISOString().slice(0, 10);
}

function isoMonthStart(): string {
  const now = new Date();
  return `${now.getUTCFullYear()}-${String(now.getUTCMonth() + 1).padStart(2, "0")}-01`;
}

/** Limites da competência `YYYY-MM` — defaults do modo contextual (UX-011). */
function periodDateRange(period: string): {
  startDate: string;
  endDate: string;
} {
  const [year, month] = period.split("-").map(Number);
  const lastDay = new Date(year, month, 0).getDate();
  return {
    startDate: `${period}-01`,
    endDate: `${period}-${String(lastDay).padStart(2, "0")}`,
  };
}

function formatPeriod(period: string): string {
  const [year, month] = period.split("-");
  return `${month}/${year}`;
}

type AppliedFilters = {
  side: SettlementSide;
  startDate: string;
  endDate: string;
  natureCode: string;
  movementType: string;
  sortBy: string;
  sortDir: "asc" | "desc";
};

type FetchState =
  | { kind: "error"; status: number; code: string | null; message: string }
  | { kind: "ready"; list: SettlementsListPayload; summary: SettlementsSummaryPayload | null };

type FetchResult = { key: string } & FetchState;

/**
 * Contexto do relatório dentro do Fechamento Mensal (UX-011): a
 * competência vem da rota contextual e inicia os filtros de data; o
 * modo exibe a tabela de agrupamentos por colunas e o slot de PDF.
 */
export type FinancialSettlementsReportContext = { period: string };

export function FinancialSettlementsPage({
  reportContext,
}: {
  reportContext?: FinancialSettlementsReportContext;
}) {
  const contextRange = useMemo(
    () => (reportContext ? periodDateRange(reportContext.period) : null),
    [reportContext],
  );
  // RW01: no modo contextual os filtros iniciais vêm da query da rota —
  // F5, deep link e voltar/avançar restauram o contexto da análise.
  const [urlInit] = useState(() =>
    reportContext && contextRange
      ? parseSettlementsQuery(readReportSearchParams(), contextRange)
      : null,
  );
  const [side, setSide] = useState<SettlementSide>(
    () => urlInit?.side ?? "payable",
  );
  const [startDate, setStartDate] = useState(
    () =>
      urlInit?.startDate ??
      contextRange?.startDate ??
      isoMonthStart(),
  );
  const [endDate, setEndDate] = useState(
    () => urlInit?.endDate ?? contextRange?.endDate ?? isoToday(),
  );
  const [natureCode, setNatureCode] = useState(
    () => urlInit?.natureCode ?? "",
  );
  const [movementType, setMovementType] = useState(
    () => urlInit?.movementType ?? "",
  );
  const [sortBy, setSortBy] = useState(
    () => urlInit?.sortBy ?? "settlement_date",
  );
  const [sortDir, setSortDir] = useState<"asc" | "desc">(
    () => urlInit?.sortDir ?? "desc",
  );

  const debouncedNatureCode = useDebouncedValue(natureCode.trim(), DEBOUNCE_MS);
  const debouncedMovementType = useDebouncedValue(
    movementType.trim(),
    DEBOUNCE_MS,
  );

  const [page, setPage] = useState(() => urlInit?.page ?? 1);
  const [result, setResult] = useState<FetchResult | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [retryNonce, setRetryNonce] = useState(0);
  const requestId = useRef(0);

  const filtersValid = useMemo(() => {
    if (!startDate || !endDate) return false;
    return startDate <= endDate;
  }, [startDate, endDate]);

  // Filtros vigentes: derivados diretamente dos campos (sem botão Consultar).
  // Campos digitáveis entram já com debounce; seletores/toggles/datas são
  // imediatos. Inválido => null => nenhuma consulta é disparada.
  const applied: AppliedFilters | null = useMemo(
    () =>
      filtersValid
        ? {
            side,
            startDate,
            endDate,
            natureCode: debouncedNatureCode,
            movementType: debouncedMovementType,
            sortBy,
            sortDir,
          }
        : null,
    [
      filtersValid,
      side,
      startDate,
      endDate,
      debouncedNatureCode,
      debouncedMovementType,
      sortBy,
      sortDir,
    ],
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
    setStartDate(contextRange?.startDate ?? isoMonthStart());
    setEndDate(contextRange?.endDate ?? isoToday());
    setNatureCode("");
    setMovementType("");
    setSortBy("settlement_date");
    setSortDir("desc");
  }, [contextRange]);

  const retry = useCallback(() => setRetryNonce((n) => n + 1), []);

  // RW01: a query da rota contextual espelha os campos brutos (não o
  // valor debounced) — reidratar pelo popstate nunca corrige a URL com
  // um valor ainda em debounce. Serialização é determinística e o efeito
  // só navega quando a query realmente difere.
  const hydrateFromUrl = useCallback(
    (params: URLSearchParams) => {
      if (!contextRange) return;
      const parsed = parseSettlementsQuery(params, contextRange);
      setSide(parsed.side);
      setStartDate(parsed.startDate);
      setEndDate(parsed.endDate);
      setNatureCode(parsed.natureCode);
      setMovementType(parsed.movementType);
      setSortBy(parsed.sortBy);
      setSortDir(parsed.sortDir);
      // O fingerprint esperado impede o reset de página quando o debounce
      // dos campos digitáveis alcançar o valor restaurado — a página da
      // URL deve prevalecer sobre o "volta para página 1" do ciclo local.
      setAppliedFingerprintSeen(
        JSON.stringify({
          side: parsed.side,
          startDate: parsed.startDate,
          endDate: parsed.endDate,
          natureCode: parsed.natureCode.trim(),
          movementType: parsed.movementType.trim(),
          sortBy: parsed.sortBy,
          sortDir: parsed.sortDir,
        }),
      );
      setPage(parsed.page);
    },
    [contextRange],
  );
  useReportQuerySync({
    enabled: Boolean(reportContext),
    serialize: () => {
      const query = serializeSettlementsQuery({
        side,
        startDate,
        endDate,
        natureCode: natureCode.trim(),
        movementType: movementType.trim(),
        sortBy,
        sortDir,
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
  const list = current?.kind === "ready" ? current.list : null;

  useEffect(() => {
    if (!applied || !queryKey) return;
    const id = ++requestId.current;
    const controller = new AbortController();

    const common = {
      startDate: applied.startDate,
      endDate: applied.endDate,
      natureCode: applied.natureCode || undefined,
      movementType: applied.movementType || undefined,
    };

    Promise.all([
      getFinancialSettlements(
        {
          ...common,
          side: applied.side,
          sortBy: applied.sortBy,
          sortDir: applied.sortDir,
          page,
          pageSize: PAGE_SIZE,
        },
        { signal: controller.signal },
      ),
      getFinancialSettlementsSummary(common, {
        signal: controller.signal,
      }).catch(() => null),
    ])
      .then(([list, summary]) => {
        if (controller.signal.aborted || requestId.current !== id) return;
        setResult({ key: queryKey, kind: "ready", list, summary });
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
                message: "Falha de comunicação com a API de baixas.",
              };
        setResult({ key: queryKey, kind: "error", ...detail });
      });

    return () => controller.abort();
  }, [applied, page, queryKey]);

  const summaryForSide = useMemo(() => {
    if (current?.kind !== "ready" || !current.summary) return null;
    return current.summary.groups.filter((group) => group.side === applied?.side);
  }, [current, applied?.side]);

  const currencyTotals = useMemo(() => {
    const totals = new Map<string, number>();
    for (const group of summaryForSide ?? []) {
      const code = group.currencyCode ?? "—";
      totals.set(code, (totals.get(code) ?? 0) + Number(group.totalAmount));
    }
    return [...totals.entries()].map(([code, total]) => ({
      code,
      total,
    }));
  }, [summaryForSide]);

  // KPIs do hero — somente métricas presentes no resumo vigente (doc 50 §3).
  const heroMetrics = useMemo<ClosingHeroMetric[] | undefined>(() => {
    if (!list) {
      return loading
        ? [
            {
              id: "events",
              label: "Eventos",
              value: "",
              icon: <ClipboardList size={20} aria-hidden />,
            },
            {
              id: "natures",
              label: "Naturezas",
              value: "",
              icon: <Tags size={20} aria-hidden />,
            },
            {
              id: "movementTypes",
              label: "Tipos de movimento",
              value: "",
              icon: <ArrowLeftRight size={20} aria-hidden />,
            },
          ]
        : undefined;
    }
    const groups = summaryForSide ?? [];
    if (groups.length === 0) return undefined;
    const sideHint = applied?.side === "receivable" ? "a receber" : "a pagar";
    return [
      {
        id: "events",
        label: "Eventos",
        value: String(groups.reduce((acc, g) => acc + g.eventCount, 0)),
        hint: `baixas ${sideHint} no período`,
        icon: <ClipboardList size={20} aria-hidden />,
      },
      ...currencyTotals.map(({ code, total }) => ({
        id: `currency-${code}`,
        label: "Movimentações registradas",
        value: formatAmount(String(total)),
        hint: `moeda ${code}`,
        icon: <CircleDollarSign size={20} aria-hidden />,
      })),
      {
        id: "natures",
        label: "Naturezas",
        value: String(new Set(groups.map((g) => g.natureCode ?? "—")).size),
        hint: `ativas ${sideHint}`,
        icon: <Tags size={20} aria-hidden />,
      },
      {
        id: "movementTypes",
        label: "Tipos de movimento",
        value: String(new Set(groups.map((g) => g.movementType ?? "—")).size),
        hint: `baixas ${sideHint}`,
        icon: <ArrowLeftRight size={20} aria-hidden />,
      },
    ];
  }, [list, loading, summaryForSide, currencyTotals, applied?.side]);

  const columns = useMemo<DataTableColumn<SettlementItem>[]>(
    () => [
      {
        key: "settlementDate",
        header: "Data da baixa",
        className: "cf-table__col--compact",
        render: (row) => formatCivilDate(row.settlementDate),
      },
      {
        key: "document",
        header: "Documento",
        render: (row) => {
          const doc = [row.prefix, row.documentNumber, row.documentType]
            .filter(Boolean)
            .join(" ");
          return doc ? <span className="cf-cell-primary">{doc}</span> : "—";
        },
      },
      {
        key: "installment",
        header: "Parcela",
        align: "center",
        className: "cf-table__col--compact",
        render: (row) => row.installment ?? "—",
      },
      {
        key: "party",
        header: applied?.side === "receivable" ? "Cliente" : "Fornecedor",
        className: "cf-table__col--wide",
        render: (row) => {
          const code = [row.partyCode, row.partyStore]
            .filter(Boolean)
            .join("/");
          if (!row.partyName) return code || "—";
          return (
            <>
              <span className="cf-cell-primary">{row.partyName}</span>
              {code ? (
                <span className="cf-cell-secondary">{code}</span>
              ) : null}
            </>
          );
        },
      },
      {
        key: "nature",
        header: "Natureza",
        className: "cf-table__col--wrap",
        render: (row) =>
          row.natureCode ? (
            <>
              <span className="cf-cell-primary">{row.natureCode}</span>
              {row.natureDescription ? (
                <span className="cf-cell-secondary">
                  {row.natureDescription}
                </span>
              ) : null}
            </>
          ) : (
            "—"
          ),
      },
      {
        key: "movementType",
        header: "Tipo mov.",
        mobileLabel: "Tipo de movimento",
        className: "cf-table__col--wrap",
        render: (row) =>
          row.movementType ? (
            <>
              <span className="cf-cell-primary">{row.movementType}</span>
              {row.movementDescription ? (
                <span className="cf-cell-secondary">
                  {row.movementDescription}
                </span>
              ) : null}
            </>
          ) : (
            "—"
          ),
      },
      {
        key: "paymentDirection",
        header: "Direção",
        className: "cf-table__col--status",
        // `side` do contrato é real; o código cru `paymentDirection` (D4)
        // fica em tooltip + texto para leitor de tela — nunca como
        // caractere solto em segunda linha (doc 52 / AC01).
        render: (row) =>
          row.paymentDirection ? (
            <span
              className="cf-cell-direction"
              title={`Código de direção na origem: ${row.paymentDirection}`}
            >
              <CfStatusBadge
                label={
                  applied?.side === "receivable" ? "A receber" : "A pagar"
                }
                variant={
                  applied?.side === "receivable" ? "success" : "info"
                }
              />
              <span className="cf-visually-hidden">
                {`código de direção na origem: ${row.paymentDirection}`}
              </span>
            </span>
          ) : (
            "—"
          ),
      },
      {
        key: "currencyCode",
        header: "Moeda",
        className: "cf-table__col--compact",
        render: (row) => row.currencyCode ?? "—",
      },
      {
        key: "settlementAmount",
        header: "Valor",
        align: "right",
        className: "cf-table__col--numeric",
        render: (row) => (
          <span className="cf-cell-amount">
            {formatAmount(row.settlementAmount)}
          </span>
        ),
      },
      {
        key: "dueDate",
        header: "Vencimento",
        className: "cf-table__col--compact",
        render: (row) => formatCivilDate(row.dueDate),
      },
      {
        key: "linkStatus",
        header: "Vínculo",
        className: "cf-table__col--status",
        render: (row) => (
          <CfStatusBadge
            label={LINK_STATUS_LABELS[row.linkStatus] ?? row.linkStatus}
            variant={row.linkStatus === "resolved" ? "success" : "warning"}
          />
        ),
      },
      {
        key: "branchCode",
        header: "Filial",
        className: "cf-table__col--compact",
        render: (row) =>
          row.branchCode ? (
            `Filial ${row.branchCode}`
          ) : (
            <span className="cf-cell-muted">Não identificada</span>
          ),
      },
    ],
    [applied?.side],
  );

  /** Ação «Ver registros» de um agrupamento: aplica os filtros reais do
   *  contrato (natureza/movimento) e foca a tabela de baixas. */
  const showGroupLines = useCallback(
    (group: SettlementSummaryGroup) => {
      setNatureCode(group.natureCode ?? "");
      setMovementType(group.movementType ?? "");
      const node = document.getElementById("cf-settle-detail");
      if (node) {
        node.scrollIntoView?.({ block: "start" });
        node.focus({ preventScroll: true });
      }
    },
    [],
  );

  const groupColumns = useMemo<DataTableColumn<SettlementSummaryGroup>[]>(
    () => [
      {
        key: "nature",
        header: "Natureza",
        className: "cf-table__col--wrap",
        render: (group) =>
          group.natureCode || group.natureDescription ? (
            <>
              <span className="cf-cell-primary">
                {group.natureCode ?? "—"}
              </span>
              {group.natureDescription ? (
                <span className="cf-cell-secondary">
                  {group.natureDescription}
                </span>
              ) : null}
            </>
          ) : (
            "—"
          ),
      },
      {
        key: "movement",
        header: "Tipo de movimento",
        mobileLabel: "Tipo de movimento",
        className: "cf-table__col--wrap",
        render: (group) =>
          group.movementType || group.movementDescription ? (
            <>
              <span className="cf-cell-primary">
                {group.movementType ?? "—"}
              </span>
              {group.movementDescription ? (
                <span className="cf-cell-secondary">
                  {group.movementDescription}
                </span>
              ) : null}
            </>
          ) : (
            "—"
          ),
      },
      {
        key: "events",
        header: "Baixas",
        align: "right",
        className: "cf-table__col--numeric",
        render: (group) => String(group.eventCount),
      },
      {
        key: "total",
        header: "Valor",
        align: "right",
        className: "cf-table__col--numeric",
        render: (group) => (
          <span className="cf-cell-amount">
            {formatAmount(group.totalAmount)}
          </span>
        ),
      },
      {
        key: "currency",
        header: "Moeda",
        className: "cf-table__col--compact",
        render: (group) => group.currencyCode ?? "—",
      },
      {
        key: "action",
        header: "Ação",
        className: "cf-table__col--compact",
        render: (group) => (
          <CfActionButton
            variant="ghost"
            onClick={() => showGroupLines(group)}
          >
            Ver registros
          </CfActionButton>
        ),
      },
    ],
    [showGroupLines],
  );

  const renderError = () => {
    if (current?.kind !== "error") return null;
    return (
      <CfQueryErrorBanner
        error={current}
        dataset="as baixas financeiras"
        onRetry={retry}
      />
    );
  };

  return (
    <section
      className="cf-page-stack cf-closing-layout"
      aria-label="Baixas financeiras"
    >
      <ClosingHero
        title={
          <CfTitleWithHelp
            title="Baixas financeiras"
            hint={CF_HELP.closing.page}
          />
        }
        subtitle={
          reportContext
            ? `Eventos de baixa da competência ${formatPeriod(
                reportContext.period,
              )} · Origem: TOTVS/SE5 — consulta operacional.`
            : "Eventos de baixa a pagar e a receber para conferência do fechamento."
        }
        updatedAt={lastUpdated}
        onRefresh={retry}
        refreshing={loading}
        metrics={heroMetrics}
        notice={
          <CfFeedbackMessage intent="info" title="Resumo do período">
            Soma bruta dos eventos financeiros por lado e moeda — inclui
            baixas, estornos e compensações; não representa total líquido
            pago/recebido nem conciliação bancária.
          </CfFeedbackMessage>
        }
        filters={
          <form
            className="cf-settlements-filters"
            onSubmit={(event) => event.preventDefault()}
          >
            <CfSegmentToggle<SettlementSide>
              options={SIDE_OPTIONS}
              value={side}
              onChange={setSide}
              ariaLabel="Visão das baixas financeiras"
              size="sm"
            />
            <FiltersRow>
              <FilterInputField
                id="cf-settle-start"
                label="Data inicial"
                type="date"
                value={startDate}
                onChange={setStartDate}
              />
              <FilterInputField
                id="cf-settle-end"
                label="Data final"
                type="date"
                value={endDate}
                onChange={setEndDate}
              />
              <FilterInputField
                id="cf-settle-nature"
                label="Natureza financeira"
                type="text"
                value={natureCode}
                onChange={setNatureCode}
                placeholder="Código da natureza"
              />
              <FilterInputField
                id="cf-settle-mov"
                label="Tipo de movimento"
                type="text"
                value={movementType}
                onChange={setMovementType}
                placeholder="Código do movimento"
              />
              <FilterSelectField
                label="Ordenar por"
                value={sortBy}
                onChange={setSortBy}
                options={SORT_BY_OPTIONS}
              />
              <FilterSelectField
                label="Direção da ordenação"
                value={sortDir}
                onChange={(value) => setSortDir(value as "asc" | "desc")}
                options={SORT_DIR_OPTIONS}
              />
            </FiltersRow>
            {!filtersValid ? (
              <CfFeedbackMessage intent="error" title="Período inválido">
                Informe um período válido: a data inicial deve ser anterior ou
                igual à data final.
              </CfFeedbackMessage>
            ) : null}
          </form>
        }
        onClearFilters={clearFilters}
      />

      <div className="cf-page-stack" aria-busy={loading}>
      {renderError()}

      {!applied ? (
        <CfEmptyState
          classNames={cfEmptyStateClassNames}
          defaultMessage="Informe um período válido para consultar as baixas."
        />
      ) : null}

      {list && (summaryForSide ?? []).length === 0 ? (
        <CfFeedbackMessage intent="info" title="Resumo do período">
          Sem dados de resumo no período.
        </CfFeedbackMessage>
      ) : null}

      {list ? (
        <CfFeedbackMessage intent="info" title="Qualidade dos vínculos">
          {list.quality.missingDocumentCount} sem documento ·{" "}
          {list.quality.missingNatureCount} sem natureza ·{" "}
          {list.quality.unresolvedBranchCount} sem filial identificada.
        </CfFeedbackMessage>
      ) : null}

      {/* UX-011: tabela de agrupamentos organizada por colunas — natureza
          e tipo de movimento nunca concatenados; «Ver registros» aplica
          os filtros reais do contrato à tabela de baixas abaixo. */}
      {reportContext && list && (summaryForSide ?? []).length > 0 ? (
        <DataTableSection<SettlementSummaryGroup>
          title={`Agrupamentos — ${
            applied?.side === "receivable" ? "Recebimentos" : "Pagamentos"
          }`}
          titleHint={CF_HELP.monthlyClosing.reportsResults}
          columns={groupColumns}
          rows={summaryForSide ?? []}
          rowKey={(group) =>
            `${group.side}-${group.natureCode ?? "x"}-${
              group.movementType ?? "x"
            }-${group.currencyCode ?? "x"}`
          }
          loading={loading}
          hideSearch
          emptyMessage="Nenhum agrupamento no período para os filtros aplicados."
          columnPreferencesKey="cf:closing:settlement-groups:v1"
        />
      ) : null}

      {list || loading ? (
        <div id="cf-settle-detail" tabIndex={-1}>
        <DataTableSection<SettlementItem>
          title={
            applied?.side === "receivable"
              ? "Baixas a receber"
              : "Baixas a pagar"
          }
          titleHint={CF_HELP.closing.table}
          columns={columns}
          rows={list?.items ?? []}
          rowKey={(row) => row.settlementId}
          loading={loading}
          hideSearch
          serverPagination={
            list
              ? {
                  page: list.pagination.page,
                  pageSize: list.pagination.page_size,
                  total: list.pagination.total_items,
                  onPageChange: setPage,
                }
              : undefined
          }
          emptyMessage="Nenhuma baixa encontrada no período para os filtros aplicados."
          columnPreferencesKey={`cf:closing:financial-settlements:${applied?.side ?? "payable"}:v1`}
          fontSizePreferencesKey="cf:closing:financial-settlements:font:v1"
          resizableColumns
        />
        </div>
      ) : null}
      </div>

      {reportContext ? (
        <ReportPdfSlot reportName="Baixas financeiras" />
      ) : null}
    </section>
  );
}
