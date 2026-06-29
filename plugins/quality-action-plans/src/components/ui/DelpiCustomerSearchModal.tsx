import { Search, X } from "lucide-react";
import { useEffect, useId, useState } from "react";

import {
  searchDelpiCustomers,
  type DelpiCustomerLookupItem,
} from "../../api/delpiLookupApi";
import { PAC_HELP_TOOLTIPS } from "../../content/helpTooltips";
import { TableHeaderCell } from "./HelpTooltip";
import { Modal } from "./Modal";
import { TextField } from "./TextField";

const CUSTOMER_SEARCH_PAGE_SIZE = 20;
const T = PAC_HELP_TOOLTIPS.tables;

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

  const clearFilters = () => {
    setFilters({ code: "", store: "", name: "" });
    setItems([]);
    setError(null);
    setSearched(false);
  };

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

        <div className="pac-customer-search-modal__toolbar">
          <button
            type="button"
            className="pac-ghost-btn"
            disabled={loading}
            onClick={clearFilters}
          >
            <X size={16} aria-hidden="true" />
            Limpar filtros
          </button>
          <button type="submit" className="pac-primary-btn" disabled={loading}>
            <Search size={16} aria-hidden="true" />
            {loading ? "Buscando…" : "Buscar clientes"}
          </button>
        </div>

        <div className="pac-customer-search-modal__results" aria-live="polite">
          {error ? <p className="pac-customer-search-modal__error">{error}</p> : null}

          {loading ? <p className="pac-muted pac-customer-search-modal__status">Buscando clientes…</p> : null}

          {!loading && !searched && !error ? (
            <p className="pac-muted pac-customer-search-modal__status">
              Preencha os filtros e clique em Buscar clientes.
            </p>
          ) : null}

          {!loading && searched && !error && items.length === 0 ? (
            <p className="pac-muted pac-customer-search-modal__status">Nenhum cliente encontrado.</p>
          ) : null}

          {!loading && items.length > 0 ? (
            <>
              <p className="pac-customer-search-modal__results-header">
                {items.length} resultado{items.length === 1 ? "" : "s"} (máx. {CUSTOMER_SEARCH_PAGE_SIZE})
              </p>
              <div className="pac-table-wrap pac-customer-search-modal__table">
                <table className="pac-table">
                  <thead>
                    <tr>
                      <TableHeaderCell label="Código" hint={T.customerCode} />
                      <TableHeaderCell label="Loja" hint={T.customerStore} />
                      <TableHeaderCell label="Nome do cliente" hint={T.customerName} />
                      <TableHeaderCell
                        label="Ações"
                        hint={T.selectCustomer}
                        className="pac-table__actions-col"
                      />
                    </tr>
                  </thead>
                  <tbody>
                    {items.map((item) => (
                      <tr
                        key={`${item.code}-${item.store}-${item.name}`}
                        className="pac-customer-search-modal__row"
                        tabIndex={0}
                        onClick={() => handleSelect(item)}
                        onKeyDown={(event) => {
                          if (event.key === "Enter" || event.key === " ") {
                            event.preventDefault();
                            handleSelect(item);
                          }
                        }}
                      >
                        <td>{item.code}</td>
                        <td>{item.store || "—"}</td>
                        <td>{item.name || "—"}</td>
                        <td className="pac-customer-search-modal__select-cell">
                          <button
                            type="button"
                            className="pac-ghost-btn pac-customer-search-modal__select"
                            onClick={(event) => {
                              event.stopPropagation();
                              handleSelect(item);
                            }}
                          >
                            Selecionar
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          ) : null}
        </div>
      </form>
    </Modal>
  );
}
