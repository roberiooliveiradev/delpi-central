type ModuleShortcutProps = {
  title: string;
  description: string;
  phase: string;
};

export function ModuleShortcut({ title, description, phase }: ModuleShortcutProps) {
  return (
    <article className="dq-card dq-module-shortcut" aria-disabled="true">
      <span className="dq-module-shortcut__phase">{phase}</span>
      <h3 className="dq-module-shortcut__title">{title}</h3>
      <p className="dq-module-shortcut__description">{description}</p>
    </article>
  );
}
