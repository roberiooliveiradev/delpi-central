import { useCallback, useEffect, useState } from "react";
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
  ClosingHero,
  type ClosingHeroMetric,
} from "../../app/ClosingHero";
import {
  getProductionOrderConsumption,
  getProductionOrderConsumptionDetail,
  type DateType,
  type ProductionOrderConsumptionPayload,
} from "../../api/productionOrderConsumptionApi";
import { formatCivilDate } from "../../utils/formatters";

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

const DATE_FIELD: Record<DateType, string[]> = {
  emission: ["emissionDate", "emission_date", "date"],
  finished: ["finishedAt", "finished_at", "date"],
  appointment: ["appointmentDate", "appointment_date", "date"],
};

function rowDate(row: R04Row, dateType: DateType): string | null {
  for (const key of DATE_FIELD[dateType]) {
    const value = row[key];
    if (typeof value === "string" && value) return value;
  }
  return null;
}

function formatDateCell(row: R04Row, dateType: DateType): string {
  const raw = rowDate(row, dateType);
  if (!raw) return "—";
  const formatted = formatCivilDate(raw.slice(0, 10));
  return formatted || "—";
}

function R04_COLUMNS(dateType: DateType): DataTableColumn<R04Row>[] {
  return [
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
      // Código técnico do produtor — semântica oficial não
      // comprovada no contrato; apresentar o código real.
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
      render: (row) => formatDateCell(row, dateType),
    },
  ];
}

/** Campos escalares do contrato de detalhe, na ordem de exibição. */
const DETAIL_FIELD_ORDER: [string, string][] = [
  ["productionOrder", "OP"],
  ["orderNumber", "Número da ordem"],
  ["orderItem", "Item"],
  ["orderSequence", "Sequência"],
  ["productCode", "Produto"],
  ["productDescription", "Descrição"],
  ["unitOfMeasure", "Unidade"],
  ["plannedQuantity", "Quantidade prevista"],
  ["producedQuantity", "Quantidade produzida"],
  ["status", "Status"],
  ["orderType", "Tipo da ordem"],
  ["emissionDate", "Data de emissão"],
  ["plannedStartDate", "Início previsto"],
  ["dueDate", "Data de fim prevista"],
  ["finishedAt", "Encerrada em"],
];

function snakeKey(camel: string): string {
  return camel.replace(/[A-Z]/g, (c) => `_${c.toLowerCase()}`);
}

function DetailEntries({ payload }: { payload: R04Row }) {
  const entries: [string, string][] = [];
  for (const [key, label] of DETAIL_FIELD_ORDER) {
    const value = payload[key] ?? payload[snakeKey(key)];
    if (value !== undefined && value !== null && value !== "") {
      entries.push([label, String(value)]);
    }
  }
  const dateKeys = new Set([
    "Data de emissão",
    "Início previsto",
    "Data de fim prevista",
    "Encerrada em",
  ]);
  return (
    <dl className="cf-attention-facts">
      {entries.map(([label, value]) => (
        <div key={label} className="cf-attention-facts__row">
          <dt>{label}</dt>
          <dd>
            {dateKeys.has(label)
              ? formatCivilDate(String(value).slice(0, 10)) ||
                String(value)
              : String(value)}
          </dd>
        </div>
      ))}
    </dl>
  );
}

function detailRows(payload: ProductionOrderConsumptionPayload): R04Row {
  const rows = Array.isArray(payload.items)
    ? (payload.items as R04Row[])
    : Array.isArray(payload.orders)
      ? (payload.orders as R04Row[])
      : [];
  if (rows.length > 0) return rows[0];
  const rest = { ...(payload as unknown as R04Row) };
  delete rest.items;
  delete rest.orders;
  return rest;
}

const DETAIL_LIST_KEYS = [
  "materials",
  "components",
  "consumption",
  "order_items",
];

function detailList(payload: R04Row): R04Row[] | null {
  for (const key of DETAIL_LIST_KEYS) {
    const value = payload[key];
    if (
      Array.isArray(value) &&
      value.length > 0 &&
      typeof value[0] === "object"
    ) {
      return value as R04Row[];
    }
  }
  return null;
}

function detailListColumns(sample: R04Row): DataTableColumn<R04Row>[] {
  return Object.keys(sample)
    .slice(0, 6)
    .map((key) => ({
      key,
      header: key,
      render: (row) => String(row[key] ?? "—"),
    }));
}

