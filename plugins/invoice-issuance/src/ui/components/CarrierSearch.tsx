import { useEffect, useRef, useState } from "react";
import { FieldLabel } from "@delpi/plugin-ui/index";
import * as api from "../../data/api/invoiceIssuanceApi";
import { II_HELP } from "../../content/helpTooltips";
import type { Carrier } from "../../domain/types";
import { formatTaxId } from "../format";
import { TextField } from "../kit";

type Props = {
  selected: Carrier | null;
  onSelect: (carrier: Carrier | null) => void;
  disabled?: boolean;
};

export function CarrierSearch({ selected, onSelect, disabled }: Props) {
  const [query, setQuery] = useState("");
  const [items, setItems] = useState<Carrier[]>([]);
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
        .searchCarriers(query.trim(), 20, controller.signal)
        .then((rows) => {
          setItems(rows);
          setOpen(true);
        })
        .catch((err: unknown) => {
          if ((err as { name?: string }).name === "AbortError") return;
          setSearchError(err instanceof Error ? err.message : "Falha na busca.");
        })
        .finally(() => setLoading(false));
    }, 350);
    return () => {
      if (debounceRef.current) window.clearTimeout(debounceRef.current);
    };
  }, [query]);

  return (
    <div className="ii-search" data-testid="carrier-search">
      <FieldLabel
        label="Transportadora (opcional)"
        hint={II_HELP.carrierSearch}
        htmlFor="ii-carrier-query"
      />
      <TextField
        id="ii-carrier-query"
        label="Código, nome reduzido ou CNPJ"
        value={query}
        onChange={setQuery}
        placeholder="Digite ao menos 2 caracteres"
        disabled={disabled}
        fullWidth
      />
      {loading ? <p className="ii-muted">Buscando…</p> : null}
      {searchError ? (
        <p className="ii-alert ii-error" role="alert">
          {searchError}
        </p>
      ) : null}
      {open && items.length > 0 ? (
        <ul className="ii-search__list" data-testid="carrier-results">
          {items.map((item) => (
            <li key={item.carrier_code}>
              <button
                type="button"
                disabled={item.blocked || disabled}
                onClick={() => {
                  onSelect(item);
                  setOpen(false);
                  setQuery("");
                }}
              >
                <strong>{item.carrier_code}</strong> {item.carrier_name}
                {item.legal_name && item.legal_name !== item.carrier_name ? (
                  <span className="ii-muted"> · {item.legal_name}</span>
                ) : null}
                <span className="ii-muted"> {formatTaxId(item.tax_id)}</span>
                {item.blocked ? " (bloqueada)" : ""}
              </button>
            </li>
          ))}
        </ul>
      ) : null}
      {open && !loading && query.trim().length >= 2 && items.length === 0 ? (
        <p className="ii-alert" data-testid="carrier-empty">
          {II_HELP.carrierMissing}
        </p>
      ) : null}
      {selected ? (
        <p className="ii-selected" data-testid="carrier-selected">
          Selecionada: {selected.carrier_code ? `${selected.carrier_code} — ` : ""}
          {selected.carrier_name}
          {selected.tax_id ? ` · ${formatTaxId(selected.tax_id)}` : ""}
          {selected.phone ? ` · ${selected.phone}` : ""}
          <button
            type="button"
            className="ii-btn ii-btn--ghost ii-btn--sm"
            onClick={() => onSelect(null)}
          >
            Trocar
          </button>
        </p>
      ) : null}
    </div>
  );
}
