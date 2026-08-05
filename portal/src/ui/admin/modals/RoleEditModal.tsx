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
import {
  Alert,
  Button,
  FormField,
  Input,
  Tabs,
  Textarea,
} from "../../../ui-kit";
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
          <Button variant="secondary" onClick={onClose} disabled={saving}>
            Cancelar
          </Button>
          <Button
            variant="primary"
            onClick={onSave}
            loading={saving}
            disabled={!role.name?.trim()}
          >
            Salvar
          </Button>
        </>
      }
    >
      <div className="role-edit-body">
        <Tabs
          value={activeTab}
          onChange={(id) => setActiveTab(id as RoleModalTab)}
          items={[
            { id: "details", label: "Dados" },
            { id: "users", label: "Usuários diretos" },
            { id: "permissions", label: "Permissões" },
          ]}
        />

        {activeTab === "details" && (
          <>
            <FormField label="Nome" htmlFor="role-edit-name" required>
              <Input
                id="role-edit-name"
                value={role.name}
                onChange={(event) => onChangeRole({ name: event.target.value })}
                disabled={saving}
              />
            </FormField>

            <FormField label="Descrição" htmlFor="role-edit-description">
              <Textarea
                id="role-edit-description"
                value={role.description || ""}
                onChange={(event) =>
                  onChangeRole({ description: event.target.value })
                }
                disabled={saving}
                rows={3}
              />
            </FormField>

            <Alert tone="info">
              Usuários diretos recebem este papel pela relação usuário ↔ papel.
              Usuários também podem receber permissões indiretamente por grupos.
            </Alert>
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