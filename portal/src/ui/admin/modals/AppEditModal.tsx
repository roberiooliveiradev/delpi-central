// src/ui/admin/modals/AppEditModal.tsx
import { useEffect, useMemo, useState } from "react";
import { Modal } from "../../../components/Modal";
import type { AdminApp } from "../../../data/adminApi";

type Props = {
  open: boolean;
  app: AdminApp | null;
  onClose: () => void;
  onSave: (patch: { name: string; base_path: string; active: boolean }) => Promise<void>;
};

export const AppEditModal = ({ open, app, onClose, onSave }: Props) => {
  const [name, setName] = useState("");
  const [basePath, setBasePath] = useState("");
  const [active, setActive] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!open || !app) return;
    setName(app.name || "");
    setBasePath(app.base_path || "");
    setActive(!!app.active);
  }, [open, app]);

  const canSave = useMemo(() => {
    return !!name.trim() && !!basePath.trim();
  }, [name, basePath]);

  if (!open || !app) return null;

  return (
    <Modal
      open={open}
      title={`Editar Aplicação — ${app.name}`}
      onClose={onClose}
      footer={
        <>
          <button className="btn-secondary" onClick={onClose} disabled={saving}>
            Cancelar
          </button>
          <button
            className="btn-primary"
            onClick={async () => {
              setSaving(true);
              try {
                await onSave({
                  name: name.trim(),
                  base_path: basePath.trim(),
                  active,
                });
                onClose();
              } finally {
                setSaving(false);
              }
            }}
            disabled={saving || !canSave}
          >
            {saving ? "Salvando..." : "Salvar"}
          </button>
        </>
      }
    >
      <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
        <label>
          Nome
          <input value={name} onChange={(e) => setName(e.target.value)} placeholder="ex: CRM" />
        </label>

        <label>
          Base Path
          <input value={basePath} onChange={(e) => setBasePath(e.target.value)} placeholder="ex: /crm" />
          <small>Deve começar com “/”.</small>
        </label>

        <label style={{ display: "flex", flexDirection: "row", gap: 10, alignItems: "center" }}>
          <input type="checkbox" checked={active} onChange={(e) => setActive(e.target.checked)} />
          Ativo
        </label>

        <div className="hint">
          <strong>ID:</strong> <code>{app.id}</code> &nbsp;|&nbsp; <strong>Versão:</strong>{" "}
          <code>{app.version}</code>
        </div>
      </div>
    </Modal>
  );
};