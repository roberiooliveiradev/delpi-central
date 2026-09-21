import type { ReactNode } from "react";

import {
  AlertQueue,
  alertQueueBemClasses,
  type AlertQueueClassNames,
  type AlertQueueItem,
} from "../feedback/AlertQueue";
import {
  SectionCard,
  sectionCardPacBemClasses,
  type SectionCardClassNames,
  type SectionCardLabels,
} from "./SectionCard";

export type EventsSectionItem = AlertQueueItem;

export type EventsSectionClassNames = {
  section: SectionCardClassNames;
  queue: AlertQueueClassNames;
};

export type EventsSectionProps = {
  title: string;
  subtitle?: string;
  hint?: string;
  actions?: ReactNode;
  items: EventsSectionItem[];
  /** Conteúdo extra do portal (fila, chips) — sem domínio no kit. */
  children?: ReactNode;
  /** Default true: some a seção quando não há items nem children. */
  omitWhenEmpty?: boolean;
  emptyMessage?: string;
  listAriaLabel?: string;
  classNames: EventsSectionClassNames;
  labels: SectionCardLabels;
  className?: string;
};

/**
 * Chrome de "Eventos e interações".
 * OWNS: layout da seção + lista acionável.
 * DOES NOT OWN: sourcing, prioridade de negócio, persistência.
 */
export function EventsSection({
  title,
  subtitle,
  hint,
  actions,
  items,
  children,
  omitWhenEmpty = true,
  emptyMessage,
  listAriaLabel,
  classNames,
  labels,
  className,
}: EventsSectionProps) {
  const hasItems = items.length > 0;
  const hasExtra = Boolean(children);
  if (omitWhenEmpty && !hasItems && !hasExtra) return null;

  return (
    <SectionCard
      title={title}
      subtitle={subtitle}
      hint={hint}
      actions={actions}
      className={className}
      classNames={classNames.section}
      labels={labels}
    >
      {hasItems || !hasExtra ? (
        <AlertQueue
          classNames={classNames.queue}
          items={items}
          emptyMessage={emptyMessage}
          aria-label={listAriaLabel}
        />
      ) : null}
      {children}
    </SectionCard>
  );
}

export type DashboardEventsSectionProps = Omit<EventsSectionProps, "classNames" | "labels">;

export function createDashboardEventsSection(config: {
  prefix: string;
  labels: SectionCardLabels;
  sectionClassNames?: SectionCardClassNames;
}) {
  const classNames: EventsSectionClassNames = {
    section: config.sectionClassNames ?? sectionCardPacBemClasses(config.prefix),
    queue: alertQueueBemClasses(config.prefix),
  };
  return function DashboardEventsSection(props: DashboardEventsSectionProps) {
    return <EventsSection classNames={classNames} labels={config.labels} {...props} />;
  };
}
