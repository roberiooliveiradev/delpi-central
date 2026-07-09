import { Upload } from "lucide-react";
import { useRef, useState, type DragEvent, type ReactNode } from "react";

export type FileDropzoneClassNames = {
  root: string;
  rootActive: string;
  rootDisabled: string;
  rootBusy?: string;
  input: string;
  icon: string;
  title: string;
  hint: string;
};

export type FileDropzoneLabels = {
  title: string;
  hint: string;
};

export type FileDropzoneProps = {
  disabled?: boolean;
  busy?: boolean;
  multiple?: boolean;
  accept?: string;
  onFilesSelected: (files: File[]) => void;
  className?: string;
  classNames: FileDropzoneClassNames;
  labels: FileDropzoneLabels;
  /** Substitui o layout vazio padrão (ícone + título + hint). Mantém input e DnD. */
  emptyContent?: ReactNode;
  /** Substitui o conteúdo vazio padrão (ex.: preview de foto no CE). */
  filledContent?: ReactNode;
  /** DnD controlado (ex.: chat workspace com estado externo). */
  dragActive?: boolean;
  onDragActiveChange?: (active: boolean) => void;
  ariaLabel?: string;
  footerSlot?: ReactNode;
  fieldLabel?: string;
  fieldRootClassName?: string;
  fieldLabelClassName?: string;
  /** Usa atributo `hidden` no input em vez de só classe CSS. */
  hideInput?: boolean;
};

export function fileDropzoneBemClasses(prefix: string, block = "evidence-dropzone"): FileDropzoneClassNames {
  const zone = `${prefix}-${block}`;
  return {
    root: zone,
    rootActive: `${zone} ${zone}--active`,
    rootDisabled: `${zone} ${zone}--disabled`,
    input: `${zone}__input`,
    icon: `${zone}__icon`,
    title: `${zone}__title`,
    hint: `${zone}__hint`,
  };
}

export function fileDropzoneKaizenClasses(): FileDropzoneClassNames {
  return fileDropzoneBemClasses("kz", "dropzone");
}

function pickFiles(fileList: FileList | null, multiple: boolean): File[] {
  const files = Array.from(fileList ?? []);
  return multiple ? files : files.slice(0, 1);
}

export function FileDropzone({
  disabled = false,
  busy = false,
  multiple = true,
  accept,
  onFilesSelected,
  className,
  classNames,
  labels,
  emptyContent,
  filledContent,
  dragActive,
  onDragActiveChange,
  ariaLabel,
  footerSlot,
  fieldLabel,
  fieldRootClassName,
  fieldLabelClassName,
  hideInput = false,
}: FileDropzoneProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [internalDragOver, setInternalDragOver] = useState(false);
  const isControlledDrag = dragActive !== undefined || onDragActiveChange !== undefined;
  const resolvedDragOver = isControlledDrag ? Boolean(dragActive) : internalDragOver;
  const interactionDisabled = disabled || busy;

  function setDragOver(next: boolean) {
    if (isControlledDrag) {
      onDragActiveChange?.(next);
      return;
    }

    setInternalDragOver(next);
  }

  function addFiles(fileList: FileList | null) {
    if (!fileList?.length || interactionDisabled) {
      return;
    }

    const files = pickFiles(fileList, multiple);

    if (files.length > 0) {
      onFilesSelected(files);
    }

    if (inputRef.current) {
      inputRef.current.value = "";
    }
  }

  function handleDragOver(event: DragEvent<HTMLElement>) {
    if (interactionDisabled) {
      return;
    }

    event.preventDefault();
    event.stopPropagation();
    setDragOver(true);
  }

  function handleDragLeave(event: DragEvent<HTMLElement>) {
    event.preventDefault();
    event.stopPropagation();

    if (!isControlledDrag && event.currentTarget !== event.target) {
      return;
    }

    setDragOver(false);
  }

  function handleDrop(event: DragEvent<HTMLElement>) {
    if (interactionDisabled) {
      return;
    }

    event.preventDefault();
    event.stopPropagation();
    setDragOver(false);
    addFiles(event.dataTransfer.files);
  }

  function openPicker() {
    if (!interactionDisabled) {
      inputRef.current?.click();
    }
  }

  let rootClass = classNames.root;
  if (disabled) {
    rootClass = classNames.rootDisabled;
  } else if (busy && classNames.rootBusy) {
    rootClass = classNames.rootBusy;
  } else if (resolvedDragOver) {
    rootClass = classNames.rootActive;
  }

  if (className) {
    rootClass = `${rootClass} ${className}`;
  }

  const fileInput = (
    <input
      ref={inputRef}
      type="file"
      className={classNames.input || undefined}
      hidden={hideInput || undefined}
      multiple={multiple}
      accept={accept}
      disabled={interactionDisabled}
      onChange={(event) => addFiles(event.target.files)}
    />
  );

  const dropzone =
    filledContent != null ? (
      <div className={rootClass}>
        {fileInput}
        {filledContent}
      </div>
    ) : (
      <div
        className={rootClass}
        role="button"
        tabIndex={interactionDisabled ? -1 : 0}
        aria-disabled={interactionDisabled}
        aria-label={ariaLabel ?? labels.title}
        onClick={openPicker}
        onKeyDown={(event) => {
          if (interactionDisabled) {
            return;
          }

          if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            openPicker();
          }
        }}
        onDragEnter={handleDragOver}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        {fileInput}
        {emptyContent ?? (
          <>
            <Upload size={22} aria-hidden={true} className={classNames.icon} />
            <p className={classNames.title}>{labels.title}</p>
            <p className={classNames.hint}>{labels.hint}</p>
          </>
        )}
      </div>
    );

  const content = (
    <>
      {dropzone}
      {footerSlot}
    </>
  );

  if (!fieldLabel) {
    return content;
  }

  return (
    <div className={fieldRootClassName}>
      <span className={fieldLabelClassName}>{fieldLabel}</span>
      {content}
    </div>
  );
}

export type DashboardFileDropzoneProps = Omit<FileDropzoneProps, "classNames" | "labels">;

export function createDashboardFileDropzone(config: {
  classNames: FileDropzoneClassNames;
  labels: FileDropzoneLabels;
}) {
  return function DashboardFileDropzone(props: DashboardFileDropzoneProps) {
    return <FileDropzone classNames={config.classNames} labels={config.labels} {...props} />;
  };
}
