import { FINANCIAL_ROUTES } from "../constants/routes";
import type { FinancialFilterUrlState } from "../utils/filterUrl";
import { appendFiltersToPath, readFinancialFilters } from "../utils/filterUrl";
import { navigateFinancial } from "../utils/navigation";

type FinancialNavProps = {
  currentPath?: string;
  filterState?: FinancialFilterUrlState;
};

const NAV_ITEMS = [
  { path: FINANCIAL_ROUTES.home, label: "Visão geral" },
  { path: FINANCIAL_ROUTES.rol, label: "ROL" },
  { path: FINANCIAL_ROUTES.ebitda, label: "EBITDA" },
  { path: FINANCIAL_ROUTES.fixedCost, label: "Custos fixos" },
  { path: FINANCIAL_ROUTES.pmr, label: "PMR" },
] as const;

function isActive(path: string, currentPath?: string): boolean {
  if (!currentPath) return path === FINANCIAL_ROUTES.home;
  if (path === FINANCIAL_ROUTES.home) {
    return currentPath === path || currentPath === `${path}/`;
  }
  return currentPath === path || currentPath.startsWith(`${path}/`);
}

export function FinancialNav({ currentPath, filterState }: FinancialNavProps) {
  const filters = filterState ?? readFinancialFilters();

  return (
    <nav className="ds-nav" aria-label="Navegação do dashboard financeiro">
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
            navigateFinancial(item.path, filters);
          }}
        >
          {item.label}
        </a>
      ))}
    </nav>
  );
}
