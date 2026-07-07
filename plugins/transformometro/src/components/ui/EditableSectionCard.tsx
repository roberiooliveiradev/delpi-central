import type { ReactNode } from "react";
import { Pencil, Save, X, type LucideIcon } from "lucide-react";

import { HelpTooltip } from "@delpi/plugin-ui";

type EditableSectionCardProps = {
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
};

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
  editLabel = "Editar",
  EditIcon = Pencil,
  readContent,
  editContent,
  headerActions,
}: EditableSectionCardProps) {
  return (
    <section className="ds-card ds-editable-section">
      <header className="ds-editable-section__header">
        <div>
          <h2 className="ds-section-title">
            {title}
            {hint ? <HelpTooltip content={hint} ariaLabel={`Ajuda: ${title}`} /> : null}
          </h2>
          {description ? <p className="ds-hint">{description}</p> : null}
        </div>
        <div className="ds-editable-section__actions">
          {headerActions}
          {editable && !isEditing ? (
            <button type="button" className="ds-ghost-btn" onClick={onEdit}>
              <EditIcon size={14} aria-hidden="true" />
              {editLabel}
            </button>
          ) : null}
          {isEditing ? (
            <>
              {onSave ? (
                <button type="button" className="ds-primary-btn" onClick={onSave} disabled={saving}>
                  <Save size={14} aria-hidden="true" />
                  {saving ? "Salvando…" : "Salvar"}
                </button>
              ) : null}
              <button type="button" className="ds-ghost-btn" onClick={onCancel} disabled={saving}>
                <X size={14} aria-hidden="true" />
                Cancelar
              </button>
            </>
          ) : null}
        </div>
      </header>
      <div className={isEditing ? "ds-editable-section__edit" : "ds-editable-section__read"}>
        {isEditing ? editContent : readContent}
      </div>
    </section>
  );
}
