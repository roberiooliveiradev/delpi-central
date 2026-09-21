import type { ReactNode } from "react";

import { ActionButton } from "../actions/ActionButton";
import {
  SectionCard,
  sectionCardPacBemClasses,
  type SectionCardClassNames,
  type SectionCardLabels,
} from "../layout/SectionCard";

export type TaskEditorReviewRow = {
  label: string;
  value: string;
};

export type TaskEditorFrameProps = {
  title: string;
  subtitle?: string;
  hint?: string;
  reviewTitle?: string;
  reviewRows?: TaskEditorReviewRow[];
  children: ReactNode;
  onClose: () => void;
  closeLabel?: string;
  primaryLabel: string;
  onPrimary: () => void;
  primaryBusy?: boolean;
  primaryDisabled?: boolean;
  classNames?: SectionCardClassNames;
  labels?: SectionCardLabels;
};

const DEFAULT_LABELS: SectionCardLabels = {
  titleHelpAriaLabel: (title) => `Ajuda: ${title}`,
};

export function TaskEditorFrame({
  title,
  subtitle,
  hint,
  reviewTitle = "Revise antes de gravar",
  reviewRows,
  children,
  onClose,
  closeLabel = "Cancelar",
  primaryLabel,
  onPrimary,
  primaryBusy = false,
  primaryDisabled = false,
  classNames = sectionCardPacBemClasses("delpi-ui"),
  labels = DEFAULT_LABELS,
}: TaskEditorFrameProps) {
  return (
    <SectionCard
      classNames={classNames}
      labels={labels}
      title={title}
      subtitle={subtitle}
      hint={hint}
      collapsible
      open
      onOpenChange={(open) => {
        if (!open) onClose();
      }}
      actions={
        <ActionButton variant="ghost" onClick={onClose}>
          Fechar
        </ActionButton>
      }
    >
      <div className="delpi-ui-task-editor-frame">
        {children}
        {reviewRows && reviewRows.length > 0 ? (
          <section className="delpi-ui-task-editor-frame__review" aria-label={reviewTitle}>
            <h3 className="delpi-ui-task-editor-frame__review-title">{reviewTitle}</h3>
            <dl className="delpi-ui-task-editor-frame__review-list">
              {reviewRows.map((row) => (
                <div key={row.label} className="delpi-ui-task-editor-frame__review-row">
                  <dt>{row.label}</dt>
                  <dd>{row.value}</dd>
                </div>
              ))}
            </dl>
          </section>
        ) : null}
        <div className="delpi-ui-task-editor-frame__actions">
          <ActionButton variant="ghost" onClick={onClose}>
            {closeLabel}
          </ActionButton>
          <ActionButton
            variant="primary"
            disabled={primaryBusy || primaryDisabled}
            onClick={onPrimary}
          >
            {primaryBusy ? "Salvando…" : primaryLabel}
          </ActionButton>
        </div>
      </div>
    </SectionCard>
  );
}
