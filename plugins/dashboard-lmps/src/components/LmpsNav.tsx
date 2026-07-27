import { LMPS_ROUTES } from "../constants/routes";
import type { LmpsFilterUrlState } from "../utils/filterUrl";
import { appendFiltersToPath, readLmpsFilters } from "../utils/filterUrl";
import { navigateLmps } from "../utils/navigation";

type LmpsNavProps = {
  currentPath?: string;
  filterState?: LmpsFilterUrlState;
};

const NAV_ITEMS = [
  { path: LMPS_ROUTES.home, label: "Dashboard" },
  { path: LMPS_ROUTES.nonconformities, label: "Registro de não conformidades" },
] as const;

function isActive(path: string, currentPath?: string): boolean {
  if (!currentPath) return path === LMPS_ROUTES.home;
  if (path === LMPS_ROUTES.home) {
    return currentPath === path || currentPath === `${path}/`;
  }
  return currentPath === path || currentPath.startsWith(`${path}/`);
}

export function LmpsNav({ currentPath, filterState }: LmpsNavProps) {
  const filters = filterState ?? readLmpsFilters();

  return (
    <nav className="lmps-nav" aria-label="Navegação do dashboard LMPs">
      {NAV_ITEMS.map((item) => (
        <a
          key={item.path}
          href={appendFiltersToPath(item.path, filters)}
          className={`lmps-nav__link${isActive(item.path, currentPath) ? " lmps-nav__link--active" : ""}`}
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
            navigateLmps(item.path, filters);
          }}
        >
          {item.label}
        </a>
      ))}
    </nav>
  );
}
