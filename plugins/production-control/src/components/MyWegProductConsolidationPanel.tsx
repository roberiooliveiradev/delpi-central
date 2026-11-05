import { HelpTooltip } from "@delpi/plugin-ui/index";
import { useEffect, useMemo, useState } from "react";

import { fetchMyWegNeedBatchesCompareProducts } from "../api/ppcApi";
import { httpErrorStatus } from "../api/httpClient";
import { copy } from "../content/copy";
import { helpTooltips } from "../content/helpTooltips";
import type {
  MyWegProductConsolidation,
  MyWegCompareProductsPayload,
} from "../types";
import { formatDecimalString } from "../utils/formatDecimalString";
import { DataTableSection, type DataTableColumn } from "./dataTableUi";

type Props = {
  fromId: string;
  toId: string;
  search: string;
};

const texts = copy.mywegNeeds.evolution.products;
const PAGE_SIZE = 50;

function formatRemessaBr(value: string | null | undefined): string {
  const text = (value ?? "").trim();
  if (!text) return "—";
  if (/^\d{4}-\d{2}-\d{2}/.test(text)) {
    const [y, m, d] = text.slice(0, 10).split("-");
    return `${d}/${m}/${y}`;
  }
  return text;
}

function situationLabel(situation: string): string {
  switch (situation) {
    case "increased":
      return texts.situation.increased;
    case "decreased":
      return texts.situation.decreased;
    case "unchanged":
      return texts.situation.unchanged;
    case "stable_with_date_changes":
      return texts.situation.stableWithDateChanges;
    case "appeared":
      return texts.situation.appeared;
    case "disappeared":
      return texts.situation.disappeared;
    default:
      return situation;
  }
}

function situationClass(situation: string): string {
  switch (situation) {
    case "increased":
    case "appeared":
      return "ppc-myweg-needs__movement ppc-myweg-needs__movement--up";
    case "decreased":
    case "disappeared":
      return "ppc-myweg-needs__movement ppc-myweg-needs__movement--down";
    case "stable_with_date_changes":
      return "ppc-myweg-needs__movement ppc-myweg-needs__movement--in";
    default:
      return "ppc-myweg-needs__movement";
  }
}

function movementLabel(movement: string): string {
  const base = copy.mywegNeeds.evolution.movement;
  switch (movement) {
    case "increased":
      return base.increased;
    case "decreased":
      return base.decreased;
    case "appeared":
      return base.appeared;
    case "disappeared":
      return base.disappeared;
    case "unchanged":
      return base.unchanged;
    default:
      return movement;
  }
}

function productLabel(row: MyWegProductConsolidation): string {
  if (row.identityConfirmed && row.verifiedProductCode) {
    return row.verifiedProductCode;
  }
  return (
    row.verifiedProductCode ||
    row.materialWegTratado ||
    row.codigoReferenciaWeg ||
    row.productKey ||
    "—"
  );
}

