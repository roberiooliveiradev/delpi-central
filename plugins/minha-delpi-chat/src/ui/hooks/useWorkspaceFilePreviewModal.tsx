import { useCallback, useState } from "react";

import type { ChatWorkspaceSource } from "../../data/api/chatTypes";
import {
  ChatAttachmentPreviewModal,
  type ChatAttachmentPreviewTarget,
} from "../components/workspace/ChatAttachmentPreviewModal";

type WorkspaceFilePreviewModalOptions = {
  getAccessToken?: () => string | undefined | Promise<string | undefined>;
};

export function buildWorkspaceSourcePreviewTarget(
  source: ChatWorkspaceSource,
): ChatAttachmentPreviewTarget {
  return {
    filename: source.original_filename?.trim() || source.title,
    contentType: source.content_type,
    serverSourceId: source.id,
  };
}

export function buildWorkspaceLocalFilePreviewTarget(file: File): ChatAttachmentPreviewTarget {
  return {
    filename: file.name,
    contentType: file.type,
    sizeBytes: file.size,
    localFile: file,
  };
}

export function useWorkspaceFilePreviewModal(options: WorkspaceFilePreviewModalOptions = {}) {
  const [target, setTarget] = useState<ChatAttachmentPreviewTarget | null>(null);

  const openPreview = useCallback((next: ChatAttachmentPreviewTarget) => {
    setTarget(next);
  }, []);

  const closePreview = useCallback(() => {
    setTarget(null);
  }, []);

  const previewModal = target ? (
    <ChatAttachmentPreviewModal
      target={target}
      getAccessToken={options.getAccessToken}
      onClose={closePreview}
    />
  ) : null;

  return {
    openPreview,
    closePreview,
    previewModal,
  };
}
