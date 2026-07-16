import type { ReactNode } from "react";

type FloatChecklistProps = {
  "aria-label": string;
  children: ReactNode;
};

/** Menu checklist do float (+ / pincel) — chrome próprio (paridade com td-chart-add-element). */
export function FloatChecklist({ "aria-label": ariaLabel, children }: FloatChecklistProps) {
  return (
    <div className="td-float-checklist" role="group" aria-label={ariaLabel}>
      {children}
    </div>
  );
}

type FloatChecklistItemProps = {
  label: string;
  active?: boolean;
  title?: string;
  disabled?: boolean;
  onClick: () => void;
};

export function FloatChecklistItem({
  label,
  active = false,
  title,
  disabled = false,
  onClick,
}: FloatChecklistItemProps) {
  return (
    <button
      type="button"
      role="menuitemcheckbox"
      aria-checked={active}
      title={title}
      disabled={disabled}
      className={[
        "td-deck-ribbon__cascade-item",
        "td-float-checklist__item",
        active ? "td-float-checklist__item--on" : "",
      ]
        .filter(Boolean)
        .join(" ")}
      onClick={onClick}
    >
      <span className="td-float-checklist__mark" aria-hidden="true">
        {active ? "✓" : ""}
      </span>
      <span className="td-float-checklist__label">{label}</span>
    </button>
  );
}
