import {
  isPluginNavActive,
  type PluginView,
} from "./pluginRoutes.ts";
import { navigatePluginView } from "./pluginNavigation.ts";

type PluginNavProps = {
  view: PluginView;
  basePath: string;
  search?: string;
  showConfig?: boolean;
};

const BASE_ITEMS = [
  { id: "orders" as const, label: "Pedidos em aberto" },
  { id: "customers" as const, label: "Minha carteira" },
];

export function PluginNav({ view, basePath, search, showConfig = false }: PluginNavProps) {
  const items = showConfig
    ? [...BASE_ITEMS, { id: "config" as const, label: "Configuração" }]
    : BASE_ITEMS;

  return (
    <nav className="pva-plugin-nav" aria-label="Áreas do módulo">
      <div className="pva-plugin-nav__scroller" role="tablist" aria-orientation="horizontal">
        {items.map((item) => {
          const active = isPluginNavActive(view, item.id);
          return (
            <button
              key={item.id}
              type="button"
              role="tab"
              id={`pva-tab-${item.id}`}
              className={
                active ? "pva-plugin-nav__tab pva-plugin-nav__tab--active" : "pva-plugin-nav__tab"
              }
              aria-selected={active}
              aria-current={active ? "page" : undefined}
              tabIndex={active ? 0 : -1}
              onClick={() =>
                navigatePluginView(item.id, {
                  basePath,
                  search: search || undefined,
                })
              }
              onKeyDown={(event) => {
                if (event.key !== "ArrowRight" && event.key !== "ArrowLeft") return;
                event.preventDefault();
                const currentIndex = items.findIndex((entry) => entry.id === item.id);
                const delta = event.key === "ArrowRight" ? 1 : -1;
                const next = items[(currentIndex + delta + items.length) % items.length];
                if (!next) return;
                const nextButton = document.getElementById(`pva-tab-${next.id}`);
                nextButton?.focus();
                if (!isPluginNavActive(view, next.id)) {
                  navigatePluginView(next.id, {
                    basePath,
                    search: search || undefined,
                  });
                }
              }}
            >
              <span className="pva-plugin-nav__tab-label">{item.label}</span>
            </button>
          );
        })}
      </div>
    </nav>
  );
}
