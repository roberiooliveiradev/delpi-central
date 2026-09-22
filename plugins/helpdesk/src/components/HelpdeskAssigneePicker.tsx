import { X } from "lucide-react";
import { useCallback } from "react";
import {
  FieldLabel,
  UserDirectoryPicker,
  createInitialsAvatar,
  type DirectoryUserOption,
} from "@delpi/plugin-ui/index";

import { listUsers } from "../api/helpdeskApi";

const HelpdeskAvatar = createInitialsAvatar("helpdesk");

export type HelpdeskAssigneeValue = DirectoryUserOption;

type Props = {
  label: string;
  hint?: string;
  value: HelpdeskAssigneeValue | null;
  onChange: (user: HelpdeskAssigneeValue | null) => void;
  disabled?: boolean;
  emptyLabel?: string;
};

/**
 * Técnico atribuído — busca Minha DELPI (nome/e-mail via BFF) e grava o id GLPI.
 */
export function HelpdeskAssigneePicker({
  label,
  hint,
  value,
  onChange,
  disabled = false,
  emptyLabel = "Sem técnico",
}: Props) {
  const searchUsers = useCallback(
    async (query: string, limit = 10, signal?: AbortSignal): Promise<DirectoryUserOption[]> => {
      const result = await listUsers({ q: query, limit }, signal);
      return (result.items || []).map((user) => ({
        id: String(user.id),
        name: (user.display_name || "").trim() || user.email || String(user.id),
        email: (user.email || "").trim(),
      }));
    },
    [],
  );

  const selected = value ? [value] : [];

  return (
    <div className="helpdesk-assignee-picker">
      <FieldLabel label={label} hint={hint} />
      <UserDirectoryPicker
        value={selected}
        onChange={(users) => onChange(users[0] ?? null)}
        searchUsers={searchUsers}
        maxSelected={1}
        showEmail
        disabled={disabled}
        showSelectedList
        renderOptionLeading={(user) => (
          <HelpdeskAvatar name={user.name} colorKey={user.id} size="sm" previewable={false} />
        )}
        renderSelectedChip={({ user, disabled: chipDisabled, onRemove }) => (
          <span className="delpi-ui-tag-chip helpdesk-assignee-picker__chip">
            <HelpdeskAvatar name={user.name} colorKey={user.id} size="sm" previewable={false} />
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
          placeholder: "Buscar por nome ou e-mail na Minha DELPI…",
        }}
      />
      {!value ? <p className="helpdesk-assignee-picker__empty">{emptyLabel}</p> : null}
    </div>
  );
}
