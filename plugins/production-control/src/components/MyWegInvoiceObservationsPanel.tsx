import { HelpTooltip } from "@delpi/plugin-ui/index";
import { Filter, Search } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";

import {
  fetchMyWegInvoiceObservationItems,
  fetchMyWegInvoiceObservations,
} from "../api/ppcApi";
import { httpErrorStatus } from "../api/httpClient";
import { copy } from "../content/copy";
import { helpTooltips } from "../content/helpTooltips";
import type {
  MyWegInvoiceObservationItem,
  MyWegInvoiceObservationSummary,
} from "../types";
import { formatDecimalStringFixed } from "../utils/formatDecimalString";
import {
  parseLocalIsoDate,
  previousCalendarDayIso,
} from "../utils/mywegInvoiceDocumentDate";
import { DataTableSection, type DataTableColumn } from "./dataTableUi";
import { MyWegInvoiceMonthCalendar } from "./MyWegInvoiceMonthCalendar";

const texts = copy.mywegNeeds.invoices;
const PAGE_SIZE = 50;

type InvoiceGroup = {
  key: string;
  invoiceNumber: string;
  invoiceSeries: string;
  itemCount: number;
};

function formatIsoDateBr(value: string | null | undefined): string {
  const text = (value ?? "").trim();
  if (!/^\d{4}-\d{2}-\d{2}/.test(text)) return text || "—";
  const [y, m, d] = text.slice(0, 10).split("-");
  return `${d}/${m}/${y}`;
}

function observationStatusLabel(status: string): string {
  switch (status) {
    case "with_records":
      return texts.statusWithRecords;
    case "empty_signaled_by_sap":
      return texts.statusEmptySap;
    default:
      return texts.statusOther(status);
  }
}

function groupItemsByInvoice(items: MyWegInvoiceObservationItem[]): InvoiceGroup[] {
  const map = new Map<string, InvoiceGroup>();
  for (const item of items) {
    const number = (item.invoiceNumber || "").trim() || "—";
    const series = (item.invoiceSeries || "").trim() || "—";
    const key = `${number}::${series}`;
    const current = map.get(key);
    if (current) {
      current.itemCount += 1;
    } else {
      map.set(key, {
        key,
        invoiceNumber: number,
        invoiceSeries: series,
        itemCount: 1,
      });
    }
  }
  return Array.from(map.values()).sort((a, b) => {
    const byNumber = a.invoiceNumber.localeCompare(b.invoiceNumber, "pt-BR");
    if (byNumber !== 0) return byNumber;
    return a.invoiceSeries.localeCompare(b.invoiceSeries, "pt-BR");
  });
}

function pickDefaultObservation(
  items: MyWegInvoiceObservationSummary[],
): string | null {
  if (items.length === 0) return null;
  const withRecords = items.find((row) => row.observationStatus === "with_records");
  return (withRecords ?? items[0]).id;
}

