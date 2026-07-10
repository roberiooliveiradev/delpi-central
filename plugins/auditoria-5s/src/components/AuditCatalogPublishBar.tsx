import { useState } from "react";
import { AlertTriangle, UploadCloud } from "lucide-react";

import type { CatalogDiff } from "../utils/catalogEditor";

type Props = {
  catalogVersion: number;
  diff: CatalogDiff;
  publishing: boolean;
  onPublish: () => Promise<void>;
};

export function AuditCatalogPublishBar({
  catalogVersion,
  diff,
  publishing,
  onPublish,
}: Props) {
  const [confirmOpen, setConfirmOpen] = useState(false);

  const handleConfirm = async () => {
    await onPublish();
    setConfirmOpen(false);
  };

  return (
    <>
      <aside className="a5s-catalog-publish">
        <div className="a5s-catalog-publish__summary">
          <p className="a5s-catalog-publish__label">Versão ativa</p>
          <strong className="a5s-catalog-publish__version">v{catalogVersion}</strong>
          {diff.hasChanges ? (
            <p className="a5s-catalog-publish__diff">
              +{diff.added} novos · ~{diff.edited} editados · −{diff.removed} removidos
            </p>
          ) : (
            <p className="a5s-catalog-publish__diff">Sem alterações pendentes</p>
          )}
        </div>
        <button
          type="button"
          className="a5s-btn a5s-btn--header"
          disabled={!diff.hasChanges || publishing}
          onClick={() => setConfirmOpen(true)}
        >
          <UploadCloud size={16} aria-hidden />
          {publishing ? "Publicando…" : "Publicar alterações"}
        </button>
      </aside>

      {confirmOpen ? (
        <div
          className="a5s-confirm-overlay"
          role="presentation"
          onClick={() => setConfirmOpen(false)}
        >
          <div
            className="a5s-confirm-dialog a5s-catalog-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="catalog-publish-title"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="a5s-catalog-modal__icon" aria-hidden>
              <AlertTriangle size={22} />
            </div>
            <h2 id="catalog-publish-title" className="a5s-catalog-modal__title">
              Publicar nova versão do catálogo?
            </h2>
            <p className="a5s-catalog-modal__text">
              As alterações valerão apenas para auditorias criadas após a publicação. Auditorias já
              avaliadas ou em andamento não serão modificadas.
            </p>
            <ul className="a5s-catalog-modal__list">
              <li>{diff.added} critério(s) novo(s)</li>
              <li>{diff.edited} critério(s) editado(s)</li>
              <li>{diff.removed} critério(s) removido(s)</li>
            </ul>
            <div className="a5s-catalog-modal__actions">
              <button
                type="button"
                className="a5s-btn a5s-btn--ghost"
                onClick={() => setConfirmOpen(false)}
                disabled={publishing}
              >
                Cancelar
              </button>
              <button
                type="button"
                className="a5s-btn a5s-btn--header"
                onClick={() => void handleConfirm()}
                disabled={publishing}
              >
                {publishing ? "Publicando…" : "Confirmar publicação"}
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </>
  );
}
