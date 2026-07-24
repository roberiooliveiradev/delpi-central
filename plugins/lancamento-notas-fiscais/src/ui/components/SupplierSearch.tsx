import { useEffect, useRef, useState } from "react";
import * as api from "../../data/api/invoicePostingApi";
import type { Supplier } from "../../domain/types";

type Props = {
  selected: Supplier | null;
  onSelect: (supplier: Supplier | null) => void;
  disabled?: boolean;
  error?: string | null;
};

export function SupplierSearch({ selected, onSelect, disabled, error }: Props) {
  const [query, setQuery] = useState("");
  const [items, setItems] = useState<Supplier[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [open, setOpen] = useState(false);
  const debounceRef = useRef<number | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    if (debounceRef.current) window.clearTimeout(debounceRef.current);
    if (query.trim().length < 2) {
      setItems([]);
      setSearchError(null);
      setLoading(false);
      return;
    }
    debounceRef.current = window.setTimeout(() => {
      abortRef.current?.abort();
      const controller = new AbortController();
      abortRef.current = controller;
      setLoading(true);
      setSearchError(null);
      api
        .searchSuppliers(query.trim(), 20, controller.signal)
        .then((rows) => {
          setItems(rows);
          setOpen(true);
        })
        .catch((err: unknown) => {
          if (controller.signal.aborted) return;
          setItems([]);
          setSearchError(err instanceof Error ? err.message : "Falha na pesquisa.");
        })
        .finally(() => {
          if (!controller.signal.aborted) setLoading(false);
        });
    }, 350);
    return () => {
      if (debounceRef.current) window.clearTimeout(debounceRef.current);
    };
  }, [query]);

  return (
    <div className="lnf-field" data-testid="supplier-search">
      <label htmlFor="lnf-supplier-query">Fornecedor</label>
      {selected ? (
        <div className="lnf-supplier-selected">
          <div>
            <strong>
              {selected.supplier_code}/{selected.supplier_store}
            </strong>{" "}
            — {selected.supplier_name}
            {selected.blocked ? (
              <span className="lnf-pill lnf-pill--danger"> Bloqueado</span>
            ) : null}
          </div>
          {!disabled ? (
            <button
              type="button"
              className="lnf-btn lnf-btn--ghost"
              onClick={() => {
                onSelect(null);
                setQuery("");
              }}
            >
              Trocar
            </button>
          ) : null}
        </div>
      ) : (
        <>
          <input
            id="lnf-supplier-query"
            type="search"
            placeholder="Código, nome ou CNPJ (mín. 2 caracteres)"
            value={query}
            disabled={disabled}
            onChange={(e) => setQuery(e.target.value)}
            onFocus={() => items.length > 0 && setOpen(true)}
            autoComplete="off"
          />
          {loading ? <p className="lnf-muted">Pesquisando…</p> : null}
          {searchError ? (
            <p className="lnf-error" role="alert">
              {searchError}
            </p>
          ) : null}
          {!loading && query.trim().length >= 2 && items.length === 0 && !searchError ? (
            <p className="lnf-muted">Nenhum fornecedor encontrado.</p>
          ) : null}
          {open && items.length > 0 ? (
            <ul className="lnf-supplier-list" role="listbox">
              {items.map((item) => {
                const key = `${item.supplier_code}-${item.supplier_store}`;
                return (
                  <li key={key}>
                    <button
                      type="button"
                      className="lnf-supplier-option"
                      disabled={item.blocked}
                      title={
                        item.blocked
                          ? "Fornecedor bloqueado não pode ser selecionado"
                          : undefined
                      }
                      onClick={() => {
                        if (item.blocked) return;
                        onSelect(item);
                        setOpen(false);
                        setQuery("");
                      }}
                    >
                      <span>
                        {item.supplier_code}/{item.supplier_store} — {item.supplier_name}
                      </span>
                      {item.tax_id ? (
                        <span className="lnf-muted"> CNPJ {item.tax_id}</span>
                      ) : null}
                      {item.blocked ? (
                        <span className="lnf-pill lnf-pill--danger">Bloqueado</span>
                      ) : null}
                    </button>
                  </li>
                );
              })}
            </ul>
          ) : null}
        </>
      )}
      {error ? (
        <p className="lnf-error" role="alert">
          {error}
        </p>
      ) : null}
    </div>
  );
}
