import type { ReactNode } from "react";
import { useRef } from "react";

import {
  EntityDirectoryPicker,
  type EntityDirectoryOption,
  type EntityDirectoryPickerProps,
} from "./EntityDirectoryPicker";

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

function toEntity(
  user: DirectoryUserOption,
  showEmail: boolean,
): EntityDirectoryOption {
  const name = (user.name || "").trim() || user.email;
  return {
    id: user.id,
    label: name,
    secondary: showEmail && user.email && user.email !== name ? user.email : undefined,
  };
}

function fromEntity(
  entity: EntityDirectoryOption,
  sourceById: Map<string, DirectoryUserOption>,
): DirectoryUserOption {
  const known = sourceById.get(entity.id);
  if (known) return known;
  return {
    id: entity.id,
    name: entity.label,
    email: entity.secondary || "",
  };
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
  const sourceByIdRef = useRef(new Map<string, DirectoryUserOption>());
  for (const user of value) {
    sourceByIdRef.current.set(user.id, user);
  }

  const searchEntities: EntityDirectoryPickerProps["searchEntities"] = async (
    query,
    limit,
    signal,
  ) => {
    const users = await searchUsers(query, limit, signal);
    for (const user of users) {
      sourceByIdRef.current.set(user.id, user);
    }
    return users.map((user) => toEntity(user, showEmail));
  };

  return (
    <EntityDirectoryPicker
      value={value.map((user) => toEntity(user, showEmail))}
      onChange={(entities) => {
        onChange(entities.map((entity) => fromEntity(entity, sourceByIdRef.current)));
      }}
      searchEntities={searchEntities}
      disabled={disabled}
      showSelectedList={showSelectedList}
      maxSelected={maxSelected}
      renderOptionLeading={
        renderOptionLeading
          ? (entity) => {
              const user = fromEntity(entity, sourceByIdRef.current);
              return renderOptionLeading(user);
            }
          : undefined
      }
      renderSelectedChip={
        renderSelectedChip
          ? ({ entity, label, disabled: chipDisabled, onRemove }) =>
              renderSelectedChip({
                user: fromEntity(entity, sourceByIdRef.current),
                label,
                disabled: chipDisabled,
                onRemove,
              })
          : undefined
      }
      labels={{
        title: labels?.title || "Usuários",
        hint: labels?.hint,
        placeholder:
          labels?.placeholder ||
          (showEmail ? "Buscar por nome ou e-mail" : "Buscar por nome"),
        empty: "Nenhum usuário encontrado.",
        emptySelected: "Nenhum resultado disponível — já selecionados ou membros.",
        selectedAriaLabel: "Usuários selecionados",
      }}
      className={className}
    />
  );
}
