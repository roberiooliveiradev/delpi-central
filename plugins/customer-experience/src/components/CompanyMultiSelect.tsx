import { useEffect, useMemo, useRef, useState } from "react";
import { Building2, Check, ChevronDown, X } from "lucide-react";
import { NativeTextControl } from "@delpi/plugin-ui/index";

export function CompanyMultiSelect({
  options,
  selected,
  onChange,
}: {
  options: string[];
  selected: string[];
  onChange: (next: string[]) => void;
}) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const wrapperRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const onClickAway = (e: MouseEvent) => {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", onClickAway);
    return () => document.removeEventListener("mousedown", onClickAway);
  }, []);

  const filtered = useMemo(() => {
    const term = query.trim().toLowerCase();
    if (!term) return options;
    return options.filter((o) => o.toLowerCase().includes(term));
  }, [options, query]);

  const toggle = (company: string) => {
    onChange(
      selected.includes(company)
        ? selected.filter((c) => c !== company)
        : [...selected, company],
    );
  };

  const label =
    selected.length === 0
      ? "Todas as empresas"
      : selected.length === 1
        ? selected[0]
        : `${selected.length} empresas`;

  return (
    <div className="cx-multiselect" ref={wrapperRef}>
      <button
        type="button"
        className={`cx-multiselect__trigger${selected.length > 0 ? " has-value" : ""}`}
        onClick={() => setOpen((o) => !o)}
      >
        <Building2 size={16} />
        <span className="cx-multiselect__label">{label}</span>
        {selected.length > 0 && (
          <span
            className="cx-multiselect__clear"
            role="button"
            tabIndex={0}
            aria-label="Limpar empresas"
            onClick={(e) => {
              e.stopPropagation();
              onChange([]);
            }}
            onKeyDown={(e) => {
              if (e.key === "Enter" || e.key === " ") {
                e.stopPropagation();
                onChange([]);
              }
            }}
          >
            <X size={14} />
          </span>
        )}
        <ChevronDown size={16} className="cx-multiselect__caret" />
      </button>

      {open && (
        <div className="cx-multiselect__panel">
          <NativeTextControl
            type="text"
            className="cx-multiselect__search"
            value={query}
            onChange={setQuery}
            placeholder="Filtrar empresas..."
            autoFocus
          />
          <ul className="cx-multiselect__list">
            {filtered.length === 0 ? (
              <li className="cx-multiselect__empty">Nenhuma empresa.</li>
            ) : (
              filtered.map((company) => {
                const isSelected = selected.includes(company);
                return (
                  <li key={company}>
                    <button
                      type="button"
                      className={`cx-multiselect__option${isSelected ? " is-selected" : ""}`}
                      onClick={() => toggle(company)}
                    >
                      <span className="cx-multiselect__check">
                        {isSelected && <Check size={14} />}
                      </span>
                      <span className="cx-multiselect__option-label">{company}</span>
                    </button>
                  </li>
                );
              })
            )}
          </ul>
        </div>
      )}
    </div>
  );
}
