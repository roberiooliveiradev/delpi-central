import { useState } from "react";
import { ImagePlus, Smile, X } from "lucide-react";
import { LucideIconByName, LucideIconPicker } from "@delpi/plugin-ui";
import { PhotoDropzone } from "./PhotoDropzone";
import {
  BACKGROUND_FITS,
  POINT_IMAGE_FIT_LABELS,
  normalizeBackgroundFit,
  type BackgroundFit,
} from "../types";

type IllustrationMode = "image" | "icon";

type PointIllustrationEditorProps = {
  label?: string;
  pointImageUrl?: string | null;
  pointImageFit?: BackgroundFit | null;
  pointIcon?: string | null;
  pendingFile?: File | null;
  onSelectImage: (file: File) => void;
  onClearImage: () => void;
  onChangeFit: (fit: BackgroundFit) => void;
  onChangeIcon: (icon: string | null) => void;
};

export function PointIllustrationEditor({
  label = "Ilustrativa",
  pointImageUrl,
  pointImageFit,
  pointIcon,
  pendingFile,
  onSelectImage,
  onClearImage,
  onChangeFit,
  onChangeIcon,
}: PointIllustrationEditorProps) {
  const hasImage = Boolean(pendingFile || pointImageUrl);
  const hasIcon = Boolean(pointIcon);
  const [mode, setMode] = useState<IllustrationMode>(hasIcon && !hasImage ? "icon" : "image");
  const [pickerOpen, setPickerOpen] = useState(false);

  const previewUrl = pendingFile
    ? URL.createObjectURL(pendingFile)
    : pointImageUrl ?? null;

  return (
    <div className="cx-field cx-illustration-editor">
      <span className="cx-field__label">{label}</span>
      <div className="cx-illustration-editor__modes" role="tablist" aria-label="Tipo de ilustrativa">
        <button
          type="button"
          role="tab"
          aria-selected={mode === "image"}
          className={`cx-chip-btn${mode === "image" ? " is-on" : ""}`}
          onClick={() => setMode("image")}
        >
          <ImagePlus size={14} /> Imagem
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={mode === "icon"}
          className={`cx-chip-btn${mode === "icon" ? " is-on" : ""}`}
          onClick={() => setMode("icon")}
        >
          <Smile size={14} /> Ícone
        </button>
      </div>

      {mode === "image" ? (
        <>
          <PhotoDropzone
            previewUrl={previewUrl}
            isExisting={Boolean(pointImageUrl && !pendingFile)}
            onSelect={(file) => {
              onChangeIcon(null);
              onSelectImage(file);
            }}
            onClear={onClearImage}
          />
          {hasImage && (
            <label className="cx-field">
              <span>Exibição da ilustrativa</span>
              <select
                className="cx-select"
                value={normalizeBackgroundFit(pointImageFit)}
                onChange={(e) => onChangeFit(normalizeBackgroundFit(e.target.value))}
              >
                {BACKGROUND_FITS.map((fit) => (
                  <option key={fit} value={fit}>
                    {POINT_IMAGE_FIT_LABELS[fit]}
                  </option>
                ))}
              </select>
            </label>
          )}
        </>
      ) : (
        <div className="cx-icon-attach">
          <div className="cx-icon-attach__preview">
            {pointIcon ? (
              <>
                <LucideIconByName name={pointIcon} size={36} className="cx-icon-attach__glyph" />
                <code>{pointIcon}</code>
              </>
            ) : (
              <span className="cx-muted">Nenhum ícone selecionado</span>
            )}
          </div>
          <div className="cx-icon-attach__actions">
            <button
              type="button"
              className="cx-button cx-button--ghost"
              onClick={() => setPickerOpen((v) => !v)}
            >
              <Smile size={16} /> {pointIcon ? "Trocar ícone" : "Escolher ícone"}
            </button>
            {pointIcon ? (
              <button
                type="button"
                className="cx-button cx-button--danger-ghost"
                onClick={() => onChangeIcon(null)}
              >
                <X size={16} /> Remover
              </button>
            ) : null}
          </div>
          {pickerOpen ? (
            <div className="cx-icon-attach__picker">
              <LucideIconPicker
                value={pointIcon}
                curatedOnly={false}
                onChange={(next) => {
                  if (next) onClearImage();
                  onChangeIcon(next);
                }}
                onClose={() => setPickerOpen(false)}
              />
            </div>
          ) : null}
        </div>
      )}
    </div>
  );
}
