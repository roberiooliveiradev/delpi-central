// src/ui/admin/modals/UserRbacModal.tsx

import { useEffect, useState } from "react";
import type {
  AdminGroup,
  AdminRole,
  AdminUser,
} from "../../../data/adminApi";
import { AdminApi } from "../../../data/adminApi";
import { Modal } from "../../../components/Modal";
import { RelationshipPicker } from "../../../components/RelationshipPicker";
import "./UserRbacModal.css";

type UserRbacTab = "summary" | "roles" | "groups";

type Props = {
  open: boolean;
  onClose: () => void;
  user: AdminUser | null;
  api: AdminApi;
  onSaved: () => void;
};

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

export const UserRbacModal = ({
  open,
  onClose,
  user,
  api,
  onSaved,
}: Props) => {
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<UserRbacTab>("summary");

  const [roles, setRoles] = useState<AdminRole[]>([]);
  const [groups, setGroups] = useState<AdminGroup[]>([]);

  const [selectedRoleIds, setSelectedRoleIds] = useState<string[]>([]);
  const [selectedGroupIds, setSelectedGroupIds] = useState<string[]>([]);
  const [isSuperadmin, setIsSuperadmin] = useState(false);
  const [birthDate, setBirthDate] = useState("");

  useEffect(() => {
    if (!open || !user) return;

    let cancelled = false;

    const load = async () => {
      setLoading(true);

      try {
        const [
          allRolesRes,
          allGroupsRes,
          userRolesRes,
          userGroupsRes,
        ] = await Promise.all([
          api.listRoles({ page: 1, pageSize: 999 }),
          api.listGroups({ page: 1, pageSize: 999 }),
          api.getUserRoles(user.id),
          api.getUserGroups(user.id),
        ]);

        if (cancelled) return;

        setRoles(allRolesRes.data ?? []);
        setGroups(allGroupsRes.data ?? []);
        setSelectedRoleIds(normalizeIds(userRolesRes.data ?? []));
        setSelectedGroupIds(normalizeIds(userGroupsRes.data ?? []));
        setIsSuperadmin(!!user.is_superadmin);
        setBirthDate(user.birth_date ? String(user.birth_date).slice(0, 10) : "");
        setActiveTab("summary");
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    load();

    return () => {
      cancelled = true;
    };
  }, [open, user, api]);

  if (!open || !user) return null;

  const save = async () => {
    setLoading(true);

    try {
      await api.updateUser(user.id, {
        roleIds: normalizeIds(selectedRoleIds),
        groupIds: normalizeIds(selectedGroupIds),
        is_superadmin: isSuperadmin,
        birthDate: birthDate.trim() ? birthDate.trim() : null,
      });

      onSaved();
      onClose();
    } finally {
      setLoading(false);
    }
  };

  const userStatusLabel = user.active === false ? "Inativo" : "Ativo";

  return (
    <Modal
      open={open}
      title={`Editar RBAC — ${user.email}`}
      onClose={onClose}
      size="xl"
      footer={
        <>
          <button onClick={onClose} disabled={loading}>
            Cancelar
          </button>

          <button onClick={save} disabled={loading}>
            Salvar
          </button>
        </>
      }
    >
      <div className="user-rbac-body">
        <div className="tabs">
          <button
            type="button"
            className={activeTab === "summary" ? "active" : ""}
            onClick={() => setActiveTab("summary")}
          >
            Resumo
          </button>

          <button
            type="button"
            className={activeTab === "roles" ? "active" : ""}
            onClick={() => setActiveTab("roles")}
          >
            Papéis diretos
          </button>

          <button
            type="button"
            className={activeTab === "groups" ? "active" : ""}
            onClick={() => setActiveTab("groups")}
          >
            Grupos
          </button>
        </div>

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
                    <input
                      type="date"
                      value={birthDate}
                      onChange={(event) => setBirthDate(event.target.value)}
                      disabled={loading}
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

              <label className="user-rbac-switch">
                <input
                  type="checkbox"
                  checked={isSuperadmin}
                  onChange={(event) => setIsSuperadmin(event.target.checked)}
                  disabled={loading}
                />
                <span className="user-rbac-switch-control" />
                <span className="user-rbac-switch-label">
                  {isSuperadmin ? "Ativado" : "Desativado"}
                </span>
              </label>
            </section>

            <div className="user-rbac-alert">
              Papéis diretos são concedidos diretamente ao usuário. Grupos podem
              conceder papéis adicionais de forma indireta.
            </div>
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
            disabled={loading}
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
            disabled={loading}
            getId={(group) => group.id}
            getTitle={(group) => group.name}
            getDescription={(group) => group.description ?? null}
            onChange={setSelectedGroupIds}
          />
        )}
      </div>
    </Modal>
  );
};