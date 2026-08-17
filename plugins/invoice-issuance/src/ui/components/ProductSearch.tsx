import { useEffect, useRef, useState } from "react";
import * as api from "../../data/api/invoiceIssuanceApi";
import type { ProductHit } from "../../domain/types";
import { TextField } from "../kit";

type Props = {
  onPick: (product: ProductHit) => void;
  disabled?: boolean;
};

export function ProductSearch({ onPick, disabled }: Props) {
  const [query, setQuery] = useState("");
  const [items, setItems] = useState<ProductHit[]>([]);
  const [loading, setLoading] = useState(false);
  const debounceRef = useRef<number | null>(null);

  useEffect(() => {
    if (debounceRef.current) window.clearTimeout(debounceRef.current);
    if (query.trim().length < 2) {
      setItems([]);
      return;
    }
    debounceRef.current = window.setTimeout(() => {
      setLoading(true);
      api
        .searchProducts(query.trim())
        .then(setItems)
        .catch(() => setItems([]))
        .finally(() => setLoading(false));
    }, 350);
    return () => {
      if (debounceRef.current) window.clearTimeout(debounceRef.current);
    };
  }, [query]);

  return (
    <div className="ii-search" data-testid="product-search">
      <TextField
        label="Buscar item (código ou descrição)"
        value={query}
        onChange={setQuery}
        placeholder="Digite ao menos 2 caracteres"
        disabled={disabled}
        fullWidth
      />
      {loading ? <p className="ii-muted">Buscando…</p> : null}
      {items.length > 0 ? (
        <ul className="ii-search__list" data-testid="product-results">
          {items.map((item) => (
            <li key={item.code}>
              <button
                type="button"
                disabled={item.blocked || disabled}
                onClick={() => {
                  onPick(item);
                  setQuery("");
                  setItems([]);
                }}
              >
                <strong>{item.code}</strong> {item.description}
                {item.unit ? ` (${item.unit})` : ""}
              </button>
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}
