// src/ui/admin/rbac/GroupEditPage.tsx

import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import type { AdminGroup, AdminRole, AdminUser } from "../../../data/adminApi";
import { useAdminApi } from "../../../hooks/useAdminApi";
import { RelationshipPicker } from "../../../components/RelationshipPicker";
import { useAppAlert } from "../../../components/ConfirmDialogProvider";
import {
  Alert,
  Button,
  FormField,
  Input,
  PageChrome,
  Spinner,
  Textarea,
} from "../../../ui-kit";

import "./RbacEditPage.css";

type GroupPageTab = "details" | "users" | "roles";

const normalizeIds = (items: unknown[]): string[] => {
  return items
    .map((item) => {
      if (typeof item === "string") return item;

      if (
        item &&
        typeof item === "object" &&
        "id" in item &&
        typeof (item as { id?: unknown }).id === "string"
      ) {
        return (item as { id: string }).id;
      }

      return null;
    })
    .filter((id): id is string => !!id);
};

export const GroupEditPage = () => {
  const { groupId } = useParams<{ groupId: string }>();
  const navigate = useNavigate();
  const showAlert = useAppAlert();
  const api = useAdminApi();

  const isNew = !groupId || groupId === "new";

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<GroupPageTab>("details");

  const [group, setGroup] = useState<AdminGroup | null>(null);
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [selectedUserIds, setSelectedUserIds] = useState<string[]>([]);
  const [roles, setRoles] = useState<AdminRole[]>([]);
  const [selectedRoleIds, setSelectedRoleIds] = useState<string[]>([]);

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      setLoading(true);
      setError(null);
      setActiveTab("details");

      try {
        if (isNew) {
          const [rolesRes, usersRes] = await Promise.all([
            api.listRoles({ page: 1, pageSize: 999 }),
            api.listUsers({ page: 1, pageSize: 999 }),
          ]);

          if (cancelled) return;

          setRoles(rolesRes.data ?? []);
          setUsers(usersRes.data ?? []);
          setSelectedRoleIds([]);
          setSelectedUserIds([]);
          setGroup({
            id: "",
            name: "",
            description: "",
          });
          return;
        }

        const [groupsRes, rolesRes, groupRoles, usersRes, groupUsers] =
          await Promise.all([
            api.listGroups({ page: 1, pageSize: 999 }),
            api.listRoles({ page: 1, pageSize: 999 }),
            api.getGroupRoles(groupId),
            api.listUsers({ page: 1, pageSize: 999 }),
            api.getGroupUsers(groupId),
          ]);

        if (cancelled) return;

        const found = (groupsRes.data ?? []).find((item) => item.id === groupId);
        if (!found) {
          setError("Grupo não encontrado.");
          setGroup(null);
          return;
        }

        setGroup({ ...found });
        setRoles(rolesRes.data ?? []);
        setSelectedRoleIds(normalizeIds(groupRoles.data ?? []));
        setUsers(usersRes.data ?? []);
        setSelectedUserIds(normalizeIds(groupUsers.data ?? []));
      } catch (e: unknown) {
        if (!cancelled) {
          setError(
            e instanceof Error
              ? e.message
              : "Não foi possível carregar o grupo."
          );
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    void load();

    return () => {
      cancelled = true;
    };
  }, [api, groupId, isNew]);

  const goBack = () => navigate("/admin?tab=groups");

  const syncGroupUsers = async (targetGroupId: string) => {
    const current = await api.getGroupUsers(targetGroupId);
    const currentIds = normalizeIds(current.data ?? []);
    const nextIds = normalizeIds(selectedUserIds);

    const toAdd = nextIds.filter((id) => !currentIds.includes(id));
    const toRemove = currentIds.filter((id) => !nextIds.includes(id));

    await Promise.all([
      ...toAdd.map((userId) => api.addUserToGroup(targetGroupId, userId)),
      ...toRemove.map((userId) =>
        api.removeUserFromGroup(targetGroupId, userId)
      ),
    ]);
  };

  const save = async () => {
    if (!group?.name?.trim()) return;

    setSaving(true);

    try {
      let targetGroupId = group.id;

      if (!targetGroupId) {
        const created = await api.createGroup({
          name: group.name.trim(),
          description: group.description,
        });
        targetGroupId = created.id;
      } else {
        await api.updateGroup(targetGroupId, {
          name: group.name.trim(),
          description: group.description,
        });
      }

      await api.setGroupRoles(targetGroupId, normalizeIds(selectedRoleIds));
      await syncGroupUsers(targetGroupId);

      await showAlert({
        title: "Grupo salvo",
        message: "Alterações do grupo foram aplicadas.",
      });
      goBack();
    } catch (e: unknown) {
      await showAlert({
        title: "Erro",
        message:
          e instanceof Error ? e.message : "Não foi possível salvar o grupo.",
      });
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="rbac-edit-page">
        <Spinner label="Carregando grupo…" />
      </div>
    );
  }

  if (error || !group) {
    return (
      <div className="rbac-edit-page">
        <Alert tone="danger">{error || "Grupo não encontrado."}</Alert>
        <Button variant="secondary" onClick={goBack}>
          Voltar à lista de grupos
        </Button>
      </div>
    );
  }

  return (
    <PageChrome
      className="rbac-edit-page"
      breadcrumb={[
        { label: "Admin", onClick: () => navigate("/admin") },
        { label: "Grupos", onClick: goBack },
        { label: isNew ? "Novo" : group.name },
      ]}
      title={isNew ? "Novo grupo" : `Editar grupo — ${group.name}`}
      subtitle={!isNew ? <>ID <code>{group.id}</code></> : undefined}
      actions={
        <>
          <Button variant="secondary" onClick={goBack} disabled={saving}>
            Voltar
          </Button>
          <Button
            variant="primary"
            onClick={() => void save()}
            disabled={saving || !group.name?.trim()}
            loading={saving}
          >
            {saving ? "Salvando…" : "Salvar"}
          </Button>
        </>
      }
      tabs={{
        items: [
          { id: "details", label: "Dados" },
          { id: "users", label: "Usuários" },
          { id: "roles", label: "Papéis" },
        ],
        value: activeTab,
        onChange: (id) => setActiveTab(id as GroupPageTab),
      }}
    >
      <div className="rbac-edit-card group-edit-body">
        {activeTab === "details" && (
          <>
            <FormField label="Nome" required htmlFor="group-name">
              <Input
                id="group-name"
                value={group.name}
                onChange={(event) =>
                  setGroup((prev) =>
                    prev ? { ...prev, name: event.target.value } : prev
                  )
                }
                disabled={saving}
              />
            </FormField>

            <FormField label="Descrição" htmlFor="group-description">
              <Textarea
                id="group-description"
                value={group.description || ""}
                onChange={(event) =>
                  setGroup((prev) =>
                    prev
                      ? { ...prev, description: event.target.value }
                      : prev
                  )
                }
                disabled={saving}
              />
            </FormField>

            <Alert tone="info">
              Use as abas <strong>Usuários</strong> e <strong>Papéis</strong>{" "}
              para controlar quem pertence ao grupo e quais papéis são herdados
              por esses usuários.
            </Alert>
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
            onChange={setSelectedUserIds}
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
            onChange={setSelectedRoleIds}
          />
        )}
      </div>
    </PageChrome>
  );
};
