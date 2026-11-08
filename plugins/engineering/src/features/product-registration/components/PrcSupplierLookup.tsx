import { useEffect, useRef, useState } from "react";

import { EngineeringTextField } from "../../../ui/engineeringUi";
import {
  searchPrcSuppliers,
  type PrcSupplierHit,
} from "../api/productRegistrationApi";

function useSupplierSearch(query: string) {
  const [items, setItems] = useState<PrcSupplierHit[]>([]);
  const [open, setOpen] = useState(false);
  const [state, setState] = useState<"idle" | "loading" | "error">("idle");
  const seq = useRef(0);

  useEffect(() => {
    const q = query.trim();
    if (q.length < 2) {
      setItems([]);
      setOpen(false);
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

  return { items, open, state, setOpen };
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
  const [items, setItems] = useState<PrcSupplierHit[]>([]);
  const [open, setOpen] = useState(false);
  const [state, setState] = useState<"idle" | "loading" | "error">("idle");
  const seq = useRef(0);

  useEffect(() => {
    const q = query.trim();
    if (q.length < 2) {
      setItems([]);
      setOpen(false);
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

  return (
    <div className="engineering-prc__lookup" role="combobox" aria-expanded={open}>
      <EngineeringTextField
        id={id}
        label="Fornecedor"
        hint="Busque por código ou nome — código e loja oficiais"
        value={value || query}
        onChange={(v) => {
          setQuery(v);
          onSelect({ supplier_code: "", supplier_store: "", supplier_name: v });
        }}
        disabled={disabled}
        placeholder="Código ou nome do fornecedor"
      />
      {state === "loading" ? (
        <span className="engineering-prc__muted">Buscando…</span>
      ) : null}
      {state === "error" ? (
        <span className="engineering-prc__field-error" role="alert">
          Busca indisponível — tente novamente.
        </span>
      ) : null}
      {open && items.length ? (
        <ul className="engineering-prc__lookup-list" role="listbox">
          {items.slice(0, 8).map((hit, i) => {
            const code = String(hit.supplier_code || "");
            const store = String(hit.supplier_store || "");
            const name = String(hit.supplier_name || "");
            return (
              <li
                key={`${code}.${store}.${i}`}
                role="option"
                aria-selected="false"
                className="engineering-prc__lookup-item"
                onMouseDown={(e) => {
                  e.preventDefault();
                  onSelect(hit);
                  setOpen(false);
                  setQuery("");
                }}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    onSelect(hit);
                    setOpen(false);
                  }
                }}
                tabIndex={0}
              >
                <strong>{code} / {store}</strong> — {name}
              </li>
            );
          })}
        </ul>
      ) : null}
      {open && !items.length && state === "idle" ? (
        <span className="engineering-prc__muted">
          Nenhum fornecedor encontrado.
        </span>
      ) : null}
    </div>
  );
}

/** Variante compacta do lookup SA2 para célula de tabela editável —
 * input puro (sem label), seleção oficial obrigatória. */
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
  const selected = Boolean(displayValue);

  return (
    <div className="engineering-prc__lookup" role="combobox" aria-expanded={open}>
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
          placeholder="Código ou nome"
          value={query}
          disabled={disabled}
          aria-label="Buscar fornecedor por código ou nome"
          onChange={(e) => onQueryChange(e.target.value)}
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
      {open && items.length ? (
        <ul className="engineering-prc__lookup-list" role="listbox">
          {items.slice(0, 8).map((hit, i) => {
            const code = String(hit.supplier_code || "");
            const store = String(hit.supplier_store || "");
            const name = String(hit.supplier_name || "");
            return (
              <li
                key={`${code}.${store}.${i}`}
                role="option"
                aria-selected="false"
                className="engineering-prc__lookup-item"
                onMouseDown={(e) => {
                  e.preventDefault();
                  onSelect(hit);
                  setOpen(false);
                }}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    onSelect(hit);
                    setOpen(false);
                  }
                }}
                tabIndex={0}
              >
                <strong>{code} / {store}</strong> — {name}
              </li>
            );
          })}
        </ul>
      ) : null}
      {open && !items.length && state === "idle" ? (
        <span className="engineering-prc__muted">
          Nenhum fornecedor encontrado.
        </span>
      ) : null}
    </div>
  );
}
