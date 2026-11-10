/** Pesquisa oficial de fornecedor SA2 para perguntas SUPPLIER_LINK
 * (PRC-REF-021-REF-01). Identidade atômica código+loja; sem digitação
 * livre. Reutiliza o mesmo contrato/hook da ficha técnica. */

import { useEffect, useId, useRef, useState } from "react";

import {
  EngineeringAnchoredPanel,
  ENGINEERING_PORTAL_SCOPE,
} from "../../../ui/engineeringUi";
import type { PrcSupplierHit } from "../api/productRegistrationApi";
import { PRC_INFO_COPY } from "../prcCopy";
import { supplierHitMain, supplierHitSecondary } from "../prcSuppliers";
import { useSupplierSearch } from "./PrcSupplierLookup";

const MAX_VISIBLE = 12;

export type OfficialSupplierSelection = {
  supplierCode: string;
  store: string;
  supplierName?: string;
  supplierShortName?: string;
};

export function PrcOfficialSupplierSearchField({
  id,
  selected,
  disabled,
  onSelect,
  onClear,
}: {
  id?: string;
  selected: OfficialSupplierSelection | null;
  disabled?: boolean;
  onSelect: (value: OfficialSupplierSelection) => void;
  onClear?: () => void;
}) {
  const autoId = useId();
  const fieldId = id || autoId;
  const listId = `${fieldId}-list`;
  const [query, setQuery] = useState("");
  const { items, open, state, setOpen } = useSupplierSearch(query);
  const [activeIndex, setActiveIndex] = useState(-1);
  const anchorRef = useRef<HTMLDivElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);
  const visible = items.slice(0, MAX_VISIBLE);

  useEffect(() => {
    setActiveIndex(visible.length ? 0 : -1);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [items]);

  const choose = (hit: PrcSupplierHit) => {
    const supplierCode = String(hit.supplier_code ?? "").trim();
    const store = String(hit.supplier_store ?? "").trim();
    if (!supplierCode || !store) return;
    onSelect({
      supplierCode,
      store,
      supplierName: hit.supplier_name
        ? String(hit.supplier_name)
        : undefined,
      supplierShortName: hit.supplier_short_name
        ? String(hit.supplier_short_name)
        : undefined,
    });
    setQuery("");
    setOpen(false);
  };

  const onKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      if (!open) setOpen(true);
      else setActiveIndex((i) => Math.min(i + 1, visible.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActiveIndex((i) => Math.max(i - 1, 0));
    } else if (
      e.key === "Enter" &&
      open &&
      activeIndex >= 0 &&
      visible[activeIndex]
    ) {
      e.preventDefault();
      choose(visible[activeIndex]);
    } else if (e.key === "Escape") {
      e.preventDefault();
      setOpen(false);
    }
  };

  return (
    <div className="engineering-prc__official-supplier">
      <label
        className="engineering-prc__official-supplier-label"
        htmlFor={fieldId}
      >
        {PRC_INFO_COPY.supplierSearch}
      </label>
      {selected?.supplierCode && selected.store ? (
        <div
          className="engineering-prc__official-supplier-selected"
          aria-live="polite"
        >
          <div>
            <strong>
              {selected.supplierCode} / {selected.store}
            </strong>
            {selected.supplierName || selected.supplierShortName ? (
              <span className="engineering-prc__muted">
                {" "}
                — {selected.supplierName || selected.supplierShortName}
              </span>
            ) : null}
            <div className="engineering-prc__muted">
              Código e loja preenchidos pela pesquisa oficial (somente leitura).
            </div>
          </div>
          {!disabled && onClear ? (
            <button
              type="button"
              className="engineering-prc__official-supplier-clear"
              onClick={() => {
                onClear();
                setQuery("");
              }}
            >
              Trocar
            </button>
          ) : null}
        </div>
      ) : (
        <div
          ref={anchorRef}
          className="engineering-prc__lookup engineering-prc__lookup--modal"
          role="combobox"
          aria-expanded={open}
          aria-haspopup="listbox"
          aria-owns={listId}
        >
          <input
            id={fieldId}
            type="search"
            className="engineering-prc__lookup-input"
            placeholder={PRC_INFO_COPY.supplierSearchPlaceholder}
            value={query}
            disabled={disabled}
            aria-label={PRC_INFO_COPY.supplierSearch}
            aria-autocomplete="list"
            aria-controls={listId}
            aria-activedescendant={
              activeIndex >= 0 ? `${listId}-opt-${activeIndex}` : undefined
            }
            autoComplete="off"
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={onKeyDown}
            onFocus={() => {
              if (visible.length) setOpen(true);
            }}
          />
          {state === "loading" ? (
            <span className="engineering-prc__muted">Buscando…</span>
          ) : null}
          {state === "error" ? (
            <span className="engineering-prc__field-error" role="alert">
              {PRC_INFO_COPY.supplierSearchUnavailable}
            </span>
          ) : null}
          <EngineeringAnchoredPanel
            open={open && state !== "loading"}
            anchorRef={anchorRef}
            panelRef={panelRef}
            variant="bare"
            matchAnchorWidth
            allowFlip
            portalScopeClassName={ENGINEERING_PORTAL_SCOPE}
            exclusive={false}
            onDismiss={() => setOpen(false)}
            role="presentation"
            className="engineering-prc__lookup-panel"
          >
            <ul
              id={listId}
              className="engineering-prc__lookup-list"
              role="listbox"
              aria-label="Fornecedores oficiais"
            >
              {visible.map((hit, i) => (
                <li
                  key={`${hit.supplier_code}.${hit.supplier_store}.${i}`}
                  id={`${listId}-opt-${i}`}
                  role="option"
                  aria-selected={i === activeIndex}
                  className={
                    i === activeIndex
                      ? "engineering-prc__lookup-item engineering-prc__lookup-item--active"
                      : "engineering-prc__lookup-item"
                  }
                >
                  <button
                    type="button"
                    className="engineering-prc__lookup-option"
                    onMouseDown={(e) => e.preventDefault()}
                    onClick={() => choose(hit)}
                  >
                    <span className="engineering-prc__lookup-legal">
                      {supplierHitMain(hit)}
                    </span>
                    <span className="engineering-prc__lookup-meta">
                      {supplierHitSecondary(hit)}
                    </span>
                  </button>
                </li>
              ))}
              {open && !visible.length && state === "idle" ? (
                <li className="engineering-prc__lookup-empty">
                  {PRC_INFO_COPY.supplierSearchEmpty}
                </li>
              ) : null}
            </ul>
          </EngineeringAnchoredPanel>
        </div>
      )}
    </div>
  );
}
