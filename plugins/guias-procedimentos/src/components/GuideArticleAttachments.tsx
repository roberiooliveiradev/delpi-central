import { Download } from "lucide-react";
import { useEffect, useState } from "react";

import {
  listReadableProcedureAttachments,
  triggerAuthenticatedDownload,
  type ProcedureAttachment,
} from "../api/guiasProcedimentosApi";
import { HttpRequestError } from "../api/httpClient";
import { formatBytes } from "../utils/formatBytes";

type GuideArticleAttachmentsProps = {
  procedureId: string;
};

export function GuideArticleAttachments({
  procedureId,
}: GuideArticleAttachmentsProps) {
  const [items, setItems] = useState<ProcedureAttachment[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    listReadableProcedureAttachments(procedureId)
      .then((rows) => {
        if (!cancelled) setItems(rows);
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        if (err instanceof HttpRequestError && err.status === 404) {
          setItems([]);
          return;
        }
        setError("Não foi possível carregar os anexos.");
      });
    return () => {
      cancelled = true;
    };
  }, [procedureId]);

  if (error) {
    return <p className="gp-feedback gp-feedback--error">{error}</p>;
  }
  if (items.length === 0) return null;

  return (
    <section className="gp-article-attachments" aria-label="Anexos">
      <h2 className="gp-article-attachments__title">Anexos para download</h2>
      <ul className="gp-article-attachments__list">
        {items.map((item) => (
          <li key={item.id} className="gp-article-attachments__item">
            <div>
              <div className="gp-asset-title">
                {item.title || item.original_filename || "Anexo"}
              </div>
              <div className="gp-field__hint">
                {item.original_filename || "arquivo"} ·{" "}
                {formatBytes(item.size_bytes)}
              </div>
            </div>
            <button
              type="button"
              className="gp-btn gp-btn--secondary gp-btn--compact"
              disabled={busyId === item.id}
              onClick={() => {
                setBusyId(item.id);
                void triggerAuthenticatedDownload(
                  item.download_url,
                  item.original_filename || item.title || "anexo",
                )
                  .catch(() => {
                    setError("Falha ao baixar o anexo.");
                  })
                  .finally(() => setBusyId(null));
              }}
            >
              <Download size={14} strokeWidth={2} aria-hidden="true" />
              Baixar
            </button>
          </li>
        ))}
      </ul>
    </section>
  );
}
