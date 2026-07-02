import { useEffect, useRef, useState } from "react";
import { Loader2, Search } from "lucide-react";
import { searchCustomers } from "../api/customersApi";
import { CustomerSearchModal } from "./CustomerSearchModal";
import type { Customer } from "../types";

const SUGGEST_LIMIT = 8;
const DEBOUNCE_MS = 300;
const MIN_CHARS = 2;

export function CompanyField({
  value,
  onChange,
}: {
  value: string;
  onChange: (name: string) => void;
}) {
  const [suggestions, setSuggestions] = useState<Customer[]>([]);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [highlight, setHighlight] = useState(-1);
  const wrapperRef = useRef<HTMLDivElement>(null);
  // Evita reabrir o dropdown logo após selecionar (evento de digitação sintético).
  const skipNextSearch = useRef(false);

  useEffect(() => {
    if (skipNextSearch.current) {
      skipNextSearch.current = false;
      return;
    }
    const term = value.trim();
    if (term.length < MIN_CHARS) {
      setSuggestions([]);
      setOpen(false);
      return;
    }
    const controller = new AbortController();
    const timer = window.setTimeout(async () => {
      setLoading(true);
      try {
        const result = await searchCustomers(
          { name: term, pageSize: SUGGEST_LIMIT },
          controller.signal,
        );
        setSuggestions(result.items);
        setOpen(result.items.length > 0);
        setHighlight(-1);
      } catch {
        // Silencioso: autocomplete é assistivo; usuário pode digitar livremente.
        setSuggestions([]);
        setOpen(false);
      } finally {
        setLoading(false);
      }
    }, DEBOUNCE_MS);

    return () => {
      controller.abort();
      window.clearTimeout(timer);
    };
  }, [value]);

  useEffect(() => {
    const onClickAway = (e: MouseEvent) => {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", onClickAway);
    return () => document.removeEventListener("mousedown", onClickAway);
  }, []);

  const pick = (customer: Customer) => {
    skipNextSearch.current = true;
    onChange(customer.name);
    setOpen(false);
    setSuggestions([]);
    setHighlight(-1);
  };

  const onKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (!open || suggestions.length === 0) return;
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setHighlight((h) => Math.min(h + 1, suggestions.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setHighlight((h) => Math.max(h - 1, 0));
    } else if (e.key === "Enter" && highlight >= 0) {
      e.preventDefault();
      pick(suggestions[highlight]);
    } else if (e.key === "Escape") {
      setOpen(false);
    }
  };

  return (
    <div className="cx-field" ref={wrapperRef}>
      <span>Empresa</span>
      <div className="cx-company-input">
        <input
          type="text"
          required
          value={value}
          autoComplete="off"
          onChange={(e) => onChange(e.target.value)}
          onFocus={() => suggestions.length > 0 && setOpen(true)}
          onKeyDown={onKeyDown}
          placeholder="Digite ou pesquise o cliente"
        />
        {loading && <Loader2 size={16} className="cx-spin cx-company-input__spin" />}
        <button
          className="cx-company-input__search"
          type="button"
          onClick={() => setModalOpen(true)}
          title="Pesquisar cliente no TOTVS"
          aria-label="Pesquisar cliente no TOTVS"
        >
          <Search size={16} />
        </button>

        {open && suggestions.length > 0 && (
          <ul className="cx-suggestions" role="listbox">
            {suggestions.map((customer, index) => (
              <li key={`${customer.code}-${customer.store}`}>
                <button
                  type="button"
                  role="option"
                  aria-selected={index === highlight}
                  className={`cx-suggestion${index === highlight ? " is-active" : ""}`}
                  onMouseEnter={() => setHighlight(index)}
                  onClick={() => pick(customer)}
                >
                  <span className="cx-suggestion__name">{customer.name}</span>
                  <span className="cx-suggestion__meta">
                    {customer.code}
                    {customer.store ? `/${customer.store}` : ""}
                  </span>
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>

      {modalOpen && (
        <CustomerSearchModal
          initialName={value.trim()}
          onSelect={(customer) => {
            pick(customer);
            setModalOpen(false);
          }}
          onClose={() => setModalOpen(false)}
        />
      )}
    </div>
  );
}
