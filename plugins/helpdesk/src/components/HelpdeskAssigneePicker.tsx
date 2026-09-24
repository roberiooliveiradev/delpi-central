import { X } from "lucide-react";
import { useCallback, useMemo, useState } from "react";
import {
  UserDirectoryPicker,
  createInitialsAvatar,
  type DirectoryUserOption,
} from "@delpi/plugin-ui/index";

import { listUsers } from "../api/helpdeskApi";
import { useDirectoryUserPhotoUrls } from "../presentation/useDirectoryUserPhotoUrls";

const HelpdeskAvatar = createInitialsAvatar("helpdesk");

export type HelpdeskAssigneeValue = DirectoryUserOption;

type Props = {
  label: string;
  hint?: string;
  value: HelpdeskAssigneeValue | null;
  onChange: (user: HelpdeskAssigneeValue | null) => void;
  disabled?: boolean;
  emptyLabel?: string;
  /** BFF listUsers purpose — assignee (technicians) or mention (broader catalog). */
  purpose?: "assignee" | "mention";
  placeholder?: string;
};

/**
 * User picker backed by Helpdesk BFF `/users`.
 * Default purpose=assignee (técnicos atribuíveis). Use purpose=mention for approver search.
 */
export function HelpdeskAssigneePicker({
  label,
  hint,
  value,
  onChange,
  disabled = false,
  emptyLabel = "Sem técnico",
  purpose = "assignee",
  placeholder = "Buscar por nome ou e-mail…",
}: Props) {
  const [searching, setSearching] = useState(false);
  const [resultOptions, setResultOptions] = useState<DirectoryUserOption[]>([]);

  const photoEntries = useMemo(() => {
    const rows = [...resultOptions];
    if (value) rows.push(value);
    return rows.map((user) => ({
      directoryUserId: user.directoryUserId,
      hasPhoto: user.hasPhoto,
    }));
  }, [resultOptions, value]);

  const { photoFor } = useDirectoryUserPhotoUrls(photoEntries);

  const searchUsers = useCallback(
    async (query: string, limit = 10, signal?: AbortSignal): Promise<DirectoryUserOption[]> => {
      const result = await listUsers({ q: query, limit, purpose }, signal);
      const mapped = (result.items || []).map((user) => ({
        id: String(user.id),
        name: (user.display_name || "").trim() || user.email || String(user.id),
        email: (user.email || "").trim(),
        directoryUserId: (user.directory_user_id || "").trim() || undefined,
        hasPhoto: Boolean(user.has_photo),
      }));
      setResultOptions(mapped);
      return mapped;
    },
    [purpose],
  );

  const selected = value ? [value] : [];

  const renderAvatar = (user: DirectoryUserOption) => (
    <HelpdeskAvatar
      name={user.name}
      colorKey={user.directoryUserId || user.id}
      size="sm"
      src={photoFor(user.directoryUserId)}
      previewable={false}
    />
  );

  return (
    <div className="helpdesk-assignee-picker">
      <UserDirectoryPicker
        value={selected}
        onChange={(users) => onChange(users[0] ?? null)}
        searchUsers={searchUsers}
        maxSelected={1}
        showEmail
        disabled={disabled}
        showSelectedList
        onSearchingChange={setSearching}
        renderOptionLeading={renderAvatar}
        renderSelectedChip={({ user, disabled: chipDisabled, onRemove }) => (
          <span className="delpi-ui-tag-chip helpdesk-assignee-picker__chip">
            {renderAvatar(user)}
            <span className="helpdesk-assignee-picker__chip-text">
              <strong>{user.name}</strong>
              {user.email ? <span>{user.email}</span> : null}
            </span>
            <button
              type="button"
              className="delpi-ui-tag-chip__remove"
              disabled={chipDisabled || disabled}
              aria-label={`Remover ${user.name || emptyLabel}`}
              onClick={onRemove}
            >
              <X size={14} aria-hidden />
            </button>
          </span>
        )}
        labels={{
          title: label,
          hint,
          placeholder,
          searching: "Buscando…",
          empty: "Nenhum usuário encontrado.",
        }}
      />
      {!value && !searching ? (
        <p className="helpdesk-assignee-picker__empty">{emptyLabel}</p>
      ) : null}
    </div>
  );
}
