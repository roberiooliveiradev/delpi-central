import { Download, X } from "lucide-react";
import { useCallback } from "react";

import { FilePreviewView, useFilePreviewLoader } from "@delpi/plugin-ui";

import {
  downloadChatSource,
  fetchChatAttachmentBlob,
  fetchChatSourceBlob,
} from "../../../data/api/chatApi";
import { workspaceFileKindLabel } from "../../../content/workspaceFileIngestContent";
import {
  formatAttachmentSize,
  resolveAttachmentPreviewKind,
} from "../../chatAttachmentPreview";
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

export function ChatAttachmentPreviewModal({
  target,
  getAccessToken,
  onDownload,
  onClose,
}: ChatAttachmentPreviewModalProps) {
  const previewKind = resolveAttachmentPreviewKind(target.contentType, target.filename);
  const canPreview = previewKind !== "unsupported";

  const previewSource = useCallback(async () => {
    if (target.localFile) {
      return target.localFile;
    }

    if (target.serverSourceId) {
      const fetched = await fetchChatSourceBlob(target.serverSourceId, { getAccessToken });
      return fetched.blob;
    }

    if (!target.serverAttachmentId) {
      throw new Error("Anexo indisponível para pré-visualização.");
    }

    const fetched = await fetchChatAttachmentBlob(target.serverAttachmentId, { getAccessToken });
    return fetched.blob;
  }, [
    getAccessToken,
    target.localFile,
    target.serverAttachmentId,
    target.serverSourceId,
  ]);

  const state = useFilePreviewLoader({
    source: canPreview ? previewSource : null,
    mimeType: target.contentType,
    fileName: target.filename,
    enabled: canPreview,
  });

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
        {canPreview ? (
          <FilePreviewView
            state={state}
            title={target.filename}
            labels={{
              loading: "Carregando pré-visualização...",
              loadFailed: "Não foi possível carregar a pré-visualização.",
              unavailable:
                "Pré-visualização inline não disponível para este tipo de arquivo. Use o botão Baixar para abrir no seu computador.",
            }}
          />
        ) : (
          <p className="mdc-attachment-preview-modal__unsupported">
            Pré-visualização inline não disponível para este tipo de arquivo. Use o botão Baixar
            para abrir no seu computador.
          </p>
        )}
      </div>
    </ChatModal>
  );
}
