import "./AdminShellAlerts.css";

type AdminShellAlertsProps = {
  error: string | null;
  successMessage: string | null;
};

export function AdminShellAlerts({ error, successMessage }: AdminShellAlertsProps) {
  return (
    <>
      {error ? (
        <div className="mdc-admin-shell-alert" role="alert">
          {error}
        </div>
      ) : null}

      {successMessage ? (
        <div
          className="mdc-admin-shell-alert mdc-admin-shell-alert--success"
          role="status"
        >
          {successMessage}
        </div>
      ) : null}
    </>
  );
}
