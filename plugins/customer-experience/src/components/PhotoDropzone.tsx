import { useRef } from "react";
import { Upload, X } from "lucide-react";

import { CxPhotoDropzoneEmpty } from "./cxFileDropzone";

const DEFAULT_ACCEPT = "image/jpeg,image/png,image/webp";

export function PhotoDropzone({
  previewUrl,
  fileName,
  isExisting = false,
  accept = DEFAULT_ACCEPT,
  onSelect,
  onClear,
}: {
  previewUrl: string | null;
  fileName?: string | null;
  isExisting?: boolean;
  accept?: string;
  onSelect: (file: File) => void;
  onClear: () => void;
}) {
  const inputRef = useRef<HTMLInputElement>(null);

  const pick = (files: FileList | null) => {
    const file = files?.[0];
    if (file) onSelect(file);
    if (inputRef.current) inputRef.current.value = "";
  };

  if (previewUrl) {
    return (
      <div className="cx-photo-drop cx-photo-drop--filled">
        <img className="cx-photo-drop__thumb" src={previewUrl} alt="Prévia da foto" />
        <div className="cx-photo-drop__meta">
          <span className="cx-photo-drop__name">
            {fileName ?? (isExisting ? "Foto atual" : "Foto selecionada")}
          </span>
          <div className="cx-photo-drop__actions">
            <button
              type="button"
              className="cx-button cx-button--ghost"
              onClick={() => inputRef.current?.click()}
            >
              <Upload size={15} /> Trocar
            </button>
            <button
              type="button"
              className="cx-button cx-button--danger-ghost"
              onClick={onClear}
            >
              <X size={15} /> Remover
            </button>
          </div>
        </div>
        <input
          ref={inputRef}
          type="file"
          className="cx-photo-drop__input"
          accept={accept}
          onChange={(e) => pick(e.target.files)}
        />
      </div>
    );
  }

  return (
    <CxPhotoDropzoneEmpty
      multiple={false}
      accept={accept}
      onFilesSelected={(files) => {
        const file = files[0];
        if (file) onSelect(file);
      }}
    />
  );
}
