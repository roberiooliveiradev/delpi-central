import { Pencil, History, Power, PowerOff } from "lucide-react";

type ActionButtonsProps = {
  onEdit?: () => void;
  onHistory?: () => void;
  onActivate?: () => void;
  onDeactivate?: () => void;
  disabled?: boolean;
};

export function ActionButtons({
  onEdit,
  onHistory,
  onActivate,
  onDeactivate,
  disabled = false,
}: ActionButtonsProps) {
  if (!onEdit && !onHistory && !onActivate && !onDeactivate) {
    return null;
  }

  return (
    <div className="si-table-actions" aria-label="Ações da linha">
      {onEdit ? (
        <button
          type="button"
          className="si-table-actions__button"
          onClick={onEdit}
          disabled={disabled}
          title="Editar"
          aria-label="Editar"
        >
          <Pencil size={16} />
        </button>
      ) : null}

      {onHistory ? (
        <button
          type="button"
          className="si-table-actions__button"
          onClick={onHistory}
          disabled={disabled}
          title="Histórico"
          aria-label="Ver histórico"
        >
          <History size={16} />
        </button>
      ) : null}

      {onActivate ? (
        <button
          type="button"
          className="si-table-actions__button si-table-actions__button--success"
          onClick={onActivate}
          disabled={disabled}
          title="Ativar"
          aria-label="Ativar versão"
        >
          <Power size={16} />
        </button>
      ) : null}

      {onDeactivate ? (
        <button
          type="button"
          className="si-table-actions__button si-table-actions__button--danger"
          onClick={onDeactivate}
          disabled={disabled}
          title="Desativar"
          aria-label="Desativar versão"
        >
          <PowerOff size={16} />
        </button>
      ) : null}
    </div>
  );
}