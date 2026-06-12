import { useEffect, useState } from "react";

import { fetchChatAttachmentBlob } from "../../data/api/chatApi";
import {
  resolveAttachmentPreviewKind,
  revokeAttachmentPreviewUrl,
} from "../chatAttachmentPreview";
import {
  workspaceFileIconToneForAttachment,
  workspaceFileKindLabel,
  workspaceFileReadingStatusTone,
} from "../../content/workspaceFileIngestContent";
import { attachmentReadingStatusLabel } from "../chatAttachmentStatus";
import { WorkspaceFileCard } from "./workspace-files/WorkspaceFileCard";

import "./ChatAttachmentCard.css";
import "./workspace-files/workspaceFileIngest.css";

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
  const statusTone = workspaceFileReadingStatusTone(attachment.status, attachment.parsed);
  const kindLabel = workspaceFileKindLabel(attachment.filename);
  const resolvedPreviewKind = previewKind === "image" ? "image" : "file";
  const iconTone = workspaceFileIconToneForAttachment(
    attachment.filename,
    resolvedPreviewKind,
    statusTone,
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

  const thumb =
    thumbUrl && previewKind === "image" ? <img src={thumbUrl} alt="" /> : undefined;

  return (
    <WorkspaceFileCard
      variant="card"
      filename={attachment.filename}
      kindLabel={kindLabel}
      statusLabel={statusLabel}
      statusTone={statusTone}
      iconTone={iconTone}
      thumb={thumb}
      previewKind={resolvedPreviewKind}
      editable={editable}
      showInlineActions={editable}
      dismissRemove={editable}
      onPreview={onPreview ? () => onPreview(attachment) : undefined}
      onRemove={onRemove ? () => onRemove(attachment.key) : undefined}
    />
  );
}
