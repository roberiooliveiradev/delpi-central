import { X } from "lucide-react";
import type { ReactNode } from "react";
import { useEffect, useRef, useState } from "react";

export type EntityDirectoryOption = {
  id: string;
  label: string;
  secondary?: string;
};

export type EntityDirectoryPickerProps = {
  value: EntityDirectoryOption[];
  onChange: (entities: EntityDirectoryOption[]) => void;
  searchEntities: (
    query: string,
    limit?: number,
    signal?: AbortSignal,
  ) => Promise<EntityDirectoryOption[]>;
  disabled?: boolean;
  /**
   * Exibe chips dos selecionados com × (default true).
   * Passe false quando o consumidor já renderiza a própria lista (evita duplicação).
   */
  showSelectedList?: boolean;
  /**
   * Limite de selecionados. Com `1`, a próxima escolha substitui a atual (single-select).
   */
  maxSelected?: number;
  /** Conteúdo à esquerda de cada sugestão (ex.: avatar). */
  renderOptionLeading?: (entity: EntityDirectoryOption) => ReactNode;
  /**
   * Chip selecionado customizado. Sem slot, usa tag-chip padrão com label + ×.
   */
  renderSelectedChip?: (args: {
    entity: EntityDirectoryOption;
    label: string;
    disabled: boolean;
    onRemove: () => void;
  }) => ReactNode;
  labels?: {
    title?: string;
    hint?: string;
    placeholder?: string;
    searching?: string;
    empty?: string;
    emptySelected?: string;
    selectedAriaLabel?: string;
  };
  className?: string;
};

export function entityDirectoryLabel(entity: EntityDirectoryOption): string {
  const primary = (entity.label || "").trim() || entity.id;
  const secondary = (entity.secondary || "").trim();
  if (!secondary || secondary === primary) {
    return primary;
  }
  return `${primary} · ${secondary}`;
}

function isAbortError(error: unknown): boolean {
  if (!error || typeof error !== "object") return false;
  const name = "name" in error ? String((error as { name?: unknown }).name) : "";
  return name === "AbortError";
}

export function EntityDirectoryPicker({
  value,
  onChange,
  searchEntities,
  disabled = false,
  showSelectedList = true,
  maxSelected,
  renderOptionLeading,
  renderSelectedChip,
  labels,
  className,
}: EntityDirectoryPickerProps) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<EntityDirectoryOption[]>([]);
  const [searching, setSearching] = useState(false);
  /** Evita re-abortar a busca quando o pai passa `searchEntities` inline a cada render. */
  const searchEntitiesRef = useRef(searchEntities);
  searchEntitiesRef.current = searchEntities;

  useEffect(() => {
    const normalized = query.trim();
    if (normalized.length < 2) {
      setResults([]);
      setSearching(false);
      return;
    }
    const controller = new AbortController();
    const timeoutId = window.setTimeout(() => {
      setSearching(true);
      void searchEntitiesRef
        .current(normalized, 10, controller.signal)
        .then((items) => {
          if (!controller.signal.aborted) setResults(items);
        })
        .catch((error: unknown) => {
          if (controller.signal.aborted || isAbortError(error)) return;
          setResults([]);
        })
        .finally(() => {
          if (!controller.signal.aborted) setSearching(false);
        });
    }, 280);
    return () => {
      controller.abort();
      window.clearTimeout(timeoutId);
    };
  }, [query]);

  const selectedIds = new Set(value.map((item) => item.id));
  const atLimit =
    typeof maxSelected === "number" && maxSelected > 0 && value.length >= maxSelected;
  const visibleResults = results.filter((entity) => !selectedIds.has(entity.id));

  return (
    <div className={["delpi-ui-user-directory-picker", className].filter(Boolean).join(" ")}>
      <div className="delpi-ui-user-directory-picker__head">
        <span className="delpi-ui-user-directory-picker__title">
          {labels?.title || "Entidades"}
        </span>
        {labels?.hint ? (
          <p className="delpi-ui-user-directory-picker__hint">{labels.hint}</p>
        ) : null}
      </div>
      <input
        className="delpi-ui-user-directory-picker__input"
        value={query}
        disabled={disabled}
        placeholder={labels?.placeholder || "Buscar…"}
        onChange={(e) => setQuery(e.target.value)}
      />
      {searching ? (
        <p className="delpi-ui-user-directory-picker__status">
          {labels?.searching || "Buscando…"}
        </p>
      ) : null}
      {!searching && query.trim().length >= 2 && visibleResults.length === 0 ? (
        <p className="delpi-ui-user-directory-picker__status">
          {results.length > 0
            ? labels?.emptySelected ||
              "Nenhum resultado disponível — já selecionados."
            : labels?.empty || "Nenhum resultado encontrado."}
        </p>
      ) : null}
      {visibleResults.length > 0 ? (
        <ul className="delpi-ui-user-directory-picker__results">
          {visibleResults.map((entity) => (
            <li key={entity.id}>
              <button
                type="button"
                className={
                  renderOptionLeading
                    ? "delpi-ui-user-directory-picker__option delpi-ui-user-directory-picker__option--with-leading"
                    : undefined
                }
                disabled={disabled || (atLimit && maxSelected !== 1)}
                onClick={() => {
                  if (selectedIds.has(entity.id)) return;
                  if (maxSelected === 1) {
                    onChange([entity]);
                  } else if (atLimit) {
                    return;
                  } else {
                    onChange([...value, entity]);
                  }
                  setQuery("");
                  setResults([]);
                }}
              >
                {renderOptionLeading ? (
                  <span className="delpi-ui-user-directory-picker__option-leading">
                    {renderOptionLeading(entity)}
                  </span>
                ) : null}
                <span className="delpi-ui-user-directory-picker__option-label">
                  {entityDirectoryLabel(entity)}
                </span>
              </button>
            </li>
          ))}
        </ul>
      ) : null}
      {showSelectedList && value.length > 0 ? (
        <div
          className="delpi-ui-tag-list delpi-ui-user-directory-picker__selected"
          aria-label={labels?.selectedAriaLabel || "Selecionados"}
        >
          {value.map((entity) => {
            const label = entityDirectoryLabel(entity);
            const onRemove = () =>
              onChange(value.filter((item) => item.id !== entity.id));
            if (renderSelectedChip) {
              return (
                <span key={entity.id}>
                  {renderSelectedChip({ entity, label, disabled, onRemove })}
                </span>
              );
            }
            return (
              <span key={entity.id} className="delpi-ui-tag-chip">
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
