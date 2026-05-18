import { QUALITY_ROUTES } from "../constants/routes";
import type { QualityFilterUrlState } from "../utils/filterUrl";
import { appendFiltersToPath } from "../utils/filterUrl";
import { navigateQuality } from "../utils/navigation";

type ModuleShortcutProps = {
  title: string;
  description: string;
  phase?: string;
  href?: string;
  filterState?: QualityFilterUrlState;
};

export function ModuleShortcut({
  title,
  description,
  phase,
  href,
  filterState,
}: ModuleShortcutProps) {
  const resolvedHref =
    href && filterState ? appendFiltersToPath(href, filterState) : href;

  const className = `dq-card dq-module-shortcut${resolvedHref ? " dq-module-shortcut--link" : ""}`;

  const content = (
    <>
      {phase ? <span className="dq-module-shortcut__phase">{phase}</span> : null}
      <h3 className="dq-module-shortcut__title">{title}</h3>
      <p className="dq-module-shortcut__description">{description}</p>
    </>
  );

  if (resolvedHref) {
    return (
      <a
        href={resolvedHref}
        className={className}
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
          navigateQuality(href ?? "", filterState);
        }}
      >
        {content}
      </a>
    );
  }

  return (
    <article className={className} aria-disabled="true">
      {content}
    </article>
  );
}

export const PPM_SHORTCUT_HREF = QUALITY_ROUTES.ppm;
