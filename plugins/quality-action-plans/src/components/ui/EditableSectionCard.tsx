import type { ReactNode } from "react";
import type { LucideIcon } from "lucide-react";
import { Pencil, X } from "lucide-react";

import { SectionCard } from "./SectionCard";

type EditableSectionCardProps = {
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
  /** Quando false, oculta o botão Editar (somente leitura). */
  editable?: boolean;
  /** Rótulos customizados (ex.: evidências → Anexar / Fechar). */
  editLabel?: string;
  cancelLabel?: string;
  EditIcon?: LucideIcon;
};

export function EditableSectionCard({
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
  editLabel = "Editar",
  cancelLabel = "Cancelar",
  EditIcon = Pencil,
}: EditableSectionCardProps) {
  return (
    <SectionCard
      title={title}
      subtitle={subtitle}
      hint={hint}
      className={className}
      actions={
        <>
          {headerExtra}
          {editable ? (
            isEditing ? (
              <button type="button" className="pac-ghost-btn" onClick={onCancelEdit}>
                <X size={16} aria-hidden="true" />
                {cancelLabel}
              </button>
            ) : (
              <button type="button" className="pac-ghost-btn" onClick={onEdit}>
                <EditIcon size={16} aria-hidden="true" />
                {editLabel}
              </button>
            )
          ) : null}
        </>
      }
    >
      <div className={isEditing ? "pac-section-edit" : "pac-section-read"}>
        {isEditing ? editContent : readContent}
      </div>
    </SectionCard>
  );
}
