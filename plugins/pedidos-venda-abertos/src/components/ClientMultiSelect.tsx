import { ChevronDown } from "lucide-react";
import { useEffect, useId, useMemo, useRef, useState } from "react";

import type { ClientOption } from "../utils/filterItems";

type ClientMultiSelectProps = {
  clients: ClientOption[];
  selectedKeys: string[];
  onChange: (keys: string[]) => void;
};

export function ClientMultiSelect({
  clients,
  selectedKeys,
  onChange,
}: ClientMultiSelectProps) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const wrapperRef = useRef<HTMLDivElement>(null);
  const listId = useId();

  const filteredClients = useMemo(() => {
    const normalizedQuery = query.trim().toLocaleLowerCase("pt-BR");
    if (!normalizedQuery) return clients;
    return clients.filter((client) =>
      client.name.toLocaleLowerCase("pt-BR").includes(normalizedQuery),
    );
  }, [clients, query]);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (wrapperRef.current?.contains(event.target as Node)) return;
      setOpen(false);
    }

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const triggerLabel = useMemo(() => {
    if (selectedKeys.length === 0) return "Todos os clientes";
    if (selectedKeys.length === 1) {
      return clients.find((client) => client.key === selectedKeys[0])?.name ?? "1 cliente";
    }
    return `${selectedKeys.length} clientes selecionados`;
  }, [clients, selectedKeys]);

  const toggleClient = (key: string) => {
    if (selectedKeys.includes(key)) {
      onChange(selectedKeys.filter((selected) => selected !== key));
      return;
    }
    onChange([...selectedKeys, key]);
  };

  const selectVisible = () => {
    const visibleKeys = filteredClients.map((client) => client.key);
    onChange([...new Set([...selectedKeys, ...visibleKeys])]);
  };

  return (
    <div className="pva-field pva-field--clients" ref={wrapperRef}>
      <span>Cliente</span>
      <div className={`pva-multi-select${open ? " pva-multi-select--open" : ""}`}>
        <button
          type="button"
          className="pva-multi-select__trigger"
          aria-expanded={open}
          aria-haspopup="listbox"
          aria-controls={listId}
          onClick={() => setOpen((current) => !current)}
        >
          <span className="pva-multi-select__trigger-label">{triggerLabel}</span>
          <ChevronDown size={16} aria-hidden="true" />
        </button>

        {open ? (
          <div className="pva-multi-select__panel">
            <input
              type="search"
              className="pva-multi-select__search"
              placeholder="Buscar cliente…"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
            />

            <div className="pva-multi-select__actions">
              <button type="button" className="pva-btn pva-btn--ghost pva-btn--sm" onClick={selectVisible}>
                Marcar visíveis
              </button>
              <button
                type="button"
                className="pva-btn pva-btn--ghost pva-btn--sm"
                onClick={() => onChange([])}
              >
                Limpar seleção
              </button>
            </div>

            <ul id={listId} className="pva-check-list" role="listbox" aria-multiselectable="true">
              {filteredClients.length === 0 ? (
                <li className="pva-check-list__empty">Nenhum cliente encontrado.</li>
              ) : (
                filteredClients.map((client) => (
                  <li key={client.key}>
                    <label className="pva-check-option" title={client.name}>
                      <input
                        type="checkbox"
                        checked={selectedKeys.includes(client.key)}
                        onChange={() => toggleClient(client.key)}
                      />
                      <span className="pva-check-option__label">{client.name}</span>
                    </label>
                  </li>
                ))
              )}
            </ul>
          </div>
        ) : null}
      </div>
    </div>
  );
}
