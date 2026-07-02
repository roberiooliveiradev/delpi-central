import type { ReactNode } from "react";
import { Pencil, Save, X, type LucideIcon } from "lucide-react";

type EditableSectionCardProps = {
  title: string;
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
    <section className="kz-card kz-section-card">
      <header className="kz-section-card__header">
        <div>
          <h2 className="kz-section-card__title">{title}</h2>
          {description ? <p className="kz-section-card__desc">{description}</p> : null}
        </div>
        <div className="kz-section-card__actions">
          {headerActions}
          {editable && !isEditing ? (
            <button type="button" className="kz-ghost-btn" onClick={onEdit}>
              <EditIcon size={14} aria-hidden={true} />
              {editLabel}
            </button>
          ) : null}
          {isEditing ? (
            <>
              {onSave ? (
                <button
                  type="button"
                  className="kz-primary-btn"
                  onClick={onSave}
                  disabled={saving}
                >
                  <Save size={14} aria-hidden={true} />
                  {saving ? "Salvando…" : "Salvar"}
                </button>
              ) : null}
              <button type="button" className="kz-ghost-btn" onClick={onCancel} disabled={saving}>
                <X size={14} aria-hidden={true} />
                Cancelar
              </button>
            </>
          ) : null}
        </div>
      </header>
      <div className={isEditing ? "kz-section-edit" : "kz-section-read"}>
        {isEditing ? editContent : readContent}
      </div>
    </section>
  );
}
