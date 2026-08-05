// src/ui/admin/rbac/RoleEditPage.tsx

import { useContext, useEffect, useMemo, useState } from "react";
import { useNavigate, useParams, useSearchParams } from "react-router-dom";

import { AuthContext } from "../../../state/AuthContext";
import { ApiClient } from "../../../data/apiClient";
import { AdminApi } from "../../../data/adminApi";
import type {
  AdminApp,
  AdminPermission,
  AdminRole,
  AdminUser,
} from "../../../data/adminApi";
import { AppGroupedPermissionPicker } from "../../../components/AppGroupedPermissionPicker";
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
import type { AppInfoByModule } from "../tabs/RolesTab";

import "../modals/RoleEditModal.css";
import "./RbacEditPage.css";

type RolePageTab = "details" | "users" | "permissions";

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

const normalizeModuleKey = (value: string | null | undefined) => {
  return (value ?? "")
    .trim()
    .toLowerCase()
    .replace(/^\/+/, "")
    .replace(/^apps\//, "");
};

const buildAppInfoByModule = (apps: AdminApp[]): AppInfoByModule => {
  const result: AppInfoByModule = {};

  apps.forEach((app) => {
    const info = {
      name: app.name ?? app.id,
      icon: app.icon ?? null,
    };

    const idKey = normalizeModuleKey(app.id);
    const basePathKey = normalizeModuleKey(app.base_path);

    if (idKey) result[idKey] = info;
    if (basePathKey) result[basePathKey] = info;
  });

  return result;
};

const resolvePreselectedPermissionIds = (
  allPerms: AdminPermission[],
  permissionCodes: string[]
): string[] => {
  const codeSet = new Set(
    permissionCodes.map((code) => code.trim()).filter(Boolean)
  );

  if (codeSet.size === 0) return [];

  return allPerms
    .filter((perm) => codeSet.has(perm.code))
    .map((perm) => perm.id);
};

export const RoleEditPage = () => {
  const { roleId } = useParams<{ roleId: string }>();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { getAccessToken } = useContext(AuthContext);
  const showAlert = useAppAlert();

  const isNew = !roleId || roleId === "new";

  const api = useMemo(
    () => new AdminApi(new ApiClient("", getAccessToken)),
    [getAccessToken]
  );

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<RolePageTab>("details");

  const [role, setRole] = useState<AdminRole | null>(null);
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [selectedUserIds, setSelectedUserIds] = useState<string[]>([]);
  const [allPerms, setAllPerms] = useState<AdminPermission[]>([]);
  const [selectedPermIds, setSelectedPermIds] = useState<string[]>([]);
  const [appInfoByModule, setAppInfoByModule] = useState<AppInfoByModule>({});

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      setLoading(true);
      setError(null);
      setActiveTab("details");

      try {
        const permissionCodesParam = searchParams.get("permissionCodes") || "";
        const permissionCodes = permissionCodesParam
          .split(",")
          .map((code) => code.trim())
          .filter(Boolean);

        if (isNew) {
          const [permissionsRes, usersRes, appsRes] = await Promise.all([
            api.listPermissions({ page: 1, pageSize: 999 }),
            api.listUsers({ page: 1, pageSize: 999 }),
            api.listApps({ page: 1, pageSize: 999 }),
          ]);

          if (cancelled) return;

          const perms = permissionsRes.data ?? [];
          setAllPerms(perms);
          setUsers(usersRes.data ?? []);
          setAppInfoByModule(buildAppInfoByModule(appsRes.data ?? []));
          setSelectedUserIds([]);
          setSelectedPermIds(
            resolvePreselectedPermissionIds(perms, permissionCodes)
          );
          setRole({
            id: "",
            name: "",
            description: "",
          });
          return;
        }

        const [
          rolesRes,
          permissionsRes,
          rolePermissions,
          usersRes,
          roleUsers,
          appsRes,
        ] = await Promise.all([
          api.listRoles({ page: 1, pageSize: 999 }),
          api.listPermissions({ page: 1, pageSize: 999 }),
          api.getRolePermissions(roleId),
          api.listUsers({ page: 1, pageSize: 999 }),
          api.getRoleUsers(roleId),
          api.listApps({ page: 1, pageSize: 999 }),
        ]);

        if (cancelled) return;

        const found = (rolesRes.data ?? []).find((item) => item.id === roleId);
        if (!found) {
          setError("Papel não encontrado.");
          setRole(null);
          return;
        }

        setRole({ ...found });
        setAllPerms(permissionsRes.data ?? []);
        setSelectedPermIds(normalizeIds(rolePermissions.data ?? []));
        setUsers(usersRes.data ?? []);
        setSelectedUserIds(normalizeIds(roleUsers.data ?? []));
        setAppInfoByModule(buildAppInfoByModule(appsRes.data ?? []));
      } catch (e: unknown) {
        if (!cancelled) {
          setError(
            e instanceof Error ? e.message : "Não foi possível carregar o papel."
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
  }, [api, isNew, roleId, searchParams]);

  const goBack = () => navigate("/admin?tab=roles");

  const syncRoleUsers = async (targetRoleId: string) => {
    const current = await api.getRoleUsers(targetRoleId);
    const currentIds = normalizeIds(current.data ?? []);
    const nextIds = normalizeIds(selectedUserIds);

    const toAdd = nextIds.filter((id) => !currentIds.includes(id));
    const toRemove = currentIds.filter((id) => !nextIds.includes(id));

    await Promise.all([
      ...toAdd.map((userId) => api.addUserToRole(targetRoleId, userId)),
      ...toRemove.map((userId) => api.removeUserFromRole(targetRoleId, userId)),
    ]);
  };

  const save = async () => {
    if (!role?.name?.trim()) return;

    setSaving(true);

    try {
      let targetRoleId: string;

      if (!role.id) {
        const created = await api.createRole({
          name: role.name.trim(),
          description: role.description ?? undefined,
        });
        targetRoleId = created.id;
      } else {
        await api.updateRole(role.id, {
          name: role.name.trim(),
          description: role.description ?? undefined,
        });
        targetRoleId = role.id;
      }

      await api.setRolePermissions(targetRoleId, normalizeIds(selectedPermIds));
      await syncRoleUsers(targetRoleId);

      await showAlert({
        title: "Papel salvo",
        message: "Alterações do papel foram aplicadas.",
      });
      goBack();
    } catch (e: unknown) {
      await showAlert({
        title: "Erro",
        message:
          e instanceof Error ? e.message : "Não foi possível salvar o papel.",
      });
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="rbac-edit-page">
        <Spinner label="Carregando papel…" />
      </div>
    );
  }

  if (error || !role) {
    return (
      <div className="rbac-edit-page">
        <Alert tone="danger">{error || "Papel não encontrado."}</Alert>
        <Button variant="secondary" onClick={goBack}>
          Voltar à lista de papéis
        </Button>
      </div>
    );
  }

  return (
    <PageChrome
      className="rbac-edit-page"
      breadcrumb={[
        { label: "Admin", onClick: () => navigate("/admin") },
        { label: "Papéis", onClick: goBack },
        { label: isNew ? "Novo" : role.name },
      ]}
      title={isNew ? "Novo papel" : `Editar papel — ${role.name}`}
      subtitle={!isNew ? <>ID <code>{role.id}</code></> : undefined}
      actions={
        <>
          <Button variant="secondary" onClick={goBack} disabled={saving}>
            Voltar
          </Button>
          <Button
            variant="primary"
            onClick={() => void save()}
            disabled={saving || !role.name?.trim()}
            loading={saving}
          >
            {saving ? "Salvando…" : "Salvar"}
          </Button>
        </>
      }
      tabs={{
        items: [
          { id: "details", label: "Dados" },
          { id: "users", label: "Usuários diretos" },
          { id: "permissions", label: "Permissões" },
        ],
        value: activeTab,
        onChange: (id) => setActiveTab(id as RolePageTab),
      }}
    >
      <div className="rbac-edit-card role-edit-body">
        {activeTab === "details" && (
          <>
            <FormField label="Nome" required htmlFor="role-name">
              <Input
                id="role-name"
                value={role.name}
                onChange={(event) =>
                  setRole((prev) =>
                    prev ? { ...prev, name: event.target.value } : prev
                  )
                }
                disabled={saving}
              />
            </FormField>

            <FormField label="Descrição" htmlFor="role-description">
              <Textarea
                id="role-description"
                value={role.description || ""}
                onChange={(event) =>
                  setRole((prev) =>
                    prev
                      ? { ...prev, description: event.target.value }
                      : prev
                  )
                }
                disabled={saving}
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
            onChange={setSelectedUserIds}
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
            onChange={setSelectedPermIds}
          />
        )}
      </div>
    </PageChrome>
  );
};
