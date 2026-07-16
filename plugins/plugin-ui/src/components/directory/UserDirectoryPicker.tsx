import { useEffect, useState } from "react";

export type DirectoryUserOption = {
  id: string;
  name: string;
  email: string;
};

export type UserDirectoryPickerProps = {
  value: DirectoryUserOption[];
  onChange: (users: DirectoryUserOption[]) => void;
  searchUsers: (
    query: string,
    limit?: number,
    signal?: AbortSignal,
  ) => Promise<DirectoryUserOption[]>;
  disabled?: boolean;
  labels?: {
    title?: string;
    hint?: string;
    placeholder?: string;
  };
  className?: string;
};

export function UserDirectoryPicker({
  value,
  onChange,
  searchUsers,
  disabled = false,
  labels,
  className,
}: UserDirectoryPickerProps) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<DirectoryUserOption[]>([]);
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
      void searchUsers(normalized, 10, controller.signal)
        .then((items) => {
          if (!controller.signal.aborted) setResults(items);
        })
        .catch(() => {
          if (!controller.signal.aborted) setResults([]);
        })
        .finally(() => {
          if (!controller.signal.aborted) setSearching(false);
        });
    }, 280);
    return () => {
      controller.abort();
      window.clearTimeout(timeoutId);
    };
  }, [query, searchUsers]);

  const selectedIds = new Set(value.map((item) => item.id));

  return (
    <div className={["delpi-ui-user-directory-picker", className].filter(Boolean).join(" ")}>
      <div className="delpi-ui-user-directory-picker__head">
        <span className="delpi-ui-user-directory-picker__title">
          {labels?.title || "Usuários"}
        </span>
        {labels?.hint ? (
          <p className="delpi-ui-user-directory-picker__hint">{labels.hint}</p>
        ) : null}
      </div>
      <input
        className="delpi-ui-user-directory-picker__input"
        value={query}
        disabled={disabled}
        placeholder={labels?.placeholder || "Buscar por nome ou e-mail"}
        onChange={(e) => setQuery(e.target.value)}
      />
      {searching ? (
        <p className="delpi-ui-user-directory-picker__status">Buscando…</p>
      ) : null}
      {results.length > 0 ? (
        <ul className="delpi-ui-user-directory-picker__results">
          {results.map((user) => (
            <li key={user.id}>
              <button
                type="button"
                disabled={disabled || selectedIds.has(user.id)}
                onClick={() => {
                  if (selectedIds.has(user.id)) return;
                  onChange([...value, user]);
                  setQuery("");
                  setResults([]);
                }}
              >
                {user.name || user.email}
                {user.email ? ` · ${user.email}` : ""}
              </button>
            </li>
          ))}
        </ul>
      ) : null}
      <ul className="delpi-ui-user-directory-picker__selected">
        {value.map((user) => (
          <li key={user.id}>
            <span>{user.name || user.email}</span>
            <button
              type="button"
              disabled={disabled}
              onClick={() => onChange(value.filter((item) => item.id !== user.id))}
            >
              Remover
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
