import { useEffect, useMemo, useState } from "react";

import { fetchMyWegNeedBatchesCompare } from "../api/ppcApi";
import { httpErrorStatus } from "../api/httpClient";
import { copy } from "../content/copy";
import { helpTooltips } from "../content/helpTooltips";
import type { MyWegComparePayload, MyWegNeedsBatchSummary } from "../types";
import { formatDecimalString } from "../utils/formatDecimalString";
import { DataTableSection, type DataTableColumn } from "./dataTableUi";

type Props = {
  historyItems: MyWegNeedsBatchSummary[];
  selectedBatchId: string | null;
};

const texts = copy.mywegNeeds.evolution;

function movementLabel(movement: string): string {
  switch (movement) {
    case "increased":
      return texts.movement.increased;
    case "decreased":
      return texts.movement.decreased;
    case "appeared":
      return texts.movement.appeared;
    case "disappeared":
      return texts.movement.disappeared;
    case "unchanged":
      return texts.movement.unchanged;
    default:
      return movement;
  }
}

export function MyWegPlanningEvolutionPanel({ historyItems, selectedBatchId }: Props) {
  const [fromId, setFromId] = useState<string>("");
  const [toId, setToId] = useState<string>("");
  const [billingMode, setBillingMode] = useState<"none" | "indicative">("none");
  const [payload, setPayload] = useState<MyWegComparePayload | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<number | null>(null);

  useEffect(() => {
    if (historyItems.length < 2) {
      setFromId("");
      setToId("");
      return;
    }
    const to = selectedBatchId || historyItems[0]?.id || "";
    const from =
      historyItems.find((item) => item.id !== to)?.id || historyItems[1]?.id || "";
    setToId(to);
    setFromId(from);
  }, [historyItems, selectedBatchId]);

  useEffect(() => {
    if (!fromId || !toId || fromId === toId) {
      setPayload(null);
      return;
    }
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    setStatus(null);
    void fetchMyWegNeedBatchesCompare({
      fromBatchId: fromId,
      toBatchId: toId,
      billingMode,
      page: 1,
      pageSize: 50,
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
  }, [fromId, toId, billingMode]);

  const columns = useMemo<DataTableColumn<MyWegComparePayload["items"][number]>[]>(
    () => [
      {
        key: "product",
        header: texts.columns.product,
        render: (row) =>
          row.verifiedProductCode || row.materialWegTratado || row.productKey || "—",
      },
      {
        key: "remessa",
        header: texts.columns.remessa,
        render: (row) => row.remessa,
      },
      {
        key: "movement",
        header: texts.columns.movement,
        render: (row) => {
          const label = movementLabel(row.movement);
          return row.inHorizon14d ? `${label} · ${texts.horizonBadge}` : label;
        },
      },
      {
        key: "prev",
        header: texts.columns.previous,
        align: "right",
        render: (row) => formatDecimalString(row.previousQuantityUn),
      },
      {
        key: "curr",
        header: texts.columns.current,
        align: "right",
        render: (row) => formatDecimalString(row.currentQuantityUn),
      },
      {
        key: "delta",
        header: texts.columns.delta,
        align: "right",
        render: (row) => formatDecimalString(row.deltaQuantityUn),
      },
    ],
    [],
  );

  if (historyItems.length < 2) {
    return (
      <section className="ppc-myweg-needs__evolution" aria-label={texts.title}>
        <h2>{texts.title}</h2>
        <p className="ppc-myweg-needs__evolution-note">{texts.insufficient}</p>
      </section>
    );
  }

  const summary = payload?.observed.summary;
  const changedItems = (payload?.items ?? []).filter((row) => row.movement !== "unchanged");

  return (
    <section className="ppc-myweg-needs__evolution" aria-label={texts.title}>
      <h2 title={helpTooltips.mywegNeedsEvolution}>{texts.title}</h2>
      <p className="ppc-myweg-needs__evolution-note">{texts.intro}</p>

      <div className="ppc-myweg-needs__toolbar">
        <label className="ppc-myweg-needs__history">
          {texts.fromLabel}
          <select
            value={fromId}
            onChange={(event) => setFromId(event.target.value)}
            aria-label={texts.fromLabel}
          >
            {historyItems.map((item) => (
              <option key={`from-${item.id}`} value={item.id}>
                {item.collectionDate} · {item.recordCount} regs
              </option>
            ))}
          </select>
        </label>
        <label className="ppc-myweg-needs__history">
          {texts.toLabel}
          <select
            value={toId}
            onChange={(event) => setToId(event.target.value)}
            aria-label={texts.toLabel}
          >
            {historyItems.map((item) => (
              <option key={`to-${item.id}`} value={item.id}>
                {item.collectionDate} · {item.recordCount} regs
              </option>
            ))}
          </select>
        </label>
        <label className="ppc-myweg-needs__history">
          {texts.billingLabel}
          <select
            value={billingMode}
            onChange={(event) =>
              setBillingMode(event.target.value === "indicative" ? "indicative" : "none")
            }
          >
            <option value="none">{texts.billingNone}</option>
            <option value="indicative">{texts.billingIndicative}</option>
          </select>
        </label>
      </div>

      {loading ? <p role="status">{texts.loading}</p> : null}
      {status === 403 ? (
        <div className="ppc-state ppc-state--error" role="alert">
          {texts.forbidden}
        </div>
      ) : null}
      {status === 409 ? (
        <div className="ppc-state" role="status">
          {texts.insufficient}
        </div>
      ) : null}
      {error && status !== 403 && status !== 409 ? (
        <div className="ppc-state ppc-state--error" role="alert">
          {error}
        </div>
      ) : null}

      {payload && !loading ? (
        <>
          <p className="ppc-myweg-needs__evolution-scope">
            {payload.scope.customerName} · cliente {payload.scope.protheusCustomerCode}/
            {payload.scope.protheusCustomerStore}
          </p>
          <div className="ppc-myweg-needs__summary" aria-label={texts.summaryAria}>
            <article className="ppc-myweg-needs__kpi">
              <h3>{texts.kpi.increased}</h3>
              <p>{summary?.increased ?? 0}</p>
            </article>
            <article className="ppc-myweg-needs__kpi">
              <h3>{texts.kpi.decreased}</h3>
              <p>{summary?.decreased ?? 0}</p>
            </article>
            <article className="ppc-myweg-needs__kpi">
              <h3>{texts.kpi.appeared}</h3>
              <p>{summary?.appeared ?? 0}</p>
            </article>
            <article className="ppc-myweg-needs__kpi">
              <h3>{texts.kpi.disappeared}</h3>
              <p>{summary?.disappeared ?? 0}</p>
            </article>
            <article className="ppc-myweg-needs__kpi">
              <h3>{texts.kpi.horizon}</h3>
              <p>{summary?.horizon_14d_changes ?? 0}</p>
            </article>
          </div>
          <p className="ppc-myweg-needs__evolution-note">{payload.observed.disclaimer}</p>
          <aside className="ppc-myweg-needs__billing" aria-label={texts.billingAria}>
            <h3>{texts.billingTitle}</h3>
            <p>{payload.billing.disclaimer || texts.billingSkipped}</p>
            {payload.billing.status === "unavailable" ? (
              <p role="status">{texts.billingUnavailable}</p>
            ) : null}
          </aside>
          {changedItems.length === 0 ? (
            <p role="status">{texts.noChanges}</p>
          ) : (
            <DataTableSection
              title={texts.tableTitle}
              rows={changedItems}
              columns={columns}
              rowKey={(row) => `${row.productKey}|${row.remessa}|${row.movement}`}
              emptyMessage={texts.noChanges}
              columnPreferencesKey="production-control:myweg-evolution:columns:v1"
            />
          )}
        </>
      ) : null}
    </section>
  );
}
