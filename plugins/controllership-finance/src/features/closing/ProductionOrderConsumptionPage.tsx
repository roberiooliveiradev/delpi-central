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
            {total} OP(s) — página {data?.page ?? page} | proveniência:{" "}
            {String(data?.provenance ?? "api-delpi consumption-audit")}
          </p>
          <table className="cf-table" aria-label="Ordens de produção">
            <thead>
              <tr>
                <th>OP</th>
                <th>Produto</th>
                <th>Status</th>
                <th>Centro de trabalho</th>
                <th>Data</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row, idx) => (
                <tr key={String(row.productionOrder ?? row.op ?? idx)}>
                  <td>{String(row.productionOrder ?? row.op ?? "—")}</td>
                  <td>
                    {String(
                      row.productDescription ?? row.product ?? "—",
                    )}
                  </td>
                  <td>{String(row.status ?? "—")}</td>
                  <td>{String(row.workCenter ?? "—")}</td>
                  <td>{String(row.date ?? row.emissionDate ?? "—")}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="cf-settlements-actions">
            <button
              type="button"
              disabled={page <= 1}
              onClick={() => setPage((p) => p - 1)}
            >
              Anterior
            </button>
            <button
              type="button"
              disabled={page * 25 >= total}
              onClick={() => setPage((p) => p + 1)}
            >
              Próxima
            </button>
          </div>
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
