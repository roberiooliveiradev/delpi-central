import { useEffect, useId, useState } from "react";

import { searchChatUsers } from "../../../data/api/chatApi";
import type { ChatDirectoryUser } from "../../../data/api/chatTypes";

import "./ChatUserSearchField.css";

type ChatUserSearchFieldProps = {
  value: string;
  onChange: (userId: string) => void;
  onSelectUser?: (user: ChatDirectoryUser | null) => void;
  placeholder?: string;
  disabled?: boolean;
  getAccessToken?: () => string | undefined | Promise<string | undefined>;
};

export function ChatUserSearchField({
  value,
  onChange,
  onSelectUser,
  placeholder = "Buscar por nome ou e-mail",
  disabled = false,
  getAccessToken,
}: ChatUserSearchFieldProps) {
  const listId = useId();
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<ChatDirectoryUser[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [selectedLabel, setSelectedLabel] = useState<string | null>(null);

  useEffect(() => {
    if (!value) {
      setSelectedLabel(null);
    }
  }, [value]);

  useEffect(() => {
    const normalized = query.trim();

    if (normalized.length < 2) {
      setResults([]);
      return;
    }

    let isMounted = true;
    const timeoutId = window.setTimeout(() => {
      setIsSearching(true);

      void searchChatUsers(normalized, { getAccessToken })
        .then((items) => {
          if (isMounted) {
            setResults(items);
          }
        })
        .catch(() => {
          if (isMounted) {
            setResults([]);
          }
        })
        .finally(() => {
          if (isMounted) {
            setIsSearching(false);
          }
        });
    }, 280);

    return () => {
      isMounted = false;
      window.clearTimeout(timeoutId);
    };
  }, [getAccessToken, query]);

  function handleSelect(user: ChatDirectoryUser) {
    onChange(user.id);
    onSelectUser?.(user);
    setSelectedLabel(`${user.name} · ${user.email}`);
    setQuery("");
    setResults([]);
  }

  return (
    <div className="mdc-chat-user-search">
      <label>
        <span>Usuário</span>
        <input
          value={query}
          disabled={disabled}
          list={listId}
          placeholder={selectedLabel ?? placeholder}
          onChange={(event) => {
            setQuery(event.target.value);
            setSelectedLabel(null);
            onChange("");
            onSelectUser?.(null);
          }}
        />
      </label>

      {value && selectedLabel ? (
        <p className="mdc-chat-muted mdc-chat-user-search__selected">{selectedLabel}</p>
      ) : null}

      {isSearching ? <p className="mdc-chat-muted">Buscando...</p> : null}

      {!isSearching && query.trim().length >= 2 && results.length === 0 ? (
        <p className="mdc-chat-muted">Nenhum usuário encontrado.</p>
      ) : null}

      <datalist id={listId}>
        {results.map((user) => (
          <option
            key={user.id}
            value={`${user.name} (${user.email})`}
            label={user.email}
          />
        ))}
      </datalist>

      {results.length > 0 ? (
        <ul className="mdc-chat-user-search__results" role="listbox">
          {results.map((user) => (
            <li key={user.id}>
              <button type="button" onClick={() => handleSelect(user)}>
                <strong>{user.name}</strong>
                <small>{user.email}</small>
              </button>
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}
