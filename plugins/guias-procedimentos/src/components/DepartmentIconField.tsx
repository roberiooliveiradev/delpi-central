import { Search, X } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { createPortal } from "react-dom";

import {
  DEPARTMENT_ICON_CATALOG,
  listLucideIconNames,
  resolveLucideIcon,
  toKebabCase,
  toPascalCaseFromKebab,
} from "../utils/lucideIcons.ts";
import { DepartmentIcon } from "./DepartmentIcon";

type DepartmentIconFieldProps = {
  value: string;
  onChange: (icon: string) => void;
  disabled?: boolean;
};

const DEFAULT_ICON = "book-open";
const MAX_SEARCH_RESULTS = 240;

/**
 * Campo de ícone com prévia + biblioteca local (sem depender do picker federado).
 */
export function DepartmentIconField({
  value,
  onChange,
  disabled = false,
}: DepartmentIconFieldProps) {
  const [pickerOpen, setPickerOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [draft, setDraft] = useState(value.trim() || DEFAULT_ICON);
  const current = value.trim() || DEFAULT_ICON;

  useEffect(() => {
    if (!pickerOpen) return;
    setDraft(current);
    setQuery("");
    const previous = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = previous;
    };
  }, [pickerOpen, current]);

  const allPascal = useMemo(() => listLucideIconNames(), []);

  const curated = useMemo(
    () =>
      DEPARTMENT_ICON_CATALOG.filter((kebab) => resolveLucideIcon(kebab) != null),
    [],
  );

  const searchResults = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return [];
    return allPascal
      .filter((pascal) => {
        const kebab = toKebabCase(pascal);
        return kebab.includes(q) || pascal.toLowerCase().includes(q);
      })
      .slice(0, MAX_SEARCH_RESULTS)
      .map((pascal) => toKebabCase(pascal));
  }, [allPascal, query]);

  const visibleIcons = query.trim() ? searchResults : [...curated];
  const selectedPascal = current.includes("-")
    ? toPascalCaseFromKebab(current)
    : current;
  const draftPascal = draft.includes("-")
    ? toPascalCaseFromKebab(draft)
    : draft;

  function applyAndClose(next: string) {
    const normalized = next.trim() || DEFAULT_ICON;
    setDraft(normalized);
    onChange(normalized);
    // Evita “click-through” do evento no overlay após desmontar o portal.
    window.setTimeout(() => setPickerOpen(false), 0);
  }

  function confirmDraft() {
    applyAndClose(draft || DEFAULT_ICON);
  }

  return (
    <div className="gp-icon-field">
      <span className="gp-icon-field__label">Ícone</span>

      <div className="gp-icon-field__preview-row">
        <span className="gp-icon-field__preview" aria-hidden="true">
          <DepartmentIcon icon={current} size={28} />
        </span>
        <div className="gp-icon-field__meta">
          <code className="gp-icon-field__code">{current}</code>
          <span className="gp-field__hint">
            Prévia em tempo real — escolha na biblioteca Lucide.
          </span>
        </div>
        <button
          type="button"
          className="gp-btn gp-btn--secondary gp-btn--compact"
          disabled={disabled}
          onClick={() => setPickerOpen(true)}
        >
          Biblioteca de ícones
        </button>
      </div>

      {pickerOpen && typeof document !== "undefined"
        ? createPortal(
            <div
              className="dashboard-guias-procedimentos gp-modal-overlay"
              role="presentation"
              onMouseDown={(event) => {
                if (event.target === event.currentTarget) {
                  setPickerOpen(false);
                }
              }}
            >
              <div
                className="gp-modal gp-modal--icon-picker"
                role="dialog"
                aria-modal="true"
                aria-label="Selecionar ícone do departamento"
                onMouseDown={(event) => event.stopPropagation()}
              >
                <div className="gp-icon-picker">
                  <header className="gp-icon-picker__header">
                    <h2 className="gp-icon-picker__title">Ícone do departamento</h2>
                    <button
                      type="button"
                      className="gp-modal__close"
                      aria-label="Fechar"
                      onClick={() => setPickerOpen(false)}
                    >
                      <X size={18} aria-hidden="true" />
                    </button>
                  </header>

                  <div className="gp-icon-picker__body">
                    <label className="gp-icon-picker__search">
                      <Search size={16} aria-hidden="true" />
                      <input
                        className="gp-input"
                        type="search"
                        value={query}
                        placeholder="Buscar (ex.: fábrica, receita, livro…)"
                        onChange={(event) => setQuery(event.target.value)}
                        autoComplete="off"
                        spellCheck={false}
                      />
                    </label>

                    <div className="gp-icon-picker__selected">
                      <span>Selecionado:</span>
                      <DepartmentIcon icon={draft} size={20} />
                      <code>{draft}</code>
                    </div>

                    <div className="gp-icon-picker__grid" role="listbox">
                      {visibleIcons.map((kebab) => {
                        const pascal = toPascalCaseFromKebab(kebab);
                        const active =
                          pascal === draftPascal || pascal === selectedPascal;
                        return (
                          <button
                            key={kebab}
                            type="button"
                            role="option"
                            aria-selected={active}
                            className={`gp-icon-picker__card${active ? " is-active" : ""}`}
                            title={kebab}
                            onClick={() => {
                              setDraft(kebab);
                              onChange(kebab);
                            }}
                          >
                            <span className="gp-icon-picker__card-icon" aria-hidden="true">
                              <DepartmentIcon icon={kebab} size={28} />
                            </span>
                            <span className="gp-icon-picker__card-label">{kebab}</span>
                          </button>
                        );
                      })}
                    </div>

                    {visibleIcons.length === 0 ? (
                      <p className="gp-field__hint">Nenhum ícone encontrado.</p>
                    ) : null}
                    {query.trim() && searchResults.length >= MAX_SEARCH_RESULTS ? (
                      <p className="gp-field__hint">
                        Mostrando {MAX_SEARCH_RESULTS} resultados. Refine a busca.
                      </p>
                    ) : null}
                  </div>

                  <footer className="gp-icon-picker__footer">
                    <button
                      type="button"
                      className="gp-btn gp-btn--ghost"
                      onClick={() => applyAndClose(DEFAULT_ICON)}
                    >
                      Usar padrão (book-open)
                    </button>
                    <button
                      type="button"
                      className="gp-btn gp-btn--secondary"
                      onClick={confirmDraft}
                    >
                      Concluir
                    </button>
                  </footer>
                </div>
              </div>
            </div>,
            document.body,
          )
        : null}
    </div>
  );
}
