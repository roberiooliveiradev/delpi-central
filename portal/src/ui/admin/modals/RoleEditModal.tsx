// src/ui/admin/modals/RoleEditModal.tsx
import { useMemo, useState } from "react";
import type { AdminPermission, AdminRole } from "../../../data/adminApi";
import { Modal } from "../../../components/Modal";

type Props = {
  open: boolean;
  role: AdminRole | null;
  allPerms: AdminPermission[];
  selectedPermIds: string[];
  saving?: boolean;

  onClose: () => void;
  onSave: () => void;

  onChangeRole: (patch: Partial<AdminRole>) => void;
  onTogglePerm: (permId: string) => void;
};

export const RoleEditModal = ({
  open,
  role,
  allPerms,
  selectedPermIds,
  saving = false,
  onClose,
  onSave,
  onChangeRole,
  onTogglePerm,
}: Props) => {
  const [permSearch, setPermSearch] = useState("");

  const filteredPerms = useMemo(() => {
    const s = permSearch.trim().toLowerCase();
    if (!s) return allPerms;

    return allPerms.filter((p) => {
      return (
        (p.code || "").toLowerCase().includes(s) ||
        (p.name || "").toLowerCase().includes(s)
      );
    });
  }, [allPerms, permSearch]);

  if (!open || !role) return null;

  const isEdit = !!role.id;

  return (
    <Modal
      open={open}
      title={isEdit ? `Editar Papel — ${role.name}` : "Novo Papel"}
      onClose={onClose}
      size="lg"
      footer={
        <>
          <button onClick={onClose} disabled={saving}>
            Cancelar
          </button>
          <button onClick={onSave} disabled={saving || !role.name?.trim()}>
            Salvar
          </button>
        </>
      }
    >
      <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
        <label>
          Nome
          <input
            value={role.name}
            onChange={(e) => onChangeRole({ name: e.target.value })}
            disabled={saving}
          />
        </label>

        <label>
          Descrição
          <textarea
            value={role.description || ""}
            onChange={(e) => onChangeRole({ description: e.target.value })}
            disabled={saving}
          />
        </label>

        <hr />

        <input
          placeholder="Buscar permissões"
          value={permSearch}
          onChange={(e) => setPermSearch(e.target.value)}
          disabled={saving}
        />

        <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
          {filteredPerms.map((p) => (
            <label key={p.id} className="checkbox-item">
              <input
                type="checkbox"
                checked={selectedPermIds.includes(p.id)}
                onChange={() => onTogglePerm(p.id)}
                disabled={saving}
              />
              <span style={{ fontFamily: "monospace" }}>{p.code}</span>
              <span className="dt-muted">{p.name || ""}</span>
            </label>
          ))}
        </div>
      </div>
    </Modal>
  );
};