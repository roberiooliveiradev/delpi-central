import { ModuleHomeNavButton } from "./ModuleHomeNavButton";
import { MAINTENANCE_ROUTES } from "../constants/routes";
import { normalizeMaintenancePath, RESERVED_MINI_SEGMENTS } from "../utils/routeParser";

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

function isToolDetailPath(currentPath: string | undefined): boolean {
  const path = normalizeMaintenancePath(currentPath ?? "");
  const detailMatch = path.match(/^\/apps\/maintenance\/mini-aplicadores\/([^/]+)$/);
  return Boolean(detailMatch && !RESERVED_MINI_SEGMENTS.has(detailMatch[1]));
}

function isActive(currentPath: string | undefined, linkPath: string): boolean {
  const path = normalizeMaintenancePath(currentPath ?? "");

  if (linkPath === MAINTENANCE_ROUTES.miniAplicadores) {
    if (path === linkPath) return true;
    const detailMatch = path.match(/^\/apps\/maintenance\/mini-aplicadores\/([^/]+)$/);
    return Boolean(detailMatch && !RESERVED_MINI_SEGMENTS.has(detailMatch[1]));
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
  const onDetailPage = isToolDetailPath(currentPath);
  const backLabel = onDetailPage ? "Voltar" : "Início";
  const backPath = onDetailPage ? MAINTENANCE_ROUTES.miniAplicadores : moduleHomePath;

  return (
    <nav className="dm-nav dm-nav--submodule" aria-label="Navegação mini-aplicadores">
      <ModuleHomeNavButton
        label={backLabel}
        targetPath={backPath}
        onNavigate={onNavigate}
        variant={onDetailPage ? "back" : "home"}
      />
      <div className="dm-nav__tabs" role="tablist" aria-label="Abas do submódulo">
        {links.map((link) => {
          const active = isActive(currentPath, link.path);
          return (
            <button
              key={link.path}
              type="button"
              role="tab"
              aria-selected={active}
              className={`dm-nav__link${active ? " is-active" : ""}`}
              onClick={() => onNavigate(link.path)}
            >
              {link.label}
            </button>
          );
        })}
      </div>
    </nav>
  );
}
