import { useEffect, useState } from "react";
import { Search, X } from "lucide-react";
import { NativeTextControl } from "@delpi/plugin-ui/index";

import { searchDirectoryUsers, type DirectoryUser } from "../api/directoryApi";
import type { AuditAuditorSelection } from "../types/auditAuditor";
import { formatPersonName } from "../utils/formatPersonName";

type Props = {
  value: AuditAuditorSelection[];
  onChange: (auditors: AuditAuditorSelection[]) => void;
  disabled?: boolean;
};

export function AuditAuditorPicker({ value, onChange, disabled = false }: Props) {
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

  const selectedIds = new Set(value.map((item) => item.user_id));

  const addAuditor = (user: DirectoryUser) => {
    if (selectedIds.has(user.id)) return;
    onChange([
      ...value,
      {
        user_id: user.id,
        display_name: formatPersonName(user.name.trim() || user.email) || user.email,
      },
    ]);
    setQuery("");
    setResults([]);
  };

  const removeAuditor = (userId: string) => {
    onChange(value.filter((item) => item.user_id !== userId));
  };

  return (
    <div className="a5s-auditor-picker">
      <div className="a5s-auditor-picker__head">
        <span className="a5s-auditor-picker__label">Auditores</span>
        <p className="a5s-auditor-picker__hint">
          Selecione quem participará da avaliação — não é necessário estar online no momento.
        </p>
      </div>

      {value.length > 0 ? (
        <ul className="a5s-auditor-picker__selected">
          {value.map((auditor) => (
            <li key={auditor.user_id}>
              <span>{formatPersonName(auditor.display_name) || auditor.display_name}</span>
              <button
                type="button"
                className="a5s-auditor-picker__remove"
                disabled={disabled}
                aria-label={`Remover ${auditor.display_name}`}
                onClick={() => removeAuditor(auditor.user_id)}
              >
                <X size={14} aria-hidden />
              </button>
            </li>
          ))}
        </ul>
      ) : (
        <p className="a5s-auditor-picker__empty">Nenhum auditor selecionado.</p>
      )}

      <div className="a5s-auditor-picker__search">
        <Search size={16} aria-hidden />
        <NativeTextControl
          type="search"
          value={query}
          disabled={disabled}
          placeholder="Buscar por nome ou e-mail…"
          aria-label="Buscar auditor por nome ou e-mail"
          onChange={setQuery}
        />
      </div>

      {searching ? <p className="a5s-auditor-picker__status">Buscando…</p> : null}

      {!searching && query.trim().length >= 2 && results.length === 0 ? (
        <p className="a5s-auditor-picker__status">Nenhum usuário encontrado.</p>
      ) : null}

      {results.length > 0 ? (
        <ul className="a5s-auditor-picker__results">
          {results.map((user) => {
            const alreadySelected = selectedIds.has(user.id);
            return (
              <li key={user.id}>
                <button
                  type="button"
                  disabled={disabled || alreadySelected}
                  onClick={() => addAuditor(user)}
                >
                  <strong>{formatPersonName(user.name) || user.name}</strong>
                  <small>{user.email}</small>
                  {alreadySelected ? <span className="a5s-auditor-picker__tag">Adicionado</span> : null}
                </button>
              </li>
            );
          })}
        </ul>
      ) : null}
    </div>
  );
}
