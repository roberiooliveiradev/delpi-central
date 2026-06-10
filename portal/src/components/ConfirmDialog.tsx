import { Modal } from "./Modal";

type ModalSize = "sm" | "md" | "lg" | "xl";

type Props = {
  open: boolean;
  title?: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  danger?: boolean;
  showCancel?: boolean;
  onConfirm: () => void | Promise<void>;
  onCancel: () => void;
  loading?: boolean;
  size?: ModalSize;
};

export const ConfirmDialog = ({
  open,
  title = "Confirmar ação",
  message,
  confirmText = "Confirmar",
  cancelText = "Cancelar",
  danger = true,
  showCancel = true,
  onConfirm,
  onCancel,
  loading,
  size = "sm",
}: Props) => {
  return (
    <Modal
      open={open}
      title={title}
      onClose={onCancel}
      size={size}
      footer={
        <>
          {showCancel ? (
            <button type="button" onClick={onCancel} disabled={loading}>
              {cancelText}
            </button>
          ) : null}
          <button
            type="button"
            className={danger ? "btn-danger" : ""}
            onClick={onConfirm}
            disabled={loading}
          >
            {loading ? "Processando..." : confirmText}
          </button>
        </>
      }
    >
      <p className="confirm-dialog-message">{message}</p>
    </Modal>
  );
};