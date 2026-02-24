import { Pencil, Trash2 } from "lucide-react";

type Props = {
  onEdit?: () => void;
  onDelete?: () => void;
  disabled?: boolean;
};

export const ActionButtons = ({ onEdit, onDelete, disabled }: Props) => {
  // Se nenhuma ação existir, nem renderiza o container
  if (!onEdit && !onDelete) {
    return null;
  }

  return (
    <div className="dt-actions">
      {onEdit && (
        <button
          type="button"
          className="dt-action-btn"
          onClick={onEdit}
          disabled={disabled}
          title="Editar"
        >
          <Pencil size={16} />
        </button>
      )}

      {onDelete && (
        <button
          type="button"
          className="dt-action-btn danger"
          onClick={onDelete}
          disabled={disabled}
          title="Excluir"
        >
          <Trash2 size={16} />
        </button>
      )}
    </div>
  );
};