import { Download, Loader2, X } from "lucide-react";
import { useEffect, useState } from "react";

import {
  downloadChatSource,
  fetchChatAttachmentBlob,
  fetchChatSourceBlob,
} from "../../../data/api/chatApi";
import {
  formatAttachmentSize,
  resolveAttachmentPreviewKind,
  revokeAttachmentPreviewUrl,
  type AttachmentPreviewKind,
} from "../../chatAttachmentPreview";
import {
  renderDocxPreviewHtml,
  renderSpreadsheetPreviewHtml,
} from "../../chatAttachmentPreviewRender";
import { workspaceFileKindLabel } from "../../../content/workspaceFileIngestContent";
import { ChatModal } from "../shared/modal/ChatModal";
import "./ChatAttachmentPreviewModal.css";

export type ChatAttachmentPreviewTarget = {
  filename: string;
  contentType?: string | null;
  sizeBytes?: number;
  serverAttachmentId?: string;
  serverSourceId?: string;
  localFile?: File;
  localPreviewUrl?: string | null;
};

type ChatAttachmentPreviewModalProps = {
  target: ChatAttachmentPreviewTarget;
  getAccessToken?: () => string | undefined | Promise<string | undefined>;
  onDownload?: (attachmentId: string) => Promise<void>;
  onClose: () => void;
};

type PreviewPayload = {
  kind: AttachmentPreviewKind;
  previewUrl: string | null;
  textPreview: string | null;
  htmlPreview: string | null;
  ownedUrl: string | null;
};

async function buildPreviewPayload(
  blob: Blob,
  contentType: string | null | undefined,
  filename: string,
): Promise<PreviewPayload> {
  const kind = resolveAttachmentPreviewKind(contentType, filename);

  if (kind === "text") {
    const text = await blob.text();
    return {
      kind,
      previewUrl: null,
      textPreview: text.slice(0, 120_000),
      htmlPreview: null,
      ownedUrl: null,
    };
  }

  if (kind === "spreadsheet") {
    const html = await renderSpreadsheetPreviewHtml(blob);
    return {
      kind,
      previewUrl: null,
      textPreview: null,
      htmlPreview: html,
      ownedUrl: null,
    };
  }

  if (kind === "docx") {
    const html = await renderDocxPreviewHtml(blob);
    return {
      kind,
      previewUrl: null,
      textPreview: null,
      htmlPreview: html,
      ownedUrl: null,
    };
  }

  const ownedUrl = URL.createObjectURL(blob);

  return {
    kind,
    previewUrl: ownedUrl,
    textPreview: null,
    htmlPreview: null,
    ownedUrl,
  };
}

export function ChatAttachmentPreviewModal({
  target,
  getAccessToken,
  onDownload,
  onClose,
}: ChatAttachmentPreviewModalProps) {
  const [previewKind, setPreviewKind] = useState<AttachmentPreviewKind>("unsupported");
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [textPreview, setTextPreview] = useState<string | null>(null);
  const [htmlPreview, setHtmlPreview] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    let ownedUrl: string | null = null;

    async function loadPreview() {
      setLoading(true);
      setError(null);
      setTextPreview(null);
      setHtmlPreview(null);
      setPreviewUrl(null);

      const initialKind = resolveAttachmentPreviewKind(target.contentType, target.filename);
      setPreviewKind(initialKind);

      try {
        if (target.localFile) {
          const payload = await buildPreviewPayload(
            target.localFile,
            target.contentType || target.localFile.type,
            target.filename,
          );

          if (!active) {
            revokeAttachmentPreviewUrl(payload.ownedUrl);
            return;
          }

          ownedUrl = payload.ownedUrl;
          setPreviewKind(payload.kind);
          setPreviewUrl(payload.previewUrl || target.localPreviewUrl || null);
          setTextPreview(payload.textPreview);
          setHtmlPreview(payload.htmlPreview);
          return;
        }

        if (target.serverSourceId) {
          const fetched = await fetchChatSourceBlob(target.serverSourceId, {
            getAccessToken,
          });
          const payload = await buildPreviewPayload(
            fetched.blob,
            fetched.contentType || target.contentType,
            fetched.filename || target.filename,
          );

          if (!active) {
            revokeAttachmentPreviewUrl(payload.ownedUrl);
            return;
          }

          ownedUrl = payload.ownedUrl;
          setPreviewKind(payload.kind);
          setPreviewUrl(payload.previewUrl);
          setTextPreview(payload.textPreview);
          setHtmlPreview(payload.htmlPreview);
          return;
        }

        if (!target.serverAttachmentId) {
          throw new Error("Anexo indisponível para pré-visualização.");
        }

        const fetched = await fetchChatAttachmentBlob(target.serverAttachmentId, {
          getAccessToken,
        });
        const payload = await buildPreviewPayload(
          fetched.blob,
          fetched.contentType || target.contentType,
          fetched.filename || target.filename,
        );

        if (!active) {
          revokeAttachmentPreviewUrl(payload.ownedUrl);
          return;
        }

        ownedUrl = payload.ownedUrl;
        setPreviewKind(payload.kind);
        setPreviewUrl(payload.previewUrl);
        setTextPreview(payload.textPreview);
        setHtmlPreview(payload.htmlPreview);
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
  const typeBadge = workspaceFileKindLabel(target.filename);

  return (
    <ChatModal
      open
      onClose={onClose}
      size="none"
      panelClassName="mdc-attachment-preview-modal"
      ariaLabel={`Pré-visualização de ${target.filename}`}
    >
      <header className="mdc-attachment-preview-modal__header">
        <div className="mdc-attachment-preview-modal__title-wrap">
          <span className="mdc-attachment-preview-modal__type-badge" aria-hidden="true">
            {typeBadge}
          </span>
          <div>
            <strong>{target.filename}</strong>
            {sizeLabel ? <small>{sizeLabel}</small> : null}
          </div>
        </div>

        <div className="mdc-attachment-preview-modal__actions">
          {target.serverSourceId || (target.serverAttachmentId && onDownload) ? (
            <button
              type="button"
              className="mdc-attachment-preview-modal__tool-btn mdc-chat-modal-tool-btn"
              onClick={() => {
                if (target.serverSourceId) {
                  void downloadChatSource(target.serverSourceId, { getAccessToken });
                  return;
                }

                if (target.serverAttachmentId && onDownload) {
                  void onDownload(target.serverAttachmentId);
                }
              }}
            >
              <Download size={15} aria-hidden="true" />
              Baixar
            </button>
          ) : null}

          <button
            type="button"
            className="mdc-chat-modal-icon-btn mdc-chat-modal-icon-btn--outlined mdc-chat-modal-icon-btn--sm"
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

        {!loading &&
        !error &&
        (previewKind === "spreadsheet" || previewKind === "docx") &&
        htmlPreview ? (
          <div
            className="mdc-attachment-preview-modal__rich-html"
            dangerouslySetInnerHTML={{ __html: htmlPreview }}
          />
        ) : null}

        {!loading && !error && previewKind === "unsupported" ? (
          <p className="mdc-attachment-preview-modal__unsupported">
            Pré-visualização inline não disponível para este tipo de arquivo. Use o botão Baixar
            para abrir no seu computador.
          </p>
        ) : null}
      </div>
    </ChatModal>
  );
}
