type Props = {
  open: boolean;
  onReloadLatest: () => void;
  onExportLocal: () => void;
  onStay: () => void;
};

/** Dialog de conflito de versão (P4 §15) — sem merge, sem force overwrite. */
export function ConflictDialog({ open, onReloadLatest, onExportLocal, onStay }: Props) {
  if (!open) return null;
  return (
    <div className="bpmnm-overlay" role="presentation">
      <div
        className="bpmnm-dialog"
        role="alertdialog"
        aria-modal="true"
        aria-labelledby="bpmnm-conflict-title"
      >
        <h2 id="bpmnm-conflict-title">Conflito de versão</h2>
        <p>
          Outro usuário ou processo alterou este modelo enquanto você editava.
          Sua versão local diverge da versão autoritativa.
        </p>
        <div className="bpmnm-dialog__actions">
          <button type="button" onClick={onReloadLatest} className="bpmnm-btn bpmnm-btn--primary">
            Recarregar versão mais recente
          </button>
          <button type="button" onClick={onExportLocal} className="bpmnm-btn">
            Exportar meu BPMN local
          </button>
          <button type="button" onClick={onStay} className="bpmnm-btn bpmnm-btn--ghost">
            Permanecer em conflito
          </button>
        </div>
      </div>
    </div>
  );
}
