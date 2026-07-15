import type { ReactNode } from "react";
import { Pencil, Save, X, type LucideIcon } from "lucide-react";

import { HelpTooltip } from "../help/HelpTooltip";
import { delpiUiClass } from "../../utils/delpiUiClass";
import { ghostBtnBemClasses } from "../../utils/ghostBtnBem";
import { SectionCard, sectionCardPacBemClasses, type SectionCardLabels } from "./SectionCard";

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
  const ui = "delpi-ui-section-card";
  const pair = (local: string, canonical: string) => delpiUiClass(local, canonical);
  return {
    section: pair(`${card} ${section}`, `delpi-ui-card ${ui}`),
    header: pair(`${section}__header`, `${ui}__header`),
    title: pair(`${section}__title`, `${ui}__title`),
    description: pair(`${section}__desc`, `${ui}__subtitle`),
    actions: pair(`${section}__actions`, `${ui}__actions`),
    readContent: `${prefix}-section-read`,
    editContent: `${prefix}-section-edit`,
    ghostButton: ghostBtnBemClasses(prefix),
    primaryButton: `${prefix}-primary-btn`,
  };
}

export function editableSectionCardTransformometroClasses(prefix: string): EditableSectionCardClassNames {
  const section = `${prefix}-editable-section`;
  const ui = "delpi-ui-section-card";
  const pair = (local: string, canonical: string) => delpiUiClass(local, canonical);
  return {
    section: pair(`${prefix}-card ${section}`, `delpi-ui-card ${ui}`),
    header: pair(`${section}__header`, `${ui}__header`),
    title: pair(`${prefix}-section-title`, "delpi-ui-section-title"),
    description: pair(`${prefix}-hint`, `${ui}__subtitle`),
    actions: pair(`${section}__actions`, `${ui}__actions`),
    readContent: `${section}__read`,
    editContent: `${section}__edit`,
    ghostButton: ghostBtnBemClasses(prefix),
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

export type EditableSectionCardPacProps = {
  title: string;
  subtitle?: string;
  hint?: string;
  className?: string;
  isEditing: boolean;
  onEdit: () => void;
  onCancelEdit: () => void;
  readContent: ReactNode;
  editContent: ReactNode;
  headerExtra?: ReactNode;
  editable?: boolean;
  editLabel?: string;
  cancelLabel?: string;
  EditIcon?: LucideIcon;
  ghostButtonClassName: string;
  readContentClassName: string;
  editContentClassName: string;
  sectionClassNames: ReturnType<typeof sectionCardPacBemClasses>;
  sectionLabels: SectionCardLabels;
  defaultEditLabel: string;
  defaultCancelLabel: string;
};

export function EditableSectionCardPac({
  title,
  subtitle,
  hint,
  className,
  isEditing,
  onEdit,
  onCancelEdit,
  readContent,
  editContent,
  headerExtra,
  editable = true,
  editLabel,
  cancelLabel,
  EditIcon = Pencil,
  ghostButtonClassName,
  readContentClassName,
  editContentClassName,
  sectionClassNames,
  sectionLabels,
  defaultEditLabel,
  defaultCancelLabel,
}: EditableSectionCardPacProps) {
  const resolvedEditLabel = editLabel ?? defaultEditLabel;
  const resolvedCancelLabel = cancelLabel ?? defaultCancelLabel;

  return (
    <SectionCard
      title={title}
      subtitle={subtitle}
      hint={hint}
      className={className}
      classNames={sectionClassNames}
      labels={sectionLabels}
      actions={
        <>
          {headerExtra}
          {editable ? (
            isEditing ? (
              <button type="button" className={ghostButtonClassName} onClick={onCancelEdit}>
                <X size={16} aria-hidden={true} />
                {resolvedCancelLabel}
              </button>
            ) : (
              <button type="button" className={ghostButtonClassName} onClick={onEdit}>
                <EditIcon size={16} aria-hidden={true} />
                {resolvedEditLabel}
              </button>
            )
          ) : null}
        </>
      }
    >
      <div className={isEditing ? editContentClassName : readContentClassName}>
        {isEditing ? editContent : readContent}
      </div>
    </SectionCard>
  );
}

export type DashboardEditableSectionCardPacProps = Omit<
  EditableSectionCardPacProps,
  | "sectionClassNames"
  | "sectionLabels"
  | "ghostButtonClassName"
  | "readContentClassName"
  | "editContentClassName"
  | "defaultEditLabel"
  | "defaultCancelLabel"
>;

export function createDashboardEditableSectionCardPac(config: {
  prefix: string;
  labels: SectionCardLabels & { edit: string; cancel: string };
}) {
  const sectionClassNames = sectionCardPacBemClasses(config.prefix);

  return function DashboardEditableSectionCardPac(props: DashboardEditableSectionCardPacProps) {
    return (
      <EditableSectionCardPac
        sectionClassNames={sectionClassNames}
        sectionLabels={config.labels}
        ghostButtonClassName={`${config.prefix}-ghost-btn`}
        readContentClassName={`${config.prefix}-section-read`}
        editContentClassName={`${config.prefix}-section-edit`}
        defaultEditLabel={config.labels.edit}
        defaultCancelLabel={config.labels.cancel}
        {...props}
      />
    );
  };
}
