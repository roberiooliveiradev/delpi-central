import { Plus, Upload } from "lucide-react";
import { createDashboardFileDropzone, type FileDropzoneClassNames } from "@delpi/plugin-ui/index";

export function workspaceFileDropzoneClasses(): FileDropzoneClassNames {
  const root = "mdc-workspace-file-dropzone";
  return {
    root,
    rootActive: `${root} mdc-workspace-file-dropzone--active`,
    rootDisabled: `${root} mdc-workspace-file-dropzone--disabled`,
    rootBusy: `${root} mdc-workspace-file-dropzone--busy`,
    input: "",
    icon: "mdc-workspace-file-dropzone__icon",
    title: "mdc-workspace-file-dropzone__copy",
    hint: "mdc-workspace-file-dropzone__copy",
  };
}

export const ChatWorkspaceFileDropzoneBase = createDashboardFileDropzone({
  classNames: workspaceFileDropzoneClasses(),
  labels: {
    title: "",
    hint: "",
  },
});

export function WorkspaceFileDropzoneEmptyContent({
  title,
  hint,
  actionLabel,
}: {
  title: string;
  hint: string;
  actionLabel: string;
}) {
  return (
    <>
      <span className="mdc-workspace-file-dropzone__icon">
        <Upload size={20} aria-hidden="true" />
      </span>

      <div className="mdc-workspace-file-dropzone__copy">
        <strong>{title}</strong>
        <span>{hint}</span>
      </div>

      <span className="mdc-chat-ws-outline-btn mdc-workspace-file-dropzone__action">
        <Plus size={16} aria-hidden="true" />
        <span>{actionLabel}</span>
      </span>
    </>
  );
}
