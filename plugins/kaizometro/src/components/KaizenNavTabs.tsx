import { dashboardPath, listPath } from "../constants/kaizen";

type Props = {
  active: "dashboard" | "list";
  onNavigate: (path: string) => void;
};

const ITEMS: Array<{ key: "dashboard" | "list"; label: string; path: string }> = [
  { key: "dashboard", label: "Dashboard", path: dashboardPath() },
  { key: "list", label: "Cadastros", path: listPath() },
];

export function KaizenNavTabs({ active, onNavigate }: Props) {
  return (
    <nav className="kz-nav" aria-label="Navegação do módulo de kaizens">
      {ITEMS.map((item) => (
        <button
          key={item.key}
          type="button"
          className={`kz-nav__link${active === item.key ? " kz-nav__link--active" : ""}`}
          aria-current={active === item.key ? "page" : undefined}
          onClick={() => onNavigate(item.path)}
        >
          {item.label}
        </button>
      ))}
    </nav>
  );
}
