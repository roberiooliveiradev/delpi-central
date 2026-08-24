// src/ui/admin/rbac/UserEditPage.tsx

import { useEffect, useState } from "react";
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

type UserPageTab = "summary" | "roles" | "groups" | "usage";

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

export const UserEditPage = () => {
  const { userId = "" } = useParams<{ userId: string }>();
  const navigate = useNavigate();
  const showAlert = useAppAlert();
  const api = useAdminApi();

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<UserPageTab>("summary");

  const [user, setUser] = useState<AdminUser | null>(null);
  const [roles, setRoles] = useState<AdminRole[]>([]);
  const [groups, setGroups] = useState<AdminGroup[]>([]);
  const [selectedRoleIds, setSelectedRoleIds] = useState<string[]>([]);
  const [selectedGroupIds, setSelectedGroupIds] = useState<string[]>([]);
  const [isSuperadmin, setIsSuperadmin] = useState(false);
  const [birthDate, setBirthDate] = useState("");

  useEffect(() => {
    if (!userId) return;

    let cancelled = false;

    const load = async () => {
      setLoading(true);
      setError(null);
      setActiveTab("summary");

      try {
        const [
          usersRes,
          allRolesRes,
          allGroupsRes,
          userRolesRes,
          userGroupsRes,
        ] = await Promise.all([
          api.listUsers({ page: 1, pageSize: 999 }),
          api.listRoles({ page: 1, pageSize: 999 }),
          api.listGroups({ page: 1, pageSize: 999 }),
          api.getUserRoles(userId),
          api.getUserGroups(userId),
        ]);

        if (cancelled) return;

        const found = (usersRes.data ?? []).find((item) => item.id === userId);
        if (!found) {
          setError("Usuário não encontrado.");
          setUser(null);
          return;
        }

        setUser(found);
        setRoles(allRolesRes.data ?? []);
        setGroups(allGroupsRes.data ?? []);
        setSelectedRoleIds(normalizeIds(userRolesRes.data ?? []));
        setSelectedGroupIds(normalizeIds(userGroupsRes.data ?? []));
        setIsSuperadmin(!!found.is_superadmin);
        setBirthDate(
          found.birth_date ? String(found.birth_date).slice(0, 10) : ""
        );
      } catch (e: unknown) {
        if (!cancelled) {
          setError(
            e instanceof Error
              ? e.message
              : "Não foi possível carregar o usuário."
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
  }, [api, userId]);

  const goBack = () => navigate("/admin?tab=users");

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

  if (loading) {
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

  const userStatusLabel = user.active === false ? "Inativo" : "Ativo";
  const busy = loading || saving;

  return (
    <PageChrome
      className="rbac-edit-page"
      breadcrumb={[
        { label: "Admin", onClick: () => navigate("/admin") },
        { label: "Usuários", onClick: goBack },
        { label: user.email },
      ]}
      title={`Editar RBAC — ${user.email}`}
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
          <Button
            variant="primary"
            onClick={() => void save()}
            disabled={busy}
            loading={saving}
          >
            {saving ? "Salvando…" : "Salvar"}
          </Button>
        </>
      }
      tabs={{
        items: [
          { id: "summary", label: "Resumo" },
          { id: "roles", label: "Papéis diretos" },
          { id: "groups", label: "Grupos" },
          { id: "usage", label: "Uso" },
        ],
        value: activeTab,
        onChange: (id) => setActiveTab(id as UserPageTab),
      }}
    >
      <div className="rbac-edit-card user-rbac-body">
        {activeTab === "summary" && (
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
                    {userStatusLabel}
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
                    <strong>{userStatusLabel}</strong>
                  </div>

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
                </div>
              </section>

              <section className="user-rbac-panel">
                <div className="user-rbac-panel-header">
                  <div>
                    <h4>Acessos</h4>
                    <p>Resumo dos vínculos diretos configurados no RBAC.</p>
                  </div>
                </div>

                <div className="user-rbac-stat-grid">
                  <button
                    type="button"
                    className="user-rbac-stat-card"
                    onClick={() => setActiveTab("roles")}
                  >
                    <strong>{selectedRoleIds.length}</strong>
                    <span>Papéis diretos</span>
                  </button>

                  <button
                    type="button"
                    className="user-rbac-stat-card"
                    onClick={() => setActiveTab("groups")}
                  >
                    <strong>{selectedGroupIds.length}</strong>
                    <span>Grupos</span>
                  </button>
                </div>
              </section>
            </div>

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

            <Alert tone="info">
              Papéis diretos são concedidos diretamente ao usuário. Grupos podem
              conceder papéis adicionais de forma indireta.
            </Alert>
          </div>
        )}

        {activeTab === "roles" && (
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

        {activeTab === "groups" && (
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

        {activeTab === "usage" && userId ? (
          <UserUsageTab userId={userId} active={activeTab === "usage"} />
        ) : null}
      </div>
    </PageChrome>
  );
};
