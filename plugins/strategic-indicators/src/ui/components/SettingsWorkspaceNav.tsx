import "./SettingsWorkspaceNav.css";

type SettingsWorkspaceNavItem = {
  id: string;
  label: string;
};

type SettingsWorkspaceNavProps = {
  items: SettingsWorkspaceNavItem[];
};

export function SettingsWorkspaceNav({
  items,
}: SettingsWorkspaceNavProps) {
  function navigateToSection(id: string) {
    const element = document.getElementById(id);
    if (!element) return;

    element.scrollIntoView({
      behavior: "smooth",
      block: "start",
    });
  }

  return (
    <nav className="si-settings-workspace-nav" aria-label="Navegação administrativa">
      <div className="si-settings-workspace-nav__list">
        {items.map((item) => (
          <button
            key={item.id}
            type="button"
            className="si-settings-workspace-nav__item"
            onClick={() => navigateToSection(item.id)}
          >
            {item.label}
          </button>
        ))}
      </div>
    </nav>
  );
}