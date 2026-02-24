// src/ui/admin/modals/UserRbacModal.tsx
import { useEffect, useState } from "react";
import type { AdminGroup, AdminRole, AdminUser } from "../../../data/adminApi";
import { AdminApi } from "../../../data/adminApi";
import { Modal } from "../../../components/Modal";

type Props = {
  open: boolean;
  onClose: () => void;
  user: AdminUser | null;
  api: AdminApi;
  onSaved: () => void;
};

export const UserRbacModal = ({
  open,
  onClose,
  user,
  api,
  onSaved,
}: Props) => {
  const [loading, setLoading] = useState(false);

  const [roles, setRoles] = useState<AdminRole[]>([]);
  const [groups, setGroups] = useState<AdminGroup[]>([]);

  const [selectedRoleIds, setSelectedRoleIds] = useState<string[]>([]);
  const [selectedGroupIds, setSelectedGroupIds] = useState<string[]>([]);
  const [isSuperadmin, setIsSuperadmin] = useState(false);

  useEffect(() => {
    if (!open || !user) return;

    setSelectedRoleIds(user.roles.map((r) => r.id));
    setSelectedGroupIds(user.groups.map((g) => g.id));
    setIsSuperadmin(!!user.is_superadmin);

    (async () => {
      const [rolesRes, groupsRes] = await Promise.all([
        api.listRoles({ page: 1, pageSize: 999 }),
        api.listGroups({ page: 1, pageSize: 999 }),
      ]);

      setRoles(rolesRes.data ?? []);
      setGroups(groupsRes.data ?? []);
    })();
  }, [open, user, api]);

  const toggle = (arr: string[], id: string) =>
    arr.includes(id) ? arr.filter((x) => x !== id) : [...arr, id];

  if (!open || !user) return null;

  const save = async () => {
    setLoading(true);
    try {
      await api.updateUser(user.id, {
        roleIds: selectedRoleIds,
        groupIds: selectedGroupIds,
        is_superadmin: isSuperadmin,
      });

      onSaved();
      onClose();
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      open={open}
      title={`Editar RBAC — ${user.email}`}
      onClose={onClose}
      size="lg"
      footer={
        <>
          <button onClick={onClose} disabled={loading}>
            Cancelar
          </button>
          <button onClick={save} disabled={loading}>
            Salvar
          </button>
        </>
      }
    >
      <div className="superadmin-row">
        <input
          type="checkbox"
          checked={isSuperadmin}
          onChange={(e) => setIsSuperadmin(e.target.checked)}
          disabled={loading}
        />
        <span>Superadmin</span>
      </div>

      <div className="rbac-grid">
        {/* ROLES */}
        <div className="rbac-column">
          <h4>Papéis do usuário</h4>
          <div className="dt-muted">
            Papéis aplicam permissões diretamente.
          </div>

          <div className="checkbox-list">
            {roles.map((r) => (
              <label key={r.id} className="checkbox-item">
                <input
                  type="checkbox"
                  checked={selectedRoleIds.includes(r.id)}
                  onChange={() =>
                    setSelectedRoleIds((s) => toggle(s, r.id))
                  }
                  disabled={loading}
                />
                {r.name}
              </label>
            ))}
          </div>
        </div>

        {/* GROUPS */}
        <div className="rbac-column">
          <h4>Grupos do usuário</h4>
          <div className="dt-muted">
            Grupos agregam papéis (herança).
          </div>

          <div className="checkbox-list">
            {groups.map((g) => (
              <label key={g.id} className="checkbox-item">
                <input
                  type="checkbox"
                  checked={selectedGroupIds.includes(g.id)}
                  onChange={() =>
                    setSelectedGroupIds((s) => toggle(s, g.id))
                  }
                  disabled={loading}
                />
                {g.name}
              </label>
            ))}
          </div>
        </div>
      </div>
    </Modal>
  );
};