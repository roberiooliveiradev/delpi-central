// portal/src/ui/admin/rbac/UserSummaryTab.tsx

import type { AdminUser } from "../../../data/adminApi";
import type { UserAccessProfile } from "../../../data/userAccessProfileTypes";
import { Alert, Input, Spinner, Switch } from "../../../ui-kit";

import { RbacAccessTree } from "./RbacAccessTree";
import { userStatusLabel } from "./userEditUtils";

type Props = {
  mode: "view" | "edit";
  user: AdminUser;
  birthDate: string;
  isSuperadmin: boolean;
  busy: boolean;
  accessProfile: UserAccessProfile | null;
  accessProfileLoading: boolean;
  accessProfileError: string | null;
  onBirthDateChange: (value: string) => void;
  onSuperadminChange: (value: boolean) => void;
  onOpenRole?: (roleId: string) => void;
  onOpenGroup?: (groupId: string) => void;
};

export function UserSummaryTab({
  mode,
  user,
  birthDate,
  isSuperadmin,
  busy,
  accessProfile,
  accessProfileLoading,
  accessProfileError,
  onBirthDateChange,
  onSuperadminChange,
  onOpenRole,
  onOpenGroup,
}: Props) {
  const statusLabel = userStatusLabel(user.active);
  const isEditing = mode === "edit";

  return (
    <div className="user-rbac-summary">
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
                onChange={(event) => onBirthDateChange(event.target.value)}
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
                Concede acesso administrativo completo, independentemente dos
                papéis, grupos ou permissões vinculadas ao usuário.
              </p>
            </div>
          </div>

          <Switch
            checked={isSuperadmin}
            onChange={(event) => onSuperadminChange(event.target.checked)}
            disabled={busy}
            label={isSuperadmin ? "Ativado" : "Desativado"}
          />
        </section>
      ) : (
        <section className="user-rbac-panel user-rbac-panel--access-map">
          <div className="user-rbac-panel-header">
            <div>
              <h4>Mapa de acesso</h4>
              <p>Caminhos diretos e herdados via grupos.</p>
            </div>
            {isSuperadmin ? (
              <span className="user-rbac-status user-rbac-status-warning">Superadmin</span>
            ) : null}
          </div>

          {accessProfileLoading ? (
            <Spinner label="Carregando mapa de acesso…" />
          ) : accessProfileError ? (
            <Alert tone="danger">{accessProfileError}</Alert>
          ) : accessProfile ? (
            <RbacAccessTree
              variant="unified"
              profile={accessProfile}
              userDisplayName={user.name || user.email}
              onOpenRole={onOpenRole}
              onOpenGroup={onOpenGroup}
            />
          ) : (
            <Alert tone="info">Perfil de acesso indisponível.</Alert>
          )}
        </section>
      )}
    </div>
  );
}
