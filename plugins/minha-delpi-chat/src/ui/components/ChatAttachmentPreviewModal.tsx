import { Download, FileText, Image as ImageIcon, Loader2, X } from "lucide-react";
import { useEffect, useState } from "react";

import { fetchChatAttachmentBlob } from "../../data/api/chatApi";
import {
  formatAttachmentSize,
  resolveAttachmentPreviewKind,
  revokeAttachmentPreviewUrl,
  type AttachmentPreviewKind,
} from "../chatAttachmentPreview";
import { ModalPortal } from "./ModalPortal";
import "./chat-modal-surface.css";
import "./ChatAttachmentPreviewModal.css";

export type ChatAttachmentPreviewTarget = {
  filename: string;
  contentType?: string | null;
  sizeBytes?: number;
  serverAttachmentId?: string;
  localFile?: File;
  localPreviewUrl?: string | null;
};

type ChatAttachmentPreviewModalProps = {
  target: ChatAttachmentPreviewTarget;
  getAccessToken?: () => string | undefined | Promise<string | undefined>;
  onDownload?: (attachmentId: string) => Promise<void>;
  onClose: () => void;
};

export function ChatAttachmentPreviewModal({
  target,
  getAccessToken,
  onDownload,
  onClose,
}: ChatAttachmentPreviewModalProps) {
  const [previewKind, setPreviewKind] = useState<AttachmentPreviewKind>("unsupported");
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [textPreview, setTextPreview] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    function handleKey(event: KeyboardEvent) {
      if (event.key === "Escape") {
        onClose();
      }
    }

    document.addEventListener("keydown", handleKey);
    return () => document.removeEventListener("keydown", handleKey);
  }, [onClose]);

  useEffect(() => {
    let active = true;
    let ownedUrl: string | null = null;

    async function loadPreview() {
      setLoading(true);
      setError(null);
      setTextPreview(null);

      const kind = resolveAttachmentPreviewKind(target.contentType, target.filename);
      setPreviewKind(kind);

      try {
        if (target.localFile) {
          if (kind === "text") {
            const text = await target.localFile.text();
            if (active) {
              setTextPreview(text.slice(0, 120_000));
            }
            return;
          }

          const url = target.localPreviewUrl || URL.createObjectURL(target.localFile);
          ownedUrl = url.startsWith("blob:") && !target.localPreviewUrl ? url : null;

          if (active) {
            setPreviewUrl(url);
          }
          return;
        }

        if (!target.serverAttachmentId) {
          throw new Error("Anexo indisponível para pré-visualização.");
        }

        const fetched = await fetchChatAttachmentBlob(target.serverAttachmentId, {
          getAccessToken,
        });
        const resolvedKind = resolveAttachmentPreviewKind(
          fetched.contentType || target.contentType,
          fetched.filename || target.filename,
        );
        setPreviewKind(resolvedKind);

        if (resolvedKind === "text") {
          const text = await fetched.blob.text();
          if (active) {
            setTextPreview(text.slice(0, 120_000));
          }
          return;
        }

        ownedUrl = URL.createObjectURL(fetched.blob);

        if (active) {
          setPreviewUrl(ownedUrl);
        }
      } catch (loadError) {
        if (active) {
          setError(
            loadError instanceof Error
              ? loadError.message
              : "Não foi possível carregar a pré-visualização.",
          );
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    void loadPreview();

    return () => {
      active = false;
      revokeAttachmentPreviewUrl(ownedUrl);
    };
  }, [getAccessToken, target]);

  const sizeLabel = formatAttachmentSize(target.sizeBytes);

  return (
    <ModalPortal>
      <div
        className="mdc-chat-overlay-scrim mdc-chat-overlay-scrim--centered mdc-attachment-preview-modal__backdrop"
        role="dialog"
        aria-modal="true"
        aria-label={`Pré-visualização de ${target.filename}`}
        onMouseDown={(event) => {
          if (event.target === event.currentTarget) {
            onClose();
          }
        }}
      >
        <div className="mdc-chat-overlay-panel mdc-attachment-preview-modal">
          <header className="mdc-attachment-preview-modal__header">
            <div className="mdc-attachment-preview-modal__title-wrap">
              {previewKind === "image" ? (
                <ImageIcon size={18} aria-hidden="true" />
              ) : (
                <FileText size={18} aria-hidden="true" />
              )}
              <div>
                <strong>{target.filename}</strong>
                {sizeLabel ? <small>{sizeLabel}</small> : null}
              </div>
            </div>

            <div className="mdc-attachment-preview-modal__actions">
              {target.serverAttachmentId && onDownload ? (
                <button
                  type="button"
                  className="mdc-attachment-preview-modal__tool-btn"
                  onClick={() => void onDownload(target.serverAttachmentId!)}
                >
                  <Download size={15} aria-hidden="true" />
                  Baixar
                </button>
              ) : null}

              <button
                type="button"
                className="mdc-attachment-preview-modal__close"
                onClick={onClose}
                aria-label="Fechar pré-visualização"
              >
                <X size={18} aria-hidden="true" />
              </button>
            </div>
          </header>

          <div className="mdc-attachment-preview-modal__body">
            {loading ? (
              <div className="mdc-attachment-preview-modal__loading">
                <Loader2 size={22} className="mdc-attachment-preview-modal__spinner" />
                <span>Carregando pré-visualização...</span>
              </div>
            ) : null}

            {!loading && error ? (
              <p className="mdc-attachment-preview-modal__error">{error}</p>
            ) : null}

            {!loading && !error && previewKind === "image" && previewUrl ? (
              <img
                className="mdc-attachment-preview-modal__image"
                src={previewUrl}
                alt={target.filename}
              />
            ) : null}

            {!loading && !error && previewKind === "pdf" && previewUrl ? (
              <iframe
                className="mdc-attachment-preview-modal__pdf"
                src={previewUrl}
                title={target.filename}
              />
            ) : null}

            {!loading && !error && previewKind === "text" && textPreview !== null ? (
              <pre className="mdc-attachment-preview-modal__text">{textPreview}</pre>
            ) : null}

            {!loading && !error && previewKind === "unsupported" ? (
              <p className="mdc-attachment-preview-modal__unsupported">
                Pré-visualização inline não disponível para este tipo de arquivo. Use o botão
                Baixar para abrir no seu computador.
              </p>
            ) : null}
          </div>
        </div>
      </div>
    </ModalPortal>
  );
}
