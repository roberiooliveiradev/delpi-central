// src/components/RelationshipPicker.tsx

import type { ReactNode } from "react";
import { useMemo, useState } from "react";
import "./RelationshipPicker.css";

export type RelationshipPickerMeta = {
  label: string;
  tone?: "default" | "success" | "warning" | "danger";
};

type RelationshipPickerProps<T> = {
  title?: string;
  description?: string;

  availableTitle?: string;
  selectedTitle?: string;

  searchPlaceholder?: string;
  emptyAvailableText?: string;
  emptySelectedText?: string;

  items: T[];
  selectedIds: string[];

  disabled?: boolean;

  getId: (item: T) => string;
  getTitle: (item: T) => string;
  getSubtitle?: (item: T) => string | null | undefined;
  getDescription?: (item: T) => string | null | undefined;
  getMeta?: (item: T) => RelationshipPickerMeta[];
  getAvatar?: (item: T) => ReactNode;

  onChange: (nextIds: string[]) => void;
};

const normalize = (value: string | null | undefined) => {
  return (value ?? "").toLowerCase().trim();
};

export function RelationshipPicker<T>({
  title,
  description,
  availableTitle = "Disponíveis",
  selectedTitle = "Vinculados",
  searchPlaceholder = "Buscar...",
  emptyAvailableText = "Nenhum item disponível.",
  emptySelectedText = "Nenhum item vinculado.",
  items,
  selectedIds,
  disabled = false,
  getId,
  getTitle,
  getSubtitle,
  getDescription,
  getMeta,
  getAvatar,
  onChange,
}: RelationshipPickerProps<T>) {
  const [availableSearch, setAvailableSearch] = useState("");
  const [selectedSearch, setSelectedSearch] = useState("");

  const selectedIdSet = useMemo(() => {
    return new Set(selectedIds);
  }, [selectedIds]);

  const getMetaSearchText = (item: T) => {
    return (getMeta?.(item) ?? [])
      .map((meta) => meta.label)
      .join(" ");
  };

  const matchesSearch = (item: T, search: string) => {
    const term = normalize(search);

    if (!term) return true;

    return (
      normalize(getTitle(item)).includes(term) ||
      normalize(getSubtitle?.(item)).includes(term) ||
      normalize(getDescription?.(item)).includes(term) ||
      normalize(getMetaSearchText(item)).includes(term)
    );
  };

  const availableItems = useMemo(() => {
    return items
      .filter((item) => !selectedIdSet.has(getId(item)))
      .filter((item) => matchesSearch(item, availableSearch))
      .sort((a, b) => getTitle(a).localeCompare(getTitle(b)));
  }, [
    items,
    selectedIdSet,
    availableSearch,
    getId,
    getTitle,
    getSubtitle,
    getDescription,
    getMeta,
  ]);

  const linkedItems = useMemo(() => {
    return items
      .filter((item) => selectedIdSet.has(getId(item)))
      .filter((item) => matchesSearch(item, selectedSearch))
      .sort((a, b) => getTitle(a).localeCompare(getTitle(b)));
  }, [
    items,
    selectedIdSet,
    selectedSearch,
    getId,
    getTitle,
    getSubtitle,
    getDescription,
    getMeta,
  ]);

  const addOne = (id: string) => {
    if (disabled || selectedIdSet.has(id)) return;
    onChange([...selectedIds, id]);
  };

  const removeOne = (id: string) => {
    if (disabled) return;
    onChange(selectedIds.filter((selectedId) => selectedId !== id));
  };

  const addAllFiltered = () => {
    if (disabled || availableItems.length === 0) return;

    const next = new Set(selectedIds);

    availableItems.forEach((item) => {
      next.add(getId(item));
    });

    onChange(Array.from(next));
  };

  const removeAllFiltered = () => {
    if (disabled || linkedItems.length === 0) return;

    const removeIds = new Set(linkedItems.map(getId));

    onChange(selectedIds.filter((id) => !removeIds.has(id)));
  };

  const getInitial = (item: T) => {
    const titleValue = getTitle(item).trim();

    if (!titleValue) return "•";

    return titleValue[0].toUpperCase();
  };

  const renderMeta = (item: T) => {
    const meta = getMeta?.(item) ?? [];

    if (meta.length === 0) return null;

    return (
      <div className="relationship-card-meta">
        {meta.map((m) => (
          <span
            key={`${getId(item)}-${m.label}`}
            className={[
              "relationship-pill",
              m.tone ? `relationship-pill-${m.tone}` : "",
            ]
              .filter(Boolean)
              .join(" ")}
          >
            {m.label}
          </span>
        ))}
      </div>
    );
  };

  const renderCard = (item: T, mode: "available" | "selected") => {
    const id = getId(item);
    const subtitle = getSubtitle?.(item);
    const descriptionValue = getDescription?.(item);

    const isAvailable = mode === "available";
    const avatar = getAvatar?.(item);

    return (
      <article
        key={id}
        className={[
          "relationship-card",
          isAvailable
            ? "relationship-card-available"
            : "relationship-card-selected",
        ]
          .filter(Boolean)
          .join(" ")}
      >
        <div className="relationship-card-icon" aria-hidden="true">
          {avatar ?? getInitial(item)}
        </div>

        <div className="relationship-card-main">
          <div className="relationship-card-title-row">
            <strong className="relationship-card-title">
              {getTitle(item)}
            </strong>
          </div>

          {subtitle && (
            <div className="relationship-card-subtitle">
              {subtitle}
            </div>
          )}

          {descriptionValue && (
            <div className="relationship-card-description">
              {descriptionValue}
            </div>
          )}

          {renderMeta(item)}
        </div>

        <button
          type="button"
          className={[
            "relationship-action",
            isAvailable
              ? "relationship-action-add"
              : "relationship-action-remove",
          ]
            .filter(Boolean)
            .join(" ")}
          disabled={disabled}
          onClick={() => (isAvailable ? addOne(id) : removeOne(id))}
          aria-label={
            isAvailable
              ? `Adicionar ${getTitle(item)}`
              : `Remover ${getTitle(item)}`
          }
        >
          <span>{isAvailable ? "Adicionar" : "Remover"}</span>
          <strong aria-hidden="true">{isAvailable ? "→" : "×"}</strong>
        </button>
      </article>
    );
  };

  return (
    <section className="relationship-picker">
      {(title || description) && (
        <header className="relationship-picker-header">
          <div className="relationship-picker-heading">
            {title && <h4>{title}</h4>}
            {description && <p>{description}</p>}
          </div>

          <div className="relationship-picker-summary">
            <span>
              <strong>{selectedIds.length}</strong>
              vinculados
            </span>
            <span>
              <strong>{items.length}</strong>
              no catálogo
            </span>
          </div>
        </header>
      )}

      <div className="relationship-columns">
        <section className="relationship-column relationship-column-available">
          <div className="relationship-column-header">
            <div>
              <strong>{availableTitle}</strong>
              <span>{availableItems.length} itens encontrados</span>
            </div>

            <button
              type="button"
              className="relationship-mini-button"
              disabled={disabled || availableItems.length === 0}
              onClick={addAllFiltered}
            >
              Adicionar filtrados
            </button>
          </div>

          <div className="relationship-searchbar">
            <span aria-hidden="true">⌕</span>
            <input
              value={availableSearch}
              onChange={(event) => setAvailableSearch(event.target.value)}
              placeholder={searchPlaceholder}
              disabled={disabled}
              aria-label={availableTitle}
            />
          </div>

          <div className="relationship-list">
            {availableItems.length === 0 ? (
              <div className="relationship-empty">
                <div className="relationship-empty-icon">+</div>
                <strong>Nada por aqui</strong>
                <span>{emptyAvailableText}</span>
              </div>
            ) : (
              availableItems.map((item) => renderCard(item, "available"))
            )}
          </div>
        </section>

        <section className="relationship-column relationship-column-selected">
          <div className="relationship-column-header">
            <div>
              <strong>{selectedTitle}</strong>
              <span>{linkedItems.length} itens encontrados</span>
            </div>

            <button
              type="button"
              className="relationship-mini-button relationship-mini-danger"
              disabled={disabled || linkedItems.length === 0}
              onClick={removeAllFiltered}
            >
              Remover filtrados
            </button>
          </div>

          <div className="relationship-searchbar">
            <span aria-hidden="true">⌕</span>
            <input
              value={selectedSearch}
              onChange={(event) => setSelectedSearch(event.target.value)}
              placeholder={searchPlaceholder}
              disabled={disabled}
              aria-label={selectedTitle}
            />
          </div>

          <div className="relationship-list">
            {linkedItems.length === 0 ? (
              <div className="relationship-empty relationship-empty-selected">
                <div className="relationship-empty-icon">✓</div>
                <strong>Nenhum vínculo</strong>
                <span>{emptySelectedText}</span>
              </div>
            ) : (
              linkedItems.map((item) => renderCard(item, "selected"))
            )}
          </div>
        </section>
      </div>
    </section>
  );
}