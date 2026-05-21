type ModuleShortcutProps = {
  title: string;
  description: string;
  path: string;
  onNavigate: (path: string) => void;
};

export function ModuleShortcut({ title, description, path, onNavigate }: ModuleShortcutProps) {
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
      <h3 className="ds-module-shortcut__title">{title}</h3>
      <p className="ds-module-shortcut__description">{description}</p>
    </a>
  );
}
