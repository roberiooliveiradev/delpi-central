import {
  Pencil,
  History,
  Power,
  PowerOff,
  FolderOpen,
  Copy,
  Wand2,
  Trash2,
} from "lucide-react";

type ActionButtonsProps = {
  onOpen?: () => void;
  onEdit?: () => void;
  onHistory?: () => void;
  onActivate?: () => void;
  onDeactivate?: () => void;
  onDuplicate?: () => void;
  onFillMissing?: () => void;
  onDelete?: () => void;
  disabled?: boolean;
};

export function ActionButtons({
  onOpen,
  onEdit,
  onHistory,
  onActivate,
  onDeactivate,
  onDuplicate,
  onFillMissing,
  onDelete,
  disabled = false,
}: ActionButtonsProps) {
  if (
    !onOpen &&
    !onEdit &&
    !onHistory &&
    !onActivate &&
    !onDeactivate &&
    !onDuplicate &&
    !onFillMissing &&
    !onDelete
  ) {
    return null;
  }

  return (
    <div className="si-table-actions" aria-label="Ações da linha">
      {onOpen ? (
        <button
          type="button"
          className="si-table-actions__button si-table-actions__button--primary"
          onClick={onOpen}
          disabled={disabled}
          title="Abrir"
          aria-label="Abrir"
        >
          <FolderOpen size={18} />
        </button>
      ) : null}

      {onDuplicate ? (
        <button
          type="button"
          className="si-table-actions__button"
          onClick={onDuplicate}
          disabled={disabled}
          title="Duplicar para outro ano"
          aria-label="Duplicar para outro ano"
        >
          <Copy size={18} />
        </button>
      ) : null}

      {onFillMissing ? (
        <button
          type="button"
          className="si-table-actions__button"
          onClick={onFillMissing}
          disabled={disabled}
          title="Preencher faltantes neste ano"
          aria-label="Preencher faltantes neste ano"
        >
          <Wand2 size={18} />
        </button>
      ) : null}

      {onEdit ? (
        <button
          type="button"
          className="si-table-actions__button"
          onClick={onEdit}
          disabled={disabled}
          title="Editar"
          aria-label="Editar"
        >
          <Pencil size={18} />
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
          <History size={18} />
        </button>
      ) : null}

      {onActivate ? (
        <button
          type="button"
          className="si-table-actions__button si-table-actions__button--success"
          onClick={onActivate}
          disabled={disabled}
          title="Ativar"
          aria-label="Ativar"
        >
          <Power size={18} />
        </button>
      ) : null}

      {onDeactivate ? (
        <button
          type="button"
          className="si-table-actions__button si-table-actions__button--danger"
          onClick={onDeactivate}
          disabled={disabled}
          title="Desativar"
          aria-label="Desativar"
        >
          <PowerOff size={18} />
        </button>
      ) : null}

      {onDelete ? (
        <button
          type="button"
          className="si-table-actions__button si-table-actions__button--danger"
          onClick={onDelete}
          disabled={disabled}
          title="Excluir"
          aria-label="Excluir"
        >
          <Trash2 size={18} />
        </button>
      ) : null}
    </div>
  );
}