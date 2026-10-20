/**
 * Baixas financeiras (R01/R02) — Central de Fechamento.
 *
 * Consome `GET /closing/financial-settlements` e `/summary` da BFF.
 * Falha tipada `scope_unavailable` (D3/D3.1) é estado próprio — nunca
 * confundida com ausência de registros nem com falta de autorização.
 */
import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type FormEvent,
} from "react";

import { ApiError } from "../../api/httpClient";
import {
  getFinancialSettlements,
  getFinancialSettlementsSummary,
  type SettlementItem,
  type SettlementSide,
  type SettlementsListPayload,
  type SettlementsSummaryPayload,
} from "../../api/financialSettlementsApi";
import {
  CfActionButton,
  CfEmptyState,
  CfSectionCard,
  CfSegmentToggle,
  CfStateBanner,
  cfEmptyStateClassNames,
} from "../../app/controllershipFinanceUi";
import { DataTableSection, type DataTableColumn } from "../../app/cfDataTableUi";
import { FilterInputField, FilterSelectField, FiltersRow } from "../../app/cfFiltersUi";
import { CF_HELP } from "../../content/helpTooltips";

const PAGE_SIZE = 50;

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

const DATE_FMT = new Intl.DateTimeFormat("pt-BR");
const AMOUNT_FMT = new Intl.NumberFormat("pt-BR", {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

function formatDate(iso: string | null): string {
  if (!iso) return "—";
  const [y, m, d] = iso.slice(0, 10).split("-").map(Number);
  if (!y || !m || !d) return iso;
  return DATE_FMT.format(new Date(Date.UTC(y, m - 1, d)));
}

function formatAmount(raw: string): string {
  const value = Number(raw);
  return Number.isFinite(value) ? AMOUNT_FMT.format(value) : raw;
}

function isoToday(): string {
  return new Date().toISOString().slice(0, 10);
}

function isoMonthStart(): string {
  const now = new Date();
  return `${now.getUTCFullYear()}-${String(now.getUTCMonth() + 1).padStart(2, "0")}-01`;
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

export function FinancialSettlementsPage() {
  const [side, setSide] = useState<SettlementSide>("payable");
  const [startDate, setStartDate] = useState(isoMonthStart);
  const [endDate, setEndDate] = useState(isoToday);
  const [natureCode, setNatureCode] = useState("");
  const [movementType, setMovementType] = useState("");
  const [sortBy, setSortBy] = useState("settlement_date");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");

  const [applied, setApplied] = useState<AppliedFilters | null>(null);
  const [page, setPage] = useState(1);
  const [result, setResult] = useState<FetchResult | null>(null);
  const requestId = useRef(0);

  const filtersValid = useMemo(() => {
    if (!startDate || !endDate) return false;
    return startDate <= endDate;
  }, [startDate, endDate]);

  const applyFilters = useCallback(
    (event?: FormEvent) => {
      event?.preventDefault();
      if (!filtersValid) return;
      setPage(1);
      setApplied({
        side,
        startDate,
        endDate,
        natureCode: natureCode.trim(),
        movementType: movementType.trim(),
        sortBy,
        sortDir,
      });
    },
    [filtersValid, side, startDate, endDate, natureCode, movementType, sortBy, sortDir],
  );

  const clearFilters = useCallback(() => {
    setStartDate(isoMonthStart());
    setEndDate(isoToday());
    setNatureCode("");
    setMovementType("");
    setSortBy("settlement_date");
    setSortDir("desc");
    setPage(1);
    setApplied(null);
    setResult(null);
  }, []);

  const queryKey = applied ? JSON.stringify({ ...applied, page }) : null;
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

  const columns = useMemo<DataTableColumn<SettlementItem>[]>(
    () => [
      {
        key: "settlementDate",
        header: "Data da baixa",
        render: (row) => formatDate(row.settlementDate),
      },
      {
        key: "document",
        header: "Documento",
        render: (row) =>
          [row.prefix, row.documentNumber, row.documentType]
            .filter(Boolean)
            .join(" ") || "—",
      },
      {
        key: "installment",
        header: "Parcela",
        render: (row) => row.installment ?? "—",
      },
      {
        key: "party",
        header: applied?.side === "receivable" ? "Cliente" : "Fornecedor",
        render: (row) =>
          row.partyName ??
          ([row.partyCode, row.partyStore].filter(Boolean).join("/") || "—"),
      },
      {
        key: "nature",
        header: "Natureza",
        render: (row) =>
          row.natureCode
            ? `${row.natureCode}${row.natureDescription ? ` — ${row.natureDescription}` : ""}`
            : "—",
      },
      {
        key: "movementType",
        header: "Tipo mov.",
        render: (row) =>
          row.movementType
            ? `${row.movementType}${row.movementDescription ? ` — ${row.movementDescription}` : ""}`
            : "—",
      },
      {
        key: "paymentDirection",
        header: "Direção",
        render: (row) => row.paymentDirection ?? "—",
      },
      {
        key: "currencyCode",
        header: "Moeda",
        render: (row) => row.currencyCode ?? "—",
      },
      {
        key: "settlementAmount",
        header: "Valor",
        align: "right",
        render: (row) => formatAmount(row.settlementAmount),
      },
      {
        key: "dueDate",
        header: "Vencimento",
        render: (row) => formatDate(row.dueDate),
      },
      {
        key: "linkStatus",
        header: "Vínculo",
        render: (row) => LINK_STATUS_LABELS[row.linkStatus] ?? row.linkStatus,
      },
      {
        key: "branchCode",
        header: "Filial",
        render: (row) => row.branchCode ?? "Não identificada",
      },
    ],
    [applied?.side],
  );

  const renderError = () => {
    if (current?.kind !== "error") return null;
    if (current.code === "scope_unavailable") {
      return (
        <CfStateBanner variant="error">
          <p className="cf-banner-title">Escopo de dados indisponível</p>
          <p className="cf-banner-text">
            O acesso ao conjunto de dados financeiros ainda não está liberado
            para este ambiente.
          </p>
        </CfStateBanner>
      );
    }
    if (current.status === 401) {
      return (
        <CfStateBanner variant="error">
          <p className="cf-banner-title">Sessão expirada</p>
          <p className="cf-banner-text">Entre novamente para continuar.</p>
        </CfStateBanner>
      );
    }
    if (current.status === 403) {
      return (
        <CfStateBanner variant="error">
          <p className="cf-banner-title">Acesso restrito</p>
          <p className="cf-banner-text">
            Você não tem autorização para consultar as baixas financeiras.
          </p>
        </CfStateBanner>
      );
    }
    return (
      <CfStateBanner variant="error">
        <p className="cf-banner-title">Falha de comunicação</p>
        <p className="cf-banner-text">{current.message}</p>
        <CfActionButton variant="ghost" onClick={() => applyFilters()}>
          Tentar novamente
        </CfActionButton>
      </CfStateBanner>
    );
  };

  return (
    <section
      className="cf-page-stack cf-closing-layout"
      aria-label="Baixas financeiras"
    >
      <CfSectionCard
        title="Baixas financeiras"
        subtitle="Central de Fechamento — eventos de baixa a pagar e a receber."
        hint={CF_HELP.closing.page}
      >
        <form className="cf-settlements-filters" onSubmit={applyFilters}>
          <CfSegmentToggle<SettlementSide>
            options={SIDE_OPTIONS}
            value={side}
            onChange={(value) => {
              setSide(value);
              if (applied) {
                setPage(1);
                setApplied({ ...applied, side: value });
              }
            }}
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
            <CfStateBanner variant="error">
              <p className="cf-banner-text">
                Informe um período válido: a data inicial deve ser anterior ou
                igual à data final.
              </p>
            </CfStateBanner>
          ) : null}
          <div className="cf-settlements-actions">
            <CfActionButton
              variant="primary"
              type="submit"
              disabled={!filtersValid || loading}
            >
              Aplicar filtros
            </CfActionButton>
            <CfActionButton variant="ghost" onClick={clearFilters}>
              Limpar
            </CfActionButton>
          </div>
        </form>
      </CfSectionCard>

      {renderError()}

      {!applied ? (
        <CfEmptyState
          classNames={cfEmptyStateClassNames}
          defaultMessage="Informe o período e aplique os filtros para consultar as baixas."
        />
      ) : null}

      {list || loading ? (
        <CfSectionCard
          title="Resumo do período"
          subtitle="Soma bruta dos eventos financeiros por lado e moeda. Inclui baixas, estornos e compensações; não representa total líquido pago/recebido nem conciliação bancária."
          hint={CF_HELP.closing.summary}
        >
          {summaryForSide && summaryForSide.length > 0 ? (
            <ul className="cf-settlements-summary" aria-label="Resumo por moeda">
              <li>
                <span className="cf-settlements-summary-label">Eventos</span>
                <strong>
                  {summaryForSide.reduce((acc, g) => acc + g.eventCount, 0)}
                </strong>
              </li>
              {currencyTotals.map(({ code, total }) => (
                <li key={code}>
                  <span className="cf-settlements-summary-label">
                    Movimentações registradas — moeda {code}
                  </span>
                  <strong>{formatAmount(String(total))}</strong>
                </li>
              ))}
              <li>
                <span className="cf-settlements-summary-label">Naturezas</span>
                <strong>
                  {new Set(summaryForSide.map((g) => g.natureCode ?? "—")).size}
                </strong>
              </li>
              <li>
                <span className="cf-settlements-summary-label">
                  Tipos de movimento
                </span>
                <strong>
                  {new Set(summaryForSide.map((g) => g.movementType ?? "—")).size}
                </strong>
              </li>
            </ul>
          ) : (
            <p className="cf-banner-text">
              {loading ? "Carregando resumo…" : "Sem dados de resumo no período."}
            </p>
          )}
          {list ? (
            <p className="cf-settlements-quality" role="note">
              Qualidade dos vínculos: {list.quality.missingDocumentCount} sem
              documento · {list.quality.missingNatureCount} sem natureza ·{" "}
              {list.quality.unresolvedBranchCount} sem filial identificada.
            </p>
          ) : null}
        </CfSectionCard>
      ) : null}

      {list || loading ? (
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
        />
      ) : null}
    </section>
  );
}
