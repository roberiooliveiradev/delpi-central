import { QUALITY_ROUTES } from "../constants/routes";
import type { QualityFilterUrlState } from "../utils/filterUrl";
import { appendFiltersToPath, readQualityFilters } from "../utils/filterUrl";
import { navigateQuality } from "../utils/navigation";

type QualityNavProps = {
  currentPath?: string;
  filterState?: QualityFilterUrlState;
};

const NAV_ITEMS = [
  { path: QUALITY_ROUTES.home, label: "Visão geral" },
  { path: QUALITY_ROUTES.ppm, label: "PPM" },
  { path: QUALITY_ROUTES.nonconformities, label: "NC TOTVS" },
  { path: QUALITY_ROUTES.kaizen, label: "Kaizen" },
  { path: QUALITY_ROUTES.audit5s, label: "5S" },
] as const;

function isActive(path: string, currentPath?: string): boolean {
  if (!currentPath) return path === QUALITY_ROUTES.home;
  if (path === QUALITY_ROUTES.home) {
    return currentPath === path || currentPath === `${path}/`;
  }
  return currentPath === path || currentPath.startsWith(`${path}/`);
}

export function QualityNav({ currentPath, filterState }: QualityNavProps) {
  const filters = filterState ?? readQualityFilters();

  return (
    <nav className="dq-nav" aria-label="Navegação do dashboard de qualidade">
      {NAV_ITEMS.map((item) => (
        <a
          key={item.path}
          href={appendFiltersToPath(item.path, filters)}
          className={`dq-nav__link${isActive(item.path, currentPath) ? " dq-nav__link--active" : ""}`}
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
            navigateQuality(item.path, filters);
          }}
        >
          {item.label}
        </a>
      ))}
    </nav>
  );
}
