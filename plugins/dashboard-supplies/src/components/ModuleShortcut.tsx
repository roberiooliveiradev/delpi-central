import type { SuppliesFilterUrlState } from "../utils/filterUrl";
import { appendFiltersToPath } from "../utils/filterUrl";
import { navigateSupplies } from "../utils/navigation";

type ModuleShortcutProps = {
  title: string;
  description: string;
  href: string;
  filterState?: SuppliesFilterUrlState;
};

export function ModuleShortcut({
  title,
  description,
  href,
  filterState,
}: ModuleShortcutProps) {
  const resolvedHref = filterState
    ? appendFiltersToPath(href, filterState)
    : href;

  return (
    <a
      href={resolvedHref}
      className="ds-card ds-module-shortcut ds-module-shortcut--link"
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
        if (filterState) {
          navigateSupplies(href, filterState);
        }
      }}
    >
      <h3 className="ds-module-shortcut__title">{title}</h3>
      <p className="ds-module-shortcut__description">{description}</p>
    </a>
  );
}
