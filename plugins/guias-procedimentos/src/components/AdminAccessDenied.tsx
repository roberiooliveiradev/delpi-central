import { ModuleHeader } from "./ModuleHeader";
import { navigateGuiasProcedimentos } from "../utils/navigation";
import { GUIAS_PROCEDIMENTOS_ROUTES } from "../utils/route";

type AdminAccessDeniedProps = {
  standalone?: boolean;
  message?: string;
};

export function AdminAccessDenied({
  standalone = false,
  message = "Você não tem permissão para administrar este módulo.",
}: AdminAccessDeniedProps) {
  return (
    <div className="dashboard-guias-procedimentos gp-page">
      <div className="gp-shell">
        <ModuleHeader showThemeToggle={standalone} />
        <p className="gp-feedback gp-feedback--error" role="alert">
          {message}
        </p>
        <button
          type="button"
          className="gp-btn gp-btn--secondary"
          onClick={() =>
            navigateGuiasProcedimentos(GUIAS_PROCEDIMENTOS_ROUTES.home)
          }
        >
          Voltar aos guias
        </button>
      </div>
    </div>
  );
}
