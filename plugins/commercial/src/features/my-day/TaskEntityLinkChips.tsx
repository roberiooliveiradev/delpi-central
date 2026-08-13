import type { ReactNode } from "react";

export type TaskEntityLinkChip = {
  key: string;
  label: string;
  /** Linha secundária (ex.: código/loja do cliente). */
  subtitle?: string;
  avatar?: ReactNode;
  onOpen: () => void;
};

type TaskEntityLinkChipsProps = {
  items: TaskEntityLinkChip[];
  ariaLabel: string;
};

/**
 * Chips clicáveis com avatar opcional (kit tag-chip) para responsáveis/clientes no card.
 * Nome/subtitle → `onOpen`; foto no avatar → lightbox do kit (stopPropagation).
 */
export function TaskEntityLinkChips({
  items,
  ariaLabel,
}: TaskEntityLinkChipsProps): ReactNode {
  if (items.length === 0) return null;
  return (
    <div className="cm-task-link-chips" role="group" aria-label={ariaLabel}>
      {items.map((item) => (
        <div key={item.key} className="cm-task-link-chip">
          {item.avatar ? (
            <span className="cm-task-link-chip__avatar">{item.avatar}</span>
          ) : null}
          <button
            type="button"
            className="delpi-ui-tag-chip cm-task-link-chip__label"
            onClick={item.onOpen}
          >
            <span className="cm-task-link-chip__name">{item.label}</span>
            {item.subtitle ? (
              <span className="cm-task-link-chip__subtitle">{item.subtitle}</span>
            ) : null}
          </button>
        </div>
      ))}
    </div>
  );
}
