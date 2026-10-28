/** Configurable Comex selector (PROC-0076.COMEX.S4/S6/S7).

Two selection origins feeding one analysis: real SB1010 products via
the BFF proxy, or direct NCM codes (8 digits) with no product link.
S7: the NCM branch also exposes the shared catalog — any authorized
user can add a code (registered as candidate, idempotent) and select
NCMs added by others. Only allowlisted NCMs feed the chart; lifecycle
administration lives in a separate manage-only area.
*/

import { useCallback, useEffect, useMemo, useState } from "react";
import { Plus, Save, Trash2, X } from "lucide-react";

import {
  SuppliesActionButton,
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
/** BFF contract cap on the multi-NCM analysis CSV. */
const MAX_ANALYSIS_NCMS = 20;

export type ComexNcmCatalogEntry = {
  ncm_code: string;
  description: string;
};

type SelectorOrigin = "products" | "ncm";

export type MarketComexSelectorProps = {
  /** Selected SB1010 product codes — persisted in the URL. */
  selectedProducts: string[];
  onProductsChange: (codes: string[]) => void;
  /** NCMs entered directly (no product link) — persisted in the URL. */
  directNcms: string[];
  onDirectNcmsChange: (codes: string[]) => void;
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

/** Functional catalog states (S7) — no internal workflow jargon on
 * the main surface. */
type NcmDisplayStatus =
  | "available"
  | "registered"
  | "review"
  | "inactive"
  | "not_cataloged"
  | "missing"
  | "malformed";

function ncmStatusLabel(status: NcmDisplayStatus): string {
  switch (status) {
    case "available":
      return C.ncmStatusAvailable;
    case "registered":
      return C.ncmStatusRegistered;
    case "review":
      return C.ncmStatusReview;
    case "inactive":
      return C.ncmStatusInactive;
    case "missing":
      return C.ncmStatusMissing;
    case "malformed":
      return C.ncmStatusMalformed;
    default:
      return C.ncmStatusNotCataloged;
  }
}

function ncmBadgeKind(status: NcmDisplayStatus): string {
  if (status === "available") return "ok";
  if (status === "inactive" || status === "malformed") return "danger";
  if (status === "review" || status === "missing") return "warning";
  return "neutral";
}

export function MarketComexSelector({
  selectedProducts,
  onProductsChange,
  directNcms,
  onDirectNcmsChange,
  approvedNcms,
  analysisNcms,
  onAnalysisNcmsChange,
  canManage,
  buildViewPayload,
  onApplyView,
  onCatalogDirty,
}: MarketComexSelectorProps) {
  const C2 = C;
  const [origin, setOrigin] = useState<SelectorOrigin>("products");
  const [directInput, setDirectInput] = useState("");
  const [catalogQuery, setCatalogQuery] = useState("");
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
      const item = details[code];
      if (item?.ncm_status === "present" && item.ncm_code) {
        set.add(item.ncm_code);
      }
    }
    return [...set];
  }, [selectedProducts, details]);

  /** Functional state of an NCM for the shared catalog (S7):
   * allowlist-active → available; candidate → registered;
   * pending/approved-but-not-yet-active → review;
   * rejected/inactive → inactive; unknown → not cataloged. */
  const displayStatus = useCallback(
    (ncm: string): NcmDisplayStatus => {
      if (approvedSet.has(ncm)) return "available";
      const status = governanceByNcm.get(ncm)?.status;
      if (status === "candidate") return "registered";
      if (status === "pending_fiscal_review" || status === "approved")
        return "review";
      if (status === "rejected" || status === "inactive")
        return "inactive";
      return "not_cataloged";
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

  /** Direct NCM entry (S7 one-action flow): normalize
   * spacing/punctuation, require exactly 8 digits per token, dedupe
   * against every selection origin and cap the union at the BFF
   * multi-NCM contract limit. Codes not yet in the shared catalog are
   * registered as candidates — format validation never implies fiscal
   * validity. */
  const addDirectNcms = useCallback(async () => {
    setNotice(null);
    const tokens = directInput
      .split(/[\s,;]+/)
      .map((token) => token.trim())
      .filter(Boolean);
    if (!tokens.length) return;
    const normalized: string[] = [];
    const invalid: string[] = [];
    for (const token of tokens) {
      const digits = token.replace(/\D/g, "");
      if (/^[0-9]{8}$/.test(digits)) normalized.push(digits);
      else invalid.push(token);
    }
    const existing = new Set([
      ...productNcms,
      ...directNcms,
      ...analysisNcms,
    ]);
    const fresh = [...new Set(normalized)].filter(
      (code) => !existing.has(code),
    );
    const room = Math.max(0, MAX_ANALYSIS_NCMS - existing.size);
    const accepted = fresh.slice(0, room);

    const toRegister = accepted.filter(
      (code) => !governanceByNcm.has(code),
    );
    if (toRegister.length) {
      setBusy(true);
      const failed: string[] = [];
      try {
        for (const code of toRegister) {
          try {
            await createComexNcmRequest({
              ncm_code: code,
              initial_status: "candidate",
            });
          } catch {
            failed.push(code);
          }
        }
        await reloadGovernance();
      } finally {
        setBusy(false);
      }
      if (failed.length) {
        setNotice({ kind: "error", text: C2.actionError });
        return;
      }
    }

    if (accepted.length) {
      onDirectNcmsChange([...directNcms, ...accepted]);
      // Allowlisted codes feed the analysis immediately — same rule
      // as the product origin.
      const promotable = accepted.filter(
        (code) => approvedSet.has(code) && !analysisNcms.includes(code),
      );
      if (promotable.length) {
        onAnalysisNcmsChange([...analysisNcms, ...promotable]);
      }
      setDirectInput("");
    }
    if (invalid.length) {
      setNotice({ kind: "error", text: C2.directNcmInvalid(invalid) });
    } else if (fresh.length > accepted.length) {
      setNotice({ kind: "error", text: C2.directNcmLimit });
    } else if (!accepted.length && normalized.length) {
      setNotice({ kind: "error", text: C2.directNcmDuplicated });
    } else if (toRegister.length) {
      setNotice({ kind: "success", text: C2.catalogAdded });
    }
  }, [
    directInput,
    productNcms,
    directNcms,
    analysisNcms,
    approvedSet,
    governanceByNcm,
    reloadGovernance,
    onDirectNcmsChange,
    onAnalysisNcmsChange,
    C2,
  ]);

  /** Removing a direct NCM also drops its analysis contribution when
   * no selected product still maps to the same code. */

  /** Single-action catalog add (S7): registers the NCM as a shared
   * catalog candidate — never an implicit fiscal approval. The BFF
   * makes the write idempotent, so re-adding an existing code just
   * returns the shared record. */
  const addToCatalog = useCallback(
    async (ncm: string): Promise<boolean> => {
      setBusy(true);
      setNotice(null);
      try {
        const linkedProducts = selectedProducts.filter(
          (code) => details[code]?.ncm_code === ncm,
        );
        const record = await createComexNcmRequest({
          ncm_code: ncm,
          description: details[linkedProducts[0]]
            ? `Produto ${linkedProducts[0]}`
            : undefined,
          product_codes: linkedProducts,
          initial_status: "candidate",
        });
        setNotice({
          kind: "success",
          text: record?.already_registered
            ? C2.alreadyInCatalog
            : C2.catalogAdded,
        });
        await reloadGovernance();
        return true;
      } catch {
        setNotice({ kind: "error", text: C2.actionError });
        return false;
      } finally {
        setBusy(false);
      }
    },
    [selectedProducts, details, reloadGovernance, C2],
  );

  /** Selects an NCM: tracks it in the user selection (URL-persisted)
   * and promotes it into the analysis when the source is enabled. */
  const selectNcm = useCallback(
    (ncm: string) => {
      if (!directNcms.includes(ncm)) {
        const existing = new Set([
          ...productNcms,
          ...directNcms,
          ...analysisNcms,
        ]);
        if (existing.size >= MAX_ANALYSIS_NCMS) {
          setNotice({ kind: "error", text: C2.directNcmLimit });
          return;
        }
        onDirectNcmsChange([...directNcms, ncm]);
      }
      if (approvedSet.has(ncm) && !analysisNcms.includes(ncm)) {
        onAnalysisNcmsChange([...analysisNcms, ncm]);
      }
    },
    [
      productNcms,
      directNcms,
      analysisNcms,
      approvedSet,
      onDirectNcmsChange,
      onAnalysisNcmsChange,
      C2,
    ],
  );

  const isCatalogSelected = useCallback(
    (ncm: string) =>
      directNcms.includes(ncm) || analysisNcms.includes(ncm),
    [directNcms, analysisNcms],
  );

  const deselectNcm = useCallback(
    (ncm: string) => {
      if (directNcms.includes(ncm)) {
        onDirectNcmsChange(directNcms.filter((code) => code !== ncm));
      }
      const stillUsedByProduct = selectedProducts.some(
        (code) => details[code]?.ncm_code === ncm,
      );
      if (!stillUsedByProduct && analysisNcms.includes(ncm)) {
        onAnalysisNcmsChange(
          analysisNcms.filter((code) => code !== ncm),
        );
      }
    },
    [
      directNcms,
      selectedProducts,
      details,
      analysisNcms,
      onDirectNcmsChange,
      onAnalysisNcmsChange,
    ],
  );

  const clearSelection = useCallback(() => {
    onDirectNcmsChange([]);
    onAnalysisNcmsChange([]);
  }, [onDirectNcmsChange, onAnalysisNcmsChange]);

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

  const directSet = useMemo(() => new Set(directNcms), [directNcms]);

  /** Shared catalog (S7): every governance record is one catalog row.
   * Free-text filter matches the code digits or the description. */
  const catalogEntries = useMemo(() => {
    const needle = catalogQuery.trim().toLowerCase();
    const digits = needle.replace(/\D/g, "");
    if (!needle) return governance;
    return governance.filter(
      (entry) =>
        (digits && entry.ncm_code.includes(digits)) ||
        (entry.description ?? "").toLowerCase().includes(needle),
    );
  }, [governance, catalogQuery]);

  const ncmChips = useMemo(() => {
    // União: NCMs de produtos + entrada direta + análise manual.
    const set = new Set<string>([
      ...productNcms,
      ...directNcms,
      ...analysisNcms,
    ]);
    return [...set];
  }, [productNcms, directNcms, analysisNcms]);

  return (
    <SuppliesSectionCard
      title={C2.selectionTitle}
      subtitle={C2.selectionHint}
    >
      <div className="sp-comex-selector">
        <SuppliesSegmentToggle
          ariaLabel={C2.selectionTitle}
          idPrefix="comex-origin"
          size="sm"
          widthMode="content"
          value={origin}
          options={[
            { value: "products", label: C2.originProducts },
            { value: "ncm", label: C2.originNcm },
          ]}
          onChange={(value) => setOrigin(value as SelectorOrigin)}
        />

        {origin === "products" ? (
          <>
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
                  <li
                    key={item.code}
                    className="sp-comex-selector__result"
                  >
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
          </>
        ) : (
          <>
            <form
              className="sp-comex-selector__search"
              onSubmit={(event) => {
                event.preventDefault();
                void addDirectNcms();
              }}
            >
              <SuppliesTextField
                label={C2.directNcmLabel}
                hint={C2.directNcmHint}
                value={directInput}
                placeholder={C2.directNcmPlaceholder}
                onChange={setDirectInput}
              />
              <SuppliesActionButton type="submit" disabled={busy}>
                <Plus size={14} aria-hidden="true" />
                {C2.directNcmAdd}
              </SuppliesActionButton>
            </form>

            <div className="sp-comex-selector__catalog">
              <SuppliesTextField
                label={C2.catalogTitle}
                value={catalogQuery}
                placeholder={C2.catalogSearchPlaceholder}
                onChange={setCatalogQuery}
              />
              {governance.length === 0 ? (
                <p
                  className="sp-comex-selector__empty"
                  role="status"
                >
                  {C2.catalogEmpty}
                </p>
              ) : catalogEntries.length === 0 ? (
                <p
                  className="sp-comex-selector__empty"
                  role="status"
                >
                  {C2.catalogNoMatch}
                </p>
              ) : (
                <ul
                  className="sp-comex-selector__ncm-list"
                  aria-label={C2.catalogTitle}
                >
                  {catalogEntries.map((entry) => {
                    const status = displayStatus(entry.ncm_code);
                    const selected = isCatalogSelected(
                      entry.ncm_code,
                    );
                    return (
                      <li
                        key={entry.governance_id}
                        className="sp-comex-selector__ncm"
                      >
                        <code>{entry.ncm_code}</code>
                        {entry.description ? (
                          <span className="sp-comex-selector__ncm-desc">
                            {entry.description}
                          </span>
                        ) : null}
                        <span
                          className={`sp-comex-selector__badge sp-comex-selector__badge--${ncmBadgeKind(status)}`}
                        >
                          {ncmStatusLabel(status)}
                        </span>
                        <SuppliesActionButton
                          type="button"
                          variant={selected ? "ghost" : "primary"}
                          disabled={busy}
                          aria-pressed={selected}
                          onClick={() =>
                            selected
                              ? deselectNcm(entry.ncm_code)
                              : selectNcm(entry.ncm_code)
                          }
                        >
                          {selected ? C2.deselectNcm : C2.selectNcm}
                        </SuppliesActionButton>
                        {entry.status === "rejected" ? (
                          <SuppliesActionButton
                            type="button"
                            variant="ghost"
                            disabled={busy}
                            onClick={() =>
                              void decideNcm(
                                entry,
                                "pending_fiscal_review",
                              )
                            }
                          >
                            {C2.resubmit}
                          </SuppliesActionButton>
                        ) : null}
                      </li>
                    );
                  })}
                </ul>
              )}
            </div>
          </>
        )}

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
                      className={`sp-comex-selector__badge sp-comex-selector__badge--${ncmBadgeKind(status)}`}
                    >
                      {ncmStatusLabel(status)}
                    </span>
                    {status === "not_cataloged" ? (
                      <SuppliesActionButton
                        type="button"
                        variant="ghost"
                        disabled={busy}
                        onClick={() => void addToCatalog(ncm)}
                      >
                        {C2.addToCatalog}
                      </SuppliesActionButton>
                    ) : null}
                    {/* Re-review path: rejected → pending is open to any
                        supplies.access user; other lifecycle actions
                        live in the admin section (manage only). */}
                    {gov?.status === "rejected" ? (
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
                    {directSet.has(ncm) ? (
                      <button
                        type="button"
                        className="sp-comex-selector__chip-remove"
                        aria-label={C2.removeNcm(ncm)}
                        onClick={() => deselectNcm(ncm)}
                      >
                        <X size={12} aria-hidden="true" />
                      </button>
                    ) : null}
                  </li>
                );
              })}
            </ul>
          </div>
        ) : (
          <p className="sp-comex-selector__empty" role="status">
            {C2.emptySelection}
          </p>
        )}

        <div className="sp-comex-selector__footer">
          <div className="sp-comex-selector__analysis">
            {analysisNcms.length > 0 ? (
              <p className="sp-comex-selector__note">
                {C2.aggregateNote}
              </p>
            ) : null}
            {ncmChips.length > 0 ? (
              <SuppliesActionButton
                type="button"
                variant="ghost"
                disabled={busy}
                onClick={clearSelection}
              >
                {C2.clearSelection}
              </SuppliesActionButton>
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
        </div>

        {notice ? (
          <SuppliesStateBanner
            variant={notice.kind}
          >
            {notice.text}
          </SuppliesStateBanner>
        ) : null}

        {/* Admin area (S7 D-05): lifecycle decisions stay out of the
            main selection flow and are only rendered when the user has
            effective supplies.manage. The BFF re-checks authorization
            server-side either way. */}
        {canManage ? (
          <details className="sp-comex-selector__admin">
            <summary>{C2.adminTitle}</summary>
            <ul
              className="sp-comex-selector__ncm-list"
              aria-label={C2.adminTitle}
            >
              {governance.map((gov) => (
                <li
                  key={gov.governance_id}
                  className="sp-comex-selector__ncm"
                >
                  <code>{gov.ncm_code}</code>
                  <span
                    className={`sp-comex-selector__badge sp-comex-selector__badge--${ncmBadgeKind(displayStatus(gov.ncm_code))}`}
                  >
                    {ncmStatusLabel(displayStatus(gov.ncm_code))}
                  </span>
                  {gov.status === "candidate" ? (
                    <SuppliesActionButton
                      type="button"
                      variant="ghost"
                      disabled={busy}
                      onClick={() =>
                        void decideNcm(gov, "pending_fiscal_review")
                      }
                    >
                      {C2.submitReview}
                    </SuppliesActionButton>
                  ) : null}
                  {gov.status === "pending_fiscal_review" ? (
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
                  {gov.status === "approved" ? (
                    <SuppliesActionButton
                      type="button"
                      variant="ghost"
                      disabled={busy}
                      onClick={() => void decideNcm(gov, "inactive")}
                    >
                      {C2.deactivate}
                    </SuppliesActionButton>
                  ) : null}
                  {gov.status === "rejected" ||
                  gov.status === "inactive" ? (
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
              ))}
            </ul>
            <p className="sp-comex-selector__note">{C2.manageHint}</p>
          </details>
        ) : null}
      </div>
    </SuppliesSectionCard>
  );
}
