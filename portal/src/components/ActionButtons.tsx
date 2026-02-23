import { Pencil, Trash2 } from "lucide-react";

type Props = {
  onEdit?: () => void;
  onDelete?: () => void;
  disabled?: boolean;
};

export const ActionButtons = ({ onEdit, onDelete, disabled }: Props) => {
  return (
    <div className="dt-actions">
      <button
        type="button"
        className="dt-action-btn"
        onClick={onEdit}
        disabled={disabled || !onEdit}
        title="Editar"
      >
        <Pencil size={16} />
      </button>

      <button
        type="button"
        className="dt-action-btn danger"
        onClick={onDelete}
        disabled={disabled || !onDelete}
        title="Excluir"
      >
        <Trash2 size={16} />
      </button>
    </div>
  );
};