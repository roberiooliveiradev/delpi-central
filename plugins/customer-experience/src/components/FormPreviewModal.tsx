import { X } from "lucide-react";
import type { CSSProperties } from "react";
import FormPreviewView from "../FormPreviewView";
import type { BackgroundFit } from "../types";
import type { PreviewForm } from "../utils/formPreviewModel";
import { PreviewThemeToggle, usePreviewThemeMode } from "./PreviewThemeToggle";

type FormPreviewModalProps = {
  form: PreviewForm;
  onClose: () => void;
};

function resolveBackgroundFit(value: string | null | undefined): BackgroundFit {
  if (value === "fixed" || value === "tile" || value === "scale") return value;
  return "scale";
}

export function FormPreviewModal({ form, onClose }: FormPreviewModalProps) {
  const [themeMode, setThemeMode] = usePreviewThemeMode();
  const backgroundUrl = form.backgroundImageUrl ?? null;
  const backgroundFit = resolveBackgroundFit(form.backgroundFit);
  const viewportPhotoStyle = backgroundUrl
    ? ({ backgroundImage: `url(${backgroundUrl})` } as CSSProperties)
    : undefined;

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
        {/*
          Fundo fora do scroll (igual position:fixed no link público).
          Antes o mosaico vivia dentro do conteúdo rolável e cortava na altura do card.
        */}
        {backgroundUrl && (
          <div className="cxform-viewport-bg" aria-hidden="true">
            <div
              className={`cxform-viewport-bg__photo cxform-viewport-bg__photo--${backgroundFit}`}
              style={viewportPhotoStyle}
            />
            <div className="cxform-viewport-bg__scrim" />
          </div>
        )}
        <div className="cx-form-preview-scroll">
          <FormPreviewView form={form} />
        </div>
      </div>
    </div>
  );
}
