import { Upload } from "lucide-react";
import { useRef, useState } from "react";

type Props = {
  disabled?: boolean;
  multiple?: boolean;
  onFilesSelected: (files: File[]) => void;
};

export function KaizenEvidenceDropzone({
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
      className={`kz-dropzone${dragOver ? " kz-dropzone--active" : ""}${
        disabled ? " kz-dropzone--disabled" : ""
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
        className="kz-dropzone__input"
        multiple={multiple}
        disabled={disabled}
        onChange={(event) => addFiles(event.target.files)}
      />
      <Upload size={22} aria-hidden="true" className="kz-dropzone__icon" />
      <p className="kz-dropzone__title">Arraste arquivos aqui ou clique para buscar na pasta</p>
      <p className="kz-empty-hint kz-dropzone__hint">
        Você pode selecionar mais de um arquivo (fotos, PDFs, planilhas…).
      </p>
    </div>
  );
}
