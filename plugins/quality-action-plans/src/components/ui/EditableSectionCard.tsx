import type { ReactNode } from "react";
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
          {isEditing ? (
            <button type="button" className="pac-ghost-btn" onClick={onCancelEdit}>
              <X size={16} aria-hidden="true" />
              Cancelar
            </button>
          ) : (
            <button type="button" className="pac-ghost-btn" onClick={onEdit}>
              <Pencil size={16} aria-hidden="true" />
              Editar
            </button>
          )}
        </>
      }
    >
      <div className={isEditing ? "pac-section-edit" : "pac-section-read"}>
        {isEditing ? editContent : readContent}
      </div>
    </SectionCard>
  );
}
