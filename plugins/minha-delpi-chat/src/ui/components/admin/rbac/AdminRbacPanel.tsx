import type { AdminRbacSummary } from "../../../../data/api/adminTypes";

import "./AdminRbacPanel.css";

type AdminRbacPanelProps = {
  rbac: AdminRbacSummary | null;
};

const ROLE_LABELS: Record<string, string> = {
  admin: "Admin",
  operator: "Operador",
  auditor: "Auditor",
  viewer: "Viewer",
};

export function AdminRbacPanel({ rbac }: AdminRbacPanelProps) {
  return (
    <article className="mdc-admin-panel mdc-admin-rbac-panel">
      <header className="mdc-admin-tab-header">
        <div className="mdc-admin-panel__intro">
          <p className="mdc-chat-eyebrow">RBAC</p>
          <h2>Permissões administrativas</h2>
          <p>Capacidades do seu perfil no painel admin (curadoria, auditoria e operações sensíveis).</p>
        </div>
      </header>

      {!rbac ? (
        <p className="mdc-chat-muted">Carregando permissões administrativas...</p>
      ) : (
        <>
          <div className="mdc-admin-rbac-panel__roles">
            {rbac.roles.length === 0 ? (
              <span className="mdc-admin-badge mdc-admin-badge--muted">
                Nenhum perfil administrativo detectado
              </span>
            ) : (
              rbac.roles.map((role) => (
                <span key={role} className="mdc-admin-badge mdc-admin-badge--muted">
                  {ROLE_LABELS[role] ?? role}
                </span>
              ))
            )}

            {rbac.isSuperadmin ? (
              <span className="mdc-admin-badge mdc-admin-badge--success">Superadmin</span>
            ) : null}
          </div>

          <div className="mdc-admin-entity-list mdc-admin-rbac-panel__matrix">
            {rbac.matrix.map((item) => (
              <article key={item.key} className="mdc-admin-entity-row">
                <div className="mdc-admin-entity-row__body">
                  <div className="mdc-admin-entity-row__title-line">
                    <strong>{item.label}</strong>
                    <span
                      className={`mdc-admin-badge ${
                        item.allowed ? "mdc-admin-badge--success" : "mdc-admin-badge--danger"
                      }`}
                    >
                      {item.allowed ? "Permitido" : "Bloqueado"}
                    </span>
                  </div>
                  <p className="mdc-admin-entity-row__detail">{item.requiredPermission}</p>
                </div>
              </article>
            ))}
          </div>

          <details className="mdc-admin-rbac-panel__permissions">
            <summary>Permissões brutas</summary>
            {rbac.permissions.length === 0 ? (
              <p className="mdc-chat-muted">Nenhuma permissão retornada.</p>
            ) : (
              <ul>
                {rbac.permissions.map((permission) => (
                  <li key={permission}>{permission}</li>
                ))}
              </ul>
            )}
          </details>
        </>
      )}
    </article>
  );
}
