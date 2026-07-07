import type { ReactNode } from "react";
import { Pencil, Save, X, type LucideIcon } from "lucide-react";

import { HelpTooltip } from "../help/HelpTooltip";

export type EditableSectionCardClassNames = {
  section: string;
  header: string;
  title: string;
  description: string;
  actions: string;
  readContent: string;
  editContent: string;
  ghostButton: string;
  primaryButton: string;
};

export type EditableSectionCardLabels = {
  edit: string;
  save: string;
  saving: string;
  cancel: string;
  titleHelpAriaLabel: (title: string) => string;
};

export type EditableSectionCardProps = {
  title: string;
  hint?: string;
  description?: string;
  isEditing: boolean;
  onEdit: () => void;
  onCancel: () => void;
  onSave?: () => void;
  saving?: boolean;
  editable?: boolean;
  editLabel?: string;
  EditIcon?: LucideIcon;
  readContent: ReactNode;
  editContent: ReactNode;
  headerActions?: ReactNode;
  classNames: EditableSectionCardClassNames;
  labels: EditableSectionCardLabels;
};

export function editableSectionCardBemClasses(
  prefix: string,
  options?: { cardClass?: string; sectionBlock?: string },
): EditableSectionCardClassNames {
  const card = options?.cardClass ?? `${prefix}-card`;
  const section = options?.sectionBlock ?? `${prefix}-section-card`;
  return {
    section: `${card} ${section}`,
    header: `${section}__header`,
    title: `${section}__title`,
    description: `${section}__desc`,
    actions: `${section}__actions`,
    readContent: `${prefix}-section-read`,
    editContent: `${prefix}-section-edit`,
    ghostButton: `${prefix}-ghost-btn`,
    primaryButton: `${prefix}-primary-btn`,
  };
}

export function editableSectionCardTransformometroClasses(prefix: string): EditableSectionCardClassNames {
  const section = `${prefix}-editable-section`;
  return {
    section: `${prefix}-card ${section}`,
    header: `${section}__header`,
    title: `${prefix}-section-title`,
    description: `${prefix}-hint`,
    actions: `${section}__actions`,
    readContent: `${section}__read`,
    editContent: `${section}__edit`,
    ghostButton: `${prefix}-ghost-btn`,
    primaryButton: `${prefix}-primary-btn`,
  };
}

export function EditableSectionCard({
  title,
  hint,
  description,
  isEditing,
  onEdit,
  onCancel,
  onSave,
  saving = false,
  editable = true,
  editLabel,
  EditIcon = Pencil,
  readContent,
  editContent,
  headerActions,
  classNames,
  labels,
}: EditableSectionCardProps) {
  const resolvedEditLabel = editLabel ?? labels.edit;

  return (
    <section className={classNames.section}>
      <header className={classNames.header}>
        <div>
          <h2 className={classNames.title}>
            {title}
            {hint ? (
              <HelpTooltip
                content={hint}
                ariaLabel={labels.titleHelpAriaLabel(title)}
              />
            ) : null}
          </h2>
          {description ? <p className={classNames.description}>{description}</p> : null}
        </div>
        <div className={classNames.actions}>
          {headerActions}
          {editable && !isEditing ? (
            <button type="button" className={classNames.ghostButton} onClick={onEdit}>
              <EditIcon size={14} aria-hidden={true} />
              {resolvedEditLabel}
            </button>
          ) : null}
          {isEditing ? (
            <>
              {onSave ? (
                <button
                  type="button"
                  className={classNames.primaryButton}
                  onClick={onSave}
                  disabled={saving}
                >
                  <Save size={14} aria-hidden={true} />
                  {saving ? labels.saving : labels.save}
                </button>
              ) : null}
              <button
                type="button"
                className={classNames.ghostButton}
                onClick={onCancel}
                disabled={saving}
              >
                <X size={14} aria-hidden={true} />
                {labels.cancel}
              </button>
            </>
          ) : null}
        </div>
      </header>
      <div className={isEditing ? classNames.editContent : classNames.readContent}>
        {isEditing ? editContent : readContent}
      </div>
    </section>
  );
}

export type DashboardEditableSectionCardProps = Omit<
  EditableSectionCardProps,
  "classNames" | "labels"
>;

export function createDashboardEditableSectionCard(config: {
  classNames: EditableSectionCardClassNames;
  labels: EditableSectionCardLabels;
}) {
  return function DashboardEditableSectionCard(props: DashboardEditableSectionCardProps) {
    return (
      <EditableSectionCard
        classNames={config.classNames}
        labels={config.labels}
        {...props}
      />
    );
  };
}
