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
    <article className="mdc-admin-rbac-panel">
      <div>
        <p className="mdc-chat-eyebrow">RBAC</p>
        <h2>Permissões administrativas</h2>
      </div>

      {!rbac ? (
        <p className="mdc-chat-muted">Carregando permissões administrativas...</p>
      ) : (
        <>
          <div className="mdc-admin-rbac-panel__roles">
            {rbac.roles.length === 0 ? (
              <span>Nenhum perfil administrativo detectado.</span>
            ) : (
              rbac.roles.map((role) => (
                <span key={role}>{ROLE_LABELS[role] ?? role}</span>
              ))
            )}

            {rbac.isSuperadmin ? <strong>Superadmin</strong> : null}
          </div>

          <div className="mdc-admin-rbac-panel__matrix">
            {rbac.matrix.map((item) => (
              <section key={item.key}>
                <div>
                  <strong>{item.label}</strong>
                  <small>{item.requiredPermission}</small>
                </div>

                <span className={item.allowed ? "is-allowed" : "is-denied"}>
                  {item.allowed ? "Permitido" : "Bloqueado"}
                </span>
              </section>
            ))}
          </div>

          <details className="mdc-admin-rbac-panel__permissions">
            <summary>Permissões brutas</summary>
            {rbac.permissions.length === 0 ? (
              <p>Nenhuma permissão retornada.</p>
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
