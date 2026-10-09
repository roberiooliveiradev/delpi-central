import { ActionButton } from "@delpi/plugin-ui/index";
import { BpmnmModal } from "../ui/kit";

type Props = {
  open: boolean;
  canEdit: boolean;
  onContinue: () => void;
  onDiscard: () => void;
  onSaveAndExit: () => void;
};

/** Guard de alterações não salvas (P4 §16) — navegação in-app. */
export function UnsavedChangesDialog({
  open,
  canEdit,
  onContinue,
  onDiscard,
  onSaveAndExit,
}: Props) {
  return (
    <BpmnmModal
      open={open}
      title="Alterações não salvas"
      onClose={onContinue}
      footer={
        <>
          <ActionButton onClick={onContinue}>
            Continuar editando
          </ActionButton>
          <ActionButton variant="ghost" onClick={onDiscard}>
            Descartar alterações
          </ActionButton>
          {canEdit ? (
            <ActionButton variant="primary" onClick={onSaveAndExit}>
              Salvar e sair
            </ActionButton>
          ) : null}
        </>
      }
    >
      <p className="bpmnm-dialog__text">
        Você tem alterações não salvas neste modelo.
      </p>
    </BpmnmModal>
  );
}
