// portal/src/ui/admin/rbac/UserEditPage.tsx

import { useCallback, useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import type { AdminGroup, AdminRole, AdminUser } from "../../../data/adminApi";
import { useAdminApi } from "../../../hooks/useAdminApi";
import { useAppAlert } from "../../../components/ConfirmDialogProvider";
import { Alert, Button, PageChrome, Spinner } from "../../../ui-kit";

import "./RbacEditPage.css";
import { UserSummaryTab } from "./UserSummaryTab";
import { UserGroupsEditTab } from "./UserGroupsEditTab";
import { UserGroupsViewTab } from "./UserGroupsViewTab";
import { UserRolesEditTab } from "./UserRolesEditTab";
import { UserRolesViewTab } from "./UserRolesViewTab";
import { UserUsageTab } from "./UserUsageTab";
import { useAdminUserAccessProfile } from "./useAdminUserAccessProfile";
import { useUserPageMode, type UserPageTab } from "./useUserPageMode";
import { normalizeIds } from "./userEditUtils";

export const UserEditPage = () => {
  const { userId = "" } = useParams<{ userId: string }>();
  const navigate = useNavigate();
  const showAlert = useAppAlert();
  const api = useAdminApi();

  const {
    isEditing,
    activeTab,
    setActiveTab,
    enterEdit,
    exitEdit,
    pageTitleSuffix,
  } = useUserPageMode();

  const accessProfile = useAdminUserAccessProfile(userId, !isEditing);

  const [loadingUser, setLoadingUser] = useState(true);
  const [loadingEdit, setLoadingEdit] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [user, setUser] = useState<AdminUser | null>(null);
  const [roles, setRoles] = useState<AdminRole[]>([]);
  const [groups, setGroups] = useState<AdminGroup[]>([]);
  const [selectedRoleIds, setSelectedRoleIds] = useState<string[]>([]);
  const [selectedGroupIds, setSelectedGroupIds] = useState<string[]>([]);
  const [isSuperadmin, setIsSuperadmin] = useState(false);
  const [birthDate, setBirthDate] = useState("");

  const applyUserSnapshot = useCallback((found: AdminUser) => {
    setUser(found);
    setIsSuperadmin(!!found.is_superadmin);
    setBirthDate(found.birth_date ? String(found.birth_date).slice(0, 10) : "");
  }, []);

  useEffect(() => {
    if (!userId) return;

    let cancelled = false;

    const loadUser = async () => {
      setLoadingUser(true);
      setError(null);

      try {
        const usersRes = await api.listUsers({ page: 1, pageSize: 999 });
        if (cancelled) return;

        const found = (usersRes.data ?? []).find((item) => item.id === userId);
        if (!found) {
          setError("Usuário não encontrado.");
          setUser(null);
          return;
        }

        applyUserSnapshot(found);
      } catch (e: unknown) {
        if (!cancelled) {
          setError(
            e instanceof Error
              ? e.message
              : "Não foi possível carregar o usuário.",
          );
        }
      } finally {
        if (!cancelled) setLoadingUser(false);
      }
    };

    void loadUser();

    return () => {
      cancelled = true;
    };
  }, [api, applyUserSnapshot, userId]);

  useEffect(() => {
    if (!userId || !isEditing) {
      return;
    }

    let cancelled = false;

    const loadEditData = async () => {
      setLoadingEdit(true);

      try {
        const [allRolesRes, allGroupsRes, userRolesRes, userGroupsRes] =
          await Promise.all([
            api.listRoles({ page: 1, pageSize: 999 }),
            api.listGroups({ page: 1, pageSize: 999 }),
            api.getUserRoles(userId),
            api.getUserGroups(userId),
          ]);

        if (cancelled) return;

        setRoles(allRolesRes.data ?? []);
        setGroups(allGroupsRes.data ?? []);
        setSelectedRoleIds(normalizeIds(userRolesRes.data ?? []));
        setSelectedGroupIds(normalizeIds(userGroupsRes.data ?? []));
      } catch (e: unknown) {
        if (!cancelled) {
          await showAlert({
            title: "Erro",
            message:
              e instanceof Error
                ? e.message
                : "Não foi possível carregar dados para edição.",
          });
          exitEdit();
        }
      } finally {
        if (!cancelled) setLoadingEdit(false);
      }
    };

    void loadEditData();

    return () => {
      cancelled = true;
    };
  }, [api, exitEdit, isEditing, showAlert, userId]);

  const goBack = () => navigate("/admin?tab=users");

  const handleCancelEdit = () => {
    if (user) {
      applyUserSnapshot(user);
    }
    exitEdit();
  };

  const save = async () => {
    if (!user) return;

    setSaving(true);

    try {
      await api.updateUser(user.id, {
        roleIds: normalizeIds(selectedRoleIds),
        groupIds: normalizeIds(selectedGroupIds),
        is_superadmin: isSuperadmin,
        birthDate: birthDate.trim() ? birthDate.trim() : null,
      });

      applyUserSnapshot({
        ...user,
        is_superadmin: isSuperadmin,
        birth_date: birthDate.trim() ? birthDate.trim() : null,
      });

      await showAlert({
        title: "Usuário salvo",
        message: "Papéis, grupos e privilégios foram atualizados.",
      });

      exitEdit();
      await accessProfile.load({ silent: true });
    } catch (e: unknown) {
      await showAlert({
        title: "Erro",
        message:
          e instanceof Error
            ? e.message
            : "Não foi possível salvar o usuário.",
      });
    } finally {
      setSaving(false);
    }
  };

  const openRoleAdmin = useCallback(
    (roleId: string) => navigate(`/admin/roles/${roleId}`),
    [navigate],
  );

  const openGroupAdmin = useCallback(
    (groupId: string) => navigate(`/admin/groups/${groupId}`),
    [navigate],
  );

  if (loadingUser) {
    return (
      <div className="rbac-edit-page">
        <Spinner label="Carregando usuário…" />
      </div>
    );
  }

  if (error || !user) {
    return (
      <div className="rbac-edit-page">
        <Alert tone="danger">{error || "Usuário não encontrado."}</Alert>
        <Button variant="secondary" onClick={goBack}>
          Voltar à lista de usuários
        </Button>
      </div>
    );
  }

  const busy = loadingUser || loadingEdit || saving;

  const tabItems = [
    { id: "summary", label: "Resumo" },
    { id: "roles", label: isEditing ? "Papéis diretos" : "Papéis" },
    { id: "groups", label: "Grupos" },
    { id: "usage", label: "Uso" },
  ];

  return (
    <PageChrome
      className="rbac-edit-page"
      breadcrumb={[
        { label: "Admin", onClick: () => navigate("/admin") },
        { label: "Usuários", onClick: goBack },
        { label: user.email },
      ]}
      title={`${pageTitleSuffix} — ${user.email}`}
      subtitle={
        <>
          {user.name || "Sem nome"} · ID <code>{user.id}</code>
        </>
      }
      actions={
        <>
          <Button variant="secondary" onClick={goBack} disabled={busy}>
            Voltar
          </Button>
          {isEditing ? (
            <>
              <Button variant="secondary" onClick={handleCancelEdit} disabled={busy}>
                Cancelar
              </Button>
              <Button
                variant="primary"
                onClick={() => void save()}
                disabled={busy}
                loading={saving}
              >
                {saving ? "Salvando…" : "Salvar"}
              </Button>
            </>
          ) : (
            <Button variant="primary" onClick={() => enterEdit()} disabled={busy}>
              Editar
            </Button>
          )}
        </>
      }
      tabs={{
        items: tabItems,
        value: activeTab,
        onChange: (id) => setActiveTab(id as UserPageTab),
      }}
    >
      <div className="rbac-edit-card user-rbac-body">
        {isEditing && loadingEdit ? (
          <Spinner label="Carregando dados para edição…" />
        ) : null}

        {activeTab === "summary" && !(isEditing && loadingEdit) ? (
          <UserSummaryTab
            mode={isEditing ? "edit" : "view"}
            user={user}
            birthDate={birthDate}
            isSuperadmin={isSuperadmin}
            busy={busy}
            accessProfile={accessProfile.data}
            accessProfileLoading={accessProfile.loading}
            accessProfileError={accessProfile.error}
            onBirthDateChange={setBirthDate}
            onSuperadminChange={setIsSuperadmin}
            onOpenRole={openRoleAdmin}
            onOpenGroup={openGroupAdmin}
          />
        ) : null}

        {!isEditing && activeTab === "roles" ? (
          <UserRolesViewTab
            profile={accessProfile.data}
            loading={accessProfile.loading}
            error={accessProfile.error}
            onEditDirectRoles={() => enterEdit("roles")}
            onOpenRole={openRoleAdmin}
            onOpenGroup={openGroupAdmin}
          />
        ) : null}

        {!isEditing && activeTab === "groups" ? (
          <UserGroupsViewTab
            profile={accessProfile.data}
            loading={accessProfile.loading}
            error={accessProfile.error}
            onEditGroups={() => enterEdit("groups")}
            onOpenRole={openRoleAdmin}
            onOpenGroup={openGroupAdmin}
          />
        ) : null}

        {isEditing && activeTab === "roles" && !loadingEdit ? (
          <UserRolesEditTab
            roles={roles}
            selectedRoleIds={selectedRoleIds}
            busy={busy}
            onChange={setSelectedRoleIds}
          />
        ) : null}

        {isEditing && activeTab === "groups" && !loadingEdit ? (
          <UserGroupsEditTab
            groups={groups}
            selectedGroupIds={selectedGroupIds}
            busy={busy}
            onChange={setSelectedGroupIds}
          />
        ) : null}

        {activeTab === "usage" && userId ? (
          <UserUsageTab userId={userId} active={activeTab === "usage"} />
        ) : null}
      </div>
    </PageChrome>
  );
};
