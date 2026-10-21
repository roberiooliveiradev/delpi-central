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
  CfActionButton,
  CfEmptyState,
  CfLoadingCard,
  CfSectionCard,
  CfSegmentToggle,
  CfStateBanner,
  cfEmptyStateClassNames,
} from "../../app/controllershipFinanceUi";
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

  const renderStatusBanner = () => {
    if (!payload || payload.status === "available") return null;
    if (payload.status === "source_missing") {
      return (
        <CfStateBanner variant="error">
          <p className="cf-banner-title">Snapshot não encontrado</p>
          <p className="cf-banner-text">
            O ERP não possui fechamento de estoque registrado para{" "}
            {payload.period}
            {payload.branchesMissing.length > 0
              ? ` na filial ${payload.branchesMissing.join(", ")}`
              : ""}
            . Consulte outra competência ou filial — a ausência não é um
            saldo zero.
          </p>
        </CfStateBanner>
      );
    }
    if (payload.status === "incomplete") {
      return (
        <CfStateBanner variant="error">
          <p className="cf-banner-title">Dados parcialmente disponíveis</p>
          <p className="cf-banner-text">
            O snapshot de {payload.period} não existe para{" "}
            {payload.branchesMissing.length === 1
              ? `a filial ${payload.branchesMissing[0]}`
              : `as filiais ${payload.branchesMissing.join(", ")}`}
            . Os totais abaixo cobrem somente{" "}
            {payload.branchesAvailable.length === 1
              ? `a filial ${payload.branchesAvailable[0]}`
              : `as filiais ${payload.branchesAvailable.join(", ")}`}
            .
          </p>
        </CfStateBanner>
      );
    }
    return (
      <CfStateBanner variant="error">
        <p className="cf-banner-title">Sem itens para o filtro</p>
        <p className="cf-banner-text">
          O snapshot de {payload.period} existe, mas nenhum item corresponde
          aos filtros aplicados.
        </p>
      </CfStateBanner>
    );
  };

  const renderError = () => {
    if (current?.kind !== "error") return null;
    if (current.code === "scope_unavailable") {
      return (
        <CfStateBanner variant="error">
          <p className="cf-banner-title">Consulta ainda não habilitada</p>
          <p className="cf-banner-text">
            O acesso ao conjunto de dados de estoque ainda não está liberado
            para este ambiente.
          </p>
        </CfStateBanner>
      );
    }
    if (current.code && current.code.startsWith("S2S_")) {
      return (
        <CfStateBanner variant="error">
          <p className="cf-banner-title">Integração de dados pendente</p>
          <p className="cf-banner-text">
            A credencial técnica entre o Portal e a origem de dados ainda não
            possui a autorização necessária para esta consulta. Acione o
            suporte informando esta tela.
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
            Você não tem autorização para consultar o estoque histórico.
          </p>
        </CfStateBanner>
      );
    }
    if (current.status === 503) {
      return (
        <CfStateBanner variant="error">
          <p className="cf-banner-title">Origem indisponível</p>
          <p className="cf-banner-text">
            A fonte de dados de estoque está temporariamente indisponível.
          </p>
          <CfActionButton variant="ghost" onClick={retry}>
            Tentar novamente
          </CfActionButton>
        </CfStateBanner>
      );
    }
    return (
      <CfStateBanner variant="error">
        <p className="cf-banner-title">Falha de comunicação</p>
        <p className="cf-banner-text">{current.message}</p>
        <CfActionButton variant="ghost" onClick={retry}>
          Tentar novamente
        </CfActionButton>
      </CfStateBanner>
    );
  };

  const showData = payload !== null || loading;

  return (
    <section
      className="cf-page-stack cf-closing-layout"
      aria-label="Estoque histórico — P7"
    >
      <CfSectionCard
        title="Estoque histórico — P7"
        subtitle="Consulta operacional dos saldos históricos de estoque por competência, filial e classificação de produto."
        hint={CF_HELP.stockInventory.page}
      >
        <p className="cf-banner-text" role="note">
          Consulta operacional — os resultados ainda não equivalem ao
          relatório oficial MATR460.
        </p>
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
            <CfStateBanner variant="error">
              <p className="cf-banner-text">
                Informe uma competência válida no formato AAAA-MM.
              </p>
            </CfStateBanner>
          ) : null}
          <div className="cf-settlements-actions">
            <CfActionButton
              variant="ghost"
              type="button"
              onClick={clearFilters}
            >
              Limpar
            </CfActionButton>
          </div>
        </form>
      </CfSectionCard>

      <div aria-busy={loading}>
      {renderError()}
      {renderStatusBanner()}

      {!applied ? (
        <CfEmptyState
          classNames={cfEmptyStateClassNames}
          defaultMessage="Informe uma competência válida para ver o estoque histórico."
        />
      ) : null}

      {showData ? (
        <CfSectionCard
          title="Indicadores"
          subtitle="Totais calculados sobre todo o universo do filtro — não apenas a página exibida."
          hint={CF_HELP.stockInventory.indicators}
        >
          {payload ? (
            <ul className="cf-settlements-summary" aria-label="Indicadores do estoque">
              <li>
                <span className="cf-settlements-summary-label">
                  Disponibilidade
                </span>
                <strong>
                  {STATUS_LABELS[payload.status] ?? payload.status}
                </strong>
              </li>
              <li>
                <span className="cf-settlements-summary-label">Data-base</span>
                <strong>{formatCivilDate(payload.dataAsOf)}</strong>
              </li>
              <li>
                <span className="cf-settlements-summary-label">Itens</span>
                <strong>{payload.pagination.total_items}</strong>
              </li>
              {payload.branchCode === "all" ? (
                <li>
                  <span className="cf-settlements-summary-label">
                    Filiais com dados
                  </span>
                  <strong>{payload.branchesAvailable.length}</strong>
                </li>
              ) : null}
              {payload.historicalTotal !== null ? (
                <li>
                  <span className="cf-settlements-summary-label">
                    Valor histórico total
                  </span>
                  <strong>{formatAmount(payload.historicalTotal)}</strong>
                </li>
              ) : null}
            </ul>
          ) : (
            <CfLoadingCard
              title="Carregando indicadores"
              description="Obtendo saldos do snapshot histórico."
              variant="compact"
            />
          )}
          {payload ? (
            <p className="cf-settlements-quality" role="note">
              Consulta operacional — não é o relatório oficial MATR460 (
              {STATUS_LABELS[payload.status] ?? payload.status}).
            </p>
          ) : null}
        </CfSectionCard>
      ) : null}

      {showData && payload && payload.summariesByType.length > 0 ? (
        <CfSectionCard
          title="Resumo por tipo de produto"
          hint={CF_HELP.stockInventory.summaryType}
        >
          <ul
            className="cf-settlements-summary"
            aria-label="Resumo por tipo de produto"
          >
            {payload.summariesByType.map((group) => (
              <li key={group.productType ?? "sem-tipo"}>
                <span className="cf-settlements-summary-label">
                  {group.productType ?? "Sem tipo"} — {group.itemCount} itens
                </span>
                <strong>{formatAmount(group.totalStockValue)}</strong>
              </li>
            ))}
          </ul>
        </CfSectionCard>
      ) : null}

      {showData && payload && payload.summariesByWarehouse.length > 0 ? (
        <CfSectionCard
          title="Resumo por armazém"
          hint={CF_HELP.stockInventory.summaryWarehouse}
        >
          <ul
            className="cf-settlements-summary"
            aria-label="Resumo por armazém"
          >
            {payload.summariesByWarehouse.map((group) => (
              <li
                key={`${group.branchCode ?? ""}-${group.warehouse ?? "sem-armazem"}`}
              >
                <span className="cf-settlements-summary-label">
                  Armazém {group.warehouse ?? "—"} · Filial{" "}
                  {group.branchCode ?? "—"} — {group.itemCount} itens
                </span>
                <strong>{formatAmount(group.totalStockValue)}</strong>
              </li>
            ))}
          </ul>
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
        />
      ) : null}
      </div>
    </section>
  );
}
