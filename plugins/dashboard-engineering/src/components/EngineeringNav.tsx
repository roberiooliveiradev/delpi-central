import { ENGINEERING_ROUTES } from "../constants/routes";
import type { EngineeringFilterUrlState } from "../utils/filterUrl";
import { appendFiltersToPath, readEngineeringFilters } from "../utils/filterUrl";
import { navigateEngineering } from "../utils/navigation";

type EngineeringNavProps = {
  currentPath?: string;
  filterState?: EngineeringFilterUrlState;
};

const NAV_ITEMS = [
  { path: ENGINEERING_ROUTES.home, label: "Visão geral" },
  { path: ENGINEERING_ROUTES.lmp, label: "LMPs no prazo" },
  { path: ENGINEERING_ROUTES.transforma, label: "TRANSFORMA+" },
] as const;

function isActive(path: string, currentPath?: string): boolean {
  if (!currentPath) return path === ENGINEERING_ROUTES.home;
  if (path === ENGINEERING_ROUTES.home) {
    return currentPath === path || currentPath === `${path}/`;
  }
  return currentPath === path || currentPath.startsWith(`${path}/`);
}

export function EngineeringNav({ currentPath, filterState }: EngineeringNavProps) {
  const filters = filterState ?? readEngineeringFilters();

  return (
    <nav className="ds-nav" aria-label="Navegação do dashboard de engenharia">
      {NAV_ITEMS.map((item) => (
        <a
          key={item.path}
          href={appendFiltersToPath(item.path, filters)}
          className={`ds-nav__link${isActive(item.path, currentPath) ? " ds-nav__link--active" : ""}`}
          aria-current={isActive(item.path, currentPath) ? "page" : undefined}
          onClick={(event) => {
            if (
              event.metaKey ||
              event.ctrlKey ||
              event.shiftKey ||
              event.altKey ||
              event.button !== 0
            ) {
              return;
            }

            event.preventDefault();
            navigateEngineering(item.path, filters);
          }}
        >
          {item.label}
        </a>
      ))}
    </nav>
  );
}
