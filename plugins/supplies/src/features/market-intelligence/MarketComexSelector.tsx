/** Configurable Comex selector (PROC-0076.COMEX.S4).

Product-driven NCM selection: search real SB1010 products via the BFF
proxy, pick multiple items, see each one's registered fiscal NCM with
its homologation state, request homologation, and persist personal
saved views. Only allowlisted NCMs feed the analysis — pending states
stay visible instead of masquerading as data.
*/

import { useCallback, useEffect, useMemo, useState } from "react";
import { Plus, Save, Trash2, X } from "lucide-react";

import {
  SuppliesActionButton,
  SuppliesMultiSelectField,
  SuppliesSectionCard,
  SuppliesSegmentToggle,
  SuppliesSelectField,
  SuppliesStateBanner,
  SuppliesTextField,
} from "../../app/suppliesUi";
import { MARKET_INTELLIGENCE_CONTENT } from "./content";
import {
  createComexNcmRequest,
  createComexView,
  deleteComexView,
  listComexNcmGovernance,
  listComexViews,
  searchComexProducts,
  transitionComexNcm,
  updateComexView,
  type ComexNcmGovernance,
  type ComexNcmStatus,
  type ComexProductItem,
  type ComexProductType,
  type ComexSavedView,
  type ComexViewPayload,
} from "./comexApi";

const C = MARKET_INTELLIGENCE_CONTENT.comex;

const TYPE_OPTIONS: { value: string; label: string }[] = [
  { value: "", label: C.productTypeAll },
  { value: "MP", label: C.productTypeMp },
  { value: "PI", label: C.productTypePi },
  { value: "PA", label: C.productTypePa },
];

const RESULTS_PAGE_SIZE = 12;

export type ComexNcmCatalogEntry = {
  ncm_code: string;
  description: string;
};

export type MarketComexSelectorProps = {
  /** Selected SB1010 product codes — persisted in the URL. */
  selectedProducts: string[];
  onProductsChange: (codes: string[]) => void;
  /** Allowlisted (selectable) NCMs from the market-data catalog. */
  approvedNcms: ComexNcmCatalogEntry[];
  /** NCMs feeding the analysis — CSV union, deduplicated. */
  analysisNcms: string[];
  onAnalysisNcmsChange: (codes: string[]) => void;
  /** Current user can decide homologation (supplies.manage). */
  canManage: boolean;
  /** Build the payload persisted when saving a view. */
  buildViewPayload: () => Omit<ComexViewPayload, "name">;
  /** Apply a saved view's full filter set on the page. */
  onApplyView: (view: ComexSavedView) => void;
  /** Governance transitions can flip the allowlist — the page refetches
   * its catalog so a newly approved NCM becomes selectable. */
  onCatalogDirty?: () => void;
};

type NcmDisplayStatus =
  | ComexNcmStatus
  | "not_requested"
  | "missing"
  | "malformed";

function ncmStatusLabel(status: NcmDisplayStatus): string {
  switch (status) {
    case "approved":
      return C.ncmStatusApproved;
    case "pending_fiscal_review":
      return C.ncmStatusPending;
    case "candidate":
      return C.ncmStatusCandidate;
    case "rejected":
      return C.ncmStatusRejected;
    case "inactive":
      return C.ncmStatusInactive;
    case "missing":
      return C.ncmStatusMissing;
    case "malformed":
      return C.ncmStatusMalformed;
    default:
      return C.ncmStatusNotRequested;
  }
}

