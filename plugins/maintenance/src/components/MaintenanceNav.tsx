import { ModuleHomeNavButton } from "./ModuleHomeNavButton";
import { resolveMaintenanceHomePath } from "../utils/routeParser";

type MaintenanceNavProps = {
  filialScope?: string;
  onNavigate: (path: string) => void;
};

export function MaintenanceNav({ filialScope, onNavigate }: MaintenanceNavProps) {
  const homePath = resolveMaintenanceHomePath(filialScope);

  return (
    <nav className="dm-nav dm-nav--submodule" aria-label="Navegação do módulo Manutenção">
      <ModuleHomeNavButton label="Início" targetPath={homePath} onNavigate={onNavigate} />
    </nav>
  );
}
