import { QUALITY_ROUTES } from "../constants/routes";

type QualityNavProps = {
  currentPath?: string;
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

export function QualityNav({ currentPath }: QualityNavProps) {
  return (
    <nav className="dq-nav" aria-label="Navegação do dashboard de qualidade">
      {NAV_ITEMS.map((item) => (
        <a
          key={item.path}
          href={item.path}
          className={`dq-nav__link${isActive(item.path, currentPath) ? " dq-nav__link--active" : ""}`}
          aria-current={isActive(item.path, currentPath) ? "page" : undefined}
        >
          {item.label}
        </a>
      ))}
    </nav>
  );
}
