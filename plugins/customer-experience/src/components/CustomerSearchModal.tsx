import { useCallback, useEffect, useRef, useState } from "react";
import { Building2, Loader2, X } from "lucide-react";
import { searchCustomers } from "../api/customersApi";
import type { Customer } from "../types";

const PAGE_SIZE = 20;

export function CustomerSearchModal({
  initialName,
  onSelect,
  onClose,
}: {
  initialName?: string;
  onSelect: (customer: Customer) => void;
  onClose: () => void;
}) {
  const [name, setName] = useState(initialName ?? "");
  const [code, setCode] = useState("");
  const [store, setStore] = useState("");
  const [page, setPage] = useState(1);
  const [items, setItems] = useState<Customer[]>([]);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searched, setSearched] = useState(false);
  const nameRef = useRef<HTMLInputElement>(null);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    nameRef.current?.focus();
  }, []);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  const runSearch = useCallback(
    async (targetPage: number) => {
      abortRef.current?.abort();
      if (!name.trim() && !code.trim() && !store.trim()) {
        setItems([]);
        setTotal(0);
        setTotalPages(0);
        setPage(1);
        setSearched(false);
        setError(null);
        setLoading(false);
        return;
      }
      const controller = new AbortController();
      abortRef.current = controller;
      setLoading(true);
      setError(null);
      try {
        const result = await searchCustomers(
          { name, code, store, page: targetPage, pageSize: PAGE_SIZE },
          controller.signal,
        );
        setItems(result.items);
        setTotal(result.total);
        setTotalPages(result.totalPages);
        setPage(result.page);
        setSearched(true);
      } catch (err) {
        if (controller.signal.aborted) return;
        setItems([]);
        setTotal(0);
        setTotalPages(0);
        setError(err instanceof Error ? err.message : "Erro ao buscar clientes.");
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    },
    [name, code, store],
  );

  // Busca ao vivo: dispara automaticamente (com debounce) conforme o usuário
  // digita em qualquer filtro; abre já com os 20 primeiros do nome pré-preenchido.
  useEffect(() => {
    const timer = window.setTimeout(() => {
      void runSearch(1);
    }, 300);
    return () => window.clearTimeout(timer);
  }, [runSearch]);

  useEffect(() => () => abortRef.current?.abort(), []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    void runSearch(1);
  };

  return (
    <div className="cx-modal-backdrop" role="presentation" onClick={onClose}>
      <div
        className="cx-modal"
        role="dialog"
        aria-modal="true"
        aria-label="Pesquisar cliente no TOTVS"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="cx-modal__head">
          <h3 className="cx-modal__title">
            <Building2 size={18} /> Pesquisar cliente
            {loading && <Loader2 size={15} className="cx-spin cx-modal__title-spin" />}
          </h3>
          <button
            className="cx-icon-btn"
            type="button"
            onClick={onClose}
            aria-label="Fechar"
          >
            <X size={16} />
          </button>
        </div>

        <form className="cx-modal__filters" onSubmit={handleSubmit}>
          <label className="cx-field">
            <span>Nome da empresa</span>
            <input
              ref={nameRef}
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Ex.: WEG, Bosch..."
            />
          </label>
          <label className="cx-field cx-field--narrow">
            <span>Código</span>
            <input
              type="text"
              value={code}
              onChange={(e) => setCode(e.target.value)}
              placeholder="A1_COD"
            />
          </label>
          <label className="cx-field cx-field--narrow">
            <span>Loja</span>
            <input
              type="text"
              value={store}
              onChange={(e) => setStore(e.target.value)}
              placeholder="A1_LOJA"
            />
          </label>
        </form>

        {error && (
          <div className="cx-banner cx-banner--error" role="alert">
            {error}
          </div>
        )}

        <div className="cx-modal__results">
          {loading ? (
            <p className="cx-state">Buscando clientes...</p>
          ) : items.length === 0 ? (
            <p className="cx-state">
              {searched ? "Nenhum cliente encontrado." : "Digite o nome, código ou loja para buscar."}
            </p>
          ) : (
            <table className="cx-customer-table">
              <thead>
                <tr>
                  <th>Código</th>
                  <th>Loja</th>
                  <th>Nome</th>
                  <th aria-label="Selecionar" />
                </tr>
              </thead>
              <tbody>
                {items.map((customer) => (
                  <tr key={`${customer.code}-${customer.store}`}>
                    <td className="cx-customer-table__code">{customer.code}</td>
                    <td className="cx-customer-table__code">{customer.store}</td>
                    <td>{customer.name}</td>
                    <td className="cx-customer-table__action">
                      <button
                        className="cx-button cx-button--ghost"
                        type="button"
                        onClick={() => onSelect(customer)}
                      >
                        Selecionar
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {totalPages > 1 && (
          <div className="cx-modal__pagination">
            <button
              className="cx-button cx-button--ghost"
              type="button"
              disabled={loading || page <= 1}
              onClick={() => void runSearch(page - 1)}
            >
              Anterior
            </button>
            <span className="cx-modal__page-info">
              Página {page} de {totalPages} · {total} cliente(s)
            </span>
            <button
              className="cx-button cx-button--ghost"
              type="button"
              disabled={loading || page >= totalPages}
              onClick={() => void runSearch(page + 1)}
            >
              Próxima
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
