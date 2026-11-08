import { useEffect, useRef, useState } from "react";

import {
  EngineeringAnchoredPanel,
  EngineeringTextField,
  ENGINEERING_PORTAL_SCOPE,
} from "../../../ui/engineeringUi";
import { PRC_SUPPLIER_HELP } from "../prcCopy";
import {
  searchPrcSuppliers,
  type PrcSupplierHit,
} from "../api/productRegistrationApi";
import { supplierHitMain, supplierHitSecondary } from "../prcSuppliers";

const MAX_VISIBLE = 8;

type LookupState = "idle" | "loading" | "error";

function useSupplierSearch(query: string) {
  const [items, setItems] = useState<PrcSupplierHit[]>([]);
  const [open, setOpen] = useState(false);
  const [state, setState] = useState<LookupState>("idle");
  const seq = useRef(0);

  useEffect(() => {
    const q = query.trim();
    if (q.length < 2) {
      setItems([]);
      setOpen(false);
      setState("idle");
      return undefined;
    }
    const current = ++seq.current;
    const timer = window.setTimeout(async () => {
      setState("loading");
      try {
        const env = await searchPrcSuppliers(q);
        if (current !== seq.current) return;
        setItems(env.data.items || []);
        setOpen(true);
        setState("idle");
      } catch {
        if (current !== seq.current) return;
        setState("error");
        setOpen(false);
      }
    }, 300);
    return () => window.clearTimeout(timer);
  }, [query]);

  return { items, open, state, setOpen, setItems };
}

type LookupPanelProps = {
  open: boolean;
  anchorRef: React.RefObject<HTMLDivElement | null>;
  listId: string;
  items: PrcSupplierHit[];
  activeIndex: number;
  emptyText: string;
  showEmpty: boolean;
  onChoose: (hit: PrcSupplierHit) => void;
  onDismiss: () => void;
};

/** Painel de sugestões SA2 renderizado via portal oficial — escapa do
 * clipping de `overflow` do wrapper da tabela (o culpado do dropdown
 * cortado) e mantém âncora/flip/clamp de viewport. */
