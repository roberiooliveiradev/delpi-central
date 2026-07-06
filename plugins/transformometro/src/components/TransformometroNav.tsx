import { TRANSFORMOMETRO_ROUTES } from "../constants/routes";

type TransformometroNavProps = {
  currentPath?: string;
  onNavigate: (path: string) => void;
};

/** Alinhado ao manifest (routes showInMenu) e ao menu lateral do portal. */
const LINKS = [
  { path: TRANSFORMOMETRO_ROUTES.dashboard, label: "Dashboard" },
  { path: TRANSFORMOMETRO_ROUTES.processos, label: "Processos" },
  { path: TRANSFORMOMETRO_ROUTES.filiais, label: "Unidades" },
  { path: TRANSFORMOMETRO_ROUTES.setores, label: "Departamentos" },
  { path: TRANSFORMOMETRO_ROUTES.recursos, label: "Recursos" },
  { path: TRANSFORMOMETRO_ROUTES.dados, label: "Exportar / Importar" },
] as const;

function isActive(path: string, currentPath?: string): boolean {
  if (!currentPath) {
    return path === TRANSFORMOMETRO_ROUTES.dashboard;
  }
  if (path === TRANSFORMOMETRO_ROUTES.dashboard) {
    return (
      currentPath === path ||
      currentPath === TRANSFORMOMETRO_ROUTES.home ||
      currentPath === "/apps/transformometro"
    );
  }
  if (path === TRANSFORMOMETRO_ROUTES.processos) {
    return (
      currentPath === path ||
      currentPath.startsWith(`${path}/`)
    );
  }
  return currentPath === path || currentPath.startsWith(`${path}/`);
}

export function TransformometroNav({ currentPath, onNavigate }: TransformometroNavProps) {
  return (
    <nav className="ds-nav" aria-label="Navegação Transformômetro">
      {LINKS.map((link) => (
        <a
          key={link.path}
          href={link.path}
          className={`ds-nav__link${isActive(link.path, currentPath) ? " ds-nav__link--active" : ""}`}
          aria-current={isActive(link.path, currentPath) ? "page" : undefined}
          onClick={(event) => {
            if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
            event.preventDefault();
            onNavigate(link.path);
          }}
        >
          {link.label}
        </a>
      ))}
    </nav>
  );
}
