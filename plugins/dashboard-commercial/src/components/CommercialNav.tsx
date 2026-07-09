import { COMMERCIAL_ROUTES } from "../constants/routes";
import type { CommercialFilterUrlState } from "../utils/filterUrl";
import { appendFiltersToPath, readCommercialFilters } from "../utils/filterUrl";
import { navigateCommercial } from "../utils/navigation";

type CommercialNavProps = {
  currentPath?: string;
  filterState?: CommercialFilterUrlState;
};

const NAV_ITEMS = [
  { path: COMMERCIAL_ROUTES.home, label: "Visão geral" },
  { path: COMMERCIAL_ROUTES.salesOrderOtd, label: "OTD pedidos de venda" },
] as const;

function isActive(path: string, currentPath?: string): boolean {
  if (!currentPath) return path === COMMERCIAL_ROUTES.home;
  if (path === COMMERCIAL_ROUTES.home) {
    return currentPath === path || currentPath === `${path}/`;
  }
  return currentPath === path || currentPath.startsWith(`${path}/`);
}

export function CommercialNav({ currentPath, filterState }: CommercialNavProps) {
  const filters = filterState ?? readCommercialFilters();

  return (
    <nav className="dc-nav" aria-label="Navegação do dashboard comercial">
      {NAV_ITEMS.map((item) => (
        <a
          key={item.path}
          href={appendFiltersToPath(item.path, filters)}
          className={`dc-nav__link${isActive(item.path, currentPath) ? " dc-nav__link--active" : ""}`}
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
            navigateCommercial(item.path, filters);
          }}
        >
          {item.label}
        </a>
      ))}
    </nav>
  );
}
