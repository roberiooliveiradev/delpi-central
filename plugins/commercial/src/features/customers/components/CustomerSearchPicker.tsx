import { X } from "lucide-react";
import { useMemo, type ReactNode } from "react";

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
  /**
   * Chaves `code/store` já vinculadas (ou bloqueadas) — não entram na lista de resultados.
   */
  excludeKeys?: ReadonlySet<string>;
  /** Conteúdo à esquerda de cada sugestão (ex.: avatar). */
  renderOptionLeading?: (hit: TotvsCustomerHit) => ReactNode;
  /**
   * Chip selecionado customizado. Sem slot, usa tag-chip padrão com label + ×.
   */
  renderSelectedChip?: (args: {
    item: CustomerSearchSelection;
    label: string;
    disabled: boolean;
    onRemove: () => void;
  }) => ReactNode;
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
  excludeKeys,
  renderOptionLeading,
  renderSelectedChip,
  labels,
  className,
}: CustomerSearchPickerProps) {
  const { query, setQuery, hits, searching, error, queryReady, reset } =
    useActiveCustomerSearch({ pageSize: 12 });

  const blockedKeys = useMemo(() => {
    const next = new Set<string>();
    if (excludeKeys) {
      for (const key of excludeKeys) {
        const normalized = key.trim();
        if (normalized) next.add(normalized);
      }
    }
    for (const item of value) {
      const key = customerKey(item.code, item.store);
      if (key) next.add(key);
    }
    return next;
  }, [excludeKeys, value]);

  const visibleHits = useMemo(
    () =>
      hits.filter((hit) => {
        const key = customerKey(hit.code, hit.store);
        return Boolean(key) && !blockedKeys.has(key);
      }),
    [blockedKeys, hits],
  );

  const atLimit = maxSelected > 0 && value.length >= maxSelected;

  const selectHit = (hit: TotvsCustomerHit) => {
    const code = hit.code.trim();
    const store = hit.store.trim();
    if (!code || !store) return;
    const key = customerKey(code, store);
    if (!key || blockedKeys.has(key)) return;
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

  const selectAllHits = () => {
    if (disabled || maxSelected === 1 || visibleHits.length === 0) return;
    const remaining =
      typeof maxSelected === "number" && maxSelected > 0
        ? Math.max(0, maxSelected - value.length)
        : visibleHits.length;
    if (remaining === 0) return;
    const additions: CustomerSearchSelection[] = [];
    for (const hit of visibleHits) {
      if (additions.length >= remaining) break;
      const code = hit.code.trim();
      const store = hit.store.trim();
      if (!code || !store) continue;
      const key = customerKey(code, store);
      if (!key || blockedKeys.has(key)) continue;
      if (additions.some((item) => customerKey(item.code, item.store) === key)) {
        continue;
      }
      additions.push({
        code,
        store,
        name: (hit.name || "").trim(),
      });
    }
    if (additions.length === 0) return;
    onChange([...value, ...additions]);
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
      {!searching && queryReady && !error && visibleHits.length === 0 ? (
        <p className="delpi-ui-user-directory-picker__status">
          {hits.length > 0
            ? "Nenhum resultado disponível — já selecionados ou vinculados."
            : "Nenhum cliente encontrado."}
        </p>
      ) : null}
      {visibleHits.length > 0 ? (
        <>
          {maxSelected !== 1 ? (
            <div className="delpi-ui-user-directory-picker__status">
              <button
                type="button"
                className="delpi-ui-user-directory-picker__option"
                disabled={disabled || atLimit}
                onClick={selectAllHits}
              >
                {atLimit
                  ? "Limite de seleção atingido"
                  : `Selecionar todos filtrados (${Math.min(
                      visibleHits.length,
                      typeof maxSelected === "number" && maxSelected > 0
                        ? Math.max(0, maxSelected - value.length)
                        : visibleHits.length,
                    )})`}
              </button>
            </div>
          ) : null}
          <ul className="delpi-ui-user-directory-picker__results">
            {visibleHits.map((hit) => {
              const key = customerKey(hit.code, hit.store);
              return (
                <li key={key || `${hit.code}-${hit.store}`}>
                  <button
                    type="button"
                    className={
                      renderOptionLeading
                        ? "delpi-ui-user-directory-picker__option delpi-ui-user-directory-picker__option--with-leading"
                        : undefined
                    }
                    disabled={disabled || (atLimit && maxSelected !== 1)}
                    onClick={() => selectHit(hit)}
                  >
                    {renderOptionLeading ? (
                      <span className="delpi-ui-user-directory-picker__option-leading">
                        {renderOptionLeading(hit)}
                      </span>
                    ) : null}
                    <span className="delpi-ui-user-directory-picker__option-label">
                      {hitLabel(hit)}
                    </span>
                  </button>
                </li>
              );
            })}
          </ul>
        </>
      ) : null}
      {value.length > 0 ? (
        <div
          className="delpi-ui-tag-list delpi-ui-user-directory-picker__selected"
          aria-label="Clientes selecionados"
        >
          {value.map((item) => {
            const label = customerSelectionLabel(item);
            const key = customerKey(item.code, item.store);
            const onRemove = () =>
              onChange(value.filter((row) => customerKey(row.code, row.store) !== key));
            if (renderSelectedChip) {
              return (
                <span key={key}>
                  {renderSelectedChip({ item, label, disabled, onRemove })}
                </span>
              );
            }
            return (
              <span key={key} className="delpi-ui-tag-chip">
                <span>{label}</span>
                <button
                  type="button"
                  className="delpi-ui-tag-chip__remove"
                  disabled={disabled}
                  aria-label={`Remover ${label}`}
                  onClick={onRemove}
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
