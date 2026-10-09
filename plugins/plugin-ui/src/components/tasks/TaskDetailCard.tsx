import type { ReactNode } from "react";

import { ActionButton } from "../actions/ActionButton";
import { StatusBadge, statusBadgeBemClasses, type StatusBadgeVariant } from "../feedback/StatusBadge";
import { DetailCard, detailCardRichBemClasses } from "../layout/DetailCard";
import { DetailFieldGrid, detailFieldGridBemClasses, type DetailField } from "../layout/DetailFieldGrid";
import type { TaskItemPresentation } from "./taskPresentation";

export type { DetailField as TaskDetailField };

export type TaskDetailCardProps = {
  item: TaskItemPresentation;
  /** Extra fields appended after the defaults (Prazo / Responsável / Origem / Contexto). */
  fields?: DetailField[];
  /** Set false when the portal supplies its own complete field set via `fields`. */
  includeDefaultFields?: boolean;
  /** Override for the status badge label (defaults to item.statusLabel). */
  statusLabel?: string;
  /** Override for the badge variant (defaults to item.statusTone, danger when overdue). */
  statusVariant?: StatusBadgeVariant;
  /** Full replacement for the icon slot (defaults to the status badge). */
  icon?: ReactNode;
  /** Help tooltip on the card title. */
  titleHint?: string;
  /** Hint line under the title (defaults to due/source/context summary). */
  hint?: ReactNode;
  /** Full replacement for header actions (defaults to flag-driven buttons). */
  headerActions?: ReactNode;
  /** Custom description rendering (markdown etc.); defaults to plain text. */
  description?: ReactNode;
  /** Extra body content rendered after the fields grid (attachments, chips…). */
  children?: ReactNode;
  /** Extra card classes (tone modifiers, portal-specific tweaks). */
  className?: string;
  /** BEM prefix for card/grid/badge classes — portals pass their prefix to keep styling. */
  classNamePrefix?: string;
  /** Hides the flag-driven actions (completed/read-only cards). */
  readOnly?: boolean;
  onOpen?: (item: TaskItemPresentation) => void;
  onEdit?: (item: TaskItemPresentation) => void;
  onComplete?: (item: TaskItemPresentation) => void;
  onCancel?: (item: TaskItemPresentation) => void;
};

/**
 * Rich worklist card shared by the portals. Presentational only: it renders
 * a TaskItemPresentation through DetailCard + DetailFieldGrid + StatusBadge
 * and never fetches, authorizes, or navigates on its own.
 */
export function TaskDetailCard({
  item,
  fields,
  includeDefaultFields = true,
  statusLabel,
  statusVariant,
  icon,
  titleHint,
  hint,
  headerActions,
  description,
  children,
  className,
  classNamePrefix = "delpi-ui",
  readOnly = false,
  onOpen,
  onEdit,
  onComplete,
  onCancel,
}: TaskDetailCardProps) {
  const cardClasses = detailCardRichBemClasses(classNamePrefix);
  const gridClasses = detailFieldGridBemClasses(classNamePrefix);
  const badgeClasses = statusBadgeBemClasses(classNamePrefix);

  const resolvedVariant: StatusBadgeVariant =
    statusVariant ?? (item.overdue ? "danger" : item.statusTone ?? "neutral");
  const resolvedLabel =
    statusLabel ?? (item.overdue ? `${item.statusLabel} · vencida` : item.statusLabel);

  const defaultFields: DetailField[] = includeDefaultFields
    ? [
        { label: "Prazo", value: item.dueDateLabel ?? null },
        { label: "Responsável", value: item.assigneeLabel ?? null },
        { label: "Origem", value: item.sourceLabel ?? null },
        { label: "Contexto", value: item.contextLabel ?? null },
      ]
    : [];
  const allFields = [...defaultFields, ...(fields ?? [])];

  const defaultHint = [
    item.dueDateLabel,
    item.sourceLabel,
    item.contextLabel,
  ].filter(Boolean).join(" · ");

  const elementBase = `${classNamePrefix}-task-detail-card`;
  const el = (name: string) =>
    `${elementBase}__${name} delpi-ui-task-detail-card__${name}`;

  const actions = item.actions;
  const defaultActions =
    !readOnly && actions && (onOpen || onEdit || onComplete || onCancel) ? (
      <div className={el("actions")}>
        {actions.canOpen && onOpen ? (
          <ActionButton variant="ghost" onClick={() => onOpen(item)}>
            Abrir
          </ActionButton>
        ) : null}
        {actions.canEdit && onEdit ? (
          <ActionButton variant="ghost" onClick={() => onEdit(item)}>
            Editar
          </ActionButton>
        ) : null}
        {actions.canCancel && onCancel ? (
          <ActionButton variant="ghost" onClick={() => onCancel(item)}>
            Cancelar
          </ActionButton>
        ) : null}
        {actions.canComplete && onComplete ? (
          <ActionButton variant="primary" onClick={() => onComplete(item)}>
            Concluir
          </ActionButton>
        ) : null}
      </div>
    ) : null;

  return (
    <DetailCard
      classNames={cardClasses}
      labels={{ titleHelpAriaLabel: (title) => `Ajuda: ${title}` }}
      title={item.title}
      titleHint={titleHint}
      hint={hint ?? (defaultHint || undefined)}
      icon={icon ?? <StatusBadge classNames={badgeClasses} label={resolvedLabel} variant={resolvedVariant} />}
      headerActions={headerActions ?? defaultActions}
      className={[`${elementBase} delpi-ui-task-detail-card`, className]
        .filter(Boolean)
        .join(" ")}
    >
      <div className={el("body")}>
        {description !== undefined ? (
          description
        ) : item.description ? (
          <p className={el("description")}>{item.description}</p>
        ) : null}
        <DetailFieldGrid
          fields={allFields}
          classNames={gridClasses}
          labels={{ fieldHelpAriaLabel: (label) => `Ajuda: ${label}` }}
          valueFallback="—"
          wrapLabels
        />
        {children}
      </div>
    </DetailCard>
  );
}
