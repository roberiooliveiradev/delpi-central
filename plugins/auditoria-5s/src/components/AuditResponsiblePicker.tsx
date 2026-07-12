import { useEffect, useState } from "react";
import { Search, X } from "lucide-react";

import { searchDirectoryUsers, type DirectoryUser } from "../api/directoryApi";
import { formatPersonName } from "../utils/formatPersonName";

type Props = {
  value: string;
  onChange: (responsibleName: string) => void;
  onBlur?: () => void;
  disabled?: boolean;
  label?: string;
  hint?: string;
  searchAriaLabel?: string;
};

export function AuditResponsiblePicker({
  value,
  onChange,
  onBlur,
  disabled = false,
  label = "Responsável",
  hint = "Busque e selecione um usuário do Minha Delpi — o nome não pode ser digitado manualmente.",
  searchAriaLabel = "Buscar responsável por nome ou e-mail",
}: Props) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<DirectoryUser[]>([]);
  const [searching, setSearching] = useState(false);

  useEffect(() => {
    const normalized = query.trim();
    if (normalized.length < 2) {
      setResults([]);
      return;
    }

    const controller = new AbortController();
    const timeoutId = window.setTimeout(() => {
      setSearching(true);
      void searchDirectoryUsers(normalized, 10, controller.signal)
        .then((items) => {
          if (!controller.signal.aborted) {
            setResults(items);
          }
        })
        .catch(() => {
          if (!controller.signal.aborted) {
            setResults([]);
          }
        })
        .finally(() => {
          if (!controller.signal.aborted) {
            setSearching(false);
          }
        });
    }, 280);

    return () => {
      controller.abort();
      window.clearTimeout(timeoutId);
    };
  }, [query]);

  const selectedName = value.trim();

  const selectUser = (user: DirectoryUser) => {
    const displayName = formatPersonName(user.name.trim() || user.email) || user.email;
    onChange(displayName);
    setQuery("");
    setResults([]);
    onBlur?.();
  };

  const clearSelection = () => {
    onChange("");
    onBlur?.();
  };

  return (
    <div className="a5s-auditor-picker a5s-auditor-picker--single">
      <div className="a5s-auditor-picker__head">
        <span className="a5s-auditor-picker__label">{label}</span>
        <p className="a5s-auditor-picker__hint">{hint}</p>
      </div>

      {selectedName ? (
        <ul className="a5s-auditor-picker__selected">
          <li>
            <span>{formatPersonName(selectedName) || selectedName}</span>
            <button
              type="button"
              className="a5s-auditor-picker__remove"
              disabled={disabled}
              aria-label={`Remover ${selectedName}`}
              onClick={clearSelection}
            >
              <X size={14} aria-hidden />
            </button>
          </li>
        </ul>
      ) : (
        <p className="a5s-auditor-picker__empty">Nenhum responsável selecionado.</p>
      )}

      <div className="a5s-auditor-picker__search">
        <Search size={16} aria-hidden />
        <input
          type="search"
          value={query}
          disabled={disabled}
          placeholder="Buscar por nome ou e-mail…"
          aria-label={searchAriaLabel}
          onChange={(event) => setQuery(event.target.value)}
        />
      </div>

      {searching ? <p className="a5s-auditor-picker__status">Buscando…</p> : null}

      {!searching && query.trim().length >= 2 && results.length === 0 ? (
        <p className="a5s-auditor-picker__status">Nenhum usuário encontrado.</p>
      ) : null}

      {results.length > 0 ? (
        <ul className="a5s-auditor-picker__results">
          {results.map((user) => (
            <li key={user.id}>
              <button type="button" disabled={disabled} onClick={() => selectUser(user)}>
                <strong>{formatPersonName(user.name) || user.name}</strong>
                <small>{user.email}</small>
              </button>
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}
