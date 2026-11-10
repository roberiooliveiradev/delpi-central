import { useEffect, useRef, useState } from "react";

import {
  EngineeringAnchoredPanel,
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

/** Busca SA2 oficial (Engineering API → api-delpi) — debounce, cancelamento
 * e descarte de resposta obsoleta. Reutilizado pela ficha e pelo modal REF-019. */
export function useSupplierSearch(query: string) {
  const [items, setItems] = useState<PrcSupplierHit[]>([]);
  const [open, setOpen] = useState(false);
  const [state, setState] = useState<LookupState>("idle");
  const seq = useRef(0);
  const aborter = useRef<AbortController | null>(null);

  useEffect(() => {
    const q = query.trim();
    aborter.current?.abort();
    if (q.length < 2) {
      setItems([]);
      setOpen(false);
      setState("idle");
      return undefined;
    }
    const current = ++seq.current;
    /* loading desde a mudança do termo — nunca exibir "nenhum
     * resultado" nem lista obsoleta enquanto a busca remota segue. */
    setState("loading");
    const controller = new AbortController();
    aborter.current = controller;
    const timer = window.setTimeout(async () => {
      try {
        const env = await searchPrcSuppliers(q, controller.signal);
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
    return () => {
      window.clearTimeout(timer);
      controller.abort();
    };
  }, [query]);

  return { items, open, state, setOpen, setItems };
}

type LookupPanelProps = {
  open: boolean;
  anchorRef: React.RefObject<HTMLDivElement | null>;
  panelRef: React.RefObject<HTMLDivElement | null>;
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
  panelRef,
  listId,
  items,
  activeIndex,
  emptyText,
  showEmpty,
  onChoose,
  onDismiss,
}: LookupPanelProps) {
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

/** Lookup SA2 embutido na linha auxiliar da tabela de fornecedores —
 * input puro dentro da área expansível aberta pela lupa da coluna
 * Busca. Seleção oficial SA2 preenche código+loja+razão+fantasia nas
 * colunas próprias (nunca concatena nem exibe identidade na Busca);
 * Escape ou clique externo recolhe a área sem apagar a seleção. */
export function PrcSupplierCellLookup({
  id,
  query,
  disabled,
  onQueryChange,
  onSelect,
  onClose,
}: {
  id: string;
  query: string;
  disabled?: boolean;
  onQueryChange: (v: string) => void;
  onSelect: (hit: PrcSupplierHit) => void;
  onClose: () => void;
}) {
  const { items, open, state, setOpen } = useSupplierSearch(query);
  const [activeIndex, setActiveIndex] = useState(-1);
  const anchorRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);
  const onCloseRef = useRef(onClose);
  useEffect(() => {
    onCloseRef.current = onClose;
  });
  const listId = `${id}-list`;
  const visible = items.slice(0, MAX_VISIBLE);

  useEffect(() => {
    setActiveIndex(visible.length ? 0 : -1);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [items]);

  /* Foco no input quando a área expansível da linha é aberta. */
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  /* Clique fora da área expandida da linha (`.supplier-aux`) e fora do
   * painel de sugestões portado recolhe a busca — nunca apaga a seleção
   * nem cria diff. A lupa (`.search-toggle`) é excluída para o próprio
   * toggle não reabrir a área na mesma interação. */
  useEffect(() => {
    const onDocMouseDown = (e: MouseEvent) => {
      const t = e.target as Node;
      if (
        anchorRef.current?.contains(t) ||
        panelRef.current?.contains(t)
      ) {
        return;
      }
      if (
        t instanceof Element &&
        (t.closest(".engineering-prc__supplier-aux") ||
          t.closest(".engineering-prc__search-toggle"))
      ) {
        return;
      }
      onCloseRef.current();
    };
    document.addEventListener("mousedown", onDocMouseDown);
    return () =>
      document.removeEventListener("mousedown", onDocMouseDown);
  }, []);

  const choose = (hit: PrcSupplierHit) => {
    onSelect(hit);
    setOpen(false);
  };
  const lookupKeys = useLookupKeys({
    open, visible, activeIndex, setActiveIndex, setOpen, onChoose: choose,
  });
  const onKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Escape") {
      e.preventDefault();
      e.stopPropagation();
      onCloseRef.current();
      return;
    }
    lookupKeys(e);
  };

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
      <input
        ref={inputRef}
        id={id}
        type="text"
        className="engineering-prc__lookup-input"
        placeholder={PRC_SUPPLIER_HELP.placeholder}
        value={query}
        disabled={disabled}
        aria-label="Buscar fornecedor por código, razão social ou nome fantasia"
        aria-autocomplete="list"
        aria-controls={listId}
        aria-activedescendant={
          activeIndex >= 0 ? `${listId}-opt-${activeIndex}` : undefined
        }
        /* Autocomplete nativo do Chrome desligado só neste input —
         * evita sugestão visual concorrente com o listbox SA2 oficial. */
        autoComplete="off"
        onChange={(e) => onQueryChange(e.target.value)}
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
          Busca indisponível — tente novamente.
        </span>
      ) : null}
      <SupplierSuggestPanel
        open={open && state !== "loading"}
        anchorRef={anchorRef}
        panelRef={panelRef}
        listId={listId}
        items={visible}
        activeIndex={activeIndex}
        emptyText="Nenhum fornecedor encontrado para o termo pesquisado."
        showEmpty={open && !visible.length && state === "idle"}
        onChoose={choose}
        onDismiss={() => setOpen(false)}
      />
    </div>
  );
}
