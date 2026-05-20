import { ENGINEERING_BASE_PATH } from "../constants/routes";
import type { EngineeringFilterUrlState } from "../utils/filterUrl";
import { appendFiltersToPath } from "../utils/filterUrl";
import { navigateEngineering } from "../utils/navigation";

type ModuleShortcutProps = {
  title: string;
  description: string;
  href: string;
  filterState?: EngineeringFilterUrlState;
  /** Navegação para outro app do portal (ex.: dashboard LMPs). */
  external?: boolean;
};

export function ModuleShortcut({
  title,
  description,
  href,
  filterState,
  external = false,
}: ModuleShortcutProps) {
  const isInternal = !external && href.startsWith(ENGINEERING_BASE_PATH);
  const resolvedHref = filterState && isInternal
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

        if (!isInternal) {
          return;
        }

        event.preventDefault();
        navigateEngineering(href, filterState);
      }}
    >
      <h3 className="ds-module-shortcut__title">{title}</h3>
      <p className="ds-module-shortcut__description">{description}</p>
    </a>
  );
}
