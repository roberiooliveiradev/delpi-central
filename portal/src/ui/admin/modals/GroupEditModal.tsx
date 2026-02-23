// src/ui/admin/modals/GroupEditModal.tsx
import type { AdminGroup, AdminRole } from "../../../data/adminApi";
import { Modal } from "../../../components/Modal";

type Props = {
  open: boolean;
  group: AdminGroup | null;
  roles: AdminRole[];
  selectedRoleIds: string[];
  saving?: boolean;

  onClose: () => void;
  onSave: () => void;

  onChangeGroup: (patch: Partial<AdminGroup>) => void;
  onToggleRole: (roleId: string) => void;
};

export const GroupEditModal = ({
  open,
  group,
  roles,
  selectedRoleIds,
  saving = false,
  onClose,
  onSave,
  onChangeGroup,
  onToggleRole,
}: Props) => {
  if (!open || !group) return null;

  const isEdit = !!group.id;

  return (
    <Modal
      open={open}
      title={isEdit ? `Editar Grupo — ${group.name}` : "Novo Grupo"}
      onClose={onClose}
      size="lg"
      footer={
        <>
          <button onClick={onClose} disabled={saving}>
            Cancelar
          </button>
          <button onClick={onSave} disabled={saving || !group.name?.trim()}>
            Salvar
          </button>
        </>
      }
    >
      <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
        <label>
          Nome
          <input
            value={group.name}
            onChange={(e) => onChangeGroup({ name: e.target.value })}
            disabled={saving}
          />
        </label>

        <label>
          Descrição
          <textarea
            value={group.description || ""}
            onChange={(e) => onChangeGroup({ description: e.target.value })}
            disabled={saving}
          />
        </label>

        <hr />

        <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
          {roles.map((r) => (
            <label key={r.id} className="checkbox-item">
              <input
                type="checkbox"
                checked={selectedRoleIds.includes(r.id)}
                onChange={() => onToggleRole(r.id)}
                disabled={saving}
              />
              {r.name}
            </label>
          ))}
        </div>
      </div>
    </Modal>
  );
};