import { ArrowLeft } from "lucide-react";

import { MAINTENANCE_ROUTES } from "../constants/routes";
import { normalizeMaintenancePath } from "../utils/routeParser";

type MiniAplicadoresNavProps = {
  currentPath?: string;
  moduleHomePath: string;
  showConfiguration?: boolean;
  onNavigate: (path: string) => void;
};

const BASE_LINKS = [
  { path: MAINTENANCE_ROUTES.miniAplicadores, label: "Ferramentas" },
  { path: MAINTENANCE_ROUTES.miniAplicadoresRelatorio, label: "Relatório preventivo" },
];

const CONFIG_LINK = {
  path: MAINTENANCE_ROUTES.miniAplicadoresConfiguracao,
  label: "Configuração",
};

function isActive(currentPath: string | undefined, linkPath: string): boolean {
  const path = normalizeMaintenancePath(currentPath ?? "");
  if (linkPath === MAINTENANCE_ROUTES.miniAplicadores) {
    return path === linkPath || /^\/apps\/maintenance\/mini-aplicadores\/[^/]+$/.test(path);
  }
  return path === linkPath;
}

export function MiniAplicadoresNav({
  currentPath,
  moduleHomePath,
  showConfiguration = false,
  onNavigate,
}: MiniAplicadoresNavProps) {
  const links = showConfiguration ? [...BASE_LINKS, CONFIG_LINK] : BASE_LINKS;

  return (
    <nav className="dm-nav dm-nav--submodule" aria-label="Navegação mini-aplicadores">
      <button
        type="button"
        className="dm-nav__link dm-nav__link--back"
        onClick={() => onNavigate(moduleHomePath)}
      >
        <ArrowLeft size={14} aria-hidden="true" />
        Manutenção
      </button>
      {links.map((link) => {
        const active = isActive(currentPath, link.path);
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
