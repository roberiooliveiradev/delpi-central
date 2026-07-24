type Props = {
  open: boolean;
  busy?: boolean;
  onClose: () => void;
  onConfirm: () => Promise<void> | void;
};

export function ManualPostModal({ open, busy, onClose, onConfirm }: Props) {
  if (!open) return null;

  return (
    <div className="lnf-modal-backdrop" role="presentation">
      <div
        className="lnf-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="lnf-manual-post-title"
      >
        <h2 id="lnf-manual-post-title">Já lançada?</h2>
        <p className="lnf-muted">
          Confirma que esta nota já foi lançada no Protheus? A solicitação será
          marcada como lançada mesmo sem conciliação automática.
        </p>
        <div className="lnf-modal__actions">
          <button
            type="button"
            className="lnf-btn lnf-btn--ghost"
            onClick={onClose}
            disabled={busy}
          >
            Voltar
          </button>
          <button
            type="button"
            className="lnf-btn lnf-btn--primary"
            disabled={busy}
            data-testid="manual-post-submit"
            onClick={() => void onConfirm()}
          >
            Já lançada
          </button>
        </div>
      </div>
    </div>
  );
}
