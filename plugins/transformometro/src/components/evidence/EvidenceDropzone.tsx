import { Upload } from "lucide-react";
import { useRef, useState } from "react";

type Props = {
  disabled?: boolean;
  multiple?: boolean;
  onFilesSelected: (files: File[]) => void;
};

export function EvidenceDropzone({
  disabled = false,
  multiple = true,
  onFilesSelected,
}: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragOver, setDragOver] = useState(false);

  function addFiles(fileList: FileList | null) {
    if (!fileList?.length || disabled) return;
    onFilesSelected(Array.from(fileList));
    if (inputRef.current) inputRef.current.value = "";
  }

  return (
    <div
      className={`tm-evidence-dropzone${dragOver ? " tm-evidence-dropzone--active" : ""}${
        disabled ? " tm-evidence-dropzone--disabled" : ""
      }`}
      role="button"
      tabIndex={disabled ? -1 : 0}
      aria-disabled={disabled}
      onClick={() => {
        if (!disabled) inputRef.current?.click();
      }}
      onKeyDown={(event) => {
        if (disabled) return;
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          inputRef.current?.click();
        }
      }}
      onDragEnter={(event) => {
        event.preventDefault();
        if (!disabled) setDragOver(true);
      }}
      onDragOver={(event) => {
        event.preventDefault();
        if (!disabled) setDragOver(true);
      }}
      onDragLeave={(event) => {
        event.preventDefault();
        if (event.currentTarget === event.target) setDragOver(false);
      }}
      onDrop={(event) => {
        event.preventDefault();
        setDragOver(false);
        if (!disabled) addFiles(event.dataTransfer.files);
      }}
    >
      <input
        ref={inputRef}
        type="file"
        className="tm-evidence-dropzone__input"
        multiple={multiple}
        disabled={disabled}
        onChange={(event) => addFiles(event.target.files)}
      />
      <Upload size={22} aria-hidden="true" className="tm-evidence-dropzone__icon" />
      <p className="tm-evidence-dropzone__title">Arraste arquivos aqui ou clique para buscar</p>
      <p className="ds-hint tm-evidence-dropzone__hint">
        Fotos, PDFs, planilhas e documentos (até 25 MB por arquivo).
      </p>
    </div>
  );
}
