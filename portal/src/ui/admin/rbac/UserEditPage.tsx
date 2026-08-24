// portal/src/ui/admin/rbac/UserEditPage.tsx

import { useCallback, useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import type { AdminGroup, AdminRole, AdminUser } from "../../../data/adminApi";
import { useAdminApi } from "../../../hooks/useAdminApi";
import { RelationshipPicker } from "../../../components/RelationshipPicker";
import { useAppAlert } from "../../../components/ConfirmDialogProvider";
import {
  Alert,
  Button,
  Input,
  PageChrome,
  Spinner,
  Switch,
} from "../../../ui-kit";

import "./RbacEditPage.css";
import { UserUsageTab } from "./UserUsageTab";
import { useAdminUserAccessProfile } from "./useAdminUserAccessProfile";
import { useUserPageMode, type UserPageTab } from "./useUserPageMode";
import { normalizeIds, userStatusLabel } from "./userEditUtils";

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

      await showAlert({
        title: "Usuário salvo",
        message: "Papéis, grupos e privilégios foram atualizados.",
      });
      goBack();
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

  const statusLabel = userStatusLabel(user.active);
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

        {activeTab === "summary" && !(isEditing && loadingEdit) && (
          <div className="user-rbac-summary">
            <div className="user-rbac-summary-grid">
              <section className="user-rbac-panel">
                <div className="user-rbac-panel-header">
                  <div>
                    <h4>Usuário</h4>
                    <p>Identidade sincronizada pelo provedor de autenticação.</p>
                  </div>

                  <span
                    className={[
                      "user-rbac-status",
                      user.active === false
                        ? "user-rbac-status-danger"
                        : "user-rbac-status-success",
                    ].join(" ")}
                  >
                    {statusLabel}
                  </span>
                </div>

                <div className="user-rbac-info-list">
                  <div className="user-rbac-info-item">
                    <span>Nome</span>
                    <strong>{user.name || "-"}</strong>
                  </div>

                  <div className="user-rbac-info-item">
                    <span>Email</span>
                    <strong>{user.email}</strong>
                  </div>

                  <div className="user-rbac-info-item">
                    <span>Status</span>
                    <strong>{statusLabel}</strong>
                  </div>

                  {isEditing ? (
                    <label className="user-rbac-info-item user-rbac-info-item--field">
                      <span>Data de nascimento</span>
                      <Input
                        type="date"
                        value={birthDate}
                        onChange={(event) => setBirthDate(event.target.value)}
                        disabled={busy}
                      />
                      <small>Usada na automação de aniversário.</small>
                    </label>
                  ) : (
                    <div className="user-rbac-info-item">
                      <span>Data de nascimento</span>
                      <strong>
                        {birthDate
                          ? new Date(`${birthDate}T00:00:00`).toLocaleDateString("pt-BR")
                          : "-"}
                      </strong>
                    </div>
                  )}
                </div>
              </section>

              {!isEditing ? (
                <section className="user-rbac-panel">
                  <div className="user-rbac-panel-header">
                    <div>
                      <h4>Mapa de acesso</h4>
                      <p>Carregando perfil efetivo…</p>
                    </div>
                  </div>
                  {accessProfile.loading ? (
                    <Spinner label="Carregando mapa de acesso…" />
                  ) : accessProfile.error ? (
                    <Alert tone="danger">{accessProfile.error}</Alert>
                  ) : null}
                </section>
              ) : null}
            </div>

            {isEditing ? (
              <section
                className={[
                  "user-rbac-superadmin-card",
                  isSuperadmin ? "active" : "",
                ]
                  .filter(Boolean)
                  .join(" ")}
              >
                <div className="user-rbac-superadmin-content">
                  <div className="user-rbac-superadmin-icon">★</div>
                  <div>
                    <h4>Privilégio administrativo</h4>
                    <strong>Superadmin</strong>
                    <p>
                      Concede acesso administrativo completo, independentemente
                      dos papéis, grupos ou permissões vinculadas ao usuário.
                    </p>
                  </div>
                </div>

                <Switch
                  checked={isSuperadmin}
                  onChange={(event) => setIsSuperadmin(event.target.checked)}
                  disabled={busy}
                  label={isSuperadmin ? "Ativado" : "Desativado"}
                />
              </section>
            ) : null}
          </div>
        )}

        {isEditing && activeTab === "roles" && !loadingEdit && (
          <RelationshipPicker<AdminRole>
            title="Papéis diretos do Usuário"
            availableTitle="Papéis disponíveis"
            selectedTitle="Papéis vinculados ao usuário"
            searchPlaceholder="Buscar papel..."
            emptyAvailableText="Nenhum papel disponível para adicionar."
            emptySelectedText="Nenhum papel direto vinculado a este usuário."
            items={roles}
            selectedIds={selectedRoleIds}
            disabled={busy}
            getId={(role) => role.id}
            getTitle={(role) => role.name}
            getDescription={(role) => role.description ?? null}
            onChange={setSelectedRoleIds}
          />
        )}

        {isEditing && activeTab === "groups" && !loadingEdit && (
          <RelationshipPicker<AdminGroup>
            title="Grupos do Usuário"
            availableTitle="Grupos disponíveis"
            selectedTitle="Grupos vinculados ao usuário"
            searchPlaceholder="Buscar grupo..."
            emptyAvailableText="Nenhum grupo disponível para adicionar."
            emptySelectedText="Nenhum grupo vinculado a este usuário."
            items={groups}
            selectedIds={selectedGroupIds}
            disabled={busy}
            getId={(group) => group.id}
            getTitle={(group) => group.name}
            getDescription={(group) => group.description ?? null}
            onChange={setSelectedGroupIds}
          />
        )}

        {!isEditing && (activeTab === "roles" || activeTab === "groups") ? (
          accessProfile.loading ? (
            <Spinner label="Carregando perfil de acesso…" />
          ) : accessProfile.error ? (
            <Alert tone="danger">{accessProfile.error}</Alert>
          ) : null
        ) : null}

        {activeTab === "usage" && userId ? (
          <UserUsageTab userId={userId} active={activeTab === "usage"} />
        ) : null}
      </div>
    </PageChrome>
  );
};
