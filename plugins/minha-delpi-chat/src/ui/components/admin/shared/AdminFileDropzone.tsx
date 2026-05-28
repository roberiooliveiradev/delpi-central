import { Plus, Upload } from "lucide-react";
import { useRef, type DragEvent, type ReactNode } from "react";

import "./AdminFileDropzone.css";

type AdminFileDropzoneProps = {
  label: string;
  accept?: string;
  multiple?: boolean;
  disabled?: boolean;
  isBusy?: boolean;
  isDragActive?: boolean;
  title: string;
  hint: string;
  actionLabel?: string;
  onFilesSelected: (files: File[]) => void;
  onDragActiveChange?: (active: boolean) => void;
  footerSlot?: ReactNode;
};

export function AdminFileDropzone({
  label,
  accept,
  multiple = false,
  disabled = false,
  isBusy = false,
  isDragActive = false,
  title,
  hint,
  actionLabel = "Adicionar",
  onFilesSelected,
  onDragActiveChange,
  footerSlot,
}: AdminFileDropzoneProps) {
  const inputRef = useRef<HTMLInputElement | null>(null);

  function handleDragOver(event: DragEvent<HTMLElement>) {
    if (disabled || isBusy) {
      return;
    }

    event.preventDefault();
    event.stopPropagation();
    onDragActiveChange?.(true);
  }

  function handleDragLeave(event: DragEvent<HTMLElement>) {
    event.preventDefault();
    event.stopPropagation();
    onDragActiveChange?.(false);
  }

  function handleDrop(event: DragEvent<HTMLElement>) {
    if (disabled || isBusy) {
      return;
    }

    event.preventDefault();
    event.stopPropagation();
    onDragActiveChange?.(false);

    const files = Array.from(event.dataTransfer.files ?? []);

    if (files.length > 0) {
      onFilesSelected(multiple ? files : files.slice(0, 1));
    }
  }

  function openPicker() {
    if (!disabled && !isBusy) {
      inputRef.current?.click();
    }
  }

  return (
    <div className="mdc-admin-file-dropzone-field">
      <span className="mdc-admin-file-dropzone-field__label">{label}</span>

      <div
        className={[
          "mdc-admin-file-dropzone",
          isDragActive ? "mdc-admin-file-dropzone--active" : "",
          isBusy ? "mdc-admin-file-dropzone--busy" : "",
          disabled ? "mdc-admin-file-dropzone--disabled" : "",
        ]
          .filter(Boolean)
          .join(" ")}
        onDragEnter={handleDragOver}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={openPicker}
        onKeyDown={(event) => {
          if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            openPicker();
          }
        }}
        role="button"
        tabIndex={disabled ? -1 : 0}
        aria-disabled={disabled || isBusy}
        aria-label={label}
      >
        <span className="mdc-admin-file-dropzone__icon">
          <Upload size={20} aria-hidden="true" />
        </span>

        <div className="mdc-admin-file-dropzone__copy">
          <strong>{title}</strong>
          <span>{hint}</span>
        </div>

        <span className="mdc-chat-ws-outline-btn mdc-admin-file-dropzone__action">
          <Plus size={16} aria-hidden="true" />
          <span>{actionLabel}</span>
        </span>

        <input
          ref={inputRef}
          type="file"
          hidden
          accept={accept}
          multiple={multiple}
          disabled={disabled || isBusy}
          onChange={(event) => {
            const files = Array.from(event.target.files ?? []);

            if (files.length > 0) {
              onFilesSelected(files);
            }

            event.target.value = "";
          }}
        />
      </div>

      {footerSlot}
    </div>
  );
}
