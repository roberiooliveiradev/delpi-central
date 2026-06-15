import { PRODUCTION_ROUTES } from "../constants/routes";
import type { ProductionFilterUrlState } from "../utils/filterUrl";
import { appendFiltersToPath, readProductionFilters } from "../utils/filterUrl";
import { navigateProduction } from "../utils/navigation";

type ProductionNavProps = {
  currentPath?: string;
  filterState?: ProductionFilterUrlState;
};

const NAV_ITEMS = [
  { path: PRODUCTION_ROUTES.home, label: "Visão geral" },
  { path: PRODUCTION_ROUTES.otd, label: "OTD produção" },
] as const;

function isActive(path: string, currentPath?: string): boolean {
  if (!currentPath) return path === PRODUCTION_ROUTES.home;
  if (path === PRODUCTION_ROUTES.home) {
    return currentPath === path || currentPath === `${path}/`;
  }
  return currentPath === path || currentPath.startsWith(`${path}/`);
}

export function ProductionNav({ currentPath, filterState }: ProductionNavProps) {
  const filters = filterState ?? readProductionFilters();

  return (
    <nav className="dp-nav" aria-label="Navegação do dashboard de produção">
      {NAV_ITEMS.map((item) => (
        <a
          key={item.path}
          href={appendFiltersToPath(item.path, filters)}
          className={`dp-nav__link${isActive(item.path, currentPath) ? " dp-nav__link--active" : ""}`}
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
            navigateProduction(item.path, filters);
          }}
        >
          {item.label}
        </a>
      ))}
    </nav>
  );
}
