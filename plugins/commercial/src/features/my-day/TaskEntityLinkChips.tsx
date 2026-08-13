import type { ReactNode } from "react";

type TaskEntityLinkChip = {
  key: string;
  label: string;
  onOpen: () => void;
};

type TaskEntityLinkChipsProps = {
  items: TaskEntityLinkChip[];
  ariaLabel: string;
};

/** Chips clicáveis (kit tag-chip) para responsáveis/clientes no card da tarefa. */
export function TaskEntityLinkChips({
  items,
  ariaLabel,
}: TaskEntityLinkChipsProps): ReactNode {
  if (items.length === 0) return null;
  return (
    <div className="cm-task-link-chips" role="group" aria-label={ariaLabel}>
      {items.map((item) => (
        <button
          key={item.key}
          type="button"
          className="delpi-ui-tag-chip"
          onClick={item.onOpen}
        >
          {item.label}
        </button>
      ))}
    </div>
  );
}
