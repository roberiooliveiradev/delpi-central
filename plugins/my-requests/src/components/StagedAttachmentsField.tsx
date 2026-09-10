import { FieldLabel } from "@delpi/plugin-ui/index";
import { useMemo, useState } from "react";

import { MY_REQUESTS_HELP_TOOLTIPS } from "../content/helpTooltips";
import {
  MyRequestsAttachmentPreviewStrip,
  MyRequestsFileDropzone,
} from "../ui/mrUi";
import {
  RequestFilePreviewModal,
  type RequestFilePreviewTarget,
} from "./RequestFilePreviewModal";

export type StagedAttachment = {
  id: string;
  file: File;
  previewUrl?: string | null;
};

type StagedAttachmentsFieldProps = {
  items: StagedAttachment[];
  onChange: (items: StagedAttachment[]) => void;
  busy?: boolean;
  heading?: string;
};

function isImageFile(file: File): boolean {
  if ((file.type || "").toLowerCase().startsWith("image/")) return true;
  return /\.(png|jpe?g|webp|gif|bmp|svg)$/i.test(file.name || "");
}

export function stageFiles(files: File[]): StagedAttachment[] {
  return files.map((file) => ({
    id: `local-${crypto.randomUUID()}`,
    file,
    previewUrl: isImageFile(file) ? URL.createObjectURL(file) : null,
  }));
}

export function revokeStagedPreviews(items: StagedAttachment[]): void {
  for (const item of items) {
    if (item.previewUrl) URL.revokeObjectURL(item.previewUrl);
  }
}

/** Local staging UI for create/edit before files exist on the server. */
export function StagedAttachmentsField({
  items,
  onChange,
  busy = false,
  heading = "Documentos da solicitação",
}: StagedAttachmentsFieldProps) {
  const [preview, setPreview] = useState<RequestFilePreviewTarget>(null);
  const stripItems = useMemo(
    () =>
      items.map((item) => ({
        id: item.id,
        fileName: item.file.name,
        contentType: item.file.type || null,
        previewUrl: item.previewUrl,
        detail: `${Math.max(1, Math.round(item.file.size / 1024))} KB`,
      })),
    [items],
  );

  function onFilesSelected(files: File[]) {
    if (!files.length || busy) return;
    onChange([...items, ...stageFiles(files)]);
  }

  function onRemove(id: string) {
    const next = items.filter((item) => item.id !== id);
    const removed = items.find((item) => item.id === id);
    if (removed?.previewUrl) URL.revokeObjectURL(removed.previewUrl);
    onChange(next);
  }

  return (
    <>
      <div className="my-requests-upload-field" data-help="attachments-create">
        <FieldLabel
          label={heading}
          hint={MY_REQUESTS_HELP_TOOLTIPS.attachments.create}
        />
        <MyRequestsFileDropzone
          multiple
          busy={busy}
          disabled={busy}
          accept=".pdf,.png,.jpg,.jpeg,.webp,application/pdf,image/*"
          onFilesSelected={onFilesSelected}
          ariaLabel={heading}
        />
        <MyRequestsAttachmentPreviewStrip
          mode="manage"
          items={stripItems}
          emptyMessage="Nenhum documento selecionado ainda."
          onOpen={(item) => {
            const staged = items.find((row) => row.id === item.id);
            if (!staged) return;
            setPreview({ kind: "local", file: staged.file });
          }}
          onRemove={(item) => onRemove(item.id)}
        />
      </div>
      <RequestFilePreviewModal
        target={preview}
        open={Boolean(preview)}
        onClose={() => setPreview(null)}
      />
    </>
  );
}
