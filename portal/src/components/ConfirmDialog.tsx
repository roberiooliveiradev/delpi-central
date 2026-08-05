import { Modal } from "./Modal";
import { Button } from "../ui-kit";

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
            <Button
              type="button"
              variant="secondary"
              onClick={onCancel}
              disabled={loading}
            >
              {cancelText}
            </Button>
          ) : null}
          <Button
            type="button"
            variant={danger ? "danger" : "primary"}
            onClick={onConfirm}
            disabled={loading}
            loading={loading}
          >
            {loading ? "Processando..." : confirmText}
          </Button>
        </>
      }
    >
      <p className="confirm-dialog-message">{message}</p>
    </Modal>
  );
};
