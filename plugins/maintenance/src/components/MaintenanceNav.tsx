import { MAINTENANCE_ROUTES } from "../constants/routes";

type MaintenanceNavProps = {
  currentPath?: string;
  onNavigate: (path: string) => void;
};

const LINKS = [
  { path: MAINTENANCE_ROUTES.home, label: "Início" },
  { path: MAINTENANCE_ROUTES.miniAplicadores, label: "Mini-aplicadores" },
  { path: MAINTENANCE_ROUTES.relatorio, label: "Relatório preventivo" },
  { path: MAINTENANCE_ROUTES.configuracao, label: "Configuração" },
];

export function MaintenanceNav({ currentPath, onNavigate }: MaintenanceNavProps) {
  return (
    <nav className="dm-nav" aria-label="Navegação do módulo Manutenção">
      {LINKS.map((link) => {
        const active = currentPath === link.path;
        return (
          <button
            key={link.path}
            type="button"
            className={`dm-nav__link${active ? " is-active" : ""}`}
            onClick={() => onNavigate(link.path)}
          >
            {link.label}
          </button>
        );
      })}
    </nav>
  );
}
