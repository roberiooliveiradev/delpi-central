import { QUALITY_ROUTES } from "../constants/routes";
import { navigateQuality } from "../utils/navigation";

type ModuleShortcutProps = {
  title: string;
  description: string;
  phase?: string;
  href?: string;
};

export function ModuleShortcut({
  title,
  description,
  phase,
  href,
}: ModuleShortcutProps) {
  const className = `dq-card dq-module-shortcut${href ? " dq-module-shortcut--link" : ""}`;

  const content = (
    <>
      {phase ? <span className="dq-module-shortcut__phase">{phase}</span> : null}
      <h3 className="dq-module-shortcut__title">{title}</h3>
      <p className="dq-module-shortcut__description">{description}</p>
    </>
  );

  if (href) {
    return (
      <a
        href={href}
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
          navigateQuality(href);
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
