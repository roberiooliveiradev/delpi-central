import { useRef, useState } from "react";
import { Upload, X } from "lucide-react";

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
  const [dragOver, setDragOver] = useState(false);

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
            {!isExisting && (
              <button
                type="button"
                className="cx-button cx-button--danger-ghost"
                onClick={onClear}
              >
                <X size={15} /> Remover
              </button>
            )}
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
    <div
      className={`cx-photo-drop${dragOver ? " cx-photo-drop--active" : ""}`}
      role="button"
      tabIndex={0}
      onClick={() => inputRef.current?.click()}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          inputRef.current?.click();
        }
      }}
      onDragEnter={(e) => {
        e.preventDefault();
        setDragOver(true);
      }}
      onDragOver={(e) => {
        e.preventDefault();
        setDragOver(true);
      }}
      onDragLeave={(e) => {
        e.preventDefault();
        if (e.currentTarget === e.target) setDragOver(false);
      }}
      onDrop={(e) => {
        e.preventDefault();
        setDragOver(false);
        pick(e.dataTransfer.files);
      }}
    >
      <input
        ref={inputRef}
        type="file"
        className="cx-photo-drop__input"
        accept={accept}
        onChange={(e) => pick(e.target.files)}
      />
      <Upload size={22} className="cx-photo-drop__icon" aria-hidden="true" />
      <p className="cx-photo-drop__title">Arraste uma foto aqui ou clique para selecionar</p>
      <p className="cx-photo-drop__hint">JPG, PNG ou WEBP.</p>
    </div>
  );
}
