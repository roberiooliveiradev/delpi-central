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
  if (!open) return null;
  return (
    <div className="bpmnm-overlay" role="presentation">
      <div className="bpmnm-dialog" role="alertdialog" aria-modal="true">
        <h2>Alterações não salvas</h2>
        <p>Você tem alterações não salvas neste modelo.</p>
        <div className="bpmnm-dialog__actions">
          <button type="button" onClick={onContinue} className="bpmnm-btn">
            Continuar editando
          </button>
          <button type="button" onClick={onDiscard} className="bpmnm-btn bpmnm-btn--danger">
            Descartar alterações
          </button>
          {canEdit ? (
            <button type="button" onClick={onSaveAndExit} className="bpmnm-btn bpmnm-btn--primary">
              Salvar e sair
            </button>
          ) : null}
        </div>
      </div>
    </div>
  );
}
