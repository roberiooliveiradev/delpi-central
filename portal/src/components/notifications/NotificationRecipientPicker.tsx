// src/components/notifications/NotificationRecipientPicker.tsx

import { useEffect, useMemo, useState } from "react";
import { Plus, ShieldCheck, UserRound, Users, X } from "lucide-react";

import type { AdminApi, AdminUser } from "../../data/adminApi";
import { AdminEntityList } from "../admin/AdminEntityList";
import { Modal } from "../Modal";
import { usePaginatedResource } from "../../hooks/usePaginatedResource";
import { parseRecipientsBulk } from "./notificationRecipients";

import "./NotificationRecipientPicker.css";

const PAGE_SIZE = 12;

type RecipientLabel = {
  name: string;
  email: string;
};

export type RecipientLabelMap = Record<string, RecipientLabel>;

type NotificationRecipientPickerProps = {
  adminApi: AdminApi;
  selectedUserIds: string[];
  extraEmails: string[];
  onChangeSelectedUserIds: (ids: string[]) => void;
  onChangeExtraEmails: (emails: string[]) => void;
  disabled?: boolean;
  previewUserId?: string | null;
  onPreviewUserIdChange?: (id: string | null) => void;
  onRecipientLabelsChange?: (labels: RecipientLabelMap) => void;
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
  previewUserId = null,
  onPreviewUserIdChange,
  onRecipientLabelsChange,
}: NotificationRecipientPickerProps) {
  const [modalOpen, setModalOpen] = useState(false);
  const [draftUserIds, setDraftUserIds] = useState<string[]>([]);
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
        q: modalOpen ? search : "",
        sort: "name",
        direction: "asc",
      }),
    PAGE_SIZE,
    [search, modalOpen],
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

  const openModal = () => {
    if (disabled) {
      return;
    }
    setDraftUserIds([...selectedUserIds]);
    setSearch("");
    usersResource.setPage(1);
    setModalOpen(true);
  };

  const closeModal = () => {
    setModalOpen(false);
    setSearch("");
  };

  const confirmModal = () => {
    for (const userId of draftUserIds) {
      const user = usersById.get(userId);
      if (user) {
        rememberUser(user);
      }
    }
    onChangeSelectedUserIds([...draftUserIds]);
    closeModal();
  };

  const toggleDraftUser = (userId: string) => {
    const user = usersById.get(userId);

    if (draftUserIds.includes(userId)) {
      setDraftUserIds(draftUserIds.filter((id) => id !== userId));
      return;
    }

    if (user) {
      rememberUser(user);
    }

    setDraftUserIds([...draftUserIds, userId]);
  };

  const selectVisibleDraftUsers = () => {
    const next = new Set(draftUserIds);

    for (const user of users) {
      if (user.active === false) {
        continue;
      }
      rememberUser(user);
      next.add(user.id);
    }

    setDraftUserIds(Array.from(next));
  };

  const clearDraftUsers = () => {
    setDraftUserIds([]);
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
  const userCountLabel =
    selectedUserIds.length === 0
      ? "Nenhum usuário selecionado"
      : selectedUserIds.length === 1
        ? "1 usuário selecionado"
        : `${selectedUserIds.length} usuários selecionados`;

  useEffect(() => {
    onRecipientLabelsChange?.(recipientLabels);
  }, [recipientLabels, onRecipientLabelsChange]);

  useEffect(() => {
    if (previewUserId && !selectedUserIds.includes(previewUserId)) {
      onPreviewUserIdChange?.(null);
    }
  }, [previewUserId, selectedUserIds, onPreviewUserIdChange]);

  const userList = (
    <AdminEntityList<AdminUser>
      className="notification-recipients__modal-list"
      title=""
      description=""
      listTitle="Usuários ativos"
      listSubtitle={`Página ${currentPage} de ${totalPages}`}
      items={users.filter((user) => user.active !== false)}
      loading={usersResource.loading}
      emptyText="Nenhum usuário ativo encontrado."
      getId={(user) => user.id}
      selectedIds={draftUserIds}
      selectionLabel="selecionados no modal"
      onToggleSelected={toggleDraftUser}
      onSelectVisible={selectVisibleDraftUsers}
      onClearSelection={clearDraftUsers}
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
  );

  return (
    <div className="notification-recipients">
      <div className="notification-recipients__picker-bar">
        <div className="notification-recipients__picker-summary">
          <span className="notification-recipients__picker-icon" aria-hidden="true">
            <Users size={18} />
          </span>
          <div>
            <strong>{userCountLabel}</strong>
            {extraEmails.length > 0 ? (
              <span className="notification-recipients__picker-extra">
                + {extraEmails.length} e-mail(s) avulso(s)
              </span>
            ) : null}
          </div>
        </div>
        <div className="notification-recipients__picker-actions">
          <button
            type="button"
            className="notification-recipients__open-modal"
            onClick={openModal}
            disabled={disabled}
          >
            <Users size={16} aria-hidden="true" />
            Selecionar usuários
          </button>
          {totalRecipients > 0 ? (
            <button
              type="button"
              className="notification-recipients__clear"
              onClick={clearSelection}
              disabled={disabled}
            >
              Limpar todos
            </button>
          ) : null}
        </div>
      </div>

      <div className="notification-recipients__quick">
        <label className="notification-recipients__quick-label">
          <span>Adicionar por e-mail ou ID (rápido)</span>
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
              rows={2}
              placeholder={
                "usuario@empresa.com, outro@empresa.com\n550e8400-e29b-41d4-a716-446655440000"
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
          Separe vários itens por vírgula ou quebra de linha. E-mails de usuários cadastrados viram
          seleção por ID automaticamente.
        </p>
        {quickSuccess ? <p className="notification-recipients__success">{quickSuccess}</p> : null}
        {quickError ? <p className="notification-recipients__error">{quickError}</p> : null}
      </div>

      {totalRecipients > 0 ? (
        <div className="notification-recipients__chips">
          <div className="notification-recipients__chips-header">
            <strong>{totalRecipients} destinatário(s) no total</strong>
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

          {selectedUserIds.length > 0 && onPreviewUserIdChange ? (
            <label className="notification-recipients__preview-select">
              <span>Pré-visualizar como</span>
              <select
                value={previewUserId ?? ""}
                disabled={disabled}
                onChange={(event) =>
                  onPreviewUserIdChange(event.target.value ? event.target.value : null)
                }
              >
                <option value="">Eu (remetente)</option>
                {selectedUserIds.map((userId) => {
                  const label = recipientLabels[userId];
                  return (
                    <option key={userId} value={userId}>
                      {label?.name ?? "Usuário"} — {label?.email ?? userId}
                    </option>
                  );
                })}
              </select>
            </label>
          ) : null}
        </div>
      ) : null}

      <Modal
        open={modalOpen}
        title="Selecionar usuários"
        size="xl"
        onClose={closeModal}
        footer={
          <div className="notification-recipients__modal-footer">
            <span className="notification-recipients__modal-count">
              {draftUserIds.length === 0
                ? "Nenhum usuário marcado"
                : draftUserIds.length === 1
                  ? "1 usuário marcado"
                  : `${draftUserIds.length} usuários marcados`}
            </span>
            <div className="notification-recipients__modal-footer-actions">
              <button type="button" className="notification-recipients__modal-btn" onClick={closeModal}>
                Cancelar
              </button>
              <button
                type="button"
                className="notification-recipients__modal-btn notification-recipients__modal-btn--primary"
                onClick={confirmModal}
              >
                Confirmar seleção
              </button>
            </div>
          </div>
        }
      >
        <p className="notification-recipients__modal-intro">
          Marque um ou mais usuários ativos. Use a busca para filtrar por nome ou e-mail. As
          alterações só são aplicadas ao confirmar.
        </p>
        {userList}
      </Modal>
    </div>
  );
}
