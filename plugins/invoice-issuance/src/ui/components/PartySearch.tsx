import { useEffect, useRef, useState } from "react";
import { FieldLabel } from "@delpi/plugin-ui/index";
import * as api from "../../data/api/invoiceIssuanceApi";
import { II_HELP } from "../../content/helpTooltips";
import type { Party, PartyType } from "../../domain/types";
import { formatTaxId } from "../format";
import { SegmentToggle, TextField } from "../kit";

type Props = {
  partyType: PartyType;
  selected: Party | null;
  onPartyTypeChange: (value: PartyType) => void;
  onSelect: (party: Party | null) => void;
  disabled?: boolean;
};

export function PartySearch({
  partyType,
  selected,
  onPartyTypeChange,
  onSelect,
  disabled,
}: Props) {
  const [query, setQuery] = useState("");
  const [items, setItems] = useState<Party[]>([]);
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
        .searchParties(partyType, query.trim(), 20, controller.signal)
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
  }, [query, partyType]);

  return (
    <div className="ii-search" data-testid="party-search">
      <SegmentToggle
        ariaLabel="Tipo de destinatário"
        value={partyType}
        onChange={(value: string) => {
          onPartyTypeChange(value as PartyType);
          onSelect(null);
          setQuery("");
          setItems([]);
        }}
        disabled={disabled}
        options={[
          { value: "customer", label: "Cliente" },
          { value: "supplier", label: "Fornecedor" },
        ]}
      />
      <FieldLabel
        label="Busca no TOTVS"
        hint={II_HELP.partySearch}
        htmlFor="ii-party-query"
      />
      <TextField
        id="ii-party-query"
        label="Código, nome ou CNPJ"
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
        <ul className="ii-search__list" data-testid="party-results">
          {items.map((item) => (
            <li key={`${item.party_code}-${item.party_store}`}>
              <button
                type="button"
                disabled={item.blocked || disabled}
                onClick={() => {
                  onSelect(item);
                  setOpen(false);
                  setQuery("");
                }}
              >
                <strong>
                  {item.party_code} / {item.party_store}
                </strong>{" "}
                {item.party_name}
                <span className="ii-muted"> {formatTaxId(item.tax_id)}</span>
                {item.blocked ? " (bloqueado)" : ""}
              </button>
            </li>
          ))}
        </ul>
      ) : null}
      {open && !loading && query.trim().length >= 2 && items.length === 0 ? (
        <p className="ii-alert" data-testid="party-empty">
          {II_HELP.partyMissing}
        </p>
      ) : null}
      {selected ? (
        <p className="ii-selected" data-testid="party-selected">
          Selecionado: {selected.party_code}/{selected.party_store} — {selected.party_name}
          <button type="button" className="ii-btn ii-btn--ghost ii-btn--sm" onClick={() => onSelect(null)}>
            Trocar
          </button>
        </p>
      ) : null}
    </div>
  );
}
