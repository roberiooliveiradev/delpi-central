import type { ReactNode } from "react";

import { CommercialEntityLink } from "../../app/commercialUi";

export type TaskEntityLinkChip = {
  key: string;
  label: string;
  /** Linha secundária (e-mail do usuário ou código/loja do cliente). */
  subtitle?: string;
  avatar?: ReactNode;
  href: string;
  title: string;
  onNavigate?: () => void;
};

type TaskEntityLinkChipsProps = {
  items: TaskEntityLinkChip[];
  ariaLabel: string;
};

/**
 * Badge único (avatar + texto): link real abre perfil/Conta.
 */
export function TaskEntityLinkChips({
  items,
  ariaLabel,
}: TaskEntityLinkChipsProps): ReactNode {
  if (items.length === 0) return null;
  return (
    <div className="cm-task-link-chips" role="group" aria-label={ariaLabel}>
      {items.map((item) => (
        <CommercialEntityLink
          key={item.key}
          href={item.href}
          title={item.title}
          className="delpi-ui-tag-chip cm-task-link-chip"
          onNavigate={item.onNavigate}
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
        </CommercialEntityLink>
      ))}
    </div>
  );
}
