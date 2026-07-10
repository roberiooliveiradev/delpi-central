import { Download } from "lucide-react";
import { useCallback } from "react";

import { FilePreviewModal, resolveFilePreviewKind } from "@delpi/plugin-ui/index";

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

  const sizeLabel = formatAttachmentSize(target.sizeBytes);
  const typeBadge = workspaceFileKindLabel(target.filename);
  const kindLabel = resolveFilePreviewKind({
    mimeType: target.contentType,
    fileName: target.filename,
  });

  const showDownload =
    Boolean(target.serverSourceId) || Boolean(target.serverAttachmentId && onDownload);

  return (
    <FilePreviewModal
      open
      title={target.filename}
      onClose={onClose}
      source={canPreview ? previewSource : null}
      mimeType={target.contentType}
      fileName={target.filename}
      enabled
      metaItems={[typeBadge, sizeLabel, kindLabel !== "none" ? kindLabel.toUpperCase() : null]}
      labels={{
        loading: "Carregando pré-visualização...",
        loadFailed: "Não foi possível carregar a pré-visualização.",
        unavailable:
          "Pré-visualização inline não disponível para este tipo de arquivo. Use o botão Baixar para abrir no seu computador.",
      }}
      headerActions={
        showDownload ? (
          <button
            type="button"
            className="delpi-ui-file-preview__tool-btn"
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
        ) : null
      }
    />
  );
}
