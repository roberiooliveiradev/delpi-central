import { useCallback, useEffect, useState } from "react";
import { UserRound, X } from "lucide-react";

import type { AdminApi, AdminGroup, AdminRole } from "../../data/adminApi";
import type { CoreApi } from "../../data/coreApi";

import "./NotificationRoleGroupPicker.css";

export type ResolvedRecipient = {
  id: string;
  name: string;
  email: string;
};

type Props = {
  adminApi: AdminApi;
  coreApi: CoreApi;
  selectedRoleIds: string[];
  selectedGroupIds: string[];
  excludedUserIds: string[];
  onChangeRoleIds: (ids: string[]) => void;
  onChangeGroupIds: (ids: string[]) => void;
  onChangeExcludedUserIds: (ids: string[]) => void;
  disabled?: boolean;
};

export function NotificationRoleGroupPicker({
  adminApi,
  coreApi,
  selectedRoleIds,
  selectedGroupIds,
  excludedUserIds,
  onChangeRoleIds,
  onChangeGroupIds,
  onChangeExcludedUserIds,
  disabled = false,
}: Props) {
  const [roles, setRoles] = useState<AdminRole[]>([]);
  const [groups, setGroups] = useState<AdminGroup[]>([]);
  const [resolvedUsers, setResolvedUsers] = useState<ResolvedRecipient[]>([]);
  const [excludedUsers, setExcludedUsers] = useState<Record<string, ResolvedRecipient>>({});
  const [loadingCatalog, setLoadingCatalog] = useState(true);
  const [loadingUsers, setLoadingUsers] = useState(false);
  const [resolveError, setResolveError] = useState<string | null>(null);

  const hasRoleOrGroup = selectedRoleIds.length > 0 || selectedGroupIds.length > 0;

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoadingCatalog(true);
      try {
        const [rolesRes, groupsRes] = await Promise.all([
          adminApi.listRoles({ page: 1, pageSize: 500 }),
          adminApi.listGroups({ page: 1, pageSize: 500 }),
        ]);
        if (!cancelled) {
          setRoles(rolesRes.data ?? []);
          setGroups(groupsRes.data ?? []);
        }
      } finally {
        if (!cancelled) {
          setLoadingCatalog(false);
        }
      }
    }

    void load();
    return () => {
      cancelled = true;
    };
  }, [adminApi]);

  const clearExclusionsIfEmpty = useCallback(
    (nextRoleIds: string[], nextGroupIds: string[]) => {
      if (nextRoleIds.length === 0 && nextGroupIds.length === 0) {
        onChangeExcludedUserIds([]);
        setExcludedUsers({});
      }
    },
    [onChangeExcludedUserIds],
  );

  const loadResolvedUsers = useCallback(async () => {
    if (!hasRoleOrGroup) {
      setResolvedUsers([]);
      setResolveError(null);
      return;
    }

    setLoadingUsers(true);
    setResolveError(null);

    try {
      const response = await coreApi.resolveNotificationRecipients({
        roleIds: selectedRoleIds,
        groupIds: selectedGroupIds,
        excludedUserIds,
        broadcast: false,
        userIds: [],
        emails: [],
        message: "preview",
      });
      setResolvedUsers(response.users);
    } catch (err) {
      setResolvedUsers([]);
      setResolveError(err instanceof Error ? err.message : "Falha ao listar destinatários");
    } finally {
      setLoadingUsers(false);
    }
  }, [coreApi, excludedUserIds, hasRoleOrGroup, selectedGroupIds, selectedRoleIds]);

  useEffect(() => {
    void loadResolvedUsers();
  }, [loadResolvedUsers]);

  useEffect(() => {
    setExcludedUsers((current) => {
      const next: Record<string, ResolvedRecipient> = {};
      for (const userId of excludedUserIds) {
        if (current[userId]) {
          next[userId] = current[userId];
        }
      }
      return next;
    });
  }, [excludedUserIds]);

  function toggleRole(roleId: string) {
    const next = selectedRoleIds.includes(roleId)
      ? selectedRoleIds.filter((id) => id !== roleId)
      : [...selectedRoleIds, roleId];
    onChangeRoleIds(next);
    clearExclusionsIfEmpty(next, selectedGroupIds);
  }

  function toggleGroup(groupId: string) {
    const next = selectedGroupIds.includes(groupId)
      ? selectedGroupIds.filter((id) => id !== groupId)
      : [...selectedGroupIds, groupId];
    onChangeGroupIds(next);
    clearExclusionsIfEmpty(selectedRoleIds, next);
  }

  function excludeUser(user: ResolvedRecipient) {
    if (excludedUserIds.includes(user.id)) {
      return;
    }
    setExcludedUsers((current) => ({ ...current, [user.id]: user }));
    onChangeExcludedUserIds([...excludedUserIds, user.id]);
  }

  function restoreUser(userId: string) {
    onChangeExcludedUserIds(excludedUserIds.filter((id) => id !== userId));
    setExcludedUsers((current) => {
      const next = { ...current };
      delete next[userId];
      return next;
    });
  }

  const excludedList = excludedUserIds
    .map((id) => excludedUsers[id])
    .filter((user): user is ResolvedRecipient => Boolean(user));

  if (loadingCatalog) {
    return <p className="notification-rg-picker__loading">Carregando papéis e grupos…</p>;
  }

  return (
    <div className="notification-rg-picker">
      <div className="notification-rg-picker__columns">
        <div className="notification-rg-picker__block">
          <h4>Papéis (roles)</h4>
          <p className="notification-rg-picker__hint">
            Inclui usuários com o papel direto ou herdado via grupo.
          </p>
          {roles.length === 0 ? (
            <p className="notification-rg-picker__empty">Nenhum papel cadastrado.</p>
          ) : (
            <ul className="notification-rg-picker__list">
              {roles.map((role) => (
                <li key={role.id}>
                  <label className="notification-rg-picker__item">
                    <input
                      type="checkbox"
                      className="notification-rg-picker__checkbox"
                      disabled={disabled}
                      checked={selectedRoleIds.includes(role.id)}
                      onChange={() => toggleRole(role.id)}
                    />
                    <span className="notification-rg-picker__label-text">{role.name}</span>
                  </label>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="notification-rg-picker__block">
          <h4>Grupos</h4>
          <p className="notification-rg-picker__hint">Inclui todos os membros do grupo.</p>
          {groups.length === 0 ? (
            <p className="notification-rg-picker__empty">Nenhum grupo cadastrado.</p>
          ) : (
            <ul className="notification-rg-picker__list">
              {groups.map((group) => (
                <li key={group.id}>
                  <label className="notification-rg-picker__item">
                    <input
                      type="checkbox"
                      className="notification-rg-picker__checkbox"
                      disabled={disabled}
                      checked={selectedGroupIds.includes(group.id)}
                      onChange={() => toggleGroup(group.id)}
                    />
                    <span className="notification-rg-picker__label-text">{group.name}</span>
                  </label>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>

      {hasRoleOrGroup ? (
        <section className="notification-rg-picker__recipients" aria-live="polite">
          <header className="notification-rg-picker__recipients-head">
            <h4>Usuários que receberão o envio</h4>
            <span className="notification-rg-picker__recipients-count">
              {loadingUsers
                ? "Calculando…"
                : resolvedUsers.length === 1
                  ? "1 usuário"
                  : `${resolvedUsers.length} usuários`}
            </span>
          </header>
          <p className="notification-rg-picker__hint">
            Remova quem não deve receber esta notificação. Usuários removidos não serão
            notificados, mesmo pertencendo ao papel ou grupo selecionado.
          </p>

          {resolveError ? (
            <p className="notification-rg-picker__error">{resolveError}</p>
          ) : null}

          {loadingUsers ? (
            <p className="notification-rg-picker__loading">Carregando destinatários…</p>
          ) : resolvedUsers.length === 0 ? (
            <p className="notification-rg-picker__empty">
              Nenhum usuário ativo encontrado para os papéis/grupos selecionados.
            </p>
          ) : (
            <ul className="notification-rg-picker__user-list">
              {resolvedUsers.map((user) => (
                <li key={user.id} className="notification-rg-picker__user-row">
                  <span className="notification-rg-picker__user-icon" aria-hidden="true">
                    <UserRound size={16} />
                  </span>
                  <span className="notification-rg-picker__user-text">
                    <strong>{user.name || "Usuário"}</strong>
                    <small>{user.email}</small>
                  </span>
                  <button
                    type="button"
                    className="notification-rg-picker__user-remove"
                    disabled={disabled}
                    onClick={() => excludeUser(user)}
                    aria-label={`Remover ${user.name || user.email} do envio`}
                  >
                    <X size={14} />
                    Remover
                  </button>
                </li>
              ))}
            </ul>
          )}

          {excludedList.length > 0 ? (
            <div className="notification-rg-picker__excluded">
              <p className="notification-rg-picker__excluded-title">
                Removidos deste envio ({excludedList.length})
              </p>
              <ul className="notification-rg-picker__excluded-list">
                {excludedList.map((user) => (
                  <li key={user.id}>
                    <span>
                      {user.name || "Usuário"}
                      <small>{user.email}</small>
                    </span>
                    <button
                      type="button"
                      disabled={disabled}
                      onClick={() => restoreUser(user.id)}
                    >
                      Incluir novamente
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
        </section>
      ) : null}
    </div>
  );
}
