import { resolveLucideIconOrFallback } from "./lucideIconResolver";

export type LucideIconGridItem = {
  /** Nome PascalCase do Lucide (ex.: Star). */
  name: string;
  label: string;
  hint?: string;
};

export type LucideIconGridPanelProps = {
  title?: string;
  items: readonly LucideIconGridItem[];
  onSelect: (pascalName: string) => void;
  columns?: 3 | 4;
  className?: string;
};

/** Grade compacta de ícones Lucide — ribbon / popover (tema via tokens delpi-ui). */
export function LucideIconGridPanel({
  title,
  items,
  onSelect,
  columns = 3,
  className,
}: LucideIconGridPanelProps) {
  const rootClass = [
    "delpi-ui-lucide-icon-grid",
    columns === 4 ? "delpi-ui-lucide-icon-grid--cols-4" : "",
    className,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div className={rootClass} role="menu">
      {title ? <h4 className="delpi-ui-lucide-icon-grid__title">{title}</h4> : null}
      <div
        className="delpi-ui-lucide-icon-grid__items"
        style={{ gridTemplateColumns: `repeat(${columns}, minmax(0, 1fr))` }}
      >
        {items.map((item) => (
          <LucideIconGridButton key={item.name} item={item} onSelect={onSelect} />
        ))}
      </div>
    </div>
  );
}

function LucideIconGridButton({
  item,
  onSelect,
}: {
  item: LucideIconGridItem;
  onSelect: (pascalName: string) => void;
}) {
  const Icon = resolveLucideIconOrFallback(item.name, item.name);

  return (
    <button
      type="button"
      role="menuitem"
      className="delpi-ui-lucide-icon-grid__item"
      title={item.hint ?? item.label}
      aria-label={item.label}
      onClick={() => onSelect(item.name)}
    >
      <span className="delpi-ui-lucide-icon-grid__icon" aria-hidden="true">
        <Icon size={22} strokeWidth={1.75} />
      </span>
      <span className="delpi-ui-lucide-icon-grid__label">{item.label}</span>
    </button>
  );
}