export function MarketComexSelector({
  selectedProducts,
  onProductsChange,
  approvedNcms,
  analysisNcms,
  onAnalysisNcmsChange,
  canManage,
  buildViewPayload,
  onApplyView,
  onCatalogDirty,
}: MarketComexSelectorProps) {
  const C2 = C;
  const [productType, setProductType] = useState<ComexProductType | "">(
    "",
  );
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<ComexProductItem[]>([]);
  const [searching, setSearching] = useState(false);
  const [searched, setSearched] = useState(false);
  const [notice, setNotice] = useState<
    { kind: "error" | "success"; text: string } | null
  >(null);
  const [details, setDetails] = useState<
    Record<string, ComexProductItem>
  >({});
  const [governance, setGovernance] = useState<ComexNcmGovernance[]>([]);
  const [views, setViews] = useState<ComexSavedView[]>([]);
  const [appliedView, setAppliedView] = useState<string>("");
  const [viewName, setViewName] = useState("");
  const [busy, setBusy] = useState(false);

  const approvedSet = useMemo(
    () => new Set(approvedNcms.map((n) => n.ncm_code)),
    [approvedNcms],
  );
  const governanceByNcm = useMemo(() => {
    const map = new Map<string, ComexNcmGovernance>();
    for (const entry of governance) map.set(entry.ncm_code, entry);
    return map;
  }, [governance]);

  const reloadGovernance = useCallback(async (signal?: AbortSignal) => {
    try {
      const payload = await listComexNcmGovernance(undefined, signal);
      setGovernance(payload.items ?? []);
    } catch {
      if (!signal?.aborted) setGovernance([]);
    }
  }, []);

  const reloadViews = useCallback(async (signal?: AbortSignal) => {
    try {
      const payload = await listComexViews(signal);
      setViews(payload.items ?? []);
    } catch {
      if (!signal?.aborted) setViews([]);
    }
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    void reloadGovernance(controller.signal);
    void reloadViews(controller.signal);
    return () => controller.abort();
  }, [reloadGovernance, reloadViews]);

  // Hydrate product details for URL-restored codes — one lookup per
  // unknown code, cached in ``details``.
  useEffect(() => {
    const missing = selectedProducts.filter(
      (code) => !(code in details),
    );
    if (!missing.length) return;
    const controller = new AbortController();
    (async () => {
      for (const code of missing) {
        try {
          const payload = await searchComexProducts(
            { code, page: 1, page_size: 5 },
            controller.signal,
          );
          const item = (payload.items ?? []).find(
            (entry) => entry.code === code,
          );
          if (item) {
            setDetails((prev) =>
              prev[code] ? prev : { ...prev, [code]: item },
            );
          }
        } catch {
          if (controller.signal.aborted) return;
        }
      }
    })();
    return () => controller.abort();
  }, [selectedProducts, details]);

  const runSearch = useCallback(async () => {
    setSearching(true);
    setSearched(true);
    setNotice(null);
    try {
      const payload = await searchComexProducts({
        description: query || undefined,
        product_type: productType || undefined,
        page: 1,
        page_size: RESULTS_PAGE_SIZE,
      });
      setResults(payload.items ?? []);
    } catch {
      setResults([]);
      setNotice({ kind: "error", text: C2.actionError });
    } finally {
      setSearching(false);
    }
  }, [query, productType, C2.actionError]);

  // NCMs derivadas da seleção — dedup por código.
  const productNcms = useMemo(() => {
    const set = new Set<string>();
    for (const code of selectedProducts) {
      const ncm = details[code]?.ncm_code;
      if (ncm) set.add(ncm);
    }
    return [...set];
  }, [selectedProducts, details]);

  const displayStatus = useCallback(
    (ncm: string): NcmDisplayStatus => {
      if (approvedSet.has(ncm)) return "approved";
      const gov = governanceByNcm.get(ncm);
      return gov?.status ?? "not_requested";
    },
    [approvedSet, governanceByNcm],
  );

  const addProduct = useCallback(
    (item: ComexProductItem) => {
      if (selectedProducts.includes(item.code)) return;
      const next = [...selectedProducts, item.code];
      setDetails((prev) => ({ ...prev, [item.code]: item }));
      onProductsChange(next);
      // NCM homologada entra direto na análise — dedup pela união.
      if (item.ncm_code && approvedSet.has(item.ncm_code)) {
        if (!analysisNcms.includes(item.ncm_code)) {
          onAnalysisNcmsChange([...analysisNcms, item.ncm_code]);
        }
      }
    },
    [
      selectedProducts,
      analysisNcms,
      approvedSet,
      onProductsChange,
      onAnalysisNcmsChange,
    ],
  );

  const removeProduct = useCallback(
    (code: string) => {
      onProductsChange(selectedProducts.filter((c) => c !== code));
    },
    [selectedProducts, onProductsChange],
  );

  const requestNcm = useCallback(
    async (ncm: string) => {
      setBusy(true);
      setNotice(null);
      try {
        const linkedProducts = selectedProducts.filter(
          (code) => details[code]?.ncm_code === ncm,
        );
        await createComexNcmRequest({
          ncm_code: ncm,
          description: details[linkedProducts[0]]
            ? `Produto ${linkedProducts[0]}`
            : undefined,
          product_codes: linkedProducts,
          initial_status: "pending_fiscal_review",
        });
        setNotice({ kind: "success", text: C2.requestSuccess });
        await reloadGovernance();
      } catch {
        setNotice({ kind: "error", text: C2.actionError });
      } finally {
        setBusy(false);
      }
    },
    [selectedProducts, details, reloadGovernance, C2],
  );

  const decideNcm = useCallback(
    async (gov: ComexNcmGovernance, to: ComexNcmStatus) => {
      setBusy(true);
      setNotice(null);
      try {
        await transitionComexNcm(gov.governance_id, {
          to_status: to,
          expected_revision: gov.revision,
        });
        await reloadGovernance();
        onCatalogDirty?.();
      } catch {
        setNotice({ kind: "error", text: C2.actionError });
      } finally {
        setBusy(false);
      }
    },
    [reloadGovernance, onCatalogDirty, C2],
  );

  const saveView = useCallback(async () => {
    const name = viewName.trim();
    if (!name) return;
    setBusy(true);
    setNotice(null);
    try {
      const payload = {
        ...buildViewPayload(),
        name,
        selected_product_codes: selectedProducts,
        approved_ncm_references: analysisNcms,
      };
      if (appliedView) {
        await updateComexView(appliedView, payload);
      } else {
        const created = await createComexView(payload);
        setAppliedView(created.view_id);
      }
      setNotice({ kind: "success", text: C2.viewSaved });
      setViewName("");
      await reloadViews();
    } catch {
      setNotice({ kind: "error", text: C2.actionError });
    } finally {
      setBusy(false);
    }
  }, [
    viewName,
    appliedView,
    buildViewPayload,
    selectedProducts,
    analysisNcms,
    reloadViews,
    C2,
  ]);

  const removeView = useCallback(async () => {
    if (!appliedView) return;
    setBusy(true);
    setNotice(null);
    try {
      await deleteComexView(appliedView);
      setAppliedView("");
      setNotice({ kind: "success", text: C2.viewDeleted });
      await reloadViews();
    } catch {
      setNotice({ kind: "error", text: C2.actionError });
    } finally {
      setBusy(false);
    }
  }, [appliedView, reloadViews, C2]);

  const applyView = useCallback(
    (viewId: string) => {
      setAppliedView(viewId);
      const view = views.find((entry) => entry.view_id === viewId);
      if (!view) return;
      onApplyView(view);
    },
    [views, onApplyView],
  );

  const ncmChips = useMemo(() => {
    // União: NCMs da seleção de produtos + análise manual.
    const set = new Set<string>([...productNcms, ...analysisNcms]);
    return [...set];
  }, [productNcms, analysisNcms]);

  return (
    <SuppliesSectionCard
      title={C2.selectionTitle}
      subtitle={C2.selectionHint}
    >
      <div className="sp-comex-selector">
        <div className="sp-comex-selector__search">
          <SuppliesSegmentToggle
            ariaLabel={C2.productTypeAll}
            idPrefix="comex-product-type"
            size="sm"
            widthMode="content"
            value={productType}
            options={TYPE_OPTIONS}
            onChange={(value) =>
              setProductType(value as ComexProductType | "")
            }
          />
          <SuppliesTextField
            label={C2.searchLabel}
            value={query}
            placeholder={C2.searchPlaceholder}
            onChange={setQuery}
          />
          <SuppliesActionButton
            type="button"
            disabled={searching}
            onClick={() => void runSearch()}
          >
            {searching ? C2.resultsLoading : C2.searchButton}
          </SuppliesActionButton>
        </div>

        {searched && !searching && results.length === 0 ? (
          <p className="sp-comex-selector__empty" role="status">
            {C2.resultsEmptyMessage}
          </p>
        ) : null}

        {results.length > 0 ? (
          <ul
            className="sp-comex-selector__results"
            aria-label={C2.searchLabel}
          >
            {results.map((item) => (
              <li key={item.code} className="sp-comex-selector__result">
                <div className="sp-comex-selector__result-main">
                  <strong>{item.code}</strong>
                  <span>{item.description}</span>
                  <span className="sp-comex-selector__result-meta">
                    {item.type} · {item.unit}
                    {item.ncm_code
                      ? ` · NCM ${item.ncm_code}`
                      : ` · ${C2.ncmStatusMissing}`}
                  </span>
                </div>
                {item.ncm_status === "malformed" ? (
                  <span className="sp-comex-selector__badge sp-comex-selector__badge--warning">
                    {C2.ncmStatusMalformed}
                  </span>
                ) : null}
                <SuppliesActionButton
                  type="button"
                  variant="ghost"
                  disabled={selectedProducts.includes(item.code)}
                  onClick={() => addProduct(item)}
                  aria-label={`${C2.addProduct} ${item.code}`}
                >
                  <Plus size={14} aria-hidden="true" />
                  {C2.addProduct}
                </SuppliesActionButton>
              </li>
            ))}
          </ul>
        ) : null}

        {selectedProducts.length > 0 ? (
          <div className="sp-comex-selector__selection">
            <span className="sp-comex-selector__selection-label">
              {C2.selectedProductsLabel}
            </span>
            <ul className="sp-comex-selector__chips">
              {selectedProducts.map((code) => (
                <li key={code} className="sp-comex-selector__chip">
                  <span>
                    {code}
                    {details[code]?.description
                      ? ` — ${details[code].description}`
                      : ""}
                  </span>
                  <button
                    type="button"
                    className="sp-comex-selector__chip-remove"
                    aria-label={C2.removeProduct(code)}
                    onClick={() => removeProduct(code)}
                  >
                    <X size={12} aria-hidden="true" />
                  </button>
                </li>
              ))}
            </ul>
          </div>
        ) : null}

        {ncmChips.length > 0 ? (
          <div className="sp-comex-selector__ncms">
            <span className="sp-comex-selector__selection-label">
              {C2.ncmColumnTitle}
            </span>
            <ul className="sp-comex-selector__ncm-list">
              {ncmChips.map((ncm) => {
                const status = displayStatus(ncm);
                const gov = governanceByNcm.get(ncm);
                return (
                  <li key={ncm} className="sp-comex-selector__ncm">
                    <code>{ncm}</code>
                    <span
                      className={`sp-comex-selector__badge sp-comex-selector__badge--${status === "approved" ? "ok" : status === "rejected" || status === "malformed" ? "danger" : "warning"}`}
                    >
                      {ncmStatusLabel(status)}
                    </span>
                    {status === "not_requested" ? (
                      <SuppliesActionButton
                        type="button"
                        variant="ghost"
                        disabled={busy}
                        onClick={() => void requestNcm(ncm)}
                      >
                        {C2.requestApproval}
                      </SuppliesActionButton>
                    ) : null}
                    {canManage &&
                    status === "pending_fiscal_review" &&
                    gov ? (
                      <>
                        <SuppliesActionButton
                          type="button"
                          variant="ghost"
                          disabled={busy}
                          onClick={() =>
                            void decideNcm(gov, "approved")
                          }
                        >
                          {C2.approve}
                        </SuppliesActionButton>
                        <SuppliesActionButton
                          type="button"
                          variant="ghost"
                          disabled={busy}
                          onClick={() =>
                            void decideNcm(gov, "rejected")
                          }
                        >
                          {C2.reject}
                        </SuppliesActionButton>
                      </>
                    ) : null}
                    {canManage && status === "approved" && gov ? (
                      <SuppliesActionButton
                        type="button"
                        variant="ghost"
                        disabled={busy}
                        onClick={() => void decideNcm(gov, "inactive")}
                      >
                        {C2.deactivate}
                      </SuppliesActionButton>
                    ) : null}
                    {/* Re-review path: rejected → pending is open to any
                        supplies.access user; inactive → pending stays a
                        manage decision (lifecycle contract). */}
                    {((status === "rejected" && gov) ||
                      (status === "inactive" && gov && canManage)) && gov ? (
                      <SuppliesActionButton
                        type="button"
                        variant="ghost"
                        disabled={busy}
                        onClick={() =>
                          void decideNcm(gov, "pending_fiscal_review")
                        }
                      >
                        {C2.resubmit}
                      </SuppliesActionButton>
                    ) : null}
                  </li>
                );
              })}
            </ul>
          </div>
        ) : null}

        <div className="sp-comex-selector__analysis">
          <SuppliesMultiSelectField
            label={C2.approvedNcmsLabel}
            hint={C2.approvedNcmsHint}
            options={approvedNcms.map((entry) => ({
              value: entry.ncm_code,
              label: `${entry.ncm_code} — ${entry.description}`,
            }))}
            selectedValues={analysisNcms}
            onChange={(values) => onAnalysisNcmsChange(values)}
            emptyLabel={C2.noApprovedNcm}
            searchable
          />
          {analysisNcms.length > 0 ? (
            <p className="sp-comex-selector__note">{C2.aggregateNote}</p>
          ) : null}
        </div>

        <div className="sp-comex-selector__views">
          <SuppliesSelectField
            label={C2.viewsLabel}
            value={appliedView}
            options={[
              { value: "", label: C2.viewsPlaceholder },
              ...views.map((view) => ({
                value: view.view_id,
                label: view.name,
              })),
            ]}
            onChange={applyView}
          />
          <SuppliesTextField
            label={C2.viewNamePlaceholder}
            value={viewName}
            placeholder={C2.viewNamePlaceholder}
            onChange={setViewName}
          />
          <SuppliesActionButton
            type="button"
            variant="ghost"
            disabled={busy || !viewName.trim()}
            onClick={() => void saveView()}
          >
            <Save size={14} aria-hidden="true" />
            {appliedView ? C2.updateView : C2.saveView}
          </SuppliesActionButton>
          {appliedView ? (
            <SuppliesActionButton
              type="button"
              variant="ghost"
              disabled={busy}
              onClick={() => void removeView()}
            >
              <Trash2 size={14} aria-hidden="true" />
              {C2.deleteView}
            </SuppliesActionButton>
          ) : null}
        </div>

        {notice ? (
          <SuppliesStateBanner
            variant={notice.kind}
          >
            {notice.text}
          </SuppliesStateBanner>
        ) : null}
        {canManage ? (
          <p className="sp-comex-selector__note">{C2.manageHint}</p>
        ) : null}
      </div>
    </SuppliesSectionCard>
  );
}
