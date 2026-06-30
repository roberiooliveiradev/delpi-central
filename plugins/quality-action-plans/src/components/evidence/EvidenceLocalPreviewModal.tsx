import { Modal } from "../ui/Modal";
import { formatEvidenceFileSize } from "./evidenceAttachmentUtils";
import { EvidenceLocalPreviewContent } from "./EvidenceLocalPreviewContent";

type Props = {
  file: File | null;
  open: boolean;
  onClose: () => void;
};

export function EvidenceLocalPreviewModal({ file, open, onClose }: Props) {
  return (
    <Modal
      open={open}
      title={file?.name ?? "Pré-visualização"}
      className="pac-modal--evidence-preview"
      onClose={onClose}
    >
      {file ? (
        <div className="pac-evidence-preview-modal">
          <EvidenceLocalPreviewContent file={file} />
          <div className="pac-evidence-preview-modal__meta">
            <span>{formatEvidenceFileSize(file.size)}</span>
            <span>{file.type || "Tipo não informado"}</span>
          </div>
        </div>
      ) : null}
    </Modal>
  );
}
