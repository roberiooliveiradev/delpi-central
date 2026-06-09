import { Eye, FileText, Image as ImageIcon, Trash2, X } from "lucide-react";
import { useEffect, useState } from "react";

import { fetchChatAttachmentBlob } from "../../data/api/chatApi";
import {
  formatAttachmentSize,
  resolveAttachmentPreviewKind,
  revokeAttachmentPreviewUrl,
} from "../chatAttachmentPreview";
import { attachmentReadingStatusLabel } from "../chatAttachmentStatus";
import "./ChatAttachmentCard.css";

export type ChatAttachmentCardModel = {
  key: string;
  filename: string;
  contentType?: string | null;
  sizeBytes?: number;
  status?: string;
  readingStatus?: string;
  parsed?: boolean;
  serverAttachmentId?: string;
  localFile?: File;
  localPreviewUrl?: string | null;
};

type ChatAttachmentCardProps = {
  attachment: ChatAttachmentCardModel;
  editable?: boolean;
  getAccessToken?: () => string | undefined | Promise<string | undefined>;
  onPreview?: (attachment: ChatAttachmentCardModel) => void;
  onRemove?: (key: string) => void;
};

export function ChatAttachmentCard({
  attachment,
  editable = false,
  getAccessToken,
  onPreview,
  onRemove,
}: ChatAttachmentCardProps) {
  const previewKind = resolveAttachmentPreviewKind(
    attachment.contentType || attachment.localFile?.type,
    attachment.filename,
  );
  const [thumbUrl, setThumbUrl] = useState<string | null>(
    attachment.localPreviewUrl || null,
  );
  const statusLabel =
    attachment.readingStatus ||
    attachmentReadingStatusLabel(attachment.status, attachment.parsed);
  const sizeLabel = formatAttachmentSize(
    attachment.sizeBytes ?? attachment.localFile?.size,
  );

  useEffect(() => {
    if (previewKind !== "image") {
      return;
    }

    if (attachment.localPreviewUrl) {
      setThumbUrl(attachment.localPreviewUrl);
      return;
    }

    if (attachment.localFile) {
      const url = URL.createObjectURL(attachment.localFile);
      setThumbUrl(url);
      return () => revokeAttachmentPreviewUrl(url);
    }

    if (!attachment.serverAttachmentId) {
      return;
    }

    let active = true;
    let ownedUrl: string | null = null;

    void fetchChatAttachmentBlob(attachment.serverAttachmentId, { getAccessToken })
      .then((result) => {
        if (!active) {
          return;
        }

        ownedUrl = URL.createObjectURL(result.blob);
        setThumbUrl(ownedUrl);
      })
      .catch(() => {
        if (active) {
          setThumbUrl(null);
        }
      });

    return () => {
      active = false;
      revokeAttachmentPreviewUrl(ownedUrl);
    };
  }, [
    attachment.localFile,
    attachment.localPreviewUrl,
    attachment.serverAttachmentId,
    getAccessToken,
    previewKind,
  ]);

  return (
    <article className="mdc-chat-attachment-card">
      <button
        type="button"
        className="mdc-chat-attachment-card__preview-hit"
        onClick={() => onPreview?.(attachment)}
        aria-label={`Pré-visualizar ${attachment.filename}`}
      >
        <div className="mdc-chat-attachment-card__thumb" aria-hidden="true">
          {thumbUrl ? (
            <img src={thumbUrl} alt="" />
          ) : previewKind === "image" ? (
            <ImageIcon size={20} />
          ) : (
            <FileText size={20} />
          )}
        </div>

        <div className="mdc-chat-attachment-card__meta">
          <strong title={attachment.filename}>{attachment.filename}</strong>
          <div className="mdc-chat-attachment-card__details">
            {sizeLabel ? <span>{sizeLabel}</span> : null}
            {statusLabel ? <span>{statusLabel}</span> : null}
          </div>
        </div>
      </button>

      <div className="mdc-chat-attachment-card__actions">
        <button
          type="button"
          className="mdc-chat-attachment-card__action"
          onClick={() => onPreview?.(attachment)}
          aria-label={`Abrir pré-visualização de ${attachment.filename}`}
          title="Pré-visualizar"
        >
          <Eye size={15} aria-hidden="true" />
        </button>

        {editable && onRemove ? (
          <button
            type="button"
            className="mdc-chat-attachment-card__action mdc-chat-attachment-card__action--danger"
            onClick={() => onRemove(attachment.key)}
            aria-label={`Remover ${attachment.filename}`}
            title="Remover anexo"
          >
            {editable ? <Trash2 size={15} aria-hidden="true" /> : <X size={15} aria-hidden="true" />}
          </button>
        ) : null}
      </div>
    </article>
  );
}
