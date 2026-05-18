import { useEffect, useState } from "react";

import type { AdminApi, AdminGroup, AdminRole } from "../../data/adminApi";

import "./NotificationRoleGroupPicker.css";

type Props = {
  adminApi: AdminApi;
  selectedRoleIds: string[];
  selectedGroupIds: string[];
  onChangeRoleIds: (ids: string[]) => void;
  onChangeGroupIds: (ids: string[]) => void;
  disabled?: boolean;
};

export function NotificationRoleGroupPicker({
  adminApi,
  selectedRoleIds,
  selectedGroupIds,
  onChangeRoleIds,
  onChangeGroupIds,
  disabled = false,
}: Props) {
  const [roles, setRoles] = useState<AdminRole[]>([]);
  const [groups, setGroups] = useState<AdminGroup[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
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
          setLoading(false);
        }
      }
    }

    void load();
    return () => {
      cancelled = true;
    };
  }, [adminApi]);

  function toggleId(ids: string[], id: string, onChange: (next: string[]) => void) {
    onChange(ids.includes(id) ? ids.filter((item) => item !== id) : [...ids, id]);
  }

  if (loading) {
    return <p className="notification-rg-picker__loading">Carregando papéis e grupos…</p>;
  }

  return (
    <div className="notification-rg-picker">
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
                    disabled={disabled}
                    checked={selectedRoleIds.includes(role.id)}
                    onChange={() => toggleId(selectedRoleIds, role.id, onChangeRoleIds)}
                  />
                  <span>{role.name}</span>
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
                    disabled={disabled}
                    checked={selectedGroupIds.includes(group.id)}
                    onChange={() => toggleId(selectedGroupIds, group.id, onChangeGroupIds)}
                  />
                  <span>{group.name}</span>
                </label>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
