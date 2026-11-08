import { useEffect, useRef, useState } from "react";

import { EngineeringTextField } from "../../../ui/engineeringUi";
import {
  searchPrcSuppliers,
  type PrcSupplierHit,
} from "../api/productRegistrationApi";

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
