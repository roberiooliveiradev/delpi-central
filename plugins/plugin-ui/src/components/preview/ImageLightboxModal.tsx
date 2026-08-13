import type { ReactNode } from "react";

import { FilePreviewModal } from "./FilePreviewModal";
import type { FilePreviewContentState } from "./filePreviewTypes";

export type ImageLightboxModalProps = {
  open: boolean;
  src: string;
  title: string;
  onClose: () => void;
  headerActions?: ReactNode;
  footer?: ReactNode;
  portalScopeClassName?: string;
  containInHost?: boolean;
  portalTarget?: Element | null;
};

function imagePreviewState(src: string): FilePreviewContentState {
  return {
    kind: "image",
    loading: false,
    error: null,
    previewUrl: src,
    textContent: null,
    textTruncated: false,
    spreadsheetData: null,
    docxData: null,
  };
}

/**
 * Modal host-contained para ampliação de imagem (avatar, thumbnails).
 * Reutiliza `FilePreviewModal` — sem segundo stack de overlay.
 */
export function ImageLightboxModal({
  open,
  src,
  title,
  onClose,
  headerActions,
  footer,
  portalScopeClassName,
  containInHost,
  portalTarget,
}: ImageLightboxModalProps) {
  return (
    <FilePreviewModal
      open={open}
      title={title}
      onClose={onClose}
      source={null}
      previewState={imagePreviewState(src)}
      headerActions={headerActions}
      footer={footer}
      portalScopeClassName={portalScopeClassName}
      containInHost={containInHost}
      portalTarget={portalTarget}
    />
  );
}
