import { SUPPLIES_ROUTES } from "../constants/routes";
import type { SuppliesFilterUrlState } from "../utils/filterUrl";
import { appendFiltersToPath, readSuppliesFilters } from "../utils/filterUrl";
import { navigateSupplies } from "../utils/navigation";

type SuppliesNavProps = {
  currentPath?: string;
  filterState?: SuppliesFilterUrlState;
};

const NAV_ITEMS = [
  { path: SUPPLIES_ROUTES.home, label: "Visão geral" },
  { path: SUPPLIES_ROUTES.cpv, label: "CPV" },
  { path: SUPPLIES_ROUTES.otd, label: "OTD compras" },
  { path: SUPPLIES_ROUTES.stock, label: "Estoque" },
  { path: SUPPLIES_ROUTES.inventoryTurnover, label: "Giro IDD" },
] as const;

function isActive(path: string, currentPath?: string): boolean {
  if (!currentPath) return path === SUPPLIES_ROUTES.home;
  if (path === SUPPLIES_ROUTES.home) {
    return currentPath === path || currentPath === `${path}/`;
  }
  return currentPath === path || currentPath.startsWith(`${path}/`);
}

export function SuppliesNav({ currentPath, filterState }: SuppliesNavProps) {
  const filters = filterState ?? readSuppliesFilters();

  return (
    <nav className="ds-nav" aria-label="Navegação do dashboard de suprimentos">
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
            navigateSupplies(item.path, filters);
          }}
        >
          {item.label}
        </a>
      ))}
    </nav>
  );
}