function SupplierSuggestPanel({
  open,
  anchorRef,
  listId,
  items,
  activeIndex,
  emptyText,
  showEmpty,
  onChoose,
  onDismiss,
}: LookupPanelProps) {
  const panelRef = useRef<HTMLDivElement>(null);
  return (
    <EngineeringAnchoredPanel
      open={open}
      anchorRef={anchorRef}
      panelRef={panelRef}
      variant="bare"
      matchAnchorWidth
      allowFlip
      portalScopeClassName={ENGINEERING_PORTAL_SCOPE}
      exclusive={false}
      onDismiss={onDismiss}
      role="presentation"
      className="engineering-prc__lookup-panel"
    >
      <ul
        id={listId}
        className="engineering-prc__lookup-list"
        role="listbox"
        aria-label="Fornecedores sugeridos"
      >
        {items.map((hit, i) => (
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
              onClick={() => onChoose(hit)}
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
        {showEmpty ? (
          <li className="engineering-prc__lookup-empty">{emptyText}</li>
        ) : null}
      </ul>
    </EngineeringAnchoredPanel>
  );
}

function useLookupKeys({
  open,
  visible,
  activeIndex,
  setActiveIndex,
  setOpen,
  onChoose,
}: {
  open: boolean;
  visible: PrcSupplierHit[];
  activeIndex: number;
  setActiveIndex: (v: number | ((i: number) => number)) => void;
  setOpen: (v: boolean) => void;
  onChoose: (hit: PrcSupplierHit) => void;
}) {
  return (e: React.KeyboardEvent) => {
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
      onChoose(visible[activeIndex]);
    }
  };
}

/** Combobox SA2 — busca código/nome via BFF Engenharia → api-delpi →
 * TOTVS. Seleção define código+loja+nome oficiais; PN/catálogo ficam
 * editáveis e não são inferidos. */
export function PrcSupplierLookup({
  id,
  value,
  disabled,
  onSelect,
}: {
  id: string;
  value: string;
  disabled?: boolean;
  onSelect: (hit: PrcSupplierHit) => void;
}) {
  const [query, setQuery] = useState("");
  const { items, open, state, setOpen } = useSupplierSearch(query);
  const [activeIndex, setActiveIndex] = useState(-1);
  const anchorRef = useRef<HTMLDivElement>(null);
  const listId = `${id}-list`;
  const visible = items.slice(0, MAX_VISIBLE);

  useEffect(() => {
    setActiveIndex(visible.length ? 0 : -1);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [items]);

  const choose = (hit: PrcSupplierHit) => {
    onSelect(hit);
    setOpen(false);
    setQuery("");
  };
  const onKeyDown = useLookupKeys({
    open, visible, activeIndex, setActiveIndex, setOpen, onChoose: choose,
  });

  return (
    <div
      ref={anchorRef}
      className="engineering-prc__lookup"
      role="combobox"
      aria-expanded={open}
      aria-haspopup="listbox"
      aria-owns={listId}
      onBlur={(e) => {
        if (!e.currentTarget.contains(e.relatedTarget)) setOpen(false);
      }}
    >
      <EngineeringTextField
        id={id}
        label="Fornecedor"
        hint={PRC_SUPPLIER_HELP.search}
        value={value || query}
        onChange={(v) => {
          setQuery(v);
          onSelect({ supplier_code: "", supplier_store: "", supplier_name: v });
        }}
        disabled={disabled}
        placeholder={PRC_SUPPLIER_HELP.placeholder}
      />
      {state === "loading" ? (
        <span className="engineering-prc__muted">Buscando…</span>
      ) : null}
      {state === "error" ? (
        <span className="engineering-prc__field-error" role="alert">
          Busca indisponível — tente novamente.
        </span>
      ) : null}
      <span onKeyDown={onKeyDown} className="engineering-prc__lookup-keys">
        <SupplierSuggestPanel
          open={open}
          anchorRef={anchorRef}
          listId={listId}
          items={visible}
          activeIndex={activeIndex}
          emptyText="Nenhum fornecedor encontrado."
          showEmpty={open && !visible.length && state === "idle"}
          onChoose={choose}
          onDismiss={() => setOpen(false)}
        />
      </span>
    </div>
  );
}

/** Variante compacta do lookup SA2 para célula de tabela editável —
 * input puro (sem label), seleção oficial obrigatória, dropdown em
 * portal para nunca ser cortado pelo overflow da tabela. */
export function PrcSupplierCellLookup({
  id,
  displayValue,
  query,
  disabled,
  onQueryChange,
  onSelect,
  onClear,
}: {
  id: string;
  displayValue: string;
  query: string;
  disabled?: boolean;
  onQueryChange: (v: string) => void;
  onSelect: (hit: PrcSupplierHit) => void;
  onClear: () => void;
}) {
  const { items, open, state, setOpen } = useSupplierSearch(query);
  const [activeIndex, setActiveIndex] = useState(-1);
  const anchorRef = useRef<HTMLDivElement>(null);
  const selected = Boolean(displayValue);
  const listId = `${id}-list`;
  const visible = items.slice(0, MAX_VISIBLE);

  useEffect(() => {
    setActiveIndex(visible.length ? 0 : -1);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [items]);

  const choose = (hit: PrcSupplierHit) => {
    onSelect(hit);
    setOpen(false);
  };
  const onKeyDown = useLookupKeys({
    open, visible, activeIndex, setActiveIndex, setOpen, onChoose: choose,
  });

  return (
    <div
      ref={anchorRef}
      className="engineering-prc__lookup"
      role="combobox"
      aria-expanded={open}
      aria-haspopup="listbox"
      aria-owns={listId}
      onBlur={(e) => {
        if (!e.currentTarget.contains(e.relatedTarget)) setOpen(false);
      }}
    >
      {selected ? (
        <div className="engineering-prc__lookup-selected">
          <span>{displayValue}</span>
          <button
            type="button"
            className="engineering-prc__lookup-clear"
            disabled={disabled}
            onClick={onClear}
            aria-label="Alterar fornecedor"
          >
            Alterar
          </button>
        </div>
      ) : (
        <input
          id={id}
          type="text"
          className="engineering-prc__lookup-input"
          placeholder={PRC_SUPPLIER_HELP.placeholder}
          value={query}
          disabled={disabled}
          aria-label="Buscar fornecedor por código ou nome"
          aria-autocomplete="list"
          aria-controls={listId}
          aria-activedescendant={
            activeIndex >= 0 ? `${listId}-opt-${activeIndex}` : undefined
          }
          onChange={(e) => onQueryChange(e.target.value)}
          onKeyDown={onKeyDown}
          onFocus={() => {
            if (visible.length) setOpen(true);
          }}
        />
      )}
      {state === "loading" ? (
        <span className="engineering-prc__muted">Buscando…</span>
      ) : null}
      {state === "error" ? (
        <span className="engineering-prc__field-error" role="alert">
          Busca indisponível.
        </span>
      ) : null}
      <SupplierSuggestPanel
        open={open && !selected}
        anchorRef={anchorRef}
        listId={listId}
        items={visible}
        activeIndex={activeIndex}
        emptyText="Nenhum fornecedor encontrado."
        showEmpty={open && !visible.length && state === "idle"}
        onChoose={choose}
        onDismiss={() => setOpen(false)}
      />
    </div>
  );
}
