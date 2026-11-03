import { useEffect, useState } from "react";
import {
  CfEmptyState,
  CfLoadingCard,
  CfSelectField,
  CfStateBanner,
  cfEmptyStateClassNames,
} from "../../app/controllershipFinanceUi";
import {
  FilterInputField,
} from "../../app/cfFiltersUi";
import {
  DataTableSection,
  type DataTableColumn,
} from "../../app/cfDataTableUi";
import {
  getProductionOrderConsumption,
  type DateType,
  type ProductionOrderConsumptionPayload,
} from "../../api/productionOrderConsumptionApi";

const BRANCHES = [
  { value: "01", label: "Filial 01" },
  { value: "02", label: "Filial 02" },
];

const DATE_TYPES: { value: DateType; label: string }[] = [
  { value: "emission", label: "Emissão da OP" },
  { value: "finished", label: "Finalização" },
  { value: "appointment", label: "Apontamento" },
];

type R04Row = Record<string, unknown>;

const R04_COLUMNS: DataTableColumn<R04Row>[] = [
  {
    key: "op",
    header: "OP",
    render: (row) => String(row.productionOrder ?? row.op ?? "—"),
    sortable: true,
    sortValue: (row) =>
      String(row.productionOrder ?? row.op ?? "") || null,
  },
  {
    key: "product",
    header: "Produto",
    render: (row) => String(row.productCode ?? "—"),
  },
  {
    key: "description",
    header: "Descrição",
    render: (row) =>
      String(row.productDescription ?? row.product ?? "—"),
  },
  {
    key: "status",
    header: "Status",
    align: "center",
    render: (row) => String(row.status ?? "—"),
  },
  {
    key: "workCenter",
    header: "Centro de trabalho",
    render: (row) => String(row.workCenter ?? "—"),
  },
  {
    key: "date",
    header: "Data",
    render: (row) => String(row.date ?? row.emissionDate ?? "—"),
  },
];

/** R04 — Consumo por OP (visão operacional; paridade MATR860 pendente). */
export function ProductionOrderConsumptionPage({
  reportContext,
}: {
  reportContext: { period: string };
}) {
  const [branch, setBranch] = useState<"01" | "02">("01");
  const [dateType, setDateType] = useState<DateType>("emission");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [data, setData] = useState<ProductionOrderConsumptionPayload | null>(
    null,
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    getProductionOrderConsumption({
      period: reportContext.period,
      branch,
      dateType,
      search: search || undefined,
      page,
    })
      .then((payload) => {
        if (!cancelled) setData(payload);
      })
      .catch((exc: unknown) => {
        if (!cancelled)
          setError(
            exc instanceof Error ? exc.message : "Falha ao consultar a BFF.",
          );
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [reportContext.period, branch, dateType, search, page]);

  const rows = Array.isArray(data?.orders)
    ? (data?.orders as Record<string, unknown>[])
    : Array.isArray(data?.items)
      ? (data?.items as Record<string, unknown>[])
      : [];
  const total = typeof data?.total === "number" ? data.total : rows.length;

  return (
    <div className="cf-page-stack">
      <CfStateBanner>
        <p className="cf-banner-title">
          Visão operacional — paridade oficial pendente
        </p>
        <p className="cf-banner-text">
          Consumo por ordem de produção via contrato vigente do produtor
          TOTVS (consumption-audit). A equivalência com o relatório
          oficial MATR860 ainda não foi homologada.
        </p>
      </CfStateBanner>
      <div className="cf-settlements-actions" role="group" aria-label="Filtros">
        <CfSelectField
          label="Filial"
          value={branch}
          onChange={(v) => {
            setBranch(v as "01" | "02");
            setPage(1);
          }}
          options={BRANCHES}
        />
        <CfSelectField
          label="Tipo de data"
          value={dateType}
          onChange={(v) => {
            setDateType(v as DateType);
            setPage(1);
          }}
          options={DATE_TYPES}
        />
        <FilterInputField
          id="cf-r04-search"
          label="Busca OP / produto"
          type="search"
          value={search}
          onChange={(value) => {
            setSearch(value);
            setPage(1);
          }}
          placeholder="Fragmento da OP ou produto"
        />
      </div>
      {loading ? (
        <CfLoadingCard
          title="Carregando OPs…"
          variant="compact"
          description="Consultando o produtor consumption-audit."
        />
      ) : error ? (
        <CfStateBanner>
          <p className="cf-banner-title">Falha na consulta</p>
          <p className="cf-banner-text">{error}</p>
        </CfStateBanner>
      ) : rows.length === 0 ? (
        <CfEmptyState
          classNames={cfEmptyStateClassNames}
          defaultMessage="Nenhuma OP encontrada para os filtros informados."
        />
      ) : (
        <>
          <p className="cf-muted" aria-live="polite">
            {total} OP(s) — proveniência:{" "}
            {String(data?.provenance ?? "api-delpi consumption-audit")}
          </p>
          <DataTableSection<Record<string, unknown>>
            title="Ordens de produção"
            columns={R04_COLUMNS}
            rows={rows}
            rowKey={(row) =>
              String(
                row.productionOrder ??
                  row.op ??
                  row.orderNumber ??
                  "row",
              )
            }
            hideSearch
            emptyMessage="Nenhuma OP encontrada para os filtros informados."
            serverPagination={{
              page,
              pageSize: 25,
              total,
              onPageChange: setPage,
            }}
          />
          {Array.isArray(data?.limitations) && data!.limitations!.length > 0 ? (
            <ul className="cf-muted" aria-label="Limitações">
              {data!.limitations!.map((lim, i) => (
                <li key={i}>{lim}</li>
              ))}
            </ul>
          ) : null}
        </>
      )}
    </div>
  );
}
