import { X } from "lucide-react";
import FormPreviewView from "../FormPreviewView";
import type { PreviewForm } from "../utils/formPreviewModel";
import { PreviewThemeToggle, usePreviewThemeMode } from "./PreviewThemeToggle";

type FormPreviewModalProps = {
  form: PreviewForm;
  onClose: () => void;
};

export function FormPreviewModal({ form, onClose }: FormPreviewModalProps) {
  const [themeMode, setThemeMode] = usePreviewThemeMode();

  return (
    <div
      className="cx-form-preview-overlay"
      role="dialog"
      aria-modal="true"
      aria-label="Prévia do formulário"
    >
      <div className="cx-form-preview-toolbar">
        <span className="cx-form-preview-badge">Prévia — nenhuma resposta será enviada</span>
        <div className="cx-form-preview-toolbar__actions">
          <PreviewThemeToggle mode={themeMode} onChange={setThemeMode} />
          <button className="cx-button cx-button--ghost" type="button" onClick={onClose}>
            <X size={18} /> Fechar
          </button>
        </div>
      </div>
      <div className="cx-form-preview-stage" data-theme={themeMode}>
        <FormPreviewView form={form} />
      </div>
    </div>
  );
}
