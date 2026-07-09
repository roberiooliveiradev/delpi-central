import { Upload } from "lucide-react";
import { useRef, useState, type ReactNode } from "react";

export type FileDropzoneClassNames = {
  root: string;
  rootActive: string;
  rootDisabled: string;
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
  multiple?: boolean;
  accept?: string;
  onFilesSelected: (files: File[]) => void;
  className?: string;
  classNames: FileDropzoneClassNames;
  labels: FileDropzoneLabels;
  /** Substitui o conteúdo vazio padrão (ex.: preview de foto no CE). */
  filledContent?: ReactNode;
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

export function FileDropzone({
  disabled = false,
  multiple = true,
  accept,
  onFilesSelected,
  className,
  classNames,
  labels,
  filledContent,
}: FileDropzoneProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragOver, setDragOver] = useState(false);

  function addFiles(fileList: FileList | null) {
    if (!fileList?.length || disabled) return;
    onFilesSelected(Array.from(fileList));
    if (inputRef.current) {
      inputRef.current.value = "";
    }
  }

  let rootClass = classNames.root;
  if (disabled) {
    rootClass = classNames.rootDisabled;
  } else if (dragOver) {
    rootClass = classNames.rootActive;
  }
  if (className) {
    rootClass = `${rootClass} ${className}`;
  }

  if (filledContent) {
    return (
      <div className={rootClass}>
        <input
          ref={inputRef}
          type="file"
          className={classNames.input}
          multiple={multiple}
          accept={accept}
          disabled={disabled}
          onChange={(event) => addFiles(event.target.files)}
        />
        {filledContent}
      </div>
    );
  }

  return (
    <div
      className={rootClass}
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
        if (event.currentTarget === event.target) {
          setDragOver(false);
        }
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
        className={classNames.input}
        multiple={multiple}
        accept={accept}
        disabled={disabled}
        onChange={(event) => addFiles(event.target.files)}
      />
      <Upload size={22} aria-hidden={true} className={classNames.icon} />
      <p className={classNames.title}>{labels.title}</p>
      <p className={classNames.hint}>{labels.hint}</p>
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
