import {
  withStrategicIndicatorsErrorMode,
  type StrategicIndicatorsErrorMode,
  type StrategicIndicatorsErrorView,
} from "../../data/errors/strategicIndicatorsError";
import { Modal } from "./Modal";
import { StrategicIndicatorsErrorState } from "./StrategicIndicatorsErrorState";

type StrategicIndicatorsErrorModalProps = {
  open: boolean;
  onClose: () => void;
  error: StrategicIndicatorsErrorView;
  mode?: StrategicIndicatorsErrorMode;
  actionLabel?: string;
  onAction?: () => void;
};

/**
 * Modal padronizado de erros do módulo (mesmo conteúdo do card analítico).
 */
export function StrategicIndicatorsErrorModal({
  open,
  onClose,
  error,
  mode = "refresh",
  actionLabel = "Tentar novamente",
  onAction,
}: StrategicIndicatorsErrorModalProps) {
  const resolvedError = withStrategicIndicatorsErrorMode(error, mode);

  return (
    <Modal
      open={open}
      onClose={onClose}
      title={resolvedError.title}
      description={resolvedError.summary}
      size="lg"
      footer={
        onAction ? (
          <button
            type="button"
            className="si-error-state__action"
            onClick={onAction}
          >
            {actionLabel}
          </button>
        ) : undefined
      }
    >
      <StrategicIndicatorsErrorState error={resolvedError} embedded />
    </Modal>
  );
}
