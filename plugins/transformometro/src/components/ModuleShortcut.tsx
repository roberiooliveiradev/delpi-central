import type { ReactNode } from "react";

type ModuleShortcutProps = {
  title: string;
  description: string;
  path: string;
  onNavigate: (path: string) => void;
  icon?: ReactNode;
};

export function ModuleShortcut({
  title,
  description,
  path,
  onNavigate,
  icon,
}: ModuleShortcutProps) {
  return (
    <a
      href={path}
      className="ds-card ds-module-shortcut ds-module-shortcut--link"
      onClick={(event) => {
        if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
        event.preventDefault();
        onNavigate(path);
      }}
    >
      {icon ? (
        <span className="ds-module-shortcut__icon" aria-hidden="true">
          {icon}
        </span>
      ) : null}
      <h3 className="ds-module-shortcut__title">{title}</h3>
      <p className="ds-module-shortcut__description">{description}</p>
    </a>
  );
}