function ProductDetail({
  row,
  fromLabel,
  toLabel,
}: {
  row: MyWegProductConsolidation;
  fromLabel: string;
  toLabel: string;
}) {
  return (
    <div className="ppc-myweg-needs__product-detail">
      <p className="ppc-myweg-needs__evolution-note">
        <strong>{texts.detailPair}:</strong> {fromLabel} → {toLabel}
      </p>
      <p className="ppc-myweg-needs__evolution-note">
        <strong>{texts.detailTotals}:</strong>{" "}
        {formatDecimalString(row.previousQuantityUn)} UN →{" "}
        {formatDecimalString(row.currentQuantityUn)} UN (
        {formatDecimalString(row.deltaQuantityUn)} UN)
      </p>
      {!row.identityConfirmed ? (
        <p className="ppc-myweg-needs__evolution-note" role="status">
          {texts.identityUnconfirmed}
        </p>
      ) : null}
      <div className="ppc-myweg-needs__shifts-table-wrap">
        <table className="ppc-myweg-needs__shifts-table">
          <caption className="ppc-myweg-needs__product-detail-caption">
            {texts.remessaTableTitle}
          </caption>
          <thead>
            <tr>
              <th scope="col">{texts.remessaColumns.remessa}</th>
              <th scope="col">{texts.remessaColumns.previous}</th>
              <th scope="col">{texts.remessaColumns.current}</th>
              <th scope="col">{texts.remessaColumns.delta}</th>
              <th scope="col">{texts.remessaColumns.situation}</th>
            </tr>
          </thead>
          <tbody>
            {row.remessas.map((item) => (
              <tr key={`${row.productKey}|${item.remessa}|${item.movement}`}>
                <td>{formatRemessaBr(item.remessa)}</td>
                <td>{formatDecimalString(item.previousQuantityUn)}</td>
                <td>{formatDecimalString(item.currentQuantityUn)}</td>
                <td>{formatDecimalString(item.deltaQuantityUn)}</td>
                <td>
                  <span className={situationClass(item.movement)}>
                    {movementLabel(item.movement)}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {row.probableDateShifts.length > 0 ? (
        <div className="ppc-myweg-needs__product-shifts">
          <h4>{texts.relatedShiftsTitle}</h4>
          <p className="ppc-myweg-needs__evolution-note">{texts.relatedShiftsNote}</p>
          <ul>
            {row.probableDateShifts.map((shift, index) => (
              <li
                key={`${shift.productKey}|${shift.fromRemessa}|${shift.toRemessa}|${index}`}
              >
                {shift.kind === "possible_advancement"
                  ? texts.shiftAdvancement
                  : shift.kind === "possible_postponement"
                    ? texts.shiftPostponement
                    : texts.shiftOther}
                : {formatDecimalString(shift.quantityUn)} UN ·{" "}
                {formatRemessaBr(shift.fromRemessa)} → {formatRemessaBr(shift.toRemessa)}
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </div>
  );
}

export function MyWegProductConsolidationPanel({ fromId, toId, search }: Props) {
  const [page, setPage] = useState(1);
  const [payload, setPayload] = useState<MyWegCompareProductsPayload | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<number | null>(null);
  const [expandedKey, setExpandedKey] = useState<string | null>(null);

  useEffect(() => {
    setPage(1);
    setExpandedKey(null);
  }, [fromId, toId, search]);

  useEffect(() => {
    if (!fromId || !toId || fromId === toId) {
      setPayload(null);
      return;
    }
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    setStatus(null);
    void fetchMyWegNeedBatchesCompareProducts({
      fromBatchId: fromId,
      toBatchId: toId,
      search,
      page,
      pageSize: PAGE_SIZE,
      changesOnly: true,
      signal: controller.signal,
    })
      .then((data) => {
        if (!controller.signal.aborted) setPayload(data);
      })
      .catch((err) => {
        if (controller.signal.aborted) return;
        setPayload(null);
        setStatus(httpErrorStatus(err));
        setError(err instanceof Error ? err.message : texts.loadError);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [fromId, toId, search, page]);

  const columns = useMemo<DataTableColumn<MyWegProductConsolidation>[]>(
    () => [
      {
        key: "product",
        header: texts.columns.product,
        render: (row) => (
          <span>
            <span className="ppc-myweg-needs__shifts-product">{productLabel(row)}</span>
            {!row.identityConfirmed ? (
              <span className="ppc-myweg-needs__shifts-identity">
                {texts.identityUnconfirmed}
              </span>
            ) : null}
          </span>
        ),
      },
      {
        key: "previous",
        header: texts.columns.previous,
        align: "right",
        render: (row) => formatDecimalString(row.previousQuantityUn),
      },
      {
        key: "current",
        header: texts.columns.current,
        align: "right",
        render: (row) => formatDecimalString(row.currentQuantityUn),
      },
      {
        key: "delta",
        header: texts.columns.delta,
        align: "right",
        render: (row) => (
          <span className={situationClass(row.situation)}>
            {formatDecimalString(row.deltaQuantityUn)}
          </span>
        ),
      },
      {
        key: "percent",
        header: texts.columns.percent,
        align: "right",
        render: (row) =>
          row.percentChange == null ? "—" : `${formatDecimalString(row.percentChange)}%`,
      },
      {
        key: "situation",
        header: texts.columns.situation,
        render: (row) => (
          <span className={situationClass(row.situation)}>{situationLabel(row.situation)}</span>
        ),
      },
      {
        key: "details",
        header: texts.columns.details,
        render: (row) => (
          <button
            type="button"
            className="ppc-btn ppc-btn--secondary"
            aria-expanded={expandedKey === row.productKey}
            onClick={() =>
              setExpandedKey((current) =>
                current === row.productKey ? null : row.productKey,
              )
            }
          >
            {expandedKey === row.productKey ? texts.hideDetails : texts.showDetails}
          </button>
        ),
      },
    ],
    [expandedKey],
  );

  if (loading && !payload) {
    return <p role="status">{texts.loading}</p>;
  }
  if (status === 403) {
    return (
      <div className="ppc-state ppc-state--error" role="alert">
        {texts.forbidden}
      </div>
    );
  }
  if (error) {
    return (
      <div className="ppc-state ppc-state--error" role="alert">
        {error}
      </div>
    );
  }
  if (!payload) {
    return null;
  }

  const expanded = payload.items.find((row) => row.productKey === expandedKey) ?? null;
  const fromLabel = formatRemessaBr(payload.fromBatch.collectionDate);
  const toLabel = formatRemessaBr(payload.toBatch.collectionDate);

  return (
    <section className="ppc-myweg-needs__products" aria-label={texts.title}>
      <header className="ppc-myweg-needs__products-header">
        <h3 className="ppc-myweg-needs__shifts-title">
          {texts.title}
          <HelpTooltip content={helpTooltips.mywegNeedsProductAnalysis} trigger="icon" />
        </h3>
        <p className="ppc-myweg-needs__evolution-note">{texts.intro}</p>
        <p className="ppc-myweg-needs__evolution-note" role="status">
          {texts.totalsHint(
            payload.totalProductsCompared,
            payload.totalProductsChanged,
            formatDecimalString(payload.totals.deltaQuantityUn),
          )}
        </p>
        <p className="ppc-myweg-needs__evolution-note">{payload.disclaimer}</p>
      </header>

      <DataTableSection
        title={texts.tableTitle}
        rows={payload.items}
        columns={columns}
        rowKey={(row) => row.productKey}
        emptyMessage={search ? copy.tableSection.emptyMessage : texts.empty}
        columnPreferencesKey="production-control:myweg-products:columns:v1"
        getRowClassName={(row) =>
          row.productKey === expandedKey ? "ppc-myweg-needs__product-row--expanded" : undefined
        }
        serverPagination={{
          page: payload.page,
          pageSize: payload.pageSize,
          total: payload.total,
          onPageChange: (nextPage) => setPage(nextPage),
          onPageSizeChange: () => {
            /* pageSize fixo 50 nesta etapa */
          },
        }}
      />

      {expanded ? (
        <ProductDetail row={expanded} fromLabel={fromLabel} toLabel={toLabel} />
      ) : null}
    </section>
  );
}
