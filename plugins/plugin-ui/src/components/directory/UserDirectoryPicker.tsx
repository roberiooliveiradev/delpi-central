import { X } from "lucide-react";
import type { ReactNode } from "react";
import { useEffect, useRef, useState } from "react";

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
  /**
   * Exibe chips dos selecionados com × (default true).
   * Passe false quando o consumidor já renderiza a própria lista (evita duplicação).
   */
  showSelectedList?: boolean;
  /**
   * Quando true (default), resultados e selecionados mostram «Nome · e-mail».
   * Passe false para listar apenas o nome de exibição.
   */
  showEmail?: boolean;
  /**
   * Limite de selecionados. Com `1`, a próxima escolha substitui a atual (single-select).
   */
  maxSelected?: number;
  /** Conteúdo à esquerda de cada sugestão (ex.: avatar). */
  renderOptionLeading?: (user: DirectoryUserOption) => ReactNode;
  /**
   * Chip selecionado customizado. Sem slot, usa tag-chip padrão com label + ×.
   */
  renderSelectedChip?: (args: {
    user: DirectoryUserOption;
    label: string;
    disabled: boolean;
    onRemove: () => void;
  }) => ReactNode;
  labels?: {
    title?: string;
    hint?: string;
    placeholder?: string;
  };
  className?: string;
};

function directoryUserLabel(user: DirectoryUserOption, showEmail: boolean): string {
  const name = (user.name || "").trim() || user.email;
  if (!showEmail || !user.email || user.email === name) {
    return name;
  }
  return `${name} · ${user.email}`;
}

function isAbortError(error: unknown): boolean {
  if (!error || typeof error !== "object") return false;
  const name = "name" in error ? String((error as { name?: unknown }).name) : "";
  return name === "AbortError";
}

export function UserDirectoryPicker({
  value,
  onChange,
  searchUsers,
  disabled = false,
  showSelectedList = true,
  showEmail = true,
  maxSelected,
  renderOptionLeading,
  renderSelectedChip,
  labels,
  className,
}: UserDirectoryPickerProps) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<DirectoryUserOption[]>([]);
  const [searching, setSearching] = useState(false);
  /** Evita re-abortar a busca quando o pai passa `searchUsers` inline a cada render. */
  const searchUsersRef = useRef(searchUsers);
  searchUsersRef.current = searchUsers;

  useEffect(() => {
    const normalized = query.trim();
    if (normalized.length < 2) {
      setResults([]);
      setSearching(false);
      return;
    }
    const controller = new AbortController();
    const timeoutId = window.setTimeout(() => {
      setSearching(true);
      void searchUsersRef
        .current(normalized, 10, controller.signal)
        .then((items) => {
          if (!controller.signal.aborted) setResults(items);
        })
        .catch((error: unknown) => {
          if (controller.signal.aborted || isAbortError(error)) return;
          setResults([]);
        })
        .finally(() => {
          if (!controller.signal.aborted) setSearching(false);
        });
    }, 280);
    return () => {
      controller.abort();
      window.clearTimeout(timeoutId);
    };
  }, [query]);

  const selectedIds = new Set(value.map((item) => item.id));
  const atLimit =
    typeof maxSelected === "number" && maxSelected > 0 && value.length >= maxSelected;

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
        placeholder={
          labels?.placeholder ||
          (showEmail ? "Buscar por nome ou e-mail" : "Buscar por nome")
        }
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
                className={
                  renderOptionLeading
                    ? "delpi-ui-user-directory-picker__option delpi-ui-user-directory-picker__option--with-leading"
                    : undefined
                }
                disabled={
                  disabled ||
                  selectedIds.has(user.id) ||
                  (atLimit && maxSelected !== 1)
                }
                onClick={() => {
                  if (selectedIds.has(user.id)) return;
                  if (maxSelected === 1) {
                    onChange([user]);
                  } else if (atLimit) {
                    return;
                  } else {
                    onChange([...value, user]);
                  }
                  setQuery("");
                  setResults([]);
                }}
              >
                {renderOptionLeading ? (
                  <span className="delpi-ui-user-directory-picker__option-leading">
                    {renderOptionLeading(user)}
                  </span>
                ) : null}
                <span className="delpi-ui-user-directory-picker__option-label">
                  {directoryUserLabel(user, showEmail)}
                </span>
              </button>
            </li>
          ))}
        </ul>
      ) : null}
      {showSelectedList && value.length > 0 ? (
        <div
          className="delpi-ui-tag-list delpi-ui-user-directory-picker__selected"
          aria-label="Usuários selecionados"
        >
          {value.map((user) => {
            const label = directoryUserLabel(user, showEmail);
            const onRemove = () =>
              onChange(value.filter((item) => item.id !== user.id));
            if (renderSelectedChip) {
              return (
                <span key={user.id}>
                  {renderSelectedChip({ user, label, disabled, onRemove })}
                </span>
              );
            }
            return (
              <span key={user.id} className="delpi-ui-tag-chip">
                <span>{label}</span>
                <button
                  type="button"
                  className="delpi-ui-tag-chip__remove"
                  disabled={disabled}
                  aria-label={`Remover ${label}`}
                  onClick={onRemove}
                >
                  <X size={14} aria-hidden="true" />
                </button>
              </span>
            );
          })}
        </div>
      ) : null}
    </div>
  );
}
