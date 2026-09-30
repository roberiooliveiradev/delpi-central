import { ActionButton } from "@delpi/plugin-ui/index";
import { BpmnmModal } from "../ui/kit";

type Props = {
  open: boolean;
  onReloadLatest: () => void;
  onExportLocal: () => void;
  onStay: () => void;
};

/** Dialog de conflito de versão (P4 §15) — sem merge, sem force overwrite. */
export function ConflictDialog({ open, onReloadLatest, onExportLocal, onStay }: Props) {
  return (
    <BpmnmModal
      open={open}
      title="Conflito de versão"
      onClose={onStay}
    >
      <p className="bpmnm-dialog__text">
        Outro usuário ou processo alterou este modelo enquanto você editava.
        Sua versão local diverge da versão autoritativa.
      </p>
      <div className="bpmnm-dialog__actions">
        <ActionButton variant="primary" onClick={onReloadLatest}>
          Recarregar versão mais recente
        </ActionButton>
        <ActionButton onClick={onExportLocal}>
          Exportar meu BPMN local
        </ActionButton>
        <ActionButton variant="ghost" onClick={onStay}>
          Permanecer em conflito
        </ActionButton>
      </div>
    </BpmnmModal>
  );
}
