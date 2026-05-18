// src/components/notifications/NotificationRecipientPicker.tsx

import { useMemo, useState } from "react";
import { Plus, ShieldCheck, UserRound, X } from "lucide-react";

import type { AdminApi, AdminUser } from "../../data/adminApi";
import { AdminEntityList } from "../admin/AdminEntityList";
import { usePaginatedResource } from "../../hooks/usePaginatedResource";
import { parseRecipientsBulk } from "./notificationRecipients";

import "./NotificationRecipientPicker.css";

const PAGE_SIZE = 12;

type RecipientLabel = {
  name: string;
  email: string;
};

type NotificationRecipientPickerProps = {
  adminApi: AdminApi;
  selectedUserIds: string[];
  extraEmails: string[];
  onChangeSelectedUserIds: (ids: string[]) => void;
  onChangeExtraEmails: (emails: string[]) => void;
  disabled?: boolean;
};

const getInitials = (user: AdminUser) => {
  const source = user.name?.trim() || user.email?.trim() || "?";

  const parts = source
    .split(" ")
    .map((part) => part.trim())
    .filter(Boolean);

  if (parts.length >= 2) {
    return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
  }

  return source.slice(0, 2).toUpperCase();
};

export function NotificationRecipientPicker({
  adminApi,
  selectedUserIds,
  extraEmails,
  onChangeSelectedUserIds,
  onChangeExtraEmails,
  disabled = false,
}: NotificationRecipientPickerProps) {
  const [search, setSearch] = useState("");
  const [quickInput, setQuickInput] = useState("");
  const [quickError, setQuickError] = useState<string | null>(null);
  const [quickSuccess, setQuickSuccess] = useState<string | null>(null);
  const [recipientLabels, setRecipientLabels] = useState<Record<string, RecipientLabel>>({});
  const [emailLabels, setEmailLabels] = useState<Record<string, string>>({});

  const usersResource = usePaginatedResource<AdminUser>(
    ({ page, pageSize }) =>
      adminApi.listUsers({
        page,
        pageSize,
        q: search,
        sort: "name",
        direction: "asc",
      }),
    PAGE_SIZE,
    [search],
  );

  const users = usersResource.data ?? [];
  const totalPages = usersResource.pagination?.total_pages ?? 1;
  const currentPage = usersResource.page;

  const usersById = useMemo(() => {
    const map = new Map<string, AdminUser>();
    for (const user of users) {
      map.set(user.id, user);
    }
    return map;
  }, [users]);

  const rememberUser = (user: AdminUser) => {
    setRecipientLabels((current) => ({
      ...current,
      [user.id]: {
        name: user.name?.trim() || user.email,
        email: user.email,
      },
    }));
  };

  const toggleUserSelection = (userId: string) => {
    if (disabled) {
      return;
    }

    const user = usersById.get(userId);

    if (selectedUserIds.includes(userId)) {
      onChangeSelectedUserIds(selectedUserIds.filter((id) => id !== userId));
      return;
    }

    if (user) {
      rememberUser(user);
    }

    onChangeSelectedUserIds([...selectedUserIds, userId]);
  };

  const selectVisibleUsers = () => {
    if (disabled) {
      return;
    }

    const next = new Set(selectedUserIds);

    for (const user of users) {
      if (user.active === false) {
        continue;
      }
      rememberUser(user);
      next.add(user.id);
    }

    onChangeSelectedUserIds(Array.from(next));
  };

  const clearSelection = () => {
    if (disabled) {
      return;
    }
    onChangeSelectedUserIds([]);
    onChangeExtraEmails([]);
    setRecipientLabels({});
    setEmailLabels({});
  };

  const removeUserId = (userId: string) => {
    onChangeSelectedUserIds(selectedUserIds.filter((id) => id !== userId));
  };

  const removeEmail = (email: string) => {
    onChangeExtraEmails(extraEmails.filter((item) => item !== email));
  };

  function handleQuickAdd() {
    if (disabled || !quickInput.trim()) {
      return;
    }

    setQuickError(null);
    setQuickSuccess(null);

    const { parsed, invalid } = parseRecipientsBulk(quickInput);

    if (parsed.length === 0) {
      const preview = invalid.slice(0, 3).join(", ");
      setQuickError(
        invalid.length > 0
          ? `Nenhum destinatário válido. Exemplos inválidos: ${preview}${invalid.length > 3 ? "…" : ""}`
          : "Informe um ou mais e-mails ou IDs (UUID), separados por vírgula ou quebra de linha.",
      );
      return;
    }

    const nextIds = new Set(selectedUserIds);
    const nextEmails = new Set(extraEmails);
    const nextRecipientLabels = { ...recipientLabels };
    const nextEmailLabels = { ...emailLabels };

    const emailToUser = new Map<string, AdminUser>();
    for (const user of users) {
      emailToUser.set(user.email.trim().toLowerCase(), user);
    }

    let added = 0;
    let duplicates = 0;

    for (const item of parsed) {
      if (item.kind === "id") {
        if (nextIds.has(item.value)) {
          duplicates += 1;
          continue;
        }

        const visible = usersById.get(item.value);
        if (visible) {
          nextRecipientLabels[item.value] = {
            name: visible.name?.trim() || visible.email,
            email: visible.email,
          };
        } else {
          nextRecipientLabels[item.value] = {
            name: "Usuário (ID)",
            email: item.value,
          };
        }

        nextIds.add(item.value);
        added += 1;
        continue;
      }

      const normalizedEmail = item.value;
      const visible = emailToUser.get(normalizedEmail);

      if (visible) {
        if (nextIds.has(visible.id)) {
          duplicates += 1;
          continue;
        }

        nextRecipientLabels[visible.id] = {
          name: visible.name?.trim() || visible.email,
          email: visible.email,
        };
        nextEmails.delete(normalizedEmail);
        nextIds.add(visible.id);
        added += 1;
        continue;
      }

      if (nextEmails.has(normalizedEmail)) {
        duplicates += 1;
        continue;
      }

      const alreadyByEmail = Array.from(nextIds).some((userId) => {
        const label = nextRecipientLabels[userId];
        return label?.email.trim().toLowerCase() === normalizedEmail;
      });

      if (alreadyByEmail) {
        duplicates += 1;
        continue;
      }

      nextEmails.add(normalizedEmail);
      nextEmailLabels[normalizedEmail] = normalizedEmail;
      added += 1;
    }

    onChangeSelectedUserIds(Array.from(nextIds));
    onChangeExtraEmails(Array.from(nextEmails));
    setRecipientLabels(nextRecipientLabels);
    setEmailLabels(nextEmailLabels);
    setQuickInput("");

    const summary: string[] = [];
    if (added > 0) {
      summary.push(`${added} destinatário(s) adicionado(s)`);
    }
    if (duplicates > 0) {
      summary.push(`${duplicates} já estava(m) na lista`);
    }
    if (invalid.length > 0) {
      summary.push(`${invalid.length} inválido(s) ignorado(s)`);
    }

    if (summary.length > 0) {
      setQuickSuccess(summary.join(" · "));
    }
  }

  const totalRecipients = selectedUserIds.length + extraEmails.length;

  return (
    <div className="notification-recipients">
      <div className="notification-recipients__quick">
        <label className="notification-recipients__quick-label">
          <span>Adicionar destinatários (um ou vários)</span>
          <div className="notification-recipients__quick-row">
            <textarea
              value={quickInput}
              onChange={(event) => {
                setQuickInput(event.target.value);
                if (quickError) {
                  setQuickError(null);
                }
                if (quickSuccess) {
                  setQuickSuccess(null);
                }
              }}
              rows={3}
              placeholder={
                "usuario@empresa.com\noutro@empresa.com\n550e8400-e29b-41d4-a716-446655440000"
              }
              disabled={disabled}
            />
            <button
              type="button"
              className="notification-recipients__quick-add"
              onClick={handleQuickAdd}
              disabled={disabled || !quickInput.trim()}
            >
              <Plus size={16} aria-hidden="true" />
              Adicionar
            </button>
          </div>
        </label>
        <p className="notification-recipients__hint">
          Vários e-mails ou IDs: separe por vírgula, ponto-e-vírgula ou quebra de linha. Também
          marque vários usuários nos cards (seleção múltipla).
        </p>
        {quickSuccess ? <p className="notification-recipients__success">{quickSuccess}</p> : null}
        {quickError ? <p className="notification-recipients__error">{quickError}</p> : null}
      </div>

      {totalRecipients > 0 ? (
        <div className="notification-recipients__chips">
          <div className="notification-recipients__chips-header">
            <strong>{totalRecipients} destinatário(s)</strong>
            <button
              type="button"
              className="notification-recipients__clear"
              onClick={clearSelection}
              disabled={disabled}
            >
              Limpar todos
            </button>
          </div>

          {selectedUserIds.map((userId) => {
            const label = recipientLabels[userId];
            return (
              <span key={userId} className="notification-recipients__chip">
                <span className="notification-recipients__chip-text">
                  {label?.name ?? "Usuário"}
                  <small>{label?.email ?? userId}</small>
                </span>
                <button
                  type="button"
                  aria-label="Remover destinatário"
                  onClick={() => removeUserId(userId)}
                  disabled={disabled}
                >
                  <X size={14} />
                </button>
              </span>
            );
          })}

          {extraEmails.map((email) => (
            <span key={email} className="notification-recipients__chip notification-recipients__chip--email">
              <span className="notification-recipients__chip-text">
                E-mail
                <small>{emailLabels[email] ?? email}</small>
              </span>
              <button
                type="button"
                aria-label="Remover e-mail"
                onClick={() => removeEmail(email)}
                disabled={disabled}
              >
                <X size={14} />
              </button>
            </span>
          ))}
        </div>
      ) : null}

      <AdminEntityList<AdminUser>
        className="notification-recipients__list"
        title="Selecionar usuários"
        description="Marque um ou mais usuários ativos. A busca filtra por nome ou e-mail."
        listTitle="Usuários"
        listSubtitle={`Página ${currentPage} de ${totalPages}`}
        items={users.filter((user) => user.active !== false)}
        loading={usersResource.loading}
        emptyText="Nenhum usuário ativo encontrado."
        getId={(user) => user.id}
        selectedIds={selectedUserIds}
        selectionLabel="destinatários"
        onToggleSelected={toggleUserSelection}
        onSelectVisible={selectVisibleUsers}
        onClearSelection={clearSelection}
        search={{
          value: search,
          placeholder: "Buscar por nome ou e-mail...",
          onChange: (value) => {
            setSearch(value);
            usersResource.setPage(1);
          },
        }}
        pagination={
          usersResource.pagination
            ? {
                page: currentPage,
                totalPages,
                onPrevious: () => usersResource.prev(),
                onNext: () => usersResource.next(),
              }
            : undefined
        }
        renderIcon={getInitials}
        renderTitle={(user) => user.name || "Usuário sem nome"}
        renderSubtitle={(user) => user.email}
        renderBadges={(user) => [
          {
            label: user.active === false ? "Inativo" : "Ativo",
            tone: user.active === false ? "danger" : "success",
          },
          ...(user.is_superadmin
            ? [
                {
                  label: (
                    <>
                      <ShieldCheck size={12} />
                      Superadmin
                    </>
                  ),
                  tone: "warning" as const,
                },
              ]
            : []),
        ]}
        renderMeta={(user) => [
          <>
            <UserRound size={13} />
            ID: {user.id}
          </>,
        ]}
      />
    </div>
  );
}
