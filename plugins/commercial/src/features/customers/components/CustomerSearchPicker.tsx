import type { TotvsCustomerHit } from "../../../types/portfolio";
import { customerKey } from "../../../shared/format";
import { useActiveCustomerSearch } from "../hooks/useActiveCustomerSearch";

export type CustomerSearchSelection = {
  code: string;
  store: string;
  name: string;
};

export type CustomerSearchPickerProps = {
  value: CustomerSearchSelection | null;
  onChange: (value: CustomerSearchSelection | null) => void;
  disabled?: boolean;
  labels?: {
    title?: string;
    hint?: string;
    placeholder?: string;
  };
  className?: string;
};

function hitLabel(hit: TotvsCustomerHit): string {
  const codeStore = `${hit.code}/${hit.store}`;
  const name = (hit.name || "").trim();
  return name ? `${codeStore} · ${name}` : codeStore;
}

function selectionLabel(value: CustomerSearchSelection): string {
  const codeStore = `${value.code}/${value.store}`;
  const name = (value.name || "").trim();
  return name ? `${codeStore} · ${name}` : codeStore;
}

/**
 * Typeahead single-select de cliente TOTVS (busca global via commercial-api).
 * Visual alinhado ao UserDirectoryPicker do kit.
 */
export function CustomerSearchPicker({
  value,
  onChange,
  disabled = false,
  labels,
  className,
}: CustomerSearchPickerProps) {
  const { query, setQuery, hits, searching, error, queryReady, reset } =
    useActiveCustomerSearch({ pageSize: 12 });

  const selectHit = (hit: TotvsCustomerHit) => {
    if (!hit.code.trim() || !hit.store.trim()) return;
    onChange({
      code: hit.code.trim(),
      store: hit.store.trim(),
      name: (hit.name || "").trim(),
    });
    reset();
  };

  return (
    <div
      className={["delpi-ui-user-directory-picker", "cm-customer-search-picker", className]
        .filter(Boolean)
        .join(" ")}
    >
      <div className="delpi-ui-user-directory-picker__head">
        <span className="delpi-ui-user-directory-picker__title">
          {labels?.title || "Cliente"}
        </span>
        {labels?.hint ? (
          <p className="delpi-ui-user-directory-picker__hint">{labels.hint}</p>
        ) : null}
      </div>
      <input
        className="delpi-ui-user-directory-picker__input"
        type="search"
        value={query}
        disabled={disabled}
        placeholder={labels?.placeholder || "Código ou nome do cliente"}
        onChange={(e) => setQuery(e.target.value)}
        aria-label={labels?.title || "Cliente"}
      />
      {searching ? (
        <p className="delpi-ui-user-directory-picker__status">Buscando…</p>
      ) : null}
      {error ? (
        <p className="delpi-ui-user-directory-picker__status" role="alert">
          {error}
        </p>
      ) : null}
      {!searching && queryReady && !error && hits.length === 0 ? (
        <p className="delpi-ui-user-directory-picker__status">Nenhum cliente encontrado.</p>
      ) : null}
      {hits.length > 0 ? (
        <ul className="delpi-ui-user-directory-picker__results">
          {hits.map((hit) => {
            const key = customerKey(hit.code, hit.store);
            return (
              <li key={key || `${hit.code}-${hit.store}`}>
                <button
                  type="button"
                  disabled={disabled}
                  onClick={() => selectHit(hit)}
                >
                  {hitLabel(hit)}
                </button>
              </li>
            );
          })}
        </ul>
      ) : null}
      {value ? (
        <ul className="delpi-ui-user-directory-picker__selected">
          <li>
            <span>{selectionLabel(value)}</span>
            <button
              type="button"
              disabled={disabled}
              onClick={() => onChange(null)}
            >
              Remover
            </button>
          </li>
        </ul>
      ) : null}
    </div>
  );
}
