import { Search } from "lucide-react";
import { useEffect, useId, useState } from "react";

import {
  searchDelpiCustomers,
  type DelpiCustomerLookupItem,
} from "../../api/delpiLookupApi";
import { Modal } from "./Modal";
import { TextField } from "./TextField";

const CUSTOMER_SEARCH_PAGE_SIZE = 20;

export type DelpiCustomerSearchFilters = {
  code: string;
  store: string;
  name: string;
};

type DelpiCustomerSearchModalProps = {
  open: boolean;
  onClose: () => void;
  initialFilters?: Partial<DelpiCustomerSearchFilters>;
  onSelect: (customer: DelpiCustomerLookupItem) => void;
};

function normalizeFilters(filters?: Partial<DelpiCustomerSearchFilters>): DelpiCustomerSearchFilters {
  return {
    code: filters?.code?.trim() ?? "",
    store: filters?.store?.trim() ?? "",
    name: filters?.name?.trim() ?? "",
  };
}

function hasSearchCriteria(filters: DelpiCustomerSearchFilters): boolean {
  return Boolean(filters.code || filters.store || filters.name);
}

export function DelpiCustomerSearchModal({
  open,
  onClose,
  initialFilters,
  onSelect,
}: DelpiCustomerSearchModalProps) {
  const formId = useId();
  const [filters, setFilters] = useState<DelpiCustomerSearchFilters>(() =>
    normalizeFilters(initialFilters),
  );
  const [items, setItems] = useState<DelpiCustomerLookupItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searched, setSearched] = useState(false);

  useEffect(() => {
    if (!open) return;
    setFilters(normalizeFilters(initialFilters));
    setItems([]);
    setError(null);
    setSearched(false);
    setLoading(false);
  }, [initialFilters, open]);

  const runSearch = async () => {
    const normalized = normalizeFilters(filters);
    if (!hasSearchCriteria(normalized)) {
      setError("Informe pelo menos código, loja ou nome para buscar.");
      setItems([]);
      setSearched(false);
      return;
    }

    setLoading(true);
    setError(null);
    setSearched(true);

    try {
      const results = await searchDelpiCustomers({
        code: normalized.code || undefined,
        store: normalized.store || undefined,
        name: normalized.name || undefined,
        pageSize: CUSTOMER_SEARCH_PAGE_SIZE,
      });
      setItems(results);
    } catch (searchError: unknown) {
      setItems([]);
      setError(searchError instanceof Error ? searchError.message : "Erro ao buscar clientes.");
    } finally {
      setLoading(false);
    }
  };

  const handleSelect = (customer: DelpiCustomerLookupItem) => {
    onSelect(customer);
    onClose();
  };

  return (
    <Modal
      open={open}
      title="Pesquisar cliente na Delpi"
      onClose={onClose}
      className="pac-modal--customer-search"
    >
      <form
        id={formId}
        className="pac-customer-search-modal"
        onSubmit={(event) => {
          event.preventDefault();
          void runSearch();
        }}
      >
        <p className="pac-muted pac-customer-search-modal__hint">
          Informe código, loja e/ou nome. Exibimos até {CUSTOMER_SEARCH_PAGE_SIZE} resultados.
        </p>

        <div className="pac-form-grid pac-customer-search-modal__filters">
          <TextField
            id={`${formId}-code`}
            label="Código do cliente"
            value={filters.code}
            onChange={(code) => setFilters((current) => ({ ...current, code }))}
            placeholder="Ex.: 000123"
          />
          <TextField
            id={`${formId}-store`}
            label="Loja"
            value={filters.store}
            onChange={(store) => setFilters((current) => ({ ...current, store }))}
            placeholder="Ex.: 01"
          />
          <TextField
            id={`${formId}-name`}
            label="Nome do cliente"
            value={filters.name}
            onChange={(name) => setFilters((current) => ({ ...current, name }))}
            placeholder="Ex.: WEG"
          />
        </div>

        <div className="pac-customer-search-modal__actions">
          <button type="submit" className="pac-primary-btn" disabled={loading}>
            <Search size={16} aria-hidden="true" />
            {loading ? "Buscando…" : "Buscar"}
          </button>
        </div>

        {error ? <p className="pac-customer-search-modal__error">{error}</p> : null}

        {loading ? <p className="pac-muted">Buscando clientes…</p> : null}

        {!loading && searched && !error ? (
          items.length === 0 ? (
            <p className="pac-muted">Nenhum cliente encontrado.</p>
          ) : (
            <div className="pac-table-wrap pac-customer-search-modal__table">
              <table className="pac-table">
                <thead>
                  <tr>
                    <th>Código</th>
                    <th>Loja</th>
                    <th>Nome</th>
                    <th aria-label="Ações" />
                  </tr>
                </thead>
                <tbody>
                  {items.map((item) => (
                    <tr key={`${item.code}-${item.store}-${item.name}`}>
                      <td>{item.code}</td>
                      <td>{item.store || "—"}</td>
                      <td>{item.name || "—"}</td>
                      <td>
                        <button
                          type="button"
                          className="pac-ghost-btn pac-customer-search-modal__select"
                          onClick={() => handleSelect(item)}
                        >
                          Selecionar
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )
        ) : null}
      </form>
    </Modal>
  );
}