/** R04 — Consumo por OP (visão operacional; paridade MATR860 pendente). */
export function ProductionOrderConsumptionPage({
  reportContext,
}: {
  reportContext: { period: string };
}) {
  const period = reportContext.period;
  const [branch, setBranch] = useState<"01" | "02">("01");
  const [dateType, setDateType] = useState<DateType>("emission");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [refreshNonce, setRefreshNonce] = useState(0);
  const [data, setData] = useState<ProductionOrderConsumptionPayload | null>(
    null,
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [updatedAt, setUpdatedAt] = useState<Date | null>(null);
  const [selectedOp, setSelectedOp] = useState<string | null>(null);
  const [detail, setDetail] = useState<{
    kind: "loading" | "ready" | "error";
    payload?: ProductionOrderConsumptionPayload;
    message?: string;
  } | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    getProductionOrderConsumption({
      period,
      branch,
      dateType,
      search: search || undefined,
      page,
    })
      .then((payload) => {
        if (!cancelled) {
          setData(payload);
          setUpdatedAt(new Date());
        }
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
  }, [period, branch, dateType, search, page, refreshNonce]);

  const openDetail = useCallback(
    (op: string) => {
      setSelectedOp(op);
      setDetail({ kind: "loading" });
      getProductionOrderConsumptionDetail(period, op, branch)
        .then((payload) =>
          setDetail({ kind: "ready", payload }),
        )
        .catch((exc: unknown) =>
          setDetail({
            kind: "error",
            message:
              exc instanceof Error
                ? exc.message
                : "Falha ao consultar o detalhe.",
          }),
        );
    },
    [period, branch],
  );

  const rows = Array.isArray(data?.orders)
    ? (data?.orders as R04Row[])
    : Array.isArray(data?.items)
      ? (data?.items as R04Row[])
      : [];
  const total = typeof data?.total === "number" ? data.total : rows.length;

  const clearFilters = useCallback(() => {
    setBranch("01");
    setDateType("emission");
    setSearch("");
    setPage(1);
  }, []);

  const heroMetrics: ClosingHeroMetric[] = [
    {
      id: "ops",
      label: "Ordens de produção",
      value: loading && data === null ? "—" : total.toLocaleString("pt-BR"),
      hint: `competência ${period} · filial ${branch}`,
    },
    {
      id: "parity",
      label: "Paridade oficial",
      value: "Pendente",
      tone: "warning",
      hint: "visão operacional — equivalência MATR860 não homologada",
    },
  ];

  return (
    <div className="cf-page-stack" aria-label="Consumo por OP">
      <ClosingHero
        title="Consumo por OP"
        subtitle="Consulta operacional de consumo por ordem de produção da competência selecionada."
        updatedAt={updatedAt}
        onRefresh={() => setRefreshNonce((n) => n + 1)}
        refreshing={loading}
        metrics={heroMetrics}
        filters={
          <fieldset className="cf-settlements-filters">
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
          </fieldset>
        }
        onClearFilters={clearFilters}
        notice={
          <CfStateBanner>
            <p className="cf-banner-title">
              Visão operacional — paridade oficial pendente
            </p>
            <p className="cf-banner-text">
              Consumo por ordem de produção via produtor
              consumption-audit. A equivalência com o relatório oficial
              MATR860 ainda não foi homologada.
            </p>
          </CfStateBanner>
        }
      />
      {loading && data === null ? (
        <CfLoadingCard
          title="Carregando OPs…"
          variant="compact"
          description="Consultando o produtor consumption-audit."
        />
      ) : error && data === null ? (
        <CfStateBanner>
          <p className="cf-banner-title">Falha na consulta</p>
          <p className="cf-banner-text">{error}</p>
        </CfStateBanner>
      ) : (
        <>
          {!loading && rows.length === 0 ? (
            <CfEmptyState
              classNames={cfEmptyStateClassNames}
              defaultMessage="Nenhuma OP encontrada para os filtros informados."
            />
          ) : (
            <DataTableSection<R04Row>
              title={`Ordens de produção — ${total.toLocaleString("pt-BR")} OP(s)`}
              titleHint={`Proveniência: ${String(
                data?.provenance ?? "api-delpi consumption-audit",
              )}`}
              columns={R04_COLUMNS(dateType)}
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
              onRowClick={(row) => {
                const op = String(
                  row.productionOrder ?? row.op ?? "",
                );
                if (op) openDetail(op);
              }}
              serverPagination={{
                page,
                pageSize: 25,
                total,
                onPageChange: setPage,
              }}
            />
          )}
          {Array.isArray(data?.limitations) &&
          data!.limitations!.length > 0 ? (
            <ul className="cf-muted" aria-label="Limitações">
              {data!.limitations!.map((lim, i) => (
                <li key={i}>{lim}</li>
              ))}
            </ul>
          ) : null}
          {selectedOp ? (
            <section
              className="cf-page-stack"
              aria-label={`Detalhe da OP ${selectedOp}`}
            >
              <h2 className="cf-catalog-group__title">
                Detalhe da OP {selectedOp}
              </h2>
              {detail?.kind === "loading" ? (
                <CfLoadingCard
                  title="Carregando detalhe da OP…"
                  variant="compact"
                />
              ) : detail?.kind === "error" ? (
                <CfStateBanner>
                  <p className="cf-banner-title">Falha no detalhe</p>
                  <p className="cf-banner-text">{detail.message}</p>
                </CfStateBanner>
              ) : detail?.kind === "ready" && detail.payload ? (
                <>
                  <DetailEntries
                    payload={detailRows(detail.payload)}
                  />
                  {(() => {
                    const list = detailList(
                      detail.payload as unknown as R04Row,
                    );
                    return list ? (
                      <DataTableSection<R04Row>
                        title="Materiais e consumo"
                        columns={detailListColumns(list[0])}
                        rows={list}
                        rowKey={(row) =>
                          String(
                            row.productCode ??
                              row.product_code ??
                              JSON.stringify(row),
                          )
                        }
                        hideSearch
                        emptyMessage="Sem materiais no contrato."
                      />
                    ) : null;
                  })()}
                </>
              ) : null}
            </section>
          ) : null}
        </>
      )}
    </div>
  );
}
