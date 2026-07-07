import { X } from "lucide-react";
import FormPreviewView from "../FormPreviewView";
import type { PreviewForm } from "../utils/formPreviewModel";

type FormPreviewModalProps = {
  form: PreviewForm;
  onClose: () => void;
};

export function FormPreviewModal({ form, onClose }: FormPreviewModalProps) {
  return (
    <div
      className="cx-form-preview-overlay"
      role="dialog"
      aria-modal="true"
      aria-label="Prévia do formulário"
    >
      <div className="cx-form-preview-toolbar">
        <span className="cx-form-preview-badge">Prévia — nenhuma resposta será enviada</span>
        <button className="cx-button cx-button--ghost" type="button" onClick={onClose}>
          <X size={18} /> Fechar
        </button>
      </div>
      <div className="cx-form-preview-stage">
        <FormPreviewView form={form} />
      </div>
    </div>
  );
}
