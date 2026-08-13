import type { ReactNode } from "react";

export type TaskEntityLinkChip = {
  key: string;
  label: string;
  /** Linha secundária (e-mail do usuário ou código/loja do cliente). */
  subtitle?: string;
  avatar?: ReactNode;
  /** Abre perfil do usuário ou Conta do cliente. */
  onOpen: () => void;
};

type TaskEntityLinkChipsProps = {
  items: TaskEntityLinkChip[];
  ariaLabel: string;
};

/**
 * Badge único (avatar + texto): clique abre perfil/Conta.
 * Avatar fica dentro do chip; sem lightbox no card (expandir fica na página do perfil).
 */
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
          className="delpi-ui-tag-chip cm-task-link-chip"
          onClick={item.onOpen}
        >
          {item.avatar ? (
            <span className="cm-task-link-chip__avatar" aria-hidden>
              {item.avatar}
            </span>
          ) : null}
          <span className="cm-task-link-chip__text">
            <span className="cm-task-link-chip__name">{item.label}</span>
            {item.subtitle ? (
              <span className="cm-task-link-chip__subtitle">{item.subtitle}</span>
            ) : null}
          </span>
        </button>
      ))}
    </div>
  );
}
