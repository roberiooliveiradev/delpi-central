import { Pencil, Trash2 } from "lucide-react";
import { Button } from "../ui-kit";

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
    <div className="dt-actions" style={{ display: "inline-flex", gap: 6 }}>
      {onEdit && (
        <Button
          size="sm"
          onClick={onEdit}
          disabled={disabled}
          title="Editar"
          aria-label="Editar"
          icon={<Pencil size={16} />}
        />
      )}

      {onDelete && (
        <Button
          size="sm"
          variant="danger-soft"
          onClick={onDelete}
          disabled={disabled}
          title="Excluir"
          aria-label="Excluir"
          icon={<Trash2 size={16} />}
        />
      )}
    </div>
  );
};