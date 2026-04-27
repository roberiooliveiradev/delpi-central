// src/ui/admin/modals/GroupEditModal.tsx

import { useEffect, useState } from "react";
import type { AdminGroup, AdminRole, AdminUser } from "../../../data/adminApi";
import { Modal } from "../../../components/Modal";
import { RelationshipPicker } from "../../../components/RelationshipPicker";
import "./GroupEditModal.css";

type GroupModalTab = "details" | "users" | "roles";

type Props = {
  open: boolean;
  group: AdminGroup | null;

  users: AdminUser[];
  selectedUserIds: string[];

  roles: AdminRole[];
  selectedRoleIds: string[];

  saving?: boolean;

  onClose: () => void;
  onSave: () => void;

  onChangeGroup: (patch: Partial<AdminGroup>) => void;
  onChangeUserIds: (nextIds: string[]) => void;
  onChangeRoleIds: (nextIds: string[]) => void;
};

export const GroupEditModal = ({
  open,
  group,
  users,
  selectedUserIds,
  roles,
  selectedRoleIds,
  saving = false,
  onClose,
  onSave,
  onChangeGroup,
  onChangeUserIds,
  onChangeRoleIds,
}: Props) => {
  const [activeTab, setActiveTab] = useState<GroupModalTab>("details");

  useEffect(() => {
    if (open) {
      setActiveTab("details");
    }
  }, [open, group?.id]);

  if (!open || !group) return null;

  const isEdit = !!group.id;

  return (
    <Modal
      open={open}
      title={isEdit ? `Editar Grupo — ${group.name}` : "Novo Grupo"}
      onClose={onClose}
      size="xl"
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
      <div className="group-edit-body">
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
            Usuários
          </button>

          <button
            type="button"
            className={activeTab === "roles" ? "active" : ""}
            onClick={() => setActiveTab("roles")}
          >
            Papéis
          </button>
        </div>

        {activeTab === "details" && (
          <>
            <label>
              Nome
              <input
                value={group.name}
                onChange={(event) =>
                  onChangeGroup({ name: event.target.value })
                }
                disabled={saving}
              />
            </label>

            <label>
              Descrição
              <textarea
                value={group.description || ""}
                onChange={(event) =>
                  onChangeGroup({ description: event.target.value })
                }
                disabled={saving}
              />
            </label>

            <div className="alert">
              Use as abas <strong>Usuários</strong> e <strong>Papéis</strong> para
              controlar quem pertence ao grupo e quais papéis são herdados por
              esses usuários.
            </div>
          </>
        )}

        {activeTab === "users" && (
          <RelationshipPicker<AdminUser>
            title="Usuários do Grupo"
            availableTitle="Usuários disponíveis"
            selectedTitle="Usuários vinculados ao grupo"
            searchPlaceholder="Buscar por nome ou email..."
            emptyAvailableText="Nenhum usuário disponível para adicionar."
            emptySelectedText="Nenhum usuário vinculado a este grupo."
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

        {activeTab === "roles" && (
          <RelationshipPicker<AdminRole>
            title="Papéis do Grupo"
            availableTitle="Papéis disponíveis"
            selectedTitle="Papéis vinculados ao grupo"
            searchPlaceholder="Buscar papel..."
            emptyAvailableText="Nenhum papel disponível para adicionar."
            emptySelectedText="Nenhum papel vinculado a este grupo."
            items={roles}
            selectedIds={selectedRoleIds}
            disabled={saving}
            getId={(role) => role.id}
            getTitle={(role) => role.name}
            getDescription={(role) => role.description ?? null}
            onChange={onChangeRoleIds}
          />
        )}
      </div>
    </Modal>
  );
};