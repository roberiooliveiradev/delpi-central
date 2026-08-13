import { X } from "lucide-react";

import type { TotvsCustomerHit } from "../../../types/portfolio";
import { customerKey } from "../../../shared/format";
import { useActiveCustomerSearch } from "../hooks/useActiveCustomerSearch";

export type CustomerSearchSelection = {
  code: string;
  store: string;
  name: string;
};

export type CustomerSearchPickerProps = {
  value: CustomerSearchSelection[];
  onChange: (value: CustomerSearchSelection[]) => void;
  disabled?: boolean;
  /** Limite de selecionados (default 20). Com `1`, a próxima escolha substitui. */
  maxSelected?: number;
  labels?: {
    title?: string;
    hint?: string;
    placeholder?: string;
  };
  className?: string;
};

/** Label canônico: `{nome} · {código}/{loja}`. */
export function customerSelectionLabel(value: CustomerSearchSelection): string {
  const codeStore = `${value.code}/${value.store}`;
  const name = (value.name || "").trim();
  return name ? `${name} · ${codeStore}` : codeStore;
}

function hitLabel(hit: TotvsCustomerHit): string {
  return customerSelectionLabel({
    code: hit.code,
    store: hit.store,
    name: hit.name || "",
  });
}

/**
 * Typeahead multi-select de cliente TOTVS (busca global via commercial-api).
 * Chips alinhados ao UserDirectoryPicker / delpi-ui-tag-chip.
 */
export function CustomerSearchPicker({
  value,
  onChange,
  disabled = false,
  maxSelected = 20,
  labels,
  className,
}: CustomerSearchPickerProps) {
  const { query, setQuery, hits, searching, error, queryReady, reset } =
    useActiveCustomerSearch({ pageSize: 12 });

  const selectedKeys = new Set(value.map((item) => customerKey(item.code, item.store)));
  const atLimit = maxSelected > 0 && value.length >= maxSelected;

  const selectHit = (hit: TotvsCustomerHit) => {
    const code = hit.code.trim();
    const store = hit.store.trim();
    if (!code || !store) return;
    const key = customerKey(code, store);
    if (selectedKeys.has(key)) return;
    const next: CustomerSearchSelection = {
      code,
      store,
      name: (hit.name || "").trim(),
    };
    if (maxSelected === 1) {
      onChange([next]);
    } else if (atLimit) {
      return;
    } else {
      onChange([...value, next]);
    }
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
                  disabled={
                    disabled ||
                    selectedKeys.has(key) ||
                    (atLimit && maxSelected !== 1)
                  }
                  onClick={() => selectHit(hit)}
                >
                  {hitLabel(hit)}
                </button>
              </li>
            );
          })}
        </ul>
      ) : null}
      {value.length > 0 ? (
        <div
          className="delpi-ui-tag-list delpi-ui-user-directory-picker__selected"
          aria-label="Clientes selecionados"
        >
          {value.map((item) => {
            const label = customerSelectionLabel(item);
            const key = customerKey(item.code, item.store);
            return (
              <span key={key} className="delpi-ui-tag-chip">
                <span>{label}</span>
                <button
                  type="button"
                  className="delpi-ui-tag-chip__remove"
                  disabled={disabled}
                  aria-label={`Remover ${label}`}
                  onClick={() =>
                    onChange(value.filter((row) => customerKey(row.code, row.store) !== key))
                  }
                >
                  <X size={14} aria-hidden="true" />
                </button>
              </span>
            );
          })}
        </div>
      ) : null}
    </div>
  );
}
