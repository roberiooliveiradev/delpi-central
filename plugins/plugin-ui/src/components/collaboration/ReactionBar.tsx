import { delpiUiClass } from "../../utils/delpiUiClass";

export type ReactionBarItem = {
  code: string;
  label: string;
  count: number;
  reactedByMe?: boolean;
};

export type ReactionBarClassNames = {
  root: string;
  chip: string;
  chipActive: string;
  count: string;
  add: string;
};

export type ReactionBarProps = {
  items: readonly ReactionBarItem[];
  classNames: ReactionBarClassNames;
  /** Codes the host allows to add (shown as secondary chips). */
  availableCodes?: readonly { code: string; label: string }[];
  onToggle?: (code: string) => void;
  onAdd?: (code: string) => void;
  addAriaLabel?: string;
  listAriaLabel: string;
  className?: string;
};

export function reactionBarBemClasses(prefix: string): ReactionBarClassNames {
  const base = `${prefix}-reaction-bar`;
  const ui = "delpi-ui-reaction-bar";
  const pair = (local: string, canonical: string) => delpiUiClass(local, canonical);
  return {
    root: pair(base, ui),
    chip: pair(`${base}__chip`, `${ui}__chip`),
    chipActive: pair(
      `${base}__chip ${base}__chip--active`,
      `${ui}__chip ${ui}__chip--active`,
    ),
    count: pair(`${base}__count`, `${ui}__count`),
    add: pair(`${base}__add`, `${ui}__add`),
  };
}

/**
 * Reaction chips. Codes and labels come from the host catalog.
 */
export function ReactionBar({
  items,
  classNames,
  availableCodes = [],
  onToggle,
  onAdd,
  addAriaLabel,
  listAriaLabel,
  className,
}: ReactionBarProps) {
  const rootClass = [classNames.root, className].filter(Boolean).join(" ");
  const unused = availableCodes.filter(
    (opt) => !items.some((item) => item.code === opt.code),
  );

  return (
    <div className={rootClass} role="group" aria-label={listAriaLabel}>
      {items.map((item) => (
        <button
          key={item.code}
          type="button"
          className={item.reactedByMe ? classNames.chipActive : classNames.chip}
          aria-pressed={Boolean(item.reactedByMe)}
          aria-label={item.label}
          disabled={!onToggle}
          onClick={() => onToggle?.(item.code)}
        >
          <span>{item.label}</span>
          {item.count > 0 ? (
            <span className={classNames.count}>{item.count}</span>
          ) : null}
        </button>
      ))}
      {onAdd && unused.length > 0 && addAriaLabel
        ? unused.map((opt) => (
            <button
              key={`add-${opt.code}`}
              type="button"
              className={classNames.add}
              aria-label={`${addAriaLabel}: ${opt.label}`}
              onClick={() => onAdd(opt.code)}
            >
              {opt.label}
            </button>
          ))
        : null}
    </div>
  );
}

export type DashboardReactionBarProps = Omit<ReactionBarProps, "classNames">;

export function createDashboardReactionBar(prefix: string) {
  const classNames = reactionBarBemClasses(prefix);
  return function DashboardReactionBar(props: DashboardReactionBarProps) {
    return <ReactionBar classNames={classNames} {...props} />;
  };
}
