import { MAINTENANCE_ROUTES } from "../constants/routes";
import { resolveMaintenanceHomePath } from "../utils/routeParser";

type MaintenanceNavProps = {
  currentPath?: string;
  filialScope?: string;
  onNavigate: (path: string) => void;
};

export function MaintenanceNav({ currentPath, filialScope, onNavigate }: MaintenanceNavProps) {
  const homePath = resolveMaintenanceHomePath(filialScope);
  const active = currentPath === homePath || currentPath === MAINTENANCE_ROUTES.home;

  return (
    <nav className="dm-nav" aria-label="Navegação do módulo Manutenção">
      <button
        type="button"
        className={`dm-nav__link${active ? " is-active" : ""}`}
        onClick={() => onNavigate(homePath)}
      >
        Início
      </button>
    </nav>
  );
}
