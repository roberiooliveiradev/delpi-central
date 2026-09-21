import type { ReactNode } from "react";

import {
  SectionCard,
  sectionCardPacBemClasses,
  type SectionCardClassNames,
  type SectionCardLabels,
} from "../layout/SectionCard";

export type TaskWorklistSectionProps = {
  title: string;
  subtitle?: string;
  hint?: string;
  actions?: ReactNode;
  search?: ReactNode;
  /** Filtros secundários abaixo da busca (domínio no portal). */
  filters?: ReactNode;
  children: ReactNode;
  classNames?: SectionCardClassNames;
  labels?: SectionCardLabels;
};

const DEFAULT_LABELS: SectionCardLabels = {
  titleHelpAriaLabel: (title) => `Ajuda: ${title}`,
};

/** Seção da fila. Não busca, não filtra e não conhece a entidade de tarefa. */
export function TaskWorklistSection({
  title,
  subtitle,
  hint,
  actions,
  search,
  filters,
  children,
  classNames = sectionCardPacBemClasses("delpi-ui"),
  labels = DEFAULT_LABELS,
}: TaskWorklistSectionProps) {
  return (
    <SectionCard
      classNames={classNames}
      labels={labels}
      title={title}
      subtitle={subtitle}
      hint={hint}
      actions={actions ? <div className="delpi-ui-task-worklist__actions">{actions}</div> : undefined}
    >
      <div className="delpi-ui-task-worklist">
        {search ? <div className="delpi-ui-task-worklist__search">{search}</div> : null}
        {filters ? <div className="delpi-ui-task-worklist__filters">{filters}</div> : null}
        <div className="delpi-ui-task-worklist__content">{children}</div>
      </div>
    </SectionCard>
  );
}
