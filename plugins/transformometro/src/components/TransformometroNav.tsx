import { PORTAL_NAV_LINKS, isPortalNavActive } from "../constants/portalExperience";

type TransformometroNavProps = {
  currentPath?: string;
  onNavigate: (path: string) => void;
};

export function TransformometroNav({ currentPath, onNavigate }: TransformometroNavProps) {
  return (
    <nav className="ds-nav" aria-label="Navegação do Portal Transforma+">
      {PORTAL_NAV_LINKS.map((link) => {
        const active = isPortalNavActive(link.path, currentPath);
        return (
          <a
            key={link.path}
            href={link.path}
            className={`ds-nav__link${active ? " ds-nav__link--active" : ""}`}
            aria-current={active ? "page" : undefined}
            onClick={(event) => {
              if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
              event.preventDefault();
              onNavigate(link.path);
            }}
          >
            {link.label}
          </a>
        );
      })}
    </nav>
  );
}
