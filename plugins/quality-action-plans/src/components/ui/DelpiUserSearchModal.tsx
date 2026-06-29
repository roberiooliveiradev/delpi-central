import { Search, X } from "lucide-react";
import { type FormEvent, useEffect, useId, useState } from "react";

import { searchDirectoryUsers, type DirectoryUser } from "../../api/directoryApi";
import { PAC_HELP_TOOLTIPS } from "../../content/helpTooltips";
import { formatPersonName } from "../../utils/formatPersonName";
import { TableHeaderCell } from "./HelpTooltip";
import { Modal } from "./Modal";
import { TextField } from "./TextField";

const USER_SEARCH_PAGE_SIZE = 20;
const T = PAC_HELP_TOOLTIPS.tables;

function filterExcludedUsers(
  users: DirectoryUser[],
  excludedUserIds: string[] | undefined,
): DirectoryUser[] {
  if (!excludedUserIds?.length) {
    return users;
  }
  const excluded = new Set(excludedUserIds);
  return users.filter((user) => !excluded.has(user.id));
}

type DelpiUserSearchModalProps = {
  open: boolean;
  onClose: () => void;
  initialQuery?: string;
  /** IDs já vinculados em outros membros — não aparecem na lista. */
  excludedUserIds?: string[];
  onSelect: (user: DirectoryUser) => void;
};

export function DelpiUserSearchModal({
  open,
  onClose,
  initialQuery,
  excludedUserIds,
  onSelect,
}: DelpiUserSearchModalProps) {
  const formId = useId();
  const [query, setQuery] = useState("");
  const [items, setItems] = useState<DirectoryUser[]>([]);
  const [hiddenLinkedCount, setHiddenLinkedCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searched, setSearched] = useState(false);

  const runSearch = async (searchQuery: string, browse: boolean) => {
    setLoading(true);
    setError(null);
    setSearched(true);

    try {
      const results = await searchDirectoryUsers(searchQuery, {
        limit: USER_SEARCH_PAGE_SIZE,
        browse,
      });
      const visible = filterExcludedUsers(results, excludedUserIds);
      setHiddenLinkedCount(results.length - visible.length);
      setItems(visible);
    } catch (searchError: unknown) {
      setItems([]);
      setError(searchError instanceof Error ? searchError.message : "Erro ao buscar usuários.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!open) return;
    const initial = initialQuery?.trim() ?? "";
    setQuery(initial);
    setItems([]);
    setHiddenLinkedCount(0);
    setError(null);
    setSearched(false);
    void runSearch(initial, !initial);
  }, [excludedUserIds, initialQuery, open]);

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    const normalized = query.trim();
    void runSearch(normalized, !normalized);
  };

  const clearFilters = () => {
    setQuery("");
    setItems([]);
    setError(null);
    setSearched(false);
    void runSearch("", true);
  };

  const handleSelect = (user: DirectoryUser) => {
    onSelect(user);
    onClose();
  };

  return (
    <Modal
      open={open}
      title="Pesquisar usuário na Delpi"
      onClose={onClose}
      className="pac-modal--customer-search"
    >
      <form id={formId} className="pac-customer-search-modal" onSubmit={handleSubmit}>
        <p className="pac-muted pac-customer-search-modal__hint">
          Usuários com acesso ao PAC. Ao abrir, listamos até {USER_SEARCH_PAGE_SIZE}; refine por
          nome ou e-mail e clique em Buscar.
        </p>

        <div className="pac-form-grid pac-customer-search-modal__filters">
          <TextField
            id={`${formId}-query`}
            label="Nome ou e-mail"
            value={query}
            onChange={setQuery}
            placeholder="Ex.: Robério ou engenharia@"
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
            Limpar e listar todos
          </button>
          <button type="submit" className="pac-primary-btn" disabled={loading}>
            <Search size={16} aria-hidden="true" />
            {loading ? "Buscando…" : "Buscar usuários"}
          </button>
        </div>

        <div className="pac-customer-search-modal__results" aria-live="polite">
          {error ? <p className="pac-customer-search-modal__error">{error}</p> : null}

          {loading ? <p className="pac-muted pac-customer-search-modal__status">Buscando usuários…</p> : null}

          {!loading && !searched && !error ? (
            <p className="pac-muted pac-customer-search-modal__status">Carregando usuários…</p>
          ) : null}

          {!loading && searched && !error && items.length === 0 ? (
            <p className="pac-muted pac-customer-search-modal__status">
              {hiddenLinkedCount > 0
                ? "Nenhum usuário disponível — os demais já estão vinculados à equipe."
                : "Nenhum usuário encontrado."}
            </p>
          ) : null}

          {!loading && items.length > 0 ? (
            <>
              <p className="pac-customer-search-modal__results-header">
                {items.length} resultado{items.length === 1 ? "" : "s"} (máx. {USER_SEARCH_PAGE_SIZE})
                {hiddenLinkedCount > 0
                  ? ` · ${hiddenLinkedCount} já vinculado${hiddenLinkedCount === 1 ? "" : "s"} oculto${hiddenLinkedCount === 1 ? "" : "s"}`
                  : ""}
              </p>
              <div className="pac-table-wrap pac-customer-search-modal__table">
                <table className="pac-table">
                  <thead>
                    <tr>
                      <TableHeaderCell label="Nome" hint={T.directoryUserName} />
                      <TableHeaderCell label="E-mail" hint={T.directoryUserEmail} />
                      <TableHeaderCell
                        label="Ações"
                        hint={T.selectDirectoryUser}
                        className="pac-table__actions-col"
                      />
                    </tr>
                  </thead>
                  <tbody>
                    {items.map((item) => (
                      <tr
                        key={item.id}
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
                        <td>{formatPersonName(item.name) || "—"}</td>
                        <td>{item.email || "—"}</td>
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