export function MyWegInvoiceObservationsPanel() {
  const initialDate = useMemo(() => previousCalendarDayIso(), []);
  const initialParsed = parseLocalIsoDate(initialDate);
  const [appliedDate, setAppliedDate] = useState(initialDate);
  const [viewYear, setViewYear] = useState(initialParsed?.year ?? new Date().getFullYear());
  const [viewMonth, setViewMonth] = useState(
    initialParsed?.month ?? new Date().getMonth() + 1,
  );
  const [searchDraft, setSearchDraft] = useState("");
  const [search, setSearch] = useState("");
  const [listLoading, setListLoading] = useState(false);
  const [itemsLoading, setItemsLoading] = useState(false);
  const [listError, setListError] = useState<string | null>(null);
  const [itemsError, setItemsError] = useState<string | null>(null);
  const [observations, setObservations] = useState<MyWegInvoiceObservationSummary[]>(
    [],
  );
  const [selectedObservationId, setSelectedObservationId] = useState<string | null>(
    null,
  );
  const [allItems, setAllItems] = useState<MyWegInvoiceObservationItem[]>([]);
  const [observationStatus, setObservationStatus] = useState<string | null>(null);
  const [selectedInvoiceKey, setSelectedInvoiceKey] = useState<string | null>(null);
  const [itemPage, setItemPage] = useState(1);

  const selectedObservation = useMemo(
    () => observations.find((row) => row.id === selectedObservationId) ?? null,
    [observations, selectedObservationId],
  );

  const invoiceGroups = useMemo(() => groupItemsByInvoice(allItems), [allItems]);

  const selectedInvoiceItems = useMemo(() => {
    if (!selectedInvoiceKey) return allItems;
    return allItems.filter((item) => {
      const number = (item.invoiceNumber || "").trim() || "—";
      const series = (item.invoiceSeries || "").trim() || "—";
      return `${number}::${series}` === selectedInvoiceKey;
    });
  }, [allItems, selectedInvoiceKey]);

  const pagedItems = useMemo(() => {
    const start = (itemPage - 1) * PAGE_SIZE;
    return selectedInvoiceItems.slice(start, start + PAGE_SIZE);
  }, [itemPage, selectedInvoiceItems]);

  useEffect(() => {
    const date = appliedDate.trim();
    if (!date) {
      setObservations([]);
      setSelectedObservationId(null);
      setAllItems([]);
      setObservationStatus(null);
      setSelectedInvoiceKey(null);
      return;
    }

    const controller = new AbortController();
    setListLoading(true);
    setListError(null);
    setObservations([]);
    setSelectedObservationId(null);
    setAllItems([]);
    setObservationStatus(null);
    setSelectedInvoiceKey(null);

    void (async () => {
      try {
        const payload = await fetchMyWegInvoiceObservations({
          documentDate: date,
          page: 1,
          pageSize: 50,
          signal: controller.signal,
        });
        if (controller.signal.aborted) return;
        setObservations(payload.items);
        setSelectedObservationId(pickDefaultObservation(payload.items));
      } catch (err) {
        if (controller.signal.aborted) return;
        setListError(
          err instanceof Error ? err.message : texts.loadListError,
        );
        if (httpErrorStatus(err) === 403) {
          setListError(copy.mywegNeeds.forbidden);
        }
      } finally {
        if (!controller.signal.aborted) setListLoading(false);
      }
    })();

    return () => controller.abort();
  }, [appliedDate]);

  useEffect(() => {
    if (!selectedObservationId) {
      setAllItems([]);
      setObservationStatus(null);
      return;
    }
    const controller = new AbortController();
    setItemsLoading(true);
    setItemsError(null);
    setSelectedInvoiceKey(null);
    setItemPage(1);
    void (async () => {
      try {
        const first = await fetchMyWegInvoiceObservationItems({
          observationId: selectedObservationId,
          search,
          page: 1,
          pageSize: PAGE_SIZE,
          signal: controller.signal,
        });
        if (controller.signal.aborted) return;
        setObservationStatus(first.observationStatus);
        const collected = [...first.items];
        const totalPages = Math.min(Math.ceil(first.total / PAGE_SIZE) || 1, 10);
        for (let page = 2; page <= totalPages; page += 1) {
          const next = await fetchMyWegInvoiceObservationItems({
            observationId: selectedObservationId,
            search,
            page,
            pageSize: PAGE_SIZE,
            signal: controller.signal,
          });
          if (controller.signal.aborted) return;
          collected.push(...next.items);
        }
        setAllItems(collected);
      } catch (err) {
        if (controller.signal.aborted) return;
        setItemsError(
          err instanceof Error ? err.message : texts.loadItemsError,
        );
        setAllItems([]);
      } finally {
        if (!controller.signal.aborted) setItemsLoading(false);
      }
    })();
    return () => controller.abort();
  }, [search, selectedObservationId]);

  const onSelectDate = useCallback((iso: string) => {
    setAppliedDate(iso);
    const parsed = parseLocalIsoDate(iso);
    if (parsed) {
      setViewYear(parsed.year);
      setViewMonth(parsed.month);
    }
  }, []);

  const applyItemSearch = useCallback(() => {
    setSearch(searchDraft.trim());
    setItemPage(1);
  }, [searchDraft]);

  const columns = useMemo<DataTableColumn<MyWegInvoiceObservationItem>[]>(
    () => [
      {
        key: "invoiceNumber",
        header: texts.columns.invoiceNumber,
        render: (row) => row.invoiceNumber || "—",
      },
      {
        key: "invoiceSeries",
        header: texts.columns.invoiceSeries,
        render: (row) => row.invoiceSeries || "—",
      },
      {
        key: "materialWeg",
        header: texts.columns.material,
        render: (row) => row.materialWeg || "—",
      },
      {
        key: "delpiProductCode",
        header: texts.columns.delpiCode,
        render: (row) =>
          row.delpiProductCode?.trim() ||
          row.verifiedProductCode?.trim() ||
          row.informedProductCode?.trim() ||
          "—",
      },
      {
        key: "materialDescription",
        header: texts.columns.description,
        render: (row) => row.materialDescription?.trim() || "—",
      },
      {
        key: "quantityUn",
        header: texts.columns.qtyUn,
        align: "right",
        render: (row) =>
          formatDecimalStringFixed(row.quantityUn ?? row.quantityOriginal, 3),
      },
      {
        key: "sourceUnit",
        header: texts.columns.unit,
        render: (row) => row.sourceUnit || "—",
      },
      {
        key: "departureDate",
        header: texts.columns.departure,
        render: (row) => formatIsoDateBr(row.departureDate),
      },
    ],
    [],
  );

  return (
    <section className="ppc-myweg-needs__invoices" aria-label={texts.sectionAria}>
      <div
        className="ppc-myweg-needs__invoice-filter-bar"
        role="search"
        aria-label={texts.sectionAria}
      >
        <MyWegInvoiceMonthCalendar
          selectedIso={appliedDate}
          onSelectDate={onSelectDate}
          viewYear={viewYear}
          viewMonth={viewMonth}
          onViewChange={({ year, month }) => {
            setViewYear(year);
            setViewMonth(month);
          }}
        />

        <span className="ppc-myweg-needs__invoice-filter-divider" aria-hidden="true" />

        <label className="ppc-myweg-needs__invoice-date">
          <span className="ppc-myweg-needs__invoice-date-label">
            {texts.documentDateLabel}
            <HelpTooltip content={helpTooltips.mywegNeedsInvoices} trigger="icon" />
          </span>
          <input
            type="date"
            value={appliedDate}
            onChange={(event) => {
              const next = event.target.value;
              if (parseLocalIsoDate(next)) onSelectDate(next);
            }}
            aria-label={texts.documentDateLabel}
          />
        </label>

        <span className="ppc-myweg-needs__invoice-filter-divider" aria-hidden="true" />

        <label className="ppc-myweg-needs__invoice-search">
          <span className="ppc-sr-only">{texts.searchLabel}</span>
          <Search
            className="ppc-myweg-needs__invoice-search-icon"
            size={15}
            strokeWidth={1.85}
            aria-hidden
          />
          <input
            type="search"
            value={searchDraft}
            placeholder={texts.searchPlaceholder}
            onChange={(event) => setSearchDraft(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter") applyItemSearch();
            }}
            aria-label={texts.searchAria}
            disabled={!selectedObservationId}
          />
        </label>

        <button
          type="button"
          className="ppc-btn ppc-btn--primary ppc-btn--compact ppc-myweg-needs__invoice-filter-btn"
          onClick={applyItemSearch}
          disabled={!selectedObservationId}
        >
          <Filter size={14} strokeWidth={2} aria-hidden />
          {texts.applyItemSearch}
        </button>
      </div>

      {listLoading ? (
        <div className="ppc-state" role="status">
          {texts.loadingList}
        </div>
      ) : null}

      {listError ? (
        <div className="ppc-state ppc-state--error" role="alert">
          {listError}
        </div>
      ) : null}

      {appliedDate && !listLoading && !listError && observations.length === 0 ? (
        <div className="ppc-state" role="status">
          {texts.emptyForDate(formatIsoDateBr(appliedDate))}
        </div>
      ) : null}

      {observations.length > 0 ? (
        <div className="ppc-myweg-needs__invoice-layout">
          <aside className="ppc-myweg-needs__invoice-list" aria-label={texts.observationsAria}>
            <h3 className="ppc-myweg-needs__invoice-list-title">
              {texts.observationsTitle(formatIsoDateBr(appliedDate))}
            </h3>
            <ul className="ppc-myweg-needs__invoice-obs">
              {observations.map((obs) => {
                const active = obs.id === selectedObservationId;
                return (
                  <li key={obs.id}>
                    <button
                      type="button"
                      className={
                        active
                          ? "ppc-myweg-needs__invoice-obs-btn ppc-myweg-needs__invoice-obs-btn--active"
                          : "ppc-myweg-needs__invoice-obs-btn"
                      }
                      aria-pressed={active}
                      onClick={() => setSelectedObservationId(obs.id)}
                    >
                      <strong>{observationStatusLabel(obs.observationStatus)}</strong>
                      <span>
                        {texts.observationMeta(
                          obs.recordCount,
                          formatDecimalStringFixed(obs.totalQuantityUn, 3),
                        )}
                      </span>
                      <span className="ppc-myweg-needs__invoice-obs-id">
                        {obs.collectionId}
                      </span>
                    </button>
                  </li>
                );
              })}
            </ul>

            {invoiceGroups.length > 0 ? (
              <>
                <h4 className="ppc-myweg-needs__invoice-list-subtitle">
                  {texts.invoicesTitle}
                </h4>
                <ul className="ppc-myweg-needs__invoice-nfs">
                  <li>
                    <button
                      type="button"
                      className={
                        selectedInvoiceKey == null
                          ? "ppc-myweg-needs__invoice-nf-btn ppc-myweg-needs__invoice-nf-btn--active"
                          : "ppc-myweg-needs__invoice-nf-btn"
                      }
                      aria-pressed={selectedInvoiceKey == null}
                      onClick={() => {
                        setSelectedInvoiceKey(null);
                        setItemPage(1);
                      }}
                    >
                      {texts.allInvoices(allItems.length)}
                    </button>
                  </li>
                  {invoiceGroups.map((group) => {
                    const active = selectedInvoiceKey === group.key;
                    return (
                      <li key={group.key}>
                        <button
                          type="button"
                          className={
                            active
                              ? "ppc-myweg-needs__invoice-nf-btn ppc-myweg-needs__invoice-nf-btn--active"
                              : "ppc-myweg-needs__invoice-nf-btn"
                          }
                          aria-pressed={active}
                          onClick={() => {
                            setSelectedInvoiceKey(group.key);
                            setItemPage(1);
                          }}
                        >
                          {texts.invoiceLabel(
                            group.invoiceNumber,
                            group.invoiceSeries,
                            group.itemCount,
                          )}
                        </button>
                      </li>
                    );
                  })}
                </ul>
              </>
            ) : null}
          </aside>

          <div className="ppc-myweg-needs__invoice-detail">
            {selectedObservation?.observationStatus === "empty_signaled_by_sap" ? (
              <div className="ppc-state" role="status">
                {texts.emptySignaledHint}
              </div>
            ) : null}

            {itemsError ? (
              <div className="ppc-state ppc-state--error" role="alert">
                {itemsError}
              </div>
            ) : null}

            {selectedObservation &&
            observationStatus === "with_records" &&
            !itemsError ? (
              <DataTableSection<MyWegInvoiceObservationItem>
                title={texts.tableTitle}
                hint={texts.tableHint}
                columns={columns}
                rows={pagedItems}
                rowKey={(row) => row.id}
                loading={itemsLoading}
                emptyMessage={texts.emptyItems}
                hideSearch
                columnPreferencesKey="production-control:myweg-invoices:columns:v1"
                serverPagination={{
                  page: itemPage,
                  pageSize: PAGE_SIZE,
                  total: selectedInvoiceItems.length,
                  onPageChange: setItemPage,
                  onPageSizeChange: () => {
                    /* pageSize fixo */
                  },
                }}
              />
            ) : null}

            {selectedObservation &&
            !itemsLoading &&
            allItems.length === 0 &&
            observationStatus === "with_records" &&
            !itemsError ? (
              <div className="ppc-state" role="status">
                {texts.emptyItems}
              </div>
            ) : null}
          </div>
        </div>
      ) : null}
    </section>
  );
}
