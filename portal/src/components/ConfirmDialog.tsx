import { Modal } from "./Modal";

type Props = {
  open: boolean;
  title?: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  danger?: boolean;
  onConfirm: () => void | Promise<void>;
  onCancel: () => void;
  loading?: boolean;
};

export const ConfirmDialog = ({
  open,
  title = "Confirmar ação",
  message,
  confirmText = "Confirmar",
  cancelText = "Cancelar",
  danger = true,
  onConfirm,
  onCancel,
  loading,
}: Props) => {
  return (
    <Modal
      open={open}
      title={title}
      onClose={onCancel}
      footer={
        <>
          <button onClick={onCancel} disabled={loading}>
            {cancelText}
          </button>
          <button
            className={danger ? "btn-danger" : ""}
            onClick={onConfirm}
            disabled={loading}
          >
            {loading ? "Processando..." : confirmText}
          </button>
        </>
      }
    >
      <p style={{ color: "var(--text-muted)" }}>{message}</p>
    </Modal>
  );
};