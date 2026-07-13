// src/ui/admin/modals/RoleEditModal.tsx

import { useEffect, useState } from "react";
import type {
  AdminPermission,
  AdminRole,
  AdminUser,
} from "../../../data/adminApi";
import { Modal } from "../../../components/Modal";
import { AppGroupedPermissionPicker } from "../../../components/AppGroupedPermissionPicker";
import { RelationshipPicker } from "../../../components/RelationshipPicker";
import type { AppInfoByModule } from "../tabs/RolesTab";
import "./RoleEditModal.css";

type RoleModalTab = "details" | "users" | "permissions";

type Props = {
  open: boolean;
  role: AdminRole | null;

  users: AdminUser[];
  selectedUserIds: string[];

  allPerms: AdminPermission[];
  selectedPermIds: string[];
  appInfoByModule?: AppInfoByModule;

  saving?: boolean;

  onClose: () => void;
  onSave: () => void;

  onChangeRole: (patch: Partial<AdminRole>) => void;
  onChangeUserIds: (nextIds: string[]) => void;
  onChangePermissionIds: (nextIds: string[]) => void;
};

export const RoleEditModal = ({
  open,
  role,
  users,
  selectedUserIds,
  allPerms,
  selectedPermIds,
  appInfoByModule = {},
  saving = false,
  onClose,
  onSave,
  onChangeRole,
  onChangeUserIds,
  onChangePermissionIds,
}: Props) => {
  const [activeTab, setActiveTab] = useState<RoleModalTab>("details");

  useEffect(() => {
    if (open) {
      setActiveTab("details");
    }
  }, [open, role?.id]);

  if (!open || !role) return null;

  const isEdit = !!role.id;

  return (
    <Modal
      open={open}
      title={isEdit ? `Editar Papel — ${role.name}` : "Novo Papel"}
      onClose={onClose}
      size="xl"
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
      <div className="role-edit-body">
        <div className="tabs">
          <button
            type="button"
            className={activeTab === "details" ? "active" : ""}
            onClick={() => setActiveTab("details")}
          >
            Dados
          </button>

          <button
            type="button"
            className={activeTab === "users" ? "active" : ""}
            onClick={() => setActiveTab("users")}
          >
            Usuários diretos
          </button>

          <button
            type="button"
            className={activeTab === "permissions" ? "active" : ""}
            onClick={() => setActiveTab("permissions")}
          >
            Permissões
          </button>
        </div>

        {activeTab === "details" && (
          <>
            <label className="portal-form-label">
              Nome
              <input
                value={role.name}
                onChange={(event) =>
                  onChangeRole({ name: event.target.value })
                }
                disabled={saving}
              />
            </label>

            <label className="portal-form-label">
              Descrição
              <textarea
                value={role.description || ""}
                onChange={(event) =>
                  onChangeRole({ description: event.target.value })
                }
                disabled={saving}
              />
            </label>

            <div className="alert">
              Usuários diretos recebem este papel pela relação usuário ↔ papel.
              Usuários também podem receber permissões indiretamente por grupos.
            </div>
          </>
        )}

        {activeTab === "users" && (
          <RelationshipPicker<AdminUser>
            title="Usuários diretos do Papel"
            availableTitle="Usuários disponíveis"
            selectedTitle="Usuários com este papel"
            searchPlaceholder="Buscar por nome ou email..."
            emptyAvailableText="Nenhum usuário disponível para adicionar."
            emptySelectedText="Nenhum usuário direto vinculado a este papel."
            items={users}
            selectedIds={selectedUserIds}
            disabled={saving}
            getId={(user) => user.id}
            getTitle={(user) => user.name || user.email}
            getSubtitle={(user) => user.email}
            getMeta={(user) => [
              {
                label: user.is_superadmin ? "Superadmin" : "Usuário",
                tone: user.is_superadmin ? "warning" : "default",
              },
              {
                label: user.active === false ? "Inativo" : "Ativo",
                tone: user.active === false ? "danger" : "success",
              },
            ]}
            onChange={onChangeUserIds}
          />
        )}

        {activeTab === "permissions" && (
          <AppGroupedPermissionPicker
            title="Permissões do Papel"
            availableTitle="Apps disponíveis"
            selectedTitle="Apps vinculados ao papel"
            searchPlaceholder="Buscar por código, nome, app ou módulo..."
            emptyAvailableText="Nenhuma permissão disponível para adicionar."
            emptySelectedText="Nenhuma permissão vinculada a este papel."
            permissions={allPerms}
            selectedIds={selectedPermIds}
            appInfoByModule={appInfoByModule}
            disabled={saving}
            onChange={onChangePermissionIds}
          />
        )}
      </div>
    </Modal>
  );
};